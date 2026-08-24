from __future__ import annotations

import os

import httpx


def main() -> int:
    client_id = os.environ["BLIZZARD_CLIENT_ID"]
    client_secret = os.environ["BLIZZARD_CLIENT_SECRET"]
    with httpx.Client(timeout=20.0) as client:
        token_response = client.post(
            "https://oauth.battle.net/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        print(f"oauth_status={token_response.status_code}")
        token_response.raise_for_status()
        token = token_response.json()["access_token"]
        stats_response = client.get(
            "https://us.api.blizzard.com/profile/wow/character/aerie-peak/swordish/statistics",
            params={"namespace": "profile-us", "locale": "en_US"},
            headers={"Authorization": f"Bearer {token}"},
        )
        print(f"statistics_status={stats_response.status_code}")
        if stats_response.is_success:
            payload = stats_response.json()
            print("statistics_keys=" + ",".join(sorted(payload)))
            for name in ("melee_crit", "melee_haste", "mastery", "versatility"):
                value = payload.get(name)
                detail = ",".join(sorted(value)) if isinstance(value, dict) else "scalar"
                print(f"{name}_shape={type(value).__name__}:{detail}")
        return 0 if stats_response.is_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
