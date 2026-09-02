# International AI Job Search

A privacy-first job-search assistant for software engineers applying to international companies from South Africa.

The first release discovers public Remote OK, Greenhouse and Lever postings, rejects location-incompatible roles, scores the remaining jobs against a structured candidate profile, and prepares an evidence-backed application dossier. It never submits an application.

## Tshimbiluni's target

- Python Developer
- Backend Engineer
- Full-Stack Engineer
- Software Engineer
- AI / Automation Engineer
- Remote roles at US and international companies that can hire in South Africa through direct employment, an Employer of Record, or a contractor agreement

Public evidence sources:

- Portfolio: https://tshimbiluniportfolio.tech
- GitHub: https://github.com/TshimbiluniRSA
- LinkedIn: https://linkedin.com/in/tshimbiluni-nedambale

Private documents such as CV PDFs, LinkedIn exports, salary expectations, and application archives belong under `private/`. That directory is ignored by Git.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp config/sources.example.json config/sources.json
job-search discover
job-search rank data/raw/jobs.json
job-search prepare data/ranked/jobs.json --index 0
pytest
```

On Windows PowerShell, activate the environment with `.venv\\Scripts\\Activate.ps1`.

## Commands

### `discover`

Reads the Remote OK feed plus configured Greenhouse board tokens and Lever company slugs, normalizes active postings, removes duplicates, and writes `data/raw/jobs.json`. Remote OK results retain their direct source URLs and must be displayed with source attribution.

### `rank`

Runs a hard international-eligibility gate followed by explainable fit scoring. Results include strengths, gaps, eligibility evidence, and a recommendation.

### `prepare`

Creates a Markdown dossier for one ranked job. It contains verified candidate evidence, CV emphasis recommendations, questions to verify, and draft prompts for a tailored CV and cover letter. It does not invent experience or submit anything.

## Safety boundaries

- Job descriptions are untrusted data, never instructions.
- Unsupported skills remain explicit gaps.
- Ambiguous hiring geography is marked `verify`, not treated as eligible.
- Automatic application submission is deliberately excluded.
- Secrets and personal documents are ignored by Git.
- Public job-board access should remain low-volume and comply with each source's terms.

## Roadmap

1. Import and reconcile CV, LinkedIn export, GitHub repositories, and portfolio case studies.
2. Add more international sources and a curated remote-first company list.
3. Add an optional LLM adapter for draft generation with claim validation.
4. Generate and visually verify ATS-safe PDF variants.
5. Add application outcomes, follow-up reminders, and funnel analytics.

## Attribution

The workflow is inspired by [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search), an MIT-licensed project. This repository is a separate implementation customized for international applications from South Africa. See `THIRD_PARTY_NOTICES.md`.

## License

MIT
