import { History } from "lucide-react";

export default function TripHistory({ trips }) {
  if (!trips?.length) {
    return null;
  }

  return (
    <section className="history-panel">
      <h3>
        <History size={17} />
        Recent trips
      </h3>
      <div className="history-list">
        {trips.slice(0, 5).map((trip) => (
          <article key={trip.id}>
            <strong>{trip.pickup_location} to {trip.dropoff_location}</strong>
            <span>{trip.summary?.distance_miles || "-"} mi / {trip.summary?.trip_days || "-"} days</span>
            <small>{trip.compliance?.status || "UNKNOWN"}</small>
          </article>
        ))}
      </div>
    </section>
  );
}
