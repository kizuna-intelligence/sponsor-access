"""Withdraw Hugging Face access from those who stop sponsoring kizuna-intelligence on GitHub.

Sponsors get access on https://kizuna-intelligence.com/sponsors/mame-tts by signing in with GitHub and with Hugging
Face; that page records which Hugging Face account each GitHub login linked in the private dataset MAP. Every run
moves the access of a Hugging Face account back to pending when no GitHub login linked to it sponsors at the repo's
minimum any more, so sponsoring again and getting access on that page restores it.

    GH_TOKEN=... HF_TOKEN=... python sponsor_access.py [--dry-run]
"""
import json
import os
import sys
import urllib.request

from huggingface_hub import HfApi

ORG = "kizuna-intelligence"
REPOS = {"kizuna-intelligence/mame-tts": 5}  # gated Hugging Face repo -> minimum monthly amount in USD
MAP = "kizuna-intelligence/sponsor-access-map"  # dataset with map.json: GitHub login -> Hugging Face user
KEEP = {"yusuke-ai"}  # Hugging Face users granted by hand; never withdrawn


def graphql(query, **variables):
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}"})
    out = json.load(urllib.request.urlopen(req))
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def sponsors():
    """GitHub login (lowercase) -> monthly amount in USD, for active sponsorships by users."""
    amounts, cursor = {}, None
    while True:
        page = graphql("""query($org: String!, $after: String) { organization(login: $org) {
            sponsorshipsAsMaintainer(first: 100, after: $after, activeOnly: true) {
              pageInfo { hasNextPage endCursor }
              nodes { sponsorEntity { ... on User { login } } tier { monthlyPriceInDollars } } } } }""",
                       org=ORG, after=cursor)["organization"]["sponsorshipsAsMaintainer"]
        for n in page["nodes"]:
            login = (n["sponsorEntity"] or {}).get("login")
            if login:
                amounts[login.lower()] = max(amounts.get(login.lower(), 0), n["tier"]["monthlyPriceInDollars"])
        if not page["pageInfo"]["hasNextPage"]:
            return amounts
        cursor = page["pageInfo"]["endCursor"]


def main(dry_run):
    """Logs are public (this repository is public), so they carry counts only, never who sponsors."""
    api, paid = HfApi(), sponsors()
    links = json.load(open(api.hf_hub_download(MAP, "map.json", repo_type="dataset", force_download=True)))
    for repo, minimum in REPOS.items():
        eligible = {login for login, amount in paid.items() if amount >= minimum}
        keep = KEEP | {user for login, user in links.items() if login in eligible}
        accepted = {r.username for r in api.list_accepted_access_requests(repo)}
        withdrawn = failed = 0
        for user in sorted(set(links.values()) & accepted - keep):
            try:
                if not dry_run:
                    api.cancel_access_request(repo, user)
                withdrawn += 1
            except Exception:
                failed += 1
        print(f"{repo}: {len(eligible)} eligible sponsors, {len(links)} links, withdrew {withdrawn}, failed {failed}")
        if failed:
            sys.exit(1)


if __name__ == "__main__":
    main("--dry-run" in sys.argv)
