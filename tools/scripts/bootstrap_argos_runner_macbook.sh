#!/usr/bin/env bash
set -euo pipefail

REPO="lukeeterna/europeanautoscout"
TARGET_DIR="${ARGOS_RUNNER_DIR:-$HOME/actions-runner-argos}"
IMAC_HOST="${ARGOS_IMAC_HOST:-iMac-di-gianluca.local}"
IMAC_USER="${ARGOS_IMAC_USER:-gianlucadistasi}"

fail() { echo "BLOCKED: $*" >&2; exit 2; }

[[ "$(uname -s)" == "Darwin" ]] || fail "this bootstrap must run on the MacBook"
command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) is required"
command -v ssh >/dev/null 2>&1 || fail "ssh is required"
command -v rsync >/dev/null 2>&1 || fail "rsync is required"

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

# GitHub Runner treats either .runner or .runner_migrated as configured.
# If a previous ARGOS bootstrap stopped before registration, remove only
# partial registration metadata inside the dedicated ARGOS directory.
# Never touch the FLUXION source runner or any worktree/runtime state.
if [[ ! -f .runner && ! -f .runner_migrated ]]; then
  for stale in \
    .credentials \
    .credentials_rsaparams \
    .credentials_migrated \
    .service; do
    if [[ -f "$stale" || -L "$stale" ]]; then
      rm -f -- "$stale"
      echo "STALE_ARGOS_RUNNER_STATE_REMOVED=$stale"
    fi
  done
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

runner_name="argos-$(scutil --get LocalHostName 2>/dev/null || hostname | cut -d. -f1)"

if [[ ! -f .runner && ! -f .runner_migrated ]]; then
  token="$(gh api --method POST "repos/$REPO/actions/runners/registration-token" --jq '.token')"
  [[ -n "$token" ]] || fail "could not obtain repository runner registration token"
  ./config.sh \
    --unattended \
    --url "https://github.com/$REPO" \
    --token "$token" \
    --name "$runner_name" \
    --labels "macbook,argos" \
    --work "_work" \
    --replace
  unset token
else
  echo "RUNNER_CONFIGURATION=EXISTING"
fi

if [[ -x ./svc.sh ]]; then
  if ! ./svc.sh status >/dev/null 2>&1; then
    ./svc.sh install
  fi
  ./svc.sh start >/dev/null 2>&1 || true
  ./svc.sh status
else
  fail "svc.sh missing; refusing non-persistent runner"
fi

status="$(gh api "repos/$REPO/actions/runners" --jq ".runners[] | select(.name == \"$runner_name\") | [.status, (.busy|tostring), (.labels|map(.name)|join(\",\"))] | @tsv" | tail -n1)"
[[ -n "$status" ]] || fail "runner registered locally but not visible through GitHub API"

printf 'ARGOS_RUNNER=%s\t%s\n' "$runner_name" "$status"
echo "ARGOS_RUNNER_BOOTSTRAP=PASS"
echo "NEXT=queued_C10T1_job_will_start_automatically"
