"use strict";
const find = (selector) => document.querySelector(selector);
let adminToken,
  adminData,
  pendingAction,
  fetching = false,
  submitting = false;
const labels = {
  running: "실행 중",
  exited: "중지",
  created: "생성됨",
  restarting: "재시작 중",
  paused: "일시 정지",
  dead: "종료 오류",
  healthy: "정상",
  unhealthy: "비정상",
  starting: "준비 중",
  not_configured: "미설정",
};
function element(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    signal: AbortSignal.timeout(20000),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "요청을 처리하지 못했습니다. 상태를 새로고침하세요.",
    );
  return data;
}
function showError(message) {
  find("#admin-error").hidden = !message;
  find("#admin-error").textContent = message || "";
}
function updateDisabled() {
  const busy =
    submitting ||
    fetching ||
    adminData?.operation?.state === "running" ||
    adminData?.engine !== "reachable";
  document
    .querySelectorAll("[data-action]")
    .forEach((b) => (b.disabled = busy));
}
function ask(target, action) {
  pendingAction = { target: target.id, action, confirmed: true };
  const verb = action === "start" ? "시작" : "중지";
  find("#action-title").textContent = `${target.label} ${verb}`;
  find("#action-impact").textContent =
    action === "stop"
      ? target.stop_impact
      : `다음 서비스의 기존 컨테이너를 순서대로 시작합니다: ${target.start_services.join(" → ")}. 이미 실행 중이면 상태를 확인합니다. 중지 시 함께 멈췄던 다른 서비스는 자동으로 재개하지 않습니다.`;
  find("#confirm-action").textContent = `${verb} 실행`;
  find("#action-dialog").showModal();
  find("#cancel-action").focus();
}
function controls(data) {
  const host = find("#service-controls");
  // Keep nodes stable while polling: focus and open dialogs must not be displaced.
  if (host.children.length) {
    const membership = {
      workspace: [
        "app-db",
        "minio",
        "dashboard",
        "airflow-api",
        "airflow-scheduler",
        "airflow-db",
        "airflow-dag-processor",
        "kind",
      ],
      dashboard: ["dashboard"],
      database: ["app-db"],
      storage: ["minio"],
      airflow: [
        "airflow-api",
        "airflow-scheduler",
        "airflow-db",
        "airflow-dag-processor",
      ],
      kubernetes: ["kind"],
    };
    for (const target of data.targets) {
      const matches = data.containers.filter(
        (i) => membership[target.id].includes(i.service) && !i.oneoff,
      );
      const running = matches.filter((i) => i.state === "running").length;
      find(`[data-target-status="${target.id}"]`).textContent = data.error
        ? "상태 확인 불가"
        : `${running} / ${matches.length}개 실행 중${matches.length ? "" : " · 구성 필요"}`;
    }
    return;
  }
  const descriptions = {
    workspace: "기본 3개 서비스 시작 / 프로젝트 전체 중지",
    dashboard: "분석·월간 보고서 · 8502",
    database: "분석 카탈로그 · PostgreSQL · 55432",
    storage: "게시된 결과 저장소 · MinIO · 59000",
    airflow: "예약 처리·실행 관리 · 8080",
    kubernetes: "SolarOps kind 노드 · 선택 실행",
  };
  for (const target of data.targets) {
    const row = element("div", undefined, "service-row"),
      copy = element("div");
    const status = element("span", "확인 중…", "service-state");
    status.dataset.targetStatus = target.id;
    copy.append(
      element("h3", target.label),
      element("p", descriptions[target.id]),
      status,
    );
    const actions = element("div", undefined, "inline-actions");
    for (const [action, text] of [
      ["start", "시작"],
      ["stop", "중지"],
    ]) {
      const b = element("button", text, "secondary");
      b.dataset.action = `${target.id}-${action}`;
      b.setAttribute("aria-label", `${target.label} ${text}`);
      b.onclick = () => ask(target, action);
      actions.append(b);
    }
    row.append(copy, actions);
    host.append(row);
  }
  controls(data);
}
function renderContainers(data) {
  const host = find("#container-list");
  if (!data.containers.length) {
    host.replaceChildren(
      element(
        "p",
        data.error
          ? "연결 오류로 컨테이너 상태를 확인할 수 없습니다."
          : "구성된 SolarOps 컨테이너가 없습니다. 운영 가이드의 최초 구성이 필요합니다.",
      ),
    );
    return;
  }
  const wrap = element("div", undefined, "table-wrap"),
    table = element("table", undefined, "container-table");
  const head = element("thead"),
    header = element("tr"),
    body = element("tbody");
  for (const label of ["컨테이너", "실행 상태", "건강 검사", "서비스 준비"]) {
    const th = element("th", label);
    th.scope = "col";
    header.append(th);
  }
  head.append(header);
  for (const item of data.containers) {
    const row = element("tr");
    let ready = "별도 확인 필요";
    if (item.service === "dashboard")
      ready = data.dashboard_ready ? "API·DB·저장소 준비됨" : "미준비";
    else if (item.service === "minio")
      ready = data.storage_ready ? "저장소 준비됨" : "미준비";
    else if (item.service.endsWith("db"))
      ready =
        item.health === "healthy" && item.state === "running"
          ? "DB 연결 가능"
          : "미준비";
    if (item.state !== "running") ready = "실행되지 않음";
    [
      item.name,
      labels[item.state] || item.state,
      item.state === "running"
        ? labels[item.health] || item.health
        : "검사 중단",
      ready,
    ].forEach((text, i) => {
      const cell = element("td", text);
      cell.dataset.label = header.children[i].textContent;
      row.append(cell);
    });
    body.append(row);
  }
  table.append(head, body);
  wrap.append(table);
  host.replaceChildren(wrap);
}
async function refreshStatus() {
  if (fetching) return;
  fetching = true;
  find("#admin-refresh").disabled = true;
  try {
    if (!adminToken) adminToken = (await request("/api/admin/session")).token;
    const data = await request("/api/admin/status");
    adminData = data;
    find("#engine").textContent =
      data.engine === "reachable"
        ? "Docker 엔진 · 연결됨"
        : "Docker 엔진 · 확인 불가";
    find("#checked-at").textContent =
      `마지막 확인 ${new Date(data.checked_at).toLocaleTimeString("ko-KR")} · 5초마다 갱신`;
    showError(data.error);
    controls(data);
    renderContainers(data);
    const op = data.operation;
    if (op) {
      const target =
        data.targets.find((t) => t.id === op.target)?.label || op.target;
      find("#operation").textContent =
        `${target} ${op.action === "start" ? "시작" : "중지"} · ${op.state === "running" ? `진행 중 (${op.step})` : op.state === "succeeded" ? "완료" : `실패: ${op.error}`}`;
      find("#operation").className =
        op.state === "failed" ? "operation-failed" : "";
    }
  } catch (error) {
    adminData = undefined;
    find("#engine").textContent = "상태 확인 중단";
    showError(
      `${error.name === "TimeoutError" ? "응답 시간을 초과했습니다." : error.message} 관리 서버가 실행 중인지 확인한 뒤 새로고침하세요.`,
    );
  } finally {
    fetching = false;
    find("#admin-refresh").disabled = false;
    updateDisabled();
  }
}
find("#cancel-action").onclick = () => find("#action-dialog").close();
find("#confirm-action").onclick = async () => {
  if (!pendingAction || submitting) return;
  submitting = true;
  find("#action-dialog").close();
  updateDisabled();
  find("#operation").textContent = "요청을 보내고 있습니다…";
  try {
    await request("/api/admin/actions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-SolarOps-Token": adminToken,
      },
      body: JSON.stringify(pendingAction),
    });
    await refreshStatus();
  } catch (error) {
    // A lost response can still mean the server accepted the operation. Never retry automatically.
    find("#operation").textContent =
      `요청 결과를 확인하지 못했습니다: ${error.message} 자동 재시도하지 않습니다. 최근 작업과 실제 상태를 확인하세요.`;
    showError(error.message);
    if (error.message.includes("새로고침")) adminToken = undefined;
  } finally {
    submitting = false;
    pendingAction = undefined;
    updateDisabled();
  }
};
find("#admin-refresh").onclick = refreshStatus;
refreshStatus();
setInterval(() => {
  if (!document.hidden) refreshStatus();
}, 5000);
const adminQuery = new URLSearchParams(location.search);
for (const anchor of document.querySelectorAll(
  "nav a:not([data-view=system]), footer a",
)) {
  const url = new URL(anchor.href);
  if (/^\d{4}-\d{2}$/.test(adminQuery.get("period") || ""))
    url.searchParams.set("period", adminQuery.get("period"));
  if (["all", "public", "synthetic"].includes(adminQuery.get("source")))
    url.searchParams.set("source", adminQuery.get("source"));
  anchor.href = url.href;
}
