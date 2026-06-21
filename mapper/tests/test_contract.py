"""Guards against schema drift: the bundled copy must match the canonical contract."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL = REPO_ROOT / "schemas" / "event.schema.json"
BUNDLED = REPO_ROOT / "mapper" / "mapper" / "event.schema.json"


def test_bundled_schema_matches_canonical():
    assert json.loads(BUNDLED.read_text()) == json.loads(CANONICAL.read_text())
