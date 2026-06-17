import { daysToWorkHours, formatWorkHours } from "./durationUtils";

export default function StatDaysPill({ days, label, className = "" }) {
  const hoursLabel = formatWorkHours(daysToWorkHours(days));
  return (
    <span className={`stat-pill stat-pill-days${className ? ` ${className}` : ""}`}>
      <span className="stat-pill-main">
        <strong>{days}</strong> {label}
      </span>
      <span className="stat-pill-sub">{hoursLabel} work hours</span>
    </span>
  );
}
