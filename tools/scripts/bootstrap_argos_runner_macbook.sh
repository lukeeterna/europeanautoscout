#!/usr/bin/env bash
set -euo pipefail

REPO="lukeeterna/europeanautoscout"
TARGET_DIR="${ARGOS_RUNNER_DIR:-$HOME/actions-runner-argos}"
IMAC_HOST="${ARGOS_IMAC_HOST:-iMac-di-gianluca.local}"
IMAC_USER="${ARGOS_IMAC_USER:-gianlucadistasi}"
EXPECTED_REPO_URL="https://github.com/$REPO"

fail() { echo "BLOCKED: $*" >&2; exit 2; }

[[ "$(uname -s)" == "Darwin" ]] || fail "this bootstrap must run on the MacBook"
command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) is required"
command -v ssh >/dev/null 2>&1 || fail "ssh is required"
command -v rsync >/dev/null 2>&1 || fail "rsync is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"

gh auth status -h github.com >/dev/null 2>&1 || fail "gh is not authenticated to github.com"
gh repo view "$REPO" >/dev/null 2>&1 || fail "current gh identity cannot access $REPO"

# Prove the existing MacBook -> iMac lane before registering any new runner.
ssh \
  -o BatchMode=yes \
  -o ConnectTimeout=10 \
  -o StrictHostKeyChecking=yes \
  "$IMAC_USER@$IMAC_HOST" \
  'printf "ARGOS_IMAC_SSH=PASS\n"' \
  | grep -qx 'ARGOS_IMAC_SSH=PASS' \
  || fail "existing passwordless SSH/known-host lane to the iMac is not ready"

echo "ARGOS_IMAC_SSH=PASS"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

runner_name="argos-$(scutil --get LocalHostName 2>/dev/null || hostname | cut -d. -f1)"

runner_api_status() {
  gh api "repos/$REPO/actions/runners" \
    --jq ".runners[] | select(.name == \"$runner_name\") | [.status, (.busy|tostring), (.labels|map(.name)|join(\",\"))] | @tsv" \
    | tail -n1
}

remove_target_registration_metadata() {
  # This function is intentionally scoped to TARGET_DIR. It must never call
  # svc.sh when metadata belongs to another runner (for example FLUXION),
  # because that could stop the other runner's real LaunchAgent.
  for stale in \
    .runner \
    .runner_migrated \
    .credentials \
    .credentials_migrated \
    .credentials_rsaparams \
    .service \
    .env; do
    if [[ -f "$stale" || -L "$stale" ]]; then
      rm -f -- "$stale"
      echo "STALE_ARGOS_RUNNER_STATE_REMOVED=$stale"
    fi
  done
}

local_runner_identity() {
  local meta=""
  if [[ -f .runner ]]; then
    meta=.runner
  elif [[ -f .runner_migrated ]]; then
    meta=.runner_migrated
  else
    return 1
  fi
  python3 - "$meta" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
try:
    data = json.loads(p.read_text(encoding="utf-8"))
except Exception:
    print("UNPARSEABLE\tUNPARSEABLE")
    raise SystemExit(0)
name = str(data.get("agentName") or data.get("name") or "")
url = str(data.get("gitHubUrl") or data.get("githubUrl") or data.get("serverUrl") or "")
print(f"{name}\t{url}")
PY
}

# Reject copied/foreign registration metadata before touching svc.sh.
# The first failed bootstrap proved this matters: metadata inside the ARGOS
# directory referenced the FLUXION runner service. Removing these local copies
# does not mutate the real FLUXION runner directory or LaunchAgent.
if identity="$(local_runner_identity 2>/dev/null)"; then
  local_name="${identity%%$'\t'*}"
  local_url="${identity#*$'\t'}"
  local_is_argos=false
  [[ "$local_name" == "$runner_name" ]] && local_is_argos=true
  repo_matches=false
  case "$local_url" in
    "$EXPECTED_REPO_URL"|"$EXPECTED_REPO_URL/"|*"github.com/$REPO"*) repo_matches=true ;;
  esac

  if [[ "$local_is_argos" != true || "$repo_matches" != true ]]; then
    echo "FOREIGN_RUNNER_METADATA=DETECTED"
    echo "FOREIGN_RUNNER_NAME=${local_name:-UNKNOWN}"
    echo "FOREIGN_RUNNER_REPO_MATCH=$repo_matches"
    remove_target_registration_metadata
  else
    api_status="$(runner_api_status || true)"
    if [[ -z "$api_status" ]]; then
      echo "STALE_ARGOS_REGISTRATION=LOCAL_ONLY"
      # Only an ARGOS-owned service metadata file is eligible for cleanup.
      # Never stop/uninstall a service unless its recorded label is ARGOS-owned.
      if [[ -f .service ]]; then
        service_label="$(cat .service 2>/dev/null || true)"
        case "$service_label" in
          *europeanautoscout*|*"$runner_name"*)
            ./svc.sh stop >/dev/null 2>&1 || true
            ./svc.sh uninstall >/dev/null 2>&1 || true
            ;;
          *) echo "FOREIGN_SERVICE_METADATA=PRESERVED_FROM_EXECUTION" ;;
        esac
      fi
      remove_target_registration_metadata
    else
      echo "RUNNER_CONFIGURATION=EXISTING_VALID"
    fi
  fi
fi

if [[ ! -x ./config.sh ]]; then
  SOURCE=""
  for candidate in "$HOME/actions-runner-fluxion" "$HOME/actions-runner"; do
    if [[ -x "$candidate/config.sh" ]]; then
      SOURCE="$candidate"
      break
    fi
  done

  if [[ -n "$SOURCE" ]]; then
    echo "RUNNER_BINARY_SOURCE=existing_compatible_install"
    rsync -a \
      --exclude '.runner' \
      --exclude '.runner_migrated' \
      --exclude '.credentials' \
      --exclude '.credentials_migrated' \
      --exclude '.credentials_rsaparams' \
      --exclude '.service' \
      --exclude '.env' \
      --exclude '_work' \
      --exclude '_diag' \
      "$SOURCE/" "$TARGET_DIR/"
  else
    echo "RUNNER_BINARY_SOURCE=official_latest_release"
    tag="$(gh api repos/actions/runner/releases/latest --jq '.tag_name')"
    version="${tag#v}"
    arch="$(uname -m)"
    case "$arch" in
      x86_64) package_arch="x64" ;;
      arm64) package_arch="arm64" ;;
      *) fail "unsupported Mac architecture: $arch" ;;
    esac
    url="https://github.com/actions/runner/releases/download/${tag}/actions-runner-osx-${package_arch}-${version}.tar.gz"
    tmp="$(mktemp -t argos-runner.XXXXXX.tar.gz)"
    curl --fail --location --silent --show-error "$url" -o "$tmp"
    tar xzf "$tmp"
    rm -f "$tmp"
  fi
fi

[[ -x ./config.sh ]] || fail "runner config.sh is unavailable"

if [[ ! -f .runner && ! -f .runner_migrated ]]; then
  token="$(gh api --method POST "repos/$REPO/actions/runners/registration-token" --jq '.token')"
  [[ -n "$token" ]] || fail "could not obtain repository runner registration token"
  ./config.sh \
    --unattended \
    --url "$EXPECTED_REPO_URL" \
    --token "$token" \
    --name "$runner_name" \
    --labels "macbook,argos" \
    --work "_work" \
    --replace
  unset token
fi

# At this point service metadata must belong to the configured ARGOS runner.
if [[ -x ./svc.sh ]]; then
  if [[ -f .service ]]; then
    service_label="$(cat .service 2>/dev/null || true)"
    case "$service_label" in
      *europeanautoscout*|*"$runner_name"*) ;;
      *) fail "refusing to operate a non-ARGOS service from the ARGOS runner directory" ;;
    esac
  fi

  # On macOS svc.sh status may print "not installed" while returning exit 0.
  # Treat the textual state as authoritative so registration cannot be falsely
  # reported PASS while GitHub still sees the runner offline.
  service_status="$(./svc.sh status 2>&1 || true)"
  if printf '%s\n' "$service_status" | grep -Eqi 'not installed|not found'; then
    echo "ARGOS_RUNNER_SERVICE=INSTALLING"
    ./svc.sh install
    service_status="$(./svc.sh status 2>&1 || true)"
  fi

  if printf '%s\n' "$service_status" | grep -q '^Started:$'; then
    echo "ARGOS_RUNNER_SERVICE=ALREADY_STARTED"
  elif printf '%s\n' "$service_status" | grep -q '^Stopped$'; then
    echo "ARGOS_RUNNER_SERVICE=STARTING"
    ./svc.sh start >/dev/null
  else
    printf '%s\n' "$service_status"
    fail "ARGOS runner service state is indeterminate"
  fi

  service_status="$(./svc.sh status 2>&1 || true)"
  printf '%s\n' "$service_status"
  printf '%s\n' "$service_status" | grep -q '^Started:$' \
    || fail "ARGOS runner service did not reach Started state"
else
  fail "svc.sh missing; refusing non-persistent runner"
fi

# GitHub registration is eventually consistent for a few seconds after the
# LaunchAgent starts. Bound the check and fail closed unless the runner becomes
# online with the expected labels.
status=""
for _ in $(seq 1 15); do
  status="$(runner_api_status || true)"
  case "$status" in
    online$'\t'*) break ;;
  esac
  sleep 2
done
[[ -n "$status" ]] || fail "runner registered locally but not visible through GitHub API"

IFS=$'\t' read -r runner_state runner_busy runner_labels <<< "$status"
[[ "$runner_state" == "online" ]] || fail "runner is registered but did not become online"
for required_label in self-hosted macbook argos; do
  case ",$runner_labels," in
    *",$required_label,"*) ;;
    *) fail "runner online without required label: $required_label" ;;
  esac
done

printf 'ARGOS_RUNNER=%s\t%s\n' "$runner_name" "$status"
echo "ARGOS_RUNNER_BOOTSTRAP=PASS"
echo "NEXT=queued_C10T1_job_will_start_automatically"
