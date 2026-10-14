"""Grant GitHub Sponsors of kizuna-intelligence access to gated Hugging Face repos, and withdraw it when they stop.

A Hugging Face access request names a GitHub account. It is accepted when that account is an active sponsor at the
repo's minimum monthly amount and no other Hugging Face account already holds access through it: each sponsorship
grants one Hugging Face account, so naming someone else's GitHub account gets nothing once its owner is in.
An accepted request whose sponsor has left goes back to pending, so sponsoring again restores access on the next run.

    GH_TOKEN=... HF_TOKEN=... python sponsor_access.py [--dry-run]
"""
import json
import os
import sys
import urllib.request

from huggingface_hub import HfApi

ORG = "kizuna-intelligence"
REPOS = {"kizuna-intelligence/mame-tts": 5}  # gated Hugging Face repo -> minimum monthly amount in USD
FIELD = "GitHub username"
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


def github_login(request):
    return (request.fields or {}).get(FIELD, "").strip().lstrip("@").lower()


def main(dry_run):
    """Logs are public (this repository is public), so they carry counts only, never who sponsors."""
    api, paid = HfApi(), sponsors()
    for repo, minimum in REPOS.items():
        eligible = {login for login, amount in paid.items() if amount >= minimum}
        accepted = withdrawn = failed = 0
        holders = {github_login(r) for r in api.list_accepted_access_requests(repo)}
        for r in api.list_pending_access_requests(repo):
            login = github_login(r)
            try:
                if login in eligible and login not in holders:
                    holders.add(login)
                    if not dry_run:
                        api.accept_access_request(repo, r.username)
                    accepted += 1
            except Exception:
                failed += 1
        for r in api.list_accepted_access_requests(repo):
            login = github_login(r)
            if r.username not in KEEP and login and login not in eligible:
                try:
                    if not dry_run:
                        api.cancel_access_request(repo, r.username)
                    withdrawn += 1
                except Exception:
                    failed += 1
        print(f"{repo}: {len(eligible)} eligible sponsors, accepted {accepted}, withdrew {withdrawn}, failed {failed}")
        if failed:
            sys.exit(1)


if __name__ == "__main__":
    main("--dry-run" in sys.argv)
