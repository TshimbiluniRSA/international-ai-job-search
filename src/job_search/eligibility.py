from __future__ import annotations

import re

from .models import EligibilityResult, Job

INELIGIBLE_PATTERNS = {
    "US work authorization required": r"(?:must|should) (?:be )?(?:currently )?authorized to work in (?:the )?(?:u\.?s\.?|united states)",
    "US-only remote role": r"(?:remote[- ]?(?:us|usa)|(?:u\.?s\.?|united states) only|must (?:reside|live|be located) in (?:the )?(?:u\.?s\.?|united states))",
    "No sponsorship": r"(?:unable|not able) to (?:provide|offer) (?:visa )?sponsorship|no (?:visa )?sponsorship",
    "Security clearance": r"(?:active |eligible for )(?:u\.?s\.? )?(?:security )?clearance|u\.?s\.? citizen(?:ship)? required",
    "On-site or hybrid": (
        r"\b(?:on[- ]?site|onsite)\b"
        r"|\bhybrid\s+(?:role|position|job|work(?:ing)?|schedule|arrangement|model)\b"
        r"|\b(?:role|position|job|work(?:ing)?|schedule|arrangement|model)\s+is\s+hybrid\b"
        r"|\bhybrid\s*[-–|,]\s*[a-z]"
    ),
}

ELIGIBLE_PATTERNS = {
    "Worldwide remote": r"(?:remote worldwide|worldwide remote|work from anywhere|globally remote|global remote)",
    "International candidates": r"(?:international candidates|hire globally|global applicants|candidates worldwide)",
    "Contractor supported": r"(?:independent contractor|contractor agreement|b2b contract)",
    "Employer of Record supported": r"(?:employer of record|\beor\b)",
    "South Africa accepted": r"(?:south africa|africa remote|remote.{0,80}emea|emea.{0,80}remote)",
}

LOCATION_ELIGIBLE = re.compile(
    r"\b(?:worldwide|global|south africa|africa|emea)\b",
    re.IGNORECASE,
)


def _location_evidence(job: Job) -> tuple[list[str], list[str]]:
    location = job.location.strip()
    if not location:
        return [], []
    if LOCATION_ELIGIBLE.search(location):
        return [], ["Job-board location permits South Africa or a broader region"]
    if location.casefold() in {"remote", "anywhere", "home based", "home-based"}:
        return [], []
    return ["Job-board location is restricted outside South Africa"], []


def evaluate_eligibility(job: Job) -> EligibilityResult:
    text = f"{job.title} {job.location} {job.description}".lower()
    negative = [label for label, pattern in INELIGIBLE_PATTERNS.items() if re.search(pattern, text, re.IGNORECASE)]
    positive = [label for label, pattern in ELIGIBLE_PATTERNS.items() if re.search(pattern, text, re.IGNORECASE)]
    location_negative, location_positive = _location_evidence(job)
    negative.extend(location_negative)
    positive.extend(location_positive)

    # Explicit worldwide/SA/EOR/contractor evidence overrides a generic "US" location label,
    # but never an explicit citizenship, authorization, or clearance restriction.
    hard_negative = [reason for reason in negative if reason != "US-only remote role"]
    if hard_negative or ("US-only remote role" in negative and not positive):
        return EligibilityResult("ineligible", negative, positive)
    if positive:
        return EligibilityResult("eligible", [], positive)
    return EligibilityResult(
        "verify",
        ["The posting does not clearly confirm hiring from South Africa"],
        [],
    )
