import re

def scan_constraints(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    print(f"Scanning Constraints in {filepath}...")
    
    for i, line in enumerate(lines):
        line_num = i + 1
        strip = line.strip()
        
        # Detect Constraint Headers
        if "CONSTRAINT" in strip and "#" in strip:
            print(f"Line {line_num}: {strip}")
        
        if "prob +=" in strip and line_num > 660 and line_num < 1400:
             # Sample the constraint addition lines
             if "MinRegular" in lines[i+1] or "Strict" in lines[i+1]:
                 print(f"Line {line_num}: ADD CONSTRAINT 8 Logic")

scan_constraints("/Users/ibrahim/Documents/GitHub/NSS/model.py")
