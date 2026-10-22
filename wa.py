#!/usr/bin/env python3
"""Punto de entrada: python wa.py <comando>  (los lanzadores `wa`, `wa.cmd`, `wa.ps1` lo usan)."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wa_proxy.cli import main  # noqa: E402

sys.exit(main())
