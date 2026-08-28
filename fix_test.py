import sys

with open(r'E:\CODING\Floatchat\tests\test_unit.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''class TestScenarioAgent:
    @pytest.mark.asyncio
    async def test_scenario_types(self):
        from app.agents.scenario_agent import get_scenario_agent
        from app.agents import ExecutionContext
        
        agent = get_scenario_agent()
        
        ctx = ExecutionContext(
            query_run_id="test_3",
            user_query="What if departure time changes?",
            structured_query={"scenario_type": "departure_time_change", "new_departure_time": "tomorrow"},
            detected_language="en-IN",
            session_id="sess_2",
        )
        
        result = await agent.execute(ctx)
        assert len(result) == 1
        assert result[0]["scenario_type"] == "departure_time_change"'''

new = '''class TestScenarioAgent:
    @pytest.mark.asyncio
    async def test_scenario_types(self):
        from app.agents.scenario_agent import get_scenario_agent
        from app.agents import ExecutionContext
        
        agent = get_scenario_agent()
        
        ctx = ExecutionContext(
            query_run_id="test_3",
            user_query="What if departure time changes?",
            structured_query={
                "scenario_type": "departure_time_change",
                "base_request": {
                    "origin_lat": 19.0760,
                    "origin_lon": 72.8777,
                    "destination_lat": 15.2993,
                    "destination_lon": 74.1240,
                },
                "new_departure_time": "tomorrow",
            },
            detected_language="en-IN",
            session_id="sess_2",
        )
        
        result = await agent.execute(ctx)
        assert len(result) == 1
        assert "scenario_type" in result[0]
        assert result[0]["scenario_type"] == "departure_time_change"'''

content = content.replace(old, new)

with open(r'E:\CODING\Floatchat\tests\test_unit.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed')