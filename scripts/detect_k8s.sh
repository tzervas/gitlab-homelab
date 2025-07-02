#!/bin/bash
# Dynamic Kubernetes Backend Detection Script
# Detects microk8s, k3s, or upstream kubectl and exposes K8S_DISTRO variable
# Author: Tyler Zervas
# License: MIT

set -euo pipefail

# Initialize variables
export K8S_DISTRO=""
export K8S_VERSION=""
export K8S_CLUSTER_INFO=""

# Function to check if command exists in PATH
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect microk8s
detect_microk8s() {
    if command_exists microk8s; then
        # Check if microk8s is running
        if microk8s status --wait-ready --timeout 5 >/dev/null 2>&1; then
            K8S_DISTRO="microk8s"
            # Get microk8s version
            if command_exists microk8s.kubectl; then
                K8S_VERSION=$(microk8s.kubectl version --client --output=json 2>/dev/null | jq -r '.clientVersion.gitVersion' 2>/dev/null || echo "unknown")
            fi
            return 0
        fi
    fi
    return 1
}

# Function to detect k3s
detect_k3s() {
    if command_exists k3s; then
        # Check if k3s is accessible
        if k3s kubectl version --client >/dev/null 2>&1; then
            K8S_DISTRO="k3s"
            K8S_VERSION=$(k3s kubectl version --client --output=json 2>/dev/null | jq -r '.clientVersion.gitVersion' 2>/dev/null || echo "unknown")
            return 0
        fi
    fi
    
    # Also check for k3s kubectl
    if command_exists k3s-kubectl; then
        K8S_DISTRO="k3s"
        K8S_VERSION=$(k3s-kubectl version --client --output=json 2>/dev/null | jq -r '.clientVersion.gitVersion' 2>/dev/null || echo "unknown")
        return 0
    fi
    
    return 1
}

# Function to detect upstream kubectl
detect_upstream_kubectl() {
    if command_exists kubectl; then
        # Get kubectl version and check if it's not from microk8s or k3s
        local kubectl_path
        kubectl_path=$(command -v kubectl)
        
        # Check if kubectl path suggests it's not from microk8s or k3s
        if [[ ! "$kubectl_path" == *"microk8s"* ]] && [[ ! "$kubectl_path" == *"k3s"* ]]; then
            # Try to get version info
            if kubectl version --client >/dev/null 2>&1; then
                K8S_DISTRO="upstream"
                K8S_VERSION=$(kubectl version --client --output=json 2>/dev/null | jq -r '.clientVersion.gitVersion' 2>/dev/null || echo "unknown")
                
                # Try to get cluster info if kubectl can connect
                if kubectl cluster-info >/dev/null 2>&1; then
                    K8S_CLUSTER_INFO=$(kubectl cluster-info 2>/dev/null | head -1 || echo "cluster info unavailable")
                fi
                return 0
            fi
        fi
    fi
    return 1
}

# Function to detect custom kubectl binaries
detect_custom_kubectl() {
    local custom_paths=(
        "/usr/local/bin/kubectl"
        "/opt/kubectl/bin/kubectl"
        "$HOME/.local/bin/kubectl"
        "/snap/bin/kubectl"
    )
    
    for path in "${custom_paths[@]}"; do
        if [[ -x "$path" ]]; then
            # Check if this is different from the standard kubectl
            if [[ "$path" != "$(command -v kubectl 2>/dev/null || echo '')" ]]; then
                if "$path" version --client >/dev/null 2>&1; then
                    K8S_DISTRO="custom"
                    K8S_VERSION=$("$path" version --client --output=json 2>/dev/null | jq -r '.clientVersion.gitVersion' 2>/dev/null || echo "unknown")
                    export CUSTOM_KUBECTL_PATH="$path"
                    return 0
                fi
            fi
        fi
    done
    return 1
}

# Function to get current kubectl context
get_kubectl_context() {
    local kubectl_cmd=""
    
    case "$K8S_DISTRO" in
        "microk8s")
            kubectl_cmd="microk8s.kubectl"
            ;;
        "k3s")
            kubectl_cmd="k3s kubectl"
            ;;
        "upstream"|"custom")
            kubectl_cmd="kubectl"
            ;;
        *)
            return 1
            ;;
    esac
    
    if $kubectl_cmd config current-context >/dev/null 2>&1; then
        export K8S_CURRENT_CONTEXT=$($kubectl_cmd config current-context 2>/dev/null)
    else
        export K8S_CURRENT_CONTEXT="no-context"
    fi
}

# Main detection logic
main() {
    echo "Detecting Kubernetes backend..." >&2
    
    # Detection priority: microk8s -> k3s -> upstream -> custom
    if detect_microk8s; then
        echo "Detected: $K8S_DISTRO" >&2
    elif detect_k3s; then
        echo "Detected: $K8S_DISTRO" >&2
    elif detect_upstream_kubectl; then
        echo "Detected: $K8S_DISTRO" >&2
    elif detect_custom_kubectl; then
        echo "Detected: $K8S_DISTRO" >&2
    else
        echo "No Kubernetes backend detected" >&2
        K8S_DISTRO="none"
        return 1
    fi
    
    # Get context information
    get_kubectl_context
    
    # Export variables for consumption by other scripts
    export K8S_DISTRO
    export K8S_VERSION
    export K8S_CLUSTER_INFO
    
    # Print summary
    echo "K8S_DISTRO=$K8S_DISTRO" >&2
    echo "K8S_VERSION=$K8S_VERSION" >&2
    echo "K8S_CURRENT_CONTEXT=${K8S_CURRENT_CONTEXT:-unknown}" >&2
    
    return 0
}

# Allow script to be sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
