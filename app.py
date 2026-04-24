import streamlit as st
import asyncio
import os
from Orchestration_Agent.orchestrator_a2a import GoogleA2AOrchestrator
from logger import get_logger

logger = get_logger("App")

st.set_page_config(
    page_title="Google A2A Protocol Multi-Agent System",
    page_icon="🚀",
    layout="wide"
)

logger.info("Streamlit UI initialized.")

# --- Sidebar ---
st.sidebar.title("Google A2A Protocol Multi-Agent System")
st.sidebar.markdown("""
**Features**
- 🧑‍🔬 Research Agent: Research & trend analysis  
- ✍️ Writer Agent: Articles & marketing copy  
- 📝 Editor Agent: Editorial review  
- 🤖 Orchestration Agent: Workflow routing  
- ⚙️ Config-driven, clear logging  
""")
st.sidebar.markdown("---")
st.sidebar.markdown("**Project Structure**")
st.sidebar.code("""
app.py
requirements.txt
README.md
Agent_Framework/
Editor_Agent/
Orchestration_Agent/
Research_Agent/
Writer_Agent/
""")
st.sidebar.markdown("---")
st.sidebar.info("Ensure all agents are running before using the app.")

# --- Main UI ---
st.title("🚀 Google A2A Protocol Multi-Agent System")
st.markdown("""
Welcome to the **Google A2A Protocol Multi-Agent System** powered by Google Gemini and FastAPI.

**Agents available:**
- 🔬 **Research**: Comprehensive research & trend analysis
- ✍️ **Writer**: Professional articles & marketing copy
- 📝 **Editor**: Editorial review & improvement
- 🤖 **Orchestrator**: Workflow routing

---
""")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def get_orchestrator():
    orchestrator = GoogleA2AOrchestrator()
    asyncio.run(orchestrator.initialize())
    logger.info("Orchestrator initialized.")
    return orchestrator

orchestrator = get_orchestrator()

st.subheader("💬 Interactive Chat")
st.markdown("""
Type your request below.  
**Examples:**  
- `research artificial intelligence trends`  
- `write article about quantum computing`  
- `edit: Please proofread this text...`  
- `status` (check agent health)  
- `help` (show usage examples)  
""")

def show_chat():
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

show_chat()

user_input = st.chat_input("Type your request and press Enter...")

async def process_user_input(user_input):
    logger.info(f"User input: {user_input}")
    if user_input.lower() == "help":
        return (
            "**Usage Examples:**\n"
            "- `research artificial intelligence trends`\n"
            "- `write article about quantum computing`\n"
            "- `edit: Please proofread this text...`\n"
            "- `status` (check agent health)\n"
            "- `help` (show usage examples)\n"
            "- `quit` (exit)\n"
        )
    elif user_input.lower() == "status":
        status = await orchestrator.get_agent_status()
        logger.info(f"Agent status: {status}")
        return "\n".join([f"- **{k.title()}**: {v}" for k, v in status.items()])
    elif user_input.lower() == "quit":
        logger.info("Session ended by user.")
        return "👋 Session ended. You may close this tab."
    else:
        response = await orchestrator.process_request(user_input)
        logger.info(f"Response: {response}")
        return response

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Processing..."):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(process_user_input(user_input))
    st.session_state.messages.append({"role": "assistant", "content": response})
    show_chat()

st.markdown("---")
st.caption("Enjoy your modular, multi-agent Google A2A Protocol system! 🚀")