from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

EligibilityStatus = Literal["eligible", "ineligible", "verify"]


@dataclass(slots=True)
class Job:
    source: str
    source_id: str
    company: str
    title: str
    location: str
    url: str
    description: str
    posted_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Job:
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value.get(key) for key in allowed})


@dataclass(slots=True)
class EligibilityResult:
    status: EligibilityStatus
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RankedJob:
    job: Job
    eligibility: EligibilityResult
    score: int
    strengths: list[str]
    gaps: list[str]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "job": self.job.to_dict(),
            "eligibility": asdict(self.eligibility),
            "score": self.score,
            "strengths": self.strengths,
            "gaps": self.gaps,
            "recommendation": self.recommendation,
        }
