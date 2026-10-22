-- Generated from solarops.storage.postgres; additive baseline only.

CREATE TABLE active_partition_manifest (
	org_id VARCHAR NOT NULL,
	plant_id VARCHAR NOT NULL,
	partition_id VARCHAR NOT NULL,
	report_timezone VARCHAR NOT NULL,
	calculation_version VARCHAR NOT NULL,
	run_id VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (org_id, plant_id, partition_id, report_timezone, calculation_version)
)

;


CREATE TABLE active_report_manifest (
	org_id VARCHAR NOT NULL,
	period VARCHAR NOT NULL,
	scope VARCHAR NOT NULL,
	report_timezone VARCHAR NOT NULL,
	report_run_id VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (org_id, period, scope, report_timezone)
)

;


CREATE TABLE anomaly_event (
	run_id VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (run_id)
)

;


CREATE TABLE daily_plant_metric (
	run_id VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (run_id)
)

;


CREATE TABLE dim_plant (
	org_id VARCHAR NOT NULL,
	plant_id VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (org_id, plant_id)
)

;


CREATE TABLE dq_issue (
	run_id VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (run_id)
)

;


CREATE TABLE pipeline_run (
	run_id VARCHAR NOT NULL,
	org_id VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (run_id)
)

;


CREATE TABLE report_run (
	report_run_id VARCHAR NOT NULL,
	org_id VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (report_run_id)
)

;


CREATE TABLE source_object (
	source_object_id VARCHAR NOT NULL,
	org_id VARCHAR NOT NULL,
	sha256 VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (source_object_id),
	UNIQUE (org_id, sha256)
)

;


CREATE TABLE source_version (
	org_id VARCHAR NOT NULL,
	plant_id VARCHAR NOT NULL,
	source_version VARCHAR NOT NULL,
	payload JSON NOT NULL,
	PRIMARY KEY (org_id, plant_id, source_version)
)

;