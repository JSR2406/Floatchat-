#!/usr/bin/env python
"""
ORCA Offline Demo Runner
Runs all flagship queries in sequence and captures responses for demo recording.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.demo.offline_demo import FLAGSHIP_QUERIES, DEMO_MANIFEST
from app.agents import ExecutionContext
from app.agents.orchestrator import get_orchestrator
from app.agents.intent_agent import IntentAgent
from app.services.risk_engine import get_risk_engine
from app.agents.scenario_agent import get_scenario_agent


class OfflineDemoRunner:
    """Runs flagship queries in offline mode and captures responses for demo recording."""
    
    def __init__(self):
        self.orchestrator = get_orchestrator()
        self.intent_agent = IntentAgent()
        self.risk_engine = get_risk_engine()
        self.scenario_agent = get_scenario_agent()
        self.results = []
    
    async def run_query(self, query_data: dict) -> dict:
        """Run a single flagship query through the pipeline."""
        query_id = query_data["id"]
        user_query = query_data["query"]
        language = query_data.get("language", "en-IN")
        
        print(f"\n{'='*60}")
        print(f"Running: {query_data['name']} ({query_id})")
        # Handle Unicode encoding for Windows console
        safe_query = user_query.encode('ascii', errors='replace').decode('ascii')
        print(f"Query: {safe_query}")
        print(f"Language: {language}")
        print(f"{'='*60}")
        
        # Create execution context
        context = ExecutionContext(
            query_run_id=f"demo_{query_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            user_query=user_query,
            structured_query={},
            detected_language=language,
            session_id=f"demo_session_{query_id}",
        )
        
        try:
            # Step 1: Intent extraction
            print("  [1/3] Extracting intent...")
            intent_bundles = await self.intent_agent.execute(context)
            
            # Step 2: Orchestrate agents
            print("  [2/3] Orchestrating agents...")
            evidence_bundles = await self.orchestrator.execute(context)
            
            # Step 3: Generate response (simplified for demo)
            print("  [3/3] Generating response...")
            response = self._generate_demo_response(query_data, context, evidence_bundles)
            
            result = {
                "query_id": query_id,
                "name": query_data["name"],
                "query": user_query,
                "language": language,
                "status": "success",
                "response": response,
                "context": {
                    "structured_query": context.structured_query,
                    "evidence_count": len(evidence_bundles),
                    "trace": context.trace,
                    "errors": context.errors,
                    "warnings": context.warnings,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            print(f"  [OK] Completed: {query_data['name']}")
            return result
            
        except Exception as e:
            print(f"  [FAIL] Failed: {str(e)}")
            return {
                "query_id": query_id,
                "name": query_data["name"],
                "query": user_query,
                "language": language,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    def _generate_demo_response(self, query_data: dict, context: ExecutionContext, evidence_bundles: list) -> dict:
        """Generate a demo response based on expected output."""
        return query_data.get("demo_response", {
            "summary": "Demo response generated",
            "evidence_count": len(evidence_bundles),
        })
    
    async def run_all(self) -> dict:
        """Run all flagship queries."""
        print(f"\n{'#'*60}")
        print(f"ORCA OFFLINE DEMO RUNNER")
        print(f"Running {len(FLAGSHIP_QUERIES)} flagship queries...")
        print(f"{'#'*60}")
        
        start_time = datetime.utcnow()
        
        for query_data in FLAGSHIP_QUERIES:
            result = await self.run_query(query_data)
            self.results.append(result)
            # Small delay between queries
            await asyncio.sleep(0.5)
        
        end_time = datetime.utcnow()
        
        # Summary
        successful = sum(1 for r in self.results if r["status"] == "success")
        failed = sum(1 for r in self.results if r["status"] == "error")
        
        summary = {
            "demo_run_id": f"demo_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "total_queries": len(FLAGSHIP_QUERIES),
            "successful": successful,
            "failed": failed,
            "results": self.results,
        }
        
        return summary
    
    def save_results(self, summary: dict, output_dir: Path = None):
        """Save demo results to JSON file."""
        if output_dir is None:
            output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"demo_results_{timestamp}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        return output_file


async def main():
    """Main entry point for demo runner."""
    runner = OfflineDemoRunner()
    summary = await runner.run_all()
    output_file = runner.save_results(summary)
    
    # Print summary
    print(f"\n{'#'*60}")
    print(f"DEMO RUN COMPLETE")
    print(f"{'#'*60}")
    print(f"Total Queries: {summary['total_queries']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Duration: {summary['duration_seconds']:.1f}s")
    print(f"Results saved to: {output_file}")
    
    return summary


if __name__ == "__main__":
    asyncio.run(main())