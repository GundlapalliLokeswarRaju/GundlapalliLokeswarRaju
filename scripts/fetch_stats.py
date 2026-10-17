#!/usr/bin/env python3
"""Fetch GitHub totals for the profile owner and write stats.json.

Needs an env var GH_TOKEN (a personal access token with `read:user` and `repo`
scopes gives private + organisation totals; the default GITHUB_TOKEN only sees
public data). Only aggregate numbers are stored - no repo names, no code.
"""
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
USER = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))["username"]
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    latest: repositories(privacy: PUBLIC, isFork: false, ownerAffiliations: OWNER, first: 20, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes { ...R }
    }
    pinned: pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository { ...R } }
    }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 6, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}

fragment R on Repository {
  name
  description
  url
  stargazerCount
  isPrivate
  primaryLanguage { name }
  repositoryTopics(first: 3) { nodes { topic { name } } }
}
"""


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


def streaks(days):
    days = sorted(days, key=lambda d: d["date"])
    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, cur)
    # current streak: count back from today (allow today to be empty)
    current = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current += 1
        elif d["date"] == dt.date.today().isoformat():
            continue
        else:
            break
    return current, longest


def pick_projects(u):
    """Choose repos for the Featured Projects section.

    projects_mode "latest" (default): newest public, non-fork repos first, so a
    repo you upload tomorrow appears automatically.
    projects_mode "pinned": the repos you pinned on your GitHub profile.
    """
    cfg = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))
    mode = cfg.get("projects_mode", "latest")
    count = int(cfg.get("projects_count", 6))
    skip = {USER.lower(), *[x.lower() for x in cfg.get("exclude_repos", [])]}
    nodes = u["pinned"]["nodes"] if mode == "pinned" and u["pinned"]["nodes"] else u["latest"]["nodes"]
    out = []
    for r in nodes:
        if not r or r.get("isPrivate") or r["name"].lower() in skip:
            continue
        tags = []
        if r.get("primaryLanguage"):
            tags.append(r["primaryLanguage"]["name"])
        tags += [t["topic"]["name"] for t in r["repositoryTopics"]["nodes"]]
        out.append(
            {
                "title": r["name"],
                "repo": r["name"],
                "url": r["url"],
                "desc": " ".join((r.get("description") or "No description yet.").split()),
                "tags": tags[:4] or ["code"],
                "stars": r["stargazerCount"],
            }
        )
        if len(out) >= count:
            break
    return out


def main():
    if not TOKEN:
        sys.exit("GH_TOKEN is not set")
    u = gql(QUERY, {"login": USER})["user"]
    cc = u["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    current, longest = streaks(days)

    sizes = {}
    stars = 0
    for repo in u["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for e in repo["languages"]["edges"]:
            sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
    total = sum(sizes.values()) or 1
    top = [
        {"name": n, "pct": round(s * 100 / total, 1)}
        for n, s in sorted(sizes.items(), key=lambda kv: -kv[1])[:6]
    ]

    projects = pick_projects(u)

    stats = {
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "stars": stars,
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "current_streak": current,
        "longest_streak": longest,
        "contributions_year": cc["contributionCalendar"]["totalContributions"],
        "top_languages": top,
        "projects": projects,
        "updated": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }
    (ROOT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print("stats.json updated")


if __name__ == "__main__":
    main()
