# Persistent Project-Local Hermes Agent

## Purpose

This repository packages a minimal Hermes agent that runs through Docker. Its
identity and procedures are deliberately configured by the operator over time;
no legacy specialist workflow is active by default.

## Runtime and confidentiality

- The persistent project-local Hermes runtime is `/opt/data`, mounted from
  `./runtime/hermes`.
- `/workspace` is read-only in the container and contains versioned source,
  templates and documentation.
- Never read, display, copy or commit `.env`, credentials, access tokens,
  session databases, chat transcripts or logs.
- No external actions: no sending, publishing, contact, deployment, GitHub
  push, deletion outside the project runtime, or account changes without
  explicit operator approval.

## Configuration discipline

- `SOUL.md` in the runtime is the durable identity and core behaviour.
- Longer approved instructions belong under `/opt/data/instructions/`.
- An instruction stored only in a file is not automatically active; permanent
  required behaviour must be included in the SOUL or explicitly referenced by
  it.
- Prepare persistent changes as reviewable proposals. Apply them only after an
  explicit approval and record the outcome.
- Do not invent workflows, questions, paths or completed configuration steps.

## Source-control boundary

- `agent-profile/` is the versionable, canonical source for `SOUL.md`,
  `config.yaml` and approved `instructions/**/*.md`.
- After changing `agent-profile/`, use `make profile-apply` to apply it to the
  local runtime. This does not touch chats, state, logs or credentials.
- `runtime/` is local operational state and remains ignored by Git.
- `make profile-snapshot` is the deliberate reverse operation for importing
  already-reviewed manual runtime edits back into `agent-profile/`; it replaces
  the snapshot and must not be used by default.