from datetime import UTC, datetime

from specmeta_pipeline.config import Settings
from specmeta_pipeline.models import RunQuery
from specmeta_pipeline.providers.raiderio import RaiderIOProvider


class _UnusedClient:
    pass


def test_spec_leaderboard_rejects_mismatched_spec() -> None:
    provider = RaiderIOProvider(Settings(), _UnusedClient())  # type: ignore[arg-type]
    row = {
        "character": {
            "name": "Example", "level": 90,
            "region": {"slug": "eu"}, "realm": {"slug": "realm"},
            "spec": {"id": 577}, "talentLoadoutText": "A" * 30,
        },
        "runs": [{
            "keystoneRunId": 1, "mythicLevel": 15, "score": 400,
            "clearTimeMs": 1000, "parTimeMs": 2000,
        }],
    }
    request = RunQuery("season-mn-2", "eu", datetime.now(UTC))
    assert provider._parse_leaderboard_row(
        row, request, 1480, datetime.now(UTC),
    ) is None


def test_spec_leaderboard_preserves_complete_talent_code() -> None:
    provider = RaiderIOProvider(Settings(), _UnusedClient())  # type: ignore[arg-type]
    code = "CcQ" + "A" * 40
    row = {
        "character": {
            "name": "Example", "level": 90,
            "region": {"slug": "eu"}, "realm": {"slug": "realm"},
            "spec": {"id": 263}, "talentLoadoutText": code,
        },
        "runs": [{
            "keystoneRunId": 7, "mythicLevel": 16, "score": 425,
            "clearTimeMs": 1000, "parTimeMs": 2000,
        }],
    }
    request = RunQuery("season-mn-2", "eu", datetime.now(UTC))
    parsed = provider._parse_leaderboard_row(
        row, request, 263, datetime.now(UTC),
    )
    assert parsed is not None
    assert parsed.members[0].talent_import == code
    assert parsed.members[0].spec_id == 263
