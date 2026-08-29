# Security notes

Scout is a demonstration application for imported business-lead data. It does not scrape websites, send outreach, or require third-party API credentials.

## Implemented safeguards

- CSV uploads are limited to UTF-8 files under 5 MB.
- Required fields, numeric ranges, text lengths, founding years, and website URL schemes are validated before database insertion.
- Domains and case-insensitive company/location pairs are deduplicated.
- Exported text that could be interpreted as a spreadsheet formula is escaped.
- The UI independently permits only `http` and `https` company links.
- SQLAlchemy parameterizes search and filter queries.
- API filter values use explicit allowlists.
- Production Nginx and API responses include defensive browser headers.
- Docker build contexts exclude local dependencies, caches, secrets, and development databases; published application ports bind to host loopback behind the TLS proxy.
- Secrets and local databases are ignored by Git; no API key is required.
- Dependency updates are monitored with Dependabot, and CI runs tests, linting, builds, dependency audit, and Compose validation.

## Production boundary

This five-hour prototype intentionally has no authentication or multi-tenancy and must not be exposed as a shared production service in its current form. Before handling real lead data, add identity and authorization, workspace isolation, TLS, audit logging, rate limits, encrypted backups, retention/deletion controls, database migrations, centralized monitoring, and a formal privacy review.

Report a suspected vulnerability privately to the repository owner rather than opening a public issue containing sensitive details.
