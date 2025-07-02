#!/bin/bash

# Configuration variables
ARGOCD_VERSION="${ARGOCD_VERSION:-v3.0.6}"
ARGOCD_MANIFEST_URL="${ARGOCD_MANIFEST_URL:-https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml}"
ARGOCD_MANIFEST_CHECKSUM="${ARGOCD_MANIFEST_CHECKSUM:-e6683f77ee15226766b89b02a34e5f580418dfe4ec5c7407fc024b45616bc663}"
DOMAIN="${DOMAIN:-example.com}"  # Replace with your domain
ARGOCD_SUBDOMAIN="${ARGOCD_SUBDOMAIN:-argocd}"  # Subdomain for Argo CD
ENABLE_INGRESS="${ENABLE_INGRESS:-true}"  # Set to true to enable ingress
INGRESS_CLASS="${INGRESS_CLASS:-nginx}"  # Replace with your ingress class (e.g., nginx, traefik, etc.)
STATIC_IP="${STATIC_IP:-237.84.2.178}"  # Static IP for LAN ingress
ARC_VERSION="${ARC_VERSION:-0.12.1}"  # Version of Actions Runner Controller
EMAIL="${EMAIL:-OgP6o@example.com}"  # Email for Let's Encrypt
CERT_MANAGER_VERSION="${CERT_MANAGER_VERSION:-v1.18.1}"  # Version of cert-manager
CERT_MANAGER_MANIFEST_URL="${CERT_MANAGER_MANIFEST_URL:-https://github.com/cert-manager/cert-manager/releases/download/${CERT_MANAGER_VERSION}/cert-manager.yaml}"
CERT_MANAGER_CHECKSUM="${CERT_MANAGER_CHECKSUM:-bfa31f0130a7ae2d56b4c163a1ddadb4ff4dfd2954466727b83c92a61197b6a2}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"  # Replace with your AWS key
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"  # Replace with your AWS secret
AWS_REGION="${AWS_REGION:-us-east-1}"  # e.g., us-east-2, eu-west-1, etc.

# Check for required parameters
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <GITHUB_URL> <RUNNER_TOKEN>"
  exit 1
fi

GITHUB_URL=$1
RUNNER_TOKEN=$2

# Create namespaces idempotently
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace arc-systems --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace arc-runners --dry-run=client -o yaml | kubectl apply -f -

# Download and verify Argo CD manifest
ARGOCD_MANIFEST_FILE="argocd-install.yaml"
curl -sSL -o ${ARGOCD_MANIFEST_FILE} ${ARGOCD_MANIFEST_URL}
ARGOCD_DOWNLOADED_CHECKSUM=$(sha256sum ${ARGOCD_MANIFEST_FILE} | awk '{print $1}')

if [ "${ARGOCD_DOWNLOADED_CHECKSUM}" != "${ARGOCD_MANIFEST_CHECKSUM}" ];
then "${ARGOCD_MANIFEST_CHECKSUM:-e6683f77ee15226766b89b02a34e5f580418dfe4ec5c7407fc024b45616bc663}"en
  echo "Checksum mismatch for Argo CD manifest"
  exit 1
fi

# Apply Argo CD manifest
kubectl apply -n argocd -f ${ARGOCD_MANIFEST_FILE}

# Wait for Argo CD to be ready
echo "Waiting for Argo CD to be ready..."
until kubectl -n argocd get pods -l app.kubernetes.io/name=argocd-server -o jsonpath='{.items[0].status.phase}' | grep -q "Running"; do
  sleep 5
done

# Retrieve initial admin password
PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "Argo CD initial admin password: ${PASSWORD}"

# Create runner token secret
kubectl create secret generic runner-token --namespace arc-runners --from-literal=runner_token=${RUNNER_TOKEN}

# Apply ARC controller application
cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: arc-controller
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'oci://ghcr.io/actions/actions-runner-controller-charts'
    chart: gha-runner-scale-set-controller
    targetRevision: ${ARC_VERSION}
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: arc-systems
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF

# Apply runner scale set application
cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: arc-runner-set
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'oci://ghcr.io/actions/actions-runner-controller-charts'
    chart: gha-runner-scale-set
    targetRevision: ${ARC_VERSION}
    helm:
      values: |
        githubConfigUrl: "${GITHUB_URL}"
        githubConfigSecret: "runner-token"
        minRunners: 1
        maxRunners: 6
        runnerScaleSetName: "my-runners"
        template:
          spec:
            containers:
            - name: runner
              resources:
                requests:
                  cpu: "500m"
                  memory: "2Gi"
                  ephemeral-storage: "10Gi"
                limits:
                  cpu: "4"
                  memory: "6Gi"
                  ephemeral-storage: "80Gi"
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: arc-runners
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF

# Set up ingress with Let's Encrypt if enabled
if [ "$ENABLE_INGRESS" = true ]; then
  # Install cert-manager
  CERT_MANAGER_MANIFEST_FILE="cert-manager.yaml"
  curl -sSL -o ${CERT_MANAGER_MANIFEST_FILE} ${CERT_MANAGER_MANIFEST_URL}
  CERT_MANAGER_DOWNLOADED_CHECKSUM=$(sha256sum ${CERT_MANAGER_MANIFEST_FILE} | awk '{print $1}')
  if [ "${CERT_MANAGER_DOWNLOADED_CHECKSUM}" != "${CERT_MANAGER_CHECKSUM}" ]; then
    echo "Checksum mismatch for cert-manager manifest"
    exit 1
  fi
  kubectl apply -f ${CERT_MANAGER_MANIFEST_FILE}
  echo "Waiting for cert-manager to be ready..."
  sleep 30  # Adjust as needed

  # Create AWS credentials secret for cert-manager
  kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -
  kubectl create secret generic route53-credentials --namespace cert-manager \
    --from-literal=access-key-id=${AWS_ACCESS_KEY_ID} \
    --from-literal=secret-access-key=${AWS_SECRET_ACCESS_KEY}

  # Create ClusterIssuer for Let's Encrypt with DNS-01 challenge
  cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ${EMAIL}
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - dns01:
        route53:
          region: ${AWS_REGION}
          accessKeyIDSecretRef:
            name: route53-credentials
            key: access-key-id
          secretAccessKeySecretRef:
            name: route53-credentials
            key: secret-access-key
EOF

  # Create Ingress with static IP and cert-manager annotations
  cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: ${INGRESS_CLASS}
  rules:
  - host: ${ARGOCD_SUBDOMAIN}.${DOMAIN}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 80
  tls:
  - hosts:
    - ${ARGOCD_SUBDOMAIN}.${DOMAIN}
    secretName: argocd-tls
EOF

  # Assign static IP to ingress (requires NGINX ingress controller support)
  kubectl -n argocd patch ingress argocd-server-ingress -p "{\"spec\":{\"loadBalancerIP\":\"${STATIC_IP}\"}}" || echo "Static IP assignment may require additional ingress controller configuration."

  echo "Ingress created for Argo CD at https://${ARGOCD_SUBDOMAIN}.${DOMAIN} on LAN IP ${STATIC_IP}"
  echo "Ensure your LAN DNS resolves ${ARGOCD_SUBDOMAIN}.${DOMAIN} to ${STATIC_IP}."
fi

# Provide access instructions
echo "To access Argo CD UI locally on your LAN:"
echo "1. Ensure ${ARGOCD_SUBDOMAIN}.${DOMAIN} resolves to ${STATIC_IP} (e.g., via /etc/hosts or local DNS)."
echo "2. Open https://${ARGOCD_SUBDOMAIN}.${DOMAIN} in your browser."
echo "3. Use username 'admin' and password '${PASSWORD}'."
echo "If DNS isn’t set up, port-forward locally:"
echo "kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "Then visit https://localhost:8080 (ignore cert warning)."
