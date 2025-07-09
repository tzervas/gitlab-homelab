"""Tests for network security policies."""

import pytest
from security.policies.network import (
    FirewallRule,
    NetworkSegment,
    NetworkPolicyChecker,
    create_default_policy,
)

def test_firewall_rule_creation():
    """Test firewall rule creation and defaults."""
    rule = FirewallRule(port=80, protocol="tcp")
    assert rule.port == 80
    assert rule.protocol == "tcp"
    assert rule.direction == "in"
    assert rule.action == "allow"
    
    rule_with_desc = FirewallRule(
        port=443,
        protocol="tcp",
        description="HTTPS",
        direction="out",
        action="deny"
    )
    assert rule_with_desc.description == "HTTPS"
    assert rule_with_desc.direction == "out"
    assert rule_with_desc.action == "deny"

def test_network_segment_creation():
    """Test network segment creation."""
    segment = NetworkSegment(
        name="test-segment",
        cidr="192.168.1.0/24",
        allowed_ports=[80, 443],
        allowed_protocols=["tcp"]
    )
    assert segment.name == "test-segment"
    assert segment.cidr == "192.168.1.0/24"
    assert 80 in segment.allowed_ports
    assert "tcp" in segment.allowed_protocols

def test_network_policy_checker():
    """Test network policy checker functionality."""
    checker = NetworkPolicyChecker()
    
    # Add and verify firewall rule
    rule = FirewallRule(port=8080, protocol="tcp")
    checker.add_firewall_rule(rule)
    assert len(checker.firewall_rules) == 1
    assert checker.firewall_rules[0].port == 8080
    
    # Add and verify network segment
    segment = NetworkSegment(
        name="test",
        cidr="10.0.0.0/24",
        allowed_ports=[8080],
        allowed_protocols=["tcp"]
    )
    checker.add_network_segment(segment)
    assert len(checker.network_segments) == 1
    assert checker.network_segments[0].name == "test"

def test_default_policy_creation():
    """Test default policy creation and configuration."""
    checker = create_default_policy()
    
    # Verify default firewall rules
    assert len(checker.firewall_rules) > 0
    ports = [rule.port for rule in checker.firewall_rules]
    assert 22 in ports  # SSH
    assert 80 in ports  # HTTP
    assert 443 in ports  # HTTPS
    assert 6443 in ports  # Kubernetes API
    
    # Verify default network segments
    assert len(checker.network_segments) > 0
    segments = {seg.name: seg for seg in checker.network_segments}
    assert "control-plane" in segments
    assert "worker-nodes" in segments
    
    # Verify control plane configuration
    control_plane = segments["control-plane"]
    assert 6443 in control_plane.allowed_ports  # Kubernetes API
    assert 2379 in control_plane.allowed_ports  # etcd
    
    # Verify worker node configuration
    worker_nodes = segments["worker-nodes"]
    assert 10250 in worker_nodes.allowed_ports  # Kubelet API
