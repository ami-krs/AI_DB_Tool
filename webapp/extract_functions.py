#!/usr/bin/env python3
"""Helper script to extract functions from app.py for modularization"""
import ast
import re

def extract_function_from_file(filepath, function_name):
    """Extract a function definition from a Python file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse the file
    tree = ast.parse(content)
    
    # Find the function
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Get the function source
            start_line = node.lineno - 1
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else None
            
            if end_line:
                lines = content.split('\n')
                return '\n'.join(lines[start_line:end_line])
    
    return None

if __name__ == '__main__':
    # Test extraction
    func = extract_function_from_file('app.py', 'inject_dark_mode_css')
    if func:
        print(f"Extracted {len(func)} characters")
    else:
        print("Function not found")
