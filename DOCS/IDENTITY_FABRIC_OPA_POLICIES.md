# Identity Fabric - OPA Policy Framework

## Overview

The Open Policy Agent (OPA) integration provides fine-grained authorization for the AgentVault ecosystem. Combined with SPIFFE identities, it enables policy-based access control across all services and agent interactions.

## Architecture

### Policy Decision Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Service/Agent │────▶│   Policy Query  │────▶│   OPA Server    │
│   (with SVID)   │     │   (context)     │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
         ▲                                                │
         │                                                ▼
         │                                       ┌─────────────────┐
         └───────────────[Allow/Deny]────────────│  Rego Policies  │
                                                 └─────────────────┘
```

### Integration Points

1. **Service Authorization**: Inter-service API calls
2. **Agent Operations**: Token transfers, attestations
3. **Admin Functions**: Governance and management
4. **Resource Access**: Data and configuration

## Policy Language (Rego)

### Basic Structure

```rego
# Package declaration
package agentvault.authz

# Import future keywords for better syntax
import future.keywords.if
import future.keywords.in
import future.keywords.contains

# Default deny
default allow = false

# Allow rule with conditions
allow if {
    # Check subject identity
    input.subject.type == "agent"
    
    # Check action permitted
    input.action in allowed_actions
    
    # Check resource ownership
    input.resource.owner == input.subject.id
}

# Define allowed actions
allowed_actions := {
    "token.transfer",
    "token.balance.read",
    "attestation.submit"
}
```

### Input Structure

```json
{
  "subject": {
    "id": "spiffe://agentvault.com/agent/user123",
    "type": "agent",
    "attributes": {
      "reputation_score": 150,
      "account_status": "active",
      "created_at": "2024-01-15T00:00:00Z"
    }
  },
  "action": "token.transfer",
  "resource": {
    "type": "token_balance",
    "id": "balance_123",
    "owner": "spiffe://agentvault.com/agent/user123",
    "attributes": {
      "amount": "1000.0"
    }
  },
  "context": {
    "source_ip": "192.168.1.100",
    "request_time": "2025-06-17T10:30:00Z",
    "tls_verified": true
  }
}
```

## Core Policies

### Agent Authorization

```rego
package agentvault.agent

import future.keywords.if
import future.keywords.in

# Agent can read own balance
allow if {
    input.action == "token.balance.read"
    input.subject.id == input.resource.owner
}

# Agent can transfer tokens if active
allow if {
    input.action == "token.transfer"
    input.subject.attributes.account_status == "active"
    input.subject.attributes.reputation_score >= 0
}

# Agent can submit attestations with reputation > 100
allow if {
    input.action == "attestation.submit"
    input.subject.attributes.reputation_score > 100
}

# Agent can stake tokens if balance sufficient
allow if {
    input.action == "token.stake"
    to_number(input.resource.attributes.amount) >= 100
}
```

### Service Authorization

```rego
package agentvault.service

import future.keywords.if
import future.keywords.in

# Registry can create agent identities
allow if {
    input.subject.id == "spiffe://agentvault.com/service/registry-backend"
    input.action == "identity.create"
    input.resource.type == "agent_identity"
}

# TEG can modify token balances
allow if {
    input.subject.id == "spiffe://agentvault.com/service/teg-core"
    input.action in ["token.balance.update", "token.balance.read"]
}

# Chronicle can read all events
allow if {
    input.subject.id == "spiffe://agentvault.com/service/chronicle"
    input.action == "event.read"
}
```

### Admin Authorization

```rego
package agentvault.admin

import future.keywords.if
import future.keywords.in

# Define admin identities
admin_ids := {
    "spiffe://agentvault.com/admin/root",
    "spiffe://agentvault.com/admin/operator"
}

# Admins have full access
allow if {
    input.subject.id in admin_ids
}

# Specific admin actions
admin_actions := {
    "token.issue",
    "account.suspend",
    "policy.update",
    "audit.read"
}

# Role-based admin access
allow if {
    input.subject.attributes.role == "admin"
    input.action in admin_actions
}
```

## Advanced Policies

### Time-Based Access Control

```rego
package agentvault.temporal

import future.keywords.if
import time

# Business hours (UTC)
business_hours if {
    current_hour := time.clock([time.now_ns(), "UTC"])[0]
    current_hour >= 9
    current_hour < 17
}

# Maintenance window (Sunday 2-4 AM UTC)
maintenance_window if {
    day := time.weekday(time.now_ns())
    hour := time.clock([time.now_ns(), "UTC"])[0]
    day == "Sunday"
    hour >= 2
    hour < 4
}

# Restrict certain operations to business hours
allow if {
    input.action in ["token.issue", "account.create"]
    business_hours
}

# Only allow maintenance operations during window
allow if {
    input.action in ["system.upgrade", "database.migrate"]
    maintenance_window
    input.subject.attributes.role == "operator"
}
```

### Dynamic Reputation-Based Access

```rego
package agentvault.reputation

import future.keywords.if

# Reputation tiers
reputation_tier(score) := "untrusted" if score < -100
reputation_tier(score) := "new" if {
    score >= -100
    score <= 100
}
reputation_tier(score) := "trusted" if {
    score > 100
    score <= 500
}
reputation_tier(score) := "verified" if {
    score > 500
    score <= 800
}
reputation_tier(score) := "elite" if score > 800

# Transfer limits by tier
transfer_limit := {
    "untrusted": 10,
    "new": 100,
    "trusted": 1000,
    "verified": 10000,
    "elite": 1000000
}

# Check transfer amount against reputation limit
allow if {
    input.action == "token.transfer"
    score := input.subject.attributes.reputation_score
    tier := reputation_tier(score)
    limit := transfer_limit[tier]
    to_number(input.context.transfer_amount) <= limit
}
```

### Resource-Specific Policies

```rego
package agentvault.resources

import future.keywords.if
import future.keywords.in

# Attestation type permissions
attestation_permissions := {
    "identity_proof": {
        "min_reputation": 0,
        "required_attributes": ["email_verified"]
    },
    "fair_markup_policy": {
        "min_reputation": 100,
        "required_attributes": ["service_provider"]
    },
    "compliance_audit": {
        "min_reputation": 500,
        "required_attributes": ["auditor_certified"]
    }
}

# Check attestation submission
allow if {
    input.action == "attestation.submit"
    attestation_type := input.resource.attributes.type
    requirements := attestation_permissions[attestation_type]
    
    # Check reputation requirement
    input.subject.attributes.reputation_score >= requirements.min_reputation
    
    # Check required attributes
    required_attrs_present(requirements.required_attributes)
}

# Helper: Check if all required attributes are present
required_attrs_present(required) := true if {
    present := {attr | input.subject.attributes[attr]; attr := required[_]}
    count(present) == count(required)
}
```

## Policy Testing

### Unit Tests

```rego
package agentvault.authz_test

import future.keywords.if

test_agent_can_read_own_balance if {
    allow with input as {
        "subject": {
            "id": "spiffe://agentvault.com/agent/user123",
            "type": "agent"
        },
        "action": "token.balance.read",
        "resource": {
            "owner": "spiffe://agentvault.com/agent/user123"
        }
    }
}

test_agent_cannot_read_others_balance if {
    not allow with input as {
        "subject": {
            "id": "spiffe://agentvault.com/agent/user123",
            "type": "agent"
        },
        "action": "token.balance.read",
        "resource": {
            "owner": "spiffe://agentvault.com/agent/user456"
        }
    }
}

test_suspended_agent_cannot_transfer if {
    not allow with input as {
        "subject": {
            "id": "spiffe://agentvault.com/agent/user123",
            "type": "agent",
            "attributes": {
                "account_status": "suspended",
                "reputation_score": 100
            }
        },
        "action": "token.transfer"
    }
}
```

### Integration Tests

```python
import requests
import json

class OPAPolicyTests:
    def __init__(self, opa_url="http://localhost:8181"):
        self.opa_url = opa_url
        
    def test_policy(self, input_data, expected_result):
        """Test a policy decision"""
        response = requests.post(
            f"{self.opa_url}/v1/data/agentvault/authz/allow",
            json={"input": input_data}
        )
        
        result = response.json()
        assert result["result"] == expected_result, \
            f"Expected {expected_result}, got {result['result']}"
    
    def run_test_suite(self):
        """Run comprehensive test suite"""
        # Test agent operations
        self.test_policy({
            "subject": {"id": "spiffe://agentvault.com/agent/test", "type": "agent"},
            "action": "token.balance.read",
            "resource": {"owner": "spiffe://agentvault.com/agent/test"}
        }, expected_result=True)
        
        # Test unauthorized access
        self.test_policy({
            "subject": {"id": "spiffe://agentvault.com/agent/test", "type": "agent"},
            "action": "token.issue",
            "resource": {"type": "token"}
        }, expected_result=False)
```

## Policy Management

### Bundle Service

```yaml
# opa-bundle-server.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: opa-bundle-config
data:
  bundles.yaml: |
    services:
      bundle-server:
        url: https://bundle-server.agentvault.com
        
    bundles:
      authz:
        resource: "/bundles/authz/bundle.tar.gz"
        polling:
          min_delay_seconds: 10
          max_delay_seconds: 20
        signing:
          keyid: "agentvault-bundle-key"
```

### Policy Deployment

```bash
#!/bin/bash
# deploy-policies.sh

# Build policy bundle
opa build \
  --bundle policies/ \
  --signing-key bundle-signing-key.pem \
  --output bundle.tar.gz

# Upload to bundle server
aws s3 cp bundle.tar.gz s3://agentvault-policies/bundles/authz/

# Trigger OPA reload
curl -X POST http://opa:8181/v1/data/system/bundles/authz/refresh
```

### Policy Versioning

```rego
# policies/metadata.rego
package system

version := "2.0.0"
last_updated := "2025-06-17T10:30:00Z"
compatibility := ["v1.0.0", "v2.0.0"]

# Version-specific rules
import future.keywords.if

# v1 compatibility mode
allow_v1 if {
    input.api_version == "v1"
    data.agentvault.v1.authz.allow
}

# v2 mode (current)
allow if {
    input.api_version == "v2"
    data.agentvault.authz.allow
}
```

## Performance Optimization

### Decision Caching

```yaml
# opa-config.yaml
services:
  authz:
    url: http://opa:8181
    
decision_logs:
  console: true
  
caching:
  inter_query_builtin_cache:
    max_size_bytes: 10000000
    
  # Cache decisions for 60 seconds
  inter_query_cache:
    max_size_bytes: 50000000
    stale_entry_eviction_period_seconds: 60
```

### Query Optimization

```rego
# Optimized policy with indexing
package agentvault.optimized

import future.keywords.if
import future.keywords.in

# Pre-compute allowed actions per role
role_permissions := {
    "admin": {"*"},
    "agent": {
        "token.transfer",
        "token.balance.read",
        "attestation.submit"
    },
    "service": {
        "agent.read",
        "metrics.write"
    }
}

# Optimized allow rule
allow if {
    # Quick role check first
    permissions := role_permissions[input.subject.role]
    
    # Then check specific action
    input.action in permissions
}
```

## Monitoring & Debugging

### Decision Logging

```json
{
  "decision_id": "7c0e3f36-89c5-4549-b34f-03fe5d7ec947",
  "input": {
    "subject": {
      "id": "spiffe://agentvault.com/agent/user123",
      "type": "agent"
    },
    "action": "token.transfer",
    "resource": {
      "type": "token_balance"
    }
  },
  "result": true,
  "path": "agentvault/authz/allow",
  "requested_by": "spiffe://agentvault.com/service/teg-core",
  "timestamp": "2025-06-17T10:30:00.123Z",
  "metrics": {
    "timer_rego_query_eval_ns": 125000,
    "timer_server_handler_ns": 250000
  }
}
```

### Debug Mode

```rego
# Enable debug logging
package agentvault.debug

import future.keywords.if

# Debug wrapper
allow if {
    # Log input
    print("DEBUG: Input received:", input)
    
    # Check main policy
    decision := data.agentvault.authz.allow
    
    # Log decision path
    print("DEBUG: Decision:", decision)
    print("DEBUG: Explanation:", opa.explanation)
    
    # Return decision
    decision
}
```

### Policy Coverage

```bash
# Check policy coverage
opa test policies/ --coverage

# Generate coverage report
opa test policies/ --coverage --format=json | \
  opa eval -d policies/ -f pretty 'data.coverage'

# Find uncovered lines
opa test policies/ --coverage --threshold=80
```

## Security Considerations

### Policy Isolation

```rego
# Separate packages for different domains
package agentvault.agent    # Agent policies
package agentvault.service  # Service policies
package agentvault.admin    # Admin policies
package agentvault.audit    # Audit policies

# Explicit imports only
import data.agentvault.common.helpers
```

### Input Validation

```rego
package agentvault.validation

import future.keywords.if
import future.keywords.in

# Validate SPIFFE ID format
valid_spiffe_id(id) if {
    regex.match("^spiffe://agentvault\\.com/", id)
}

# Validate input structure
valid_input if {
    # Required fields present
    input.subject.id
    input.action
    input.resource
    
    # Valid SPIFFE ID
    valid_spiffe_id(input.subject.id)
    
    # Known action
    input.action in all_actions
}

# Deny if invalid input
deny if {
    not valid_input
}
```

### Policy Signing

```bash
# Sign policy bundle
openssl dgst -sha256 -sign policy-key.pem \
  -out bundle.tar.gz.sig bundle.tar.gz

# Verify signature in OPA
opa run --verification-key policy-cert.pem \
  --bundle bundle.tar.gz
```

## Best Practices

1. **Start with Deny by Default**
   ```rego
   default allow = false
   default deny = true
   ```

2. **Use Explicit Package Names**
   ```rego
   package agentvault.domain.specific
   ```

3. **Test Everything**
   - Unit tests for each rule
   - Integration tests for workflows
   - Coverage analysis

4. **Version Policies**
   - Semantic versioning
   - Compatibility layers
   - Gradual rollout

5. **Monitor Performance**
   - Decision latency
   - Cache hit rates
   - Policy evaluation time

6. **Secure Policy Distribution**
   - Sign bundles
   - Encrypt in transit
   - Audit policy changes

## Migration Guide

### From RBAC to ABAC

```rego
# Old RBAC approach
allow if {
    input.subject.role == "admin"
}

# New ABAC approach
allow if {
    input.subject.attributes.department == "security"
    input.subject.attributes.clearance_level >= "secret"
    input.resource.attributes.classification <= input.subject.attributes.clearance_level
}
```

### Policy Evolution

```rego
# v1: Simple ownership
allow if {
    input.subject.id == input.resource.owner
}

# v2: Add reputation check
allow if {
    input.subject.id == input.resource.owner
    input.subject.attributes.reputation_score >= 0
}

# v3: Add time-based access
allow if {
    input.subject.id == input.resource.owner
    input.subject.attributes.reputation_score >= 0
    not maintenance_window
}
```

## Conclusion

The OPA policy framework provides:

- **Fine-grained Authorization**: Attribute-based access control
- **Declarative Policies**: Clear, auditable rules
- **Performance**: Sub-millisecond decisions with caching
- **Flexibility**: Easy to extend and modify
- **Integration**: Works seamlessly with SPIFFE identities

Combined with SPIFFE/SPIRE, this creates a complete Zero Trust security model for the AgentVault ecosystem.