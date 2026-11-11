#!/usr/bin/env sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"

test -f "$BACKUP_FILE"
pg_restore --list "$BACKUP_FILE" >/dev/null
pg_restore "$DATABASE_URL" --clean --if-exists --no-owner --exit-on-error --single-transaction "$BACKUP_FILE"
printf 'Restore completed from %s\n' "$BACKUP_FILE"
