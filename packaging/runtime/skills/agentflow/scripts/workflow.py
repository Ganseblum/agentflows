#!/usr/bin/env python3
"""Portable evidence commands for the host-native Agentflow workflow."""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from workflow_lib.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
