SERVICES := kafka my-postgres dbgo bot parser spam-bot
IMAGE_NAMES := my-postgres dbgo bot parser spam-bot

POSTGRES_PATH := ./postgres
DBGO_PATH := ./db_go
BOT_PATH := ./bot
PARSER_PATH := ./parser
SPAM_BOT_PATH := ./spam_bot
KAFKA_PATH := ./k3

define build_image
	@echo "Building Docker image for $(1)..."
	docker build -t $(1):latest $(2)
	@echo "Importing image $(1) into k3d cluster test..."
	k3d image import $(1):latest -c test
endef

define deploy_service
	@echo "Deploying $(1) to Kubernetes..."
	kubectl apply -f $(2)/$(1).yaml
endef

define delete_service
	@echo "Deleting $(1) from Kubernetes..."
	kubectl delete -f $(2)/$(1).yaml
	docker rmi $(1):latest -f || true
endef

install-deps:
	@echo "curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl""
	@echo "curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash"

init-cluster:
	k3d cluster create test

create-namespace:
	kubectl create namespace kafka

init: install-deps init-cluster create-namespace
#BUILD
build-my-postgres:
	@echo "Building Docker image for my-postgres..."
	$(call build_image,my-postgres,$(POSTGRES_PATH))

build-dbgo:
	@echo "Building Docker image for dbgo..."
	$(call build_image,dbgo,$(DBGO_PATH))

build-bot:
	@echo "Building Docker image for bot..."
	$(call build_image,bot,$(BOT_PATH))

build-parser:
	@echo "Building Docker image for parser..."
	$(call build_image,parser,$(PARSER_PATH))

build-spam-bot:
	@echo "Building Docker image for spam-bot..."
	$(call build_image,spam-bot,$(SPAM_BOT_PATH))

build: build-my-postgres build-dbgo build-bot build-parser build-spam-bot
#DEPLOY
deploy-my-postgres:
	$(call deploy_service,my-postgres,$(POSTGRES_PATH))

deploy-dbgo:
	$(call deploy_service,dbgo,$(DBGO_PATH))

deploy-bot:
	$(call deploy_service,bot,$(BOT_PATH))

deploy-parser:
	$(call deploy_service,parser,$(PARSER_PATH))

deploy-spam-bot:
	$(call deploy_service,spam-bot,$(SPAM_BOT_PATH))

deploy-kafka:
	$(call deploy_service,kafka,$(KAFKA_PATH))



deploy: deploy-kafka deploy-my-postgres deploy-dbgo deploy-bot deploy-parser deploy-spam-bot 
#DELETE
delete-my-postgres:
	$(call delete_service,my-postgres,$(POSTGRES_PATH))

delete-dbgo:
	$(call delete_service,dbgo,$(DBGO_PATH))

delete-bot:
	$(call delete_service,bot,$(BOT_PATH))

delete-parser:
	$(call delete_service,parser,$(PARSER_PATH))

delete-spam-bot:
	$(call delete_service,spam-bot,$(SPAM_BOT_PATH))

delete-kafka:
	kubectl delete -f k3/kafka.yaml

delete: delete-my-postgres delete-dbgo delete-bot delete-parser delete-spam-bot delete-kafka
#REBUILD
rebuild-bot: delete-bot build-bot deploy-bot

rebuild-dbgo: delete-dbgo build-dbgo deploy-dbgo

rebuild-spam-bot: delete-spam-bot build-spam-bot deploy-spam-bot

rebuild-parser: delete-parser build-parser deploy-parser

rebuild: delete build deploy
