# v0.1

in this version i want to make completely working and ready to deploy in a single cluster app.
first, and complete feature with newsletter bot
## Requirements
tbd
## Ready:
- Parser feature fully moved from old version to a new one
- Newsletter feature probably ready, want to test it on next week(13.05.25)
- all splitted to microservices, each service performs its specific functions.
## Microservices functions
1) User Bot - allows user to check price, just by sending link.
2) Parser - bussiness logic, that takes info from page and send it to user bot.
3) Admin Bot - allows to use newsletter featuere that translate some messages between users.
4) Postgres - database, that admin bot and user bot uses 
## Next goal:
- test newsletter feature

- make some security changes 
## Problems:
- Engine doesnt work multiple times, need to restart pod after every message.
## Future goals:
- move whole project to selfhosted cluster

- move to registry, so it can help me with moving to ci later

- move to ci and make development easier
## Installing to the local machine:
1) prepare cluster(k3d used in my version, because its still not works with registry)
```
$ make install-deps && make init-cluster && make create-namespace
```
2)  create 2 secrets with you telegram bot token, and a secret with allowed users ids for admin-bot
```
$ kubectl create secret generic telegram-api-test-key --from-literal=API_KEY=<userbot_key> --namespace=kafka
$ kubectl create secret generic telegram-api-admin-test-key --from-literal=API_KEY=<adminbot_key> --namespace=kafka
$ kubectl create secret generic allowed-users --from-literal=ALLOWED_USER_IDS="123456789,976543213" --namespace=kafka
```
### Step 3)
build images and deploy them to cluster
```
$ make build
$ make deploy
```

so you can see that both services running and configured with you secret

```
$ kubectl get pods -n kafka
NAME                                  READY   STATUS    RESTARTS   AGE
admin-telegram-bot-769d5d8f49-g5jzn   1/1     Running   0          2m49s
parser-f7d4d7984-wn7lq                1/1     Running   0          118m
postgres-0                            1/1     Running   0          4h46m
telegram-bot-5d8d4b6767-xkvm4         1/1     Running   0          135m
$ kubectl get secrets -n kafka
NAME                          TYPE     DATA   AGE
allowed-users                 Opaque   1      3h10m
telegram-api-admin-test-key   Opaque   1      4h22m
telegram-api-test-key         Opaque   1      6h6m
$ kubectl get svc -n kafka
NAME       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
parser     ClusterIP   10.43.36.205    <none>        8000/TCP   118m
postgres   ClusterIP   10.43.168.192   <none>        5432/TCP   4h46m
```