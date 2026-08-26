#!/usr/bin/env python3
"""Build the PUBLICATION repository: the public, pushable form of drylab.

Ruled by Brian 2026-08-20: the repository uploaded to GitHub must exclude
``validation/``. Excluding it from new commits is not enough — pushing the
development branch would still upload every historical validation blob —
so this script constructs a FRESH single-commit repository containing only
the public surface. The development repository (full history, validation,
memory files) remains the working tree for sessions; this script is the
one-way bridge from it to the public repo, so publication is repeatable
instead of a hand-curated copy that drifts.

Also excluded (assistant's interpretation under the same ruling, flagged
in decisions.md): the internal collaboration files — ``.context/``,
``MEMORY_DIRECTIVE.md``, ``CHARTER_engineering.md``,
``NEXT_SESSION_PROMPT.md`` — which document the development process, not
the software. ``NOTICE.md`` and ``LICENSE`` are always included: the
licence obligations bind the public copy above all.

The public ``validate.yml`` keeps only the artifact-freshness job (the
oracle suites live in the development tree); the public ``README`` and
``.gitignore`` are patched accordingly. Everything else ships verbatim.

Usage:  python tools/build_publish_repo.py [dest]
        (default dest: ../drylab-publish, i.e. a sibling of the dev repo)
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

DEV = pathlib.Path(__file__).resolve().parent.parent

INCLUDE = [
    ".gitattributes",
    ".gitignore",
    ".github",
    "DEPLOY.md",
    "GITHUB_SETUP.md",
    "LICENSE",
    "NOTICE.md",
    "README.md",
    "dist",
    "drylab",
    "drylab_nb.py",
    "pyproject.toml",
    "tools",
]

# Explicit, so a future new top-level file is a deliberate decision rather
# than an accidental publication.
EXCLUDE_NOTE = [
    "validation/  (ruled out of the public repo, 2026-08-20)",
    ".context/, MEMORY_DIRECTIVE.md, CHARTER_engineering.md, "
    "NEXT_SESSION_PROMPT.md  (internal collaboration files)",
]

PUBLIC_VALIDATE_YML = """\
name: validate

# Public-repo check: the committed WASM artifact must be exactly what the
# notebook builds, so a stale dist/ cannot ship a wrong app.
#
# The seven oracle validation suites (~52,000 reference values against
# GasChromatographySimulator.jl, a Java applet, a JavaScript reference,
# Analytical Chemistry 2.0, SPYCE, and exact closed forms) are maintained
# and run in the private development tree before every release; they and
# their vendored reference materials are deliberately not part of this
# repository.

on:
  push:
  pull_request:

jobs:
  artifact-is-current:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Rebuild the artifact and demand a clean tree
        run: |
          python tools/build_wasm_notebook.py
          git diff --exit-code -- dist/ || {
            echo "dist/ is stale: run tools/build_wasm_notebook.py and commit";
            exit 1; }
"""


def patch_readme(text: str) -> str:
    """Point README's validation section at the development tree."""
    marker = "- `validation/`"
    i = text.find(marker)
    if i < 0:
        return text
    # Replace just that bullet's first line; the surrounding structure stays.
    j = text.find("\n", i)
    replacement = (
        "- validation: seven oracle suites (~52,000 reference values against"
        " Julia, Java,\n  JavaScript, Analytical Chemistry 2.0, SPYCE and"
        " exact closed forms) are\n  maintained in the private development"
        " tree and pass before every release;\n  they are not part of this"
        " repository."
    )
    return text[:i] + replacement + text[j:]


def main() -> int:
    dest = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 \
        else DEV.parent / "drylab-publish"
    # Two modes. Fresh: dest absent -> new repo, one release commit.
    # Update: dest holds a .git already -> replace the tree, commit the new
    # release ON TOP, so the public repo accumulates one commit per release
    # and a plain `git push` works (no force-push, no history surgery).
    updating = (dest / ".git").exists()
    if updating:
        for child in dest.iterdir():
            if child.name == ".git":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    else:
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)

    for name in INCLUDE:
        src = DEV / name
        if not src.exists():
            print(f"FATAL: expected {name} in the dev tree", file=sys.stderr)
            return 1
        if src.is_dir():
            shutil.copytree(src, dest / name,
                            ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(src, dest / name)

    # Public workflow set: deploy.yml verbatim, validate.yml replaced.
    (dest / ".github/workflows/validate.yml").write_text(PUBLIC_VALIDATE_YML)

    # Public README: validation section points at the dev tree.
    readme = dest / "README.md"
    readme.write_text(patch_readme(readme.read_text()))

    # Public .gitignore: keep everything, drop the tracked-goldens prose
    # (no validation dir here), and ignore the directory outright so a
    # locally copied validation/ can never be committed by accident.
    gi = (dest / ".gitignore").read_text()
    gi += (
        "\n# --- not part of the public repository "
        "----------------------------------\n"
        "# The oracle validation suites live in the private development "
        "tree; if a\n# copy is placed here for local runs it must stay "
        "untracked.\nvalidation/\n"
    )
    (dest / ".gitignore").write_text(gi)

    version = (DEV / "drylab/__init__.py").read_text().split(
        '__version__ = "')[1].split('"')[0]

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=dest, check=True,
                       capture_output=True)

    if not updating:
        git("init", "-b", "main")
        git("config", "user.name", "drylab")
        git("config", "user.email", "dev@drylab.local")
    git("add", "-A")
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"],
                            cwd=dest)
    if staged.returncode == 0:
        print(f"publication repo at {dest} already matches v{version}; "
              "nothing to commit")
        return 0
    git("commit", "-m",
        f"drylab v{version} — public release\n\n"
        "Built from the development tree by tools/build_publish_repo.py.\n"
        "Excluded from the public repository:\n"
        + "".join(f"  - {n}\n" for n in EXCLUDE_NOTE))

    print(f"publication repo {'updated' if updating else 'built'} at "
          f"{dest} (v{version})")
    print("verify: cd there, run python tools/build_wasm_notebook.py, "
          "expect a clean tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
