#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

STATE_FILE="deploy/.active_color"
NGINX_DIR="deploy/nginx"
PULL="${PULL:-0}"
RETRIES="${RETRIES:-15}"
DELAY="${DELAY:-2}"

port_of() {
  if [ "$1" = "blue" ]; then echo 5001; else echo 5002; fi
}

json_field() {
  grep -o "\"$1\": *\"[^\"]*\"" | sed 's/.*"\([^"]*\)"$/\1/'
}

if [ -f "$STATE_FILE" ]; then
  ACTIVE="$(cat "$STATE_FILE")"
else
  ACTIVE="none"
fi
if [ "$ACTIVE" = "blue" ]; then NEW="green"; else NEW="blue"; fi
echo "==> couleur active : $ACTIVE -> deploiement dans : $NEW"

mkdir -p "$NGINX_DIR/conf.d"
if [ ! -f "$NGINX_DIR/conf.d/default.conf" ]; then
  cp "$NGINX_DIR/blue.conf" "$NGINX_DIR/conf.d/default.conf"
fi
if [ "$ACTIVE" = "none" ]; then
  docker compose up -d --wait redis nginx
else
  docker compose up -d nginx
fi

if [ "$PULL" = "1" ]; then
  docker compose --profile "$NEW" pull "app-$NEW"
else
  docker compose --profile "$NEW" build "app-$NEW"
fi
docker compose --profile "$NEW" up -d --no-deps --no-build --force-recreate "app-$NEW"

URL="http://localhost:$(port_of "$NEW")"
ok=0
for i in $(seq 1 "$RETRIES"); do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$URL/health" || true)"
  color="$(curl -fsS "$URL/status" 2>/dev/null | json_field deploy_color || true)"
  echo "    tentative $i/$RETRIES : /health=$code deploy_color=${color:-?}"
  if [ "$code" = "200" ] && [ "$color" = "$NEW" ]; then
    ok=1
    break
  fi
  sleep "$DELAY"
done

if [ "$ok" != "1" ]; then
  echo "!!! ECHEC : app-$NEW ne passe pas le smoke test -> rollback"
  docker compose --profile "$NEW" logs --tail 20 "app-$NEW" || true
  docker compose --profile "$NEW" stop "app-$NEW"
  echo "!!! trafic inchange, couleur active : $ACTIVE"
  exit 1
fi

cp "$NGINX_DIR/$NEW.conf" "$NGINX_DIR/conf.d/default.conf"
docker compose exec -T nginx nginx -t
docker compose exec -T nginx nginx -s reload
echo "$NEW" > "$STATE_FILE"

if [ "$ACTIVE" != "none" ]; then
  docker compose --profile "$ACTIVE" stop "app-$ACTIVE"
fi
echo "==> OK : trafic bascule sur $NEW"
