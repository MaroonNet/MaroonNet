# MaroonNet — GitHub and local git setup guide

Written for Corey to run once. Time budget: about 45 minutes, most of it clicking through settings.
Every step says whether it is terminal, browser, or Claude Code.

## 0. Decisions to make before you start

**Organization vs. personal repo.** Create a free GitHub *organization* (for example `maroonnet`)
and put the repo under it rather than under your personal account. Reasons: the repo survives if
any one of you leaves or graduates; all four of you can be Owners so no single person is a
bottleneck; the URL (`github.com/maroonnet/MaroonNet`) reads like a real project on a resume and to
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
Name it `maroonnet` (or whatever you settle on; renaming an org later is possible but annoying).
Invite JJ, Elijah, and Diego as **Owners** (Settings > People > Invite member, role Owner).

Terminal, from the folder where you unzipped the starter:

```bash
cd ~/workspace
mv ~/Downloads/maroonnet-starter ~/workspace/maroonnet   # or wherever you unzipped it
cd ~/workspace/maroonnet
git init
git add -A
git commit -m "chore: initial repository scaffold"
gh repo create maroonnet/MaroonNet --public --source=. --remote=origin --push \
  --description "Open-source location tracking and after-action replay for Search & Rescue over LoRa/Meshtastic mesh"
```

Before `git add -A`, open `.github/CODEOWNERS` and replace the placeholder handles with everyone's
real GitHub usernames.

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
  maroonnet/    this repo (one clone; branches, not copies)
```

One clone, many branches. Do not keep separate folders per feature. The rhythm:

```bash
cd ~/workspace/maroonnet
git switch main && git pull
git switch -c feat/thing
# work, commit in small steps
git push -u origin feat/thing
gh pr create --fill
# after review + merge:
git switch main && git pull && git branch -d feat/thing
```

If you want to work on two branches at once without stashing, use worktrees rather than a second
clone: `git worktree add ../maroonnet-wt-fix fix/thing`. Claude Code has an `EnterWorktree` flow
that does this for you.

## 6. Claude Code on the repo (terminal, inside the repo)

- `CLAUDE.md` is loaded automatically. Run `/context` in a session and confirm it appears under
  *Memory files*.
- `.claude/settings.json` is committed and enables the `github`, `commit-commands`,
  `pr-review-toolkit`, `security-guidance`, and `pyright-lsp` plugins for everyone who trusts the
  folder. Each teammate will be prompted to install them the first time; accept. `pyright-lsp` needs
  `pip install pyright` (or `uv tool install pyright`) on each machine.
- The same file denies force-pushes, direct pushes to main, and reads of `.env`/key files from
  inside Claude Code, as a belt to the ruleset's suspenders.
- Personal preferences go in `CLAUDE.local.md` (gitignored) or `~/.claude/CLAUDE.md`, never in the
  shared `CLAUDE.md`.
- Run `/init` once after the first real code lands; it will suggest additions to `CLAUDE.md` based on
  the actual codebase. Review its suggestions in a PR like anything else.

## 7. Things to do in the first week

- Replace the placeholder stack section in `CLAUDE.md` after Wednesday's meeting with Ogle, via PR.
- Write ADR 0001 (stack choice) and ADR 0002 (position-data retention and access) so the
  privacy posture is decided before the first ping is stored.
- Enable a GitHub Project board (Projects tab > New project > Board) with columns Backlog / This
  week / In review / Done, and have Diego link it in the minutes.
- Create a `.env.example` when the first config value appears, and never a `.env`.
