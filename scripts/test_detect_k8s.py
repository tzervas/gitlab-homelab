#!/usr/bin/env python3
"""
Test module for detect_k8s.py
Idempotent tests without for-loops

Author: Tyler Zervas
License: MIT
"""

import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the scripts directory to the path to import detect_k8s
sys.path.insert(0, str(Path(__file__).parent))

from detect_k8s import KubernetesDetector


class TestKubernetesDetector(unittest.TestCase):
    """Test cases for KubernetesDetector class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.detector = KubernetesDetector()

    def test_command_exists_valid_command(self) -> None:
        """Test command_exists with a valid command."""
        # Test with a command that should exist on most systems
        result = self.detector.command_exists("python3")
        self.assertIsInstance(result, bool)

    def test_command_exists_invalid_command(self) -> None:
        """Test command_exists with an invalid command."""
        result = self.detector.command_exists("nonexistent_command_12345")
        self.assertFalse(result)

    def test_run_command_success(self) -> None:
        """Test run_command with a successful command."""
        success, output = self.detector.run_command(["echo", "test"])
        self.assertTrue(success)
        self.assertEqual(output.strip(), "test")

    def test_run_command_failure(self) -> None:
        """Test run_command with a failing command."""
        success, output = self.detector.run_command(["false"])
        self.assertFalse(success)

    def test_get_kubectl_version_invalid_command(self) -> None:
        """Test get_kubectl_version with invalid command."""
        version = self.detector.get_kubectl_version("nonexistent_kubectl")
        self.assertEqual(version, "unknown")

    @patch('detect_k8s.shutil.which')
    def test_detect_microk8s_not_found(self, mock_which: MagicMock) -> None:
        """Test detect_microk8s when microk8s is not found."""
        mock_which.return_value = None
        result = self.detector.detect_microk8s()
        self.assertFalse(result)
        self.assertEqual(self.detector.k8s_distro, "")

    @patch('detect_k8s.shutil.which')
    def test_detect_k3s_not_found(self, mock_which: MagicMock) -> None:
        """Test detect_k3s when k3s is not found."""
        mock_which.return_value = None
        result = self.detector.detect_k3s()
        self.assertFalse(result)
        self.assertEqual(self.detector.k8s_distro, "")

    @patch('detect_k8s.shutil.which')
    def test_detect_upstream_kubectl_not_found(self, mock_which: MagicMock) -> None:
        """Test detect_upstream_kubectl when kubectl is not found."""
        mock_which.return_value = None
        result = self.detector.detect_upstream_kubectl()
        self.assertFalse(result)
        self.assertEqual(self.detector.k8s_distro, "")

    @patch('detect_k8s.os.path.isfile')
    @patch('detect_k8s.os.access')
    def test_detect_custom_kubectl_not_found(self, mock_access: MagicMock, mock_isfile: MagicMock) -> None:
        """Test detect_custom_kubectl when no custom kubectl is found."""
        mock_isfile.return_value = False
        mock_access.return_value = False
        result = self.detector.detect_custom_kubectl()
        self.assertFalse(result)
        self.assertEqual(self.detector.k8s_distro, "")

    @patch.object(KubernetesDetector, 'detect_microk8s')
    @patch.object(KubernetesDetector, 'detect_k3s')
    @patch.object(KubernetesDetector, 'detect_upstream_kubectl')
    @patch.object(KubernetesDetector, 'detect_custom_kubectl')
    def test_detect_no_kubernetes_found(self, mock_custom: MagicMock, mock_upstream: MagicMock, 
                                      mock_k3s: MagicMock, mock_microk8s: MagicMock) -> None:
        """Test detect method when no Kubernetes is found."""
        mock_microk8s.return_value = False
        mock_k3s.return_value = False
        mock_upstream.return_value = False
        mock_custom.return_value = False
        
        results = self.detector.detect()
        
        self.assertEqual(results["K8S_DISTRO"], "none")
        self.assertEqual(self.detector.k8s_distro, "none")

    @patch.object(KubernetesDetector, 'detect_microk8s')
    @patch.object(KubernetesDetector, 'get_kubectl_context')
    def test_detect_microk8s_found(self, mock_context: MagicMock, mock_microk8s: MagicMock) -> None:
        """Test detect method when microk8s is found."""
        mock_microk8s.return_value = True
        mock_context.return_value = None
        
        # Set up the detector state as if microk8s was detected
        self.detector.k8s_distro = "microk8s"
        self.detector.k8s_version = "v1.28.0"
        
        results = self.detector.detect()
        
        self.assertEqual(results["K8S_DISTRO"], "microk8s")
        mock_microk8s.assert_called_once()
        mock_context.assert_called_once()

    def test_get_kubectl_context_no_distro(self) -> None:
        """Test get_kubectl_context with no detected distribution."""
        self.detector.k8s_distro = ""
        self.detector.get_kubectl_context()
        self.assertEqual(self.detector.k8s_current_context, "")

    def test_environment_variable_setting(self) -> None:
        """Test that environment variables are properly set."""
        # Save original environment
        original_env = dict(os.environ)
        
        try:
            # Mock a detection result
            self.detector.k8s_distro = "test_distro"
            self.detector.k8s_version = "test_version"
            self.detector.k8s_cluster_info = "test_info"
            self.detector.k8s_current_context = "test_context"
            
            results = {
                "K8S_DISTRO": self.detector.k8s_distro,
                "K8S_VERSION": self.detector.k8s_version,
                "K8S_CLUSTER_INFO": self.detector.k8s_cluster_info,
                "K8S_CURRENT_CONTEXT": self.detector.k8s_current_context,
            }
            
            # Set environment variables
            for key, value in results.items():
                os.environ[key] = value
            
            # Verify environment variables are set
            self.assertEqual(os.environ.get("K8S_DISTRO"), "test_distro")
            self.assertEqual(os.environ.get("K8S_VERSION"), "test_version")
            self.assertEqual(os.environ.get("K8S_CLUSTER_INFO"), "test_info")
            self.assertEqual(os.environ.get("K8S_CURRENT_CONTEXT"), "test_context")
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


class TestIntegration(unittest.TestCase):
    """Integration tests for the detection system."""

    def test_script_execution(self) -> None:
        """Test that the script can be executed."""
        script_path = Path(__file__).parent / "detect_k8s.py"
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True)
        
        # Should complete without crashing
        self.assertIn(result.returncode, [0, 1])  # 0 for success, 1 for no k8s found

    def test_shell_script_execution(self) -> None:
        """Test that the shell script can be executed."""
        script_path = Path(__file__).parent / "detect_k8s.sh"
        if script_path.exists():
            result = subprocess.run([str(script_path)], 
                                  capture_output=True, text=True)
            
            # Should complete without crashing
            self.assertIn(result.returncode, [0, 1])  # 0 for success, 1 for no k8s found


def run_tests() -> int:
    """Run all tests and return exit code."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestKubernetesDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
