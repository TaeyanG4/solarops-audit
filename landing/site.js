(() => {
  const data = JSON.parse(document.querySelector("#preview-data").textContent);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const number = (value, digits = 2) =>
    new Intl.NumberFormat("en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  const feedback = (element) => {
    element.getAnimations().forEach((animation) => animation.cancel());
    if (!reduced.matches)
      element.animate([{ opacity: 0.82 }, { opacity: 1 }], {
        duration: 180,
        easing: "ease-out",
      });
  };
  const metrics = {
    observed: [
      "100",
      "예상 슬롯에 관측값이 존재하는 비율입니다. 값의 유효성이나 해당 월 전체 자료의 확보를 뜻하지 않습니다.",
    ],
    valid: [
      "82.5",
      "계산 조건을 통과한 전력 슬롯의 비율입니다. 관측된 값 중에도 계산에서 제외되는 무효값이 있습니다.",
    ],
    interpolated: [
      "9.9",
      "원본 제작자가 보간했다고 표시한 슬롯의 비율입니다. 유효·무효와 중첩될 수 있어 두 비율에 더하지 않습니다.",
    ],
  };
  const result = document.querySelector("#metric-result");
  document.querySelectorAll("[data-metric]").forEach((button) => {
    button.disabled = false;
    button.addEventListener("click", () => {
      if (button.getAttribute("aria-pressed") === "true") return;
      const [value, explanation] = metrics[button.dataset.metric];
      document
        .querySelectorAll("[data-metric]")
        .forEach((other) =>
          other.setAttribute(
            "aria-pressed",
            String(other.dataset.metric === button.dataset.metric),
          ),
        );
      result
        .querySelector(".metric-value")
        .replaceChildren(
          document.createTextNode(value),
          Object.assign(document.createElement("span"), { textContent: "%" }),
        );
      result.querySelector(".metric-explanation").textContent = explanation;
      feedback(result);
    });
  });

  document.querySelectorAll("[data-unit]").forEach((button) => {
    button.disabled = false;
    button.addEventListener("click", () => {
      if (button.getAttribute("aria-pressed") === "true") return;
      const mwh = button.dataset.unit === "mwh";
      document
        .querySelectorAll("[data-unit]")
        .forEach((other) =>
          other.setAttribute("aria-pressed", String(other === button)),
        );
      document.querySelector("#hero-energy").textContent = number(
        data.report.estimated_energy_kwh / (mwh ? 1000 : 1),
      );
      document.querySelector("#hero-unit").textContent = mwh ? "MWh" : "kWh";
      feedback(document.querySelector(".preview-energy"));
    });
  });

  const days = data.timeline;
  const bars = [...document.querySelectorAll("[data-day-index]")];
  const trigger = document.querySelector("#day-trigger");
  const dateOptions = document.querySelector("#day-options");
  const dateButtons = [...document.querySelectorAll("[data-date-option]")];
  const previous = document.querySelector("#day-prev");
  const next = document.querySelector("#day-next");
  const tooltip = document.querySelector("#chart-tooltip");
  let selected = 0;
  const updateDay = (index, focus = false) => {
    selected = Math.max(0, Math.min(days.length - 1, index));
    const day = days[selected];
    bars.forEach((bar, i) => {
      bar.setAttribute("aria-pressed", String(i === selected));
      bar.setAttribute("tabindex", i === selected ? "0" : "-1");
    });
    trigger.dataset.index = String(selected);
    trigger.querySelector("span").textContent = day.day;
    dateButtons.forEach((button, i) =>
      button.setAttribute("aria-selected", String(i === selected)),
    );
    previous.disabled = selected === 0;
    next.disabled = selected === days.length - 1;
    document.querySelector("#day-energy").textContent =
      `${number(day.estimated_energy_kwh / 1000)} MWh`;
    document.querySelector("#day-description").textContent =
      `${day.day} · 추정 · ${day.plant_count}개 발전소 합계`;
    feedback(document.querySelector(".day-result"));
    if (focus) bars[selected].focus();
  };
  const showTooltip = (bar, index) => {
    const day = days[index];
    tooltip.textContent = `${day.day} · ${number(day.estimated_energy_kwh / 1000)} MWh`;
    tooltip.hidden = false;
    const area = document.querySelector(".chart-wrap").getBoundingClientRect();
    const rect = bar.getBoundingClientRect();
    const x = Math.max(
      0,
      Math.min(
        area.width - tooltip.offsetWidth,
        rect.left - area.left + rect.width / 2 - tooltip.offsetWidth / 2,
      ),
    );
    tooltip.style.left = `${x}px`;
  };
  bars.forEach((bar, index) => {
    bar.addEventListener("click", () => updateDay(index));
    bar.addEventListener("pointerenter", () => showTooltip(bar, index));
    bar.addEventListener("pointerleave", () => {
      tooltip.hidden = true;
    });
    bar.addEventListener("focus", () => showTooltip(bar, index));
    bar.addEventListener("blur", () => {
      tooltip.hidden = true;
    });
    bar.addEventListener("keydown", (event) => {
      let indexToSelect;
      if (["ArrowRight", "ArrowUp"].includes(event.key))
        indexToSelect = index + 1;
      if (["ArrowLeft", "ArrowDown"].includes(event.key))
        indexToSelect = index - 1;
      if (event.key === "Home") indexToSelect = 0;
      if (event.key === "End") indexToSelect = days.length - 1;
      if (["Enter", " "].includes(event.key)) indexToSelect = index;
      if (event.key === "Escape") tooltip.hidden = true;
      if (indexToSelect !== undefined) {
        event.preventDefault();
        updateDay(indexToSelect, true);
      }
    });
  });
  trigger.disabled = false;
  next.disabled = false;
  const closeDates = (returnFocus = false) => {
    dateOptions.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
    if (returnFocus) trigger.focus();
  };
  const focusDate = (index) => {
    const i = Math.max(0, Math.min(days.length - 1, index));
    dateButtons.forEach((button, j) => (button.tabIndex = j === i ? 0 : -1));
    dateButtons[i].focus({ preventScroll: true });
    dateButtons[i].scrollIntoView({ block: "nearest", behavior: "instant" });
  };
  const openDates = () => {
    const rect = trigger.getBoundingClientRect();
    const below = rect.top < 280 && innerHeight - rect.bottom > rect.top;
    dateOptions.dataset.placement = below ? "below" : "above";
    dateOptions.style.maxHeight = `${Math.max(120, Math.min(264, (below ? innerHeight - rect.bottom : rect.top) - 20))}px`;
    dateOptions.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    focusDate(selected);
  };
  trigger.addEventListener("click", () =>
    dateOptions.hidden ? openDates() : closeDates(),
  );
  trigger.addEventListener("keydown", (event) => {
    if (["ArrowDown", "ArrowUp"].includes(event.key)) {
      event.preventDefault();
      openDates();
    }
  });
  dateButtons.forEach((button, index) => {
    button.addEventListener("click", () => {
      updateDay(index);
      closeDates(true);
    });
    button.addEventListener("keydown", (event) => {
      let i;
      if (event.key === "ArrowDown") i = index + 1;
      if (event.key === "ArrowUp") i = index - 1;
      if (event.key === "Home") i = 0;
      if (event.key === "End") i = days.length - 1;
      if (event.key === "PageDown") i = index + 7;
      if (event.key === "PageUp") i = index - 7;
      if (i !== undefined) {
        event.preventDefault();
        focusDate(i);
      }
      if (event.key === "Escape") {
        event.preventDefault();
        closeDates(true);
      }
    });
  });
  document.addEventListener("pointerdown", (event) => {
    if (!event.target.closest(".day-picker")) closeDates();
  });
  document
    .querySelector(".day-picker")
    .addEventListener("focusout", (event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) closeDates();
    });
  previous.addEventListener("click", () => updateDay(selected - 1));
  next.addEventListener("click", () => updateDay(selected + 1));

  const viewTabs = [...document.querySelectorAll("[data-view-tab]")];
  const viewNav = document.querySelector(".app-nav");
  const wide = matchMedia("(min-width: 801px)");
  const orient = () =>
    viewNav.setAttribute(
      "aria-orientation",
      wide.matches ? "vertical" : "horizontal",
    );
  orient();
  wide.addEventListener("change", orient);
  const showView = (tab) => {
    if (tab.getAttribute("aria-selected") === "true") return;
    closeDates();
    tooltip.hidden = true;
    viewTabs.forEach((other) => {
      const active = other === tab;
      other.setAttribute("aria-selected", String(active));
      other.tabIndex = active ? 0 : -1;
      document
        .querySelector(`#view-${other.dataset.viewTab}`)
        .toggleAttribute("data-active", active);
    });
    document.querySelector("#app-crumb").textContent =
      tab.querySelector("span").textContent;
    feedback(document.querySelector(`#view-${tab.dataset.viewTab}`));
  };
  viewTabs.forEach((tab, index) => {
    tab.disabled = false;
    tab.addEventListener("click", () => showView(tab));
    tab.addEventListener("keydown", (event) => {
      let i;
      if (["ArrowDown", "ArrowRight"].includes(event.key))
        i = (index + 1) % viewTabs.length;
      if (["ArrowUp", "ArrowLeft"].includes(event.key))
        i = (index - 1 + viewTabs.length) % viewTabs.length;
      if (event.key === "Home") i = 0;
      if (event.key === "End") i = viewTabs.length - 1;
      if (i !== undefined) {
        event.preventDefault();
        showView(viewTabs[i]);
        viewTabs[i].focus();
      }
    });
  });

  const tabs = [...document.querySelectorAll("[data-format]")];
  const showFormat = (tab) => {
    if (tab.getAttribute("aria-selected") === "true") return;
    tabs.forEach((other) => {
      const active = other === tab;
      other.setAttribute("aria-selected", String(active));
      other.tabIndex = active ? 0 : -1;
      document.querySelector(`#report-${other.dataset.format}`).hidden =
        !active;
    });
    feedback(document.querySelector(`#report-${tab.dataset.format}`));
  };
  tabs.forEach((tab, index) => {
    tab.disabled = false;
    tab.addEventListener("click", () => showFormat(tab));
    tab.addEventListener("keydown", (event) => {
      let i;
      if (event.key === "ArrowRight") i = (index + 1) % tabs.length;
      if (event.key === "ArrowLeft")
        i = (index - 1 + tabs.length) % tabs.length;
      if (event.key === "Home") i = 0;
      if (event.key === "End") i = tabs.length - 1;
      if (i !== undefined) {
        event.preventDefault();
        showFormat(tabs[i]);
        tabs[i].focus();
      }
    });
  });
  const copy = document.querySelector("#copy-hash");
  copy.disabled = false;
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(data.report.source_manifest_hash);
      document.querySelector("#copy-status").textContent = "복사했습니다.";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(document.querySelector("#lineage-hash"));
      const selection = getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      document.querySelector("#copy-status").textContent =
        "선택한 해시를 복사하세요.";
    }
  });
})();
