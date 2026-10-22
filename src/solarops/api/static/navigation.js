"use strict";
// A disclosure on small screens: normal document flow, no hidden focus trap.
const menuToggle = document.querySelector(".nav-toggle");
menuToggle?.addEventListener("click", () => {
  const expanded = menuToggle.getAttribute("aria-expanded") !== "true";
  menuToggle.setAttribute("aria-expanded", String(expanded));
  menuToggle.textContent = expanded ? "메뉴 닫기" : "메뉴 열기";
  document.querySelector(".sidebar").classList.toggle("is-open", expanded);
});
document.querySelector(".sidebar")?.addEventListener("keydown", (event) => {
  if (
    event.key === "Escape" &&
    menuToggle.getAttribute("aria-expanded") === "true"
  ) {
    menuToggle.click();
    menuToggle.focus();
  }
});
