#!/bin/bash
# Example usage of Kubernetes detection scripts
# Demonstrates how to consume K8S_DISTRO and other variables
# Author: Tyler Zervas
# License: MIT

set -euo pipefail

echo "=== Kubernetes Detection Example ==="

# Method 1: Source the shell script
echo "Method 1: Sourcing shell script"
if source ./scripts/detect_k8s.sh; then
    echo "Detection successful!"
    echo "  K8S_DISTRO: $K8S_DISTRO"
    echo "  K8S_VERSION: $K8S_VERSION"
    echo "  K8S_CURRENT_CONTEXT: ${K8S_CURRENT_CONTEXT:-unknown}"
    if [ -n "${CUSTOM_KUBECTL_PATH:-}" ]; then
        echo "  CUSTOM_KUBECTL_PATH: $CUSTOM_KUBECTL_PATH"
    fi
else
    echo "No Kubernetes detected via shell script"
fi

echo ""

# Method 2: Execute shell script and capture output
echo "Method 2: Executing shell script"
if ./scripts/detect_k8s.sh; then
    echo "Shell script executed successfully"
else
    echo "Shell script execution failed or no K8s found"
fi

echo ""

# Method 3: Use Python script
echo "Method 3: Using Python script"
if python3 ./scripts/detect_k8s.py; then
    echo "Python detection successful!"
    echo "Environment variables set by Python script:"
    env | grep ^K8S_ || echo "No K8S environment variables found"
else
    echo "Python detection failed or no K8s found"
fi

echo ""

# Method 4: Conditional logic based on detection
echo "Method 4: Conditional deployment logic example"
source ./scripts/detect_k8s.sh || true

case "$K8S_DISTRO" in
    "microk8s")
        echo "Detected MicroK8s - using microk8s.kubectl for deployment"
        KUBECTL_CMD="microk8s.kubectl"
        ;;
    "k3s")
        echo "Detected K3s - using k3s kubectl for deployment"
        KUBECTL_CMD="k3s kubectl"
        ;;
    "upstream")
        echo "Detected upstream kubectl - using standard kubectl"
        KUBECTL_CMD="kubectl"
        ;;
    "custom")
        echo "Detected custom kubectl at: ${CUSTOM_KUBECTL_PATH:-kubectl}"
        KUBECTL_CMD="${CUSTOM_KUBECTL_PATH:-kubectl}"
        ;;
    "none"|*)
        echo "No Kubernetes detected - skipping deployment"
        exit 0
        ;;
esac

# Example deployment command (commented out for safety)
echo "Would execute: $KUBECTL_CMD get nodes"
# $KUBECTL_CMD get nodes

echo ""
echo "=== Detection Complete ==="
