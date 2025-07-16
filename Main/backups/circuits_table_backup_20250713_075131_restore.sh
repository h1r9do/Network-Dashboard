#!/bin/bash
# Restore script for circuits table
# Created: 2025-07-13 07:51:31.488787

echo "This will DELETE all current circuits and restore from backup!"
echo "Backup file: /usr/local/bin/Main/backups/circuits_table_backup_20250713_075131.sql"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 1
fi

# Set password
export PGPASSWORD='dsrpass123'

# Truncate table and restore
psql -h localhost -p 5432 -U dsruser -d dsrcircuits << EOF
BEGIN;
TRUNCATE TABLE circuits CASCADE;
\i /usr/local/bin/Main/backups/circuits_table_backup_20250713_075131.sql
COMMIT;
EOF

echo "Restore completed!"
