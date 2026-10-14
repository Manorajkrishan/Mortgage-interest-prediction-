# Private Mortgage Intelligence demonstration

Build: repository-root Dockerfile, branch feat/mortgage-intelligence-v2-20261014.
Required Railway environment variables: APP_ENV=preview, DEMO_USER=preview, DEMO_PASSWORD=(random 24+ character secret).
The application fails closed with HTTP 503 if secrets are missing; it returns HTTP 401 and prompts for browser Basic Auth if supplied credentials are wrong.
Create a public HTTPS Railway domain only **after** credentials are set and build has passed.
This is a temporary synthetic-data-only demonstration. HTTP Basic is not bank-grade authentication. Do not use borrower PII.
Hosting may consume Railway monthly free credits and can incur charges on paid accounts.
Validate unauthenticated -> 401, authenticated -> 200, no cookies/tokens in URL, and all API/UI on one origin.
Access can be revoked by rotating DEMO_PASSWORD or removing the public domain.
