import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    """Add missing columns for quiz_question table if they don't exist"""
    _logger.info("Running quiz_engine_pro migration to add missing columns")
    
    # Check if numerical_exact_value column exists
    cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'quiz_question' AND column_name = 'numerical_exact_value'")
    if not cr.fetchone():
        _logger.info("Adding numerical_exact_value column to quiz_question table")
        cr.execute("ALTER TABLE quiz_question ADD COLUMN numerical_exact_value float")
    
    # Check if numerical_min_value column exists
    cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'quiz_question' AND column_name = 'numerical_min_value'")
    if not cr.fetchone():
        _logger.info("Adding numerical_min_value column to quiz_question table")
        cr.execute("ALTER TABLE quiz_question ADD COLUMN numerical_min_value float")
    
    # Check if numerical_max_value column exists
    cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'quiz_question' AND column_name = 'numerical_max_value'")
    if not cr.fetchone():
        _logger.info("Adding numerical_max_value column to quiz_question table")
        cr.execute("ALTER TABLE quiz_question ADD COLUMN numerical_max_value float")
    
    # Check if numerical_tolerance column exists
    cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'quiz_question' AND column_name = 'numerical_tolerance'")
    if not cr.fetchone():
        _logger.info("Adding numerical_tolerance column to quiz_question table")
        cr.execute("ALTER TABLE quiz_question ADD COLUMN numerical_tolerance float")
    
    # Check for other columns
    for column in ['correct_text_answer', 'case_sensitive', 'allow_partial_match', 'keywords']:
        cr.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = 'quiz_question' AND column_name = '{column}'")
        if not cr.fetchone():
            _logger.info(f"Adding {column} column to quiz_question table")
            col_type = "boolean" if column in ['case_sensitive', 'allow_partial_match'] else "varchar"
            cr.execute(f"ALTER TABLE quiz_question ADD COLUMN {column} {col_type}")
