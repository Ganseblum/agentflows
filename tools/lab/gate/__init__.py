"""Gate check modules for validate.py (T02 split, feature-2026-10-13-质量提升)."""

from __future__ import annotations

import sys
from pathlib import Path

# The sibling lab modules (artifact_digest, doc_chain, ...) are flat modules next to this
# package; keep tools/lab importable so a gate module can import them directly.
_LAB = Path(__file__).resolve().parent.parent
if str(_LAB) not in sys.path:
    sys.path.insert(0, str(_LAB))
