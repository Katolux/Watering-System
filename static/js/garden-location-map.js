(function () {
  "use strict";

  function createGardenLocationMap(options) {
    options = options || {};

    var mapNode = options.node;

    var onLocationChange =
      typeof options.onLocationChange === "function"
        ? options.onLocationChange
        : function () {};

    var map = null;
    var marker = null;

    function isAvailable() {
      return (
        mapNode &&
        typeof window.L !== "undefined"
      );
    }

    function createMap() {
      if (map) {
        return true;
      }

      if (!isAvailable()) {
        return false;
      }

      mapNode.hidden = false;

      map = L.map(mapNode).setView(
        [47.4, 9.3],
        8
      );

      L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          maxZoom: 19,

          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }
      ).addTo(map);

      map.on("click", function (event) {
        setMarker(
          event.latlng.lat,
          event.latlng.lng,
          false
        );

        onLocationChange({
          latitude: event.latlng.lat,
          longitude: event.latlng.lng,
          source: "map"
        });
      });

      return true;
    }

    function refreshSize() {
      if (!map) return;

      window.setTimeout(
        function () {
          map.invalidateSize();
        },
        50
      );
    }

    function show() {
      if (!createMap()) {
        return false;
      }

      mapNode.hidden = false;

      refreshSize();

      return true;
    }

    function hide() {
      if (mapNode) {
        mapNode.hidden = true;
      }
    }

    function setMarker(
      latitude,
      longitude,
      centerMap
    ) {
      if (!show()) {
        return;
      }

      var position = [
        latitude,
        longitude
      ];

      if (!marker) {
        marker = L.marker(
          position,
          {
            draggable: true
          }
        ).addTo(map);

        marker.on(
          "dragend",
          function () {
            var position =
              marker.getLatLng();

            onLocationChange({
              latitude: position.lat,
              longitude: position.lng,
              source: "map"
            });
          }
        );
      } else {
        marker.setLatLng(position);
      }

      if (centerMap !== false) {
        map.setView(
          position,
          15
        );
      }
    }

    function setLocation(
      latitude,
      longitude
    ) {
      setMarker(
        Number(latitude),
        Number(longitude),
        true
      );
    }

    return {
      show: show,
      hide: hide,
      setLocation: setLocation
    };
  }

  window.GardenHubGardenLocationMap = {
    create: createGardenLocationMap
  };
})();