"""Validate events against the shared JSON-Schema contract.

The schema is the single source of truth shared by the adapter, mapper and the contract
test. It is loaded from `schemas/event.schema.json` (bundled into the image at build).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

# Default to a copy bundled next to the package; overridable for tests.
SCHEMA_PATH = Path(__file__).resolve().parent / "event.schema.json"


@lru_cache(maxsize=1)
def _validator(path: str = str(SCHEMA_PATH)) -> Draft202012Validator:
    schema = json.loads(Path(path).read_text())
    return Draft202012Validator(schema)


class ValidationError(ValueError):
    """Raised when an event does not satisfy the contract."""


def validate_event(event: dict[str, Any], schema_path: str | None = None) -> None:
    validator = _validator(schema_path) if schema_path else _validator()
    errors = sorted(validator.iter_errors(event), key=lambda e: e.path)
    if errors:
        msgs = "; ".join(e.message for e in errors)
        raise ValidationError(msgs)
