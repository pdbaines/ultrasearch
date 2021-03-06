#!/bin/bash

NAMESPACE=ultrasearch

kubectl create namespace ${NAMESPACE}
kubectl label namespace ${NAMESPACE} istio-injection=enabled
kubectl create secret generic broker --from-literal=url="${BROKER_URL}" --from-literal=management_url="${BROKER_MANAGEMENT_URL}" --namespace=${NAMESPACE}
kubectl create secret generic flower --from-literal=auth="${FLOWER_USERNAME}:${FLOWER_PASSWORD}" --namespace=${NAMESPACE}
kubectl create secret generic redis --from-literal=password="${REDIS_PASSWORD}" --from-literal=auth_url="${REDIS_AUTH_URL}" --namespace=${NAMESPACE}
kubectl create secret generic supabase --from-literal=url="${SUPABASE_URL}" --from-literal=key="${SUPABASE_KEY}" --namespace=${NAMESPACE}
kubectl create secret generic rabbitmq --from-literal=username="${RABBITMQ_USERNAME}" --from-literal=password="${RABBITMQ_PASSWORD}" --namespace=${NAMESPACE}

# Service account, roles and role bindings:
SA_CI_USERNAME=${NAMESPACE}-ci
kubectl create serviceaccount ${SA_CI_USERNAME}
kubectl create rolebinding ${SA_CI_USERNAME}-edit-binding \
    --clusterrole=edit \
    --serviceaccount=${NAMESPACE}:${SA_CI_USERNAME} \
    --namespace=${NAMESPACE}

# GitHub Action annotates the namespace, so need a little extra:
kubectl create role namespace-patch \
    --verb=patch \
    --verb=get \
    --resource=namespaces \
    --namespace=${NAMESPACE}

kubectl create rolebinding ${SA_CI_USERNAME}-namespace-patch \
    --role=namespace-patch \
    --serviceaccount=${NAMESPACE}:${SA_CI_USERNAME} \
    --namespace=${NAMESPACE}

# Add ability to work with virtualservices and gateways
kubectl create role istio-patch \
    --verb=create \
    --verb=patch \
    --verb=get \
    --resource=virtualservices,gateways \
    --namespace=${NAMESPACE}

kubectl create rolebinding ${SA_CI_USERNAME}-istio-patch \
    --role=istio-patch \
    --serviceaccount=${NAMESPACE}:${SA_CI_USERNAME} \
    --namespace=${NAMESPACE}

SA_APP_USERNAME=${NAMESPACE}-app
kubectl create serviceaccount ${SA_APP_USERNAME}
kubectl create rolebinding ${SA_APP_USERNAME}-edit-binding \
    --clusterrole=edit \
    --serviceaccount=${NAMESPACE}:${SA_APP_USERNAME} \
    --namespace=${NAMESPACE}
