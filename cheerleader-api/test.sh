#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# These vars are required by settings.py at import time.
# Tests mock the LangGraph app so ANTHROPIC_API_KEY is not needed.
export PROMPT_FILE_PATH="${PROMPT_FILE_PATH:-chat/prompt.txt}"
export EMAIL_ADDRESS="${EMAIL_ADDRESS:-test@example.com}"
export PHONE_NUMBER="${PHONE_NUMBER:-555-0100}"

python3 manage.py test chat "$@"
