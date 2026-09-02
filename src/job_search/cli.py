from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .config import ROOT, load_json, load_profile, save_json
from .models import EligibilityResult, Job, RankedJob
from .prepare import create_dossier
from .scoring import rank_job
from .shortlist import create_shortlist
from .sources.greenhouse import fetch_greenhouse
from .sources.lever import fetch_lever
from .sources.remoteok import fetch_remoteok
from .tracking import APPLICATION_STATUSES, load_tracker, track_job, update_application
from .workflow import create_application_queue


def _ranked_from_dict(item: dict) -> RankedJob:
    return RankedJob(
        job=Job.from_dict(item["job"]),
        eligibility=EligibilityResult(**item["eligibility"]),
        score=item["score"],
        strengths=item["strengths"],
        gaps=item["gaps"],
        recommendation=item["recommendation"],
    )


def _is_recent(job: Job, max_age_days: int) -> bool:
    if not job.posted_at:
        return True  # Unknown posting dates remain reviewable rather than silently disappearing.
    try:
        posted = datetime.fromisoformat(job.posted_at)
    except ValueError:
        return True
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=UTC)
    return posted >= datetime.now(UTC) - timedelta(days=max_age_days)


def _job_key(job: Job) -> str:
    if job.url.strip():
        return job.url.strip().casefold()
    return f"{job.source}:{job.source_id}".casefold()


def _existing_jobs(path: Path) -> list[Job]:
    if not path.exists():
        return []
    payload = load_json(path)
    if not isinstance(payload, list):
        raise TypeError(f"Existing job history at {path} must contain a JSON list")
    return [Job.from_dict(item) for item in payload]


def discover(args: argparse.Namespace) -> int:
    config = load_json(args.sources)
    source_calls: list[tuple[str, Callable[[], list[Job]]]] = []
    for source in config.get("greenhouse", []):
        source_calls.append(
            (
                f"greenhouse:{source['company']}",
                lambda source=source: fetch_greenhouse(
                    source["company"], source["board_token"]
                ),
            )
        )
    for source in config.get("lever", []):
        source_calls.append(
            (
                f"lever:{source['company']}",
                lambda source=source: fetch_lever(source["company"], source["slug"]),
            )
        )
    remoteok = config.get("remoteok") or {}
    if remoteok.get("enabled"):
        source_calls.append(
            (
                "remoteok",
                lambda: fetch_remoteok(remoteok.get("keywords", [])),
            )
        )

    if not source_calls:
        print("No enabled job sources are configured.", file=sys.stderr)
        return 1

    fetched: list[Job] = []
    failures: list[str] = []
    for label, fetch in source_calls:
        try:
            source_jobs = fetch()
        # A third-party adapter must not discard results from healthy adapters,
        # including when its failure is an unexpected parser defect.
        except Exception as error:  # noqa: BLE001
            failures.append(label)
            print(f"Warning: {label} failed: {error}", file=sys.stderr)
            continue
        fetched.extend(source_jobs)
        print(f"Fetched {len(source_jobs)} job(s) from {label}")

    if len(failures) == len(source_calls):
        print("Every configured job source failed; existing history was preserved.", file=sys.stderr)
        return 1

    try:
        existing = _existing_jobs(args.output)
    except (OSError, ValueError, TypeError) as error:
        print(f"Cannot safely merge existing job history: {error}", file=sys.stderr)
        return 1

    merged = {_job_key(job): job for job in existing}
    before = len(merged)
    merged.update({_job_key(job): job for job in fetched})
    jobs = sorted(
        merged.values(),
        key=lambda job: job.posted_at or "",
        reverse=True,
    )
    destination = save_json(args.output, [job.to_dict() for job in jobs])
    added = len(merged) - before
    print(
        f"Saved {len(merged)} unique jobs to {destination} "
        f"({added} new, {len(failures)} source failure(s))"
    )
    return 0


def rank(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    jobs = [Job.from_dict(item) for item in load_json(args.jobs)]
    jobs = [job for job in jobs if _is_recent(job, args.max_age_days)]
    ranked = sorted((rank_job(job, profile) for job in jobs), key=lambda item: item.score, reverse=True)
    destination = save_json(args.output, [item.to_dict() for item in ranked])
    qualified = sum(item.recommendation not in {"reject", "archive"} for item in ranked)
    print(f"Saved {len(ranked)} ranked jobs ({qualified} worth reviewing) to {destination}")
    return 0


def prepare(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    payload = load_json(args.jobs)
    if args.index < 0 or args.index >= len(payload):
        raise SystemExit(f"--index must be between 0 and {len(payload) - 1}")
    item = payload[args.index]
    ranked = _ranked_from_dict(item)
    slug = "-".join(filter(None, "".join(c.lower() if c.isalnum() else " " for c in f"{ranked.job.company}-{ranked.job.title}").split()))
    destination = Path(args.output_dir) / f"{slug}.md"
    create_dossier(ranked, profile, destination)
    print(f"Created application dossier at {destination}")
    return 0


def shortlist(args: argparse.Namespace) -> int:
    ranked = [_ranked_from_dict(item) for item in load_json(args.jobs)]
    destination = create_shortlist(ranked, args.output, args.limit)
    print(f"Created shortlist at {destination}")
    return 0


def track(args: argparse.Namespace) -> int:
    payload = load_json(args.jobs)
    if args.index < 0 or args.index >= len(payload):
        raise SystemExit(f"--index must be between 0 and {len(payload) - 1}")
    metadata = {
        "cv_path": args.cv_path,
        "application_policy": args.application_policy,
        "confirmation_email_id": args.confirmation_email_id,
        "last_email_at": args.last_email_at,
        "next_action": args.next_action,
        "next_action_due": args.next_action_due,
    }
    record = track_job(
        _ranked_from_dict(payload[args.index]),
        args.tracker,
        args.status,
        args.notes,
        metadata,
    )
    print(f"Tracked {record['company']} — {record['title']} as {record['status']}")
    return 0


def applications(args: argparse.Namespace) -> int:
    records = load_tracker(args.tracker)
    selected = [record for record in records if not args.status or record["status"] == args.status]
    if not selected:
        print("No matching applications.")
        return 0
    for record in sorted(selected, key=lambda value: value["updated_at"], reverse=True):
        print(f"{record['status']:22} {record['score']:3}/100  {record['company']} — {record['title']}")
    return 0


def run_all(args: argparse.Namespace) -> int:
    discover_status = discover(
        argparse.Namespace(sources=args.sources, output=args.raw_output)
    )
    if discover_status and not args.raw_output.exists():
        return discover_status

    rank_status = rank(
        argparse.Namespace(
            profile=args.profile,
            jobs=args.raw_output,
            max_age_days=args.max_age_days,
            output=args.ranked_output,
        )
    )
    if rank_status:
        return rank_status

    shortlist_status = shortlist(
        argparse.Namespace(
            jobs=args.ranked_output,
            output=args.shortlist_output,
            limit=args.limit,
        )
    )
    ranked_items = [_ranked_from_dict(item) for item in load_json(args.ranked_output)]
    queue_destination = create_application_queue(
        ranked_items,
        args.queue_output,
        args.queue_limit,
    )
    print(f"Created human-approved application queue at {queue_destination}")
    return discover_status or shortlist_status


def application_update(args: argparse.Namespace) -> int:
    metadata = {
        "cv_path": args.cv_path,
        "application_policy": args.application_policy,
        "confirmation_email_id": args.confirmation_email_id,
        "last_email_at": args.last_email_at,
        "next_action": args.next_action,
        "next_action_due": args.next_action_due,
    }
    record = update_application(
        args.tracker,
        args.url,
        args.status,
        args.notes,
        metadata,
    )
    print(f"Updated {record['company']} — {record['title']} to {record['status']}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="job-search")
    commands = root.add_subparsers(dest="command", required=True)

    discover_parser = commands.add_parser("discover", help="Fetch configured public job boards")
    discover_parser.add_argument("--sources", default=ROOT / "config" / "sources.json", type=Path)
    discover_parser.add_argument("--output", default=ROOT / "data" / "raw" / "jobs.json", type=Path)
    discover_parser.set_defaults(handler=discover)

    rank_parser = commands.add_parser("rank", help="Eligibility-filter and score jobs")
    rank_parser.add_argument("jobs", type=Path)
    rank_parser.add_argument("--profile", default=ROOT / "config" / "profile.json", type=Path)
    rank_parser.add_argument(
        "--max-age-days",
        type=int,
        default=7,
        help="Exclude jobs older than this; jobs without a date remain included",
    )
    rank_parser.add_argument("--output", default=ROOT / "data" / "ranked" / "jobs.json", type=Path)
    rank_parser.set_defaults(handler=rank)

    prepare_parser = commands.add_parser("prepare", help="Prepare a dossier for one ranked job")
    prepare_parser.add_argument("jobs", type=Path)
    prepare_parser.add_argument("--index", type=int, default=0)
    prepare_parser.add_argument("--profile", default=ROOT / "config" / "profile.json", type=Path)
    prepare_parser.add_argument("--output-dir", default=ROOT / "data" / "prepared", type=Path)
    prepare_parser.set_defaults(handler=prepare)

    shortlist_parser = commands.add_parser("shortlist", help="Create a reviewable Markdown shortlist")
    shortlist_parser.add_argument("jobs", type=Path)
    shortlist_parser.add_argument("--limit", type=int, default=20)
    shortlist_parser.add_argument(
        "--output", default=ROOT / "data" / "ranked" / "shortlist.md", type=Path
    )
    shortlist_parser.set_defaults(handler=shortlist)

    track_parser = commands.add_parser("track", help="Add or update a job in the application tracker")
    track_parser.add_argument("jobs", type=Path)
    track_parser.add_argument("--index", type=int, required=True)
    track_parser.add_argument("--status", choices=sorted(APPLICATION_STATUSES), required=True)
    track_parser.add_argument("--notes")
    track_parser.add_argument("--cv-path")
    track_parser.add_argument(
        "--application-policy",
        choices=["unchecked", "ai_allowed", "ai_restricted", "manual_review"],
    )
    track_parser.add_argument("--confirmation-email-id")
    track_parser.add_argument("--last-email-at")
    track_parser.add_argument("--next-action")
    track_parser.add_argument("--next-action-due")
    track_parser.add_argument(
        "--tracker", default=ROOT / "data" / "applications" / "tracker.json", type=Path
    )
    track_parser.set_defaults(handler=track)

    update_parser = commands.add_parser(
        "application-update",
        help="Update an existing tracked application by its job URL",
    )
    update_parser.add_argument("--url", required=True)
    update_parser.add_argument("--status", choices=sorted(APPLICATION_STATUSES), required=True)
    update_parser.add_argument("--notes")
    update_parser.add_argument("--cv-path")
    update_parser.add_argument(
        "--application-policy",
        choices=["unchecked", "ai_allowed", "ai_restricted", "manual_review"],
    )
    update_parser.add_argument("--confirmation-email-id")
    update_parser.add_argument("--last-email-at")
    update_parser.add_argument("--next-action")
    update_parser.add_argument("--next-action-due")
    update_parser.add_argument(
        "--tracker", default=ROOT / "data" / "applications" / "tracker.json", type=Path
    )
    update_parser.set_defaults(handler=application_update)

    applications_parser = commands.add_parser("applications", help="List tracked applications")
    applications_parser.add_argument("--status", choices=sorted(APPLICATION_STATUSES))
    applications_parser.add_argument(
        "--tracker", default=ROOT / "data" / "applications" / "tracker.json", type=Path
    )
    applications_parser.set_defaults(handler=applications)

    run_all_parser = commands.add_parser(
        "run-all", help="Discover, rank and create a shortlist in one command"
    )
    run_all_parser.add_argument(
        "--sources", default=ROOT / "config" / "sources.json", type=Path
    )
    run_all_parser.add_argument(
        "--profile", default=ROOT / "config" / "profile.json", type=Path
    )
    run_all_parser.add_argument(
        "--raw-output", default=ROOT / "data" / "raw" / "jobs.json", type=Path
    )
    run_all_parser.add_argument(
        "--ranked-output", default=ROOT / "data" / "ranked" / "jobs.json", type=Path
    )
    run_all_parser.add_argument(
        "--shortlist-output",
        default=ROOT / "data" / "ranked" / "shortlist.md",
        type=Path,
    )
    run_all_parser.add_argument("--max-age-days", type=int, default=7)
    run_all_parser.add_argument("--limit", type=int, default=20)
    run_all_parser.add_argument(
        "--queue-output",
        default=ROOT / "data" / "applications" / "queue.json",
        type=Path,
    )
    run_all_parser.add_argument("--queue-limit", type=int, default=10)
    run_all_parser.set_defaults(handler=run_all)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
