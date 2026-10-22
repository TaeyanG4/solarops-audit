"""Airflow only coordinates the same versioned application CLI."""

import os
import subprocess
from datetime import UTC, datetime, timedelta

from airflow.sdk import DAG, Param, task


def cli_task(task_id, arguments, fault=False):
    if os.getenv("SOLAROPS_EXECUTION_MODE", "local") == "kubernetes":
        from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
        from kubernetes.client import models as k8s

        env = {"SOLAROPS_DATA_DIR": "/data", "SOLAROPS_SOURCE_DIR": "/data/source"}
        if fault:
            env["SOLAROPS_FAIL_ONCE_MARKER"] = "{{ params.fault_marker }}"
            env["SOLAROPS_TEST_DELAY"] = "{{ params.test_delay }}"
        return KubernetesPodOperator(
            task_id=task_id,
            name="solarops-" + task_id.replace("_", "-"),
            namespace="solarops",
            image="solarops-worker:0.3.1",
            image_pull_policy="IfNotPresent",
            cmds=["solarops"],
            arguments=arguments,
            in_cluster=True,
            service_account_name="solarops-worker",
            get_logs=True,
            env_vars=env,
            env_from=[k8s.V1EnvFromSource(secret_ref=k8s.V1SecretEnvSource(name="solarops-app"))],
            volumes=[
                k8s.V1Volume(
                    name="data",
                    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                        claim_name="solarops-data"
                    ),
                ),
                k8s.V1Volume(name="tmp", empty_dir=k8s.V1EmptyDirVolumeSource()),
            ],
            volume_mounts=[
                k8s.V1VolumeMount(name="data", mount_path="/data"),
                k8s.V1VolumeMount(name="tmp", mount_path="/tmp"),
            ],
            container_resources=k8s.V1ResourceRequirements(
                requests={"cpu": "250m", "memory": "512Mi"}, limits={"cpu": "2", "memory": "2Gi"}
            ),
            security_context={"runAsUser": 10001, "runAsGroup": 10001, "fsGroup": 10001},
            container_security_context={
                "allowPrivilegeEscalation": False,
                "readOnlyRootFilesystem": True,
                "capabilities": {"drop": ["ALL"]},
            },
            startup_timeout_seconds=300,
            active_deadline_seconds=900,
            on_finish_action="keep_pod",
            do_xcom_push=False,
        )

    @task(task_id=task_id, do_xcom_push=False)
    def local_cli(args, fault_marker="", test_delay="0"):
        env = os.environ.copy()
        if fault:
            env["SOLAROPS_FAIL_ONCE_MARKER"] = fault_marker
            env["SOLAROPS_TEST_DELAY"] = test_delay
        subprocess.run(
            [os.getenv("SOLAROPS_CLI", "solarops"), *args], check=True, env=env, timeout=900
        )

    return local_cli(arguments, "{{ params.fault_marker }}", "{{ params.test_delay }}")


def make_dag(dag_id, schedule=None, mode="ingest"):
    params = {
        "source_kind": Param("synthetic", enum=["synthetic", "public"]),
        "plant": Param("DEMO_01", type="string", pattern="^(DEMO_01|PS_[0-9]{3})$"),
        "from_date": Param("2024-04-01", type="string", format="date"),
        "to_date": Param("2024-04-08", type="string", format="date"),
        "source_version": Param("synthetic-v1", type="string", pattern="^[A-Za-z0-9_-]{1,80}$"),
        "period": Param("2024-04", type="string", pattern="^[0-9]{4}-[0-9]{2}$"),
        "dry_run": Param("true" if mode == "backfill" else "false", enum=["true", "false"]),
        "fault_marker": Param("", type="string", pattern="^[A-Za-z0-9_-]{0,80}$"),
        "test_delay": Param("0", enum=["0", "30", "60", "120"]),
    }
    with DAG(
        dag_id=dag_id,
        schedule=schedule,
        start_date=datetime(2024, 4, 1, tzinfo=UTC),
        catchup=False,
        max_active_runs=1,
        dagrun_timeout=timedelta(minutes=45),
        default_args={
            "retries": 2,
            "retry_delay": timedelta(seconds=15),
            "retry_exponential_backoff": True,
            "execution_timeout": timedelta(minutes=20),
        },
        params=params,
        tags=["solarops", "historical-replay"],
        is_paused_upon_creation=True,
        description="Bounded public BR-PVGen or synthetic replay. Never a live source feed.",
    ) as dag:
        if mode in ("ingest", "backfill"):
            inspect = cli_task("validate_runtime", ["doctor"])
            publish = cli_task(
                "replay_validate_publish",
                [
                    "replay",
                    "--source-kind",
                    "{{ params.source_kind }}",
                    "--plant",
                    "{{ params.plant }}",
                    "--from",
                    "{{ params.from_date }}",
                    "--to",
                    "{{ params.to_date }}",
                    "--source-version",
                    "{{ params.source_version }}",
                    "--dry-run",
                    "{{ params.dry_run }}",
                ],
                fault=True,
            )
            inspect >> publish
        elif mode == "quality":
            cli_task(
                "verify_published_metrics",
                [
                    "analyze",
                    "--from",
                    "{{ params.from_date }}",
                    "--to",
                    "{{ params.to_date }}",
                    "--plant",
                    "{{ params.plant }}",
                    "--source-kind",
                    "{{ params.source_kind }}",
                ],
            )
        else:
            validated = cli_task(
                "await_validated_data",
                [
                    "analyze",
                    "--period",
                    "{{ params.period }}",
                    "--plant",
                    "{{ params.plant }}",
                    "--source-kind",
                    "{{ params.source_kind }}",
                ],
            )
            report = cli_task(
                "generate_check_lineage_publish_report",
                [
                    "report",
                    "--period",
                    "{{ params.period }}",
                    "--plant",
                    "{{ params.plant }}",
                    "--source-kind",
                    "{{ params.source_kind }}",
                ],
            )
            validated >> report
    return dag
