# Fine-grained PATs for private organization repos

Use this when a private organization repo was created for a user, invitations were accepted, but API/git access still returns 404/403.

## Symptom pattern

- `GET /user` succeeds and shows the expected GitHub user.
- `GET /user/repository_invitations` returns `[]`, so there is no pending invitation to accept.
- `GET /user/repos?affiliation=owner,collaborator,organization_member` lists the user's repos and some collaborator repos, but no repos from the target org.
- `GET /repos/ORG/REPO` returns 404.
- `GET /repos/ORG/REPO/contents` returns 404, but response headers may include `x-accepted-github-permissions: contents=read`.
- `git clone` may say either `Repository not found` or `Write access to repository not granted`.

This usually means the token is valid and has the right permission *types*, but the repo is not in the token's resource/installation scope.

## Root cause

Fine-grained PAT repository access is scoped by **Resource owner** first. Selecting “All repositories” under resource owner `USER` does not include private repos owned by organization `ORG`, even when `USER` is a collaborator on that repo.

For a repo like `GPNCTF24/91625365_Enzosama_food-poisoning-challenge`, a fine-grained PAT whose resource owner is `Enzosama` and access is “All repositories” will still not see the `GPNCTF24` repo.

## Correct fix

Ask the user to create/update a token with:

1. Resource owner: the organization that owns the repo, e.g. `GPNCTF24`.
2. Repository access: the exact repo, or all repositories under that organization.
3. Permissions as needed:
   - Metadata: read (default)
   - Contents: read for inspection/clone; read/write if pushing exploit changes
   - Actions: read for workflow inspection; read/write if dispatching/rerunning workflows
   - Pull requests: read/write only if the workflow requires PR-based triggering

If GitHub does not allow selecting the organization as Resource owner, the organization likely disallows fine-grained PAT access. Use a classic PAT instead.

## Classic PAT fallback

Create a classic token with:

- `repo`
- `workflow` if manipulating GitHub Actions

If GitHub shows “Configure SSO” or “Authorize” for the organization, the user must authorize the token for that org before API/git access works.

## Verification probes

Use the token without printing it:

```bash
curl -sS -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user

curl -sS -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/user/repos?per_page=100&affiliation=owner,collaborator,organization_member"

curl -sS -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/ORG/REPO
```

If `/user` works but `/repos/ORG/REPO` is 404 and the repo is absent from `/user/repos`, do not keep retrying clone. Fix token resource owner/scope first.
