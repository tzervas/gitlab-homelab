# GitLab Authentication Configuration

This document describes the authentication setup for our GitLab instance.

## Token-based Authentication

We use Kubernetes service account tokens for authentication. The configuration includes:

1. A service account token secret (`gitlab-auth-token`)
2. A dedicated service account (`gitlab-service-account`)
3. RBAC configuration with role and role binding

### Token Rotation

Tokens are automatically rotated based on the following policy:
- Monthly rotation schedule
- 30-day token lifetime
- Retention of last 2 tokens
- Minimum age of 7 days for token deletion

## External Authentication

### OIDC Integration

The OIDC configuration allows for single sign-on with our identity provider:

1. Configure the OIDC provider in GitLab
2. Set up client credentials
3. Configure callback URLs
4. Enable required scopes (openid, profile, email)

To set up OIDC:
1. Update the `external-auth-config.yaml` with your OIDC provider details
2. Set the OIDC client secret: `export OIDC_CLIENT_SECRET=your-secret`
3. Apply the configuration: `kubectl apply -f external-auth-config.yaml`

### LDAP Authentication

LDAP authentication is configured for directory service integration:

1. LDAP server connection details
2. Bind DN and credentials
3. User attribute mapping
4. Group synchronization

To set up LDAP:
1. Update the `external-auth-config.yaml` with your LDAP server details
2. Set the LDAP bind password: `export LDAP_BIND_PASSWORD=your-password`
3. Apply the configuration: `kubectl apply -f external-auth-config.yaml`

## Security Considerations

1. Token Security:
   - Service account tokens are stored as Kubernetes secrets
   - Regular rotation is enforced
   - Access is restricted through RBAC

2. External Authentication:
   - Sensitive credentials are stored as environment variables
   - TLS encryption is required for LDAP
   - OIDC uses secure callback URLs

3. Monitoring and Maintenance:
   - Token rotation is automated
   - Email notifications for token expiration
   - Regular audit of access patterns

## Troubleshooting

1. Token Issues:
   - Check secret existence: `kubectl get secret gitlab-auth-token -n gitlab`
   - Verify service account: `kubectl get serviceaccount gitlab-service-account -n gitlab`
   - Check RBAC permissions: `kubectl auth can-i --as system:serviceaccount:gitlab:gitlab-service-account`

2. OIDC Issues:
   - Verify callback URL configuration
   - Check client credentials
   - Review OIDC provider logs

3. LDAP Issues:
   - Test LDAP connection
   - Verify bind credentials
   - Check user attribute mapping
