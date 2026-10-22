"use strict";

const $ = (selector) => document.querySelector(selector);
const view = $("#view");
const query = new URLSearchParams(location.search);
const state = {
  view: query.get("view") || "overview",
  period: query.get("period") || "2024-04",
  source: query.get("source") || "all",
  plant: query.get("plant") || "PS_001",
  day: query.get("day") || "",
  status: "",
  level: "batch",
  offset: 0,
  run: "",
};
if (!["overview", "reports", "runs", "series"].includes(state.view))
  state.view = "overview";
if (!["all", "public", "synthetic"].includes(state.source))
  state.source = "all";
if (!/^\d{4}-\d{2}$/.test(state.period)) state.period = "2024-04";
let revision = 0;
let controller;
const number = (value, digits = 0) =>
  value === null || value === undefined
    ? "—"
    : Number(value).toLocaleString("ko-KR", { maximumFractionDigits: digits });
const pct = (value) =>
  value === null || value === undefined ? "—" : `${number(value * 100, 1)}%`;
const time = (value) =>
  value
    ? value.replace("T", " ").replace(/\.\d+/, "").replace("+00:00", " UTC")
    : "기록 없음";
const names = {
  overview: "전체 현황",
  reports: "월간 보고서",
  runs: "실행 이력",
  series: "발전소 관측 자료",
};
const statuses = {
  committed: ["완료", "good"],
  failed: ["실패", "bad"],
  running: ["실행 중", "neutral"],
  validated: ["검증 완료", "warn"],
};

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function button(text, action, className = "secondary") {
  const element = node("button", text, className);
  element.type = "button";
  element.onclick = action;
  return element;
}
function link(text, href) {
  const element = node("a", text);
  element.href = href;
  return element;
}
function badge(status) {
  const [label, style] = statuses[status] || [status, "neutral"];
  return node("span", label, `pill ${style}`);
}
function hero(title, subtitle, side) {
  const box = node("div", undefined, "hero"),
    left = node("div");
  left.append(
    node("div", "REVIEW WITH EVIDENCE", "eyebrow"),
    node("h1", title),
    node("p", subtitle),
  );
  box.append(left);
  if (side) box.append(node("div", side, "hero-side"));
  return box;
}
function card(title, value, unit, note, primary = false) {
  const box = node("div", undefined, `card${primary ? " primary" : ""}`);
  const valueNode = node("div", value, "card-value");
  if (unit) valueNode.append(node("small", unit));
  box.append(
    node("div", title, "card-label"),
    valueNode,
    node("div", note, "card-note"),
  );
  return box;
}
function panel(title, subtitle, action) {
  const box = node("section", undefined, "panel"),
    head = node("div", undefined, "panel-head"),
    copy = node("div");
  copy.append(node("h2", title));
  if (subtitle) copy.append(node("p", subtitle));
  head.append(copy);
  if (action) head.append(action);
  box.append(head);
  return box;
}
function table(headers, rows) {
  const wrap = node("div", undefined, "table-wrap"),
    tab = node("table"),
    head = node("thead"),
    tr = node("tr"),
    body = node("tbody");
  for (const title of headers) {
    const th = node("th", title);
    th.scope = "col";
    tr.append(th);
  }
  head.append(tr);
  for (const row of rows) {
    const tr = node("tr");
    for (const value of row) {
      const td = node("td");
      value instanceof Node
        ? td.append(value)
        : (td.textContent = value ?? "—");
      tr.append(td);
    }
    body.append(tr);
  }
  tab.append(head, body);
  wrap.append(tab);
  return wrap;
}
function empty(title, message, action) {
  const box = node("div", undefined, "empty");
  box.append(node("h2", title), node("p", message));
  if (action) box.append(action);
  return box;
}
function select(label, values, value, change) {
  const wrapper = node("label", label),
    input = node("select");
  for (const [key, text] of values) {
    const opt = node("option", text);
    opt.value = key;
    input.append(opt);
  }
  input.setAttribute("aria-label", label);
  input.value = value;
  input.onchange = () => change(input.value);
  wrapper.append(input);
  return wrapper;
}
async function get(path, signal) {
  const response = await fetch(path, { signal });
  if (!response.ok)
    throw new Error(
      response.status === 422
        ? "선택한 월·날짜·필터를 확인해 주세요."
        : `자료를 불러오지 못했습니다 (${response.status}).`,
    );
  return response.json();
}
function navigate(changes) {
  if (changes.view && changes.view !== state.view)
    window.scrollTo({ top: 0, behavior: "instant" });
  Object.assign(state, changes);
  render();
}
function syncURL() {
  const params = new URLSearchParams({
    view: state.view,
    period: state.period,
    source: state.source,
  });
  if (["reports", "series"].includes(state.view))
    params.set("plant", state.plant);
  if (state.view === "series") params.set("day", state.day);
  history.replaceState(null, "", `?${params}`);
}
function svgNode(tag, attrs = {}, text) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([key, value]) =>
    element.setAttribute(key, value),
  );
  if (text !== undefined) element.textContent = text;
  return element;
}
function energyChart(timeline) {
  const svg = svgNode("svg", {
    viewBox: "0 0 800 220",
    class: "chart",
    role: "img",
    "aria-label":
      "일별 추정 발전량. 자료 없는 날은 빈칸으로 표시하며 표에서 발전소별 품질을 확인할 수 있습니다.",
  });
  const max = Math.max(
    1,
    ...timeline.map((d) => d.metrics?.estimated_energy_kwh || 0),
  );
  [0, 0.5, 1].forEach((ratio) => {
    const y = 180 - ratio * 145;
    svg.append(
      svgNode("line", { x1: 58, x2: 790, y1: y, y2: y, class: "grid" }),
      svgNode(
        "text",
        { x: 48, y: y + 4, "text-anchor": "end" },
        number((max * ratio) / 1000, 1),
      ),
    );
  });
  svg.append(svgNode("text", { x: 10, y: 17 }, "MWh (추정)"));
  timeline.forEach((day, index) => {
    const width = 725 / timeline.length,
      x = 60 + index * width;
    if (day.metrics) {
      const h = (day.metrics.estimated_energy_kwh / max) * 145;
      const bar = svgNode("rect", {
        x,
        y: 180 - Math.max(h, 1),
        width: width - 5,
        height: Math.max(h, 1),
        rx: 2,
        fill: h ? "#377858" : "#bccbbb",
      });
      bar.append(
        svgNode(
          "title",
          {},
          `${day.day}: ${number(day.metrics.estimated_energy_kwh, 2)} kWh · ${day.metrics.partition_count}개 발전소`,
        ),
      );
      svg.append(bar);
    } else
      svg.append(
        svgNode("line", {
          x1: x,
          x2: x + width - 5,
          y1: 187,
          y2: 187,
          stroke: "#b1bdb0",
          "stroke-dasharray": "2 2",
        }),
      );
    if (index % 5 === 0 || index === timeline.length - 1)
      svg.append(
        svgNode(
          "text",
          { x: x + width / 2, y: 208, "text-anchor": "middle" },
          day.day.slice(8),
        ),
      );
  });
  return svg;
}
function legend(items) {
  const box = node("div", undefined, "legend");
  for (const [text, color] of items) {
    const item = node("span", text);
    item.style.setProperty("--color", color);
    box.append(item);
  }
  return box;
}

async function overview(signal) {
  const suffix = state.source === "all" ? "" : `&source_kind=${state.source}`;
  const data = await get(
    `/api/v1/overview?period=${encodeURIComponent(state.period)}${suffix}`,
    signal,
  );
  const root = node("div"),
    sum = data.summary;
  root.append(
    hero(
      "월별 데이터 현황",
      "어떤 자료를 믿고, 어디를 먼저 살펴볼지 확인하세요.",
      `${state.period} / ${data.timezone}\n현재 계산 버전의 활성 파티션`,
    ),
  );
  if (!sum.plant_count) {
    root.append(
      empty(
        "선택한 기간의 자료가 없습니다",
        "보고 월이나 자료 구분을 바꿔 확인해 주세요. 데이터 없는 기간은 0 발전량으로 처리하지 않습니다.",
        button("합성 데모 기간 보기", () =>
          navigate({ period: "2024-04", source: "synthetic" }),
        ),
      ),
    );
    return root;
  }
  const cards = node("div", undefined, "cards");
  cards.append(
    card(
      "추정 발전량",
      number(sum.estimated_energy_kwh / 1000, 2),
      "MWh",
      "관측된 유효 전력 × 0.25h",
      true,
    ),
    card(
      "유효값 비율",
      pct(sum.valid_coverage_ratio),
      "",
      `관측 슬롯 완전성 ${pct(sum.coverage_ratio)}`,
    ),
    card(
      "누락 / 무효 슬롯",
      `${number(sum.missing_slots)} / ${number(sum.invalid_slots)}`,
      "",
      "누락과 관측된 무효값을 구분",
    ),
    card(
      "조회된 발전소",
      number(sum.plant_count),
      "개",
      `월 전체 파티션 확보 ${sum.complete_plants}개`,
    ),
  );
  root.append(cards);
  const split = node("div", undefined, "split"),
    trend = panel(
      "일별 추정 발전량",
      "각 날짜에 자료가 있는 발전소의 합계 · 발전소 수가 다를 수 있습니다.",
    );
  trend.append(
    energyChart(data.timeline),
    legend([
      ["자료 있음", "#377858"],
      ["자료 없음은 빈칸", "#b1bdb0"],
    ]),
  );
  const quality = panel("자료를 읽는 세 가지 기준", "인버터 관측 슬롯 기준");
  const track = node("div", undefined, "quality-track");
  const total = sum.valid_slots + sum.invalid_slots + sum.missing_slots;
  [
    [sum.valid_slots, "valid"],
    [sum.invalid_slots, "invalid"],
    [sum.missing_slots, "missing"],
  ].forEach(([v, name]) => {
    const part = node("span", undefined, `quality-${name}`);
    part.style.width = `${total ? (v / total) * 100 : 0}%`;
    track.append(part);
  });
  const qualityRows = node("div", undefined, "quality-rows");
  [
    ["유효한 관측", sum.valid_slots],
    ["무효값 · 계산 제외", sum.invalid_slots],
    ["누락 · 채우지 않음", sum.missing_slots],
  ].forEach(([label, value]) => {
    const row = node("div");
    row.append(node("span", label), node("b", number(value)));
    qualityRows.append(row);
  });
  quality.append(
    track,
    qualityRows,
    node(
      "p",
      `보간 표시 ${pct(sum.source_interpolation_ratio)} · 보간 여부 불명 ${number(sum.interpolation_unknown_slots)}슬롯. 보간 여부는 유효/무효 분류와 별도 속성입니다.`,
      "quality-note",
    ),
  );
  split.append(trend, quality);
  root.append(split);
  const search = node("input", undefined, "search");
  search.type = "search";
  search.placeholder = "발전소 ID 검색";
  search.setAttribute("aria-label", "발전소 ID 검색");
  const list = panel(
    "발전소별 검토 순서",
    "유효값 비율 낮은 순 · 설비 고장 순위가 아닌 자료 품질 확인 순서입니다.",
    search,
  );
  const rows = data.plants.map((plant) => {
    const name = node("div");
    name.append(
      node("strong", plant.plant_id),
      node(
        "span",
        `${plant.source_kinds.includes("public") ? "공개" : "합성"} · ${plant.region} · ${number(plant.capacity_kw)} kW`,
        "small",
      ),
    );
    const dates = node("div", `${plant.partition_count}일`);
    dates.append(
      node("span", plant.period_complete ? "월 전체" : "부분 기간", "small"),
    );
    const actions = node("div", undefined, "inline-actions");
    actions.append(
      button(
        "관측",
        () =>
          navigate({
            view: "series",
            plant: plant.plant_id,
            day: plant.last_day,
          }),
        "text-button",
      ),
      button(
        "보고서",
        () => navigate({ view: "reports", plant: plant.plant_id }),
        "text-button",
      ),
    );
    return [
      name,
      dates,
      number(plant.estimated_energy_kwh / 1000, 2),
      pct(plant.valid_coverage_ratio),
      `${number(plant.missing_slots)} / ${number(plant.invalid_slots)}`,
      pct(plant.source_interpolation_ratio),
      actions,
    ];
  });
  const tableBox = node("div");
  function filter() {
    const filtered = rows.filter((_, i) =>
      data.plants[i].plant_id
        .toLowerCase()
        .includes(search.value.toLowerCase()),
    );
    tableBox.replaceChildren(
      filtered.length
        ? table(
            [
              "발전소",
              "등록 일수",
              "추정 MWh",
              "유효값 비율",
              "누락 / 무효",
              "소스 보간",
              "자세히",
            ],
            filtered,
          )
        : node("p", "일치하는 발전소가 없습니다.", "subtext"),
    );
  }
  search.oninput = filter;
  filter();
  list.append(tableBox);
  root.append(list);
  root.append(
    node(
      "p",
      "관측률 100%가 유효값 100%를 뜻하지 않습니다. 0건의 검토 후보도 고장 없음의 증거가 아닙니다. 판단 가능한 데이터 범위를 먼저 확인하세요.",
      "notice",
    ),
  );
  return root;
}

async function reports(signal) {
  const params = new URLSearchParams({ period: state.period });
  if (state.source !== "all") params.set("source_kind", state.source);
  const data = await get(`/api/v1/reports?${params}`, signal),
    root = node("div");
  const reports = [];
  for (const report of data.items.sort((a, b) =>
    b.generated_at.localeCompare(a.generated_at),
  )) {
    if (report.period !== state.period) continue;
    reports.push(report);
  }
  root.append(
    hero(
      "근거가 남는 월간 보고서",
      "생성 시점의 품질 지표와 원본 계보를 함께 보관합니다.",
    ),
  );
  if (reports.some((report) => report.source_metadata_status === "unavailable"))
    root.append(
      node("p", "일부 보고서의 출처 파일을 읽을 수 없습니다. 운영자가 저장소를 확인해 주세요.", "notice"),
    );
  if (!reports.length) {
    root.append(
      empty(
        "이 기간의 보고서가 없습니다",
        "다른 월을 선택하거나 운영자가 보고서를 생성한 뒤 새로고침해 주세요.",
      ),
    );
    return root;
  }
  if (state.plant && !reports.some((r) => r.scope === state.plant)) {
    root.append(
      empty(
        `${state.plant}의 보고서가 없습니다`,
        "선택한 월·자료 구분에 해당하는 보고서가 아직 생성되지 않았습니다.",
        button("사용 가능한 보고서 보기", () => navigate({ plant: "" })),
      ),
    );
    return root;
  }
  const preferred = reports.find((r) => r.scope === state.plant) || reports[0];
  const frame = node("iframe", undefined, "report-frame");
  frame.title = "월간 보고서";
  const toolbar = node("div", undefined, "filters");
  const downloads = node("div", undefined, "inline-actions");
  function show(id) {
    const report = reports.find((r) => r.report_id === id);
    state.plant = report.scope;
    syncURL();
    frame.src = `/reports/${encodeURIComponent(id)}/report.html`;
    downloads.replaceChildren(
      link("CSV ↗", `/reports/${id}/metrics.csv`),
      link("출처 JSON ↗", `/reports/${id}/manifest.json`),
    );
  }
  toolbar.append(
    select(
      "보고서 선택",
      reports.map((r) => [
        r.report_id,
        `${r.period} · ${r.scope} · ${r.status === "complete" ? "월 전체" : "부분 기간"}`,
      ]),
      preferred.report_id,
      show,
    ),
    downloads,
  );
  show(preferred.report_id);
  root.append(toolbar, frame);
  return root;
}

async function runs(signal) {
  const root = node("div");
  root.append(
    hero(
      "처리 과정을 확인하다",
      "작업과 일별 파티션을 구분하고, 실패 원인과 재실행 기록을 확인합니다.",
    ),
  );
  const filters = node("div", undefined, "filters");
  const reload = (key, value) => navigate({ [key]: value, offset: 0, run: "" });
  filters.append(
    select(
      "실행 단위",
      [
        ["batch", "작업 단위"],
        ["partition", "일별 파티션"],
        ["all", "전체 기록"],
      ],
      state.level,
      (value) => reload("level", value),
    ),
    select(
      "상태",
      [
        ["", "전체 상태"],
        ["committed", "완료"],
        ["failed", "실패"],
        ["running", "실행 중"],
        ["validated", "검증 완료"],
      ],
      state.status,
      (value) => reload("status", value),
    ),
  );
  filters.append(button("새로고침", render));
  root.append(filters);
  const params = new URLSearchParams({
    level: state.level,
    limit: "20",
    offset: String(state.offset),
  });
  if (state.status) params.set("status", state.status);
  const data = await get(`/api/v1/runs?${params}`, signal),
    count = data.status_counts;
  const cards = node("div", undefined, "cards");
  cards.append(
    card(
      "전체 기록",
      number(Object.values(count).reduce((a, b) => a + b, 0)),
      "건",
      "선택한 실행 단위 기준",
      true,
    ),
    card("완료", number(count.committed || 0), "건", "활성 결과 공개 완료"),
    card("실패", number(count.failed || 0), "건", "장애 주입 검증 기록 포함"),
    card(
      "실행 / 공개 대기",
      number((count.running || 0) + (count.validated || 0)),
      "건",
      "프로세스 생존 여부와 다를 수 있음",
    ),
  );
  root.append(cards);
  const list = panel("최근 실행", "완료 또는 마지막 기록 시각의 최신순 · UTC");
  if (!data.items.length)
    list.append(node("p", "선택한 상태의 실행 기록이 없습니다.", "subtext"));
  else
    list.append(
      table(
        [
          "상태",
          "발전소 / 작업",
          "처리 구간",
          "마지막 기록",
          "소요 시간",
          "상세",
        ],
        data.items.map((run) => {
          const name = node("div", run.plant_id || "—");
          name.append(node("span", run.run_id.slice(0, 8), "small"));
          const period =
            run.partition_id || `${run.from || "—"} → ${run.to || "—"}`;
          return [
            badge(run.status),
            name,
            period,
            time(run.updated_at),
            run.elapsed_ms === undefined
              ? "기록 없음"
              : `${number(run.elapsed_ms / 1000, 2)}초`,
            button(
              "상세 보기",
              () => navigate({ run: run.run_id }),
              "text-button",
            ),
          ];
        }),
      ),
    );
  const pagination = node("div", undefined, "pagination"),
    actions = node("div");
  pagination.append(
    node(
      "span",
      `${data.total ? state.offset + 1 : 0}–${Math.min(state.offset + 20, data.total)} / ${number(data.total)}건`,
    ),
  );
  const prev = button("이전", () =>
    navigate({ offset: Math.max(0, state.offset - 20), run: "" }),
  );
  prev.disabled = state.offset === 0;
  const next = button("다음", () =>
    navigate({ offset: state.offset + 20, run: "" }),
  );
  next.disabled = state.offset + 20 >= data.total;
  actions.append(prev, next);
  pagination.append(actions);
  list.append(pagination);
  root.append(list);
  if (state.run) {
    const run = await get(
      `/api/v1/runs/${encodeURIComponent(state.run)}`,
      signal,
    );
    const detail = panel(
      "선택한 실행의 근거",
      run.run_id,
      link("API JSON ↗", `/api/v1/runs/${run.run_id}`),
    );
    detail.id = "run-detail";
    detail.tabIndex = -1;
    const grid = node("div", undefined, "detail-grid");
    [
      ["상태", statuses[run.status]?.[0] || run.status],
      ["입력 버전", run.source_version || "이전 기록에 없음"],
      ["시작", time(run.started_at)],
      ["종료", time(run.finished_at)],
      ["처리 행", number(run.rows)],
      ["오류 코드", run.error_code || "없음"],
    ].forEach(([label, value]) => {
      const item = node("div", value);
      item.prepend(node("span", label));
      grid.append(item);
    });
    detail.append(grid);
    if (run.error_code)
      detail.append(
        node(
          "p",
          run.error_code.startsWith("INJECTED")
            ? "복구 동작을 확인하기 위해 의도적으로 주입한 실패입니다. 이후 성공 기록과 활성 결과를 함께 확인하세요."
            : "실패한 파티션은 이전 활성 결과를 유지합니다. 앞서 완료된 날짜가 있을 수 있으므로 하위 기록을 확인하세요.",
          "notice",
        ),
      );
    if (run.partitions.length)
      detail.append(
        table(
          ["날짜", "상태", "행", "오류"],
          run.partitions.map((row) => [
            row.partition_id,
            badge(row.status),
            number(row.rows),
            row.error_code || "—",
          ]),
        ),
      );
    else if (run.kind === "ingest")
      detail.append(
        node(
          "p",
          "이전 버전 기록에는 하위 파티션 연결이 없을 수 있습니다.",
          "subtext",
        ),
      );
    root.append(detail);
  }
  return root;
}

async function series(signal) {
  const root = node("div");
  root.append(
    hero(
      `${state.plant} · 관측 자료`,
      "전력과 POA는 서로 다른 단위입니다. 좌우 축을 함께 확인하세요.",
      "UTC / 15분 자료",
    ),
  );
  const filters = node("div", undefined, "filters"),
    label = node("label", "관측 날짜"),
    input = node("input");
  input.type = "date";
  input.value = state.day;
  input.required = true;
  input.onchange = () => {
    if (input.reportValidity()) navigate({ day: input.value });
  };
  label.append(input);
  filters.append(
    label,
    button("전체 현황으로", () => navigate({ view: "overview" })),
  );
  root.append(filters);
  const data = await get(
    `/api/v1/plants/${encodeURIComponent(state.plant)}/series?day=${encodeURIComponent(state.day)}`,
    signal,
  );
  if (!data.items.length) {
    root.append(
      empty(
        "선택한 날짜의 자료가 없습니다",
        "관측되지 않은 기간을 발전량 0으로 해석하지 않습니다.",
      ),
    );
    return root;
  }
  const box = panel(
    "관측 전력과 일사량",
    "빈 관측값은 선으로 연결하지 않습니다. 판단 불가 상태는 원본 품질을 함께 확인하세요.",
  );
  const svg = svgNode("svg", {
    viewBox: "0 0 1000 280",
    class: "chart",
    role: "img",
    "aria-label":
      "왼쪽 전력 kW, 오른쪽 POA W/m². 정확한 값과 데이터 판단은 아래 표에 있습니다.",
  });
  const items = data.items;
  for (const [key, color, side, unit] of [
    ["power_kw", "#236f50", "left", "kW"],
    ["poa_wm2", "#b47d20", "right", "W/m²"],
  ]) {
    const max = Math.max(1, ...items.map((row) => row[key] ?? 0));
    [0, 0.5, 1].forEach((ratio) => {
      const y = 225 - ratio * 180;
      if (side === "left")
        svg.append(
          svgNode("line", { x1: 70, x2: 920, y1: y, y2: y, class: "grid" }),
        );
      svg.append(
        svgNode(
          "text",
          {
            x: side === "left" ? 58 : 932,
            y: y + 4,
            "text-anchor": side === "left" ? "end" : "start",
          },
          number(max * ratio, 1),
        ),
      );
    });
    svg.append(svgNode("text", { x: side === "left" ? 25 : 932, y: 20 }, unit));
    let points = [];
    const draw = () => {
      if (points.length)
        svg.append(
          svgNode("polyline", {
            points: points.join(" "),
            stroke: color,
            "stroke-width": 2,
            fill: "none",
          }),
        );
      points = [];
    };
    items.forEach((row, index) => {
      if (row[key] === null) {
        draw();
        return;
      }
      points.push(
        `${70 + (index * 850) / Math.max(1, items.length - 1)},${225 - (row[key] / max) * 180}`,
      );
    });
    draw();
  }
  [0, Math.floor(items.length / 2), items.length - 1].forEach((index) =>
    svg.append(
      svgNode(
        "text",
        {
          x: 70 + (index * 850) / Math.max(1, items.length - 1),
          y: 255,
          "text-anchor": "middle",
        },
        items[index].ts_utc.slice(11, 16),
      ),
    ),
  );
  box.append(
    svg,
    legend([
      ["전력 · 왼쪽 kW", "#236f50"],
      ["POA · 오른쪽 W/m²", "#b47d20"],
    ]),
  );
  root.append(box);
  const records = panel(
    "관측값과 판단 가능 범위",
    "발전량은 근사치이며 저출력 표시는 사람이 확인할 검토 후보입니다.",
  );
  const labels = {
    normal: "규칙상 일반",
    INSUFFICIENT_DATA: "판단 불가",
    review_candidate: "검토 후보",
  };
  records.append(
    table(
      ["시각 (UTC)", "전력 kW", "POA W/m²", "데이터 판단"],
      items.map((row) => [
        row.ts_utc.slice(11, 16),
        number(row.power_kw, 2),
        number(row.poa_wm2, 1),
        node(
          "span",
          labels[row.assessment] || row.assessment,
          `pill ${row.assessment === "normal" ? "good" : "warn"}`,
        ),
      ]),
    ),
  );
  root.append(records);
  return root;
}

async function render() {
  const ticket = ++revision;
  controller?.abort();
  controller = new AbortController();
  const currentController = controller;
  const timeout = setTimeout(() => currentController.abort(), 20000);
  syncURL();
  $("#period").value = state.period;
  $("#source").value = state.source;
  $("#scope-controls").hidden =
    state.view === "runs" || state.view === "series";
  $("#breadcrumb").textContent = names[state.view];
  document
    .querySelectorAll("nav button")
    .forEach((b) =>
      b.setAttribute(
        "aria-current",
        b.dataset.view === state.view ||
          (state.view === "series" && b.dataset.view === "overview")
          ? "page"
          : "false",
      ),
    );
  view.setAttribute("aria-busy", "true");
  view.replaceChildren(node("div", "자료를 확인하고 있습니다…", "loading"));
  try {
    const content = await { overview, reports, runs, series }[state.view](
      currentController.signal,
    );
    if (ticket === revision) {
      view.replaceChildren(content);
      if (state.view === "runs" && state.run) {
        $("#run-detail")?.scrollIntoView({ block: "start" });
        $("#run-detail")?.focus({ preventScroll: true });
      }
    }
  } catch (error) {
    if (ticket !== revision) return;
    const box = empty(
      "자료를 불러오지 못했습니다",
      error.name === "AbortError"
        ? "응답 시간이 길어졌습니다. 잠시 후 다시 시도해 주세요."
        : error.message,
      button("다시 시도", render),
    );
    box.className = "error";
    view.replaceChildren(box);
  } finally {
    clearTimeout(timeout);
    if (ticket === revision) view.setAttribute("aria-busy", "false");
  }
}

document
  .querySelectorAll("nav button")
  .forEach(
    (b) => (b.onclick = () => navigate({ view: b.dataset.view, run: "" })),
  );
$("#period").onchange = () => {
  if ($("#period").reportValidity()) navigate({ period: $("#period").value });
};
$("#source").onchange = () => navigate({ source: $("#source").value });
$("#refresh").onclick = render;
get("/health")
  .then((data) => {
    $("#version").textContent = `v${data.version || ""}`;
  })
  .catch(() => {});
render();
