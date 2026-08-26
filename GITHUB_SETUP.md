# Getting drylab onto GitHub and live on GitHub Pages

This repository is the **publication** copy of drylab: a fresh git history
containing only the public surface. The oracle validation suites and the
development memory files live in the private development tree and are not
here, by design — `tools/build_publish_repo.py` (run from the development
tree) is what produced this repo, and is how every future release reaches
it.

Everything below was verified locally on 2026-08-20 except where marked;
the workflows themselves have not yet executed on GitHub's runners.

## 0. One-time: git identity and authentication

If this machine has never pushed to GitHub:

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@wsu.edu"
```

Pick one authentication route:

- **SSH (recommended).** Generate a key and add it to GitHub → Settings →
  SSH and GPG keys:

  ```bash
  ssh-keygen -t ed25519 -C "you@wsu.edu"      # accept defaults
  cat ~/.ssh/id_ed25519.pub                    # paste this on GitHub
  ssh -T git@github.com                        # should greet you by name
  ```

- **HTTPS + token.** GitHub → Settings → Developer settings → Personal
  access tokens → *Fine-grained*, scoped to the new repo with
  **Contents: Read and write**. Git will prompt for it as the password on
  first push.

## 1. Create the repository on GitHub

github.com → **New repository** → name `drylab` (the Pages URL becomes
`https://<you>.github.io/drylab/`). Public or private both work — but
**GitHub Pages on a private repo requires a paid plan**; on a free
account make it public. **Do not** initialize with a README, license, or
.gitignore — this repo already has its history, and an initialized remote
would force a merge on first push.

## 2. Push this repository

From this directory:

```bash
git remote add origin git@github.com:<you>/drylab.git   # SSH
#   or: git remote add origin https://github.com/<you>/drylab.git
git push -u origin main
```

## 3. Turn on Pages — the step everyone misses

Repository → **Settings** → **Pages** → under *Build and deployment*, set
**Source** to **GitHub Actions** (not "Deploy from a branch"). If Source
is left on the branch option, the deploy workflow runs, goes green, and
publishes nothing — `actions/deploy-pages` requires the Actions source.

Also confirm Settings → Actions → General → *Allow all actions and
reusable workflows* is selected.

## 4. First deployment

The push in step 2 already triggered two workflows (Actions tab):

- **validate** — rebuilds the WASM artifact and fails if the committed
  `dist/` is stale. (The seven oracle suites run in the development tree
  before each release, not here.)
- **deploy** — rebuilds the artifact from source, exports the site with
  `marimo export html-wasm`, and publishes it to Pages.

If deploy ran *before* step 3 was done, re-run it: Actions → deploy →
**Run workflow**. When it finishes, the site is at

```
https://<you>.github.io/drylab/
```

(the URL is also printed in the deploy run's `publish` job).

**First-load expectations:** the site is ~28 MB and Pyodide fetches the
numpy/pandas/plotly wheels on first visit, so the first load takes a
while on a cold cache — let it finish and confirm the tabs render before
announcing the URL to a class. One harmless curiosity: the exported site
contains a `CLAUDE.md` — that is marimo's own exporter boilerplate
(notebook-assistant instructions marimo ships), not project content.

## 5. Releasing updates (the ongoing loop)

The development tree is the source of truth. To publish a new version:

```bash
# in the DEVELOPMENT tree, after the release is committed there:
python tools/build_publish_repo.py /path/to/this/publication/repo

# in this publication repo:
git push
```

The builder replaces the working tree and commits the new release on top
(one commit per release; no force-pushes), refuses to commit when nothing
changed, and re-applies the exclusions every time — so `validation/` and
the internal collaboration files can never drift into the public repo by
accident. The deploy workflow republishes on push; nothing else is
needed.

## 6. If something goes wrong

- *Push rejected (fetch first):* the GitHub repo was initialized with a
  file in step 1. Easiest fix: delete and recreate it empty.
- *validate fails with "dist/ is stale":* in the development tree, run
  `python tools/build_wasm_notebook.py`, commit `dist/`, rebuild the
  publication repo, push.
- *deploy green but 404 at the URL:* step 3 — Pages Source must be
  **GitHub Actions**. Set it, re-run deploy.
- *Site loads but hangs at startup:* open the browser console; a wheel
  fetch may have failed on a flaky network — reload. Persistent failures
  are worth reporting with the console output.

For hosting anywhere other than Pages (departmental server, Netlify,
S3), see `DEPLOY.md` — the export is plain static files.
