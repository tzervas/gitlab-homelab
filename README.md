# GitLab HomeLab Infrastructure

A comprehensive GitLab HomeLab infrastructure project with dynamic Kubernetes backend detection and automation capabilities.

## 🚀 Features

### ✅ Completed Features

#### Dynamic Kubernetes Backend Detection
- **Multi-platform Detection**: Automatically detects `microk8s`, `k3s`, `upstream kubectl`, and custom kubectl installations
- **Cross-platform Support**: Shell script and Python implementations for Windows, macOS, and Linux compatibility
- **Environment Variables**: Exposes `K8S_DISTRO`, `K8S_VERSION`, `K8S_CURRENT_CONTEXT` for script consumption
- **Custom Binary Detection**: Searches common paths for custom kubectl installations
- **Context Awareness**: Detects and reports current kubectl contexts

### 🔧 Development Environment

- **DevContainer**: Fully configured development environment with cross-platform compatibility
- **Pre-commit Hooks**: Automated code quality checks and validation
- **Testing Suite**: Comprehensive idempotent tests without for-loops
- **Code Quality**: Integrated `ruff`, `mypy`, `black`, and `shellcheck`
- **Security**: Gitleaks integration for secret detection

## 📋 Planned Features

- [ ] **Backup Strategy**: Automated backup solutions for GitLab and Kubernetes
- [ ] **CI/CD Pipeline**: Comprehensive pipeline automation
- [ ] **DNS Strategy**: Dynamic DNS management and configuration
- [ ] **Monitoring Setup**: Observability and monitoring stack
- [ ] **Prerequisite Manager**: Automated dependency installation and management
- [ ] **Security Hardening**: Security policies and hardening configurations

## 🏗️ Project Structure

```
.
├── .devcontainer/          # Development container configuration
│   ├── devcontainer.json   # DevContainer settings
│   └── setup.sh           # Environment setup script
├── scripts/               # Automation scripts
│   ├── detect_k8s.sh      # Shell-based K8s detection
│   ├── detect_k8s.py      # Python-based K8s detection
│   ├── test_detect_k8s.sh # Shell script tests
│   ├── test_detect_k8s.py # Python script tests
│   └── example_usage.sh   # Usage examples
├── .pre-commit-config.yaml # Pre-commit hook configuration
├── .gitignore             # Git ignore rules
├── LICENSE                # MIT License
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Git with GPG signing configured
- Python 3.12+ (recommended)
- Docker (for DevContainer development)
- Optional: kubectl, microk8s, or k3s for testing

### Using the Kubernetes Detection

#### Shell Script Usage

```bash
# Source the script to get environment variables
source scripts/detect_k8s.sh

# Check detected distribution
echo "Detected Kubernetes: $K8S_DISTRO"
echo "Version: $K8S_VERSION"
echo "Context: $K8S_CURRENT_CONTEXT"

# Use in conditional logic
case "$K8S_DISTRO" in
    "microk8s")
        microk8s.kubectl get nodes
        ;;
    "k3s")
        k3s kubectl get nodes
        ;;
    "upstream"|"custom")
        kubectl get nodes
        ;;
    "none")
        echo "No Kubernetes detected"
        ;;
esac
```

#### Python Usage

```python
from scripts.detect_k8s import KubernetesDetector

detector = KubernetesDetector()
results = detector.detect()

print(f"Distribution: {results['K8S_DISTRO']}")
print(f"Version: {results['K8S_VERSION']}")
print(f"Context: {results['K8S_CURRENT_CONTEXT']}")
```

#### Environment Variables

The detection scripts expose the following environment variables:

- `K8S_DISTRO`: Detected Kubernetes distribution (`microk8s`, `k3s`, `upstream`, `custom`, `none`)
- `K8S_VERSION`: Kubernetes client version
- `K8S_CURRENT_CONTEXT`: Current kubectl context
- `K8S_CLUSTER_INFO`: Cluster information (when available)
- `CUSTOM_KUBECTL_PATH`: Path to custom kubectl binary (when detected)

### Running Tests

```bash
# Run shell script tests
bash scripts/test_detect_k8s.sh

# Run Python tests
python3 scripts/test_detect_k8s.py

# Run example usage
bash scripts/example_usage.sh
```

### Development Setup

#### Using DevContainer (Recommended)

1. Open the project in VS Code
2. Install the Dev Containers extension
3. Press `F1` and select "Dev Containers: Reopen in Container"
4. The environment will be automatically configured

#### Local Development

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install Python dependencies
pip install black mypy ruff pytest

# Install system dependencies
sudo apt-get install jq shellcheck  # On Ubuntu/Debian
```

## 🧪 Testing

The project follows strict testing guidelines:

- **No For-Loops**: Tests are idempotent and avoid for-loops as per project requirements
- **Cross-Platform**: Tests work on Windows, macOS, and Linux
- **Isolated**: Tests don't require actual Kubernetes installations
- **Comprehensive**: Both unit tests and integration tests included

### Test Commands

```bash
# All tests
python3 scripts/test_detect_k8s.py && bash scripts/test_detect_k8s.sh

# Python tests only
python3 scripts/test_detect_k8s.py

# Shell tests only
bash scripts/test_detect_k8s.sh

# Pre-commit validation
pre-commit run --all-files
```

## 🔒 Security

- **No Remote Code Execution**: All commands are executed locally with proper validation
- **Timeout Protection**: Command execution includes timeout protection
- **Secure Paths**: Only checks predefined safe paths for custom binaries
- **Gitleaks Integration**: Automatic secret detection in commits
- **GPG Signed Commits**: All commits must be GPG signed

## 🤝 Contributing

1. **Branch Naming**: Use `feature/`, `fix/`, or `docs/` prefixes
2. **Commit Signing**: All commits must be GPG signed
3. **Pre-commit Hooks**: Ensure all pre-commit checks pass
4. **Testing**: Add tests for new functionality
5. **Documentation**: Update documentation for new features

### Creating Feature Branches

```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Make changes and commit with GPG signing
git commit -S -m "feat: your feature description"

# Push and create PR
git push origin feature/your-feature-name
gh pr create --title "feat: Your Feature" --body "Description of changes"
```

## 📖 Documentation

- **API Documentation**: Comprehensive docstrings in all Python code
- **Usage Examples**: See `scripts/example_usage.sh`
- **Best Practices**: Follows DRY, SRP, and KISS principles
- **Cross-Platform**: Tested on Windows, macOS, and Linux

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Tyler Zervas

## 🔗 Repository

https://github.com/tzervas/gitlab-homelab

---

**Note**: This project is under active development. Check the issues and project board for current status and planned features.
