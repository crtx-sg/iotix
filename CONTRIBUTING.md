# Contributing to IoTix

Thank you for your interest in contributing to IoTix! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Issues

1. **Search existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide details**:
   - IoTix version
   - Operating system and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs or screenshots

### Suggesting Features

1. Open a GitHub issue with the "feature request" label
2. Describe the use case and motivation
3. Explain your proposed solution
4. Consider alternatives you've thought about

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make your changes**
4. **Write or update tests**
5. **Run the test suite**
6. **Commit with clear messages**
7. **Push and open a PR**

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- Git

### Local Development

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/iotix.git
cd iotix

# Install Python dependencies
cd services/device-engine
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node.js dependencies
cd ../../packages/device-schema
npm install

# Start dependencies
cd ../../deploy/docker
docker-compose up -d mqtt-broker kafka influxdb

# Run device engine
cd ../../services/device-engine
uvicorn src.main:app --reload --port 8080
```

### Running Tests

```bash
# Python tests
cd services/device-engine
pytest tests/ -v --cov=src

# TypeScript tests
cd packages/device-schema
npm test

# Robot Framework tests (requires running services)
cd examples/tests
robot --variable DEVICE_ENGINE_URL:http://localhost:8080 .
```

## Coding Standards

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Format with `black`
- Lint with `ruff`
- Maximum line length: 88 characters

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

### TypeScript

- Follow the project's ESLint configuration
- Use TypeScript strict mode
- Format with Prettier

```bash
# Format and lint
npm run lint
npm run format
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(device-engine): add CoAP protocol adapter
fix(test-engine): correct report generation for failed tests
docs(api): update device model schema documentation
```

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code improvements

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

### PR Description

Include:
- Summary of changes
- Related issue numbers
- Testing performed
- Screenshots (if UI changes)

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. Address review feedback
4. Squash commits before merge (if requested)

## Architecture Guidelines

### Adding New Features

1. **Device Engine**: Add to `services/device-engine/src/`
2. **Protocol Adapters**: Implement `ProtocolAdapter` interface in `adapters/`
3. **Telemetry Generators**: Extend `BaseGenerator` in `generators.py`
4. **API Endpoints**: Add to `main.py` with proper OpenAPI docs

### Adding New Services

1. Create service directory in `services/`
2. Include `requirements.txt` and `src/` structure
3. Add Dockerfile in `deploy/docker/`
4. Update `docker-compose.yml`
5. Add Helm chart if needed

### Database Changes

- Use migrations for schema changes
- Document data model changes
- Consider backward compatibility

## Testing Guidelines

### Unit Tests

- Test individual functions/classes
- Mock external dependencies
- Aim for >80% coverage

### Integration Tests

- Test API endpoints
- Use test fixtures
- Clean up test data

### End-to-End Tests

- Use Robot Framework
- Test realistic scenarios
- Include in CI pipeline

## Documentation

### Code Documentation

- Docstrings for all public functions
- Type hints for parameters and returns
- Examples in docstrings when helpful

### User Documentation

- Update docs/ for user-facing changes
- Include examples
- Keep API documentation current

## Release Process

1. Update CHANGELOG.md
2. Update version numbers
3. Create release PR
4. Tag release after merge
5. Publish Docker images
6. Update Helm chart

## Getting Help

- **Discord**: [Join our server](https://discord.gg/iotix)
- **GitHub Discussions**: Ask questions
- **Issues**: Report bugs

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md
- Release notes
- Project README

Thank you for contributing to IoTix!
