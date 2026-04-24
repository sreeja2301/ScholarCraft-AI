@echo off
REM start_all_agents.bat
REM Batch script to start all agents and then the Streamlit app.

start "Research Agent" cmd /k "echo Starting Research Agent... && python -m Research_Agent.Research"
start "Editor Agent" cmd /k "echo Starting Editor Agent... && python -m Editor_Agent.Editor"
start "Writer Agent" cmd /k "echo Starting Writer Agent... && python -m Writer_Agent.Writer"

REM Wait for agents to start
ping 127.0.0.1 -n 6 > nul

echo Starting Google A2A Client...
streamlit run app.py
