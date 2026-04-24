import json
import os
from pathlib import Path
from typing import Any, Dict

import google.generativeai as genai

from Agent_Framework.google_a2a import (
    A2AAgent,
    A2ACapability,
    GoogleA2AServer,
    SkillType,
)


class ResearchAgentA2A(GoogleA2AServer):
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(self.model_name)

        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        agent_config = config["agent"]

        print("[ResearchAgentA2A] Loaded agent configuration from config.json!")
        print(f"Agent ID: {agent_config['agent_id']}")
        print(f"Name: {agent_config['name']}")
        print(f"Description: {agent_config['description']}")
        print(f"Endpoint: {agent_config['endpoint']}")
        print(f"Model: {self.model_name}")

        agent = A2AAgent(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            description=agent_config["description"],
            version=agent_config["version"],
            endpoint=agent_config["endpoint"],
            supported_protocols=agent_config.get("supported_protocols", ["google-a2a-v1"]),
            metadata=agent_config.get("metadata", {}),
        )

        super().__init__(agent)
        self._register_capabilities()

    def _format_model_error(self, exc: Exception) -> str:
        raw = str(exc).strip() or type(exc).__name__
        if "failed to connect to all addresses" in raw.lower():
            return (
                "Unable to reach the Gemini API from this machine/network. "
                f"Underlying error: {raw}"
            )
        return raw

    def _register_capabilities(self):
        research_cap = A2ACapability(
            name="comprehensive_research",
            description="Conduct thorough research on any topic with structured analysis",
            skill_type=SkillType.RESEARCH,
            input_schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Research topic"},
                    "focus_areas": {
                        "type": "string",
                        "description": "Specific focus areas",
                        "default": "general",
                    },
                },
                "required": ["topic"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "research_report": {
                        "type": "string",
                        "description": "Comprehensive research report",
                    }
                },
            },
            examples=[
                {"input": {"topic": "AI in healthcare"}, "output": {"research_report": "..."}}
            ],
            tags=["research", "analysis", "comprehensive"],
        )
        self.register_capability(research_cap, self.handle_comprehensive_research)

        trend_cap = A2ACapability(
            name="trend_analysis",
            description="Analyze current trends and developments in specific domains",
            skill_type=SkillType.ANALYSIS,
            input_schema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain to analyze"},
                    "time_frame": {
                        "type": "string",
                        "description": "Analysis time frame",
                        "default": "current",
                    },
                },
                "required": ["domain"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "trend_report": {"type": "string", "description": "Trend analysis report"}
                },
            },
            tags=["trends", "analysis", "market-research"],
        )
        self.register_capability(trend_cap, self.handle_trend_analysis)

    async def handle_comprehensive_research(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = payload.get("topic")
        focus_areas = payload.get("focus_areas", "general")

        prompt = f"""
        As Dr. Research, conduct comprehensive research on: {topic}
        Focus areas: {focus_areas}

        Research Framework:
        1. Key concepts and definitions
        2. Current trends and developments
        3. Important statistics and data points
        4. Main challenges and opportunities
        5. Expert opinions and viewpoints
        6. Recent developments and innovations
        7. Future outlook and predictions

        Provide structured, evidence-based research with actionable insights.
        """

        try:
            response = self.model.generate_content(prompt, request_options={"timeout": 60})
            return {
                "research_report": f"Research Report by Dr. Research\n{'=' * 60}\n{response.text}",
                "topic": topic,
                "focus_areas": focus_areas,
            }
        except Exception as e:
            raise Exception(f"Research generation failed: {self._format_model_error(e)}")

    async def handle_trend_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        domain = payload.get("domain")
        time_frame = payload.get("time_frame", "current")

        prompt = f"""
        As Dr. Research, analyze current trends in: {domain}
        Time frame: {time_frame}

        Trend Analysis Framework:
        1. Emerging trends and patterns
        2. Market dynamics and drivers
        3. Key players and innovations
        4. Growth statistics and projections
        5. Disruption factors
        6. Future implications

        Provide data-driven trend analysis with supporting evidence.
        """

        try:
            response = self.model.generate_content(prompt, request_options={"timeout": 60})
            return {
                "trend_report": f"Trend Analysis by Dr. Research\n{'=' * 60}\n{response.text}",
                "domain": domain,
                "time_frame": time_frame,
            }
        except Exception as e:
            raise Exception(f"Trend analysis failed: {self._format_model_error(e)}")

    async def _execute_capability(self, capability: A2ACapability, payload: Dict[str, Any]):
        handler_name = f"handle_{capability.name}"
        handler = getattr(self, handler_name)
        return await handler(payload)


if __name__ == "__main__":
    from dotenv import load_dotenv
    from Agent_Framework.google_a2a import run_server

    load_dotenv()
    agent = ResearchAgentA2A()
    run_server(agent, host="0.0.0.0", port=8001)
