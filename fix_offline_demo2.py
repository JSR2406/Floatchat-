import re

with open(r'E:\CODING\Floatchat\apps\api\app\demo\offline_demo.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    (r'(\s+)name: "([^"]*)"', r'\1"name": "\2"'),
    (r'(\s+)category: "([^"]*)"', r'\1"category": "\2"'),
    (r'(\s+)query: "([^"]*)"', r'\1"query": "\2"'),
    (r'(\s+)language: "([^"]*)"', r'\1"language": "\2"'),
    (r'(\s+)expected_intent: "([^"]*)"', r'\1"expected_intent": "\2"'),
    (r'(\s+)expected_region: "([^"]*)"', r'\1"expected_region": "\2"'),
    (r'(\s+)expected_origin: {', r'"expected_origin": {'),
    (r'(\s+)expected_destination: {', r'"expected_destination": {'),
    (r'(\s+)context: "([^"]*)"', r'"context": "\2"'),
    (r'(\s+)demo_response: {', r'"demo_response": {'),
    (r'(\s+)summary: "([^"]*)"', r'"summary": "\2"'),
    (r'(\s+)id: "([^"]*)"', r'"id": "\2"'),
    (r'(\s+)expected_location: {', r'"expected_location": {'),
    (r'(\s+)expected_radius_km: (\d+)', r'"expected_radius_km": \2'),
    (r'(\s+)expected_variables: \[', r'"expected_variables": ['),
    (r'(\s+)expected_departure_time: "([^"]*)"', r'"expected_departure_time": "\2"'),
    (r'(\s+)expected_new_speed_knots: (\d+)', r'"expected_new_speed_knots": \2'),
    (r'(\s+)variant_waypoints: \[', r'"variant_waypoints": ['),
    (r'(\s+)weather_params: {', r'"weather_params": {'),
    (r'(\s+)new_speed_knots: (\d+)', r'"new_speed_knots": \2'),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

with open(r'E:\CODING\Floatchat\apps\api\app\demo\offline_demo.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed')