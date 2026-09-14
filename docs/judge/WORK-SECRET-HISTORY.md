# ARGOS secret-history inventory — redacted

Status: **RED / external revocation and controlled history rewrite required**.

## Observed evidence

- Repository-native scan scope: all refs visible in the Work clone, 1,049 commits
  and 7,093 reachable objects.
- Anchor HEAD at scan time: `9b5661fe6d31fec8ddb4249ba763d35040a18e75`.
- Strong-signature result: 12 unique historical blob matches, all rule
  `gmail-app-password`, limited to historical versions of `BACKLOG.md` and
  `BACKLOG.md.bak-S-A-20260701T190733`.
- Separate Gitleaks v8.30.1 observation: 21 findings across generic-api-key,
  curl-auth-header and curl-auth-user. That scanner counts findings differently;
  the two totals must not be conflated.
- Exact current tree after the redaction unit: zero strong-signature findings.

No matching value, message content, LocalAuth material or personal data is stored
in this inventory. A finding means possible exposure, not proof that a credential
is still active.

## Required closure evidence

1. Identify every affected provider/account without testing a credential in chat
   or CI; revoke/rotate through the provider's trusted control plane.
2. Record provider-side revocation evidence without storing the secret value.
3. Take recoverable mirrors/backups of all affected refs and coordinate downtime.
4. Run an explicit, reviewed history rewrite covering every affected branch/tag.
5. Re-run both strong-signature and Gitleaks full-history scans on a fresh clone.
6. Confirm required consumers use newly provisioned machine-local values and that
   old values fail provider-side validation.

History rewriting and force-updating shared refs are intentionally not performed
by the autonomous offline work: they are destructive coordination actions. Until
all six items have evidence, ARGOS release security remains RED.
