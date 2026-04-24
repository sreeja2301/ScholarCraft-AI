import asyncio
import json
import re
from pathlib import Path
from typing import Dict, Tuple

import aiohttp

from Agent_Framework.google_a2a import GoogleA2AClient


class GoogleA2AOrchestrator:
    def __init__(self):
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        self.agents = config["agents"]
        self.agent_capabilities = {}

        print("[Orchestrator] Loaded agent endpoints from config.json!")
        for name, endpoint in self.agents.items():
            print(f"{name.title()} Agent Endpoint: {endpoint}")

    async def initialize(self):
        print("Discovering agent capabilities...")
        for agent_name, endpoint in self.agents.items():
            try:
                discovery = await GoogleA2AClient.discover_agent(endpoint)
                self.agent_capabilities[agent_name] = discovery
                print(
                    f"Discovered {discovery['agent']['name']} with "
                    f"{len(discovery['capabilities'])} capabilities."
                )
            except Exception as e:
                print(f"Failed to discover {agent_name}: {str(e)}")

    def analyze_intent(self, user_input: str) -> Tuple[str, Dict]:
        user_lower = user_input.lower()

        patterns = {
            "edit_only": [
                r"edit.*?:",
                r"improve.*grammar",
                r"proofread",
                r"correct.*mistakes",
                r"fix.*spelling",
                r"enhance.*clarity",
            ],
            "research_only": [
                r"^research\s+",
                r"find.*information",
                r"lookup.*data",
                r"investigate",
                r"analyze.*trends",
            ],
            "write_with_research": [
                r"^write.*article",
                r"create.*content.*about",
                r"compose.*piece",
                r"draft.*article",
            ],
        }

        for workflow, pattern_list in patterns.items():
            if any(re.search(pattern, user_lower) for pattern in pattern_list):
                if workflow == "edit_only":
                    text = user_input.split(":", 1)[1].strip() if ":" in user_input else user_input
                    return workflow, {"text": text}
                if workflow == "research_only":
                    topic = re.sub(r"^research\s+", "", user_lower).strip()
                    return workflow, {"topic": topic or user_input.strip()}
                if workflow == "write_with_research":
                    topic = re.sub(r"^write.*?about\s+", "", user_lower).strip()
                    return workflow, {"topic": topic or user_input.strip()}

        if len(user_input) > 200 and not any(word in user_lower for word in ["research", "write", "create"]):
            return "edit_only", {"text": user_input}
        return "full_workflow", {"topic": user_input}

    async def process_request(self, user_input: str) -> str:
        workflow_type, context = self.analyze_intent(user_input)
        print(f"Detected workflow: {workflow_type}")

        try:
            if workflow_type == "edit_only":
                return await self._edit_workflow(context["text"])
            if workflow_type == "research_only":
                return await self._research_workflow(context["topic"])
            if workflow_type == "write_with_research":
                return await self._write_with_research_workflow(context["topic"])
            return await self._full_workflow(context["topic"])
        except Exception as e:
            details = str(e).strip() or type(e).__name__
            return f"Workflow execution error: {details}"

    async def _research_workflow(self, topic: str) -> str:
        print("Executing research workflow...")
        response = await GoogleA2AClient.invoke_capability(
            endpoint=self.agents["research"],
            capability_name="comprehensive_research",
            payload={"topic": topic},
            sender_id="orchestrator",
            recipient_id="research-agent-001",
        )
        if response.success:
            return response.result.get("research_report", "Research completed")
        return f"Research failed: {response.error_message}"

    async def _edit_workflow(self, text: str) -> str:
        print("Executing editing workflow...")
        response = await GoogleA2AClient.invoke_capability(
            endpoint=self.agents["editor"],
            capability_name="comprehensive_edit",
            payload={"content": text},
            sender_id="orchestrator",
            recipient_id="editor-agent-001",
        )
        if response.success:
            return response.result.get("edited_content", "Editing completed")
        return f"Editing failed: {response.error_message}"

    async def _write_with_research_workflow(self, topic: str) -> str:
        print("Executing Research -> Write -> Edit workflow...")

        print("Step 1: Research phase...")
        research_response = await GoogleA2AClient.invoke_capability(
            endpoint=self.agents["research"],
            capability_name="comprehensive_research",
            payload={"topic": topic},
            sender_id="orchestrator",
            recipient_id="research-agent-001",
        )
        if not research_response.success:
            return f"Research phase failed: {research_response.error_message}"

        research_data = research_response.result.get("research_report", "")

        print("Step 2: Writing phase...")
        write_response = await GoogleA2AClient.invoke_capability(
            endpoint=self.agents["writer"],
            capability_name="create_article",
            payload={"topic": topic, "research_data": research_data},
            sender_id="orchestrator",
            recipient_id="writer-agent-001",
        )
        if not write_response.success:
            return f"Writing phase failed: {write_response.error_message}"

        article = write_response.result.get("article", "")

        print("Step 3: Editing phase...")
        edit_response = await GoogleA2AClient.invoke_capability(
            endpoint=self.agents["editor"],
            capability_name="comprehensive_edit",
            payload={"content": article},
            sender_id="orchestrator",
            recipient_id="editor-agent-001",
        )
        if not edit_response.success:
            return f"Editing phase failed: {edit_response.error_message}"

        return edit_response.result.get("edited_content", "Full workflow completed")

    async def _full_workflow(self, topic: str) -> str:
        print("Executing full content creation workflow...")

        print("Phase 1: Comprehensive Research...")
        research_response = await GoogleA2AClient.invoke_capability(
            endpoint=self.agents["research"],
            capability_name="comprehensive_research",
            payload={"topic": topic, "focus_areas": "comprehensive analysis"},
            sender_id="orchestrator",
            recipient_id="research-agent-001",
        )
        if not research_response.success:
            return f"Research phase failed: {research_response.error_message}"
        research_data = research_response.result.get("research_report", "")
        print("Research phase completed")

        print("Phase 2: Article Creation...")
        write_response = await GoogleA2AClient.invoke_capability(
            endpoint=self.agents["writer"],
            capability_name="create_article",
            payload={
                "topic": topic,
                "research_data": research_data,
                "tone": "professional",
                "length": "medium",
            },
            sender_id="orchestrator",
            recipient_id="writer-agent-001",
        )
        if not write_response.success:
            return f"Writing phase failed: {write_response.error_message}"
        article = write_response.result.get("article", "")
        print("Writing phase completed")

        print("Phase 3: Professional Editing...")
        edit_response = await GoogleA2AClient.invoke_capability(
            endpoint=self.agents["editor"],
            capability_name="comprehensive_edit",
            payload={
                "content": article,
                "edit_focus": "clarity and engagement",
                "target_audience": "general professional",
            },
            sender_id="orchestrator",
            recipient_id="editor-agent-001",
        )
        if not edit_response.success:
            return f"Editing phase failed: {edit_response.error_message}"

        final_content = edit_response.result.get("edited_content", "")
        print("All phases completed successfully.")

        return f"""
COMPLETE CONTENT CREATION WORKFLOW FINISHED
{'=' * 80}

Topic: {topic}
Workflow: Research -> Write -> Edit
Status: SUCCESS

{final_content}

{'=' * 80}
Workflow Summary:
- Research: Completed comprehensive research
- Writing: Created professional article
- Editing: Applied professional editing
- Result: High-quality, publication-ready content
"""

    async def get_agent_status(self) -> Dict[str, str]:
        status = {}
        for agent_name, endpoint in self.agents.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{endpoint}/a2a/health") as response:
                        health_data = await response.json()
                        status[agent_name] = health_data.get("status", "unknown")
            except Exception as e:
                status[agent_name] = f"offline ({str(e)})"
        return status


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    orchestrator = GoogleA2AOrchestrator()
    asyncio.run(orchestrator.initialize())
