# Shad group integration — evaluation only

## Requested target

- Group: `ریاضی1-101`
- Group GUID: `g0DhwiT05ffedba9a45513dfcfe78f72`
- Read messages sent after activation only; do not backfill history.
- Desired behavior: draft/answer relevant math questions in the group.

## Current status

This document is an implementation plan, not an active integration. No Shad
account is connected, no session has been created, and no messages are read or
sent. The Agent remains planning-only.

## Library review

The public PyPI page for `aioshad` currently documents a Client lifecycle,
message updates, and message handlers. It is marked Beta and requires Python
3.11 or newer. PyPI metadata reports GPL-3.0-only while the page's README text
also says MIT; this licensing discrepancy must be resolved before adoption.
The release page also reports no publishing provenance for the listed release.
Therefore this repository does not install or execute the package yet.

## Safe implementation gates

1. Confirm a supported and permitted Shad integration method. The reviewed
   library is unofficial; account restrictions and service terms may apply.
2. Resolve package provenance, maintenance, security, and license questions.
3. Implement a separate worker process, disabled by default, isolated from the
   public website and planning API.
4. Start in dry-run mode. Process only the configured group and only new
   updates after the activation baseline; never fetch chat history.
5. Ignore messages authored by the connected account, deduplicate update IDs,
   enforce conservative rate limits, and restrict responses to educational
   math topics.
6. Do not log message bodies or student personal data. Keep only minimal
   operational metadata with short retention.
7. Provide a kill switch and teacher approval mode before any automatic reply.
8. Test with a private test group before enabling the requested class group.

## Authentication rules

- Authentication must be completed by the account owner through a secure,
  supported login flow on the deployment host.
- Never request or paste OTPs, passwords, cookies, browser storage, auth
  headers, or session contents into chat.
- Session files must live in a private mounted secret volume, outside the
  repository. The repository ignores `sessions/` and `*.session`.
- Never commit session files or include them in logs or support bundles.

## Activation policy

Keep the integration disabled until all gates above are satisfied and the
account owner explicitly approves a dry-run test. Do not enable automatic
posting merely because deployment succeeds.
