# Setup

## 1. Create the repo
Create a **public** repo named exactly `GundlapalliLokeswarRaju` (same as your username) and upload everything in this folder, keeping the structure:

```
README.md
SETUP.md
profile.config.json
stats.json
assets/                      (generated SVG cards)
scripts/build_assets.py
scripts/fetch_stats.py
.github/workflows/*.yml
```

## 2. Fill in your details
- Search `README.md` for `YOUR-` and replace the LinkedIn ID, portfolio URL, email and resume link.
- Edit `profile.config.json`: your four real projects (`title`, `repo`, `desc`, `tags`), stack lists, and the text in the terminal card.
- Regenerate the cards after any change to the config:

```bash
python scripts/build_assets.py
```

(The stats workflow also regenerates them daily.)

## 3. Turn on the workflows
In the repo, open **Settings > Actions > General > Workflow permissions** and choose **Read and write permissions**. Then open the **Actions** tab and run each workflow once with **Run workflow**:

| Workflow | What it does |
| --- | --- |
| Update stats | Fetches totals into `stats.json` and rebuilds the cards (daily) |
| Generate 3D contribution graph | Creates `profile-3d-contrib/*.svg` (daily) |
| Generate Contribution Snake | Publishes the snake to the `output` branch (every 12h) |
| Update Recent Activity | Fills the "Latest activity" list in the README (every 6h) |

## 4. Optional: include private and organisation work in the stats
Create a **classic personal access token** with `read:user` and `repo` scopes, and add it as a repository secret named `PROFILE_TOKEN`. Without it, the stats only count public activity. Only totals are saved.
