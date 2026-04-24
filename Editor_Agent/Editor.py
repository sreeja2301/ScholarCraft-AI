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


class EditorAgentA2A(GoogleA2AServer):
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(self.model_name)

        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        agent_config = config["agent"]

        print("[EditorAgentA2A] Loaded agent configuration from config.json!")
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
        edit_cap = A2ACapability(
            name="comprehensive_edit",
            description="Complete editorial review including grammar, structure, and engagement",
            skill_type=SkillType.EDITING,
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to edit"},
                    "edit_focus": {
                        "type": "string",
                        "description": "Editing focus",
                        "default": "general",
                    },
                    "target_audience": {
                        "type": "string",
                        "description": "Target audience",
                        "default": "general",
                    },
                },
                "required": ["content"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "edited_content": {
                        "type": "string",
                        "description": "Professionally edited content",
                    }
                },
            },
            tags=["editing", "proofreading", "quality-assurance"],
        )
        self.register_capability(edit_cap, self.handle_comprehensive_edit)

        proofread_cap = A2ACapability(
            name="quick_proofread",
            description="Fast proofreading for grammar, spelling, and basic clarity",
            skill_type=SkillType.EDITING,
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to proofread"}
                },
                "required": ["content"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "proofread_content": {"type": "string", "description": "Proofread content"}
                },
            },
            tags=["proofreading", "grammar", "quick-fix"],
        )
        self.register_capability(proofread_cap, self.handle_quick_proofread)

    async def handle_comprehensive_edit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        content = payload.get("content")
        edit_focus = payload.get("edit_focus", "general")
        target_audience = payload.get("target_audience", "general")

        prompt = f"""
        As Emma Editor, professionally edit and enhance this content:

        Content to edit:
        {content}

        Edit focus: {edit_focus}
        Target audience: {target_audience}

        Editorial framework:
        - Grammar, spelling, and punctuation perfection
        - Sentence structure and clarity optimization
        - Flow and readability enhancement
        - Consistency in tone and style
        - Voice preservation while improving quality
        - Engagement and impact enhancement
        """

        try:
            response = self.model.generate_content(prompt, request_options={"timeout": 60})
            return {
                "edited_content": f"Edited by Emma Editor\n{'=' * 60}\n{response.text}",
                "edit_focus": edit_focus,
                "target_audience": target_audience,
            }
        except Exception as e:
            raise Exception(f"Content editing failed: {self._format_model_error(e)}")

    async def handle_quick_proofread(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        content = payload.get("content")

        prompt = f"""
        As Emma Editor, perform a quick but thorough proofread:

        Content:
        {content}

        Quick proofread focus:
        - Grammar and spelling corrections
        - Basic punctuation fixes
        - Simple clarity improvements
        - Maintain original voice and intent
        """

        try:
            response = self.model.generate_content(prompt, request_options={"timeout": 60})
            return {
                "proofread_content": f"Quick Proofread by Emma Editor\n{'=' * 60}\n{response.text}"
            }
        except Exception as e:
            raise Exception(f"Proofreading failed: {self._format_model_error(e)}")

    async def _execute_capability(self, capability: A2ACapability, payload: Dict[str, Any]):
        handler_name = f"handle_{capability.name}"
        handler = getattr(self, handler_name)
        return await handler(payload)


if __name__ == "__main__":
    from dotenv import load_dotenv
    from Agent_Framework.google_a2a import run_server

    load_dotenv()
    agent = EditorAgentA2A()
    run_server(agent, host="0.0.0.0", port=8003)
