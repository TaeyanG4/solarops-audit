"""Allowlisted lifecycle controls for already provisioned, local SolarOps resources.

No shell, resource creation, SQL, volume removal, or global Docker-engine controls.
Container IDs are discovered by labels and checked against the trusted checkout.
"""

import json
import os
import shutil
import subprocess
import threading
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

PROJECT = "solarops-audit"
AIRFLOW = (
    "airflow-api",
    "airflow-scheduler",
    "airflow-dag-processor",
    "airflow-init",
    "airflow-db",
)
CONSUMERS = (*AIRFLOW, "worker", "dashboard")
STARTS = {
    "workspace": ("app-db", "minio", "dashboard"),
    "dashboard": ("app-db", "minio", "dashboard"),
    "database": ("app-db",),
    "storage": ("minio",),
    "airflow": (
        "app-db",
        "minio",
        "airflow-db",
        "airflow-api",
        "airflow-scheduler",
        "airflow-dag-processor",
    ),
    "kubernetes": ("kind",),
}
STOPS = {
    "workspace": ("kind", *CONSUMERS, "minio", "app-db"),
    "dashboard": ("dashboard",),
    "database": (*CONSUMERS, "app-db"),
    "storage": (*CONSUMERS, "minio"),
    "airflow": AIRFLOW,
    "kubernetes": ("kind",),
}
LABELS = {
    "workspace": "SolarOps 작업 환경",
    "dashboard": "대시보드",
    "database": "PostgreSQL (Compose)",
    "storage": "MinIO 저장소 (Compose)",
    "airflow": "Airflow (Compose)",
    "kubernetes": "Kubernetes (kind)",
}
IMPACTS = {
    "workspace": "SolarOps의 대시보드·DB·저장소·Airflow·작업 컨테이너와 kind 클러스터를 중지합니다. 진행 중 작업이 중단될 수 있습니다. 로컬 관리 서버와 다른 Docker 프로젝트는 계속 실행됩니다.",
    "dashboard": "분석 화면(8502)을 중지합니다. DB·저장소·Airflow·Kubernetes는 유지됩니다.",
    "database": "Compose의 대시보드·Airflow·작업 컨테이너를 먼저 중지한 뒤 PostgreSQL을 중지합니다. 진행 중 작업이 중단될 수 있습니다. MinIO와 별도 Kubernetes 환경은 유지됩니다.",
    "storage": "Compose의 대시보드·Airflow·작업 컨테이너를 먼저 중지한 뒤 MinIO를 중지합니다. 진행 중 작업이 중단될 수 있습니다. PostgreSQL과 별도 Kubernetes 환경은 유지됩니다.",
    "airflow": "Airflow 스케줄러·API·DAG 처리기·전용 DB를 중지합니다. 진행 중 Airflow 작업이 중단될 수 있습니다. 분석 화면과 kind는 유지됩니다.",
    "kubernetes": "SolarOps kind 노드를 중지합니다. 클러스터 안의 진행 중 작업이 중단될 수 있습니다. 다른 클러스터와 Docker 엔진은 유지됩니다.",
}


class ControlError(RuntimeError):
    pass


def command(args, timeout=15):
    """Capture internally; never return raw CLI output/errors to browser or logs."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("DOCKER_")}
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ControlError(
            "명령을 실행하지 못했거나 제한 시간을 초과했습니다. Docker Desktop 상태를 확인하세요."
        ) from exc
    if result.returncode:
        raise ControlError(
            "서비스 명령이 실패했습니다. Docker Desktop에서 해당 컨테이너 상태와 로그를 확인하세요."
        )
    return result.stdout.strip()


def http_ready(url):
    try:
        # Loopback probes must not travel through a configured HTTP proxy.
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
            url, timeout=3
        ) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False


class ServiceManager:
    def __init__(self, root: Path, runner=command, probe=http_ready):
        self.root = root.resolve()
        if not (self.root / "infra/compose/compose.yaml").is_file():
            raise ValueError("SolarOps 체크아웃 루트를 --project-root로 지정하세요.")
        self.runner, self.probe = runner, probe
        self.docker = shutil.which("docker") or "docker"
        self.lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.operation = None
        self.context = None

    def _docker(self, *args, timeout=15):
        if self.context is None:
            context = self.runner([self.docker, "context", "show"], timeout=10)
            raw = self.runner([self.docker, "context", "inspect", context], timeout=10)
            endpoint = json.loads(raw)[0]["Endpoints"]["docker"]["Host"]
            if not endpoint.startswith(("npipe://", "unix://")):
                raise ControlError(
                    "로컬 Docker 컨텍스트만 지원합니다. 원격 Docker는 제어하지 않습니다."
                )
            self.context = context
        return self.runner([self.docker, "--context", self.context, *args], timeout=timeout)

    def inventory(self):
        """Only inspect matching IDs; never inspect/export environment or mounts."""
        ids = set()
        for label in (f"com.docker.compose.project={PROJECT}", "io.x-k8s.kind.cluster=solarops"):
            ids.update(self._docker("ps", "-aq", "--filter", f"label={label}").split())
        if not ids:
            return []
        fmt = '{"id":{{json .Id}},"name":{{json .Name}},"state":{{json .State.Status}},"health":{{with (index .State "Health")}}{{json .Status}}{{else}}"not_configured"{{end}},"labels":{{json .Config.Labels}}}'
        raw = self._docker("inspect", "--format", fmt, *sorted(ids))
        found = []
        config_path = self.root / "infra/compose/compose.yaml"
        for line in raw.splitlines():
            item = json.loads(line)
            labels = item.pop("labels") or {}
            name = item["name"].lstrip("/")
            if labels.get("io.x-k8s.kind.cluster") == "solarops":
                if not name.startswith("solarops-") or labels.get("io.x-k8s.kind.role") not in {
                    "control-plane",
                    "worker",
                }:
                    raise ControlError(
                        "SolarOps kind 자원 식별이 일치하지 않아 제어를 중단했습니다."
                    )
                service = "kind"
            else:
                actual = labels.get("com.docker.compose.project.config_files", "")
                if (
                    labels.get("com.docker.compose.project") != PROJECT
                    or Path(actual).resolve() != config_path
                ):
                    raise ControlError(
                        "같은 이름의 다른 체크아웃 자원이 있습니다. 관리 서버의 프로젝트 경로를 확인하세요."
                    )
                service = labels.get("com.docker.compose.service")
                if service not in {*CONSUMERS, "app-db", "minio"}:
                    raise ControlError(
                        "허용 목록 밖의 SolarOps 서비스가 있습니다. Compose 구성을 확인하세요."
                    )
            found.append(
                {
                    **item,
                    "name": name,
                    "service": service,
                    "oneoff": labels.get("com.docker.compose.oneoff", "False").lower() == "true",
                }
            )
        return sorted(found, key=lambda row: (row["service"], row["name"]))

    def operation_status(self):
        with self.state_lock:
            return dict(self.operation) if self.operation else None

    def _audit(self):
        directory = self.root / "artifacts/ops"
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "admin-actions.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self.operation_status(), ensure_ascii=False) + "\n")

    def _progress(self, **changes):
        with self.state_lock:
            self.operation.update(changes)

    def status(self):
        try:
            items = self.inventory()
            error = None
        except (ControlError, ValueError, KeyError):
            items, error = (
                [],
                "Docker에 연결할 수 없거나 자원 식별이 일치하지 않습니다. Docker Desktop과 프로젝트 경로를 확인하세요.",
            )
        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "engine": "unavailable" if error else "reachable",
            "error": error,
            "containers": items,
            "operation": self.operation_status(),
            "dashboard_ready": self.probe("http://127.0.0.1:8502/ready") if not error else False,
            "storage_ready": self.probe("http://127.0.0.1:59000/minio/health/ready")
            if not error
            else False,
            "targets": [
                {
                    "id": key,
                    "label": label,
                    "stop_impact": IMPACTS[key],
                    "start_services": list(STARTS[key]),
                    "stop_services": list(STOPS[key]),
                }
                for key, label in LABELS.items()
            ],
            "manager": "호스트 Python · 127.0.0.1:8504 · Docker와 독립 실행",
        }

    def submit(self, target, action):
        if target not in STARTS or action not in {"start", "stop"}:
            raise ValueError("지원하지 않는 작업입니다.")
        if not self.lock.acquire(blocking=False):
            raise ControlError("다른 작업이 진행 중입니다. 완료 후 다시 시도하세요.")
        with self.state_lock:
            self.operation = {
                "target": target,
                "action": action,
                "state": "running",
                "step": "자원 확인",
                "started_at": datetime.now(UTC).isoformat(),
                "error": None,
            }
        try:
            self._audit()
        except OSError as exc:
            self._progress(state="failed", error="조작 기록을 저장할 수 없어 실행하지 않았습니다.")
            self.lock.release()
            raise ControlError("조작 기록을 저장할 수 없어 실행하지 않았습니다.") from exc
        thread = threading.Thread(target=self._execute, args=(target, action), daemon=True)
        thread.start()
        return self.operation_status()

    def _execute(self, target, action):
        try:
            items = self.inventory()
            services = STARTS[target] if action == "start" else STOPS[target]
            if action == "start":
                absent = [
                    s
                    for s in services
                    if not any(i["service"] == s and not i["oneoff"] for i in items)
                ]
                if absent:
                    raise ControlError(
                        "아직 생성되지 않은 서비스: "
                        + ", ".join(absent)
                        + ". 운영 가이드의 최초 구성을 먼저 실행하세요."
                    )
            for service in services:
                self._progress(step=service)
                # Refresh identity immediately before each command. IDs avoid name races.
                candidates = [
                    i
                    for i in self.inventory()
                    if i["service"] == service and (action == "stop" or not i["oneoff"])
                ]
                ids = [
                    i["id"]
                    for i in candidates
                    if (
                        i["state"] != "running"
                        if action == "start"
                        else i["state"] in {"running", "restarting", "paused"}
                    )
                ]
                if any(i["state"] == "paused" for i in candidates):
                    raise ControlError(
                        "일시 정지된 컨테이너가 있습니다. Docker Desktop에서 일시 정지를 해제한 뒤 다시 시도하세요."
                    )
                if ids:
                    args = ["start", *ids] if action == "start" else ["stop", "--time", "30", *ids]
                    self._docker(*args, timeout=120)
                if action == "start":
                    self._wait_ready(service)
                elif any(
                    i["state"] in {"running", "restarting", "paused"}
                    for i in self.inventory()
                    if i["service"] == service
                ):
                    raise ControlError(
                        f"{service}: 중지를 확인하지 못했습니다. 실제 상태를 다시 확인하세요."
                    )
            self._progress(
                state="succeeded", step="완료", finished_at=datetime.now(UTC).isoformat()
            )
        except Exception as exc:
            self._progress(
                state="failed",
                error=str(exc)
                if isinstance(exc, ControlError)
                else "서비스 상태를 확인하지 못했습니다. 로컬 Docker 상태를 확인하세요.",
                finished_at=datetime.now(UTC).isoformat(),
            )
        finally:
            try:
                self._audit()
            except OSError:
                self._progress(
                    state="failed",
                    error="최종 조작 기록 저장에 실패했습니다. 실제 컨테이너 상태를 확인하세요.",
                )
            self.lock.release()

    def _wait_ready(self, service):
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            items = [i for i in self.inventory() if i["service"] == service and not i["oneoff"]]
            ready = bool(items) and all(
                i["state"] == "running" and i["health"] not in {"starting", "unhealthy"}
                for i in items
            )
            if service == "dashboard":
                ready = ready and self.probe("http://127.0.0.1:8502/ready")
            elif service == "minio":
                ready = ready and self.probe("http://127.0.0.1:59000/minio/health/ready")
            elif service.endswith("db"):
                ready = ready and all(i["health"] == "healthy" for i in items)
            if ready:
                return
            time.sleep(1)
        raise ControlError(
            f"{service}: 준비 확인 시간이 초과됐습니다. 일부 서비스는 실행 중일 수 있습니다. 상태를 새로고침하세요."
        )
