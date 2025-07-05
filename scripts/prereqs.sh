#!/bin/bash
# Prerequisite Management Script for GitLab Homelab
# Verifies and auto-installs required tools with OS detection
# Author: Tyler Zervas
# License: MIT
#
# Usage:
#   ./scripts/prereqs.sh [--check-only] [--install] [--verbose] [--skip-distro-tools]
#
# Options:
#   --check-only      Only check prerequisites, don't install
#   --install         Install missing prerequisites (default behavior)
#   --verbose         Enable verbose logging
#   --skip-distro-tools Skip installation of Kubernetes distro tools (microk8s, k3s)
#   --help            Show this help message

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/../logs/prereqs.log"
VERBOSE=false
CHECK_ONLY=false
SKIP_DISTRO_TOOLS=false

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Required tools
REQUIRED_TOOLS=(
    "git"
    "kubectl"
    "helm"
    "aws"
    "yq"
    "gh"
)

# Kubernetes distro tools (optional based on environment)
K8S_DISTRO_TOOLS=(
    "microk8s"
    "k3s"
)

# Initialize logging
init_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
    log "INFO" "Prerequisites check started at $(date)"
}

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    if [[ "$VERBOSE" == true || "$level" == "ERROR" || "$level" == "WARN" ]]; then
        case "$level" in
            "ERROR")
                echo -e "${RED}[ERROR]${NC} $message" >&2
                ;;
            "WARN")
                echo -e "${YELLOW}[WARN]${NC} $message"
                ;;
            "INFO")
                echo -e "${BLUE}[INFO]${NC} $message"
                ;;
            "SUCCESS")
                echo -e "${GREEN}[SUCCESS]${NC} $message"
                ;;
            *)
                echo "[$level] $message"
                ;;
        esac
    fi
}

# Detect operating system and set package manager
detect_os() {
    local os_type=""
    local pkg_manager=""
    local install_cmd=""
    local update_cmd=""
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Check for WSL
        if grep -qi microsoft /proc/version 2>/dev/null; then
            os_type="WSL"
            log "INFO" "Detected Windows Subsystem for Linux"
        else
            os_type="Linux"
        fi
        
        # Detect Linux distribution and package manager
        if command -v apt-get >/dev/null 2>&1; then
            pkg_manager="apt"
            install_cmd="apt-get install -y"
            update_cmd="apt-get update"
        elif command -v yum >/dev/null 2>&1; then
            pkg_manager="yum"
            install_cmd="yum install -y"
            update_cmd="yum update"
        elif command -v dnf >/dev/null 2>&1; then
            pkg_manager="dnf"
            install_cmd="dnf install -y"
            update_cmd="dnf update"
        elif command -v pacman >/dev/null 2>&1; then
            pkg_manager="pacman"
            install_cmd="pacman -S --noconfirm"
            update_cmd="pacman -Sy"
        else
            log "ERROR" "Unsupported Linux distribution - no known package manager found"
            exit 1
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        os_type="macOS"
        pkg_manager="brew"
        install_cmd="brew install"
        update_cmd="brew update"
        
        if ! command -v brew >/dev/null 2>&1; then
            log "ERROR" "Homebrew not found. Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
        
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        os_type="Windows"
        pkg_manager="winget"
        install_cmd="winget install"
        update_cmd="winget upgrade --all"
        
        if ! command -v winget >/dev/null 2>&1; then
            log "ERROR" "winget not found. Please ensure you're running Windows 10 1709+ with App Installer"
            exit 1
        fi
        
    else
        log "ERROR" "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    log "INFO" "Detected OS: $os_type with package manager: $pkg_manager"
    
    # Export variables for use in other functions
    export OS_TYPE="$os_type"
    export PKG_MANAGER="$pkg_manager"
    export INSTALL_CMD="$install_cmd"
    export UPDATE_CMD="$update_cmd"
}

# Check if a tool is installed
check_tool() {
    local tool="$1"
    local version_cmd="$2"
    local expected_pattern="$3"
    
    if command -v "$tool" >/dev/null 2>&1; then
        if [[ -n "$version_cmd" ]]; then
            local version_output
            version_output=$(eval "$version_cmd" 2>/dev/null || echo "version check failed")
            if [[ -n "$expected_pattern" && ! "$version_output" =~ $expected_pattern ]]; then
                log "WARN" "$tool found but version check failed: $version_output"
                return 1
            fi
            log "INFO" "$tool is installed: $version_output"
        else
            log "INFO" "$tool is installed"
        fi
        return 0
    else
        log "INFO" "$tool is not installed"
        return 1
    fi
}

# Get package name for different package managers
get_package_name() {
    local tool="$1"
    local pkg_manager="$2"
    
    case "$tool" in
        "git")
            echo "git"
            ;;
        "kubectl")
            case "$pkg_manager" in
                "apt") echo "kubectl" ;;
                "brew") echo "kubectl" ;;
                "yum"|"dnf") echo "kubectl" ;;
                "pacman") echo "kubectl" ;;
                "winget") echo "Kubernetes.kubectl" ;;
                *) echo "kubectl" ;;
            esac
            ;;
        "helm")
            case "$pkg_manager" in
                "apt") echo "helm" ;;
                "brew") echo "helm" ;;
                "yum"|"dnf") echo "helm" ;;
                "pacman") echo "helm" ;;
                "winget") echo "Helm.Helm" ;;
                *) echo "helm" ;;
            esac
            ;;
        "aws")
            case "$pkg_manager" in
                "apt") echo "awscli" ;;
                "brew") echo "awscli" ;;
                "yum"|"dnf") echo "awscli" ;;
                "pacman") echo "aws-cli" ;;
                "winget") echo "Amazon.AWSCLI" ;;
                *) echo "awscli" ;;
            esac
            ;;
        "yq")
            case "$pkg_manager" in
                "apt") echo "yq" ;;
                "brew") echo "yq" ;;
                "yum"|"dnf") echo "yq" ;;
                "pacman") echo "yq" ;;
                "winget") echo "MikeFarah.yq" ;;
                *) echo "yq" ;;
            esac
            ;;
        "gh")
            case "$pkg_manager" in
                "apt") echo "gh" ;;
                "brew") echo "gh" ;;
                "yum"|"dnf") echo "gh" ;;
                "pacman") echo "github-cli" ;;
                "winget") echo "GitHub.cli" ;;
                *) echo "gh" ;;
            esac
            ;;
        "microk8s")
            case "$pkg_manager" in
                "apt") echo "microk8s" ;;
                "brew") echo "microk8s" ;;
                *) echo "microk8s" ;;
            esac
            ;;
        "k3s")
            # k3s typically installed via curl script, not package manager
            echo "k3s"
            ;;
        *)
            echo "$tool"
            ;;
    esac
}

# Install a tool using the detected package manager
install_tool() {
    local tool="$1"
    local package_name
    package_name=$(get_package_name "$tool" "$PKG_MANAGER")
    
    log "INFO" "Installing $tool (package: $package_name)..."
    
    # Special handling for tools that require custom installation
    case "$tool" in
        "kubectl")
            install_kubectl
            ;;
        "helm")
            install_helm
            ;;
        "k3s")
            install_k3s
            ;;
        *)
            # Standard package manager installation
            if ! eval "sudo $INSTALL_CMD $package_name" >> "$LOG_FILE" 2>&1; then
                log "ERROR" "Failed to install $tool"
                return 1
            fi
            ;;
    esac
    
    log "SUCCESS" "$tool installed successfully"
    return 0
}

# Custom kubectl installation
install_kubectl() {
    case "$OS_TYPE" in
        "Linux"|"WSL")
            if [[ "$PKG_MANAGER" == "apt" ]]; then
                # Add Kubernetes apt repository
                curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
                echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
                sudo apt-get update
                sudo apt-get install -y kubectl
            else
                # Direct binary installation for other Linux distros
                local kubectl_version
                kubectl_version=$(curl -L -s https://dl.k8s.io/release/stable.txt)
                curl -LO "https://dl.k8s.io/release/${kubectl_version}/bin/linux/amd64/kubectl"
                sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
                rm kubectl
            fi
            ;;
        "macOS")
            brew install kubectl
            ;;
        "Windows")
            winget install Kubernetes.kubectl
            ;;
    esac
}

# Custom helm installation
install_helm() {
    case "$OS_TYPE" in
        "Linux"|"WSL")
            curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
            ;;
        "macOS")
            brew install helm
            ;;
        "Windows")
            winget install Helm.Helm
            ;;
    esac
}

# Custom k3s installation (Linux only)
install_k3s() {
    if [[ "$OS_TYPE" == "Linux" || "$OS_TYPE" == "WSL" ]]; then
        curl -sfL https://get.k3s.io | sh -
        # Add current user to k3s group if not root
        if [[ "$EUID" -ne 0 ]]; then
            sudo usermod -aG k3s "$USER"
            log "INFO" "Added user to k3s group. You may need to log out and back in for changes to take effect."
        fi
    else
        log "WARN" "k3s installation not supported on $OS_TYPE"
        return 1
    fi
}

# Setup package repositories if needed
setup_repositories() {
    case "$PKG_MANAGER" in
        "apt")
            # Add GitHub CLI repository
            if ! check_tool "gh" "" ""; then
                curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
                sudo apt-get update
            fi
            ;;
        "yum"|"dnf")
            # Add GitHub CLI repository for RHEL/CentOS/Fedora
            if ! check_tool "gh" "" ""; then
                sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo || \
                sudo yum-config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
            fi
            ;;
    esac
}

# Update package manager cache
update_package_cache() {
    log "INFO" "Updating package manager cache..."
    case "$PKG_MANAGER" in
        "apt")
            sudo apt-get update >> "$LOG_FILE" 2>&1
            ;;
        "brew")
            brew update >> "$LOG_FILE" 2>&1
            ;;
        "yum"|"dnf")
            sudo $UPDATE_CMD >> "$LOG_FILE" 2>&1
            ;;
        "pacman")
            sudo pacman -Sy >> "$LOG_FILE" 2>&1
            ;;
        "winget")
            winget source update >> "$LOG_FILE" 2>&1
            ;;
    esac
}

# Check all prerequisites
check_prerequisites() {
    local missing_tools=()
    local tool_checks=(
        "git:git --version:version"
        "kubectl:kubectl version --client --short 2>/dev/null || kubectl version --client:Client Version"
        "helm:helm version --short:version"
        "aws:aws --version:aws-cli"
        "yq:yq --version:yq"
        "gh:gh --version:gh version"
    )
    
    log "INFO" "Checking required tools..."
    
    for tool_check in "${tool_checks[@]}"; do
        IFS=':' read -r tool version_cmd pattern <<< "$tool_check"
        if ! check_tool "$tool" "$version_cmd" "$pattern"; then
            missing_tools+=("$tool")
        fi
    done
    
    # Check Kubernetes distro tools if not skipped
    if [[ "$SKIP_DISTRO_TOOLS" == false ]]; then
        log "INFO" "Checking Kubernetes distro tools..."
        for tool in "${K8S_DISTRO_TOOLS[@]}"; do
            if ! check_tool "$tool" "" ""; then
                log "INFO" "$tool not found (optional for some environments)"
            fi
        done
    fi
    
    if [[ ${#missing_tools[@]} -eq 0 ]]; then
        log "SUCCESS" "All required tools are installed"
        return 0
    else
        log "WARN" "Missing tools: ${missing_tools[*]}"
        return 1
    fi
}

# Install missing prerequisites
install_prerequisites() {
    local missing_tools=()
    local tool_checks=(
        "git:git --version:version"
        "kubectl:kubectl version --client --short 2>/dev/null || kubectl version --client:Client Version"
        "helm:helm version --short:version"
        "aws:aws --version:aws-cli"
        "yq:yq --version:yq"
        "gh:gh --version:gh version"
    )
    
    # Setup repositories first
    setup_repositories
    
    # Update package cache
    update_package_cache
    
    log "INFO" "Installing missing tools..."
    
    for tool_check in "${tool_checks[@]}"; do
        IFS=':' read -r tool version_cmd pattern <<< "$tool_check"
        if ! check_tool "$tool" "$version_cmd" "$pattern"; then
            missing_tools+=("$tool")
            if ! install_tool "$tool"; then
                log "ERROR" "Failed to install $tool"
                return 1
            fi
        fi
    done
    
    # Install Kubernetes distro tools if not skipped and on Linux
    if [[ "$SKIP_DISTRO_TOOLS" == false && ("$OS_TYPE" == "Linux" || "$OS_TYPE" == "WSL") ]]; then
        log "INFO" "Installing Kubernetes distro tools..."
        for tool in "${K8S_DISTRO_TOOLS[@]}"; do
            if ! check_tool "$tool" "" ""; then
                log "INFO" "Installing $tool (optional)..."
                if ! install_tool "$tool"; then
                    log "WARN" "Failed to install $tool (optional)"
                fi
            fi
        done
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log "SUCCESS" "Installation completed for tools: ${missing_tools[*]}"
    fi
    
    return 0
}

# Show help
show_help() {
    cat << EOF
GitLab Homelab Prerequisites Management Script

USAGE:
    ./scripts/prereqs.sh [OPTIONS]

OPTIONS:
    --check-only      Only check prerequisites, don't install anything
    --install         Install missing prerequisites (default behavior)
    --verbose         Enable verbose logging output
    --skip-distro-tools Skip Kubernetes distro tools (microk8s, k3s)
    --help            Show this help message

DESCRIPTION:
    This script verifies and auto-installs required tools for the GitLab Homelab project.
    It automatically detects your operating system and uses the appropriate package manager.

REQUIRED TOOLS:
    - git: Version control system
    - kubectl: Kubernetes command-line tool
    - helm: Kubernetes package manager
    - aws-cli: AWS command-line interface
    - yq: YAML processor
    - gh: GitHub CLI

OPTIONAL TOOLS (Linux only):
    - microk8s: Lightweight Kubernetes distribution
    - k3s: Lightweight Kubernetes distribution

SUPPORTED PLATFORMS:
    - Linux (Ubuntu/Debian, RHEL/CentOS/Fedora, Arch)
    - macOS (with Homebrew)
    - Windows (with winget)
    - Windows Subsystem for Linux (WSL)

EXAMPLES:
    # Check what's installed without installing anything
    ./scripts/prereqs.sh --check-only

    # Install missing tools with verbose output
    ./scripts/prereqs.sh --verbose

    # Install only core tools, skip Kubernetes distributions
    ./scripts/prereqs.sh --skip-distro-tools

LOGS:
    Detailed logs are written to: logs/prereqs.log

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --check-only)
                CHECK_ONLY=true
                shift
                ;;
            --install)
                CHECK_ONLY=false
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --skip-distro-tools)
                SKIP_DISTRO_TOOLS=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    parse_arguments "$@"
    
    init_logging
    
    log "INFO" "GitLab Homelab Prerequisites Management Script"
    log "INFO" "Author: Tyler Zervas | License: MIT"
    
    detect_os
    
    if [[ "$CHECK_ONLY" == true ]]; then
        log "INFO" "Running in check-only mode"
        if check_prerequisites; then
            log "SUCCESS" "All prerequisites are satisfied"
            exit 0
        else
            log "ERROR" "Some prerequisites are missing"
            exit 1
        fi
    else
        log "INFO" "Running in install mode"
        if ! check_prerequisites; then
            log "INFO" "Installing missing prerequisites..."
            if install_prerequisites; then
                log "SUCCESS" "Prerequisites installation completed successfully"
                # Verify installation
                if check_prerequisites; then
                    log "SUCCESS" "All prerequisites are now installed and verified"
                else
                    log "ERROR" "Some tools may not have installed correctly"
                    exit 1
                fi
            else
                log "ERROR" "Prerequisites installation failed"
                exit 1
            fi
        else
            log "SUCCESS" "All prerequisites are already satisfied"
        fi
    fi
    
    log "INFO" "Prerequisites check completed at $(date)"
}

# Run main function with all arguments
main "$@"
