import { useEffect, useState } from "react";
import { AlertTriangle, Clock, MapPinned, Route } from "lucide-react";
import { listTrips, planTrip } from "./services/api";
import TripForm from "./components/TripForm";
import MapView from "./components/MapView";
import StopList from "./components/StopList";
import LogSheet from "./components/LogSheet";
import CompliancePanel from "./components/CompliancePanel";
import DecisionTrace from "./components/DecisionTrace";
import TripHistory from "./components/TripHistory";

export default function App() {
  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [selectedDay, setSelectedDay] = useState(null);
  const [hoveredStopKey, setHoveredStopKey] = useState("");
  const [activeStopKey, setActiveStopKey] = useState("");



  async function refreshHistory() {
    try {
      setHistory(await listTrips());
    } catch {
      setHistory([]);
    }
  }

  async function handleSubmit(formValues) {
    setLoading(true);
    setError("");
    try {
      const result = await planTrip(formValues);
      setTrip(result);
      setSelectedDay(null);
      setHoveredStopKey("");
      setActiveStopKey("");
      refreshHistory();
    } catch (requestError) {
      const message =
        requestError.response?.data?.detail ||
        formatFieldErrors(requestError.response?.data) ||
        "Unable to plan this trip. Check the backend server and try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-band">
        <div>
          <p className="eyebrow">FMCSA Hours of Service</p>
          <h1>Trip Planner and ELD Log Generator</h1>
          <p className="hero-copy">
            This planner automatically inserts required breaks, rest periods, and fuel stops based on FMCSA HOS rules.
          </p>
        </div>
        <div className="hero-metrics">
          <span><Clock size={18} /> 11 hr drive limit</span>
          <span><Route size={18} /> 70 hr / 8 day cycle</span>
          <span><MapPinned size={18} /> Route and stops</span>
        </div>
      </section>

      <section className="workspace">
        <aside className="planner-panel">
          <TripForm onSubmit={handleSubmit} loading={loading} />
          {error && (
            <div className="error-banner">
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}
          {trip?.summary && (
            <div className="summary-grid">
              <Metric label="Miles" value={trip.summary.distance_miles} />
              <Metric label="Drive hrs" value={trip.summary.estimated_driving_hours} />
              <Metric label="Days" value={trip.summary.trip_days} />
              <Metric label="Cycle end" value={trip.summary.ending_cycle_hours} />
            </div>
          )}
          {!trip ? (
            <p className="empty-state">Plan a trip to see history.</p>
          ) : (
            history.length > 0 && <TripHistory trips={history} />
          )}         
        </aside>
        <section className="results-panel">
          <CompliancePanel compliance={trip?.compliance} summary={trip?.summary} />
          <MapView
            route={trip?.route}
            stops={trip?.stops || []}
            selectedDay={selectedDay}
            setSelectedDay={setSelectedDay}
            hoveredStopKey={hoveredStopKey}
            activeStopKey={activeStopKey}
            onHoverStop={setHoveredStopKey}
            onSelectStop={setActiveStopKey}
          />
          <StopList
            stops={trip?.stops || []}
            hoveredStopKey={hoveredStopKey}
            activeStopKey={activeStopKey}
            onHoverStop={setHoveredStopKey}
            onSelectStop={setActiveStopKey}
            selectedDay={selectedDay}
            setSelectedDay={setSelectedDay}
          />
          <DecisionTrace decisions={trip?.decisions || []} />
          <div className="logs-stack">
            {(trip?.logs || []).map((log) => (
              <LogSheet key={log.day} log={log} />
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

function formatFieldErrors(data) {
  if (!data || typeof data !== "object") {
    return "";
  }
  return Object.entries(data)
    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(", ") : messages}`)
    .join(" ");
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
