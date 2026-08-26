# Publishing to PyPI

Package name: **onepaste** (import name stays `onepaste`, command stays `onepaste`).

## One-time setup (manual first release)

1. Register at <https://pypi.org/account/register/> and verify your email.
2. Create an API token: <https://pypi.org/manage/account/token/>
   - Scope: "Entire account" (project-scoped tokens become available after the first upload).
3. Upload the built artifacts:

   ```bash
   .venv/bin/twine upload dist/*
   # Username: __token__
   # Password: pypi-... (paste your token)
   ```

4. Verify from a clean environment:

   ```bash
   pipx install onepaste
   onepaste --version   # OnePaste v1.3.0
   ```

## Subsequent releases (GitHub Actions, zero tokens)

Uses PyPI Trusted Publishing (OIDC) — no secrets stored in GitHub.

1. On PyPI: your project → *Settings* → *Publishing* → add a **Trusted Publisher**:
   - Owner: `emVisible`  Repo: `OnePaste`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi`
2. Release: create a GitHub *Release* (or run the workflow manually via `workflow_dispatch`).
   Alternatively: `git tag vX.Y.Z && git push origin vX.Y.Z` triggers the same workflow.

The workflow runs tests, builds, twine-checks, then publishes.

## Bump a version

1. `pyproject.toml` → `version`
2. `onepaste/__init__.py` → `__version__` (a test enforces both match)
3. Commit + GitHub Release with tag `vX.Y.Z`
