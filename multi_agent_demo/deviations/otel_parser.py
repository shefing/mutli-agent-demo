"""
OpenTelemetry Data Parser
Extracts business metrics and attributes from OTEL traces
"""

from typing import Dict, List, Any, Set
from datetime import datetime
from collections import defaultdict
import re


def parse_otel_data(otel_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse OTEL data and extract structured metrics for analysis

    Args:
        otel_data: Raw OTEL data (can be in various formats)

    Returns:
        Dictionary containing:
        - traces: List of parsed trace objects
        - metrics: Extracted numeric metrics by name
        - attributes: All unique attributes found
        - temporal_groups: Traces grouped by time periods
        - parameter_groups: Traces grouped by categorical parameters
    """
    # Handle different OTEL formats
    traces = _extract_traces(otel_data)

    if not traces:
        raise ValueError("No traces found in OTEL data")

    # Aggregate spans by trace ID to merge attributes from related spans
    traces = _aggregate_spans_by_trace(traces)

    # Extract metrics and attributes
    metrics = _extract_metrics(traces)
    attributes = _extract_attributes(traces)
    temporal_groups = _group_by_time(traces)
    parameter_groups = _group_by_parameters(traces, attributes)

    return {
        "traces": traces,
        "metrics": metrics,
        "attributes": attributes,
        "temporal_groups": temporal_groups,
        "parameter_groups": parameter_groups,
        "trace_count": len(traces)
    }


def _extract_traces(otel_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract traces from OTEL data (handles various formats)

    Supports:
    - {"traces": [...]}
    - {"resourceSpans": [...]} (OTLP format)
    - Direct list of traces
    """
    traces = []

    if isinstance(otel_data, list):
        traces = otel_data
    elif "traces" in otel_data:
        traces = otel_data["traces"]
    elif "resourceSpans" in otel_data:
        # OTLP format (supports both scopeSpans and instrumentationLibrarySpans)
        for resource_span in otel_data["resourceSpans"]:
            # Try scopeSpans first (newer format)
            scope_spans = resource_span.get("scopeSpans", [])
            # Fall back to instrumentationLibrarySpans (older format)
            if not scope_spans:
                scope_spans = resource_span.get("instrumentationLibrarySpans", [])

            for scope_span in scope_spans:
                for span in scope_span.get("spans", []):
                    trace = _convert_otlp_span(span, resource_span.get("resource", {}))
                    traces.append(trace)
    elif "traceId" in otel_data or "spanId" in otel_data:
        # Single trace/span
        traces = [otel_data]

    return traces


def _convert_otlp_span(span: Dict, resource: Dict) -> Dict[str, Any]:
    """Convert OTLP span format to simplified trace format"""
    attributes = {}

    # Extract span attributes
    for attr in span.get("attributes", []):
        key = attr.get("key", "")
        value = attr.get("value", {})
        # Handle different value types
        if "stringValue" in value:
            attributes[key] = value["stringValue"]
        elif "intValue" in value:
            attributes[key] = int(value["intValue"])
        elif "doubleValue" in value:
            attributes[key] = float(value["doubleValue"])
        elif "boolValue" in value:
            attributes[key] = value["boolValue"]

    # Extract resource attributes
    for attr in resource.get("attributes", []):
        key = attr.get("key", "")
        value = attr.get("value", {})
        if "stringValue" in value:
            attributes[f"resource.{key}"] = value["stringValue"]

    return {
        "trace_id": span.get("traceId", ""),
        "span_id": span.get("spanId", ""),
        "parent_span_id": span.get("parentSpanId", ""),  # Include parent for aggregation
        "span_name": span.get("name", ""),
        "timestamp": span.get("startTimeUnixNano", ""),
        "attributes": attributes
    }


def _extract_metrics(traces: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """
    Extract numeric metrics from traces

    Returns dictionary mapping metric names to lists of values
    """
    metrics = defaultdict(list)

    for trace in traces:
        attributes = trace.get("attributes", {})
        for key, value in attributes.items():
            # Only extract numeric values as metrics
            if isinstance(value, (int, float)):
                metrics[key].append(float(value))

    return dict(metrics)


def _extract_attributes(traces: List[Dict[str, Any]]) -> Dict[str, Set[Any]]:
    """
    Extract all unique attribute values

    Returns dictionary mapping attribute names to sets of unique values
    """
    attributes = defaultdict(set)

    for trace in traces:
        trace_attrs = trace.get("attributes", {})
        for key, value in trace_attrs.items():
            attributes[key].add(value)

    return {k: v for k, v in attributes.items()}


def _group_by_time(traces: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group traces by time periods (weeks, days, hours)

    Returns dictionary with keys: 'by_week', 'by_day', 'by_hour'
    """
    by_week = defaultdict(list)
    by_day = defaultdict(list)
    by_hour = defaultdict(list)

    for trace in traces:
        timestamp = _parse_timestamp(trace.get("timestamp", ""))
        if timestamp:
            # Week number (ISO week)
            week_key = timestamp.strftime("%Y-W%W")
            by_week[week_key].append(trace)

            # Day
            day_key = timestamp.strftime("%Y-%m-%d")
            by_day[day_key].append(trace)

            # Hour
            hour_key = timestamp.strftime("%Y-%m-%d %H:00")
            by_hour[hour_key].append(trace)

        # Also handle explicit week/day attributes
        attributes = trace.get("attributes", {})
        if "week" in attributes:
            week_key = f"week_{attributes['week']}"
            by_week[week_key].append(trace)

    return {
        "by_week": dict(by_week),
        "by_day": dict(by_day),
        "by_hour": dict(by_hour)
    }


def _group_by_parameters(traces: List[Dict[str, Any]], attributes: Dict[str, Set[Any]]) -> Dict[str, Dict[Any, List[Dict[str, Any]]]]:
    """
    Group traces by categorical parameters (for bias detection)

    Returns dictionary mapping parameter names to groups
    """
    parameter_groups = {}

    for attr_name, unique_values in attributes.items():
        # Skip numeric attributes (handled as metrics)
        if all(isinstance(v, (int, float)) for v in unique_values):
            continue

        # Only group by categorical attributes with reasonable cardinality
        if len(unique_values) > 50:
            continue

        groups = defaultdict(list)
        for trace in traces:
            trace_attrs = trace.get("attributes", {})
            if attr_name in trace_attrs:
                param_value = trace_attrs[attr_name]
                groups[param_value].append(trace)

        if len(groups) > 1:  # Only include if there are multiple groups
            parameter_groups[attr_name] = dict(groups)

    return parameter_groups


def _parse_timestamp(timestamp: Any) -> datetime:
    """
    Parse timestamp from various formats

    Supports:
    - ISO 8601 strings
    - Unix timestamps (seconds)
    - Unix timestamps (nanoseconds)
    """
    if not timestamp:
        return None

    try:
        # ISO 8601 string
        if isinstance(timestamp, str):
            # Handle various ISO formats
            timestamp = timestamp.replace('Z', '+00:00')
            if 'T' in timestamp:
                return datetime.fromisoformat(timestamp)

        # Unix timestamp (seconds)
        if isinstance(timestamp, (int, float)):
            if timestamp > 1e12:  # Likely nanoseconds
                return datetime.fromtimestamp(timestamp / 1e9)
            else:  # Seconds
                return datetime.fromtimestamp(timestamp)

        # String representation of Unix timestamp
        if isinstance(timestamp, str) and timestamp.isdigit():
            ts = int(timestamp)
            if ts > 1e12:
                return datetime.fromtimestamp(ts / 1e9)
            else:
                return datetime.fromtimestamp(ts)

    except Exception:
        pass

    return None


def identify_business_metrics(parsed_data: Dict[str, Any], agent_purpose: str = "") -> List[Dict[str, Any]]:
    """
    Identify which metrics are likely business-relevant based on:
    - Metric names (semantic analysis)
    - Agent purpose
    - Statistical properties

    Returns list of metric metadata with relevance scores
    """
    metrics = parsed_data["metrics"]
    business_metrics = []

    # Keywords indicating business-relevant metrics
    business_keywords = [
        "amount", "cost", "price", "revenue", "profit", "refund", "fee", "commission",
        "score", "rating", "satisfaction", "count", "duration", "time", "delay",
        "success", "failure", "error", "rate", "percentage", "approved", "rejected"
    ]

    for metric_name, values in metrics.items():
        if len(values) < 5:  # Skip metrics with too few data points
            continue

        # Calculate relevance score
        relevance_score = 0.0

        # Name-based relevance
        metric_lower = metric_name.lower()
        for keyword in business_keywords:
            if keyword in metric_lower:
                relevance_score += 0.5

        # Agent purpose relevance
        if agent_purpose:
            purpose_lower = agent_purpose.lower()
            words = re.findall(r'\w+', metric_lower)
            for word in words:
                if len(word) > 3 and word in purpose_lower:
                    relevance_score += 0.3

        # Statistical properties (variability indicates interesting metric)
        import statistics
        if len(values) > 1:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0
            cv = stdev / mean if mean != 0 else 0  # Coefficient of variation
            if cv > 0.1:  # Some variability
                relevance_score += 0.2

        business_metrics.append({
            "name": metric_name,
            "relevance_score": relevance_score,
            "sample_count": len(values),
            "mean": statistics.mean(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0
        })

    # Sort by relevance
    business_metrics.sort(key=lambda x: x["relevance_score"], reverse=True)

    return business_metrics


def _aggregate_spans_by_trace(traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate spans that belong to the same trace to merge attributes

    This is useful when attributes are split across child spans
    (e.g., age in one span, score in another span of the same trace)

    Strategy:
    1. If spans share the same parent_span_id, aggregate them together
    2. Otherwise, group by trace_id + span_id combinations

    Args:
        traces: List of individual span traces

    Returns:
        List of aggregated traces with merged attributes
    """
    # First, try to group by parent_span_id (for child spans)
    by_parent = defaultdict(list)
    standalone = []

    for trace in traces:
        parent_id = trace.get("parent_span_id")
        if parent_id:
            # This is a child span, group with siblings
            key = f"{trace.get('trace_id', '')}:{parent_id}"
            by_parent[key].append(trace)
        else:
            # No parent, standalone span
            standalone.append(trace)

    # Aggregate child spans by parent
    aggregated = []

    for parent_key, sibling_spans in by_parent.items():
        # Merge all attributes from sibling spans
        merged_attributes = {}
        earliest_timestamp = None

        for span in sibling_spans:
            # Merge attributes
            attrs = span.get("attributes", {})
            merged_attributes.update(attrs)

            # Use earliest timestamp
            ts = span.get("timestamp")
            if ts:
                if earliest_timestamp is None:
                    earliest_timestamp = ts
                # Simple string comparison works for ISO timestamps
                elif isinstance(ts, str) and isinstance(earliest_timestamp, str):
                    if ts < earliest_timestamp:
                        earliest_timestamp = ts

        # Create aggregated trace from sibling spans
        aggregated_trace = {
            "trace_id": sibling_spans[0].get("trace_id", ""),
            "parent_span_id": sibling_spans[0].get("parent_span_id", ""),
            "timestamp": earliest_timestamp or sibling_spans[0].get("timestamp"),
            "span_name": sibling_spans[0].get("span_name", ""),
            "attributes": merged_attributes,
            "span_count": len(sibling_spans)
        }
        aggregated.append(aggregated_trace)

    # Add standalone spans as-is
    for trace in standalone:
        aggregated.append(trace)

    return aggregated
