# sponsor-access

GitHub Sponsors of kizuna-intelligence get access to gated Hugging Face repos (now: `kizuna-intelligence/mame-tts`, $5/month or more). Every 15 minutes, `sponsor_access.py` accepts pending access requests from sponsors and moves requests of former sponsors back to pending.

A request is accepted when the GitHub account written in the request form sponsors kizuna-intelligence at the repo's minimum monthly amount, and no other Hugging Face account already holds access through that GitHub account (one Hugging Face account per sponsorship). If a sponsor finds their GitHub account already taken, fix it by hand on the repo's access requests page.

## Secrets

- `SPONSORS_GH_TOKEN`: GitHub token of an owner of kizuna-intelligence that can read the organization's sponsorships (classic token with `read:org` and `read:user`).
- `HF_TOKEN`: Hugging Face token with write access to the kizuna-intelligence organization (manages access requests).

This repository is public so that its Actions are free. Logs therefore show counts only, never who sponsors; the tokens live in Actions secrets.

Run locally: `GH_TOKEN=... HF_TOKEN=... python sponsor_access.py --dry-run`
