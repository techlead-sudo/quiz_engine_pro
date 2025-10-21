#!/bin/bash

# Execute this script to clean up invalid model references in the database
# Replace 'your_db_name' with your actual database name
# Replace 'odoo_user' with your actual Odoo database user

echo "Cleaning up invalid model references in the database..."

PGPASSWORD=your_password psql -h localhost -U odoo_user your_db_name -c "
-- Delete access rights for non-existent models
DELETE FROM ir_model_access WHERE model_id IS NULL;
DELETE FROM ir_model_access WHERE name LIKE '%quiz.drag.zone%';
"

echo "Cleanup complete."
