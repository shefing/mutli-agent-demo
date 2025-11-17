"""
Bias Detection Module
Detects correlations and bias in agent behavior across parameters
"""

from typing import Dict, List, Any, Tuple
import statistics
from collections import defaultdict


def detect_bias(
    parsed_data: Dict[str, Any],
    threshold: float = 0.3,
    agent_purpose: str = ""
) -> List[Dict[str, Any]]:
    """
    Detect bias patterns in agent behavior

    Looks for correlations between parameters (e.g., age, gender, location)
    and outcomes (e.g., approval rates, scores, amounts)

    Args:
        parsed_data: Parsed OTEL data from parse_otel_data()
        threshold: Minimum effect size to consider significant (0-1)
        agent_purpose: Agent's intended purpose (for context)

    Returns:
        List of bias findings with severity, description, and statistical evidence
    """
    bias_findings = []

    parameter_groups = parsed_data["parameter_groups"]
    metrics = parsed_data["metrics"]
    traces = parsed_data["traces"]

    # Identify protected/sensitive attributes (including numeric ones like age)
    protected_attributes = _identify_protected_attributes(parameter_groups)

    # Also check numeric attributes that might be protected (like age)
    numeric_protected = []
    for attr_name in parsed_data["attributes"].keys():
        attr_lower = attr_name.lower()
        if "age" in attr_lower and attr_name in metrics:
            numeric_protected.append(attr_name)
            protected_attributes.append(attr_name)

    # Create age groups for numeric age attributes
    for age_attr in numeric_protected:
        if age_attr in metrics:
            age_groups = _create_age_groups(traces, age_attr)
            if len(age_groups) >= 2:
                parameter_groups[f"{age_attr}_group"] = age_groups
                protected_attributes.append(f"{age_attr}_group")

    # For each metric, check if it varies significantly across parameter groups
    for metric_name, metric_values in metrics.items():
        if len(metric_values) < 3:  # Lowered from 10 to 3 for smaller datasets
            continue

        # Skip temporal/technical metrics that shouldn't be checked for bias
        if _is_temporal_or_technical_metric(metric_name):
            continue

        # Check each parameter for bias
        for param_name, groups in parameter_groups.items():
            if len(groups) < 2:
                continue

            # Skip identifier parameters (names, IDs, unique values)
            if _is_identifier_parameter(param_name, groups):
                continue

            # Skip circular comparisons: don't check age metric against age_group parameter
            # This prevents false positives like "50+ has higher age than <30"
            if _is_circular_comparison(metric_name, param_name):
                continue

            # Calculate metric statistics for each parameter group
            group_stats = _calculate_group_statistics(
                groups, metric_name
            )

            if not group_stats or len(group_stats) < 2:
                continue

            # Skip if all groups have only 1 sample (not statistically meaningful)
            # This filters out comparisons like individual names or unique skill sets
            if all(stats['count'] == 1 for stats in group_stats.values()):
                continue

            # Detect bias patterns
            bias_pattern = _detect_bias_pattern(
                metric_name,
                param_name,
                group_stats,
                threshold,
                param_name in protected_attributes,
                agent_purpose
            )

            if bias_pattern:
                # Only report if it's a protected attribute OR has very high severity
                # This filters out "request_type affects fee" (expected) but keeps age bias
                if bias_pattern.get('is_protected_attribute') or bias_pattern.get('severity_score', 0) > 0.8:
                    bias_findings.append(bias_pattern)

    # Detect intersectional bias (combinations of parameters)
    intersectional_bias = _detect_intersectional_bias(
        parsed_data,
        metrics,
        parameter_groups,
        threshold,
        agent_purpose
    )
    bias_findings.extend(intersectional_bias)

    # Sort by severity
    bias_findings.sort(key=lambda x: x["severity_score"], reverse=True)

    return bias_findings


def _identify_protected_attributes(parameter_groups: Dict) -> List[str]:
    """
    Identify parameters that may be protected/sensitive attributes

    Protected attributes include: age, gender, race, ethnicity, religion,
    disability, national origin, etc.
    """
    protected_keywords = [
        "age", "gender", "sex", "race", "ethnicity", "ethnic", "religion",
        "disability", "disabled", "national", "origin", "country",
        "marital", "married", "veteran", "orientation", "lgbt"
    ]

    protected = []
    for param_name in parameter_groups.keys():
        param_lower = param_name.lower()
        if any(keyword in param_lower for keyword in protected_keywords):
            protected.append(param_name)

    return protected


def _calculate_group_statistics(
    groups: Dict[Any, List[Dict]],
    metric_name: str
) -> Dict[Any, Dict[str, float]]:
    """
    Calculate statistics for a metric across different groups
    """
    group_stats = {}

    for group_value, traces in groups.items():
        metric_values = []

        for trace in traces:
            attrs = trace.get("attributes", {})
            if metric_name in attrs:
                val = attrs[metric_name]
                if isinstance(val, (int, float)):
                    metric_values.append(float(val))

        if len(metric_values) >= 1:  # Minimum sample size (lowered for small datasets)
            group_stats[group_value] = {
                "mean": statistics.mean(metric_values),
                "stdev": statistics.stdev(metric_values) if len(metric_values) > 1 else 0,
                "count": len(metric_values),
                "values": metric_values
            }

    return group_stats


def _detect_bias_pattern(
    metric_name: str,
    param_name: str,
    group_stats: Dict[Any, Dict[str, float]],
    threshold: float,
    is_protected: bool,
    agent_purpose: str
) -> Dict[str, Any]:
    """
    Detect if there's a significant bias pattern in the data
    """
    # Find groups with highest and lowest means
    sorted_groups = sorted(
        group_stats.items(),
        key=lambda x: x[1]["mean"],
        reverse=True
    )

    highest_group = sorted_groups[0]
    lowest_group = sorted_groups[-1]

    highest_mean = highest_group[1]["mean"]
    lowest_mean = lowest_group[1]["mean"]

    # Calculate effect size (Cohen's d)
    stdevs = [g["stdev"] for _, g in sorted_groups if g["stdev"] > 0]
    if len(stdevs) == 0:
        # If no groups have stdev, use overall range as approximation
        all_values = []
        for _, g in sorted_groups:
            all_values.extend(g.get("values", []))
        if len(all_values) > 1:
            pooled_stdev = statistics.stdev(all_values)
        else:
            return None  # Can't calculate effect size with single values
    else:
        pooled_stdev = statistics.mean(stdevs)

    if pooled_stdev == 0:
        return None

    cohens_d = abs(highest_mean - lowest_mean) / pooled_stdev

    # Check if effect size exceeds threshold
    if cohens_d < threshold:
        return None

    # Calculate percent difference
    if lowest_mean != 0:
        percent_diff = ((highest_mean - lowest_mean) / lowest_mean) * 100
    else:
        percent_diff = float('inf') if highest_mean > 0 else 0

    # Calculate disparity ratio (highest/lowest)
    disparity_ratio = highest_mean / lowest_mean if lowest_mean != 0 else float('inf')

    # Assess severity
    severity = min(cohens_d, 1.0)  # Cap at 1.0
    if is_protected:
        severity = min(severity * 1.5, 1.0)  # Increase severity for protected attributes

    # Generate bias description
    description = _generate_bias_description(
        metric_name,
        param_name,
        highest_group[0],
        lowest_group[0],
        disparity_ratio,
        is_protected
    )

    # Assess fairness concern
    fairness_concern = _assess_fairness_concern(
        metric_name,
        param_name,
        highest_group[0],
        lowest_group[0],
        disparity_ratio,
        is_protected,
        agent_purpose
    )

    return {
        "type": "bias",
        "metric": metric_name,
        "parameter": param_name,
        "is_protected_attribute": is_protected,
        "severity": severity,
        "severity_score": severity,
        "description": description,
        "details": {
            "advantaged_group": str(highest_group[0]),
            "advantaged_mean": round(highest_mean, 2),
            "disadvantaged_group": str(lowest_group[0]),
            "disadvantaged_mean": round(lowest_mean, 2),
            "disparity_ratio": round(disparity_ratio, 2),
            "percent_difference": round(percent_diff, 2),
            "cohens_d": round(cohens_d, 2),
            "all_groups": {
                str(k): {"mean": round(v["mean"], 2), "count": v["count"]}
                for k, v in group_stats.items()
            }
        },
        "fairness_concern": fairness_concern,
        "statistical_significance": "High" if cohens_d > 0.8 else "Medium" if cohens_d > 0.5 else "Low"
    }


def _detect_intersectional_bias(
    parsed_data: Dict[str, Any],
    metrics: Dict[str, List[float]],
    parameter_groups: Dict,
    threshold: float,
    agent_purpose: str
) -> List[Dict[str, Any]]:
    """
    Detect bias patterns involving combinations of parameters
    (intersectional bias)

    Example: Age + Gender interactions affecting scores
    """
    intersectional_findings = []

    # Only check combinations of protected attributes
    protected = _identify_protected_attributes(parameter_groups)

    if len(protected) < 2:
        return intersectional_findings

    # Check pairs of protected attributes (limit to avoid combinatorial explosion)
    for i, param1 in enumerate(protected[:3]):  # Limit to first 3
        for param2 in protected[i+1:4]:  # Check combinations
            # Create intersectional groups
            intersectional_groups = _create_intersectional_groups(
                parsed_data["traces"],
                param1,
                param2
            )

            # Check each metric
            for metric_name in list(metrics.keys())[:5]:  # Limit metrics checked
                group_stats = _calculate_group_statistics(
                    intersectional_groups,
                    metric_name
                )

                if len(group_stats) >= 2:
                    # Look for significant disparities
                    sorted_groups = sorted(
                        group_stats.items(),
                        key=lambda x: x[1]["mean"],
                        reverse=True
                    )

                    if len(sorted_groups) >= 2:
                        highest = sorted_groups[0]
                        lowest = sorted_groups[-1]

                        pooled_stdev = statistics.mean(
                            [g["stdev"] for _, g in sorted_groups if g["stdev"] > 0]
                        ) if any(g["stdev"] > 0 for _, g in sorted_groups) else 0

                        if pooled_stdev > 0:
                            cohens_d = abs(highest[1]["mean"] - lowest[1]["mean"]) / pooled_stdev

                            if cohens_d > threshold * 1.2:  # Higher threshold for intersectional
                                disparity_ratio = highest[1]["mean"] / lowest[1]["mean"] if lowest[1]["mean"] != 0 else float('inf')

                                intersectional_findings.append({
                                    "type": "intersectional_bias",
                                    "metric": metric_name,
                                    "parameters": [param1, param2],
                                    "is_protected_attribute": True,
                                    "severity": min(cohens_d * 0.9, 1.0),
                                    "severity_score": min(cohens_d * 0.9, 1.0),
                                    "description": f"Intersectional bias detected: {metric_name} varies significantly across {param1} and {param2} combinations",
                                    "details": {
                                        "advantaged_group": str(highest[0]),
                                        "advantaged_mean": round(highest[1]["mean"], 2),
                                        "disadvantaged_group": str(lowest[0]),
                                        "disadvantaged_mean": round(lowest[1]["mean"], 2),
                                        "disparity_ratio": round(disparity_ratio, 2),
                                        "cohens_d": round(cohens_d, 2)
                                    },
                                    "fairness_concern": f"Combined effect of {param1} and {param2} creates significant disparity in {metric_name}",
                                    "statistical_significance": "High" if cohens_d > 0.8 else "Medium"
                                })

    return intersectional_findings


def _create_intersectional_groups(
    traces: List[Dict],
    param1: str,
    param2: str
) -> Dict[Tuple, List[Dict]]:
    """
    Create groups based on combinations of two parameters
    """
    groups = defaultdict(list)

    for trace in traces:
        attrs = trace.get("attributes", {})
        if param1 in attrs and param2 in attrs:
            key = (attrs[param1], attrs[param2])
            groups[key].append(trace)

    return dict(groups)


def _generate_bias_description(
    metric_name: str,
    param_name: str,
    advantaged_group: Any,
    disadvantaged_group: Any,
    disparity_ratio: float,
    is_protected: bool
) -> str:
    """
    Generate human-readable description of the bias
    """
    if disparity_ratio == float('inf'):
        return f"⚠️ {param_name}={advantaged_group} receives {metric_name} while {param_name}={disadvantaged_group} receives none"

    ratio_text = f"{disparity_ratio:.1f}x" if disparity_ratio < 10 else f"{disparity_ratio:.0f}x"

    protection_flag = "🚨 " if is_protected else ""

    return f"{protection_flag}{param_name}={advantaged_group} has {ratio_text} higher {metric_name} than {param_name}={disadvantaged_group}"


def _assess_fairness_concern(
    metric_name: str,
    param_name: str,
    advantaged_group: Any,
    disadvantaged_group: Any,
    disparity_ratio: float,
    is_protected: bool,
    agent_purpose: str
) -> str:
    """
    Assess the fairness/ethical implications of the detected bias
    """
    concerns = []

    metric_lower = metric_name.lower()
    param_lower = param_name.lower()

    # Protected attribute concerns
    if is_protected:
        concerns.append(f"⚠️ {param_name} is a protected attribute - disparate impact may violate fairness principles")

    # Specific metric concerns
    if "age" in param_lower:
        if "score" in metric_lower or "rating" in metric_lower:
            concerns.append(f"Age-based scoring disparities may indicate ageism in the agent's behavior")
        if "approval" in metric_lower or "reject" in metric_lower:
            concerns.append(f"Age-based approval differences may constitute age discrimination")

    if "hiring" in agent_purpose.lower() or "screening" in agent_purpose.lower():
        concerns.append("Bias in hiring/screening context raises significant legal and ethical concerns")

    if "score" in metric_lower or "rating" in metric_lower:
        concerns.append(f"Scoring bias of {disparity_ratio:.1f}x creates unequal opportunities between groups")

    if "refund" in metric_lower or "commission" in metric_lower or "payment" in metric_lower:
        concerns.append(f"Financial disparities may indicate unfair treatment of different customer segments")

    # Magnitude concerns
    if disparity_ratio > 4:
        concerns.append(f"⚠️ Disparity ratio of {disparity_ratio:.1f}x indicates severe bias (4x is often a legal threshold)")
    elif disparity_ratio > 2:
        concerns.append(f"Disparity ratio of {disparity_ratio:.1f}x indicates substantial bias (80% rule: 1.25x is typical threshold)")

    if concerns:
        return " | ".join(concerns)
    else:
        return f"Significant disparity detected - verify this aligns with intended agent behavior and fairness requirements"


def _create_age_groups(traces: List[Dict], age_attr: str) -> Dict[str, List[Dict]]:
    """
    Create age range groups from numeric age values

    Groups ages into ranges:
    - <30: Young professionals
    - 30-39: Early career
    - 40-49: Mid career
    - 50+: Senior professionals
    """
    groups = defaultdict(list)

    for trace in traces:
        attrs = trace.get("attributes", {})
        if age_attr in attrs:
            age = attrs[age_attr]
            if isinstance(age, (int, float)):
                # Create age bucket
                if age < 30:
                    bucket = "<30"
                elif age < 40:
                    bucket = "30-39"
                elif age < 50:
                    bucket = "40-49"
                else:
                    bucket = "50+"

                groups[bucket].append(trace)

    return dict(groups)


def _is_circular_comparison(metric_name: str, param_name: str) -> bool:
    """
    Check if comparing a metric against its own derived parameter

    Examples of circular comparisons to avoid:
    - candidate.age vs candidate.age_group (age groups derived from age)
    - salary vs salary_range (ranges derived from salary)

    Returns True if this is a circular/meaningless comparison
    """
    metric_lower = metric_name.lower()
    param_lower = param_name.lower()

    # Extract base names (remove suffixes like _group, _range, etc)
    metric_base = metric_lower.replace("_", "").replace(".", "")
    param_base = param_lower.replace("_group", "").replace("_range", "").replace("_bucket", "").replace("_", "").replace(".", "")

    # If the base names match, it's circular
    # e.g., "candidateage" matches "candidateage"
    if metric_base == param_base:
        return True

    # Check if parameter name contains metric name (or vice versa)
    # e.g., "age" in "age_group"
    if metric_lower in param_lower or param_lower in metric_lower:
        return True

    return False


def _is_temporal_or_technical_metric(metric_name: str) -> bool:
    """
    Check if metric is temporal or technical (shouldn't be checked for bias)

    Examples to skip:
    - week_number, day_of_week, month, year (temporal identifiers)
    - trace_id, span_id (technical identifiers)
    - timestamp, duration (technical metrics)

    Returns True if this is a temporal/technical metric
    """
    metric_lower = metric_name.lower()

    # Temporal indicators
    temporal_keywords = [
        "week", "day", "month", "year", "date", "time",
        "hour", "minute", "second", "period", "quarter"
    ]

    # Technical indicators
    technical_keywords = [
        "id", "uuid", "guid", "trace", "span",
        "duration", "latency", "count", "index"
    ]

    for keyword in temporal_keywords + technical_keywords:
        if keyword in metric_lower:
            return True

    return False


def _is_identifier_parameter(param_name: str, groups: Dict) -> bool:
    """
    Check if parameter is an identifier (names, IDs, unique values)

    Identifiers shouldn't be used for bias detection because:
    - Each person/entity is unique (no pattern to detect)
    - "Alice has higher X than Bob" is meaningless

    Returns True if this is an identifier parameter
    """
    param_lower = param_name.lower()

    # IMPORTANT: Exclude derived grouping parameters (age_group, salary_range, etc.)
    # These are meaningful for bias detection even if they contain identifier keywords
    grouping_suffixes = ["_group", "_range", "_bucket", "_category", "_tier"]
    if any(param_lower.endswith(suffix) for suffix in grouping_suffixes):
        return False

    # Name indicators
    name_keywords = ["name", "person", "user", "customer", "employee", "candidate"]

    # ID indicators
    id_keywords = ["id", "uuid", "guid", "identifier"]

    for keyword in name_keywords + id_keywords:
        if keyword in param_lower:
            return True

    # If too many unique groups relative to total, it's likely an identifier
    # e.g., 100 unique names for 100 people
    if len(groups) > 20:  # More than 20 unique values = likely an identifier
        return True

    return False
