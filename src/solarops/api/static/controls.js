"use strict";
// Progressive enhancement keeps native values/change events as the data contract.
(() => {
  let sequence = 0;
  const enhanced = new Map();
  function el(tag, text, className) {
    const result = document.createElement(tag);
    if (text !== undefined) result.textContent = text;
    if (className) result.className = className;
    return result;
  }
  function enhance(select) {
    if (enhanced.has(select) || select.multiple) return;
    const id = `options-${++sequence}`;
    const wrapper = el("span", undefined, "select-control");
    const trigger = el("button", undefined, "select-trigger");
    trigger.type = "button";
    trigger.setAttribute("role", "combobox");
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-controls", id);
    const label =
      select.getAttribute("aria-label") ||
      Array.from(select.closest("label")?.childNodes || [])
        .filter((n) => n.nodeType === Node.TEXT_NODE)
        .map((n) => n.textContent.trim())
        .join(" ") ||
      "목록 선택";
    trigger.setAttribute("aria-label", label);
    if (select.id) trigger.dataset.selectFor = select.id;
    const value = el("span", undefined, "select-value");
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.setAttribute("aria-hidden", "true");
    const path = document.createElementNS(icon.namespaceURI, "path");
    path.setAttribute("d", "m6 9 6 6 6-6");
    icon.append(path);
    trigger.append(value, icon);
    const list = el("div", undefined, "select-options");
    list.id = id;
    list.setAttribute("role", "listbox");
    list.setAttribute("aria-label", label);
    list.setAttribute("popover", "auto");
    const options = Array.from(select.options).map((option, index) => {
      const row = el("div", option.textContent, "select-option");
      row.id = `${id}-${index}`;
      row.setAttribute("role", "option");
      if (option.disabled) row.setAttribute("aria-disabled", "true");
      row.addEventListener("pointerdown", (event) => event.preventDefault());
      row.onclick = () => commit(index);
      list.append(row);
      return row;
    });
    let active = select.selectedIndex,
      typeahead = "",
      lastType = 0;
    function highlight(index) {
      active = Math.max(0, Math.min(options.length - 1, index));
      options.forEach((row, i) =>
        row.classList.toggle("is-highlighted", i === active),
      );
      trigger.setAttribute("aria-activedescendant", options[active]?.id || "");
      options[active]?.scrollIntoView({ block: "nearest" });
    }
    function sync() {
      value.textContent =
        select.selectedOptions[0]?.textContent || "선택할 항목 없음";
      trigger.disabled = select.disabled || !select.options.length;
      options.forEach((row, index) =>
        row.setAttribute(
          "aria-selected",
          String(index === select.selectedIndex),
        ),
      );
    }
    function open() {
      if (trigger.disabled) return;
      const rect = trigger.getBoundingClientRect();
      const width = Math.min(Math.max(rect.width, 220), innerWidth - 24);
      list.style.width = `${width}px`;
      list.style.left = `${Math.max(12, Math.min(rect.left, innerWidth - width - 12))}px`;
      const below = innerHeight - rect.bottom - 16;
      list.style.maxHeight = `${Math.min(320, Math.max(below, rect.top - 16))}px`;
      list.style.top =
        below >= Math.min(options.length * 46 + 16, 240)
          ? `${rect.bottom + 6}px`
          : "auto";
      list.style.bottom =
        list.style.top === "auto" ? `${innerHeight - rect.top + 6}px` : "auto";
      list.showPopover();
      trigger.setAttribute("aria-expanded", "true");
      highlight(select.selectedIndex);
    }
    function close() {
      if (list.matches(":popover-open")) list.hidePopover();
    }
    function commit(index) {
      if (select.options[index]?.disabled) return;
      select.selectedIndex = index;
      sync();
      close();
      trigger.focus();
      select.dispatchEvent(new Event("change", { bubbles: true }));
    }
    trigger.onclick = () => (list.matches(":popover-open") ? close() : open());
    trigger.onkeydown = (event) => {
      const opened = list.matches(":popover-open");
      if (
        [
          "ArrowDown",
          "ArrowUp",
          "Home",
          "End",
          "Enter",
          " ",
          "Escape",
        ].includes(event.key)
      ) {
        event.preventDefault();
        if (event.key === "Escape") {
          close();
          return;
        }
        if (!opened) {
          open();
          return;
        }
        if (["Enter", " "].includes(event.key)) {
          commit(active);
          return;
        }
        let next =
          event.key === "Home"
            ? 0
            : event.key === "End"
              ? options.length - 1
              : active + (event.key === "ArrowDown" ? 1 : -1);
        const direction =
          event.key === "ArrowUp" || event.key === "End" ? -1 : 1;
        while (
          next >= 0 &&
          next < options.length &&
          select.options[next].disabled
        )
          next += direction;
        if (next >= 0 && next < options.length) highlight(next);
      } else if (event.key === "Tab") close();
      else if (
        event.key.length === 1 &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey
      ) {
        typeahead =
          Date.now() - lastType > 700 ? event.key : typeahead + event.key;
        lastType = Date.now();
        const index = Array.from(select.options).findIndex(
          (o) =>
            !o.disabled &&
            o.textContent.toLowerCase().startsWith(typeahead.toLowerCase()),
        );
        if (index >= 0) {
          if (!opened) open();
          highlight(index);
        }
      }
    };
    list.addEventListener("toggle", () => {
      const opened = list.matches(":popover-open");
      trigger.setAttribute("aria-expanded", String(opened));
      if (!opened) trigger.removeAttribute("aria-activedescendant");
    });
    select.hidden = true;
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");
    wrapper.append(trigger);
    (document.querySelector("main") || document.body).append(list);
    select.after(wrapper);
    select.addEventListener("change", sync);
    enhanced.set(select, { sync, close, list });
    sync();
  }
  function syncAll() {
    document.querySelectorAll("select").forEach(enhance);
    for (const [select, control] of enhanced) {
      if (!select.isConnected) {
        control.close();
        control.list.remove();
        enhanced.delete(select);
      } else control.sync();
    }
    const input = document.querySelector("#period"),
      trigger = document.querySelector("#period-open");
    if (input && trigger) {
      const [year, month] = input.value.split("-");
      trigger.textContent = `${year}년 ${Number(month)}월`;
      trigger.setAttribute(
        "aria-label",
        `보고 월 ${year}년 ${Number(month)}월 변경`,
      );
    }
  }
  window.syncWorkspaceControls = syncAll;
  let scheduled = false;
  new MutationObserver((records) => {
    if (
      !records.some((r) =>
        Array.from(r.addedNodes).some(
          (n) =>
            n.nodeType === 1 &&
            (n.matches("select") || n.querySelector("select")),
        ),
      )
    )
      return;
    if (!scheduled) {
      scheduled = true;
      queueMicrotask(() => {
        scheduled = false;
        syncAll();
      });
    }
  }).observe(document.body, { childList: true, subtree: true });
  window.addEventListener("resize", () => enhanced.forEach((c) => c.close()));

  const period = document.querySelector("#period");
  if (period) {
    let trigger = document.querySelector("#period-open");
    if (!trigger) {
      trigger = el("button", "보고 월 선택", "secondary");
      trigger.id = "period-open";
      period.after(trigger);
    }
    trigger.type = "button";
    trigger.setAttribute("aria-haspopup", "dialog");
    const dialog = el("dialog", undefined, "month-dialog");
    const title = el("h2", "보고 월 선택");
    title.id = "month-title";
    dialog.setAttribute("aria-labelledby", title.id);
    const row = el("div", undefined, "month-year");
    const prev = el("button", "이전 연도", "secondary"),
      next = el("button", "다음 연도", "secondary");
    const yearLabel = el("label", "연도"),
      year = el("input");
    year.type = "number";
    year.min = "1900";
    year.max = "2199";
    year.required = true;
    year.name = "report-year";
    year.autocomplete = "off";
    yearLabel.append(year);
    row.append(prev, yearLabel, next);
    const months = el("div", undefined, "month-grid");
    months.setAttribute("role", "group");
    months.setAttribute("aria-label", "월 선택");
    const close = el("button", "취소", "secondary month-cancel");
    close.onclick = () => dialog.close();
    const buttons = Array.from({ length: 12 }, (_, i) => {
      const button = el("button", `${i + 1}월`, "month-option");
      button.type = "button";
      button.onclick = () => {
        if (!year.reportValidity()) return;
        period.value = `${year.value}-${String(i + 1).padStart(2, "0")}`;
        syncAll();
        dialog.close();
        period.dispatchEvent(new Event("change", { bubbles: true }));
      };
      button.onkeydown = (event) => {
        const offset = {
          ArrowRight: 1,
          ArrowLeft: -1,
          ArrowDown: 3,
          ArrowUp: -3,
        }[event.key];
        if (offset !== undefined) {
          event.preventDefault();
          buttons[Math.max(0, Math.min(11, i + offset))].focus();
        }
      };
      months.append(button);
      return button;
    });
    function updateYear() {
      prev.disabled = Number(year.value) <= 1900;
      next.disabled = Number(year.value) >= 2199;
      buttons.forEach((button, i) =>
        button.setAttribute(
          "aria-pressed",
          String(
            period.value === `${year.value}-${String(i + 1).padStart(2, "0")}`,
          ),
        ),
      );
    }
    prev.onclick = () => {
      year.value = Math.max(1900, Number(year.value) - 1);
      updateYear();
    };
    next.onclick = () => {
      year.value = Math.min(2199, Number(year.value) + 1);
      updateYear();
    };
    year.oninput = updateYear;
    dialog.append(title, row, months, close);
    document.body.append(dialog);
    trigger.onclick = () => {
      year.value = period.value.slice(0, 4);
      updateYear();
      dialog.showModal();
      buttons[Number(period.value.slice(5)) - 1].focus();
    };
  }
  syncAll();
})();
