#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file based on .env.example"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Function to run playbook with proper environment
run_playbook() {
    local playbook=$1
    echo "Running $playbook..."
    ansible-playbook -i inventory.ini "$playbook"
}

case "$1" in
    "cleanup")
        run_playbook k8s-cleanup.yml
        ;;
    "install")
        run_playbook k8s-install.yml
        ;;
    "audit")
        run_playbook k8s-audit-setup.yml
        ;;
    "all")
        run_playbook k8s-cleanup.yml
        run_playbook k8s-install.yml
        run_playbook k8s-audit-setup.yml
        ;;
    *)
        echo "Usage: $0 {cleanup|install|audit|all}"
        echo "  cleanup: Remove existing cluster"
        echo "  install: Install new cluster"
        echo "  audit: Configure audit logging"
        echo "  all: Run all playbooks in sequence"
        exit 1
        ;;
esac
