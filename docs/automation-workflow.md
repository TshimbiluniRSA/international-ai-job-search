# Human-approved application automation

The repository is the policy and state-machine source of truth. Scheduled ChatGPT tasks can
perform discovery and inbox monitoring even when GitHub Actions is unavailable, but they cannot
execute a WSL process on a powered-off or sleeping PC.

## Weekday morning run (08:00 Africa/Johannesburg)

1. Read the current profile, source registry and workflow policy from the GitHub repository.
2. Fetch the configured public Greenhouse, Lever and Remote OK sources.
3. Apply freshness, location eligibility, target seniority and deterministic scoring rules.
4. Report newly qualified roles and avoid duplicating already tracked URLs.
5. Inspect the live application form for AI-use restrictions before creating materials.
6. For permitted roles, prepare a truthful ATS-readable PDF CV from verified profile evidence.
7. For restricted roles, mark `manual_materials_required`; do not generate submission text.
8. Present the application pack for human review and explicit submission approval.
9. Check the inbox for confirmations or employer feedback on tracked applications.

## Weekday evening run (18:00 Africa/Johannesburg)

1. Search the connected inbox for application confirmations, assessments, interview requests,
   recruiter questions, rejections and offers received since the previous check.
2. Match messages by employer, role and application URL; do not guess when ambiguous.
3. Report actionable messages and the corresponding tracker update.
4. Never reply to an employer automatically.

## State transitions

`qualified -> eligibility_verified -> materials_draft -> materials_ready -> approved_to_submit -> applied -> confirmation_received`

Later outcomes include `recruiter_contact`, `technical_assessment`, `interview`, `offer`,
`rejected`, `withdrawn` and `archived`. An employer that prohibits AI-generated application
content moves to `manual_materials_required` until the candidate supplies their own materials.

## Approval and access boundaries

- Discovery, ranking, deduplication and inbox classification may run unattended.
- PDF creation is allowed only after the live form's AI policy has been inspected.
- Final application submission always requires explicit approval for that application.
- Login, MFA, CAPTCHA, demographic questions, salary, work authorization, declarations and
  ambiguous form answers require the candidate.
- Background tasks cannot control the candidate's WSL instance or an authenticated browser
  session on the work PC.
- CVs, answers, email identifiers and application history remain in ignored private/data paths;
  none are committed to Git.
