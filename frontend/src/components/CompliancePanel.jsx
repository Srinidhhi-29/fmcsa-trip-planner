import { AlertTriangle, CheckCircle2, ShieldCheck, XCircle } from "lucide-react";

export default function CompliancePanel({ compliance, summary }) {
  if (!compliance || !summary) {
    return (
      <section className="compliance-panel empty-compliance">
        <ShieldCheck size={22} />
        <div>
          <strong>Compliance engine ready</strong>
          <p>Submit a trip to validate HOS limits and cycle availability.</p>
        </div>
      </section>
    );
  }

  const isValid = compliance.is_compliant;
  const hasWarnings = compliance.warnings.length > 0;
  const StatusIcon = isValid ? CheckCircle2 : XCircle;

  return (
    <section className={`compliance-panel ${isValid ? "valid" : "invalid"}`}>
      <div className="compliance-status">
        <StatusIcon size={24} />
        <div>
          <p className="section-kicker">Compliance status</p>
          <h2>{statusText(compliance.status)}</h2>
        </div>
      </div>

      <div className="summary-grid wide">
        <Metric label="Total stops" value={summary.total_stops} />
        <Metric label="Fuel stops" value={summary.fuel_stops} />
        <Metric label="Breaks" value={summary.breaks} />
        <Metric label="Rests/restarts" value={summary.rests} />
        <Metric label="Remaining cycle" value={`${summary.remaining_cycle_hours}h`} />
        <Metric label="Ending cycle" value={`${summary.ending_cycle_hours}h`} />
      </div>

      {hasWarnings && (
        <div className="warning-list">
          {compliance.warnings.map((warning) => (
            <p key={warning}>
              <AlertTriangle size={16} />
              {warning}
            </p>
          ))}
        </div>
      )}

      <div className="checks-list">
        {compliance.checks.map((check) => (
          <span key={check.name} className={check.passed ? "passed" : "failed"}>
            {check.passed ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
            {check.name}: {check.value}h
          </span>
        ))}
      </div>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function statusText(status) {
  if (status === "VALID_WITH_WARNINGS") {
    return "Valid with cycle warning";
  }
  if (status === "VIOLATION") {
    return "Violation detected";
  }
  return "Valid HOS plan";
}

