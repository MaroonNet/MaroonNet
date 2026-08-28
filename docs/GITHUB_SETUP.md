# MaroonNet — GitHub and local git setup guide

Written for Corey to run once. Time budget: about 45 minutes, most of it clicking through settings.
Every step says whether it is terminal, browser, or Claude Code.

## 0. Decisions to make before you start

**Organization vs. personal repo.** Create a free GitHub *organization* (for example `maroonnet`)
and put the repo under it rather than under your personal account. Reasons: the repo survives if
any one of you leaves or graduates; all four of you can be Owners so no single person is a
bottleneck; the URL (`github.com/maroonnet/maroonnet`) reads like a real project on a resume and to
the SAR teams you are emailing. Free orgs get rulesets on public repos, which is exactly what you
need. Add Ogle as an outside collaborator with read access if he wants to watch.

**Public from day one.** Rulesets and most security features are free only on public repos. The
project is open source anyway. Just make sure nothing sensitive is in the first commit.

**License: GPL-3.0.** The Meshtastic firmware and the `meshtastic` Python library are both
GPL-3.0. If the backend imports that library, MIT/Apache would create a license conflict the moment
you distribute. GPL-3.0 keeps you compatible and keeps anyone who forks the project obligated to
stay open, which matches the spirit of building this for volunteer teams. The `LICENSE` file in the
starter is the SPDX GPL-3.0 text.

## 1. Prerequisites on your Mac (terminal)

```bash
brew install gh uv pre-commit
gh auth login          # choose GitHub.com, HTTPS or SSH, log in via browser
git config --global user.name "Corey <Lastname>"
git config --global user.email "<the email on your GitHub account>"
git config --global init.defaultBranch main
git config --global pull.rebase true
```

Set up SSH commit signing now so the "require signed commits" rule never bites you:

```bash
ls ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519 -C "<your email>"
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
gh ssh-key add ~/.ssh/id_ed25519.pub --type signing --title "macbook-air signing"
```

Each teammate does the same block on their own machine.

## 2. Create the organization and repo (browser + terminal)

Browser: github.com > your avatar > **Your organizations** > **New organization** > Free.
Name it `maroonnet` (fall back to `maroonnet-sar` if taken). Renaming an org later is possible but annoying.
Invite JJ, Elijah, and Diego as **Owners** (Settings > People > Invite member, role Owner).

Terminal, from the folder where you unzipped the starter:

```bash
cd ~/workspace
mv ~/Downloads/maroonnet-starter ~/workspace/maroonnet   # or wherever you unzipped it
cd ~/workspace/maroonnet
git init
git add -A
git commit -m "chore: initial repository scaffold"
gh repo create maroonnet/maroonnet --public --source=. --remote=origin --push \
  --description "Offline SAR mesh command post on Meshtastic: live POD, terrain-aware coverage, topology risk, replay, CalTopo interop"
```

Before `git add -A`: open `.github/CODEOWNERS` and replace the placeholder handles with everyone's
real GitHub usernames, and drop JJ's Project Bible PDF (and the SOW) into `docs/bible/`.

## 3. Repository settings (browser, Settings tab of the repo)

**General**

- Features: turn on Issues, Discussions (nice for design threads), Projects. Turn off Wiki (use
  `docs/` instead so documentation goes through review).
- Pull Requests: uncheck *Allow merge commits* and *Allow rebase merging*, leave only *Allow squash
  merging*, and set the default squash message to **Pull request title and description**.
  Check *Always suggest updating pull request branches* and *Automatically delete head branches*.

**Rules > Rulesets**

- Click **New ruleset** > **Import a ruleset**, pick `.github/rulesets/main-protection.json` from the
  starter, and save. It targets the default branch and does all of the following:
  restrict deletions; block force pushes; require linear history; require signed commits; require a
  pull request with **2 approvals**, approvals dismissed when new commits are pushed, approval
  required on the most recent push, all review threads resolved, squash merge only; and require the
  `lint` and `test` status checks with the branch up to date with `main`.
- The **bypass list is empty on purpose.** Repository admins are subject to the ruleset unless you
  add them to the bypass list, so leave it empty. If you ever truly need to bypass (e.g., a broken CI
  config), an Owner can temporarily set the ruleset to *Disabled*, fix, and re-enable. That is a
  visible, auditable act, which is the point.
- GitHub already refuses to count the PR author's own approval, so "2 approvals" automatically means
  2 of the 3 teammates who did not write the change.
- Add a second ruleset later if you want to protect `release/*` branches the same way.

Why rulesets and not the older "branch protection rules": rulesets are what GitHub now develops,
they can be imported/exported as JSON (so the config lives in the repo), they layer, and they apply
to admins by default.

**Code security**

- Enable **Dependabot alerts**, **Dependabot security updates**, and **Dependabot version updates**
  (it will offer to create `.github/dependabot.yml`; accept, weekly interval, `pip` and
  `github-actions` ecosystems).
- Enable **Secret scanning** and **Push protection**. Push protection blocks a push that contains
  a known secret pattern before it lands. Free on public repos.
- Enable **Private vulnerability reporting** so `SECURITY.md` has somewhere to point.
- Enable **CodeQL** default setup for Python and JavaScript once there is real code.

**Actions > General**

- Workflow permissions: **Read repository contents and packages permissions** (least privilege).
  The CI workflow declares its own `permissions: contents: read`.
- Leave *Allow GitHub Actions to create and approve pull requests* unchecked.

**Collaborators and teams**

- Everyone on the project is an org Owner. Nobody else gets write. Ogle: outside collaborator, Read.

## 4. First run of CI and the status-check names

The ruleset requires checks named `lint` and `test`. Those names come from the `name:` fields of
the jobs in `.github/workflows/ci.yml`. GitHub will not let you select a status check in the UI
until it has run at least once, but importing the JSON sets it directly. Push one small PR to
confirm the checks appear and block the merge until green.

If you rename a job, update the ruleset JSON and re-import, or edit the ruleset in the UI.

## 5. Local layout and daily flow (terminal)

```
~/workspace/
  mach/         internship
  bootdotdev/   personal training
  maroonnet/     this repo (one clone; branches, not copies)
```

One clone, many branches. Do not keep separate folders per feature. The rhythm:

```bash
cd ~/workspace/maroonnet
git switch main && git pull
git switch -c feature/thing
# work, commit in small steps
git push -u origin feature/thing
gh pr create --fill
# after review + merge:
git switch main && git pull && git branch -d feature/thing
```

If you want to work on two branches at once without stashing, use worktrees rather than a second
clone: `git worktree add ../maroonnet-wt-fix fix/thing`. Claude Code has an `EnterWorktree` flow
that does this for you.

## 6. Claude Code on the repo (terminal, inside the repo)

- `CLAUDE.md` is loaded automatically. Run `/context` in a session and confirm it appears under
  *Memory files*.
- `.claude/settings.json` is committed and enables the `github`, `commit-commands`,
  `pr-review-toolkit`, `security-guidance`, `pyright-lsp`, and `typescript-lsp` plugins for everyone who trusts the
  folder. Each teammate will be prompted to install them the first time; accept. `pyright-lsp` needs
  `uv tool install pyright` and `typescript-lsp` needs `npm i -g typescript-language-server typescript`
  on each machine.
- The same file denies force-pushes, direct pushes to main, and reads of `.env`/key files from
  inside Claude Code, as a belt to the ruleset's suspenders.
- Personal preferences go in `CLAUDE.local.md` (gitignored) or `~/.claude/CLAUDE.md`, never in the
  shared `CLAUDE.md`.
- Run `/init` once after the first real code lands; it will suggest additions to `CLAUDE.md` based on
  the actual codebase. Review its suggestions in a PR like anything else.

## 7. GitHub to Discord

Two layers, because Discord's built-in GitHub renderer covers most events but silently drops CI
results (`workflow_run` returns 204 and never shows), and it cannot @mention anyone.

**Layer 1: native webhook (5 minutes).** In Discord: channel settings > Integrations > Webhooks >
New Webhook, name it `GitHub`, copy the URL. In GitHub: repo Settings > Webhooks > Add webhook.
Payload URL is the Discord URL **with `/github` appended**; content type `application/json`; leave
the secret blank; choose *Let me select individual events* and tick Pull requests, Pull request
reviews, Pull request review comments, Issues, Issue comments, Pushes, Releases. Discord renders
these as embeds. Do not tick Check runs, Check suites, or Workflow runs; Discord accepts and drops them.

**Layer 2: `discord-notify.yml` (10 minutes).** It posts CI pass/fail after every run (with an
@mention of the author on failure) and @mentions each requested reviewer when a review is requested
or a draft is marked ready. Setup:

1. Create a second Discord webhook (or reuse the first) and copy the raw URL, **without** `/github`.
2. Repo Settings > Secrets and variables > Actions > **Secrets** > New repository secret:
   `DISCORD_WEBHOOK_URL` = that URL.
3. Same page > **Variables** > New repository variable: `DISCORD_USER_MAP` = JSON mapping GitHub
   logins to Discord user IDs, e.g. `{"coreygreene":"123456789012345678","jjwagner":"..."}`.
   Discord IDs: User Settings > Advanced > Developer Mode on, then right-click a member > Copy User ID.
4. Open a test PR and request a review; the mention should land within a minute.

Discord webhook URLs are secrets: anyone with one can post to the channel. Rotate the webhook if a
URL ever ends up in a commit or a screenshot.

## 8. Things to do in the first week

- Commit the Project Bible and SOW under `docs/bible/` (JJ) so `CLAUDE.md` can point at them.
- Open the first PR against `spec/`: interface spec v0.1 (schema with the full per-packet log fields,
  WebSocket message types, REST endpoints) before Monday, v1.0 merged by Friday (Bible §14.5). This is
  JJ's, but the repo has to exist first, so the org and ruleset come before the weekend.
- Add a decision-log row for position-data retention and access before the first packet is stored.
- Enable a GitHub Project board (Projects tab > New project > Board) with columns Backlog / Sprint /
  In progress / In review / Done; every card gets an owner, sprint, and gate label (Bible §14.4).
- Create a `.env.example` when the first config value appears, and never a `.env`.
