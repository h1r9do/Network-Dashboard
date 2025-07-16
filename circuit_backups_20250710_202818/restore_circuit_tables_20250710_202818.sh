#!/bin/bash
# Emergency restore script created 20250710_202818
# Usage: ./restore_circuit_tables.sh

echo "=== Circuit Tables Restore Script ==="
echo "This will restore circuits and enriched_circuits tables from backup"
echo "Backup timestamp: 20250710_202818"
echo
read -p "Are you sure you want to restore? This will DELETE current data! (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 1
fi

# Database connection details
export PGPASSWORD='dsrpass123'
DB_HOST='localhost'
DB_PORT='5432'
DB_USER='dsruser'
DB_NAME='dsrcircuits'

echo "Restoring enriched_circuits table..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE enriched_circuits CASCADE;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /usr/local/bin/circuit_backups_20250710_202818/enriched_circuits_backup_20250710_202818.sql

echo "Restoring circuits table..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE circuits CASCADE;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /usr/local/bin/circuit_backups_20250710_202818/circuits_backup_20250710_202818.sql

echo "Restore complete!"
