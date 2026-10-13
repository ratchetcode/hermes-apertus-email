#!/bin/sh
set -eu

: "${LLM_NAME:?LLM_NAME must be set in .env}"
: "${LLM_BASE_URL:?LLM_BASE_URL must be set in .env}"
: "${LLM_API_KEY:?LLM_API_KEY must be set in .env}"

runtime_dir="${HERMES_HOME:-/opt/data}"
template="/workspace/runtime-template/config.yaml"
soul_template="/workspace/runtime-template/SOUL.md"

mkdir -p "$runtime_dir"
if [ ! -f "$runtime_dir/config.yaml" ]; then
  cp "$template" "$runtime_dir/config.yaml"
fi
if [ ! -f "$runtime_dir/.email-framework-soul-v3" ]; then
  cp "$soul_template" "$runtime_dir/SOUL.md"
  rm -f "$runtime_dir/.email-framework-soul-v1" "$runtime_dir/.email-framework-soul-v2"
  : > "$runtime_dir/.email-framework-soul-v3"
fi
hermes config set plugins.enabled '["email-framework"]' >/dev/null

if [ "$#" -eq 0 ]; then
  set -- hermes gateway run --no-supervise --external-supervisor
fi

exec "$@"
