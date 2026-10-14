# sponsor-access

Sponsors of kizuna-intelligence ($5/month or more) get access to the gated Hugging Face repo `kizuna-intelligence/mame-tts` on https://kizuna-intelligence.com/sponsors/mame-tts by signing in with GitHub and with Hugging Face (code: `company/sponsors.py` in kizuna-intelligence-websites). That page records which Hugging Face account each GitHub login linked in the private dataset `kizuna-intelligence/sponsor-access-map`.

Every 15 minutes, `sponsor_access.py` moves the access of linked Hugging Face accounts whose sponsorship ended back to pending. Sponsoring again and visiting the page restores it.

This repository is public so that its Actions are free. Logs therefore show counts only, never who sponsors; the tokens live in Actions secrets.

## Secrets

- `SPONSORS_GH_TOKEN`: GitHub token of an owner of kizuna-intelligence that can read the organization's sponsorships (classic token with `read:org` and `read:user`).
- `HF_TOKEN`: Hugging Face token that can manage access requests of `kizuna-intelligence/mame-tts` and read `kizuna-intelligence/sponsor-access-map`.

Run locally: `GH_TOKEN=... HF_TOKEN=... python sponsor_access.py --dry-run`
