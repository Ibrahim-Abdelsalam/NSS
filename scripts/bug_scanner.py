"""
Automated Bug Detection Script

Scans codebase for common bug patterns:
- Division by zero risks
- Null/None access
- Array out-of-bounds
- Type inconsistencies
- Missing validations

Run: python tests/bug_scanner.py
"""

import re
import os
from pathlib import Path


def scan_file_for_bugs(filepath):
    """Scan a Python file for potential bugs"""
    print(f"\n{'='*80}")
    print(f"Scanning: {filepath}")
    print('='*80)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    bugs_found = []
    
    # Pattern 1: Division without zero check
    for i, line in enumerate(lines, 1):
        if re.search(r'/\s*[a-zA-Z_\[\]\.]+', line) and 'http' not in line:
            if i > 1 and 'if' not in lines[i-2] and 'assert' not in lines[i-2]:
                # Check if there's a zero check nearby
                context = ''.join(lines[max(0, i-3):min(len(lines), i+2)])
                if '!= 0' not in context and '> 0' not in context and 'zero' not in context.lower():
                    bugs_found.append({
                        'line': i,
                        'type': 'Division Risk',
                        'severity': 'Medium',
                        'content': line.strip(),
                        'suggestion': 'Add zero check before division'
                    })
    
    # Pattern 2: Dictionary access without .get()
    for i, line in enumerate(lines, 1):
        if re.search(r'\w+\[[\'\"][\w_]+[\'\"]\]', line):
            # Check if it's in a try block
            in_try_block = False
            for j in range(max(0, i-10), i):
                if 'try:' in lines[j]:
                    in_try_block = True
                if 'except' in lines[j]:
                    in_try_block = False
            
            if not in_try_block and '.get(' not in line:
                bugs_found.append({
                    'line': i,
                    'type': 'Dictionary Access',
                    'severity': 'Low',
                    'content': line.strip(),
                    'suggestion': 'Consider using .get() or wrap in try-except'
                })
    
    # Pattern 3: Array indexing without bounds check
    for i, line in enumerate(lines, 1):
        if re.search(r'\w+\[\d+\]', line) and 'if len(' not in line:
            bugs_found.append({
                'line': i,
                'type': 'Array Index',
                'severity': 'Medium',
                'content': line.strip(),
                'suggestion': 'Verify array length before accessing index'
            })
    
    # Pattern 4: None comparisons with ==
    for i, line in enumerate(lines, 1):
        if re.search(r'==\s*None|None\s*==', line):
            bugs_found.append({
                'line': i,
                'type': 'None Comparison',
                'severity': 'Low',
                'content': line.strip(),
                'suggestion': 'Use "is None" instead of "== None"'
            })
    
    # Pattern 5: Empty except blocks
    for i, line in enumerate(lines, 1):
        if 'except:' in line or 'except Exception:' in line:
            # Check if next line is just pass
            if i < len(lines) and lines[i].strip() == 'pass':
                bugs_found.append({
                    'line': i,
                    'type': 'Silent Exception',
                    'severity': 'High',
                    'content': f"{line.strip()} {lines[i].strip()}",
                    'suggestion': 'Log exception or provide user feedback'
                })
    
    return bugs_found


def analyze_streamlit_issues(filepath):
    """Scan for Streamlit-specific issues"""
    print(f"\n{'='*80}")
    print(f"Streamlit Analysis: {filepath}")
    print('='*80)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    
    # Issue 1: st.stop() without error message
    for i, line in enumerate(lines, 1):
        if 'st.stop()' in line:
            # Check if there's an error message before it
            has_error = False
            for j in range(max(0, i-5), i):
                if 'st.error' in lines[j] or 'st.warning' in lines[j]:
                    has_error = True
            
            if not has_error:
                issues.append({
                    'line': i,
                    'type': 'st.stop() without message',
                    'severity': 'Medium',
                    'content': line.strip(),
                    'suggestion': 'Add st.error() before st.stop() for user clarity'
                })
    
    # Issue 2: Missing st.cache for expensive functions
    for i, line in enumerate(lines, 1):
        if re.match(r'def \w+\(', line):
            func_name = line.split('def ')[1].split('(')[0]
            # Check if it's a data loading or processing function
            if any(keyword in func_name.lower() for keyword in ['load', 'process', 'generate', 'calculate']):
                # Check if @st.cache is above
                has_cache = False
                if i > 1 and '@st.cache' in lines[i-2]:
                    has_cache = True
                
                if not has_cache:
                    issues.append({
                        'line': i,
                        'type': 'Missing @st.cache',
                        'severity': 'Low',
                        'content': line.strip(),
                        'suggestion': f'Consider adding @st.cache_data or @st.cache_resource for {func_name}'
                    })
    
    # Issue 3: Session state without initialization
    for i, line in enumerate(lines, 1):
        if re.search(r'st\.session_state\.\w+(?!\s*=)', line):
            var_match = re.search(r'st\.session_state\.(\w+)', line)
            if var_match:
                var_name = var_match.group(1)
                # Check if it's initialized anywhere above
                initialized = False
                for j in range(0, i):
                    if f'st.session_state.{var_name} =' in lines[j]:
                        initialized = True
                
                if not initialized:
                    issues.append({
                        'line': i,
                        'type': 'Uninitialized session_state',
                        'severity': 'High',
                        'content': line.strip(),
                        'suggestion': f'Initialize st.session_state.{var_name} before use'
                    })
    
    return issues


if __name__ == "__main__":
    print("\n🐛 BUG SCANNER - FROST-NS Code Analysis\n")
    
    # Files to scan
    files_to_scan = [
        'app.py',
        'model.py'
    ]
    
    all_bugs = {}
    all_streamlit_issues = {}
    
    for filepath in files_to_scan:
        if os.path.exists(filepath):
            # General bug patterns
            bugs = scan_file_for_bugs(filepath)
            if bugs:
                all_bugs[filepath] = bugs
            
            # Streamlit-specific (only for app.py)
            if 'app.py' in filepath:
                st_issues = analyze_streamlit_issues(filepath)
                if st_issues:
                    all_streamlit_issues[filepath] = st_issues
    
    # Summary Report
    print("\n" + "="*80)
    print("BUG SCAN SUMMARY")
    print("="*80)
    
    total_bugs = sum(len(bugs) for bugs in all_bugs.values())
    total_st_issues = sum(len(issues) for issues in all_streamlit_issues.values())
    
    print(f"\nGeneral Issues Found: {total_bugs}")
    print(f"Streamlit Issues Found: {total_st_issues}")
    
    if total_bugs == 0 and total_st_issues == 0:
        print("\n✅ No obvious bugs detected!")
    else:
        print("\n⚠️ Issues requiring review found\n")
        
        # Print details
        for filepath, bugs in all_bugs.items():
            print(f"\n📁 {filepath}")
            print("-" * 80)
            for bug in bugs[:10]:  # Limit to first 10
                print(f"  Line {bug['line']}: [{bug['severity']}] {bug['type']}")
                print(f"    Code: {bug['content'][:80]}")
                print(f"    Suggestion: {bug['suggestion']}\n")
        
        for filepath, issues in all_streamlit_issues.items():
            print(f"\n🎈 Streamlit Issues in {filepath}")
            print("-" * 80)
            for issue in issues[:10]:
                print(f"  Line {issue['line']}: [{issue['severity']}] {issue['type']}")
                print(f"    Code: {issue['content'][:80]}")
                print(f"    Suggestion: {issue['suggestion']}\n")
    
    print("\n✨ Scan complete!")
