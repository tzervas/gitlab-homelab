#!/bin/bash

# Label system namespaces
kubectl label namespace kube-system name=kube-system --overwrite
kubectl label namespace default name=default --overwrite

# Label application namespaces
kubectl label namespace gitlab name=gitlab access=restricted --overwrite
kubectl label namespace ingress-nginx name=ingress-nginx --overwrite

# Label monitoring and logging namespaces
kubectl label namespace monitoring name=monitoring --overwrite
kubectl label namespace logging name=logging --overwrite

# Label namespaces that need GitLab access
kubectl get ns -o name | grep -E 'ci-|dev-|staging-|prod-' | cut -d/ -f2 | \
while read ns; do
  kubectl label namespace $ns access=gitlab-allowed --overwrite
done
