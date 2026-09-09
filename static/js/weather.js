(function () {
  "use strict";

  var svgNamespace = "http://www.w3.org/2000/svg";

  function svgElement(name, attributes, text) {
    var element = document.createElementNS(svgNamespace, name);
    Object.keys(attributes || {}).forEach(function (key) {
      element.setAttribute(key, attributes[key]);
    });
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function smoothPath(points) {
    var path = "M " + points[0].x + " " + points[0].y;
    for (var index = 1; index < points.length; index += 1) {
      var previous = points[index - 1];
      var point = points[index];
      var middleX = (previous.x + point.x) / 2;
      path += " C " + middleX + " " + previous.y;
      path += ", " + middleX + " " + point.y;
      path += ", " + point.x + " " + point.y;
    }
    return path;
  }

  function numericValue(value) {
    var number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function setDetail(details, selector, value) {
    var target = details.querySelector(selector);
    if (target) target.textContent = value;
  }

  function initHourlyChart(chart) {
    var svg = chart.querySelector("[data-hourly-temperature]");
    var hits = Array.from(chart.querySelectorAll("[data-hour-index]"));
    var details = chart
      .closest(".weather-hourly-chart-card")
      .querySelector("[data-hourly-details]");
    var temperatures = hits.map(function (hourButton) {
      return numericValue(hourButton.dataset.temperature);
    });
    var selectedIndex = 0;
    var points = [];

    if (!svg || !details || !hits.length || temperatures.some(function (value) {
      return value === null;
    })) return;

    function updateSelectedHour(index) {
      var hourButton = hits[index];
      if (!hourButton) return;
      selectedIndex = index;

      hits.forEach(function (candidate, candidateIndex) {
        candidate.setAttribute(
          "aria-pressed",
          candidateIndex === index ? "true" : "false"
        );
      });
      svg
        .querySelectorAll(".weather-hourly-chart__temperature-point")
        .forEach(function (point, pointIndex) {
          point.classList.toggle("is-selected", pointIndex === index);
        });

      setDetail(
        details,
        "[data-hourly-detail-time]",
        hourButton.dataset.dateLabel + " \u00b7 " + hourButton.dataset.timeLabel
      );
      setDetail(details, "[data-hourly-detail-condition]", hourButton.dataset.condition);
      setDetail(
        details,
        "[data-hourly-detail-temperature]",
        numericValue(hourButton.dataset.temperature).toFixed(1) + "\u00b0C"
      );
      setDetail(
        details,
        "[data-hourly-detail-feels]",
        numericValue(hourButton.dataset.feels).toFixed(1) + "\u00b0C"
      );
      setDetail(
        details,
        "[data-hourly-detail-humidity]",
        Math.round(numericValue(hourButton.dataset.humidity)) + "%"
      );
      setDetail(
        details,
        "[data-hourly-detail-sunshine]",
        Math.round(numericValue(hourButton.dataset.sunshine)) + " min"
      );
      setDetail(
        details,
        "[data-hourly-detail-rain]",
        numericValue(hourButton.dataset.rain).toFixed(1) + " mm \u00b7 " +
          Math.round(numericValue(hourButton.dataset.rainProbability)) + "%"
      );
      setDetail(
        details,
        "[data-hourly-detail-wind]",
        numericValue(hourButton.dataset.wind).toFixed(1) + " km/h"
      );
    }

    function sizeBars() {
      chart
        .querySelectorAll(".weather-hourly-chart__sunshine [data-sunshine]")
        .forEach(function (cell) {
          var minutes = Math.max(0, Math.min(60, numericValue(cell.dataset.sunshine)));
          cell.style.setProperty("--bar-height", (minutes / 60 * 42).toFixed(1) + "px");
        });

      var rainCells = Array.from(
        chart.querySelectorAll(".weather-hourly-chart__rain [data-rain]")
      );
      var rainMaximum = Math.max.apply(null, rainCells.map(function (cell) {
        return numericValue(cell.dataset.rain) || 0;
      }).concat([1]));
      rainCells.forEach(function (cell) {
        var rain = numericValue(cell.dataset.rain) || 0;
        var height = rain > 0 ? Math.max(3, rain / rainMaximum * 42) : 0;
        cell.style.setProperty("--bar-height", height.toFixed(1) + "px");
      });
    }

    function renderTemperature() {
      var width = chart.clientWidth;
      var height = 176;
      var edge = 36;
      var top = 25;
      var bottom = 151;
      if (width < 100) return;

      var rawMinimum = Math.min.apply(null, temperatures);
      var rawMaximum = Math.max.apply(null, temperatures);
      var midpoint = (rawMinimum + rawMaximum) / 2;
      var minimum = Math.floor(rawMinimum - 1);
      var maximum = Math.ceil(rawMaximum + 1);
      if (maximum - minimum < 4) {
        minimum = Math.floor(midpoint - 2);
        maximum = Math.ceil(midpoint + 2);
      }
      var spread = maximum - minimum;

      points = temperatures.map(function (temperature, index) {
        return {
          x: edge + (index + 0.5) * ((width - edge * 2) / temperatures.length),
          y: top + (maximum - temperature) / spread * (bottom - top),
          temperature: temperature
        };
      });

      svg.replaceChildren();
      svg.setAttribute("viewBox", "0 0 " + width + " " + height);

      [maximum, (maximum + minimum) / 2, minimum].forEach(function (value) {
        var y = top + (maximum - value) / spread * (bottom - top);
        svg.appendChild(svgElement("line", {
          x1: edge,
          x2: width - edge,
          y1: y,
          y2: y,
          class: "weather-hourly-chart__gridline"
        }));
        svg.appendChild(svgElement("text", {
          x: 4,
          y: y + 3,
          class: "weather-hourly-chart__scale-label"
        }, Math.round(value) + "\u00b0"));
      });

      var line = smoothPath(points);
      svg.appendChild(svgElement("path", {
        d: line + " L " + points[points.length - 1].x + " " + bottom +
          " L " + points[0].x + " " + bottom + " Z",
        class: "weather-hourly-chart__temperature-area"
      }));
      svg.appendChild(svgElement("path", {
        d: line,
        class: "weather-hourly-chart__temperature-line"
      }));

      points.forEach(function (point, index) {
        svg.appendChild(svgElement("circle", {
          cx: point.x,
          cy: point.y,
          r: index === selectedIndex ? 3.7 : 2.8,
          class: "weather-hourly-chart__temperature-point" +
            (index === selectedIndex ? " is-selected" : "")
        }));
        if (index % 3 === 0 || index === points.length - 1) {
          svg.appendChild(svgElement("text", {
            x: point.x,
            y: Math.max(12, point.y - 9),
            class: "weather-hourly-chart__temperature-value"
          }, Math.round(point.temperature) + "\u00b0"));
        }
      });
    }

    hits.forEach(function (hourButton, index) {
      ["pointerenter", "focus", "click"].forEach(function (eventName) {
        hourButton.addEventListener(eventName, function () {
          updateSelectedHour(index);
        });
      });
    });

    sizeBars();
    renderTemperature();
    updateSelectedHour(0);

    if ("ResizeObserver" in window) {
      new ResizeObserver(renderTemperature).observe(chart);
    } else {
      window.addEventListener("resize", renderTemperature);
    }
  }

  document.querySelectorAll("[data-hourly-chart]").forEach(initHourlyChart);

  var button = document.querySelector("[data-weather-refresh]");
  if (!button) return;

  var label = button.querySelector("[data-weather-refresh-label]");
  var status = document.querySelector("[data-weather-refresh-status]");
  var normalLabel = label.textContent;
  var hourlyRefreshMilliseconds = 60 * 60 * 1000;
  var loadedAt = Date.now();
  var hourlyRefreshTimer = null;

  function reloadForFreshWeather() {
    if (document.hidden || button.disabled) return;
    window.location.reload();
  }

  function scheduleHourlyRefresh(delay) {
    window.clearTimeout(hourlyRefreshTimer);
    hourlyRefreshTimer = window.setTimeout(
      reloadForFreshWeather,
      delay
    );
  }

  document
    .querySelectorAll(".weather-tabs__button")
    .forEach(function (tab, index) {
      var tabKeys = ["overview", "forecast", "history", "insights"];

      tab.addEventListener("click", function () {
        var url = new URL(window.location.href);
        url.searchParams.set("tab", tabKeys[index]);
        window.history.replaceState(null, "", url);
      });
    });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) return;

    var elapsed = Date.now() - loadedAt;
    if (elapsed >= hourlyRefreshMilliseconds) {
      reloadForFreshWeather();
      return;
    }

    scheduleHourlyRefresh(hourlyRefreshMilliseconds - elapsed);
  });

  scheduleHourlyRefresh(hourlyRefreshMilliseconds);

  function setRefreshing(isRefreshing) {
    button.disabled = isRefreshing;
    label.textContent = isRefreshing ? "Refreshing\u2026" : normalLabel;
    if (isRefreshing) {
      button.setAttribute("aria-busy", "true");
    } else {
      button.removeAttribute("aria-busy");
    }
  }

  button.addEventListener("click", async function () {
    if (button.disabled) return;

    setRefreshing(true);
    status.hidden = true;
    status.textContent = "";

    try {
      var response = await fetch(button.dataset.refreshUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Accept": "application/json",
          "X-Requested-With": "XMLHttpRequest"
        }
      });
      var result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.error || "Weather refresh request failed");
      }
      window.location.reload();
    } catch (error) {
      status.textContent = "Couldn\u2019t refresh weather. Current data is still shown.";
      status.hidden = false;
    } finally {
      setRefreshing(false);
    }
  });
})();
