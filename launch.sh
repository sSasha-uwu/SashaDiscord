#!/usr/bin/env bash
set -euo pipefail
 
export PATH="$PATH:$HOME/.local/bin"
export PYTHONPATH=.
 
PROJECT_NAME=""
while IFS='=' read -r key value; do
    key="${key// /}"
    if [[ "$key" == "name" ]]; then
        PROJECT_NAME="${value//\"/}"
        PROJECT_NAME="${PROJECT_NAME// /}"
        break
    fi
done < project/pyproject.toml
 
echo -e "\033]0;${PROJECT_NAME}\007"
 
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
fi
 
uv self update
uv sync --project project
 
if ! uv run --project project project/main.py; then
    echo
    echo
    echo -e "\033[31mAn unexpected error occurred in ${PROJECT_NAME}. Send a screenshot of your console and your log files to @sasha_uwu on discord for assistance.\033[0m"
    read -rp "Press Enter to continue..."
    exit 1
fi
 
read -rp "Press Enter to continue..."
 
