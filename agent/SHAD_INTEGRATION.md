# Shad group integration — evaluation only

## Requested target

- Group: `ریاضی۱-۱۰۱`
- Group GUID: `g0DhwiT05ffedba9a45513dfcfe78f72`
- Read messages sent after activation only; do not backfill history.
- Desired behavior: answer relevant math questions in the group.

## Current status

This document is an implementation plan, not an active integration. No Shad
account is connected, no session has been created, and no messages are read or
sent. The Agent remains planning-only.

## Findings from the public package documentation

Two distinct projects must not be confused:

- `aioshad`: PyPI documents a `Client(phone_number,
  session_directory=...)`, group filters, message handlers, and message-update
  polling. The documented update examples call
  `get_messages_updates(group_guid, state=0)`. Version 1.0.15 requires
  Python 3.11 or newer and is marked Beta. See
  https://pypi.org/project/aioshad/1.0.15/.
- `aioshad-py`: a separate project with a different API (`Client(session=...)`
  and a CLI login command). Its documentation says the session file contains
  decrypted authentication tokens and private keys. See
  https://pypi.org/project/aioshad-py/.

The `state=0` example does not document how to obtain an activation-time
cursor, whether update state is persisted, or what happens after process
restart/session renewal. The Dispatcher documentation mentions duplicate
message suppression but does not specify a durable cross-restart guarantee.
Therefore the public documentation alone cannot establish that pre-activation
messages will never reach handlers. Do not infer this guarantee from the
parameter name or default value.

The PyPI project homepage currently links to the maintainer's GitHub profile,
not to a clearly identified source repository for this exact release. The
1.0.15 source distribution is published without PyPI provenance metadata.
During this review, a repository containing the matching release source could
not be reliably identified and independently inspected. Treat the package
source and release-to-source correspondence as unverified until the maintainer
provides a direct repository/tag or verifiable build provenance.

These are unofficial third-party clients. No official public Shad developer
API or official approval for personal-account automation has been verified
during this review. Their APIs, compatibility, security, and service-policy
status are not guaranteed. An unofficial self-client can expose the account
to service restrictions and may stop working when Shad changes its protocol.

## Safe implementation gates

1. Prefer an official, documented Shad integration if one becomes available.
2. Before adopting an unofficial client, review its source, release history,
   dependencies, license, and security posture; pin an exact tested version.
3. Check runtime compatibility before installation: aioshad 1.0.15 requires
   Python 3.11 or newer. Confirm the deployment image/runtime meets this.
4. Implement a separate worker process, disabled by default, isolated from the
   public website and planning API.
5. Start in dry-run mode. Do not fetch chat history. Establish a reliable
   activation/update cursor before processing, and verify that no older
   messages are delivered to handlers. If this cannot be guaranteed, do not
   enable the worker.
6. Filter strictly to the configured group GUID; ignore messages authored by
   the connected account; deduplicate update IDs; enforce conservative rate
   limits; and restrict responses to educational math topics.
7. Do not log message bodies or student personal data. Keep only minimal
   operational metadata with short retention.
8. Provide a kill switch and teacher approval mode before any automatic reply.
9. Do not use the class group for protocol experiments. Since the owner has
   declined a test group, keep live polling and sending disabled unless a
   safe, verifiable cursor strategy can be established without that test.

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

Keep the integration disabled until the library source and update-cursor
behavior have been reviewed, the account owner has reviewed the unofficial
client risk, and the no-history guarantee can be demonstrated safely. Do not
enable automatic posting merely because deployment succeeds.

## Acceptance requirements before live use

- Prove that pre-activation messages are never delivered to the handler.
- Prove that each post-activation message is delivered at most once, including
  after worker restart and session renewal.
- Ignore messages from every other group and messages authored by the
  connected account.
- Ensure no message body or student-identifying data appears in logs.
- Ensure the kill switch stops polling promptly.
- Ensure dry-run mode never sends a reply.
- If the library cannot guarantee a stable update cursor across startup and
  reconnect, the integration must remain disabled.

## Current CI coverage

GitHub Actions currently checks Python compilation and the offline fail-closed
worker tests. It does not test authentication, Shad connectivity, update
ordering, or message delivery semantics.
