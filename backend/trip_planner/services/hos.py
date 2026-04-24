from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .map_service import AVERAGE_SPEED_MPH, coordinate_at_fraction

MAX_DAILY_DRIVING_HOURS = 11.0
MAX_DUTY_WINDOW_HOURS = 14.0
BREAK_AFTER_DRIVING_HOURS = 8.0
BREAK_DURATION_HOURS = 0.5
REQUIRED_REST_HOURS = 10.0
CYCLE_LIMIT_HOURS = 70.0
PICKUP_DURATION_HOURS = 1.0
DROPOFF_DURATION_HOURS = 1.0
FUEL_INTERVAL_MILES = 1000.0
FUEL_DURATION_HOURS = 0.5

STATUS_LABELS = {
    "OFF_DUTY": "Off Duty",
    "SLEEPER_BERTH": "Sleeper Berth",
    "DRIVING": "Driving",
    "ON_DUTY": "On Duty (not driving)",
}


@dataclass
class Segment:
    day: int
    start: float
    end: float
    status: str
    remarks: str
    rule_code: str = "INFO"

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "label": STATUS_LABELS[self.status],
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "duration": round(self.end - self.start, 2),
            "remarks": self.remarks,
            "rule_code": self.rule_code,
        }


def simulate_trip(
    distance: float,
    current_cycle_hours: int,
    route_path: list[list[float]] | None = None,
    pickup_location: str = "Pickup",
    dropoff_location: str = "Dropoff",
) -> dict:
    if distance <= 0:
        raise ValueError("Distance must be greater than zero.")
    if current_cycle_hours < 0 or current_cycle_hours > CYCLE_LIMIT_HOURS:
        raise ValueError("Current cycle hours must be between 0 and 70.")

    state = {
        "day": 1,
        "clock": 0.0,
        "duty_window_used": 0.0,
        "driving_today": 0.0,
        "driving_since_break": 0.0,
        "cycle_used": float(current_cycle_hours),
        "miles_driven": 0.0,
    }
    segments: list[Segment] = []
    stops: list[dict] = []
    decision_trace: list[dict] = []
    warnings: list[str] = []
    route_path = route_path or []

    if current_cycle_hours >= 60:
        warnings.append(
            "Driver is near the 70-hour cycle limit. The planner will force a 34-hour restart if legal time runs out."
        )

    def add_decision(rule_code: str, message: str, consequence: str):
        decision_trace.append(
            {
                "rule_code": rule_code,
                "message": message,
                "consequence": consequence,
                "day": state["day"],
                "hour": round(state["clock"], 2),
                "mile_marker": round(state["miles_driven"], 1),
            }
        )

    def add_segment(
        duration: float,
        status: str,
        remarks: str,
        advances_cycle: bool = True,
        rule_code: str = "INFO",
    ):
        remaining = duration
        while remaining > 0:
            available_today = 24 - state["clock"]
            chunk = min(remaining, available_today)
            if chunk <= 0:
                state["day"] += 1
                state["clock"] = 0.0
                continue
            segments.append(
                Segment(
                    day=state["day"],
                    start=state["clock"],
                    end=state["clock"] + chunk,
                    status=status,
                    remarks=remarks,
                    rule_code=rule_code,
                )
            )
            state["clock"] += chunk
            if status in {"DRIVING", "ON_DUTY"}:
                state["duty_window_used"] += chunk
                if advances_cycle:
                    state["cycle_used"] += chunk
            if status == "DRIVING":
                state["driving_today"] += chunk
                state["driving_since_break"] += chunk
            remaining -= chunk
            if state["clock"] >= 24 and remaining > 0:
                state["day"] += 1
                state["clock"] = 0.0

    def add_stop(
        stop_type: str,
        label: str,
        remarks: str,
        location: str | None = None,
        rule_code: str = "INFO",
        required: bool = True,
    ):
        fraction = state["miles_driven"] / distance if distance else 0
        stop = {
            "type": stop_type,
            "label": label,
            "day": state["day"],
            "hour": round(state["clock"], 2),
            "mile_marker": round(state["miles_driven"], 1),
            "coordinates": coordinate_at_fraction(route_path, fraction),
            "remarks": remarks,
            "reason": remarks,
            "rule_code": rule_code,
            "required": required,
        }
        if location:
            stop["location"] = location
        stops.append(stop)

    def start_new_driving_day(reason: str):
        add_decision("HOS_DAILY_OR_WINDOW_LIMIT", reason, "Driving is blocked until a 10-hour rest is completed.")
        add_stop("rest", "10-hour rest", reason, rule_code="HOS_10_HOUR_REST")
        add_segment(
            REQUIRED_REST_HOURS,
            "SLEEPER_BERTH",
            reason,
            advances_cycle=False,
            rule_code="HOS_10_HOUR_REST",
        )
        if state["clock"] >= 24:
            state["day"] += 1
            state["clock"] = 0.0
        elif state["clock"] > 0:
            add_segment(
                24 - state["clock"],
                "OFF_DUTY",
                "Off duty until next log day",
                advances_cycle=False,
                rule_code="LOG_24_HOUR_FILL",
            )
            state["day"] += 1
            state["clock"] = 0.0
        state["duty_window_used"] = 0.0
        state["driving_today"] = 0.0
        state["driving_since_break"] = 0.0

    def ensure_cycle_available(required_hours: float):
        if state["cycle_used"] + required_hours <= CYCLE_LIMIT_HOURS:
            return
        add_decision(
            "HOS_70_8_CYCLE",
            "70-hour / 8-day cycle limit would be exceeded.",
            "Trip is paused and a 34-hour restart is inserted before more on-duty work.",
        )
        add_stop(
            "cycle_reset",
            "34-hour restart",
            "Required because the 70-hour / 8-day cycle would be exceeded",
            rule_code="HOS_70_8_CYCLE",
        )
        add_segment(
            34.0,
            "OFF_DUTY",
            "34-hour restart to restore 70-hour cycle",
            advances_cycle=False,
            rule_code="HOS_70_8_CYCLE",
        )
        state["cycle_used"] = 0.0
        state["duty_window_used"] = 0.0
        state["driving_today"] = 0.0
        state["driving_since_break"] = 0.0
        if state["clock"] > 14:
            state["day"] += 1
            state["clock"] = 0.0

    add_stop(
        "pickup",
        "Pickup",
        "Pickup is logged as on-duty not driving for 1 hour",
        pickup_location,
        rule_code="ON_DUTY_PICKUP",
    )
    ensure_cycle_available(PICKUP_DURATION_HOURS)
    add_segment(
        PICKUP_DURATION_HOURS,
        "ON_DUTY",
        "Pickup paperwork and loading",
        rule_code="ON_DUTY_PICKUP",
    )

    next_fuel_mile = FUEL_INTERVAL_MILES
    total_driving_hours = distance / AVERAGE_SPEED_MPH
    driving_remaining = total_driving_hours

    while driving_remaining > 0:
        ensure_cycle_available(0.25)

        if state["driving_today"] >= MAX_DAILY_DRIVING_HOURS:
            start_new_driving_day("Daily 11-hour driving limit reached")
            continue

        if state["duty_window_used"] >= MAX_DUTY_WINDOW_HOURS:
            start_new_driving_day("14-hour duty window reached")
            continue

        if state["driving_since_break"] >= BREAK_AFTER_DRIVING_HOURS:
            add_decision(
                "HOS_30_MIN_BREAK",
                "Driver has reached 8 hours of cumulative driving since last qualifying break.",
                "Driving is blocked until a 30-minute off-duty break is completed.",
            )
            add_stop(
                "break",
                "30-minute break",
                "Required after 8 hours of driving per FMCSA 30-minute break rule",
                rule_code="HOS_30_MIN_BREAK",
            )
            add_segment(
                BREAK_DURATION_HOURS,
                "OFF_DUTY",
                "Required 30-minute break after 8 hours driving",
                advances_cycle=False,
                rule_code="HOS_30_MIN_BREAK",
            )
            state["driving_since_break"] = 0.0
            continue

        hours_to_fuel = (
            (next_fuel_mile - state["miles_driven"]) / AVERAGE_SPEED_MPH
            if next_fuel_mile <= distance
            else driving_remaining
        )
        segment_hours = min(
            driving_remaining,
            MAX_DAILY_DRIVING_HOURS - state["driving_today"],
            MAX_DUTY_WINDOW_HOURS - state["duty_window_used"],
            BREAK_AFTER_DRIVING_HOURS - state["driving_since_break"],
            max(0.01, hours_to_fuel),
            CYCLE_LIMIT_HOURS - state["cycle_used"],
        )

        if segment_hours <= 0.01:
            if state["cycle_used"] >= CYCLE_LIMIT_HOURS:
                ensure_cycle_available(1.0)
            else:
                start_new_driving_day("No legal driving time remains in current duty window")
            continue

        limiting_rules = _limiting_rules(
            segment_hours,
            {
                "remaining_trip": driving_remaining,
                "daily_driving": MAX_DAILY_DRIVING_HOURS - state["driving_today"],
                "duty_window": MAX_DUTY_WINDOW_HOURS - state["duty_window_used"],
                "break": BREAK_AFTER_DRIVING_HOURS - state["driving_since_break"],
                "fuel": max(0.01, hours_to_fuel),
                "cycle": CYCLE_LIMIT_HOURS - state["cycle_used"],
            },
        )
        add_decision(
            "DRIVE_SEGMENT_LIMIT",
            f"Approved {round(segment_hours, 2)} hours of driving.",
            f"Segment capped by: {', '.join(limiting_rules)}.",
        )
        add_segment(segment_hours, "DRIVING", "Driving segment", rule_code="DRIVE_SEGMENT_LIMIT")
        miles_added = segment_hours * AVERAGE_SPEED_MPH
        state["miles_driven"] += miles_added
        driving_remaining -= segment_hours

        if state["miles_driven"] >= next_fuel_mile and state["miles_driven"] < distance:
            add_decision(
                "FUEL_1000_MILES",
                "Truck reached a 1,000-mile fuel interval.",
                "Fueling is inserted as on-duty not-driving time before route continues.",
            )
            add_stop(
                "fuel",
                "Fuel stop",
                "Fuel stop required every 1,000 miles by project assumption",
                rule_code="FUEL_1000_MILES",
            )
            ensure_cycle_available(FUEL_DURATION_HOURS)
            add_segment(
                FUEL_DURATION_HOURS,
                "ON_DUTY",
                "Fueling and inspection",
                rule_code="FUEL_1000_MILES",
            )
            next_fuel_mile += FUEL_INTERVAL_MILES

    add_stop(
        "dropoff",
        "Dropoff",
        "Dropoff is logged as on-duty not driving for 1 hour",
        dropoff_location,
        rule_code="ON_DUTY_DROPOFF",
    )
    ensure_cycle_available(DROPOFF_DURATION_HOURS)
    if state["duty_window_used"] + DROPOFF_DURATION_HOURS > MAX_DUTY_WINDOW_HOURS:
        start_new_driving_day("Dropoff would exceed 14-hour duty window")
    add_segment(
        DROPOFF_DURATION_HOURS,
        "ON_DUTY",
        "Dropoff paperwork and unloading",
        rule_code="ON_DUTY_DROPOFF",
    )

    logs = _build_daily_logs(segments)
    compliance = _validate_compliance(logs, current_cycle_hours, state["cycle_used"], warnings)
    return {
        "stops": stops,
        "logs": logs,
        "decisions": decision_trace,
        "compliance": compliance,
        "summary": {
            "distance_miles": round(distance, 1),
            "estimated_driving_hours": round(total_driving_hours, 2),
            "trip_days": len(logs),
            "total_stops": len(stops),
            "fuel_stops": len([stop for stop in stops if stop["type"] == "fuel"]),
            "breaks": len([stop for stop in stops if stop["type"] == "break"]),
            "rests": len([stop for stop in stops if stop["type"] in {"rest", "cycle_reset"}]),
            "ending_cycle_hours": round(state["cycle_used"], 2),
            "remaining_cycle_hours": round(CYCLE_LIMIT_HOURS - state["cycle_used"], 2),
            "compliance_status": compliance["status"],
        },
    }


def _limiting_rules(segment_hours: float, limits: dict[str, float]) -> list[str]:
    labels = {
        "remaining_trip": "remaining trip distance",
        "daily_driving": "11-hour daily driving limit",
        "duty_window": "14-hour duty window",
        "break": "8-hour break threshold",
        "fuel": "1,000-mile fuel interval",
        "cycle": "70-hour cycle availability",
    }
    return [
        labels[name]
        for name, value in limits.items()
        if abs(value - segment_hours) < 0.02
    ] or ["available legal driving time"]


def _build_daily_logs(segments: list[Segment]) -> list[dict]:
    if not segments:
        return []

    start_date = date.today()
    logs: list[dict] = []
    for day in range(1, max(segment.day for segment in segments) + 1):
        day_segments = [segment.as_dict() for segment in segments if segment.day == day]
        day_segments = _fill_off_duty_gaps(day_segments)
        totals = {status: 0.0 for status in STATUS_LABELS}
        for segment in day_segments:
            totals[segment["status"]] += segment["duration"]
        logs.append(
            {
                "day": day,
                "date": (start_date + timedelta(days=day - 1)).isoformat(),
                "segments": day_segments,
                "totals": {key: round(value, 2) for key, value in totals.items()},
            }
        )
    return logs


def _validate_compliance(
    logs: list[dict],
    starting_cycle_hours: int,
    ending_cycle_hours: float,
    warnings: list[str],
) -> dict:
    violations: list[str] = []
    checks: list[dict] = []

    for log in logs:
        total_hours = round(sum(log["totals"].values()), 2)
        driving_hours = log["totals"]["DRIVING"]
        on_duty_hours = log["totals"]["DRIVING"] + log["totals"]["ON_DUTY"]

        checks.append(
            {
                "name": f"Day {log['day']} totals equal 24 hours",
                "passed": abs(total_hours - 24) <= 0.01,
                "value": total_hours,
            }
        )
        checks.append(
            {
                "name": f"Day {log['day']} driving is at or below 11 hours",
                "passed": driving_hours <= MAX_DAILY_DRIVING_HOURS,
                "value": round(driving_hours, 2),
            }
        )
        checks.append(
            {
                "name": f"Day {log['day']} duty time is at or below 14 hours",
                "passed": on_duty_hours <= MAX_DUTY_WINDOW_HOURS,
                "value": round(on_duty_hours, 2),
            }
        )

    checks.append(
        {
            "name": "Ending cycle hours remain at or below 70",
            "passed": ending_cycle_hours <= CYCLE_LIMIT_HOURS,
            "value": round(ending_cycle_hours, 2),
        }
    )

    for check in checks:
        if not check["passed"]:
            violations.append(f"{check['name']} failed with value {check['value']}.")

    status = "VALID" if not violations else "VIOLATION"
    if not violations and warnings:
        status = "VALID_WITH_WARNINGS"

    return {
        "status": status,
        "is_compliant": not violations,
        "starting_cycle_hours": starting_cycle_hours,
        "ending_cycle_hours": round(ending_cycle_hours, 2),
        "remaining_cycle_hours": round(CYCLE_LIMIT_HOURS - ending_cycle_hours, 2),
        "warnings": warnings,
        "violations": violations,
        "checks": checks,
    }


def _fill_off_duty_gaps(segments: list[dict]) -> list[dict]:
    ordered = sorted(segments, key=lambda item: item["start"])
    filled: list[dict] = []
    cursor = 0.0
    for segment in ordered:
        if segment["start"] > cursor:
            filled.append(
                {
                    "status": "OFF_DUTY",
                    "label": STATUS_LABELS["OFF_DUTY"],
                    "start": round(cursor, 2),
                    "end": segment["start"],
                    "duration": round(segment["start"] - cursor, 2),
                    "remarks": "Off duty",
                }
            )
        filled.append(segment)
        cursor = max(cursor, segment["end"])
    if cursor < 24:
        filled.append(
            {
                "status": "OFF_DUTY",
                "label": STATUS_LABELS["OFF_DUTY"],
                "start": round(cursor, 2),
                "end": 24,
                "duration": round(24 - cursor, 2),
                "remarks": "Off duty",
            }
        )
    return filled
