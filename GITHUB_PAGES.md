# GitHub Pages for this repo

The workflow [`.github/workflows/github-pages.yml`](.github/workflows/github-pages.yml) publishes a small static site:

- Landing page: [`web/index.html`](web/index.html) (copied to site root as `index.html`)
- [`web/nri_wfir_exposure.html`](web/nri_wfir_exposure.html) — NRI wildfire exposure tables + OSM map (regenerate HTML with `scripts/nri_wfir_exposure_by_riskr.py`, GeoJSON with `scripts/export_nri_pge_geojson.py`)
- [`web/NRI_Census_Tracts_PGE.geojson`](web/NRI_Census_Tracts_PGE.geojson) — tract polygons for that map (EPSG:4326, simplified; GDAL required to rebuild)
- [`data/utilities/pge_oas_debt_dashboard.html`](data/utilities/pge_oas_debt_dashboard.html)
- [`data/utilities/ice_bofa_oas_line_chart.html`](data/utilities/ice_bofa_oas_line_chart.html)
- [`data/utilities/ferc1_pge_viewer/`](data/utilities/ferc1_pge_viewer/) (entire directory)

No API keys or GitHub credentials are stored in the workflow. You do **not** need to paste tokens into the chat.

## Where Pages lives in the GitHub UI

Open your repo, then either:

- **Settings** (top repo nav) → **Pages** (left sidebar, under “Code and automation”), or  
- Go directly to: `https://github.com/<owner>/<repo>/settings/pages`  
  Example: [github.com/node-econ/pge/settings/pages](https://github.com/node-econ/pge/settings/pages)

If you do not see **Pages** in the sidebar, check that you have **admin** access to the repo (or the **node-econ** org is not blocking Pages in **Organization settings → Pages**).

## One-time setup on GitHub

1. Push this project to GitHub so the repo is **not empty** (include `.github/workflows/github-pages.yml` and the `web/` and `data/utilities/` paths the workflow copies). Until at least one commit exists on the default branch, **Actions** and **Pages** will not show useful deploy state.
2. Open **Settings** → **Pages** (links above).
3. Under **Build and deployment**, set **Source** to **GitHub Actions** (not “Deploy from a branch”).
4. Merge or push the workflow to your default branch (`main` or `master`). The **Deploy GitHub Pages** workflow should run.
5. After it succeeds, **Pages** will show the public URL. For a project site under an org it is usually:

   `https://<org-name>.github.io/<repository-name>/`

   Example: `https://node-econ.github.io/pge/`. The home page is that URL (the landing `index.html`).

### First push if the GitHub repo is empty

From your machine, in the project directory. The repo [`.gitignore`](.gitignore) excludes large rasters (`.tif`), `node_modules/`, FERC raw ZIPs (`ferc1_raw_zips/`), and the huge FERC taxonomy extract tree—review **`git status`** before every commit so `.env` and other secrets never ship.

```bash
git init
git branch -M main
git remote add origin https://github.com/node-econ/pge.git
git add .
git status   # confirm .env, secrets, and multi‑GB files are not staged
git commit -m "Initial import: utilities dashboards and GitHub Pages workflow"
git push -u origin main
```

If `git remote add` fails because `origin` already exists, use `git remote set-url origin https://github.com/node-econ/pge.git` instead.

## Updating the live site

Commit changes to any published files (especially regenerated HTML under `data/utilities/`) and push. The workflow runs on push to `main` or `master`, or run it manually: **Actions** → **Deploy GitHub Pages** → **Run workflow**.

## Optional: custom domain

In **Settings** → **Pages**, add your domain under **Custom domain** and follow GitHub’s DNS instructions. No change to the workflow is required for a basic CNAME setup.
