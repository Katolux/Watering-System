(function () {
  "use strict";

  var filters = Array.from(document.querySelectorAll("[data-notification-filter]"));
  var items = Array.from(document.querySelectorAll("[data-notification-item]"));
  var selectors = Array.from(document.querySelectorAll("[data-notification-select]"));
  var panes = Array.from(document.querySelectorAll("[data-notification-pane]"));
  var empty = document.querySelector("[data-notification-empty]");
  var compactQuery = window.matchMedia("(max-width: 64rem)");

  function selectEvent(eventId, toggleCompactDetails) {
    var selectedItem = items.find(function (item) { return item.dataset.eventId === eventId; });
    var wasCompactExpanded = selectedItem && selectedItem.classList.contains("is-mobile-expanded");
    items.forEach(function (item) { item.classList.remove("is-mobile-expanded"); });
    if (compactQuery.matches && toggleCompactDetails && selectedItem && !wasCompactExpanded) {
      selectedItem.classList.add("is-mobile-expanded");
    }
    items.forEach(function (item) {
      item.classList.toggle("is-selected", item.dataset.eventId === eventId);
    });
    selectors.forEach(function (button) {
      var isSelected = button.dataset.notificationSelect === eventId;
      var isExpanded = isSelected && (
        !compactQuery.matches || button.closest("[data-notification-item]").classList.contains("is-mobile-expanded")
      );
      button.setAttribute("aria-expanded", String(isExpanded));
    });
    panes.forEach(function (pane) {
      pane.hidden = pane.dataset.notificationPane !== eventId;
    });
  }

  function applyFilter(filter) {
    var visibleCount = 0;
    items.forEach(function (item) {
      var matches = filter === "all"
        || (filter === "attention" && item.dataset.attention === "true")
        || item.dataset.category === filter;
      item.hidden = !matches;
      if (matches) visibleCount += 1;
    });
    filters.forEach(function (button) {
      var selected = button.dataset.notificationFilter === filter;
      button.classList.toggle("is-active", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    if (empty) empty.hidden = visibleCount !== 0;
    var selectedItem = items.find(function (item) { return item.classList.contains("is-selected"); });
    if (!selectedItem || selectedItem.hidden) {
      var firstVisible = items.find(function (item) { return !item.hidden; });
      if (firstVisible) selectEvent(firstVisible.dataset.eventId, false);
    }
  }

  filters.forEach(function (button) {
    button.addEventListener("click", function () {
      applyFilter(button.dataset.notificationFilter);
    });
  });

  selectors.forEach(function (button) {
    button.addEventListener("click", function () {
      selectEvent(button.dataset.notificationSelect, true);
    });
  });

  function selectHashTarget() {
    items.forEach(function (item) { item.classList.remove("is-linked"); });
    if (!window.location.hash) return false;
    var target = document.querySelector(window.location.hash);
    if (target && target.matches("[data-notification-item]")) {
      target.classList.add("is-linked");
      selectEvent(target.dataset.eventId, true);
      return true;
    }
    return false;
  }

  if (!selectHashTarget() && items.length) {
    selectEvent(items[0].dataset.eventId, false);
  }

  window.addEventListener("hashchange", selectHashTarget);

  compactQuery.addEventListener("change", function () {
    var selected = items.find(function (item) { return item.classList.contains("is-selected"); });
    if (selected) selectEvent(selected.dataset.eventId, false);
  });
})();
