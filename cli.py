#!/usr/bin/env python3
"""
CLI for FENa Calculator.
Delegates to fena.py for all calculations.
"""
import sys
from fena import main

if __name__ == "__main__":
    sys.exit(main())
