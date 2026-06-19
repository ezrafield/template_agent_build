# Publishing a live VPS project directory to GitHub

Use when a user provides SSH credentials and asks to push an existing server folder to a GitHub repository.

## Checklist

1. SSH in and identify the exact source directory.
   - Prefer explicit paths such as `/opt/router` once verified.
   - Check `git --version`, `python3 --version`, and whether the directory already has `.git`.

2. Harden `.gitignore` before staging.
   Add/verify patterns for:
   - `.env`, `.env.*`, `*.env`
   - `*.db`, `*.sqlite`, `*.sqlite3`, app data dirs such as `data/`
   - `logs/`, `*.log`
   - `.venv/`, `node_modules/`, `.next/`, build/cache dirs
   - backup folders/files (`*.bak`, `*.backup`, timestamped backup dirs)
   - any discovered source/config file containing real OAuth client secrets or hardcoded tokens

3. Initialize repo safely.

```bash
cd /path/to/project
git init -b main || git branch -M main
git config --global --add safe.directory /path/to/project  # if Git reports dubious ownership
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/OWNER/REPO.git
```

4. Verify ignored sensitive/runtime files.

```bash
git check-ignore -v .env .env.local router.db data/router.db .venv node_modules .next 2>/dev/null || true
git status --short --ignored | sed -n '1,200p'
```

5. Stage and scan staged content.

Recommended minimum staged scan categories:
- `github_pat_...`
- `sk-...` provider keys
- `-----BEGIN ... PRIVATE KEY-----`
- obvious real OAuth/client secrets (manual inspection; broad `token` scans are noisy in source trees)

If a real secret is staged, add it to `.gitignore`, `git reset`, then re-stage.

6. Commit.

```bash
git add .
git commit -m "Initial commit"
```

7. Push with a PAT without persisting it on the VPS.

```bash
auth=$(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 -w0)
git -c http.https://github.com/.extraheader="AUTHORIZATION: basic $auth" push -u origin main
```

## GitHub permission failure shape

If repo creation fails:

```text
403 Resource not accessible by personal access token
```

The token can authenticate but lacks repo-creation/admin permission.

If push fails:

```text
remote: Write access to repository not granted.
fatal: unable to access 'https://github.com/OWNER/REPO.git/': The requested URL returned error: 403
```

The token lacks write access to that repo. Ask the user to create the repo or grant a fine-grained PAT `Contents: Read and write` for the repo. For private repos or org repos, also ensure the token can see the target owner/repo.

If repo check returns 404, distinguish:
- repo truly does not exist, or
- token cannot see the repo.

Check both authenticated and unauthenticated API responses before concluding.
