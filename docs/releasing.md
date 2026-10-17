# Releasing

Releases are published to PyPI by GitHub Actions when a version tag is pushed. The workflow
([release.yml](../.github/workflows/release.yml)) checks the tag matches `pyproject.toml`, runs the
tests, builds the package, installs the wheel in a clean environment and renders an example, then
publishes to PyPI and creates a GitHub release.

## One-off setup

1. On [pypi.org](https://pypi.org), sign in and open **Your projects → Publishing → Add a new
   pending publisher** with:
   - PyPI project name: `brandpdf`
   - Owner: `faisal-pm`
   - Repository name: `Branded-PDF-Generator`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
2. On GitHub, open **Settings → Environments → New environment**, name it `pypi`, and optionally
   add yourself as a required reviewer so each publish waits for your approval.

## Each release

1. Set `version` in `pyproject.toml` and run `uv lock`.
2. In `CHANGELOG.md`, replace `Unreleased` with today's date.
3. Commit, then tag and push:

   ```sh
   git tag v1.0.0
   git push origin main v1.0.0
   ```

4. Watch the **Release** workflow. When it finishes, check
   `pip install brandpdf` in a fresh virtualenv.

A version can only be uploaded to PyPI once. If something is wrong after publishing, fix it and
release the next patch version.
