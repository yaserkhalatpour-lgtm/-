# Cloud deployment

The service is container-ready and can be deployed to a managed container host
that supports Docker and secret environment variables.

## Required environment variables

- `OPENAI_API_KEY`: OpenAI API key (store only in the host's secret manager).
- `OPENAI_MODEL`: model identifier enabled for the API project.
- `AGENT_ADMIN_TOKEN`: long, random bearer token generated for this service.

## Container settings

- Dockerfile path: `agent/Dockerfile`
- Build context: repository root is **not** suitable for this Dockerfile as written;
  set the service root directory to `agent`.
- Health check path: `/health`
- Port: use the platform-provided `PORT` environment variable.

## Security checklist before going public

1. Deploy as a private service or restrict inbound access where possible.
2. Keep the admin token and OpenAI key in the provider's secret manager.
3. Do not put secrets in GitHub files, browser JavaScript, or build arguments.
4. Configure HTTPS and rotate the admin token if it is exposed.
5. The current service only plans tasks. It has no GitHub write or deploy tools.

## Next implementation milestones

1. Add read-only repository context retrieval.
2. Add constrained file editing on short-lived branches.
3. Add static checks and tests in GitHub Actions.
4. Open draft pull requests and report their URLs.
5. Consider auto-merge only for low-risk changes after checks pass and branch
   protection is configured.
