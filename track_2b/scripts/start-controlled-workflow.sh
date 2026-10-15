#!/bin/sh
set -eu

: "${LLM_NAME:?LLM_NAME must be set in .env}"
: "${LLM_BASE_URL:?LLM_BASE_URL must be set in .env}"
: "${LLM_API_KEY:?LLM_API_KEY must be set in .env}"

exec python3 -c '
import os
import sys
from pathlib import Path
sys.path.insert(0, "/workspace/src")
from operator_workflow import run_console
from workflow import generate_draft, load_fixture

state_dir = Path(os.environ.get("HERMES_HOME", "/opt/data")) / "email-framework"
fixture = load_fixture(Path("/workspace/data/test_contacts.json"))
def generate(preflight):
    return generate_draft(preflight, model_name=os.environ["LLM_NAME"], base_url=os.environ["LLM_BASE_URL"], api_key=os.environ["LLM_API_KEY"])
run_console(input_fn=input, output_fn=print, fixture=fixture, state_dir=state_dir, generate_fn=generate)
'
