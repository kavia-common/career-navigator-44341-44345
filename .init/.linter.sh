#!/bin/bash
cd /home/kavia/workspace/code-generation/career-navigator-44341-44345/career_platform_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

