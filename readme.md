# v0.1
in this version i want to make completely working and ready to deply in a single cluster app.
first, and complete feature with newsletter bot
## Requirements

## Ready:
parser functional moved to api, probably working faster than kafka

added simple tg bot for iteraction with parser, will be user bot lately, working with just 2 pods(user-bot, parser) 
## Next goal:
Connect sqlit3 and start developing newsletter engine
## Future golas:
move whole project to selfhosted cluster

move to registry, so it can help me with moving to ci later

move to ci and make development easier
## Installing to the local machine:
### Step 1)

prepare cluster(k3d used in my version)
```
$ make install-deps && make init-cluster && make create-namespace
```
### Step 2) 

create secret with you telegram bot token, take it from @BotFather
```
$ kubectl create secret generic telegram-api-test-key --from-literal=API_KEY=<key> --namespace=kafka
```
### Step 3)
build images and deploy them to cluster
```
$ make build-bot && make build-parser
$ make deploy-bot && make deploy-parser
```

so you can see that both services running and configured with you secret

```
$ kubectl get pods -n kafka
NAME                            READY   STATUS    RESTARTS   AGE
parser-f7d4d7984-4w5sv          1/1     Running   0          26m
telegram-bot-67489f49b5-vtcj9   1/1     Running   0          13m
$ kubectl get secrets -n kafka
NAME                    TYPE     DATA   AGE
telegram-api-test-key   Opaque   1      52m
```