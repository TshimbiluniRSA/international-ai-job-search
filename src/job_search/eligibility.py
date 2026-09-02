from __future__ import annotations

import re

from .models import EligibilityResult, Job


INELIGIBLE_PATTERNS = {
    "US work authorization required": r"(?:must|should) (?:be )?(?:currently )?authorized to work in (?:the )?(?:u\.?s\.?|united states)",
    "US-only remote role": r"(?:remote[- ]?(?:us|usa)|(?:u\.?s\.?|united states) only|must (?:reside|live|be located) in (?:the )?(?:u\.?s\.?|united states))",
    "No sponsorship": r"(?:unable|not able) to (?:provide|offer) (?:visa )?sponsorship|no (?:visa )?sponsorship",
    "Security clearance": r"(?:active |eligible for )(?:u\.?s\.? )?(?:security )?clearance|u\.?s\.? citizen(?:ship)? required",
    "On-site or hybrid": r"\b(?:on[- ]?site|hybrid)\b",
}

ELIGIBLE_PATTERNS = {
    "Worldwide remote": r"(?:remote worldwide|worldwide remote|work from anywhere|globally remote|global remote)",
    "International candidates": r"(?:international candidates|hire globally|global applicants|candidates worldwide)",
    "Contractor supported": r"(?:independent contractor|contractor agreement|b2b contract)",
    "Employer of Record supported": r"(?:employer of record|\beor\b)",
    "South Africa accepted": r"(?:south africa|africa remote|remote.*emea|emea.*remote)",
}


def evaluate_eligibility(job: Job) -> EligibilityResult:
    text = " ".join((job.title, job.location, job.description)).lower()
    negative = [label for label, pattern in INELIGIBLE_PATTERNS.items() if re.search(pattern, text, re.I)]
    positive = [label for label, pattern in ELIGIBLE_PATTERNS.items() if re.search(pattern, text, re.I)]

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
