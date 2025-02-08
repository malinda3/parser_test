#!/bin/bash

kubectl create ns kafka
kubectl label namespace kafka app.kubernetes.io/managed-by=Helm
kubectl annotate namespace kafka meta.helm.sh/release-name=bot-0
kubectl annotate namespace kafka meta.helm.sh/release-namespace=kafka

sleep 10

helm install bot-0 . -n kafka
#You can use "docker exec k3d-test-server-0 crictl images" to know what images was loaded to k3d cluster, swap k3d-test-server-0 to ur cluster name