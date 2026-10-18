#!/usr/bin/env python3
"""Fetches GitHub stats into stats.json (and lists your newest PUBLIC repos for the Featured Projects grid).

Token: $GH_TOKEN (falls back to $METRICS_TOKEN).
  - Inside GitHub Actions the built-in GITHUB_TOKEN works and sees public activity only.
  - A classic personal access token for YOUR account (repo, read:org, read:user) also counts
    private and organisation work — set it as the METRICS_TOKEN repo secret and the workflow uses it.
Only aggregate numbers and public repo info are written: no private repo names, no code, no commit messages.

Usage:  GH_TOKEN=... [STATS_SCOPE=all] python scripts/fetch_stats.py
"""
import datetime as dt, json, os, sys, urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIN = json.load(open(os.path.join(ROOT, "profile.config.json"), encoding="utf-8"))["username"]
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("METRICS_TOKEN")
SCOPE = "all" if os.environ.get("STATS_SCOPE") == "all" else "public"
IGNORE = {"jupyter notebook", "html", "css", "scss", "powershell", "batchfile", "makefile", "dockerfile", "shell", "procfile"}


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": LOGIN, **variables}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors"):
        sys.exit(f"GraphQL error: {out['errors']}")
    return out["data"]["user"]


ME_Q = "query($login: String!) { user(login: $login) { createdAt pullRequests(states: MERGED) { totalCount } } }"

YEAR_Q = """query($login: String!, $from: DateTime!, $to: DateTime!) { user(login: $login) {
  contributionsCollection(from: $from, to: $to) {
  totalCommitContributions restrictedContributionsCount totalPullRequestContributions
  totalPullRequestReviewContributions totalIssueContributions
  contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }"""

REPO_Q = """query($login: String!, $after: String) { user(login: $login) { repositories(first: 100, after: $after, isFork: false,
  ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
  totalCount pageInfo { hasNextPage endCursor }
  nodes { stargazerCount isPrivate languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } } } } }"""

# Newest PUBLIC, non-fork repos you own — these become the Featured Projects cards automatically.
LATEST_Q = """query($login: String!) { user(login: $login) { repositories(first: 30, privacy: PUBLIC, isFork: false,
  ownerAffiliations: OWNER, orderBy: {field: CREATED_AT, direction: DESC}) {
  nodes { name description url stargazerCount isArchived primaryLanguage { name }
          repositoryTopics(first: 3) { nodes { topic { name } } } } } } }"""


def main():
    if not TOKEN:
        sys.exit("Set GH_TOKEN (or METRICS_TOKEN) to a token for your account.")
    me = gql(ME_Q)

    # Contributions, one calendar year at a time (the API caps each window at a year).
    now = dt.datetime.now(dt.timezone.utc)
    start_year = int(me["createdAt"][:4])
    days, totals = {}, Counter()
    for y in range(start_year, now.year + 1):
        frm = dt.datetime(y, 1, 1, tzinfo=dt.timezone.utc)
        to = min(dt.datetime(y, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
        c = gql(YEAR_Q, **{"from": frm.isoformat(), "to": to.isoformat()})["contributionsCollection"]
        totals["commits"] += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        totals["prs"] += c["totalPullRequestContributions"]
        totals["reviews"] += c["totalPullRequestReviewContributions"]
        totals["issues"] += c["totalIssueContributions"]
        totals["contributions"] += c["contributionCalendar"]["totalContributions"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    ordered = sorted(days.items())
    today = now.date()
    # Streaks: today without a contribution yet doesn't break the current streak.
    longest = run = 0
    for _, n in ordered:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    for date, n in reversed(ordered):
        if n:
            current += 1
        elif date != today.isoformat():
            break

    last_year = [(d, n) for d, n in ordered if d > (today - dt.timedelta(days=371)).isoformat()]
    # Trim to whole weeks (Sun → Sat).
    while last_year and dt.date.fromisoformat(last_year[0][0]).weekday() != 6:
        last_year.pop(0)

    # Repositories + languages (owned, collaborator and org repos; private ones only if the token can see them).
    langs, stars, repos, private, after = Counter(), 0, 0, 0, None
    while True:
        r = gql(REPO_Q, after=after)["repositories"]
        for n in r["nodes"]:
            repos += 1; stars += n["stargazerCount"]; private += n["isPrivate"]
            for e in n["languages"]["edges"]:
                if e["node"]["name"].lower() not in IGNORE:
                    langs[e["node"]["name"]] += e["size"]
        if not r["pageInfo"]["hasNextPage"]:
            break
        after = r["pageInfo"]["endCursor"]
    total = sum(langs.values()) or 1
    top = [{"name": k, "pct": round(v * 100 / total, 1)} for k, v in langs.most_common(7)]

    latest = [
        {
            "name": n["name"],
            "description": n["description"],
            "url": n["url"],
            "stars": n["stargazerCount"],
            "language": (n["primaryLanguage"] or {}).get("name"),
            "topics": [t["topic"]["name"] for t in n["repositoryTopics"]["nodes"]],
        }
        for n in gql(LATEST_Q)["repositories"]["nodes"]
        if not n["isArchived"]
    ]

    out = {
        "updated": now.strftime("%Y-%m-%d"),
        "scope": SCOPE,
        "since": start_year,
        "year_contributions": sum(n for _, n in last_year),
        "contributions": totals["contributions"],
        "commits": totals["commits"],
        "prs": totals["prs"],
        "prs_merged": me["pullRequests"]["totalCount"],
        "reviews": totals["reviews"],
        "issues": totals["issues"],
        "repos": repos,
        "private_repos": private,
        "stars": stars,
        "streak_current": current,
        "streak_longest": longest,
        "best_day": max((n for _, n in last_year), default=0),
        "languages": top,
        "auto_projects": latest,
        "calendar": [n for _, n in last_year],
        "calendar_start": last_year[0][0] if last_year else today.isoformat(),
    }
    with open(os.path.join(ROOT, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print({k: v for k, v in out.items() if k not in ("calendar", "auto_projects")}, f"| {len(latest)} public repos listed")


if __name__ == "__main__":
    main()
