"""Network security policy implementations for GitLab homelab."""

import logging
import subprocess
from dataclasses import dataclass
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

@dataclass
class FirewallRule:
    """Represents a firewall rule configuration."""
    port: int
    protocol: str
    direction: str = "in"
    action: str = "allow"
    description: str = ""

@dataclass
class NetworkSegment:
    """Represents a network segment configuration."""
    name: str
    cidr: str
    allowed_ports: List[int]
    allowed_protocols: List[str]

class NetworkPolicyChecker:
    """Implements network policy validation and checking."""
    
    def __init__(self):
        self.firewall_rules: List[FirewallRule] = []
        self.network_segments: List[NetworkSegment] = []
    
    def add_firewall_rule(self, rule: FirewallRule) -> None:
        """Add a firewall rule to the checker."""
        self.firewall_rules.append(rule)
        
    def add_network_segment(self, segment: NetworkSegment) -> None:
        """Add a network segment to the checker."""
        self.network_segments.append(segment)
    
    def check_port_open(self, port: int, protocol: str = "tcp") -> bool:
        """Check if a port is open using netstat."""
        try:
            cmd = ["netstat", "-tuln"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return f":{port}" in result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check port {port}: {e}")
            return False
    
    def check_firewall_rules(self) -> Dict[str, bool]:
        """Check all firewall rules for compliance."""
        results = {}
        for rule in self.firewall_rules:
            key = f"{rule.protocol}_{rule.port}"
            is_open = self.check_port_open(rule.port, rule.protocol)
            results[key] = is_open
            logger.info(f"Checking firewall rule for port {rule.port}/{rule.protocol}: {'open' if is_open else 'closed'}")
        return results

def create_default_policy() -> NetworkPolicyChecker:
    """Create default network policy configuration."""
    checker = NetworkPolicyChecker()
    
    # Add default firewall rules
    default_rules = [
        FirewallRule(port=22, protocol="tcp", description="SSH access"),
        FirewallRule(port=80, protocol="tcp", description="HTTP access"),
        FirewallRule(port=443, protocol="tcp", description="HTTPS access"),
        FirewallRule(port=6443, protocol="tcp", description="Kubernetes API"),
    ]
    
    for rule in default_rules:
        checker.add_firewall_rule(rule)
    
    # Add default network segments
    default_segments = [
        NetworkSegment(
            name="control-plane",
            cidr="10.0.0.0/24",
            allowed_ports=[6443, 2379, 2380],
            allowed_protocols=["tcp"],
        ),
        NetworkSegment(
            name="worker-nodes",
            cidr="10.0.1.0/24",
            allowed_ports=[10250, 30000, 32767],
            allowed_protocols=["tcp"],
        ),
    ]
    
    for segment in default_segments:
        checker.add_network_segment(segment)
    
    return checker
