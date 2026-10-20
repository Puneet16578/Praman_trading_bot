"""Inputs-only reporting and metadata audit; no outcome module imports."""
from collections import Counter
from datetime import datetime
import hashlib
import re

from shared.market_time import IST


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def timing_audit(lines, study_dates):
    """Only parse weekly_ingest step-header metadata, never payload lines.

    A successful step can also mean a skip/holiday; it is not proof that a
    matching D file was ingested. Thus headers alone cannot establish by-18:00
    availability, and completion after 18:00 cannot establish unavailability.
    """
    completions = {}
    for line in lines:
        match = re.fullmatch(r"=== (\S+) weekly_ingest step=bhavcopy_today status=OK completed=(\S+) ===\s*", line)
        if match:
            started, done = (datetime.fromisoformat(x).astimezone(IST) for x in match.groups())
            day = started.date().isoformat()
            if day == done.date().isoformat():
                completions.setdefault(day, []).append(done.isoformat())
    by18 = sum(any(datetime.fromisoformat(t) <= datetime.fromisoformat(day+"T18:00:00+05:30")
                   for t in times) for day, times in completions.items())
    return dict(study_dates=len(study_dates), study_dates_with_step_metadata=sum(d in completions for d in study_dates),
        confirmed_matching_D_file_by_1800=0, availability_unknown=len(study_dates),
        logged_dates_with_successful_step=len(completions), logged_dates_with_step_completed_by_1800=by18,
        logged_dates_with_only_later_step_completions=len(completions)-by18,
        logged_matching_file_availability_unknown=len(completions),
        successful_step_completions=completions,
        limitation="Step headers do not certify the ingested file's own date. No matching-file timestamp evidence "
        "was extracted; by-18:00 availability is UNKNOWN, not zero availability. Late completion and absent logs "
        "do not prove public unavailability. No outcome payload inspected.")


def markdown(summary, meta, artifact):
    lines = ["# S1 v1 inputs-only coverage", "", "**No fills, outcomes or development evaluation.**",
             f"Code: `{meta['code_commit']}`. Artifact: `{artifact}`.", "",
             summary["overlap_note"], "",
             "| Year | Group | h | Funnel retained | Boundary removed | Inputs eligible | Dates | Scheduled overlap |",
             "|---|---|---|---|---|---|---|---|"]
    for c in summary["cells"]:
        lines.append("| " + " | ".join(str(c[k]) for k in ("year", "group", "horizon", "retained",
            "scheduled_boundary_removed", "inputs_eligible", "distinct_dates", "scheduled_overlap_count")) + " |")
    lines += ["", f"Development pooled absolute-z tercile boundaries (type 7; upper ties): "
              f"`{summary['tercile_boundaries']}`.", "",
              "The companion JSON records every standalone exclusion, exact overlap combination, turnover band "
              "and metadata audit. The immutable input artifact retains every candidate and both calendars.",
              "", "## Bhavcopy timing metadata", "",
              f"Study dates: {meta['timing_audit']['study_dates']}; dates with step metadata: "
              f"{meta['timing_audit']['study_dates_with_step_metadata']}; availability unknown: "
              f"{meta['timing_audit']['availability_unknown']}.", "",
              f"Across the available nightly log: {meta['timing_audit']['logged_dates_with_successful_step']} "
              f"dates have successful-step timestamps; "
              f"{meta['timing_audit']['logged_dates_with_step_completed_by_1800']} completed by 18:00 and "
              f"{meta['timing_audit']['logged_dates_with_only_later_step_completions']} have only later completions. "
              "These are step timestamps, not confirmed matching-D file availability.", "",
              meta["timing_audit"]["limitation"], "",
              "## Limitations", "",
              "Dated snapshots and same-day bhavcopy availability remain assumptions. Catalogue identity stitching "
              "is inherited. Fund exclusion changes the old turnover population. Weekday special hours are not "
              "reconstructed; weekend sessions inside holds are not monitored. GSM is not a research filter. "
              "These input counts are not valid-trade counts or evidence that outcome minimums are met.", ""]
    return "\n".join(lines)
