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
from Writer_Agent.pdf_generator import save_article_to_pdf


class WriterAgentA2A(GoogleA2AServer):
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(self.model_name)

        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        agent_config = config["agent"]

        print("[WriterAgentA2A] Loaded agent configuration from config.json!")
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
        article_cap = A2ACapability(
            name="create_article",
            description="Create comprehensive, engaging articles on any topic",
            skill_type=SkillType.CONTENT_CREATION,
            input_schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Article topic"},
                    "research_data": {
                        "type": "string",
                        "description": "Research foundation",
                        "default": "",
                    },
                    "tone": {"type": "string", "description": "Writing tone", "default": "professional"},
                    "length": {"type": "string", "description": "Article length", "default": "medium"},
                },
                "required": ["topic"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "article": {"type": "string", "description": "Complete article content"}
                },
            },
            tags=["writing", "articles", "content-creation"],
        )
        self.register_capability(article_cap, self.handle_create_article)

        marketing_cap = A2ACapability(
            name="create_marketing_copy",
            description="Create compelling marketing and promotional content",
            skill_type=SkillType.CONTENT_CREATION,
            input_schema={
                "type": "object",
                "properties": {
                    "product_service": {"type": "string", "description": "Product or service"},
                    "target_audience": {"type": "string", "description": "Target audience"},
                    "copy_type": {"type": "string", "description": "Type of copy", "default": "general"},
                },
                "required": ["product_service", "target_audience"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "marketing_copy": {"type": "string", "description": "Marketing copy content"}
                },
            },
            tags=["marketing", "copywriting", "promotion"],
        )
        self.register_capability(marketing_cap, self.handle_create_marketing_copy)

    async def handle_create_article(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = payload.get("topic")
        research_data = payload.get("research_data", "")
        tone = payload.get("tone", "professional")
        length = payload.get("length", "medium")

        word_targets = {
            "short": "400-600 words",
            "medium": "800-1200 words",
            "long": "1500-2000 words",
        }

        if research_data:
            prompt = f"""
            As Alex Writer, write a comprehensive article about: {topic}

            Research foundation:
            {research_data}

            Writing specifications:
            - Tone: {tone}
            - Length: {word_targets.get(length, "800-1200 words")}
            - Include compelling introduction with hook
            - Use clear headings and subheadings
            - Provide detailed explanations with examples
            - Include strong, actionable conclusion
            - Maintain engaging, accessible style throughout
            """
        else:
            prompt = f"""
            As Alex Writer, write a comprehensive article about: {topic}

            Writing specifications:
            - Tone: {tone}
            - Length: {word_targets.get(length, "800-1200 words")}
            - Create compelling introduction with hook
            - Use clear headings and subheadings
            - Provide detailed explanations with examples
            - Include strong, actionable conclusion
            """

        try:
            response = self.model.generate_content(prompt, request_options={"timeout": 60})
            article_text = f"Article by Alex Writer\n{'=' * 60}\n{response.text}"
            pdf_path = save_article_to_pdf(title=f"Article: {topic}", content=response.text)
            return {
                "article": article_text,
                "topic": topic,
                "tone": tone,
                "length": length,
                "pdf_file": pdf_path,
            }
        except Exception as e:
            raise Exception(f"Article creation failed: {self._format_model_error(e)}")

    async def handle_create_marketing_copy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        product_service = payload.get("product_service")
        target_audience = payload.get("target_audience")
        copy_type = payload.get("copy_type", "general")

        prompt = f"""
        As Alex Writer, create compelling marketing copy for: {product_service}
        Target audience: {target_audience}
        Copy type: {copy_type}

        Marketing copy framework:
        - Attention-grabbing headline
        - Clear value proposition
        - Audience-specific benefits
        - Compelling call-to-action
        - Persuasive yet authentic tone
        """

        try:
            response = self.model.generate_content(prompt, request_options={"timeout": 60})
            marketing_text = f"Marketing Copy by Alex Writer\n{'=' * 60}\n{response.text}"
            pdf_path = save_article_to_pdf(title=f"Marketing Copy: {product_service}", content=response.text)
            return {
                "marketing_copy": marketing_text,
                "product_service": product_service,
                "target_audience": target_audience,
                "pdf_file": pdf_path,
            }
        except Exception as e:
            raise Exception(f"Marketing copy creation failed: {self._format_model_error(e)}")

    async def _execute_capability(self, capability: A2ACapability, payload: Dict[str, Any]):
        handler_name = f"handle_{capability.name}"
        handler = getattr(self, handler_name)
        return await handler(payload)


if __name__ == "__main__":
    from dotenv import load_dotenv
    from Agent_Framework.google_a2a import run_server

    load_dotenv()
    agent = WriterAgentA2A()
    run_server(agent, host="0.0.0.0", port=8002)
