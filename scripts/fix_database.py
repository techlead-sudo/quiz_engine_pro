# Run this script from Odoo shell to manually fix database issues
def fix_quiz_question_fields(env):
    """Manually add missing fields to the database schema"""
    env.cr.execute("""
        DO $$
        BEGIN
            -- Add numerical fields if they don't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'quiz_question' AND column_name = 'numerical_exact_value') THEN
                ALTER TABLE quiz_question ADD COLUMN numerical_exact_value float;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'quiz_question' AND column_name = 'numerical_min_value') THEN
                ALTER TABLE quiz_question ADD COLUMN numerical_min_value float;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'quiz_question' AND column_name = 'numerical_max_value') THEN
                ALTER TABLE quiz_question ADD COLUMN numerical_max_value float;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'quiz_question' AND column_name = 'numerical_tolerance') THEN
                ALTER TABLE quiz_question ADD COLUMN numerical_tolerance float;
            END IF;
            
            -- Add text box fields if they don't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'quiz_question' AND column_name = 'correct_text_answer') THEN
                ALTER TABLE quiz_question ADD COLUMN correct_text_answer varchar;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'quiz_question' AND column_name = 'case_sensitive') THEN
                ALTER TABLE quiz_question ADD COLUMN case_sensitive boolean DEFAULT false;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'quiz_question' AND column_name = 'allow_partial_match') THEN
                ALTER TABLE quiz_question ADD COLUMN allow_partial_match boolean DEFAULT false;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'quiz_question' AND column_name = 'keywords') THEN
                ALTER TABLE quiz_question ADD COLUMN keywords text;
            END IF;
        END $$;
    """)
    
    return "Database schema fixed successfully"

# Usage in Odoo shell:
# from odoo.addons.quiz_engine_pro.scripts.fix_database import fix_quiz_question_fields
# fix_quiz_question_fields(env)
