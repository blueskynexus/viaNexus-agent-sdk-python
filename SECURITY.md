# Security Policy

## Reporting Security Vulnerabilities

We take the security of the viaNexus Agent SDK seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities to: **security@vianexus.com**

Include the following information in your report:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity, typically 30-90 days

## Security Considerations

### API Key Management

🔒 **Critical**: Never hardcode API keys or secrets in your code.

**✅ Secure Practices:**
```python
import os

config = {
    "LLM_API_KEY": os.getenv("OPENAI_API_KEY"),  # Use environment variables
    "agentServers": {
        "viaNexus": {
            "software_statement": os.getenv("VIANEXUS_JWT_TOKEN")
        }
    }
}
```

**❌ Insecure Practices:**
```python
config = {
    "LLM_API_KEY": "sk-your-actual-key-here",  # Never do this!
}
```

### JWT Token Security

The SDK handles JWT tokens for authentication with viaNexus services.

**Security Features:**
- JWT parsing with validation
- Input sanitization for system prompts
- Length limits on extracted content
- Warning logs for unsigned tokens

**Production Recommendations:**
```python
# Enable signature verification in production
system_prompt = client._extract_system_prompt_from_jwt(
    jwt_token, 
    verify_signature=True  # Enable in production with proper key management
)
```

### File Storage Security

When using file-based memory storage:

**Security Features:**
- Path traversal protection
- Session ID validation
- Reserved filename prevention
- Directory isolation

**Secure Configuration:**
```python
# Use absolute paths and secure directories
client = AnthropicClient.with_file_memory_store(
    config,
    storage_path="/secure/app/conversations",  # Secure directory
    user_id="validated_user_id"
)
```

### Input Validation

All user inputs are validated for:
- Type checking (string validation)
- Length limits (max 100KB per question)
- Content sanitization (null byte prevention)
- Format validation

### Memory Isolation

**Session Isolation:**
- Each user/session has isolated memory space
- Session IDs are validated and sanitized
- Cross-session data leakage prevention

### Network Security

**HTTPS Only:**
- All API communications use HTTPS
- Certificate validation enabled
- No plaintext transmission of sensitive data

**Connection Security:**
```python
config = {
    "agentServers": {
        "viaNexus": {
            "server_url": "https://api.vianexus.com",  # Always use HTTPS
            "server_port": 443
        }
    }
}
```

## Secure Development Practices

### Environment Variables

Use environment variables for all sensitive configuration:

```bash
# .env file (never commit to version control)
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GEMINI_API_KEY=your-gemini-key-here
VIANEXUS_JWT_TOKEN=your-jwt-token-here
```

### Configuration Files

If using YAML configuration files:

```yaml
# config.yaml
development:
  LLM_API_KEY: "${OPENAI_API_KEY}"  # Use environment variable substitution
  agentServers:
    viaNexus:
      software_statement: "${VIANEXUS_JWT_TOKEN}"
```

### Logging Security

**Safe Logging:**
- API keys and tokens are not logged
- Sensitive user data is redacted
- Debug logs may contain conversation content

**Log Level Recommendations:**
```python
import logging

# Production: Use WARNING or ERROR level
logging.basicConfig(level=logging.WARNING)

# Development: Use DEBUG for troubleshooting
logging.basicConfig(level=logging.DEBUG)
```

## Dependency Security

### Regular Updates

Keep dependencies updated:
```bash
# Check for security updates
pip list --outdated

# Update dependencies
pip install --upgrade package-name
```

### Vulnerability Scanning

The project includes security-focused dependencies:
- `PyJWT>=2.8.0` - Secure JWT handling
- `cryptography>=41.0.0` - Cryptographic operations

## Deployment Security

### Production Checklist

- [ ] Environment variables configured
- [ ] JWT signature verification enabled
- [ ] Secure file storage paths
- [ ] HTTPS-only communication
- [ ] Log level set appropriately
- [ ] Dependencies updated
- [ ] Security scanning completed

### Container Security

When deploying in containers:

```dockerfile
# Use non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Secure file permissions
COPY --chown=appuser:appuser . /app
RUN chmod 600 /app/config/*
```

## Incident Response

If you suspect a security incident:

1. **Immediate Actions:**
   - Rotate affected API keys
   - Review access logs
   - Isolate affected systems

2. **Investigation:**
   - Collect relevant logs
   - Document timeline
   - Assess impact

3. **Recovery:**
   - Apply security patches
   - Update configurations
   - Monitor for recurrence

4. **Reporting:**
   - Notify security@vianexus.com
   - Document lessons learned
   - Update security measures

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Guidelines](https://python.org/dev/security/)
- [JWT Security Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

---

**Last Updated**: October 2024
**Version**: 1.0.0-pre12
