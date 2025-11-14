# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@customify.app**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Response Process

1. **Acknowledgment** - Within 48 hours
2. **Investigation** - We'll assess the severity and impact
3. **Fix Development** - We'll develop and test a fix
4. **Release** - We'll release a patched version
5. **Disclosure** - We'll publicly disclose the issue after users have had time to update

## Security Best Practices

### For Users

- Keep your installation up to date
- Use strong, unique passwords
- Enable 2FA when available
- Review access logs regularly
- Use HTTPS in production
- Keep dependencies updated

### For Contributors

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Follow secure coding guidelines
- Run security tests before submitting PRs
- Review dependencies for known vulnerabilities

## Known Security Considerations

### Authentication

- JWT tokens expire after 7 days
- Passwords are hashed with bcrypt (cost factor 12)
- Failed login attempts are logged
- Account lockout after 5 failed attempts (planned)

### Data Protection

- All passwords are hashed before storage
- Sensitive data encrypted at rest
- TLS 1.3 required for production
- Database credentials stored in AWS Secrets Manager

### API Security

- Rate limiting: 100 req/min per user
- CORS configured for specific origins
- Input validation with Pydantic
- SQL injection prevention via ORM
- XSS prevention via Content Security Policy

## Security Updates

We'll announce security updates via:
- GitHub Security Advisories
- Release notes (CHANGELOG.md)
- Email to registered security contacts

## Bug Bounty Program

We currently do not have a bug bounty program, but we appreciate responsible disclosure and will acknowledge security researchers who help improve our security.

## Contact

For security-related questions: security@customify.app
```

---

#### 8. **LICENSE** - Archivo de Licencia

**Archivo a crear:** `LICENSE`
```
MIT License

Copyright (c) 2024 Customify Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.