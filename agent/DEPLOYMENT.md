# Cloud deployment

The service is container-ready and can be deployed to a managed container host
that supports Docker and secret environment variables.

## Required environment variables

- `GROQ_API_KEY`: Groq API key (store only in the host's secret manager).
- `GROQ_MODEL`: model identifier enabled for the Groq API project; defaults to
  `openai/gpt-oss-120b` in the application.
- `AGENT_ADMIN_TOKEN`: long, random bearer token generated for this service.

## Container settings

- Branch: `ai-agent-foundation`
- Runtime: Docker
- Service root directory: `agent`
- Dockerfile path relative to service root: `Dockerfile`
- Health check path: `/health`
- Port: use the platform-provided `PORT` environment variable.

## Security checklist before going public

1. Deploy as a private service or restrict inbound access where possible.
2. Keep the admin token and Groq key in the provider's secret manager.
3. Do not put secrets in GitHub files, browser JavaScript, or build arguments.
4. Configure HTTPS and rotate the admin token if it is exposed.
5. The current service only plans tasks. It has no GitHub write or deploy tools.
6. Never upload Shad session files, OTPs, cookies, or authentication tokens to
   GitHub, chat, build logs, or ordinary environment-variable values.

## Next implementation milestones

1. Add read-only repository context retrieval.
2. Add constrained file editing on short-lived branches.
3. Add static checks and tests in GitHub Actions.
4. Open draft pull requests and report their URLs.
5. Consider auto-merge only for low-risk changes after checks pass and branch
   protection is configured.
