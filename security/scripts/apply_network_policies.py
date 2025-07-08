#!/usr/bin/env python3
"""Script to apply network security policies."""

import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from security.policies.network import (
    NetworkPolicyChecker,
    create_default_policy,
)

def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('.local/network_policy.log')
        ]
    )

def apply_policies(checker: NetworkPolicyChecker) -> bool:
    """Apply network policies and return success status."""
    logger = logging.getLogger(__name__)
    success = True
    
    try:
        # Check firewall rules
        logger.info("Checking firewall rules...")
        rule_status = checker.check_firewall_rules()
        
        # Log results
        for rule_name, is_compliant in rule_status.items():
            status = "compliant" if is_compliant else "non-compliant"
            logger.info(f"Rule {rule_name}: {status}")
            if not is_compliant:
                success = False
        
        # Check network segments
        logger.info("Checking network segments...")
        for segment in checker.network_segments:
            logger.info(f"Validating segment: {segment.name} ({segment.cidr})")
            for port in segment.allowed_ports:
                for protocol in segment.allowed_protocols:
                    is_open = checker.check_port_open(port, protocol)
                    status = "open" if is_open else "closed"
                    logger.info(f"Port {port}/{protocol} is {status}")
                    if not is_open:
                        success = False
        
    except Exception as e:
        logger.error(f"Error applying policies: {e}")
        success = False
    
    return success

def main() -> int:
    """Main function."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create policy checker
        logger.info("Creating network policy checker...")
        checker = create_default_policy()
        
        # Apply policies
        logger.info("Applying network policies...")
        success = apply_policies(checker)
        
        # Report results
        if success:
            logger.info("All network policies applied successfully")
            return 0
        else:
            logger.error("Some network policies failed to apply")
            return 1
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
