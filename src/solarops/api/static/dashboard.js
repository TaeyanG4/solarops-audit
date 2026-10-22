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
  review: query.get("review") || "all",
  search: query.get("search") || "",
};
if (!["all", "partial", "invalid", "missing"].includes(state.review))
  state.review = "all";
if (
  ![
    "overview",
    "plants",
    "quality",
    "sources",
    "system",
    "reports",
    "runs",
    "series",
  ].includes(state.view)
)
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
const mwh = (value) =>
  value == null ? "추정값 없음" : number(value / 1000, 2);
const time = (value) =>
  value
    ? value.replace("T", " ").replace(/\.\d+/, "").replace("+00:00", " UTC")
    : "기록 없음";
const names = {
  overview: "전체 현황",
  plants: "발전소",
  quality: "데이터 품질",
  sources: "데이터 출처",
  system: "시스템 관리",
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
function workspaceURL(changes = {}) {
  const next = { ...state, ...changes };
  const params = new URLSearchParams({
    view: next.view,
    period: next.period,
    source: next.source,
  });
  if (["reports", "series"].includes(next.view))
    params.set("plant", next.plant);
  if (next.view === "series") params.set("day", next.day);
  if (["overview", "plants"].includes(next.view)) {
    if (next.review !== "all") params.set("review", next.review);
    if (next.search) params.set("search", next.search);
  }
  return `?${params}`;
}
function workspaceLink(text, changes, className) {
  const element = link(text, workspaceURL(changes));
  element.className = className;
  return element;
}
function badge(status) {
  const [label, style] = statuses[status] || [status, "neutral"];
  return node("span", label, `pill ${style}`);
}
function hero(title, subtitle, side) {
  const box = node("div", undefined, "hero"),
    left = node("div");
  left.append(node("h1", title), node("p", subtitle));
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
function table(headers, rows, className = "") {
  const wrap = node("div", undefined, "table-wrap"),
    tab = node("table", undefined, className),
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
    for (const [index, value] of row.entries()) {
      const td = node("td");
      td.dataset.label = headers[index];
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
  history.replaceState(null, "", workspaceURL());
  document.querySelectorAll("nav a").forEach((item) => {
    item.href = workspaceURL({ view: item.dataset.view });
  });
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
  const box = node("div", undefined, "energy-chart");
  if (!timeline.length) return node("p", "일별 자료가 없습니다.", "subtext");
  const hasEnergy = (day) =>
    day.metrics?.estimated_energy_kwh !== null &&
    day.metrics?.estimated_energy_kwh !== undefined;
  const max = Math.max(
    1,
    ...timeline.map((d) => d.metrics?.estimated_energy_kwh ?? 0),
  );
  const unit = node("p", "MWh · 추정", "chart-unit");
  const plot = node("div", undefined, "energy-plot"),
    axis = node("div", undefined, "chart-axis"),
    canvas = node("div", undefined, "chart-canvas");
  [1, 0.5, 0].forEach((ratio) =>
    axis.append(node("span", number((max * ratio) / 1000, 1))),
  );
  const svg = svgNode("svg", {
    viewBox: "0 0 720 200",
    preserveAspectRatio: "none",
    class: "energy-svg",
    role: "group",
    "aria-label":
      "일별 추정 발전량. 좌우 방향키로 날짜 이동. 아래 날짜 선택과 수치 표로도 확인할 수 있습니다.",
  });
  [8, 98, 188].forEach((y) =>
    svg.append(
      svgNode("line", { x1: 0, x2: 720, y1: y, y2: y, class: "grid" }),
    ),
  );
  const days = node("div", undefined, "chart-days");
  [0, 5, 10, 15, 20, 25, timeline.length - 1]
    .filter((i, n, arr) => i < timeline.length && arr.indexOf(i) === n)
    .forEach((i) => days.append(node("span", `${timeline[i].day.slice(8)}일`)));
  const inspector = node("div", undefined, "day-inspector");
  inspector.setAttribute("aria-live", "polite");
  inspector.setAttribute("aria-atomic", "true");
  const controls = node("div", undefined, "chart-controls");
  const dateLabel = select(
    "상세 날짜",
    timeline.map((d, i) => [String(i), d.day]),
    "0",
    (value) => show(Number(value)),
  );
  const previous = button(
    "이전",
    () => show(selected - 1),
    "secondary chart-step",
  );
  const next = button("다음", () => show(selected + 1), "secondary chart-step");
  previous.setAttribute("aria-label", "이전 날짜");
  next.setAttribute("aria-label", "다음 날짜");
  controls.append(dateLabel, previous, next);
  let selected = 0;
  const marks = [];
  function description(day) {
    return hasEnergy(day)
      ? `${day.day} · 추정 ${number(day.metrics.estimated_energy_kwh, 2)} kWh · ${day.metrics.partition_count}개 발전소`
      : `${day.day} · ${day.metrics ? "추정값 없음" : "자료 없음"} · 0 발전량이 아닙니다`;
  }
  function show(index) {
    selected = Math.max(0, Math.min(timeline.length - 1, index));
    const day = timeline[selected];
    dateLabel.querySelector("select").value = String(selected);
    window.syncWorkspaceControls?.();
    previous.disabled = selected === 0;
    next.disabled = selected === timeline.length - 1;
    marks.forEach((mark, i) => {
      mark.setAttribute("tabindex", i === selected ? "0" : "-1");
      mark.setAttribute("aria-pressed", String(i === selected));
    });
    inspector.replaceChildren(
      node(
        "strong",
        hasEnergy(day)
          ? `${number(day.metrics.estimated_energy_kwh / 1000, 2)} MWh`
          : day.metrics
            ? "추정값 없음"
            : "자료 없음",
      ),
      node(
        "span",
        hasEnergy(day)
          ? `${day.day} · 추정 · ${day.metrics.partition_count}개 발전소 합계`
          : `${day.day} · 0 발전량으로 처리하지 않음`,
      ),
    );
  }
  timeline.forEach((day, index) => {
    const width = 720 / timeline.length,
      x = index * width;
    const mark = svgNode("g", {
      role: "button",
      "aria-label": description(day),
      class: "day-mark",
    });
    mark.append(
      svgNode("rect", { x, y: 0, width, height: 200, class: "day-hit" }),
    );
    if (hasEnergy(day)) {
      const height = Math.max(
        1,
        (day.metrics.estimated_energy_kwh / max) * 180,
      );
      mark.append(
        svgNode("rect", {
          x: x + 3,
          y: 188 - height,
          width: Math.max(1, width - 6),
          height,
          rx: 2,
          class: "energy-bar",
        }),
      );
    } else if (day.metrics) {
      mark.append(
        svgNode("circle", {
          cx: x + width / 2,
          cy: 188,
          r: 3,
          class: "unknown-mark",
        }),
      );
    } else {
      mark.append(
        svgNode("line", {
          x1: x + 3,
          x2: x + width - 3,
          y1: 188,
          y2: 188,
          class: "missing-mark",
        }),
      );
    }
    mark.addEventListener("pointerenter", (event) => {
      if (event.pointerType === "mouse") show(index);
    });
    mark.addEventListener("click", () => show(index));
    mark.addEventListener("focus", () => show(index));
    mark.addEventListener("keydown", (event) => {
      const destinations = {
        ArrowRight: index + 1,
        ArrowLeft: index - 1,
        Home: 0,
        End: timeline.length - 1,
      };
      if (event.key in destinations) {
        event.preventDefault();
        show(destinations[event.key]);
        marks[selected].focus();
      } else if (["Enter", " "].includes(event.key)) {
        event.preventDefault();
        show(index);
      }
    });
    marks.push(mark);
    svg.append(mark);
  });
  canvas.append(svg, days);
  plot.append(axis, canvas);
  show(0);
  const details = node("details", undefined, "chart-data");
  details.append(
    node("summary", "일별 수치 표 보기"),
    table(
      ["날짜 (UTC)", "추정 kWh", "발전소 수"],
      timeline.map((day) => [
        day.day,
        day.metrics
          ? day.metrics.estimated_energy_kwh == null
            ? "추정값 없음"
            : number(day.metrics.estimated_energy_kwh, 2)
          : "자료 없음",
        day.metrics ? number(day.metrics.partition_count) : "—",
      ]),
    ),
  );
  box.append(
    unit,
    plot,
    legend([
      ["추정 발전량", "var(--green)"],
      ["점선: 자료 없음", "var(--missing)"],
      ["빈 원: 추정값 없음", "var(--missing)"],
    ]),
    controls,
    inspector,
    details,
  );
  return box;
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

async function overview(signal, mode = "overview") {
  const suffix = state.source === "all" ? "" : `&source_kind=${state.source}`;
  const data = await get(
    `/api/v1/overview?period=${encodeURIComponent(state.period)}${suffix}`,
    signal,
  );
  const root = node("div", undefined, "overview"),
    sum = data.summary;
  root.append(
    hero(
      mode === "plants"
        ? "발전소 탐색"
        : mode === "quality"
          ? "데이터 품질 검토"
          : "월간 에너지 분석",
      mode === "plants"
        ? "발전소별 자료 범위를 확인하고 일별 관측과 월간 보고서로 이동하세요."
        : mode === "quality"
          ? "유효·무효·누락을 구분하고, 원본 보간은 별도의 속성으로 확인하세요."
          : "발전량의 흐름을 읽고, 데이터 품질을 확인해 검토 대상을 선택하세요.",
      `${state.period} · ${data.timezone} 기준`,
    ),
  );
  if (sum.plant_count) {
    const scope = node("div", undefined, "scope-summary");
    for (const [label, value] of [
      ["조회된 발전소", `${sum.plant_count}개`],
      ["월 전체 자료 확보", `${sum.complete_plants}개`],
    ]) {
      const item = node("span");
      item.append(node("b", value), node("span", label));
      scope.append(item);
    }
    root.querySelector(".hero-side").replaceChildren(scope);
  }
  const provenance = node("section", undefined, "provenance");
  provenance.setAttribute("aria-label", "자료 출처와 해석");
  const sourceCopy = node("div", undefined, "provenance-copy");
  const kinds = new Set(data.plants.flatMap((plant) => plant.source_kinds));
  const includesPublic = kinds.has("public"),
    includesDemo = kinds.has("synthetic");
  sourceCopy.append(
    node(
      "h2",
      includesPublic
        ? includesDemo
          ? "공개 자료와 합성 데모를 함께 조회 중"
          : "BR-PVGen 공개 역사 자료"
        : includesDemo
          ? "합성 시나리오 · 시연용 자료"
          : "선택한 범위에 등록된 자료 없음",
    ),
    node(
      "p",
      includesPublic
        ? "브라질 발전소 · 15분 집계 · 원본 보간 포함. 에너지는 유효 전력으로 계산한 추정치입니다."
        : includesDemo
          ? "프로젝트에서 생성한 시연용 데이터입니다. 실제 발전소의 운영 실적으로 해석하지 않습니다."
          : "보고 월이나 자료 구분을 바꾸어 등록된 자료를 확인하세요.",
    ),
  );
  provenance.append(sourceCopy);
  if (includesPublic) {
    const attribution = node("div", undefined, "source-attribution");
    const sourceLink = link(
      "원본 출처 · Zenodo",
      "https://zenodo.org/records/21511487",
    );
    sourceLink.target = "_blank";
    sourceLink.rel = "noopener noreferrer";
    sourceLink.setAttribute(
      "aria-label",
      "BR-PVGen 원본 출처 · Zenodo (새 탭)",
    );
    attribution.append(sourceLink, node("span", "CC BY 4.0 · Jesus 외"));
    provenance.append(attribution);
  }
  root.append(provenance);
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
  const energySummary = card(
    "추정 발전량",
    mwh(sum.estimated_energy_kwh),
    sum.estimated_energy_kwh == null ? "" : "MWh",
    "유효 전력 × 0.25h · 원본 보간 포함 가능",
    true,
  );
  energySummary.classList.add("energy-summary");
  const split = node("div", undefined, "split"),
    trend = panel(
      "발전량 흐름",
      `${state.period} · UTC · 날짜별 포함 발전소 수가 다를 수 있습니다.`,
    );
  trend.classList.add("trend-panel");
  trend.append(energySummary, energyChart(data.timeline));
  const quality = panel("데이터 품질", "등록된 일별 파티션의 예상 슬롯 기준");
  quality.classList.add("quality-panel");
  const qualityTotal = node("div", undefined, "quality-total");
  qualityTotal.append(
    node("strong", pct(sum.valid_coverage_ratio)),
    node("span", "유효값 비율"),
  );
  quality.append(qualityTotal);
  const track = node("div", undefined, "quality-track");
  track.setAttribute("aria-hidden", "true");
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
    ["유효값", sum.valid_slots, "valid"],
    ["무효값 · 계산 제외", sum.invalid_slots, "invalid"],
    ["누락 · 채우지 않음", sum.missing_slots, "missing"],
  ].forEach(([label, value, kind]) => {
    const row = node("div", undefined, `quality-row ${kind}`);
    row.append(node("span", label), node("b", number(value)));
    qualityRows.append(row);
  });
  quality.append(
    track,
    qualityRows,
    node(
      "p",
      `관측 슬롯 완전성 ${pct(sum.coverage_ratio)}. 미등록 일자는 비율에 포함되지 않습니다. 발전소별 등록 일수를 함께 확인하세요.`,
      "quality-note",
    ),
  );
  const interpolation = node("div", undefined, "interpolation-note");
  interpolation.append(
    node("strong", `원본 보간 표시 ${pct(sum.source_interpolation_ratio)}`),
    node(
      "p",
      `보간 여부 불명 ${number(sum.interpolation_unknown_slots)}슬롯. 유효·무효와 별도 속성으로, 보간된 값도 유효값에 포함될 수 있습니다.`,
    ),
  );
  quality.append(interpolation);
  split.append(trend, quality);
  if (mode === "overview") root.append(split);
  if (mode === "quality") {
    root.append(quality);
    const detail = panel(
      "발전소별 품질 근거",
      "등록된 일별 파티션 기준 · 부분 기간의 높은 관측률을 월 전체 확보로 해석하지 않습니다.",
    );
    detail.append(
      table(
        [
          "발전소",
          "등록 일수",
          "유효 슬롯",
          "무효 슬롯",
          "누락 슬롯",
          "원본 보간",
          "근거 확인",
        ],
        data.plants.map((plant) => [
          plant.plant_id,
          `${plant.partition_count}일 · ${plant.period_complete ? "월 전체" : "부분 기간"}`,
          number(plant.valid_slots),
          number(plant.invalid_slots),
          number(plant.missing_slots),
          pct(plant.source_interpolation_ratio),
          workspaceLink(
            `${plant.plant_id} 관측`,
            { view: "series", plant: plant.plant_id, day: plant.last_day },
            "text-button",
          ),
        ]),
        "quality-table",
      ),
    );
    root.append(detail);
    const definitions = panel(
      "품질 지표 읽는 법",
      "설비 고장이나 경제적 손실을 확정하는 지표가 아닙니다.",
    );
    definitions.append(
      definitionList([
        [
          "유효값",
          "계산 조건을 통과한 전력 슬롯입니다. 원본에서 보간된 값도 포함될 수 있습니다.",
        ],
        [
          "무효값",
          "범위·품질 검사에서 제외된 슬롯입니다. 추정 에너지 계산에 사용하지 않습니다.",
        ],
        [
          "누락",
          "등록된 일자의 예상 슬롯 중 관측이 없는 슬롯입니다. 0이나 보간값으로 채우지 않습니다.",
        ],
        [
          "원본 보간",
          "제공자가 보간했다고 표시한 별도 속성입니다. 유효·무효·누락과 합산하지 않습니다.",
        ],
        [
          "부분 기간",
          "월의 일부 일자만 등록된 상태입니다. 미등록 일자는 슬롯 완전성의 분모에 포함되지 않습니다.",
        ],
      ]),
    );
    root.append(definitions);
    return root;
  }
  const search = node("input", undefined, "search");
  search.type = "search";
  search.name = "plant-search";
  search.autocomplete = "off";
  search.spellcheck = false;
  search.placeholder = "예: PS_001…";
  search.value = state.search;
  const searchLabel = node("label", "발전소 ID 검색", "plant-search");
  searchLabel.append(search);
  const list = panel(
    "발전소별 검토 순서",
    "유효값 비율 낮은 순 · 설비 고장 순위가 아닌 자료 품질 확인 순서입니다.",
  );
  list.classList.add("plant-panel");
  const predicates = {
    all: () => true,
    partial: (plant) => !plant.period_complete,
    invalid: (plant) => plant.invalid_slots > 0,
    missing: (plant) => plant.missing_slots > 0,
  };
  const filters = node("div", undefined, "review-filters");
  filters.setAttribute("role", "group");
  filters.setAttribute("aria-label", "검토할 자료 범위");
  for (const [key, label] of [
    ["all", "전체"],
    ["partial", "부분 기간"],
    ["invalid", "무효값 있음"],
    ["missing", "누락 있음"],
  ]) {
    const control = button(
      `${label} ${data.plants.filter(predicates[key]).length}`,
      () => {
        state.review = key;
        filter();
      },
      "review-filter",
    );
    control.dataset.review = key;
    filters.append(control);
  }
  const clear = button(
    "필터 초기화",
    () => {
      state.review = "all";
      search.value = "";
      filter();
      search.focus();
    },
    "text-button filter-reset",
  );
  const tools = node("div", undefined, "plant-tools");
  tools.append(filters, searchLabel);
  list.append(tools);
  const rows = data.plants.map((plant) => {
    const name = node("div");
    name.append(
      node("strong", plant.plant_id),
      node(
        "span",
        `${plant.source_kinds.map((kind) => (kind === "public" ? "공개" : "합성")).join(" / ")} · ${plant.region} · ${number(plant.capacity_kw)} kW`,
        "small",
      ),
    );
    const dates = node("div", `${plant.partition_count}일`);
    dates.append(
      node(
        "span",
        plant.period_complete ? "월 전체" : "부분 기간",
        `small period-state${plant.period_complete ? "" : " partial"}`,
      ),
    );
    const actions = node("div", undefined, "inline-actions");
    actions.append(
      workspaceLink(
        "관측",
        {
          view: "series",
          plant: plant.plant_id,
          day: plant.last_day,
        },
        "text-button",
      ),
      workspaceLink(
        "보고서",
        { view: "reports", plant: plant.plant_id },
        "text-button",
      ),
    );
    actions
      .querySelectorAll("a")
      .forEach((action) =>
        action.setAttribute(
          "aria-label",
          `${plant.plant_id} ${action.textContent} 보기`,
        ),
      );
    const valid = node("div", undefined, "coverage-cell");
    const meter = node("span", undefined, "coverage-meter");
    meter.setAttribute("aria-hidden", "true");
    const fill = node("span");
    fill.style.width = `${(plant.valid_coverage_ratio ?? 0) * 100}%`;
    meter.append(fill);
    valid.append(node("strong", pct(plant.valid_coverage_ratio)), meter);
    return [
      name,
      dates,
      mwh(plant.estimated_energy_kwh),
      valid,
      `${number(plant.missing_slots)} / ${number(plant.invalid_slots)}`,
      pct(plant.source_interpolation_ratio),
      actions,
    ];
  });
  const tableBox = node("div");
  const resultCount = node("p", "", "result-count");
  resultCount.setAttribute("role", "status");
  function filter() {
    state.search = search.value;
    syncURL();
    filters.querySelectorAll("button").forEach((control) => {
      control.setAttribute(
        "aria-pressed",
        String(control.dataset.review === state.review),
      );
    });
    clear.hidden = state.review === "all" && !search.value;
    const filtered = rows.filter(
      (_, i) =>
        predicates[state.review](data.plants[i]) &&
        data.plants[i].plant_id
          .toLowerCase()
          .includes(search.value.trim().toLowerCase()),
    );
    resultCount.textContent = `${filtered.length} / ${data.plants.length}개 발전소 · 유효값 비율 오름차순`;
    tableBox.replaceChildren(
      filtered.length
        ? table(
            [
              "발전소",
              "등록 일수",
              "추정 MWh",
              "유효값 비율",
              "누락 / 무효",
              "원본 보간",
              "자세히",
            ],
            filtered,
            "plant-table",
          )
        : node(
            "p",
            "일치하는 발전소가 없습니다. 검토 범위나 검색어를 바꾸거나 필터를 초기화하세요.",
            "filter-empty",
          ),
    );
  }
  search.oninput = filter;
  filter();
  const results = node("div", undefined, "plant-results");
  results.append(resultCount, clear);
  list.append(results, tableBox);
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
      node(
        "p",
        "일부 보고서의 출처 파일을 읽을 수 없습니다. 운영자가 저장소를 확인해 주세요.",
        "notice",
      ),
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
  const toolbar = node("div", undefined, "filters");
  const downloads = node("div", undefined, "inline-actions");
  const id = encodeURIComponent(preferred.report_id);
  state.plant = preferred.scope;
  syncURL();
  const printLink = link("인쇄용 보고서 (새 탭)", `/reports/${id}/report.html`);
  printLink.target = "_blank";
  printLink.rel = "noopener";
  downloads.append(
    link("CSV 다운로드", `/reports/${id}/metrics.csv`),
    link("출처 JSON", `/reports/${id}/manifest.json`),
    printLink,
  );
  toolbar.append(
    select(
      "보고서 선택",
      reports.map((r) => [
        r.report_id,
        `${r.period} · ${r.scope} · ${r.status === "complete" ? "월 전체" : "부분 기간"}`,
      ]),
      preferred.report_id,
      (id) =>
        navigate({ plant: reports.find((r) => r.report_id === id).scope }),
    ),
    downloads,
  );
  const manifest = await get(`/reports/${id}/manifest.json`, signal);
  root.append(toolbar, reportDocument(manifest));
  return root;
}

function reportDocument(report) {
  const sheet = node("article", undefined, "report-sheet");
  sheet.setAttribute(
    "aria-label",
    `${report.period} ${report.scope} 월간 보고서`,
  );
  const band = node("section", undefined, "report-band"),
    title = node("div"),
    energy = node("div", undefined, "report-energy");
  title.append(
    node("h2", `${report.period} · ${report.scope}`),
    node(
      "p",
      `${report.plant_count}개 발전소 · ${report.days}개 일별 파티션 · ${report.timezone}`,
    ),
    node(
      "span",
      report.status === "complete" ? "월 전체 파티션 확보" : "부분 기간 보고서",
      "report-tag",
    ),
  );
  energy.append(
    node("p", "추정 발전량"),
    node("strong", number(report.estimated_energy_kwh, 2)),
    node("span", "kWh"),
    node("p", "유효 전력 × 0.25h · 계량기 실측 전력량과 다릅니다."),
  );
  band.append(title, energy);
  sheet.append(band);
  const provenance = node(
    "p",
    report.synthetic
      ? report.public
        ? "공개 자료와 합성 데모를 함께 포함한 보고서입니다. 실제 발전소 실적으로 합산해 해석하지 않습니다."
        : "합성 데모 보고서입니다. 실제 발전소의 운영 실적을 나타내지 않습니다."
      : "BR-PVGen 공개 역사 자료 · 원본 보간 포함 · CC BY 4.0. 실시간 계측 자료가 아닙니다.",
    "report-provenance",
  );
  sheet.append(provenance);
  const metrics = node("dl", undefined, "report-metrics");
  for (const [label, value, description] of [
    ["관측 슬롯 완전성", pct(report.coverage), "등록된 일별 파티션 기준"],
    [
      "유효값 비율",
      pct(report.valid_coverage),
      "무효값은 추정 에너지 계산에서 제외",
    ],
    [
      "원본 보간 표시",
      report.interpolation == null
        ? "알 수 없음"
        : `${number(report.interpolation * 100, 2)}%`,
      "유효·무효와 겹칠 수 있는 별도 속성",
    ],
    [
      "저출력 검토 구간",
      `${number(report.candidates.length)}건`,
      "사람이 확인할 후보 · 고장 확정 아님",
    ],
  ]) {
    const metric = node("div");
    const detail = node("dd", value);
    detail.append(node("p", description));
    metric.append(node("dt", label), detail);
    metrics.append(metric);
  }
  sheet.append(metrics);
  const daily = panel(
    "일별 데이터 내역",
    "추정 발전량과 품질을 함께 확인하세요. 원본 보간 여부 불명은 0%로 표시하지 않습니다.",
  );
  daily.classList.add("report-section");
  const dailyDetails = node("details", undefined, "report-daily-details");
  dailyDetails.append(
    node("summary", `일별 내역 ${number(report.metrics.length)}건 보기`),
  );
  dailyDetails.append(
    table(
      [
        "발전소 / 날짜",
        "추정 kWh",
        "관측 / 기대 슬롯",
        "누락 / 무효",
        "원본 보간",
        "검토 구간",
      ],
      report.metrics.map((m) => [
        `${m.plant_id} · ${m.local_date}`,
        number(m.estimated_energy_kwh, 2),
        `${number(m.observed_slots)} / ${number(m.expected_slots)}`,
        `${number(m.missing_slots)} / ${number(m.invalid_slots)}`,
        m.source_interpolation_ratio == null
          ? "알 수 없음"
          : pct(m.source_interpolation_ratio),
        `${number(m.review_candidate_count)}건`,
      ]),
      "report-daily",
    ),
  );
  daily.append(dailyDetails);
  sheet.append(daily);
  const evidence = node("div", undefined, "report-evidence");
  const issues = panel(
    "데이터 품질 메모",
    `등록된 품질 이슈 ${number(report.issues.length)}건`,
  );
  for (const q of report.issues.slice(0, 12)) {
    const row = node("div", undefined, "report-entry");
    row.append(
      node("strong", `${q.plant_id} · ${q.local_date}`),
      node("p", `${q.rule_id} · ${number(q.count)}건`),
      node("p", q.reason),
    );
    issues.append(row);
  }
  if (!report.issues.length)
    issues.append(
      node(
        "p",
        "선택한 기간에 등록된 품질 이슈가 없습니다. 자료의 완전성은 별도로 확인하세요.",
      ),
    );
  if (report.issues.length > 12)
    issues.append(
      node(
        "p",
        "첫 12건을 표시합니다. 전체 근거는 출처 JSON에 포함됩니다.",
        "subtext",
      ),
    );
  const candidates = panel(
    "사람이 확인할 구간",
    "검토 후보는 확인된 고장이나 금전적 손실이 아닙니다.",
  );
  for (const e of report.candidates.slice(0, 12)) {
    const row = node("div", undefined, "report-entry");
    row.append(
      node("strong", `${e.plant_id} · ${e.intervals}개 연속 슬롯`),
      node("p", `${time(e.start_utc)} → ${time(e.end_utc)}`),
      node(
        "p",
        `POA ≥ ${e.thresholds.poa_wm2} W/m² · 출력/설비용량 < ${number(e.thresholds.power_ratio * 100, 1)}%`,
      ),
    );
    candidates.append(row);
  }
  if (!report.candidates.length)
    candidates.append(
      node(
        "p",
        "신뢰 가능한 데이터에서 연속 저출력 조건을 만족한 구간이 없습니다. 판단 불가 구간은 CSV에 별도로 기록됩니다. 0건이 고장 없음의 증거는 아닙니다.",
      ),
    );
  if (report.candidates.length > 12)
    candidates.append(
      node(
        "p",
        "첫 12건을 표시합니다. 전체 후보는 출처 JSON에 포함됩니다.",
        "subtext",
      ),
    );
  evidence.append(issues, candidates);
  sheet.append(evidence);
  const lineage = panel(
    "계산과 원본 계보",
    "생성 시점의 데이터와 계산 버전을 보존한 보고서입니다.",
  );
  lineage.classList.add("report-section");
  lineage.append(
    definitionList([
      [
        "계산 기준",
        "누락을 0으로 채우거나 앞 값으로 확장하지 않습니다. 원본 보간값은 포함될 수 있으며 별도 표시합니다. 각 인버터의 원본 관측 범위로 기대 슬롯을 계산합니다.",
      ],
      [
        "해석 범위",
        "원본 보간·누락·표본 수 불명 구간에서는 저출력을 판단하지 않습니다. DC 설비용량과 AC 출력의 비율은 탐색용입니다.",
      ],
      ["계산 버전", report.calculation_version],
      ["생성 시각", time(report.generated_at)],
      ["보고서 ID", report.report_id],
      ["원본 매니페스트 SHA-256", report.source_manifest_hash],
    ]),
  );
  const sources = node("details", undefined, "report-sources");
  sources.append(
    node("summary", `원본 파일과 체크섬 ${report.sources.length}개`),
  );
  for (const source of report.sources) {
    const row = node("div", undefined, "report-entry");
    row.append(
      node("strong", source.original_filename),
      node(
        "p",
        `${source.source_kind} · ${source.source_version} · ${source.license}`,
      ),
      node("code", source.sha256),
    );
    sources.append(row);
  }
  lineage.append(sources);
  if (report.public)
    lineage.append(
      link(
        "BR-PVGen · Jesus 외 · Zenodo · CC BY 4.0",
        "https://zenodo.org/records/21511487",
      ),
    );
  sheet.append(lineage);
  return sheet;
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
    "에너지는 추정치입니다. 저출력 슬롯이 3개 연속일 때 검토 사건으로 집계하며, 고장 확정을 뜻하지 않습니다.",
  );
  const labels = {
    normal: "규칙상 일반",
    INSUFFICIENT_DATA: "판단 불가",
    review_candidate: "저출력 슬롯 · 연속성 확인 필요",
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

function definitionList(items) {
  const list = node("dl", undefined, "definition-list");
  for (const [term, description] of items) {
    const row = node("div");
    row.append(node("dt", term), node("dd", description));
    list.append(row);
  }
  return list;
}

async function plants(signal) {
  return overview(signal, "plants");
}
async function quality(signal) {
  return overview(signal, "quality");
}

async function sources(signal) {
  const suffix = state.source === "all" ? "" : `&source_kind=${state.source}`;
  const data = await get(
    `/api/v1/overview?period=${encodeURIComponent(state.period)}${suffix}`,
    signal,
  );
  const root = node("div", undefined, "sources-view");
  root.append(
    hero(
      "데이터 출처와 계보",
      "공개 원본에서 분석 결과까지, 어디서 왔고 어떻게 해석해야 하는지 확인하세요.",
    ),
  );
  const scope = panel(
    "현재 조회 범위",
    `${state.period} · ${data.timezone} 기준`,
  );
  scope.append(
    node(
      "p",
      `${data.summary.plant_count}개 발전소가 선택한 범위에 등록되어 있습니다. 아래 자료 설명은 제공 데이터셋 전체의 설명이며, 등록 규모와 다를 수 있습니다.`,
      "subtext",
    ),
  );
  const items = data.plants.map((plant) => [
    plant.plant_id,
    plant.source_kinds
      .map((k) => (k === "public" ? "BR-PVGen 공개 자료" : "합성 데모"))
      .join(" / "),
    `${plant.partition_count}일`,
    workspaceLink(
      "관측 근거",
      { view: "series", plant: plant.plant_id, day: plant.last_day },
      "text-button",
    ),
  ]);
  scope.append(
    items.length
      ? table(
          ["발전소", "자료 구분", "등록 범위", "조회"],
          items,
          "source-table",
        )
      : node("p", "선택한 범위에 등록된 자료가 없습니다."),
  );
  root.append(scope);
  const original = panel(
    "BR-PVGen 공개 역사 자료",
    "브라질 51개 발전소를 포함하는 원본 데이터셋 · 실제 운영 중인 실시간 서비스가 아닙니다.",
  );
  original.append(
    definitionList([
      [
        "제공자와 라이선스",
        "Jesus 외 · CC BY 4.0. 원본 제공자의 보간·품질 표시를 보존합니다.",
      ],
      [
        "자료와 계산",
        "전력·기상 시계열을 15분 슬롯으로 처리합니다. 유효 전력 × 0.25시간으로 계산한 에너지는 추정 발전량입니다.",
      ],
      [
        "시간과 범위",
        "UTC 기준으로 조회합니다. 화면의 등록 일수는 현재 선택한 월의 처리 범위이며 원본 전체 기간을 뜻하지 않습니다.",
      ],
    ]),
  );
  const external = link(
    "원본 데이터셋 열기 · Zenodo (새 탭)",
    "https://zenodo.org/records/21511487",
  );
  external.target = "_blank";
  external.rel = "noopener noreferrer";
  original.append(external);
  root.append(original);
  const demo = panel(
    "합성 데모",
    "결측·중복·실패 복구 동작을 재현하기 위해 프로젝트에서 생성한 시나리오입니다.",
  );
  demo.append(
    node(
      "p",
      "실제 발전소의 실적이나 현장 장애 사례로 해석하지 않습니다. 자료 구분 필터에서 공개 자료와 분리해 조회할 수 있습니다.",
      "subtext",
    ),
  );
  root.append(demo);
  const lineage = panel(
    "결과에서 원본까지 추적",
    "원본 파일·처리 실행·게시된 파티션·월간 보고서를 연결합니다.",
  );
  const steps = node("ol", undefined, "lineage-steps");
  for (const text of [
    "원본 파일의 체크섬과 source_version을 보존합니다.",
    "실행 이력에서 처리 상태와 하위 파티션, 원본 근거를 확인합니다.",
    "검증을 완료한 파티션만 분석에 게시합니다. 실패 실행은 완료 자료와 구분됩니다.",
    "월간 보고서에서 선택된 데이터·계산 버전의 결과와 근거를 확인합니다.",
  ])
    steps.append(node("li", text));
  lineage.append(
    steps,
    workspaceLink("실행 이력에서 계보 확인", { view: "runs" }, "text-button"),
  );
  root.append(lineage);
  return root;
}

async function system() {
  const root = node("div", undefined, "system-view");
  root.append(
    hero(
      "시스템 관리",
      "분석 화면과 독립된 로컬 관리 화면에서 SolarOps 서비스를 시작하고 중지합니다.",
    ),
  );
  const controls = panel(
    "로컬 관리 콘솔",
    "대시보드가 중지되어도 8504 포트의 관리 화면은 유지됩니다.",
  );
  const open = link(
    "시스템 관리 열기",
    `http://127.0.0.1:8504/?${new URLSearchParams({ period: state.period, source: state.source })}`,
  );
  open.className = "text-button";
  controls.append(
    node(
      "p",
      "PostgreSQL·MinIO·대시보드·Airflow·SolarOps kind의 실제 상태와 시작·중지 버튼을 제공합니다. 관리자 화면은 이 PC에서만 접근할 수 있습니다.",
      "subtext",
    ),
    open,
  );
  root.append(controls);
  const help = panel(
    "관리 화면이 열리지 않을 때",
    "프로젝트 폴더에서 아래 명령을 실행한 뒤 다시 여세요.",
  );
  help.append(node("pre", "uv run solarops admin --project-root .", "code"));
  help.append(
    definitionList([
      [
        "분석 화면 · 8502",
        "Docker 안에서 실행합니다. 기본 구동에는 대시보드·PostgreSQL·MinIO가 필요합니다.",
      ],
      [
        "관리 화면 · 8504",
        "호스트 Python에서 별도로 실행합니다. 이 터미널에서 Ctrl+C를 누르면 관리 서버만 종료됩니다.",
      ],
      [
        "전체 중지",
        "관리 콘솔의 ‘SolarOps 작업 환경 → 중지’로 프로젝트 컨테이너와 kind를 멈춥니다. 관리 서버까지 끄려면 마지막에 Ctrl+C를 누르세요.",
      ],
      [
        "제어 범위",
        "기존 SolarOps 컨테이너만 시작·중지합니다. Docker Desktop 자체와 다른 프로젝트는 조작하지 않으며 데이터·볼륨 삭제 기능은 없습니다.",
      ],
    ]),
  );
  root.append(help);
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
  window.syncWorkspaceControls?.();
  $("#scope-controls").hidden = ["runs", "series", "system"].includes(
    state.view,
  );
  $("#breadcrumb").textContent = names[state.view];
  document
    .querySelectorAll("nav a")
    .forEach((b) =>
      b.setAttribute(
        "aria-current",
        b.dataset.view === state.view ||
          (state.view === "series" && b.dataset.view === "plants")
          ? "page"
          : "false",
      ),
    );
  view.setAttribute("aria-busy", "true");
  view.replaceChildren(node("div", "자료를 확인하고 있습니다…", "loading"));
  try {
    const content = await {
      overview,
      plants,
      quality,
      sources,
      system,
      reports,
      runs,
      series,
    }[state.view](currentController.signal);
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
