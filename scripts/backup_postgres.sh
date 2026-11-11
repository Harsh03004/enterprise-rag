#!/usr/bin/env sh
set -eu
umask 077

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_DIR:=./backups}"

mkdir -p "$BACKUP_DIR"
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
output="$BACKUP_DIR/enterprise_rag_${timestamp}.dump"
trap 'rm -f "$output"' EXIT

pg_dump "$DATABASE_URL" --format=custom --file="$output"
pg_restore --list "$output" >/dev/null
trap - EXIT
printf 'Backup written to %s\n' "$output"
