(function () {
  "use strict";

  var snapshot = document.querySelector("[data-garden-snapshot]");
  var context = document.querySelector("[data-bed-context]");
  if (!snapshot || !context) return;

  var overview = context.querySelector("[data-context-overview]");
  var bedButtons = Array.prototype.slice.call(snapshot.querySelectorAll("[data-bed-select]"));
  var bedPanels = Array.prototype.slice.call(context.querySelectorAll("[data-bed-panel]"));

  function showOverview(shouldFocus) {
    bedButtons.forEach(function (button) {
      button.setAttribute("aria-pressed", "false");
    });
    bedPanels.forEach(function (panel) {
      panel.hidden = true;
    });
    overview.hidden = false;
    if (shouldFocus && bedButtons.length) bedButtons[0].focus();
  }

  function showBed(button) {
    var bedId = button.dataset.bedSelect;
    bedButtons.forEach(function (item) {
      item.setAttribute("aria-pressed", String(item === button));
    });
    overview.hidden = true;
    bedPanels.forEach(function (panel) {
      panel.hidden = panel.dataset.bedPanel !== bedId;
    });

    if (window.matchMedia("(max-width: 40rem)").matches) {
      context.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  bedButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      showBed(button);
    });
  });

  context.querySelectorAll("[data-show-overview]").forEach(function (button) {
    button.addEventListener("click", function () {
      showOverview(true);
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && overview.hidden) showOverview(false);
  });

  showOverview(false);
})();
