with open(r'E:\CODING\Floatchat\apps\api\app\agents\geofence_agent.py', 'r') as f:
    content = f.read()
# Remove any better approach - just check what's there and rewrite
lines = content.split('\n')
# Find last non-empty line
last_lines = [l for l in lines if l.strip()]
print('Last lines:', last_lines[-3:] if last_lines else 'empty')
print('Total lines:', len(lines))