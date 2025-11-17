"""
Deviation Detection Module
Detects temporal anomalies and behavioral drift in agent metrics
"""

from typing import Dict, List, Any
import statistics
from collections import defaultdict
from .otel_parser import identify_business_metrics


def detect_deviations(
    parsed_data: Dict[str, Any],
    threshold: float = 2.0,
    agent_purpose: str = ""
) -> List[Dict[str, Any]]:
    """
    Detect temporal deviations in agent behavior

    Args:
        parsed_data: Parsed OTEL data from parse_otel_data()
        threshold: Number of standard deviations to consider anomalous
        agent_purpose: Agent's intended purpose (for context)

    Returns:
        List of deviation findings with severity, description, and evidence
    """
    deviations = []

    # Identify business-relevant metrics
    business_metrics = identify_business_metrics(parsed_data, agent_purpose)

    # Focus on top metrics by relevance
    top_metrics = [m for m in business_metrics if m["relevance_score"] > 0.5][:10]

    if not top_metrics:
        # Fallback: analyze all numeric metrics
        top_metrics = [
            {
                "name": metric_name,
                "relevance_score": 0.5,
                "sample_count": len(values),
                "mean": statistics.mean(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0
            }
            for metric_name, values in parsed_data["metrics"].items()
            if len(values) >= 5
        ]

    # Analyze temporal deviations for each metric
    for metric_info in top_metrics:
        metric_name = metric_info["name"]
        metric_values = parsed_data["metrics"][metric_name]

        # Temporal deviation analysis
        temporal_deviations = _detect_temporal_drift(
            metric_name,
            metric_values,
            parsed_data["temporal_groups"],
            threshold,
            agent_purpose
        )
        deviations.extend(temporal_deviations)

        # Sudden spike/drop detection
        spike_deviations = _detect_sudden_changes(
            metric_name,
            metric_values,
            parsed_data["traces"],
            threshold,
            agent_purpose
        )
        deviations.extend(spike_deviations)

    # Sort by severity
    deviations.sort(key=lambda x: x["severity_score"], reverse=True)

    return deviations


def _detect_temporal_drift(
    metric_name: str,
    metric_values: List[float],
    temporal_groups: Dict[str, Dict[str, List[Dict]]],
    threshold: float,
    agent_purpose: str
) -> List[Dict[str, Any]]:
    """
    Detect gradual drift in metrics over time periods

    Looks for:
    - Increasing/decreasing trends
    - Significant changes between time periods
    """
    deviations = []

    # Analyze by week (most common business timeframe)
    week_groups = temporal_groups.get("by_week", {})
    if not week_groups or len(week_groups) < 2:
        # Try day groups
        week_groups = temporal_groups.get("by_day", {})

    if not week_groups or len(week_groups) < 2:
        return deviations

    # Calculate metric values for each time period
    period_stats = {}
    for period_key in sorted(week_groups.keys()):
        traces = week_groups[period_key]
        period_values = []

        for trace in traces:
            attrs = trace.get("attributes", {})
            if metric_name in attrs:
                val = attrs[metric_name]
                if isinstance(val, (int, float)):
                    period_values.append(float(val))

        if period_values:
            period_stats[period_key] = {
                "mean": statistics.mean(period_values),
                "stdev": statistics.stdev(period_values) if len(period_values) > 1 else 0,
                "count": len(period_values),
                "values": period_values
            }

    if len(period_stats) < 2:
        return deviations

    # Check for monotonic trends (always increasing or decreasing)
    period_means = [stats["mean"] for stats in period_stats.values()]
    is_increasing = all(period_means[i] <= period_means[i+1] for i in range(len(period_means)-1))
    is_decreasing = all(period_means[i] >= period_means[i+1] for i in range(len(period_means)-1))

    if is_increasing or is_decreasing:
        # Calculate trend strength
        first_mean = period_means[0]
        last_mean = period_means[-1]
        percent_change = ((last_mean - first_mean) / first_mean * 100) if first_mean != 0 else 0

        # Check if change is significant
        overall_stdev = statistics.stdev(metric_values) if len(metric_values) > 1 else 0
        change_magnitude = abs(last_mean - first_mean)

        if change_magnitude > threshold * overall_stdev:
            direction = "increasing" if is_increasing else "decreasing"
            severity = _calculate_severity(percent_change, threshold)

            deviations.append({
                "type": "temporal_drift",
                "metric": metric_name,
                "severity": severity,
                "severity_score": severity,
                "description": f"{metric_name} shows consistent {direction} trend over time",
                "details": {
                    "direction": direction,
                    "percent_change": round(percent_change, 2),
                    "first_period": list(period_stats.keys())[0],
                    "last_period": list(period_stats.keys())[-1],
                    "first_mean": round(first_mean, 2),
                    "last_mean": round(last_mean, 2),
                    "periods_analyzed": len(period_stats)
                },
                "alignment_concern": _assess_alignment_concern(
                    metric_name, direction, percent_change, agent_purpose
                ),
                "evidence": period_stats
            })

    # Check for significant period-to-period changes
    period_keys = sorted(period_stats.keys())
    for i in range(len(period_keys) - 1):
        current_key = period_keys[i]
        next_key = period_keys[i + 1]

        current_stats = period_stats[current_key]
        next_stats = period_stats[next_key]

        mean_change = next_stats["mean"] - current_stats["mean"]
        pooled_stdev = statistics.mean([current_stats["stdev"], next_stats["stdev"]])

        if pooled_stdev > 0:
            z_score = abs(mean_change / pooled_stdev)

            if z_score > threshold:
                percent_change = (mean_change / current_stats["mean"] * 100) if current_stats["mean"] != 0 else 0
                severity = _calculate_severity(percent_change, threshold)

                deviations.append({
                    "type": "period_change",
                    "metric": metric_name,
                    "severity": severity,
                    "severity_score": severity,
                    "description": f"Significant change in {metric_name} between periods",
                    "details": {
                        "from_period": current_key,
                        "to_period": next_key,
                        "from_mean": round(current_stats["mean"], 2),
                        "to_mean": round(next_stats["mean"], 2),
                        "change": round(mean_change, 2),
                        "percent_change": round(percent_change, 2),
                        "z_score": round(z_score, 2)
                    },
                    "alignment_concern": _assess_alignment_concern(
                        metric_name,
                        "increasing" if mean_change > 0 else "decreasing",
                        percent_change,
                        agent_purpose
                    )
                })

    return deviations


def _detect_sudden_changes(
    metric_name: str,
    metric_values: List[float],
    traces: List[Dict],
    threshold: float,
    agent_purpose: str
) -> List[Dict[str, Any]]:
    """
    Detect sudden spikes or drops in metric values
    """
    deviations = []

    if len(metric_values) < 10:
        return deviations

    mean = statistics.mean(metric_values)
    stdev = statistics.stdev(metric_values)

    if stdev == 0:
        return deviations

    # Find outliers
    outliers = []
    for trace in traces:
        attrs = trace.get("attributes", {})
        if metric_name in attrs:
            value = attrs[metric_name]
            if isinstance(value, (int, float)):
                z_score = (value - mean) / stdev
                if abs(z_score) > threshold:
                    outliers.append({
                        "value": value,
                        "z_score": z_score,
                        "trace": trace
                    })

    # Report if significant number of outliers
    if len(outliers) > len(metric_values) * 0.05:  # >5% outliers
        severity = _calculate_severity(len(outliers) / len(metric_values) * 100, threshold)

        deviations.append({
            "type": "outliers",
            "metric": metric_name,
            "severity": severity,
            "severity_score": severity,
            "description": f"Multiple outlier values detected for {metric_name}",
            "details": {
                "outlier_count": len(outliers),
                "total_count": len(metric_values),
                "outlier_percentage": round(len(outliers) / len(metric_values) * 100, 2),
                "mean": round(mean, 2),
                "stdev": round(stdev, 2),
                "max_z_score": round(max(abs(o["z_score"]) for o in outliers), 2)
            },
            "alignment_concern": f"Unusual variability in {metric_name} may indicate inconsistent behavior"
        })

    return deviations


def _calculate_severity(percent_change: float, threshold: float) -> float:
    """
    Calculate severity score (0-1) based on magnitude of change

    Higher percent change and lower threshold = higher severity
    """
    abs_change = abs(percent_change)

    # Normalize based on threshold
    severity = min(abs_change / (threshold * 50), 1.0)  # 100% change at 2σ = severity 1.0

    return severity


def _assess_alignment_concern(
    metric_name: str,
    direction: str,
    percent_change: float,
    agent_purpose: str
) -> str:
    """
    Assess whether the deviation represents an alignment concern

    Provides context on why this deviation matters for the agent's purpose
    """
    metric_lower = metric_name.lower()
    purpose_lower = agent_purpose.lower() if agent_purpose else ""

    concerns = []

    # Financial metrics
    if any(word in metric_lower for word in ["refund", "commission", "cost", "payment", "fee"]):
        if direction == "increasing":
            concerns.append(f"Rising {metric_name} may indicate agent is becoming more generous with approvals")
        else:
            concerns.append(f"Declining {metric_name} may indicate agent is becoming more restrictive")

    # Quality/scoring metrics
    if any(word in metric_lower for word in ["score", "rating", "quality", "satisfaction"]):
        if direction == "decreasing":
            concerns.append(f"Declining {metric_name} suggests degrading performance")
        else:
            concerns.append(f"Improving {metric_name} is positive but verify legitimacy")

    # Error/failure metrics
    if any(word in metric_lower for word in ["error", "failure", "reject"]):
        if direction == "increasing":
            concerns.append(f"Rising {metric_name} indicates growing problems")

    # Time/duration metrics
    if any(word in metric_lower for word in ["duration", "time", "latency"]):
        if direction == "increasing":
            concerns.append(f"Increasing {metric_name} suggests agent is slowing down")

    # Purpose-specific concerns
    if purpose_lower:
        if "customer" in purpose_lower and "refund" in metric_lower:
            concerns.append("Deviation may affect customer satisfaction and business costs")
        if "hiring" in purpose_lower or "screening" in purpose_lower:
            if "score" in metric_lower:
                concerns.append("Changes in scoring may reflect bias or policy drift")

    if concerns:
        return " | ".join(concerns)
    else:
        return f"{direction.capitalize()} trend of {percent_change:.1f}% detected - verify this aligns with intended agent behavior"
