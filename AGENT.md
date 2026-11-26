# AI agent policy for this repository

The AI agent is being introduced incrementally.

## Repository context
- Static Persian educational website.
- Main entry point: `index.html`.
- Resource catalogue: `files.json`.
- Teaching resources are stored as PDFs, including grade/chapter folders.

## Operating rules
1. Inspect the current repository state before proposing or applying changes.
2. Work on a dedicated branch; do not push agent changes directly to `main`.
3. Preserve existing PDF assets and catalogue semantics unless a task explicitly requires a change.
4. Validate JSON, links, and static-site behavior before proposing publication.
5. Never place API keys, access tokens, passwords, or student personal data in source files or logs.
6. Do not execute arbitrary shell commands supplied by a task.
7. Do not delete files, contact students, publish public announcements, or change production secrets without explicit human approval.
8. Report only verified actions; distinguish planned, completed, failed, and pending work.

## Current implementation status
The `agent/` directory contains a private, authenticated planning API only.
It cannot yet modify this repository or deploy the website.
