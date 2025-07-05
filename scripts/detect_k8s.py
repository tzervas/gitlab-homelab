#!/usr/bin/env python3
"""
Dynamic Kubernetes Backend Detection Module
Detects microk8s, k3s, or upstream kubectl and exposes K8S_DISTRO variable

Author: Tyler Zervas
License: MIT
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


class KubernetesDetector:
    """
    Detects Kubernetes distributions and provides environment variables
    for consumption by other scripts.
    """

    def __init__(self) -> None:
        """Initialize the Kubernetes detector."""
        self.k8s_distro: str = ""
        self.k8s_version: str = ""
        self.k8s_cluster_info: str = ""
        self.k8s_current_context: str = ""
        self.custom_kubectl_path: str = ""

    def command_exists(self, command: str) -> bool:
        """
        Check if a command exists in PATH.
        
        Args:
            command: The command name to check
            
        Returns:
            True if command exists, False otherwise
        """
        return shutil.which(command) is not None

    def run_command(self, cmd: list[str], timeout: int = 10) -> Tuple[bool, str]:
        """
        Run a command and return success status and output.
        
        Args:
            cmd: List of command arguments
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.returncode == 0, result.stdout
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return False, ""

    def get_kubectl_version(self, kubectl_cmd: str) -> str:
        """
        Get kubectl version from command.
        
        Args:
            kubectl_cmd: The kubectl command to use
            
        Returns:
            Version string or "unknown"
        """
        cmd = kubectl_cmd.split() + ["version", "--client", "--output=json"]
        success, output = self.run_command(cmd)
        
        if success and output:
            try:
                version_data = json.loads(output)
                return version_data.get("clientVersion", {}).get("gitVersion", "unknown")
            except (json.JSONDecodeError, KeyError):
                pass
        
        return "unknown"

    def detect_microk8s(self) -> bool:
        """
        Detect microk8s installation.
        
        Returns:
            True if microk8s is detected and running
        """
        if not self.command_exists("microk8s"):
            return False
            
        # Check if microk8s is running
        success, _ = self.run_command(["microk8s", "status", "--wait-ready", "--timeout", "5"])
        if success:
            self.k8s_distro = "microk8s"
            if self.command_exists("microk8s.kubectl"):
                self.k8s_version = self.get_kubectl_version("microk8s.kubectl")
            return True
            
        return False

    def detect_k3s(self) -> bool:
        """
        Detect k3s installation.
        
        Returns:
            True if k3s is detected
        """
        # Check for k3s command
        if self.command_exists("k3s"):
            success, _ = self.run_command(["k3s", "kubectl", "version", "--client"])
            if success:
                self.k8s_distro = "k3s"
                self.k8s_version = self.get_kubectl_version("k3s kubectl")
                return True
        
        # Check for k3s-kubectl
        if self.command_exists("k3s-kubectl"):
            self.k8s_distro = "k3s"
            self.k8s_version = self.get_kubectl_version("k3s-kubectl")
            return True
            
        return False

    def detect_upstream_kubectl(self) -> bool:
        """
        Detect upstream kubectl installation.
        
        Returns:
            True if upstream kubectl is detected
        """
        if not self.command_exists("kubectl"):
            return False
            
        kubectl_path = shutil.which("kubectl")
        if kubectl_path and "microk8s" not in kubectl_path and "k3s" not in kubectl_path:
            success, _ = self.run_command(["kubectl", "version", "--client"])
            if success:
                self.k8s_distro = "upstream"
                self.k8s_version = self.get_kubectl_version("kubectl")
                
                # Try to get cluster info
                cluster_success, cluster_output = self.run_command(["kubectl", "cluster-info"])
                if cluster_success and cluster_output:
                    self.k8s_cluster_info = cluster_output.split("\n")[0] if cluster_output else "cluster info unavailable"
                
                return True
                
        return False

    def detect_custom_kubectl(self) -> bool:
        """
        Detect custom kubectl binaries.
        
        Returns:
            True if custom kubectl is detected
        """
        custom_paths = [
            "/usr/local/bin/kubectl",
            "/opt/kubectl/bin/kubectl",
            f"{Path.home()}/.local/bin/kubectl",
            "/snap/bin/kubectl"
        ]
        
        standard_kubectl = shutil.which("kubectl")
        
        for path in custom_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                if path != standard_kubectl:
                    success, _ = self.run_command([path, "version", "--client"])
                    if success:
                        self.k8s_distro = "custom"
                        self.k8s_version = self.get_kubectl_version(path)
                        self.custom_kubectl_path = path
                        return True
                        
        return False

    def get_kubectl_context(self) -> None:
        """Get current kubectl context based on detected distribution."""
        kubectl_cmd_map = {
            "microk8s": ["microk8s.kubectl"],
            "k3s": ["k3s", "kubectl"],
            "upstream": ["kubectl"],
            "custom": ["kubectl"]
        }
        
        kubectl_cmd = kubectl_cmd_map.get(self.k8s_distro)
        if kubectl_cmd:
            success, output = self.run_command(kubectl_cmd + ["config", "current-context"])
            self.k8s_current_context = output.strip() if success and output else "no-context"

    def detect(self) -> Dict[str, str]:
        """
        Run detection logic and return results.
        
        Returns:
            Dictionary containing detection results
        """
        print("Detecting Kubernetes backend...", file=sys.stderr)
        
        # Detection priority: microk8s -> k3s -> upstream -> custom
        detected = (
            self.detect_microk8s() or 
            self.detect_k3s() or 
            self.detect_upstream_kubectl() or 
            self.detect_custom_kubectl()
        )
        
        if not detected:
            print("No Kubernetes backend detected", file=sys.stderr)
            self.k8s_distro = "none"
        else:
            print(f"Detected: {self.k8s_distro}", file=sys.stderr)
            self.get_kubectl_context()
        
        # Prepare results
        results = {
            "K8S_DISTRO": self.k8s_distro,
            "K8S_VERSION": self.k8s_version,
            "K8S_CLUSTER_INFO": self.k8s_cluster_info,
            "K8S_CURRENT_CONTEXT": self.k8s_current_context,
        }
        
        if self.custom_kubectl_path:
            results["CUSTOM_KUBECTL_PATH"] = self.custom_kubectl_path
            
        # Set environment variables
        for key, value in results.items():
            os.environ[key] = value
            
        # Print summary
        print(f"K8S_DISTRO={self.k8s_distro}", file=sys.stderr)
        print(f"K8S_VERSION={self.k8s_version}", file=sys.stderr)
        print(f"K8S_CURRENT_CONTEXT={self.k8s_current_context}", file=sys.stderr)
        
        return results


def main() -> int:
    """Main entry point."""
    detector = KubernetesDetector()
    results = detector.detect()
    
    # Return non-zero if no k8s detected
    return 0 if results["K8S_DISTRO"] != "none" else 1


if __name__ == "__main__":
    sys.exit(main())
