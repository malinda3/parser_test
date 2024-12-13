#!bin/bash

docker rm -f bot_container 2>/dev/null
docker rmi bot_container -f 2>/dev/null

docker build -t bot .
docker run --name bot_container -d bot
