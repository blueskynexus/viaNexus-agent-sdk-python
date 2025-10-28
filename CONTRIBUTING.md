# Contributing to viaNexus Agent SDK

Thank you for your interest in contributing to the viaNexus Agent SDK for Python! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/viaNexus-agent-sdk-python.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- `uv` or `pip` for dependency management

### Installation

```bash
# Clone the repository
git clone https://github.com/blueskynexus/viaNexus-agent-sdk-python.git
cd viaNexus-agent-sdk-python

# Install dependencies
uv sync
# or
pip install -e .

# Install development dependencies
pip install pytest black flake8 mypy bandit
```

### Environment Setup

Create a `.env` file for development (never commit this file):

```bash
# .env
OPENAI_API_KEY=your-test-key-here
ANTHROPIC_API_KEY=your-test-key-here
GEMINI_API_KEY=your-test-key-here
VIANEXUS_JWT_TOKEN=your-test-jwt-here
```

## Security Requirements

### 🔒 Critical Security Rules

**All contributions must follow these security requirements:**

1. **No Hardcoded Secrets**
   - Never commit API keys, tokens, or passwords
   - Use environment variables or configuration files
   - Check with `git log --patch` before pushing

2. **JWT Security**
   - All JWT handling must include proper validation
   - Use `PyJWT` library for parsing
   - Never trust unsigned tokens in production

3. **Input Validation**
   - Validate all user inputs
   - Sanitize file paths and session IDs
   - Check for injection attacks

4. **Error Handling**
   - Use specific exception types
   - Avoid broad `except Exception` clauses
   - Don't expose sensitive information in error messages

### Security Checklist

Before submitting a PR, ensure:

- [ ] No hardcoded credentials or secrets
- [ ] All user inputs are validated
- [ ] File operations use secure paths
- [ ] JWT tokens are properly validated
- [ ] Error handling is specific and secure
- [ ] Dependencies are up to date
- [ ] Security tests pass

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

```bash
# Format code
black src/ examples/

# Check style
flake8 src/ examples/

# Type checking
mypy src/
```

### Code Quality Standards

1. **Type Hints**: All public functions must have type hints
2. **Docstrings**: Use Google-style docstrings
3. **Error Handling**: Use specific exception types
4. **Logging**: Use appropriate log levels

### Example Code Style

```python
async def ask_question(
    self, 
    question: str, 
    maintain_history: bool = False,
    use_memory: bool = False
) -> str:
    """
    Ask a question with optional conversation history.
    
    Args:
        question: The question to ask
        maintain_history: Whether to maintain conversation context
        use_memory: Whether to save messages to memory store
        
    Returns:
        The response as a string
        
    Raises:
        ValueError: If question is invalid
        ConnectionError: If API connection fails
    """
    # Validate input
    question = self._validate_question(question)
    
    try:
        # Implementation here
        pass
    except ValueError as e:
        logging.error(f"Invalid input: {e}")
        raise
    except ConnectionError as e:
        logging.error(f"Connection failed: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/

# Run security tests
bandit -r src/
```

### Test Requirements

1. **Unit Tests**: All new functions must have unit tests
2. **Integration Tests**: Test with real API calls (use test keys)
3. **Security Tests**: Test input validation and error handling
4. **Example Tests**: Ensure examples work correctly

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestAnthropicClient:
    def test_ask_question_validates_input(self):
        """Test that ask_question validates input properly."""
        client = AnthropicClient(config)
        
        # Test empty question
        with pytest.raises(ValueError, match="Question cannot be empty"):
            await client.ask_question("")
        
        # Test null bytes
        with pytest.raises(ValueError, match="null bytes"):
            await client.ask_question("test\x00question")
```

## Documentation

### Documentation Requirements

1. **API Documentation**: All public methods must be documented
2. **Examples**: Include working examples for new features
3. **Security Notes**: Document security considerations
4. **Migration Guides**: For breaking changes

### Documentation Style

```python
def new_feature(self, param: str) -> str:
    """
    Brief description of what this method does.
    
    Longer description with more details about the functionality,
    use cases, and any important considerations.
    
    Args:
        param: Description of the parameter
        
    Returns:
        Description of the return value
        
    Raises:
        ValueError: When param is invalid
        ConnectionError: When network fails
        
    Example:
        >>> client = AnthropicClient(config)
        >>> result = client.new_feature("example")
        >>> print(result)
        "Expected output"
        
    Security Note:
        This method validates all inputs to prevent injection attacks.
    """
```

## Pull Request Process

### Before Submitting

1. **Security Review**: Run security checklist
2. **Code Quality**: Run linters and formatters
3. **Tests**: Ensure all tests pass
4. **Documentation**: Update relevant documentation
5. **Examples**: Add or update examples if needed

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Security improvement

## Security Checklist
- [ ] No hardcoded secrets or credentials
- [ ] Input validation implemented
- [ ] Error handling is secure
- [ ] JWT handling follows security guidelines
- [ ] File operations use secure paths

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Examples work correctly

## Documentation
- [ ] Code comments updated
- [ ] API documentation updated
- [ ] Examples added/updated
- [ ] Security considerations documented
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Security Review**: Maintainers review for security issues
3. **Code Review**: Maintainers review code quality and design
4. **Testing**: Maintainers test functionality
5. **Merge**: After approval, changes are merged

## Security-Specific Contributions

### Reporting Security Issues

**Do not report security vulnerabilities through public issues.**

Email security issues to: **security@vianexus.com**

### Security Improvements

We welcome security improvements! Examples:

- Enhanced input validation
- Better error handling
- Dependency security updates
- Security documentation improvements
- Security test additions

### Security Review Process

Security-related PRs receive additional scrutiny:

1. **Security Team Review**: Dedicated security review
2. **Penetration Testing**: For significant changes
3. **Documentation Review**: Security implications documented
4. **Staged Rollout**: Gradual deployment for major changes

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and improve
- Follow security best practices

### Communication

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions
- **Security**: Use email for security-related matters
- **Chat**: Join our community chat (link in README)

## Release Process

### Version Numbering

We use semantic versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- `1.0.0-pre12` (pre-release)

### Release Checklist

- [ ] Security review completed
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Examples tested
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] Security scan completed

## Getting Help

### Resources

- **Documentation**: Check the README and docs/
- **Examples**: Look at examples/ directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub discussions

### Contact

- **General Questions**: GitHub discussions
- **Bug Reports**: GitHub issues
- **Security Issues**: security@vianexus.com
- **Maintainers**: See MAINTAINERS.md

---

Thank you for contributing to the viaNexus Agent SDK! Your contributions help make AI development more accessible and secure.
