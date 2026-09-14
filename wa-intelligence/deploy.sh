#!/usr/bin/env bash
# ARGOS S292/C10T1 — HISTORICAL DEPLOY SCRIPT RETIRED
#
# The former implementation predates the certified C10 single-writer runtime.
# It copied files into the historical app-antigravity-auto tree, installed npm
# packages in place, enabled the legacy com.argos.scheduler LaunchAgent and ran
# pm2 save before the C10 postdeploy gate. Those actions violate the canonical
# production invariants and are intentionally no longer executable.

set -euo pipefail

cat >&2 <<'EOF'
ARGOS_DEPLOY_RETIRED

This pre-S292 deploy path is intentionally disabled.

Use the canonical procedure instead:
  docs/runbooks/ARGOS_C10T1_CLOUD_CUTOVER.md

Required invariants include:
  - exact reviewed Git SHA in a dedicated release tree
  - runtime PAUSED
  - ARGOS_AUTOMATION_ENABLED=0
  - legacy com.argos.scheduler disabled
  - one PM2 WhatsApp writer only
  - C10 predeploy GREEN before PM2 cutover
  - C10 postdeploy --require-connected GREEN before pm2 save
  - no /resume and no dealer outreach during C10

No mutation has been performed by this retired script.
EOF

exit 64
