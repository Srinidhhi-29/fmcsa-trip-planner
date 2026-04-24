const statusRows = [
  ["OFF_DUTY", "Off Duty"],
  ["SLEEPER_BERTH", "Sleeper Berth"],
  ["DRIVING", "Driving"],
  ["ON_DUTY", "On Duty"]
];

const statusClass = {
  OFF_DUTY: "off-duty",
  SLEEPER_BERTH: "sleeper",
  DRIVING: "driving",
  ON_DUTY: "on-duty"
};

export default function LogSheet({ log }) {
  return (
    <section className="log-sheet">
      <div className="log-header">
        <div>
          <p className="section-kicker">Driver daily log</p>
          <h2>Day {log.day}</h2>
        </div>
        <time>{log.date}</time>
      </div>

      <div className="log-grid" aria-label={`Driver log for day ${log.day}`}>
        <div className="hour-row">
          <span />
          {Array.from({ length: 24 }).map((_, hour) => (
            <small key={hour}>{hour === 0 ? "Mid" : hour === 12 ? "Noon" : hour}</small>
          ))}
        </div>

        {statusRows.map(([status, label]) => (
          <div className="status-row" key={status}>
            <strong>{label}</strong>
            <div className="track">
              {log.segments
                .filter((segment) => segment.status === status)
                .map((segment, index) => (
                  <span
                    className={`segment ${statusClass[status]}`}
                    key={`${status}-${index}`}
                    style={{
                      left: `${(segment.start / 24) * 100}%`,
                      width: `${((segment.end - segment.start) / 24) * 100}%`
                    }}
                    title={`${segment.label}: ${segment.start} - ${segment.end}`}
                  />
                ))}
            </div>
          </div>
        ))}
      </div>

      <div className="totals-row">
        {statusRows.map(([status, label]) => (
          <span key={status}>
            {label}: <strong>{log.totals[status]?.toFixed(2)}h</strong>
          </span>
        ))}
      </div>

      <div className="remarks">
        <strong>Remarks</strong>
        {log.segments
          .filter((segment) => segment.remarks && segment.remarks !== "Off duty")
          .map((segment, index) => (
            <p key={index}>
              {formatHour(segment.start)} - {formatHour(segment.end)}: {segment.remarks}
              <span className="inline-rule">{segment.rule_code}</span>
            </p>
          ))}
      </div>
    </section>
  );
}

function formatHour(hour) {
  const totalMinutes = Math.round(hour * 60);
  const hh = String(Math.floor(totalMinutes / 60)).padStart(2, "0");
  const mm = String(totalMinutes % 60).padStart(2, "0");
  return `${hh}:${mm}`;
}
