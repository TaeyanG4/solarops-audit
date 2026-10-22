"""Offline lifecycle/security tests. No Docker, network, or raw datasets."""

import json
import threading
import time

import pytest
from fastapi.testclient import TestClient

from solarops.admin.app import create_admin_app
from solarops.admin.services import ControlError, ServiceManager


@pytest.fixture
def root(tmp_path):
    compose = tmp_path / "infra/compose/compose.yaml"
    compose.parent.mkdir(parents=True)
    compose.write_text("name: solarops-audit")
    return tmp_path


def item(root, name, *, kind=False, oneoff=False, state="running"):
    return {
        "id": name + "-id",
        "name": "/solarops-" + name,
        "state": state,
        "health": "healthy",
        "labels": {"io.x-k8s.kind.cluster": "solarops", "io.x-k8s.kind.role": "control-plane"}
        if kind
        else {
            "com.docker.compose.project": "solarops-audit",
            "com.docker.compose.service": name,
            "com.docker.compose.project.config_files": str(root / "infra/compose/compose.yaml"),
            "com.docker.compose.oneoff": str(oneoff),
        },
    }


class FakeDocker:
    def __init__(self, items):
        self.items, self.calls = items, []
        self.fail = None

    def __call__(self, args, timeout=15):
        self.calls.append(args)
        if args[1:] == ["context", "show"]:
            return "local"
        if args[1:3] == ["context", "inspect"]:
            return json.dumps([{"Endpoints": {"docker": {"Host": "unix:///var/run/docker.sock"}}}])
        assert args[1:3] == ["--context", "local"]
        cmd = args[3:]
        if cmd[0] == "ps":
            return " ".join(i["id"] for i in self.items)
        if cmd[0] == "inspect":
            return "\n".join(json.dumps(i) for i in self.items)
        if cmd[0] == self.fail:
            raise ControlError("Simulated command failure")
        if cmd[0] in {"start", "stop"}:
            for entry in self.items:
                if entry["id"] in cmd:
                    entry["state"] = "running" if cmd[0] == "start" else "exited"
            return ""
        raise AssertionError(cmd)


def finish(manager):
    deadline = time.monotonic() + 3
    while manager.lock.locked() and time.monotonic() < deadline:
        time.sleep(0.005)
    assert not manager.lock.locked()
    return manager.operation_status()


def manager_for(root, items):
    fake = FakeDocker(items)
    return ServiceManager(root, runner=fake, probe=lambda url: True), fake


def test_local_identity_and_response_does_not_expose_labels(root):
    manager, _ = manager_for(root, [item(root, "app-db"), item(root, "control-plane", kind=True)])
    data = manager.status()
    assert data["engine"] == "reachable"
    assert {row["service"] for row in data["containers"]} == {"app-db", "kind"}
    assert "labels" not in data["containers"][0]
    assert str(root) not in json.dumps(data)


@pytest.mark.parametrize("mismatch", ["path", "project", "service", "kind_name", "kind_role"])
def test_wrong_project_or_unknown_service_cannot_be_controlled(root, mismatch):
    row = item(root, "app-db")
    if mismatch == "path":
        row["labels"]["com.docker.compose.project.config_files"] = "/another/checkout.yaml"
    if mismatch == "project":
        row["labels"]["com.docker.compose.project"] = "another"
    if mismatch == "service":
        row["labels"]["com.docker.compose.service"] = "unapproved"
    if mismatch.startswith("kind"):
        row = item(root, "control-plane", kind=True)
        if mismatch == "kind_name":
            row["name"] = "/unrelated"
        else:
            row["labels"]["io.x-k8s.kind.role"] = "unknown"
    manager, fake = manager_for(root, [row])
    manager.submit("workspace", "stop")
    assert finish(manager)["state"] == "failed"
    assert not any("stop" in call for call in fake.calls)


def test_remote_docker_context_rejected(root):
    def runner(args, timeout=15):
        if args[1:] == ["context", "show"]:
            return "remote"
        return json.dumps([{"Endpoints": {"docker": {"Host": "tcp://remote:2375"}}}])

    manager = ServiceManager(root, runner=runner, probe=lambda url: True)
    with pytest.raises(ControlError, match="로컬"):
        manager.inventory()


def test_start_orders_dependencies_and_never_replays_oneoff(root):
    rows = [item(root, name, state="exited") for name in ("dashboard", "minio", "app-db")]
    rows.append(item(root, "worker", oneoff=True, state="exited"))
    manager, fake = manager_for(root, rows)
    manager.submit("workspace", "start")
    assert finish(manager)["state"] == "succeeded"
    starts = [c[-1] for c in fake.calls if "start" in c]
    assert starts == ["app-db-id", "minio-id", "dashboard-id"]
    assert rows[-1]["state"] == "exited"
    entries = [
        json.loads(line)
        for line in (root / "artifacts/ops/admin-actions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [entry["state"] for entry in entries] == ["running", "succeeded"]


def test_db_stop_includes_compose_consumers_but_preserves_minio_and_kind(root):
    rows = [item(root, s) for s in ("app-db", "minio", "dashboard", "airflow-api", "worker")]
    rows.append(item(root, "control-plane", kind=True))
    manager, fake = manager_for(root, rows)
    manager.submit("database", "stop")
    assert finish(manager)["state"] == "succeeded"
    stopped = [c[-1] for c in fake.calls if "stop" in c]
    assert stopped == [
        "airflow-api-id",
        "worker-id",
        "dashboard-id",
        "app-db-id",
    ]
    assert rows[1]["state"] == "running"
    assert rows[-1]["state"] == "running"


def test_missing_start_is_preflighted_before_any_mutation(root):
    manager, fake = manager_for(root, [item(root, "app-db", state="exited")])
    manager.submit("workspace", "start")
    assert "생성되지 않은" in finish(manager)["error"]
    assert not any("start" in call for call in fake.calls)


def test_partial_failure_visible_and_lock_released(root):
    manager, fake = manager_for(root, [item(root, "dashboard")])
    fake.fail = "stop"
    manager.submit("dashboard", "stop")
    assert finish(manager)["state"] == "failed"
    fake.fail = None
    manager.submit("dashboard", "stop")
    assert finish(manager)["state"] == "succeeded"


def test_concurrent_operations_rejected(root):
    manager, _ = manager_for(root, [])
    gate = threading.Event()
    manager.inventory = lambda: gate.wait(2) or []
    manager.submit("workspace", "stop")
    try:
        with pytest.raises(ControlError, match="진행 중"):
            manager.submit("workspace", "start")
    finally:
        gate.set()
        finish(manager)


@pytest.fixture
def client(root):
    manager, fake = manager_for(root, [])
    app = create_admin_app(root, manager=manager)
    return TestClient(app, base_url="http://127.0.0.1:8504", client=("127.0.0.1", 50000))


def test_admin_security_origin_host_token_and_confirmation(client):
    session = client.get("/api/admin/session")
    assert session.status_code == 200
    token = session.json()["token"]
    body = {"target": "workspace", "action": "stop", "confirmed": True}
    headers = {"Origin": "http://127.0.0.1:8504", "X-SolarOps-Token": token}
    assert client.post("/api/admin/actions", json=body).status_code == 403
    assert (
        client.post(
            "/api/admin/actions", json=body, headers={**headers, "Origin": "https://evil.invalid"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/admin/actions", json=body, headers={**headers, "X-SolarOps-Token": "wrong"}
        ).status_code
        == 403
    )
    assert (
        client.get("/api/admin/session", headers={"Host": "evil.invalid:8504"}).status_code == 403
    )
    assert (
        client.get("/api/admin/session", headers={"Sec-Fetch-Site": "cross-site"}).status_code
        == 403
    )
    assert client.get("/api/admin/session", headers={"Origin": "null"}).status_code == 403
    assert (
        client.post(
            "/api/admin/actions", json={**body, "confirmed": False}, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/admin/actions", json={**body, "command": "rm"}, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/admin/actions", json={**body, "target": "other-project"}, headers=headers
        ).status_code
        == 422
    )
    assert client.post("/api/admin/actions", json=body, headers=headers).status_code == 202
    assert session.headers["cache-control"] == "no-store"
    assert session.headers["x-frame-options"] == "DENY"
    assert "access-control-allow-origin" not in session.headers


def test_admin_does_not_mount_data_api_and_remote_clients_blocked(root, client):
    assert client.get("/api/v1/overview").status_code == 404
    app = create_admin_app(root, manager=manager_for(root, [])[0])
    remote = TestClient(app, base_url="http://127.0.0.1:8504", client=("192.0.2.1", 50000))
    assert remote.get("/").status_code == 403
