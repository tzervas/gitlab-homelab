#!/usr/bin/env python3

import sys
import yaml
import json
import logging
from typing import Dict, List, Set, Optional
from kubernetes import client, config
from dataclasses import dataclass, asdict
import requests
from pathlib import Path
import ipaddress

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NetworkFlow:
    source: str
    destination: str
    port: int
    protocol: str = "tcp"
    description: str = ""

@dataclass
class FirewallRule:
    name: str
    action: str = "pass"
    interface: str = "lan"
    source: str = "any"
    destination: str = "any"
    protocol: str = "tcp"
    destination_port: Optional[str] = None
    description: str = ""

class K8sNetworkInspector:
    def __init__(self):
        try:
            config.load_kube_config()
        except Exception:
            config.load_incluster_config()
        
        self.v1 = client.CoreV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.flows: Set[NetworkFlow] = set()
        self.internal_cidrs = set()
        self.service_ips = set()

    def inspect_services(self):
        """Inspect Kubernetes services for network flows"""
        services = self.v1.list_service_for_all_namespaces()
        for svc in services.items:
            if svc.spec.type in ["LoadBalancer", "NodePort"]:
                for port in svc.spec.ports:
                    self.flows.add(NetworkFlow(
                        source="external",
                        destination=f"svc_{svc.metadata.name}",
                        port=port.port,
                        protocol=port.protocol.lower(),
                        description=f"Allow {svc.metadata.name} service"
                    ))
                    if svc.spec.cluster_ip:
                        self.service_ips.add(svc.spec.cluster_ip)

    def inspect_ingresses(self):
        """Inspect Kubernetes ingresses for network flows"""
        ingresses = self.networking_v1.list_ingress_for_all_namespaces()
        for ing in ingresses.items:
            for rule in ing.spec.rules:
                for path in rule.http.paths:
                    self.flows.add(NetworkFlow(
                        source="external",
                        destination=f"svc_{path.backend.service.name}",
                        port=80,
                        description=f"Allow ingress to {path.backend.service.name}"
                    ))
                    self.flows.add(NetworkFlow(
                        source="external",
                        destination=f"svc_{path.backend.service.name}",
                        port=443,
                        description=f"Allow secure ingress to {path.backend.service.name}"
                    ))

    def inspect_network_policies(self):
        """Inspect NetworkPolicies for allowed flows"""
        policies = self.networking_v1.list_network_policy_for_all_namespaces()
        for policy in policies.items:
            if policy.spec.ingress:
                for ingress in policy.spec.ingress:
                    for port in ingress.ports or []:
                        self.flows.add(NetworkFlow(
                            source="internal",
                            destination=f"ns_{policy.metadata.namespace}",
                            port=port.port,
                            protocol=port.protocol.lower(),
                            description=f"Allow {policy.metadata.name} policy"
                        ))

    def get_node_ips(self) -> List[str]:
        """Get all node IPs"""
        nodes = self.v1.list_node()
        node_ips = []
        for node in nodes.items:
            for addr in node.status.addresses:
                if addr.type == "InternalIP":
                    node_ips.append(addr.address)
                    self.internal_cidrs.add(
                        str(ipaddress.IPv4Network(f"{addr.address}/24", strict=False))
                    )
        return node_ips

class OPNsenseConfigGenerator:
    def __init__(self, api_key: str, api_secret: str, api_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = api_url
        self.rules: List[FirewallRule] = []

    def generate_aliases(self, node_ips: List[str], service_ips: List[str]) -> Dict:
        """Generate OPNsense aliases"""
        return {
            "k8s_nodes": {
                "type": "host",
                "content": " ".join(node_ips),
                "description": "Kubernetes nodes"
            },
            "k8s_services": {
                "type": "network",
                "content": " ".join(service_ips),
                "description": "Kubernetes service IPs"
            }
        }

    def flows_to_rules(self, flows: Set[NetworkFlow], internal_cidrs: Set[str]) -> List[FirewallRule]:
        """Convert network flows to firewall rules"""
        rules = []
        
        # Default required rules
        rules.extend([
            FirewallRule(
                name="allow_k8s_api",
                source="k8s_nodes",
                destination="k8s_nodes",
                destination_port="6443",
                description="Allow Kubernetes API Server"
            ),
            FirewallRule(
                name="allow_kubelet",
                source="k8s_nodes",
                destination="k8s_nodes",
                destination_port="10250",
                description="Allow kubelet communication"
            )
        ])

        # Convert discovered flows to rules
        for flow in flows:
            if flow.source == "external":
                rules.append(FirewallRule(
                    name=f"allow_{flow.destination.lower()}",
                    interface="wan",
                    destination="k8s_services",
                    destination_port=str(flow.port),
                    protocol=flow.protocol,
                    description=flow.description
                ))
            elif flow.source == "internal":
                rules.append(FirewallRule(
                    name=f"allow_internal_{flow.destination.lower()}",
                    source="k8s_nodes",
                    destination="k8s_services",
                    destination_port=str(flow.port),
                    protocol=flow.protocol,
                    description=flow.description
                ))

        return rules

    def generate_waf_rules(self, services: List[Dict]) -> List[Dict]:
        """Generate WAF rules based on services"""
        waf_rules = []
        for svc in services:
            if "gitlab" in svc["name"].lower():
                waf_rules.extend([
                    {
                        "rule": 'SecRule REQUEST_URI "@rx \.git" "id:2000,phase:1,t:none,deny,status:403,msg:\'Git metadata access denied\'"'
                    },
                    {
                        "rule": 'SecRule REQUEST_HEADERS:User-Agent "@contains git" "id:2001,phase:1,t:none,deny,status:403,msg:\'Direct git protocol blocked\'"'
                    }
                ])
        return waf_rules

def main():
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                env_vars[key.strip()] = value.strip()

    # Initialize K8s inspector
    inspector = K8sNetworkInspector()
    
    # Gather network information
    inspector.inspect_services()
    inspector.inspect_ingresses()
    inspector.inspect_network_policies()
    node_ips = inspector.get_node_ips()

    # Initialize OPNsense config generator
    generator = OPNsenseConfigGenerator(
        api_key=env_vars["OPNSENSE_API_KEY"],
        api_secret=env_vars["OPNSENSE_API_SECRET"],
        api_url=env_vars["OPNSENSE_URL"]
    )

    # Generate configurations
    aliases = generator.generate_aliases(node_ips, list(inspector.service_ips))
    rules = generator.flows_to_rules(inspector.flows, inspector.internal_cidrs)

    # Create final configuration
    config = {
        "aliases": aliases,
        "rules": [asdict(rule) for rule in rules],
        "internal_networks": list(inspector.internal_cidrs),
        "waf": {
            "enabled": True,
            "rules": generator.generate_waf_rules([
                {"name": svc} for svc in inspector.flows 
                if isinstance(svc.destination, str) and "svc_" in svc.destination
            ])
        }
    }

    # Output configuration
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        # TODO: Implement direct OPNsense API calls to apply configuration
        logger.info("Would apply configuration directly to OPNsense")
    else:
        print(yaml.dump(config, default_flow_style=False))

if __name__ == "__main__":
    main()
