# Shad group integration — evaluation only

## Requested target

- Group: `ریاضی1-101`
- Group GUID: `g0DhwiT05ffedba9a45513dfcfe78f72`
- Read messages sent after activation only; do not backfill history.
- Desired behavior: answer relevant math questions in the group.

## Current status

This document is an implementation plan, not an active integration. No Shad
account is connected, no session has been created, and no messages are read or
sent. The Agent remains planning-only.

## Findings from the public package documentation

Two distinct projects must not be confused:

- `aioshad`: its PyPI documentation describes a `Client(phone_number,
  session_directory=...)`, message filters including a chat/group filter,
  message handlers, and message-update polling. It documents interactive
  phone/OTP authentication and a session directory. The package is marked
  Beta. See https://pypi.org/project/aioshad/.
- `aioshad-py`: a separate project with a different API (`Client(session=...)`
  and a CLI login command). Its documentation says the session file contains
  decrypted authentication tokens and private keys. See
  https://pypi.org/project/aioshad-py/.

These are unofficial third-party clients. No official public Shad developer
API or official approval for personal-account automation has been verified
during this review. Their APIs, compatibility, security, and service-policy
status are not guaranteed. An unofficial self-client can expose the account
to service restrictions and may stop working when Shad changes its protocol.

## Safe implementation gates

1. Prefer an official, documented Shad integration if one becomes available.
2. Before adopting an unofficial client, review its source, release history,
   dependencies, license, and security posture; pin an exact tested version.
3. Implement a separate worker process, disabled by default, isolated from the
   public website and planning API.
4. Start in dry-run mode. Do not fetch chat history. Establish a reliable
   activation/update cursor before processing, and verify experimentally that
   no older messages are delivered to handlers. If this cannot be guaranteed,
   do not enable the worker.
5. Filter strictly to the configured group GUID; ignore messages authored by
   the connected account; deduplicate update IDs; enforce conservative rate
   limits; and restrict responses to educational math topics.
6. Do not log message bodies or student personal data. Keep only minimal
   operational metadata with short retention.
7. Provide a kill switch and teacher approval mode before any automatic reply.
8. Test in a private test group before enabling the requested class group.

## Authentication rules

- If an interactive login is required, the account owner must complete it
  directly in a private terminal on the deployment host or another controlled
  environment. Do not relay OTPs or credentials through ChatGPT.
- Never request or paste OTPs, passwords, cookies, browser storage, auth
  headers, or session contents into chat.
- Session files must live in a private mounted secret volume, outside the
  repository. The repository ignores `sessions/` and `*.session`.
- Never commit session files or include them in logs, build artifacts, or
  support bundles.
- A session file is a bearer-like credential: anyone who obtains it may gain
  access to the account. Restrict filesystem permissions and access.

## Activation policy

Keep the integration disabled until the library and update-cursor behavior
have been tested, the account owner has reviewed the unofficial-client risk,
and a dry-run test has been explicitly approved. Do not enable automatic
posting merely because deployment succeeds.
