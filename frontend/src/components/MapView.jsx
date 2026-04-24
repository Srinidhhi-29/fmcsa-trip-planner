import { useEffect } from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";

const defaultCenter = [39.5, -95.2];
const stopColors = {
  pickup: "#2563eb",
  dropoff: "#2563eb",
  break: "#f59e0b",
  fuel: "#16a34a",
  rest: "#dc2626",
  cycle_reset: "#7c3aed"
};
const stopGlyphs = {
  pickup: "PU",
  dropoff: "DO",
  break: "BR",
  fuel: "FL",
  rest: "SB",
  cycle_reset: "34"
};

function markerIcon(type, isHighlighted = false) {
  const color = stopColors[type] || "#f97316";
  return L.divIcon({
    className: `custom-stop-marker ${isHighlighted ? "highlighted" : ""}`,
    html: `<span style="background:${color}">${stopGlyphs[type] || "EV"}</span>`,
    iconSize: isHighlighted ? [34, 34] : [28, 28],
    iconAnchor: isHighlighted ? [17, 17] : [14, 14]
  });
}

export default function MapView({
  route,
  stops,
  selectedDay,
  setSelectedDay,
  hoveredStopKey,
  activeStopKey,
  onHoverStop,
  onSelectStop
}) {
  const path = route?.path || [];
  const center = path.length ? path[Math.floor(path.length / 2)] : defaultCenter;
  const days = [...new Set(stops.map((stop) => stop.day))];
  const visibleStops = selectedDay ? stops.filter((stop) => stop.day === selectedDay) : stops;
  const highlightedPath = selectedDay ? pathForDay(path, stops, selectedDay, route?.distance_miles) : path;

  return (
    <section className="map-section">
      <div className="map-heading">
        <div>
          <p className="section-kicker">Route map</p>
          <h2>{route ? `Route Map - ${route.distance_miles} miles` : "Enter trip details and click Plan Trip"}</h2>
          {!route && (
            <p className="map-helper">Generate a compliant route with required breaks, rests, fuel stops, and daily logs.</p>
          )}
        </div>
        {days.length > 0 && (
          <div className="day-filter" aria-label="Filter route by day">
            <button className={!selectedDay ? "active" : ""} onClick={() => setSelectedDay(null)}>All</button>
            {days.map((day) => (
              <button
                className={selectedDay === day ? "active" : ""}
                key={day}
                onClick={() => setSelectedDay(day)}
              >
                Day {day}{selectedDay === day ? " - Active" : ""}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="map-frame">
        <MapContainer center={center} zoom={5} scrollWheelZoom className="map">
          <FitRoute path={highlightedPath.length ? highlightedPath : path} />
          <ResetMapButton path={path} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {path.length > 0 && selectedDay && <Polyline positions={path} color="#9aa9bd" weight={4} opacity={0.45} />}
          {highlightedPath.length > 0 && (
            <Polyline positions={highlightedPath} color="#1f6feb" weight={selectedDay ? 7 : 5} opacity={0.95} />
          )}
          {visibleStops.map((stop) => {
            const stopKey = stopKeyFor(stop);
            const isHighlighted = hoveredStopKey === stopKey || activeStopKey === stopKey;
            return (
            <Marker
              eventHandlers={{
                click: () => onSelectStop(stopKey),
                mouseout: () => onHoverStop(""),
                mouseover: () => onHoverStop(stopKey)
              }}
              key={stopKey}
              position={stop.coordinates}
              icon={markerIcon(stop.type, isHighlighted)}
            >
              <Popup>
                <div className="map-popup">
                  <strong>{stop.label}</strong>
                  <span>{stop.remarks}</span>
                  <small>Day {stop.day}, {formatHour(stop.hour)} / mile {stop.mile_marker}</small>
                  <em>{stop.rule_code}</em>
                </div>
              </Popup>
            </Marker>
          );
          })}
        </MapContainer>
        <div className="map-legend" aria-label="Map legend">
          <span><i className="legend-dot pickup" /> Pickup / dropoff</span>
          <span><i className="legend-dot break" /> 30-min break</span>
          <span><i className="legend-dot fuel" /> Fuel stop</span>
          <span><i className="legend-dot rest" /> Rest / reset</span>
        </div>
      </div>
    </section>
  );
}

function FitRoute({ path }) {
  const map = useMap();
  useEffect(() => {
    if (path.length > 1) {
      map.fitBounds(path, { padding: [36, 36] });
    }
  }, [map, path]);
  return null;
}

function ResetMapButton({ path }) {
  const map = useMap();
  if (path.length < 2) {
    return null;
  }
  return (
    <button className="reset-map-button" onClick={() => map.fitBounds(path, { padding: [36, 36] })}>
      Reset view
    </button>
  );
}

function pathForDay(path, stops, day, distanceMiles) {
  if (!path.length || !distanceMiles) {
    return [];
  }
  const dayStops = stops.filter((stop) => stop.day === day);
  if (!dayStops.length) {
    return path;
  }
  const minMile = Math.max(0, Math.min(...dayStops.map((stop) => stop.mile_marker)) - 60);
  const maxMile = Math.min(distanceMiles, Math.max(...dayStops.map((stop) => stop.mile_marker)) + 60);
  const startIndex = Math.max(0, Math.floor((minMile / distanceMiles) * (path.length - 1)));
  const endIndex = Math.min(path.length - 1, Math.ceil((maxMile / distanceMiles) * (path.length - 1)));
  return path.slice(startIndex, endIndex + 1);
}

function stopKeyFor(stop) {
  return `${stop.day}-${stop.type}-${stop.mile_marker}-${stop.hour}`;
}

function formatHour(hour) {
  const totalMinutes = Math.round(hour * 60);
  const hh = String(Math.floor(totalMinutes / 60)).padStart(2, "0");
  const mm = String(totalMinutes % 60).padStart(2, "0");
  return `${hh}:${mm}`;
}
