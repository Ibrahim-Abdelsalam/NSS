#!/usr/bin/env python
"""Simple runner script to avoid terminal issues"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, 'test_fatigue_basic.py'],
    cwd='/Users/ibrahim/Documents/GitHub/NSS',
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
