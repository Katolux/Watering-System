(function () {
  "use strict";

  var context = window.GardenHubGardenContext;
  var api = window.GardenHubGardenLocationApi;
  var mapModule = window.GardenHubGardenLocationMap;

  if (!context || !api || !mapModule) {
    console.error("GardenHub: location dependencies are missing.");
    return;
  }

  var dialog = document.querySelector("[data-location-dialog]");
  var form = document.querySelector("[data-location-form]");
  var input = document.querySelector("[data-location-label]");
  var status = document.querySelector("[data-location-status]");
  var results = document.querySelector("[data-location-results]");
  var coords = document.querySelector("[data-location-coordinates]");
  var latOutput = document.querySelector("[data-location-latitude]");
  var lonOutput = document.querySelector("[data-location-longitude]");
  var searchButton = document.querySelector("[data-location-search]");
  var gpsButton = document.querySelector("[data-use-device-location]");
  var mapNode = document.querySelector("[data-location-map]");

  if (!dialog || !form || !input) return;

  var draft = null;

  function message(text) {
    if (status) status.textContent = text || "";
  }

  function hasCoords(location) {
    return Boolean(
      location &&
      Number.isFinite(location.latitude) &&
      Number.isFinite(location.longitude)
    );
  }

  function showCoords() {
    var valid = hasCoords(draft);

    if (coords) coords.hidden = !valid;

    if (latOutput) {
      latOutput.textContent = valid
        ? draft.latitude.toFixed(6)
        : "";
    }

    if (lonOutput) {
      lonOutput.textContent = valid
        ? draft.longitude.toFixed(6)
        : "";
    }
  }

  function clearResults() {
    if (!results) return;

    results.innerHTML = "";
    results.hidden = true;
  }

  var locationMap = mapModule.create({
    node: mapNode,

    onLocationChange: function (location) {
      if (!draft) draft = {};

      draft.latitude = location.latitude;
      draft.longitude = location.longitude;
      draft.persisted = false;

      showCoords();

      message(
        "Marker moved. Save to use this location."
      );
    }
  });

  function selectLocation(latitude, longitude, label, source) {
    draft = Object.assign({}, draft || {}, {
      latitude: Number(latitude),
      longitude: Number(longitude),
      address_label: label || "Selected garden location",
      source: source,
      persisted: false
    });

    input.value = draft.address_label;

    showCoords();

    locationMap.setLocation(
      draft.latitude,
      draft.longitude
    );

    message(
      "Location selected. Move the marker if needed, then save."
    );
  }

  function openDialog() {
    context.closeMenu();

    draft = Object.assign(
      {},
      context.getLocation()
    );

    input.value = draft.address_label || "";

    clearResults();
    showCoords();

    dialog.showModal();

    if (hasCoords(draft)) {
      locationMap.setLocation(
        draft.latitude,
        draft.longitude
      );

      message(
        "This is the saved location used by GardenHub."
      );
    } else {
      locationMap.hide();

      message(
        "Use your current location or search for your garden."
      );
    }
  }

  async function searchLocation() {
    var query = input.value.trim();

    if (query.length < 2) {
      message("Enter a location to search.");
      input.focus();
      return;
    }

    clearResults();

    if (searchButton) searchButton.disabled = true;

    message("Searching for location…");

    try {
      var matches = await api.search(query);

      if (!matches.length) {
        message("No matching locations were found.");
        return;
      }

      matches.forEach(function (match) {
        var button = document.createElement("button");

        button.type = "button";
        button.className =
          "garden-location-dialog__result";

        button.textContent = match.label;

        button.addEventListener("click", function () {
          selectLocation(
            match.latitude,
            match.longitude,
            match.label,
            "location_search"
          );

          clearResults();
        });

        results.appendChild(button);
      });

      results.hidden = false;

      message(
        "Select the correct location from the results."
      );

    } catch (error) {
      message(
        error.message || "Location search failed."
      );

    } finally {
      if (searchButton) searchButton.disabled = false;
    }
  }

  function useDeviceLocation() {
    if (!navigator.geolocation) {
      message(
        "This browser does not provide device location."
      );

      return;
    }

    gpsButton.disabled = true;

    message("Requesting your location…");

    navigator.geolocation.getCurrentPosition(
      function (position) {
        selectLocation(
          position.coords.latitude,
          position.coords.longitude,
          input.value.trim() || "Current location",
          "browser_geolocation"
        );

        gpsButton.disabled = false;
      },

      function (error) {
        message(
          error.code === error.PERMISSION_DENIED
            ? "Location permission was denied."
            : "Your location could not be determined."
        );

        gpsButton.disabled = false;
      },

      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000
      }
    );
  }

  async function saveLocation(event) {
    event.preventDefault();

    var label = input.value.trim();

    if (!label) {
      message("Enter or select a location.");
      input.focus();
      return;
    }

    if (!hasCoords(draft)) {
      message("Choose a location before saving.");
      return;
    }

    message("Saving garden location…");

    try {
      var saved = await api.save({
        location_label: label,
        latitude: draft.latitude,
        longitude: draft.longitude
      });

      context.setLocation({
        address_label: saved.location_label,
        latitude: saved.latitude,
        longitude: saved.longitude,
        timezone: saved.timezone,
        source: "saved",
        persisted: true
      });

      dialog.close();

    } catch (error) {
      message(
        error.message ||
        "Location could not be saved."
      );
    }
  }

  document
    .querySelectorAll("[data-location-dialog-open]")
    .forEach(function (button) {
      button.addEventListener("click", openDialog);
    });

  document
    .querySelectorAll("[data-location-dialog-close]")
    .forEach(function (button) {
      button.addEventListener("click", function () {
        dialog.close();
      });
    });

  if (searchButton) {
    searchButton.addEventListener(
      "click",
      searchLocation
    );
  }

  if (gpsButton) {
    gpsButton.addEventListener(
      "click",
      useDeviceLocation
    );
  }

  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      searchLocation();
    }
  });

  form.addEventListener(
    "submit",
    saveLocation
  );
})();