(function () {
  "use strict";

  async function readJsonResponse(response) {
    var result;

    try {
      result = await response.json();
    } catch (error) {
      throw new Error("GardenHub received an invalid server response.");
    }

    if (!response.ok || !result.ok) {
      throw new Error(
        result.error || "The request could not be completed."
      );
    }

    return result;
  }

  async function searchLocation(query) {
    var response = await fetch(
      "/garden-location/search?q=" +
        encodeURIComponent(query)
    );

    var result = await readJsonResponse(response);

    return result.results || [];
  }

  async function saveLocation(location) {
    var response = await fetch(
      "/garden-location",
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json"
        },

        body: JSON.stringify({
          location_label: location.location_label,
          latitude: location.latitude,
          longitude: location.longitude
        })
      }
    );

    var result = await readJsonResponse(response);

    return result.location;
  }

  window.GardenHubGardenLocationApi = {
    search: searchLocation,
    save: saveLocation
  };
})();