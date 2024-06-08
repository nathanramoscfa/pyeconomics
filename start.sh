#!/bin/sh

# Export environment variables from .env
if [ -f .env ]; then
    export "$(grep -v '^#' .env | xargs)"
fi

# Clean previous workspace settings
rm -rf /root/.jupyter/lab/workspaces/*

# Create workspace directory
mkdir -p /root/.jupyter/lab/workspaces/unique-workspace

# Start JupyterLab with a command to open the notebook
exec jupyter lab \
    --ip=0.0.0.0 \
    --port=8080 \
    --no-browser \
    --allow-root \
    --notebook-dir=/app/examples \
    --LabApp.workspaces_dir=/root/.jupyter/lab/workspaces \
    --LabApp.default_url='/lab/tree/monetary_policy_rules/monetary_policy_rules.ipynb'
