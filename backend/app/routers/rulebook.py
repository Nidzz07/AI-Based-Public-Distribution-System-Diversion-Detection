"""Rulebook endpoint — F2 surface.

Reads through engine/rulebook.load() at request time, so an officer editing
rules.yaml sees the change on the next refresh without a restart and without a
code change. That is the feature, not a convenience: the thresholds belong to
the district supply office.

The parsed YAML is returned as-is rather than through a response model. A
response model would pin the rulebook's shape in Python, which is exactly the
coupling this feature exists to avoid — add a field to the YAML and it should
reach the screen on its own.
"""

from fastapi import APIRouter

from ..engine.rulebook import load

router = APIRouter(prefix="/rulebook", tags=["rulebook"])


@router.get("")
def get_rulebook():
    """The rulebook in force: version, updated_by, severity bands and rules."""
    return load()
