#!/bin/bash
# start_all_agents.sh
# Shell script to start all agents and then the Streamlit app.

echo_status() {
  if [ $2 -eq 0 ]; then
    echo -e "\e[32m$1 started successfully!\e[0m"
  else
    echo -e "\e[31mFailed to start $1!\e[0m"
  fi
}

(gnome-terminal -- bash -c "python -m Research_Agent.Research; exec bash" && echo_status "Research Agent" $?) &
(sleep 1; gnome-terminal -- bash -c "python -m Editor_Agent.Editor; exec bash" && echo_status "Editor Agent" $?) &
(sleep 2; gnome-terminal -- bash -c "python -m Writer_Agent.Writer; exec bash" && echo_status "Writer Agent" $?) &

echo "Waiting for agents to start..."
sleep 5
echo -e "\e[34mStarting Google A2A Client...\e[0m"
streamlit run app.py
