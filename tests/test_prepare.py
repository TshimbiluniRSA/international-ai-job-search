from pathlib import Path

from job_search.models import EligibilityResult, Job, RankedJob
from job_search.prepare import create_dossier


def test_dossier_supports_profile_schema_v2(tmp_path: Path) -> None:
    ranked = RankedJob(
        Job(
            "greenhouse",
            "1",
            "Acme",
            "Python Engineer",
            "Worldwide",
            "https://example.com",
            "Build Python APIs and automation.",
        ),
        EligibilityResult("eligible", evidence=["Worldwide"]),
        80,
        ["Matching skills: python"],
        [],
        "apply now",
    )
    profile = {
        "experience": [{"evidence": ["Built production Python automation APIs."]}],
        "selected_projects": [{"evidence": ["Created a FastAPI portfolio."]}],
        "portfolio_url": "https://portfolio.example",
        "github_url": "https://github.com/example",
        "linkedin_url": "https://linkedin.com/in/example",
    }
    destination = tmp_path / "dossier.md"
    create_dossier(ranked, profile, destination)
    contents = destination.read_text()
    assert "Built production Python automation APIs." in contents
    assert "ATS-readable PDF" in contents
