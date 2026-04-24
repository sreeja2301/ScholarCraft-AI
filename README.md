# Google A2A Protocol Multi-Agent System

This repository implements a modular, configuration-driven multi-agent system using the Google A2A Protocol. It includes specialized agents for research, writing, and editing, coordinated by an internal orchestrator and surfaced through a Streamlit frontend.

## Features
- Research Agent: Conducts comprehensive research and trend analysis.
- Writer Agent: Generates professional articles and marketing copy.
- Editor Agent: Provides editorial review and content improvement.
- Orchestration Agent: Routes and manages workflows between agents.
- Interactive Client: Streamlit chat UI for end-to-end workflow execution.
- Configuration-Driven: All agent settings are loaded from `config.json` files.
- Clear Logging: Agents print startup and workflow logs.

## Prerequisites
- Python 3.8+
- Google Gemini API key
- All dependencies in `requirements.txt`

## Setup
1. Clone the repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_google_gemini_api_key_here
   ```
4. Update each `config.json` if you want different ports, names, or endpoints.

## How To Run
Start each agent in a separate terminal:

```sh
python -m Research_Agent.Research
python -m Editor_Agent.Editor
python -m Writer_Agent.Writer
```

Then start the Streamlit app:

```sh
streamlit run app.py
```

## Start Everything At Once

- Windows:
  ```bat
  start_all_agents.bat
  ```
- Linux/macOS:
  ```sh
  bash start_all_agents.sh
  ```

## Usage
- Open the Streamlit app in your browser after startup.
- Example requests:
  - `research artificial intelligence trends`
  - `write article about quantum computing`
  - `edit: Please proofread this text...`
  - `status`
  - `help`

## Project Structure
```text
app.py
requirements.txt
README.md
Agent_Framework/
  google_a2a.py
Editor_Agent/
  Editor.py
  config.json
Orchestration_Agent/
  orchestrator_a2a.py
  config.json
Research_Agent/
  Research.py
  config.json
Writer_Agent/
  Writer.py
  config.json
```

## Notes
- Ensure all three agents are running before using the Streamlit app.
- The orchestrator is used internally by `app.py`; it does not need to be launched as a separate server.
- Generated PDFs are saved by the writer agent in an `outputs/` directory.
