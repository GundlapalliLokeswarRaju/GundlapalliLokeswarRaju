# Setup — about 15 minutes

## 1. Create the special profile repo
GitHub shows a repo's README on your profile when the repo **has the same name as your username**.

1. Go to <https://github.com/new>
2. Repository name: **`GundlapalliLokeswarRaju`** · Public · tick *Add a README file*
3. Upload everything in this folder, keeping the structure (`assets/`, `scripts/`, `profile-3d-contrib/`, `.github/`).

> The easiest and safest way is git (this also uploads the hidden `.github` folder):
> ```
> git clone https://github.com/GundlapalliLokeswarRaju/GundlapalliLokeswarRaju.git
> cd GundlapalliLokeswarRaju
> # copy the contents of this kit into this folder (replace the README), then:
> git add -A
> git commit -m "profile"
> git push
> ```
> GitHub's web uploader and some file managers skip hidden folders like `.github/`, and without it none of the automations exist.

## 2. Turn on the automations
1. Repo → **Settings → Actions → General → Workflow permissions** → choose **Read and write permissions** → Save.
2. Repo → **Actions** tab → run each workflow once with **Run workflow**:
   - *Rebuild profile visuals* — fills your real stats and your newest repos (do this first)
   - *Contribution snake* — creates the `output` branch with the snake SVGs
   - *3D contribution graph* — replaces the placeholder in `profile-3d-contrib/`
   - *Live feeds* — fills the recent-activity list
3. Optional blog feed: **Settings → Secrets and variables → Actions → Variables → New variable**
   `BLOG_FEEDS` = comma-separated RSS URLs (Medium: `https://medium.com/feed/@you`, dev.to: `https://dev.to/feed/you`).

After that everything refreshes by itself: stats and projects every 3 hours, snake and 3D graph daily, feeds every 6 hours.

## 3. Fill in your links
Search `README.md` for `YOUR-` and replace: LinkedIn ID, portfolio URL, email, résumé link.
(There are a few of each; use find-and-replace.)

## 4. Featured projects add themselves
Upload a new public repo and within 3 hours (or right after you run *Rebuild profile visuals*) it appears as a card in **Featured work** and is linked from the README. Newest repos come first; forks and your profile repo are skipped.

- Give each repo a **one-line description** on GitHub: that becomes the card text.
- Add **topics** (Settings gear next to *About*): the first three become the tags next to the language.
- Hide a repo with `"exclude_repos": ["repo-name"]` in `profile.config.json`.
- Show more or fewer cards with `"projects_count"` (default 6).
- Want a project to always be listed first (e.g. something outside your account)? Add it to `"projects"` in the config using the same fields as the placeholders.

## 5. Change any text
Edit **`profile.config.json`**: name, tagline, roles, boot lines, terminal text, services, neofetch stack, skill meters and footer. Commit, and the *Rebuild profile visuals* workflow regenerates every SVG.

The four **skill meters** at the top right of the header (`"meters"`) are just decoration: set the labels and percentages to whatever you honestly want to show, or change them to anything you like.

## 6. Add demo GIFs (optional, big win for recruiters)
Record 10–15 second clips of your best projects (ScreenToGif on Windows, Kap on Mac). Keep each under about 5 MB.
Put them in `assets/demos/` and uncomment the demo block in the README.

## 7. Polish the profile itself (Settings → Public profile)
- **Name:** Gundlapalli Lokeswar Raju
- **Bio (160 chars):** `Data Engineer · Python, SQL, Azure · AI/ML enthusiast · Cloud explorer · Open to internships, collabs & Data/AI roles`
- Fill **Company / Location / Website / Social links**; recruiters filter on them.
- **Pin your 6 best repos** (Profile → Customize your pins).
- Turn on **Settings → Public profile → Contributions & activity → "Include private contributions on my profile"** if you work in private repos.

## 8. Optional: include private & organisation work in your stats
Without this, the stats count public activity only (the cards say so). To include private and org work:

1. Create a token: GitHub → Settings → Developer settings → **Personal access tokens → Tokens (classic)** → scopes **`repo`**, **`read:org`** and **`read:user`**. Set an expiry and renew it when it lapses.
2. In the profile repo: **Settings → Secrets and variables → Actions → New repository secret** → name `METRICS_TOKEN`, paste the token. Never put it in a file.
3. Actions → *Rebuild profile visuals* → **Run workflow**.

`scripts/fetch_stats.py` stores counts, language percentages and your **public** repo names only. Private repo names, code and commit messages are never written.

## Run the scripts on your own computer (optional)
```
pip install fonttools==4.60.1 brotli==1.1.0 pyfiglet==1.0.2
python scripts/build_assets.py
```
Use `python3` on Mac/Linux. This rebuilds all SVGs from `profile.config.json` and `stats.json`. Open any file in `assets/` in your browser to preview it.

## Stats cards note
The streak, language and activity cards are generated from your own `stats.json`, so there is no third-party stats service to rate-limit you.
