(function () {
  "use strict";
  var tools = document.querySelector("[data-catalog-tools]");
  if (!tools) return;
  var search = tools.querySelector("[data-catalog-search]");
  var count = tools.querySelector("[data-catalog-count]");
  var empty = document.querySelector("[data-catalog-empty]");
  function filter() {
    var query = search.value.trim().toLowerCase();
    var category = tools.querySelector("[data-catalog-category].is-active").dataset.catalogCategory;
    var visible = 0;
    document.querySelectorAll("[data-catalog-card]").forEach(function (card) {
      var show = card.dataset.name.includes(query) && (category === "all" || card.dataset.category === category);
      card.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = visible + (visible === 1 ? " plant" : " plants");
    empty.hidden = visible !== 0;
  }
  search.addEventListener("input", filter);
  tools.querySelectorAll("[data-catalog-category]").forEach(function (button) {
    button.addEventListener("click", function () {
      tools.querySelectorAll("[data-catalog-category]").forEach(function (item) { item.classList.toggle("is-active", item === button); });
      filter();
    });
  });
})();
