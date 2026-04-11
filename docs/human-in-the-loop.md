# Human-in-the-Loop (Self-Hosted Dashboard)

The open-source core library automatically makes block/allow decisions based on risk scores.
The **self-hosted backend** adds Human-in-the-Loop (HITL) review capabilities for cases that cannot be handled by automated decisions alone. This covers medium-risk requests requiring human judgment, compliance audit trails, and multi-tenant policy management.

## Architecture

```
User Request
     |
     v
aigis core      <- pattern matching, risk scoring
     |
  CRITICAL ----------> Auto-block (no human review needed)
     |
  MEDIUM/HIGH --------> Review Queue (human review)
     |
   LOW ---------------> Auto-allow (no human review needed)
     |
     v
Human Reviewer       <- approve / reject / escalate
     |
     v
Audit Log            <- immutable event trail
```

## Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/killertcell428/aigis
cd aigis

# Copy and configure environment variables
cp .env.example .env
# Edit .env: set SECRET_KEY, OPENAI_API_KEY, POSTGRES_PASSWORD

# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Create the first admin user
docker compose exec backend python -m app.cli create-admin \
  --email admin@example.com --password changeme
```

Services:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Review Queue

Requests assessed as MEDIUM or HIGH are placed in the review queue.

### Reviewer Workflow

1. Log in to the dashboard at http://localhost:3000
2. Navigate to the **Review Queue**
3. For each item, perform one of the following:
   - **Approve** — forward the request to the LLM
   - **Reject** — permanently block the request
   - **Escalate** — route to a senior reviewer

### API Endpoints

```
GET  /api/v1/review/queue          List pending items
GET  /api/v1/review/{id}           Get item details
POST /api/v1/review/{id}/approve   Approve
POST /api/v1/review/{id}/reject    Reject
POST /api/v1/review/{id}/escalate  Escalate
```

Example:

```bash
curl -X POST http://localhost:8000/api/v1/review/abc123/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note": "Reviewed and approved — internal user, not a threat."}'
```

## Multi-Tenant Policy Management

Each tenant (team, product, or customer) can have its own policy.

```bash
# Create a tenant
curl -X POST http://localhost:8000/api/v1/admin/tenants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name": "Acme Corp", "policy": "strict"}'

# Update a tenant's policy
curl -X PUT http://localhost:8000/api/v1/policies/acme-corp \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"auto_block_threshold": 70, "custom_rules": [...]}'
```

## OpenAI-Compatible Proxy

The backend exposes an OpenAI-compatible proxy endpoint. Any OpenAI SDK client can connect to the self-hosted instance.

```python
import openai

client = openai.OpenAI(
    api_key="your-aigis-api-key",
    base_url="http://localhost:8000/api/v1/proxy",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

All requests are scanned and logged. MEDIUM/HIGH risk requests are placed in the review queue before being forwarded to OpenAI.

## Audit Log

All scan events are recorded in an immutable audit log.

```
GET /api/v1/audit?tenant=acme-corp&from=2026-01-01&to=2026-12-31
```

Each entry includes:
- `request_id` — UUID
- `tenant_id`
- `risk_score`, `risk_level`
- `reasons`, `remediation`
- `decision` — `allowed` / `blocked` / `pending_review`
- `reviewer_id` (if reviewed by a human)
- `timestamp`

## Scaling

For production deployments, the following is recommended:

- Place multiple `backend` replicas behind a load balancer
- Use managed PostgreSQL (e.g., AWS RDS, GCP Cloud SQL)
- Use managed Redis (e.g., AWS ElastiCache)
- Set `WORKERS=4` (or 2x CPU cores) in the backend environment

See `backend/README.md` for detailed deployment instructions.

## SaaS vs. Self-Hosted Comparison

| Feature                     | Core Library | Self-Hosted | SaaS (Coming Soon) |
|-----------------------------|:------------:|:-----------:|:-------------------:|
| Pattern detection           | Yes          | Yes         | Yes                 |
| Custom YAML policies        | Yes          | Yes         | Yes                 |
| Human-in-the-Loop queue     | --           | Yes         | Yes                 |
| Audit log                   | --           | Yes         | Yes                 |
| Multi-tenant management     | --           | Yes         | Yes                 |
| Analytics dashboard         | --           | Yes         | Yes                 |
| Managed hosting             | --           | --          | Yes                 |
| SSO / SAML                  | --           | --          | Yes                 |

Interested in the managed SaaS version? [Join the waitlist ->](https://github.com/killertcell428/aigis/discussions)
