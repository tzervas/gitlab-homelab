"""Tests for the baseline security policies."""
import pytest
from security.policies.baseline import load_policies, SecurityPolicy, NetworkPolicy, AccessPolicy

def test_load_policies():
    """Test that policies can be loaded."""
    policies = load_policies()
    assert len(policies) > 0
    assert "network" in policies
    assert "access" in policies
    
    network_policy = policies["network"]
    assert isinstance(network_policy, NetworkPolicy)
    assert network_policy.name == "Base Network Security"
    assert network_policy.severity == "HIGH"
    assert 443 in network_policy.allowed_ports
    
    access_policy = policies["access"]
    assert isinstance(access_policy, AccessPolicy)
    assert access_policy.name == "Base Access Control"
    assert "admin" in access_policy.required_roles
    assert "read" in access_policy.required_permissions

def test_policy_check_methods():
    """Test that policy check methods are callable."""
    policies = load_policies()
    for policy in policies.values():
        assert hasattr(policy, "check")
        result = policy.check()
        assert isinstance(result, bool)
