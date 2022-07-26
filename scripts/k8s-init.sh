#!/bin/bash

if [ -z "${BROKER_URL}" ]; then
  echo "BROKER_URL is not set"
  exit 1
fi
if [ -z "${SUPABASE_URL}" ]; then
  echo "SUPABASE_URL is not set"
  exit 1
fi
if [ -z "${SUPABASE_KEY}" ]; then
  echo "SUPABASE_KEY is not set"
  exit 1
fi
if [ -z "${RABBITMQ_USERNAME}" ]; then
  echo "RABBITMQ_USERNAME is not set"
  exit 1
fi
if [ -z "${RABBITMQ_PASSWORD}" ]; then
  echo "RABBITMQ_PASSWORD is not set"
  exit 1
fi

NAMESPACE=ultrasearch

echo "Creating namespace and secrets..."
kubectl create namespace ${NAMESPACE}
kubectl create secret generic broker --from-literal=url="${BROKER_URL}" --namespace=${NAMESPACE}
kubectl create secret generic supabase --from-literal=url="${SUPABASE_URL}" --from-literal=key="${SUPABASE_KEY}" --namespace=${NAMESPACE}
kubectl create secret generic rabbitmq --from-literal=username="${RABBITMQ_USERNAME}" --from-literal=password="${RABBITMQ_PASSWORD}" --namespace=${NAMESPACE}

# Service account, roles and role bindings:
echo "Creating CI service account and role binding..."
SA_CI_USERNAME=${NAMESPACE}-ci
kubectl create serviceaccount ${SA_CI_USERNAME} --namespace=${NAMESPACE}
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

echo "Creating app service account and role binding..."
SA_APP_USERNAME=${NAMESPACE}-app
kubectl create serviceaccount ${SA_APP_USERNAME} --namespace=${NAMESPACE}
kubectl create rolebinding ${SA_APP_USERNAME}-edit-binding \
    --clusterrole=edit \
    --serviceaccount=${NAMESPACE}:${SA_APP_USERNAME} \
    --namespace=${NAMESPACE}
echo "done."

echo "Cluster URL for GitHub actions CI: "
echo `kubectl config view --minify -o 'jsonpath={.clusters[0].cluster.server}'`
SECRET_NAME=`kubectl get serviceAccounts ${SA_CI_USERNAME} -n ${NAMESPACE} -o 'jsonpath={.secrets[*].name}'`
echo "To retrieve secret for GitHub Actions CI:\nkubectl get secret ${SECRET_NAME} -n ${NAMESPACE} -oyaml"
