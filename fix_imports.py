#!/usr/bin/env python3
"""
Script to fix relative imports in Python files
"""

import os
import re
import sys

def fix_imports_in_file(file_path):
    """Fix relative imports in a Python file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace relative imports with absolute imports
    fixed_content = re.sub(r'from\s+\.\s+import\s+(\w+)', r'import \1', content)
    fixed_content = re.sub(r'from\s+\.(\w+)\s+import', r'from \1 import', fixed_content)
    
    if content != fixed_content:
        print(f"Fixing imports in {file_path}")
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        return True
    return False

def main():
    """Main function"""
    macro_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'macro')
    
    if not os.path.exists(macro_dir):
        print(f"Error: Directory {macro_dir} does not exist")
        return 1
    
    fixed_count = 0
    for root, _, files in os.walk(macro_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_count += 1
    
    print(f"Fixed imports in {fixed_count} files")
    return 0

if __name__ == '__main__':
    sys.exit(main())
