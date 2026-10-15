#!/bin/sh
set -eu

: "${LLM_NAME:?LLM_NAME must be set in .env}"
: "${LLM_BASE_URL:?LLM_BASE_URL must be set in .env}"
: "${LLM_API_KEY:?LLM_API_KEY must be set in .env}"

runtime_dir="${HERMES_HOME:-/opt/data}"
template="/workspace/runtime-template/config.yaml"
soul_template="/workspace/runtime-template/SOUL.md"
profile_skills_dir="/workspace/profile-skills"

mkdir -p "$runtime_dir"
if [ ! -f "$runtime_dir/config.yaml" ]; then
  cp "$template" "$runtime_dir/config.yaml"
fi
if [ ! -f "$runtime_dir/SOUL.md" ]; then
  cp "$soul_template" "$runtime_dir/SOUL.md"
fi
hermes config set plugins.enabled '[]' >/dev/null
hermes config set toolsets '["hermes-cli"]' >/dev/null

# The versioned profile-skills directory is the complete allowed skill set.
rm -rf "$runtime_dir/skills"
mkdir -p "$runtime_dir/skills"
if [ -d "$profile_skills_dir" ]; then
  cp -R "$profile_skills_dir/." "$runtime_dir/skills/"
fi
: > "$runtime_dir/.no-bundled-skills"

if [ "$#" -eq 0 ]; then
  set -- hermes gateway run --no-supervise --external-supervisor
fi

exec "$@"
