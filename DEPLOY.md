# Deploying drylab

> **Publication flow (2026-08-20):** the repository pushed to GitHub is a
> separate PUBLICATION repo that excludes `validation/` and the internal
> collaboration files. Build/update it with
> `python tools/build_publish_repo.py <dest>` and follow
> `GITHUB_SETUP.md` (shipped in the publication repo) for the GitHub and
> Pages setup. Everything below applies to that publication repo.

The app is a self-contained marimo notebook that runs entirely in the
browser through Pyodide. There is no server, no backend, no database and no
secrets — publishing is just serving static files. That is the reason the
shipped package depends on numpy and plotly alone.

Two workflows are included:

| workflow | when | what it does |
|---|---|---|
| `.github/workflows/validate.yml` | every push and PR | runs the oracle suites that need no external runtime, and checks `dist/` is not stale |
| `.github/workflows/deploy.yml` | every push to `main` | rebuilds the artifact, exports the WASM site, publishes to GitHub Pages |

## One-time setup

1. **Create the repository and push.**

   ```bash
   cd drylab
   git remote add origin git@github.com:<you>/drylab.git
   git push -u origin main
   ```

   The archive already contains a git repository on branch `main` with the
   history intact, so there is nothing to initialise.

2. **Turn on Pages, and set the source to Actions.**

   Repository → **Settings** → **Pages** → under *Build and deployment*,
   set **Source** to **GitHub Actions**.

   This is the step people miss. If Source is left on *Deploy from a
   branch*, the deploy workflow will run, go green, and publish nothing —
   `actions/deploy-pages` needs the Actions source to be selected.

3. **Check Actions are enabled.** Settings → Actions → General → *Allow all
   actions*. On a fork, workflows are disabled until you confirm this.

4. **Push once more, or run the workflow by hand** (Actions tab → deploy →
   *Run workflow*). The site appears at

   ```
   https://<you>.github.io/drylab/
   ```

   The URL is also printed in the `publish` job's summary.

## Day-to-day

Push to `main`. `validate` gates correctness, `deploy` republishes. Nothing
else is needed — you do **not** have to build or commit the site.

You *should* still commit `dist/` when the notebook changes:

```bash
python tools/build_wasm_notebook.py
git add dist/ && git commit -m "rebuild artifact"
```

`validate` fails if you forget, because a stale `dist/` means the committed
deployable no longer matches the notebook. The deploy workflow rebuilds it
regardless, so a stale commit cannot ship a wrong app — but the mismatch is
worth knowing about.

## Deploying somewhere other than Pages

The export is plain static files, so any host works:

```bash
pip install uv          # newer marimo requires it for html-wasm export
python -m marimo export html-wasm dist/drylab_wasm_nb_v<latest>.py \
    -o site --mode run
python -m http.server --directory site      # local preview
```

Then upload `site/` (about 28 MB, most of it Pyodide and the scientific
wheels) to Netlify, Cloudflare Pages, S3, or a departmental web server.
Keep the `.nojekyll` file: without it, GitHub Pages strips directories
whose names begin with an underscore, which breaks the asset tree.

`--mode run` publishes the app with code hidden. Use `--mode edit` instead
if you want readers to see and modify the notebook source in the browser.

## What is verified, and what is not

Verified on this machine: the artifact rebuilds byte-for-byte from a clean
clone; `marimo export html-wasm` produces `site/index.html` plus
`.nojekyll` in about 10 seconds; both workflow files parse and their key
steps were dry-run locally against a fresh checkout.

**Not verified:** the workflows have never executed on GitHub's runners,
and the exported site has not been loaded in a browser. Pyodide must fetch
numpy, pandas and plotly wheels at first load, so expect a slow initial
page load and confirm the app actually starts before announcing the URL.
