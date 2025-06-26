#!/bin/bash
cd /home/kavia/workspace/code-generation/eventmaster-60715-97e7ae85/event_manager_backend_workspace/event_manager_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

