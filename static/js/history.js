(function () {
  "use strict";

  var hub = document.querySelector("[data-history-hub]");
  if (!hub) return;

  var filters = Array.from(hub.querySelectorAll("[data-history-filter]"));
  var items = Array.from(hub.querySelectorAll("[data-history-item]"));
  var empty = hub.querySelector("[data-history-empty]");
  var emptyTitle = hub.querySelector("[data-history-empty-title]");
  var emptyText = hub.querySelector("[data-history-empty-text]");
  var status = hub.querySelector("[data-history-status]");

  function applyFilter(button) {
    var filter = button.dataset.historyFilter;
    var visibleCount = 0;

    items.forEach(function (item) {
      var visible = filter === "all" || item.dataset.category === filter;
      item.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    filters.forEach(function (filterButton) {
      var selected = filterButton === button;
      filterButton.classList.toggle("is-active", selected);
      filterButton.setAttribute("aria-pressed", String(selected));
    });

    if (empty) empty.hidden = visibleCount !== 0;
    if (emptyTitle) emptyTitle.textContent = button.dataset.emptyTitle;
    if (emptyText) emptyText.textContent = button.dataset.emptyText;
    if (status) {
      status.textContent = visibleCount
        ? "Showing " + visibleCount + " garden history events."
        : button.dataset.emptyTitle;
    }
  }

  filters.forEach(function (button) {
    button.addEventListener("click", function () { applyFilter(button); });
  });
})();
