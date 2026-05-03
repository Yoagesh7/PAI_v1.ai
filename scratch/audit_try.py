import sys

def audit_try_blocks(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    stack = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        
        if stripped.startswith('try:'):
            stack.append((i + 1, indent))
        elif stripped.startswith(('except', 'finally')) and (stripped.startswith('except ') or stripped == 'except:' or stripped.startswith('finally')):
            # Note: this is a simple check, it might not handle nested same-indent correctly but let's see
            if stack and stack[-1][1] == indent:
                stack.pop()
    
    if stack:
        print("Found orphaned try blocks:")
        for line_num, indent in stack:
            print(f"Line {line_num}: try: (indent {indent})")
    else:
        print("No orphaned try blocks found.")

if __name__ == "__main__":
    audit_try_blocks(sys.argv[1])
