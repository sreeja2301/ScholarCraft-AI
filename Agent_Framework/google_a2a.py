import json
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import aiohttp
import requests

class MessageType(str, Enum):
    """Google A2A Protocol message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class SkillType(str, Enum):
    """Standard A2A skill classifications"""
    RESEARCH = "research"
    CONTENT_CREATION = "content_creation"
    EDITING = "editing"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"

@dataclass
class A2ACapability:
    """Google A2A Protocol capability definition"""
    name: str
    description: str
    skill_type: SkillType
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    examples: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"

@dataclass
class A2AAgent:
    """Google A2A Protocol agent definition"""
    agent_id: str
    name: str
    description: str
    version: str
    capabilities: List[A2ACapability] = field(default_factory=list)
    endpoint: str = ""
    supported_protocols: List[str] = field(default_factory=lambda: ["google-a2a-v1"])
    metadata: Dict[str, Any] = field(default_factory=dict)

class A2AMessage(BaseModel):
    """Google A2A Protocol standard message format"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType
    sender_id: str
    recipient_id: str
    capability_name: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    protocol_version: str = "google-a2a-v1"
    correlation_id: Optional[str] = None

class A2AResponse(BaseModel):
    """Google A2A Protocol response format"""
    message_id: str
    success: bool
    result: Any = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GoogleA2AServer:
    """Google A2A Protocol compliant server"""
    
    def __init__(self, agent: A2AAgent):
        self.agent = agent
        self.app = FastAPI(title=f"{agent.name} A2A Server")
        self.capabilities: Dict[str, A2ACapability] = {}
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Google A2A Protocol standard endpoints"""
        
        @self.app.get("/a2a/discovery")
        async def discovery():
            """A2A Protocol agent discovery endpoint"""
            return {
                "agent": asdict(self.agent),
                "capabilities": [asdict(cap) for cap in self.capabilities.values()],
                "protocol_version": "google-a2a-v1",
                "status": "active"
            }
        
        @self.app.post("/a2a/invoke")
        async def invoke(message: A2AMessage):
            """A2A Protocol capability invocation endpoint"""
            try:
                # Validate capability exists
                if message.capability_name not in self.capabilities:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Capability '{message.capability_name}' not found"
                    )
                
                capability = self.capabilities[message.capability_name]
                
                # Execute capability
                result = await self._execute_capability(capability, message.payload)
                
                return A2AResponse(
                    message_id=str(uuid.uuid4()),
                    success=True,
                    result=result,
                    metadata={
                        "capability": message.capability_name,
                        "processed_at": datetime.utcnow().isoformat(),
                        "correlation_id": message.correlation_id
                    }
                )
                
            except Exception as e:
                return A2AResponse(
                    message_id=str(uuid.uuid4()),
                    success=False,
                    error_code="EXECUTION_ERROR",
                    error_message=str(e),
                    metadata={"correlation_id": message.correlation_id}
                )
        
        @self.app.get("/a2a/health")
        async def health():
            """A2A Protocol health check endpoint"""
            return {
                "status": "healthy",
                "agent_id": self.agent.agent_id,
                "capabilities_count": len(self.capabilities),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_capability(self, capability: A2ACapability, payload: Dict[str, Any]):
        """Execute a capability with given payload"""
        # This will be overridden by specific agent implementations
        raise NotImplementedError("Capability execution must be implemented by agent")
    
    def register_capability(self, capability: A2ACapability, handler):
        """Register a capability with its handler"""
        self.capabilities[capability.name] = capability
        setattr(self, f"_handle_{capability.name.replace(' ', '_').lower()}", handler)

class GoogleA2AClient:
    """Google A2A Protocol compliant client"""
    
    @staticmethod
    async def discover_agent(endpoint: str) -> Dict[str, Any]:
        """Discover agent capabilities using A2A protocol"""
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{endpoint}/a2a/discovery") as response:
                return await response.json()
    
    @staticmethod
    async def invoke_capability(
        endpoint: str,
        capability_name: str,
        payload: Dict[str, Any],
        sender_id: str = "orchestrator",
        recipient_id: str = "agent"
    ) -> A2AResponse:
        """Invoke agent capability using A2A protocol"""
        
        message = A2AMessage(
            message_type=MessageType.REQUEST,
            sender_id=sender_id,
            recipient_id=recipient_id,
            capability_name=capability_name,
            payload=payload,
            correlation_id=str(uuid.uuid4())
        )
        
        timeout = aiohttp.ClientTimeout(total=120)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{endpoint}/a2a/invoke",
                    json=message.model_dump()
                ) as response:
                    result = await response.json()
                    return A2AResponse(**result)
        except aiohttp.ClientError as e:
            return A2AResponse(
                message_id=str(uuid.uuid4()),
                success=False,
                error_code="CLIENT_ERROR",
                error_message=f"Failed to reach agent at {endpoint}: {type(e).__name__}: {e}",
                metadata={"correlation_id": message.correlation_id},
            )
        except TimeoutError:
            return A2AResponse(
                message_id=str(uuid.uuid4()),
                success=False,
                error_code="TIMEOUT",
                error_message=(
                    f"Timed out waiting for agent at {endpoint}. "
                    "The agent may be unable to reach the Gemini API or is taking too long to respond."
                ),
                metadata={"correlation_id": message.correlation_id},
            )

# ✅ Added function to start the FastAPI server
def run_server(agent: GoogleA2AServer, host: str = "localhost", port: int = 8000):
    """Run the Google A2A FastAPI server using Uvicorn"""
    uvicorn.run(agent.app, host=host, port=port)
