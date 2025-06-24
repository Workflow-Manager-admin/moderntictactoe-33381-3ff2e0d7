#!/bin/bash
cd /home/kavia/workspace/code-generation/moderntictactoe-33381-3ff2e0d7/tic_tac_toe_frontend_workspace/tic_tac_toe_frontend
npm run build
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
   exit 1
fi

