# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of tokcut seriously. If you discover a security vulnerability, please do **not** open a public issue.

### Reporting Process

1. **Contact**: Send details to [INSERT SECURITY EMAIL]
2. **PGP Key**: If needed, use our PGP key: [INSERT KEY URL]
3. **What to include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Affected versions
   - Potential impact
   - Any suggested fixes (if available)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Status Update**: Within 5 business days
- **Resolution**: We aim to release a fix within 30 days

### Disclosure Policy

We follow a coordinated disclosure process:

1. Vulnerability reported and verified
2. Fix developed and tested
3. Release prepared with security advisory
4. Public disclosure after patch is available

## Security Considerations for tokcut

### API Key Handling

- tokcut acts as a proxy and passes API keys in request headers
- API keys are **never** stored to disk or logged
- We recommend using environment variables for sensitive credentials

### Cache Data

- When using the `sqlite` backend, cached responses are stored in `cache.db`
- These may contain sensitive LLM responses — secure the database file appropriately
- Use the `memory` backend if you don't need persistent caching

### Network Security

- The proxy server listens on `0.0.0.0:8800` by default
- In production, place tokcut behind a reverse proxy (nginx, caddy) with TLS
- Use firewall rules to restrict access to trusted networks only

### Input Validation

- tokcut validates incoming request body structure via FastAPI
- Content from upstream LLM APIs is passed through as-is after compression
- Be aware that compressed responses may alter the original meaning — review for your use case

## Dependencies

We monitor our dependencies for known vulnerabilities. Run regularly:

```bash
pip-audit
# or
safety check
```

To report a vulnerability in a dependency, please notify us and we will update accordingly.
