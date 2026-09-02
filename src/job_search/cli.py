from __future__ import annotations

import argparse
from pathlib import Path

from .config import ROOT, load_json, load_profile, save_json
from .models import EligibilityResult, Job, RankedJob
from .prepare import create_dossier
from .scoring import rank_job
from .sources.greenhouse import fetch_greenhouse
from .sources.lever import fetch_lever
from .sources.remoteok import fetch_remoteok


def discover(args: argparse.Namespace) -> int:
    config = load_json(args.sources)
    jobs: list[Job] = []
    for source in config.get("greenhouse", []):
        jobs.extend(fetch_greenhouse(source["company"], source["board_token"]))
    for source in config.get("lever", []):
        jobs.extend(fetch_lever(source["company"], source["slug"]))
    remoteok = config.get("remoteok") or {}
    if remoteok.get("enabled"):
        jobs.extend(fetch_remoteok(remoteok.get("keywords", [])))

    unique = {job.url or f"{job.source}:{job.source_id}": job for job in jobs}
    destination = save_json(args.output, [job.to_dict() for job in unique.values()])
    print(f"Saved {len(unique)} unique jobs to {destination}")
    return 0


def rank(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    jobs = [Job.from_dict(item) for item in load_json(args.jobs)]
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
    ranked = RankedJob(
        job=Job.from_dict(item["job"]),
        eligibility=EligibilityResult(**item["eligibility"]),
        score=item["score"],
        strengths=item["strengths"],
        gaps=item["gaps"],
        recommendation=item["recommendation"],
    )
    slug = "-".join(filter(None, "".join(c.lower() if c.isalnum() else " " for c in f"{ranked.job.company}-{ranked.job.title}").split()))
    destination = Path(args.output_dir) / f"{slug}.md"
    create_dossier(ranked, profile, destination)
    print(f"Created application dossier at {destination}")
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
    rank_parser.add_argument("--output", default=ROOT / "data" / "ranked" / "jobs.json", type=Path)
    rank_parser.set_defaults(handler=rank)

    prepare_parser = commands.add_parser("prepare", help="Prepare a dossier for one ranked job")
    prepare_parser.add_argument("jobs", type=Path)
    prepare_parser.add_argument("--index", type=int, default=0)
    prepare_parser.add_argument("--profile", default=ROOT / "config" / "profile.json", type=Path)
    prepare_parser.add_argument("--output-dir", default=ROOT / "data" / "prepared", type=Path)
    prepare_parser.set_defaults(handler=prepare)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
