#!/usr/bin/env bash
# Back up the self-hosted production stack (docker-compose.selfhost.yml):
# a custom-format PostgreSQL dump plus an archive of uploaded files.
#
#   scripts/backup_selfhost.sh                # writes to ./backups
#   BACKUP_DIR=/srv/backups KEEP_DAYS=30 scripts/backup_selfhost.sh
#
# Schedule it with cron, e.g. daily at 03:15:
#   15 3 * * * cd /home/ubuntu/enterprise-rag && scripts/backup_selfhost.sh >> backups/backup.log 2>&1
#
# Restore: see "Restoring a self-hosted backup" in DEPLOYMENT.md.
set -euo pipefail
umask 077

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"

env_file=${ENV_FILE:-.env.production}
backup_dir=${BACKUP_DIR:-$repo_root/backups}
keep_days=${KEEP_DAYS:-14}
compose=(docker compose --env-file "$env_file" -f infrastructure/docker/docker-compose.selfhost.yml)

mkdir -p "$backup_dir"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
db_file="$backup_dir/enterprise_rag_${stamp}.dump"
files_file="$backup_dir/uploads_${stamp}.tar.gz"
trap 'rm -f "$db_file.partial" "$files_file.partial"' EXIT

# Database: pg_dump runs inside the postgres container (no exposed port needed).
"${compose[@]}" exec -T postgres pg_dump -U postgres -d enterprise_rag --format=custom > "$db_file.partial"
"${compose[@]}" exec -T postgres pg_restore --list < "$db_file.partial" > /dev/null
mv "$db_file.partial" "$db_file"

# Uploaded files: archived from the backend container's /storage volume.
"${compose[@]}" exec -T backend tar czf - -C /storage . > "$files_file.partial"
tar tzf "$files_file.partial" > /dev/null
mv "$files_file.partial" "$files_file"

trap - EXIT
find "$backup_dir" -maxdepth 1 -type f \( -name 'enterprise_rag_*.dump' -o -name 'uploads_*.tar.gz' \) -mtime +"$keep_days" -delete
printf '%s backup ok: %s (%s), %s (%s)\n' "$stamp" \
  "$(basename "$db_file")" "$(du -h "$db_file" | cut -f1)" \
  "$(basename "$files_file")" "$(du -h "$files_file" | cut -f1)"
