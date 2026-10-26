#!/usr/bin/env python3
"""Deterministic cross-closure linter for feature document chains — thin launcher.

The implementation lives in the ``docchain`` package (tools/lab/docchain/):
constants, checks, self-test, and the CLI. This file only preserves the
historical ``python3 tools/lab/doc_chain.py ...`` entry point and the
``import doc_chain`` namespace the gate and its tests rely on.

See tools/lab/docchain/constants.py for the full check catalogue (C1–C24) and
usage, which is unchanged from the original monolith.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the sibling package importable even when this file is copied standalone into
# a temporary tree (validate_doc_chain_live's self-test does exactly that), so the
# subprocess re-invocation of this launcher still resolves the docchain package.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from docchain import *
from docchain import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
