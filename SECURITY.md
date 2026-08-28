# Security

MaroonNet handles the real-time positions of people in the field. Treat that data as sensitive.

If you find a vulnerability, do not open a public issue. Use GitHub's private vulnerability
reporting on this repository (Security tab > Report a vulnerability), or contact a maintainer
directly on the team Discord.

Rules we hold ourselves to:

- No secrets in git, ever. Channel keys, API tokens, and `.env` files stay out of the repo.
  `secrets-scan` in CI and a pre-commit hook back this up.
- No public network endpoint without authentication.
- Store the minimum position data needed and document retention in an ADR.
- Dependencies are pinned and Dependabot is enabled.
