# Contributing to MaroonNet

## Workflow in one screen

```bash
git switch main && git pull                 # always start from current main
git switch -c feat/short-description        # feat/ fix/ docs/ chore/ test/ refactor/
# ... make changes ...
uv run ruff check . && uv run ruff format . # lint + format
uv run pytest                               # tests
git add -p && git commit                    # Conventional Commit message
git push -u origin feat/short-description
gh pr create --fill                         # or open the PR in the browser
```

Then request review. A PR merges only when:

- two of the three teammates who did not write it have approved,
- the `lint`, `test`, and `secrets-scan` checks are green,
- every review thread is resolved, and
- the branch is up to date with `main`.

Merges are squash-only. The PR title becomes the commit message on `main`, so write it as a
Conventional Commit line (`feat: live map shows searcher pings`).

## Commit messages

```
type: short imperative summary (72 chars max)

Optional body explaining why, not what. Wrap at 72.

Refs #12
```

Types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`.

## Things that will get a PR sent back

- Secrets, `.env` files, Meshtastic channel PSKs, or personal contact details for outreach targets.
- Real location data from a person who has not agreed to it being in a public repo.
- A convention, command, or directory changed without updating `CLAUDE.md` / README / ADR.
- No tests for new behavior.
- Unrelated reformatting mixed into a functional change.

## Decisions

Anything that would be painful to reverse (stack, schema, data retention, protocol choices) gets an
Architecture Decision Record in `docs/adr/` before code lands. Copy `docs/adr/0000-template.md`.

## Signing commits

`main` requires signed commits. SSH signing takes two minutes:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

Then add the same public key on GitHub under Settings > SSH and GPG keys as a **Signing Key**
(separately from the Authentication Key, even if it is the same key).
