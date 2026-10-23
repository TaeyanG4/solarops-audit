"""Airflow only coordinates the same versioned application CLI."""

import json
import os
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from airflow.sdk import DAG, Param, task

RELEASE = json.loads(
    Path(
        os.getenv(
            "SOLAROPS_RELEASE_FILE",
            str(Path(__file__).resolve().parents[1] / "src/solarops/release.json"),
        )
    ).read_text(encoding="utf-8")
)


def cli_task(task_id, arguments, fault=False, extra_env=None, secret="solarops-app"):
    if os.getenv("SOLAROPS_EXECUTION_MODE", "local") == "kubernetes":
        from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
        from kubernetes.client import models as k8s

        env = {"SOLAROPS_DATA_DIR": "/data", "SOLAROPS_SOURCE_DIR": "/data/source"}
        env.update(
            {
                "SOLAROPS_DAG_ID": "{{ dag.dag_id }}",
                "SOLAROPS_DAG_RUN_ID": "{{ run_id }}",
                "SOLAROPS_TASK_ID": "{{ ti.task_id }}",
                "SOLAROPS_TASK_ATTEMPT": "{{ ti.try_number }}",
            }
        )
        env.update(extra_env or {})
        if fault:
            env["SOLAROPS_FAIL_ONCE_MARKER"] = "{{ params.fault_marker }}"
            env["SOLAROPS_TEST_DELAY"] = "{{ params.test_delay }}"
        return KubernetesPodOperator(
            task_id=task_id,
            name="solarops-" + task_id.replace("_", "-"),
            namespace="solarops",
            image=RELEASE["worker_image"],
            image_pull_policy="IfNotPresent",
            cmds=["solarops"],
            arguments=arguments,
            in_cluster=True,
            service_account_name="solarops-worker",
            get_logs=True,
            env_vars=[k8s.V1EnvVar(name=k, value=v) for k, v in env.items()]
            + [
                k8s.V1EnvVar(
                    name="SOLAROPS_POD_" + key,
                    value_from=k8s.V1EnvVarSource(
                        field_ref=k8s.V1ObjectFieldSelector(field_path="metadata." + field)
                    ),
                )
                for key, field in (("UID", "uid"), ("NAME", "name"), ("NAMESPACE", "namespace"))
            ],
            env_from=[k8s.V1EnvFromSource(secret_ref=k8s.V1SecretEnvSource(name=secret))],
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
    def local_cli(args, overrides, fault_marker="", test_delay="0"):
        from airflow.sdk import get_current_context

        if secret != "solarops-app":
            raise RuntimeError("Isolated public benchmark requires Kubernetes execution mode")
        env = os.environ.copy()
        env.update(overrides)
        context = get_current_context()
        env.update(
            {
                "SOLAROPS_DAG_ID": context["dag"].dag_id,
                "SOLAROPS_DAG_RUN_ID": context["run_id"],
                "SOLAROPS_TASK_ID": context["ti"].task_id,
                "SOLAROPS_TASK_ATTEMPT": str(context["ti"].try_number),
            }
        )
        if fault:
            env["SOLAROPS_FAIL_ONCE_MARKER"] = fault_marker
            env["SOLAROPS_TEST_DELAY"] = test_delay
        subprocess.run(
            [os.getenv("SOLAROPS_CLI", "solarops"), *args], check=True, env=env, timeout=900
        )

    return local_cli(
        arguments,
        extra_env or {},
        "{{ params.fault_marker }}" if fault else "",
        "{{ params.test_delay }}" if fault else "0",
    )


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


def make_ons_dag():
    with DAG(
        dag_id="solarops_ons_daily",
        schedule="0 5 * * *",
        start_date=datetime(2026, 10, 1, tzinfo=UTC),
        catchup=False,
        max_active_runs=1,
        max_active_tasks=1,
        is_paused_upon_creation=True,
        dagrun_timeout=timedelta(minutes=30),
        default_args={
            "retries": 2,
            "retry_delay": timedelta(minutes=2),
            "execution_timeout": timedelta(minutes=20),
        },
        params={"as_of": Param("", type="string", pattern=r"^([0-9]{4}-[0-9]{2}-[0-9]{2})?$")},
        tags=["solarops", "incremental-public-source"],
        description="ONS previous/current month corrections; source-native MWmed, timezone unspecified.",
    ) as dag:
        cli_task(
            "collect_ons_months",
            ["ons-sync", "--as-of", "{{ params.as_of or data_interval_end.strftime('%Y-%m-%d') }}"],
        )
    return dag


def make_public_benchmark(concurrency):
    """Same four public days, isolated databases/buckets and bounded task slots."""
    with DAG(
        dag_id=f"solarops_public_benchmark_{concurrency}",
        schedule=None,
        start_date=datetime(2024, 4, 1, tzinfo=UTC),
        catchup=False,
        max_active_runs=1,
        max_active_tasks=concurrency,
        is_paused_upon_creation=True,
        dagrun_timeout=timedelta(minutes=15),
        default_args={
            "retries": 2,
            "retry_delay": timedelta(seconds=15),
            "execution_timeout": timedelta(minutes=10),
        },
        params={
            "benchmark_id": Param(
                "benchmark-public", type="string", pattern=r"^benchmark-[A-Za-z0-9_-]{1,60}$"
            )
        },
        tags=["solarops", "benchmark", "public"],
        description="Manual four-day PS_001 benchmark, isolated storage, no source download.",
    ) as dag:
        for day in range(1, 5):
            cli_task(
                f"public_day_{day}",
                [
                    "replay",
                    "--source-kind",
                    "public",
                    "--plant",
                    "PS_001",
                    "--from",
                    f"2024-04-{day:02d}",
                    "--to",
                    f"2024-04-{day + 1:02d}",
                    "--source-version",
                    "brpvgen-public-v1",
                    "--dry-run",
                    "false",
                ],
                extra_env={
                    "SOLAROPS_DATA_DIR": "/data/benchmarks/{{ params.benchmark_id }}",
                    "SOLAROPS_PROFILE": "1",
                },
                secret=f"solarops-benchmark-{concurrency}",
            )
    return dag
