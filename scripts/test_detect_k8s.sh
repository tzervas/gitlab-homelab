#!/bin/bash
# Test Script for detect_k8s.sh
# Author: Tyler Zervas
# License: MIT

set -e

# Source the script to test
source ./scripts/detect_k8s.sh

# Function to simulate command existence in PATH
test_command_exists() {
    local cmd=$1
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "$cmd not found in the PATH"
        return 1
    fi
    echo "$cmd is available"
    return 0
}

# Test microk8s detection
if test_command_exists "microk8s"; then
    detect_microk8s && echo "Microk8s detected as expected" || echo "Microk8s not detected as expected"
else
    echo "Skipping Microk8s test: command not available"
fi

# Test k3s detection
if test_command_exists "k3s"; then
    detect_k3s && echo "K3s detected as expected" || echo "K3s not detected as expected"
else
    echo "Skipping k3s test: command not available"
fi

# Test upstream kubectl detection
if test_command_exists "kubectl"; then
    detect_upstream_kubectl && echo "Upstream kubectl detected as expected" || echo "Upstream kubectl not detected as expected"
else
    echo "Skipping upstream kubectl test: command not available"
fi

# Test custom kubectl detection
if test_command_exists "kubectl"; then
    detect_custom_kubectl && echo "Custom kubectl detected as expected" || echo "Custom kubectl not detected as expected"
else
    echo "Skipping custom kubectl test: command not available"
fi

# Final output
if [ -z "$K8S_DISTRO" ]; then
    echo "No Kubernetes distribution detected"
else
    echo "Kubernetes distribution detected - K8S_DISTRO: $K8S_DISTRO"
fi

exit 0

