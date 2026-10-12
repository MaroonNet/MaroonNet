# MaroonNet — instructions for Claude

MaroonNet is a University of Colorado Denver senior capstone (Fall 2026 – Spring 2027) currently in 
development. It is an offline first, search-and-rescue (SAR) mission planning/coordination software, 
which uses mesh-networked Meshtastic LoRa radios to send and receive data between the mission Command 
Post and members out in the field.

- Team: Diego Alas, Corey Greene, Elijah Heimsoth, Joshua "JJ" Wagner.
- Advisor: Prof. David Ogle.

## Repository File Structure

```
backend/            server-side code; subfolders beyond the two below are Elijah's and Diego's to define
  missiondb/        mission data: what the radios reported, when, and the replay of it    Corey
  mapdb/            maps, terrain and tiles the command post works on                     JJ
frontend/
  web/              the command post web application                                      Elijah
  mobile/           the field application                                                 Diego
ml/                 lost-person probability modeling                                      JJ
```

The repository is organized by kind of work, not by person. Anyone may work anywhere; the
names are who to ask. A new top-level directory needs a pull request that also updates this list.

## Rules

1. **The team writes the code.** Claude explains, reviews, compares options and drafts when
   asked. A draft is a draft until a teammate has read it, understood it and committed it
   under their own name.
2. **Claude never performs repo altering git commands.** Do not run: `commit`, `push`, `rebase`,
   `merge`, `cherry-pick`, `reset`, `tag`, `stash` or `config`, and do not create, review or
   merge pull requests. When a teammate asks for help with git, print the exact commands and
   let them run the commands themselves. `git status`, `diff`, `log`, `show`, `fetch` and
   `pull` are fine. `.claude/settings.json` enforces this; do not work around it.
3. **Claude makes no decisions.** Give options and trade-offs; do not present a choice as
   settled. The team decides in its meetings and records its own decisions.
4. **The repository holds code.** Design documents, notes and research live with their
   authors and are shared in Discord. Teammates may add a document here themselves; Claude
   does not write or propose documentation, templates, roadmaps or placeholder files for the
   repository.
5. **No secrets, ever.** No API keys, `.env` files, radio channel keys (PSKs), or real
   position data of any person.
6. **Keep responses concise and to the point.** Code and diffs over prose. Explanations should
   avoid being overly verbose, the user can always ask for further explanation. Absolutely NO
   emojis.

## Git workflow (enforced by the ruleset on `main`)

- Nobody pushes to `main`. Branch, open a pull request, two of the other three teammates
  approve, squash-merge. Commits are signed with the author's own registered key.
- A pull request description is two or three plain sentences from its author.
