import { Coffee, Fuel, MapPin, PackageCheck, PackageOpen, RotateCcw } from "lucide-react";

const icons = {
  pickup: PackageOpen,
  dropoff: PackageCheck,
  break: Coffee,
  fuel: Fuel,
  rest: MapPin,
  cycle_reset: RotateCcw
};

export default function StopList({
  stops,
  hoveredStopKey,
  activeStopKey,
  onHoverStop,
  onSelectStop,
  selectedDay,
  setSelectedDay
}) {
  const stopsByDay = stops.reduce((groups, stop) => {
    const key = `Day ${stop.day}`;
    return { ...groups, [key]: [...(groups[key] || []), stop] };
  }, {});

  return (
    <section className="stops-section">
      <div className="section-heading">
        <p className="section-kicker">Events</p>
        <h2>Stops and duty changes</h2>
      </div>
      {stops.length === 0 ? (
        <p className="empty-state">Submit a trip to see generated stops.</p>
      ) : (
        <div className="stop-list">
          {Object.entries(stopsByDay).map(([day, dayStops], index) => (
            <details className="day-group" key={day} open={index === 0}>
              <summary>
                <span>{day}</span>
                <button
                  className={selectedDay === dayStops[0]?.day ? "active" : ""}
                  type="button"
                  onClick={(event) => {
                    event.preventDefault();
                    setSelectedDay(selectedDay === dayStops[0]?.day ? null : dayStops[0]?.day);
                  }}
                >
                  {selectedDay === dayStops[0]?.day ? `Day ${dayStops[0]?.day} - Active` : "Show on map"}
                </button>
                <small>{dayStops.length} events</small>
              </summary>
              {dayStops.map((stop, stopIndex) => {
                const Icon = icons[stop.type] || MapPin;
                const stopKey = `${stop.day}-${stop.type}-${stop.mile_marker}-${stop.hour}`;
                return (
                  <article
                    className={`stop-item ${hoveredStopKey === stopKey || activeStopKey === stopKey ? "active" : ""}`}
                    onClick={() => onSelectStop(activeStopKey === stopKey ? "" : stopKey)}
                    key={stopKey}
                    onMouseEnter={() => onHoverStop(stopKey)}
                    onMouseLeave={() => onHoverStop("")}
                  >
                    <span className={`stop-icon ${stop.type}`}>
                      <Icon size={18} />
                    </span>
                    <div>
                      <strong>{stop.label}</strong>
                      <p>{stop.remarks}</p>
                      <span className="rule-pill">{stop.rule_code}</span>
                    </div>
                    <small>
                      {formatHour(stop.hour)} / mile {stop.mile_marker}
                    </small>
                  </article>
                );
              })}
            </details>
          ))}
        </div>
      )}
    </section>
  );
}

function formatHour(hour) {
  const totalMinutes = Math.round(hour * 60);
  const hh = String(Math.floor(totalMinutes / 60)).padStart(2, "0");
  const mm = String(totalMinutes % 60).padStart(2, "0");
  return `${hh}:${mm}`;
}
