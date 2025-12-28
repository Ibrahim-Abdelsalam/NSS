import re

def scan_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    print(f"Scanning {filepath} ({len(lines)} lines)...")
    
    for i, line in enumerate(lines):
        line_num = i + 1
        strip = line.strip()
        
        # Detect Section Headers
        if strip.startswith("# ===") or strip.startswith("# ---"):
            if "CONSTRAINT" in strip or "OBJECTIVE" in strip or "VAR" in strip:
                print(f"Line {line_num}: HEADER {strip}")
                # Print next few lines to see title
                if i+1 < len(lines): print(f"  > {lines[i+1].strip()}")
        
        # Detect Definitions
        if strip.startswith("def ") or strip.startswith("class "):
            print(f"Line {line_num}: DEF {strip.split('(')[0]}")
            
        # Detect Variable Blocks
        if "LpVariable.dicts" in strip:
            print(f"Line {line_num}: VAR {strip.split('=')[0].strip()}")

scan_file("/Users/ibrahim/Documents/GitHub/NSS/model.py")
