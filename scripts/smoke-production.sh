#!/usr/bin/env bash
# Production smoke test for TradeFlow paper beta.
# Usage: ./scripts/smoke-production.sh [WEB_URL] [API_URL]
set -euo pipefail

WEB_URL="${1:-${WEB_URL:-https://tradeflowweb-production-4fcc.up.railway.app}}"
API_URL="${2:-${API_URL:-https://trade-production-8a85.up.railway.app}}"

WEB_URL="${WEB_URL%/}"
API_URL="${API_URL%/}"

pass=0
fail=0

check() {
  local name="$1"
  local url="$2"
  local expect="${3:-200}"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' "$url" || echo "000")"
  if [[ "$code" == "$expect" ]]; then
    echo "✓ $name ($code)"
    pass=$((pass + 1))
  else
    echo "✗ $name — expected $expect, got $code"
    fail=$((fail + 1))
  fi
}

echo "TradeFlow production smoke test"
echo "Web: $WEB_URL"
echo "API: $API_URL"
echo ""

check "Web health" "$WEB_URL/api/health"
check "Web status page" "$WEB_URL/status"
check "Web terms page" "$WEB_URL/terms"
check "Web privacy page" "$WEB_URL/privacy"
check "API liveness" "$API_URL/api/v1/health/live"
check "API readiness" "$API_URL/api/v1/health/ready"
check "API health summary" "$API_URL/api/v1/health/"
check "Protected route (401)" "$API_URL/api/v1/auth/me" "401"

echo ""
echo "Results: $pass passed, $fail failed"

if [[ "$fail" -gt 0 ]]; then
  exit 1
fi

echo ""
echo "Manual checks still required:"
echo "  1. Register / login"
echo "  2. Connect 2 paper accounts"
echo "  3. Create copy group → start → simulate event"
echo "  4. Kill switch activate / deactivate"
echo "  5. Analytics + profile save"
