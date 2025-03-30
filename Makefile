SERVICES := parser
IMAGE_NAMES := parser
PARSER_PATH := ./parser


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
	@echo "curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash"

init-cluster:
	k3d cluster create test

#BUILD

build-parser:
	@echo "Building Docker image for parser..."
	$(call build_image,parser,$(PARSER_PATH))

build: build-parser
#DEPLOY

deploy-parser:
	$(call deploy_service,parser,$(PARSER_PATH))


create-namespace:
	@echo "Creating namespace $(NAMESPACE) if not exists..."
	kubectl create namespace kafka

deploy: create-namespace deploy-parser
#DELETE
delete-parser:
	$(call delete_service,parser,$(PARSER_PATH))


delete: delete-parser
#REBUILD
rebuild-parser: delete-parser build-parser deploy-parser


