import { GitBranch } from "lucide-react";

export default function DecisionTrace({ decisions }) {
  if (!decisions?.length) {
    return null;
  }
  const decisionsByDay = decisions.reduce((groups, decision) => {
    const key = `Day ${decision.day}`;
    return { ...groups, [key]: [...(groups[key] || []), decision] };
  }, {});

  return (
    <section className="decision-section">
      <div className="section-heading">
        <p className="section-kicker">Reasoning engine</p>
        <h2>Why the plan changed</h2>
      </div>
      <div className="decision-list">
        {Object.entries(decisionsByDay).map(([day, dayDecisions], dayIndex) => (
          <details className="decision-day" key={day} open={dayIndex === 0}>
            <summary>
              <span>{day}</span>
              <small>{dayDecisions.length} decisions</small>
            </summary>
            {dayDecisions.map((decision, index) => (
              <article className="decision-item" key={`${decision.rule_code}-${index}`}>
                <span>
                  <GitBranch size={17} />
                </span>
                <div>
                  <strong>{decision.rule_code}</strong>
                  <p>{decision.message}</p>
                  <small>{decision.consequence}</small>
                </div>
                <em>{formatHour(decision.hour)}</em>
              </article>
            ))}
          </details>
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
