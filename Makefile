SERVICES := parser telegram-bot
IMAGE_NAMES := parser telegram-bot
PARSER_PATH := ./parser
BOT_PATH := ./user_bot
POSTGRES_PATH := ./postgres

define build_image
	@echo "Building Docker image for $(1)..."
	docker build -t $(1):latest $(2)
	@echo "Importing image $(1) into k3d cluster test..."
	k3d image import $(1):latest -c test
endef

define deploy_service
	@echo "Deploying $(1) to Kubernetes..."
	kubectl apply -f $(2)
endef

define delete_service
	@echo "Deleting $(1) from Kubernetes..."
	kubectl delete -f $(2)
	docker rmi $(1):latest -f || true
endef

install-deps:
	@echo "Installing k3d..."
	curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

init-cluster:
	k3d cluster create test

# BUILD TARGETS
build-parser:
	$(call build_image,parser,$(PARSER_PATH))

build-bot:
	$(call build_image,telegram-bot,$(BOT_PATH))

build-postgres:
	$(call build_image,postgres,$(POSTGRES_PATH))

build: build-parser build-bot build-postgres

# DEPLOY TARGETS
deploy-parser:
	$(call deploy_service,parser,$(PARSER_PATH))

deploy-bot:
	$(call deploy_service,telegram-bot,$(BOT_PATH))

deploy-postgres:
	$(call deploy_service,postgres,$(POSTGRES_PATH))

create-namespace:
	@echo "Creating namespace kafka if not exists..."
	kubectl create namespace kafka || true

deploy: create-namespace build deploy-parser deploy-bot deploy-postgres

# DELETE TARGETS
delete-parser:
	$(call delete_service,parser,$(PARSER_PATH))

delete-bot:
	$(call delete_service,telegram-bot,$(BOT_PATH))

delete-postgres:
	$(call delete_service,postgres,$(POSTGRES_PATH))

delete: delete-parser delete-bot delete-postgres

# REBUILD TARGETS
rebuild-parser: delete-parser build-parser deploy-parser deploy-postgres

rebuild-bot: delete-bot build-bot deploy-bot deploy-postgres

rebuild: delete build deploy

# UTILITY TARGETS
logs-bot:
	kubectl logs -n kafka deployment/telegram-bot -f

logs-parser:
	kubectl logs -n kafka deployment/parser -f