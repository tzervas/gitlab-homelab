# Developer Guide

## Development Environment Setup

### Prerequisites

- Python 3.12 or later
- Git with GPG signing configured
- UV package manager

### Installing UV

```bash
# Install UV using pip
pip install uv

# Verify installation
uv --version
```

### Project Setup

1. Clone the repository:
```bash
git clone https://github.com/tzervas/gitlab-homelab.git
cd gitlab-homelab
```

2. Create and activate a virtual environment:
```bash
# Create new virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies using UV:
```bash
# Install all dependencies from requirements.txt
uv sync

# Update dependencies and lockfile
uv sync --update
```

## Dependency Management with UV

### Adding New Dependencies

To add a new package:
```bash
# Add a new package
uv add package_name

# Add a development dependency
uv add --dev package_name
```

### Updating Dependencies

```bash
# Update all dependencies
uv sync --update

# Update lockfile
uv lock --update
```

### Managing Virtual Environments

UV integrates with Python's built-in venv module. Always ensure you're working within the virtual environment:

```bash
# Check if you're in a virtual environment
which python

# Activate if needed
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows
```

### Dependency Resolution

UV automatically handles dependency resolution when installing or updating packages:

```bash
# Resolve and install dependencies
uv sync

# View dependency tree
uv list
```

## Development Workflow

1. Activate your virtual environment
2. Use UV to manage dependencies
3. Run tests to ensure everything works
4. Use pre-commit hooks for code quality

### Common UV Commands

- `uv sync`: Install dependencies from requirements.txt
- `uv add package_name`: Add a new package
- `uv remove package_name`: Remove a package
- `uv lock`: Generate/update lockfile
- `uv list`: List installed packages
- `uv pip compile`: Generate requirements.txt from source dependencies

## Troubleshooting

### Common Issues

1. Virtual Environment Not Activated:
   - Symptom: UV commands fail or use system Python
   - Solution: Activate virtual environment

2. Dependency Conflicts:
   - Symptom: UV sync fails with conflict errors
   - Solution: Run `uv sync --update` to resolve conflicts

3. Lockfile Synchronization:
   - Symptom: Inconsistent dependencies between environments
   - Solution: Run `uv lock --update` to regenerate lockfile

## Best Practices

1. Always use virtual environments
2. Keep requirements.txt updated
3. Use UV's lockfile for consistent environments
4. Regularly update dependencies for security
5. Test after dependency changes
