UV ?= uv
export UV_PROJECT_ENVIRONMENT ?= .venv-linux
export SOLAROPS_DATA_DIR ?= data/linux-native
COMPOSE = docker compose --env-file .env -f infra/compose/compose.yaml
.PHONY: install doctor lint test demo-sample demo-services download-metadata download-full up-local down-local db-migrate airflow-up dag-validate k8s-bootstrap k8s-deploy k8s-smoke serve test-services
install:
	$(UV) sync --frozen
doctor:
	$(UV) run solarops doctor
lint:
	$(UV) run ruff check src tests scripts dags
	$(UV) run ruff format --check src tests scripts dags
test:
	$(UV) run pytest -q
demo-sample:
	$(UV) run solarops demo
demo-services:
	$(COMPOSE) run --rm worker demo
serve:
	$(UV) run solarops serve
download-metadata:
	$(UV) run solarops source fetch
download-full:
	$(UV) run solarops source fetch --allow-large --files Readme.txt BR-PVGen_metadata.csv BR-PVGen_inverter.zip BR-PVGen_meteorological.zip
	$(UV) run solarops source extract data/source/BR-PVGen_inverter.zip data/source/inverter
	$(UV) run solarops source extract data/source/BR-PVGen_meteorological.zip data/source/station
up-local:
	bash scripts/bootstrap-local.sh
down-local:
	$(COMPOSE) --profile airflow stop
db-migrate:
	$(UV) run solarops db-migrate
airflow-up:
	$(COMPOSE) --profile airflow build airflow-api
	$(COMPOSE) --profile airflow run --rm airflow-init
	$(COMPOSE) --profile airflow up -d airflow-api airflow-scheduler airflow-dag-processor
dag-validate:
	docker run --rm -v "$(CURDIR)/scripts/validate_dags.py:/tmp/validate_dags.py:ro" --entrypoint python solarops-airflow:0.2.0 /tmp/validate_dags.py
test-services:
	$(UV) run python scripts/service-test.py
k8s-bootstrap:
	bash scripts/k8s-bootstrap.sh
k8s-deploy:
	bash scripts/k8s-deploy.sh
k8s-smoke:
	bash scripts/k8s-smoke.sh
