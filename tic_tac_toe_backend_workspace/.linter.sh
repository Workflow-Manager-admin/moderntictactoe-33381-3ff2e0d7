#!/bin/bash
cd /home/kavia/workspace/code-generation/moderntictactoe-33381-3ff2e0d7/tic_tac_toe_backend_workspace/tic_tac_toe_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

