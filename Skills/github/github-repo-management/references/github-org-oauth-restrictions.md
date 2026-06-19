# GitHub org OAuth restrictions and private challenge repos

Use this when a private org repo invitation exists but `git clone`/REST access fails after accepting it.

## Symptom

A challenge/service creates a private repository in an organization and adds the user as a collaborator. The API may show a pending invitation under:

```bash
GET /user/repository_invitations
```

After accepting it with:

```bash
PATCH /user/repository_invitations/<invitation_id>
```

repo access can still fail:

- REST `GET /repos/ORG/REPO` returns 403 with a message like:
  `Although you appear to have the correct authorization credentials, the ORG organization has enabled OAuth App access restrictions...`
- `git clone https://github.com/ORG/REPO.git` returns `Repository not found` / HTTP 404.
- A different fine-grained PAT may return 404 if it is not explicitly scoped to this private repo.

## Root cause

GitHub org OAuth App access restrictions are separate from repository collaborator status. A classic OAuth-token credential can have `repo` scope and still be blocked from accessing an organization unless that OAuth app/token is authorized for the org. Git often masks this as `Repository not found`.

## Workflow

1. Confirm which identity the token belongs to:

```bash
curl -H "Authorization: Bearer $TOKEN" https://api.github.com/user
```

2. Check pending invitations:

```bash
curl -H "Authorization: Bearer $TOKEN" https://api.github.com/user/repository_invitations
```

3. Accept the invitation if present:

```bash
curl -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/user/repository_invitations/$INVITATION_ID
```

4. If repo access still returns an OAuth restriction 403, stop retrying clone/API with the same token. Use one of:
   - A token/OAuth app authorized for the organization.
   - A fine-grained PAT explicitly granted access to `ORG/REPO` with contents read/write as needed.
   - Browser/UI access under the signed-in GitHub account, then download/clone manually if the browser session is authorized.

## Pitfalls

- Do not confuse accepted collaborator invite with token authorization for the org.
- Do not keep retrying identical `git clone` commands after `Repository not found`; inspect REST status and headers/messages.
- Avoid printing tokens. Use credential helpers or transient headers when testing.
