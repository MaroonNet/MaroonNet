# MaroonNet

Offline, mesh-networked search-and-rescue command post built on Meshtastic LoRa radios.
University of Colorado Denver senior capstone, Fall 2026 – Spring 2027.

> **Student prototype.** MaroonNet is not certified for life-safety use. Do not rely on it as a
> primary means of locating people.

## Structure

| Directory | What it holds | Who to ask |
|---|---|---|
| `backend/missiondb` | Mission data: what the radios reported, when, and the replay of it | Corey Greene |
| `backend/mapdb` | Maps, terrain and tiles the command post works on | Joshua "JJ" Wagner |
| `frontend/web` | The command post web application | Elijah Heimsoth |
| `frontend/mobile` | The field application | Diego Alas |
| `ml` | Lost-person probability modeling | Joshua "JJ" Wagner |

Other `backend/` subfolders are added as the work needs them. The repository holds code; design
documents and notes live with their authors and are shared in the team's Discord. Claude Code
reads `CLAUDE.md` for the rules it follows here.

## Working on the repository

1. Branch from an up-to-date `main`. Nobody pushes to `main`.
2. Commit your own work, signed. Claude may draft and explain; a teammate commits.
3. Open a pull request with two or three sentences on what changed. Two teammates approve.
   Squash-merge.

Before your first commit, set up signing once (the ruleset requires signed commits):

```bash
git config --global user.name  "Your Name"
git config --global user.email "<an email verified on your GitHub account>"
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub     # ssh-keygen -t ed25519 if you have no key
git config --global commit.gpgsign true
gh ssh-key add ~/.ssh/id_ed25519.pub --type signing --title "<machine> signing"
```

(Or GitHub → Settings → SSH and GPG keys → New SSH key → Key type **Signing Key**.)

## License

GPL-3.0. See `LICENSE`. The Meshtastic firmware and Python library are GPL-3.0; the same
license keeps MaroonNet compatible with them.

## Team

Diego Alas, Corey Greene, Elijah Heimsoth and Joshua "JJ" Wagner, advised by Professor David
Ogle, University of Colorado Denver.
