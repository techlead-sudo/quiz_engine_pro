{
    'name': 'Quiz',
    'version': '17.0.1.0.4',
    'category': 'Education',
    'summary': 'Advanced Quiz Engine with Multiple Question Types',
    'description': """
        Comprehensive quiz engine supporting:
        - Multiple Choice Questions
        - Fill in the Blanks
        - Drag and Drop
        - Matching Questions
        - Real-time scoring
        - Public quiz access
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'website', 'portal'],
    'external_dependencies': {'python': []},
    'data': [
        'security/security_groups.xml',
        'security/quiz_security.xml',
        'security/ir.model.access.csv',
        'data/quiz_mode_data.xml',
        'views/quiz_views.xml',
        'views/question_views.xml', 
           'views/passage_question_views.xml',
    'views/mode_views.xml',
        'views/session_views.xml',
        'views/quiz_master_views.xml',
        'views/website_templates.xml',
        'views/enhanced_website_templates.xml',
        'views/sentence_completion_template.xml',
        'views/admin_views_enhanced.xml',
        'views/matrix_views.xml',
        'views/passage_views.xml',
        'views/access_control_views.xml',
        'views/portal_access_views.xml',
        'views/access_denied_template.xml',
        'views/quiz_list_template.xml',
        'views/quiz_play_template.xml',
        'views/quiz_result_template.xml',
            'views/miku_base_template.xml',
    ],
    
    'assets': {
        'web.assets_backend': [
            'quiz_engine_pro/static/src/css/quiz_design_system.css',
            'quiz_engine_pro/static/src/js/quiz_enhanced_interaction.js',
            # Temporarily disabled due to Odoo 17 compatibility issues
            # 'quiz_engine_pro/static/src/js/question_editor.js',
            # 'quiz_engine_pro/static/src/xml/question_editor_templates.xml',
        ],
        'web.assets_frontend': [
              # Enhanced Design System
              'quiz_engine_pro/static/src/css/quiz_design_system.css',
            # Original CSS files (keep for compatibility)
            'quiz_engine_pro/static/src/css/quiz_styles.css',
            'quiz_engine_pro/static/src/css/quiz_drag_drop.css',
            'quiz_engine_pro/static/src/css/quiz_dropdown.css',
            'quiz_engine_pro/static/src/css/quiz_sequence.css',
            'quiz_engine_pro/static/src/css/quiz_matrix.css',
            'quiz_engine_pro/static/src/css/quiz_fill_blanks.css',
            'quiz_engine_pro/static/src/css/quiz_sentence_completion.css',
            'quiz_engine_pro/static/src/css/passage_question.css',
            'quiz_engine_pro/static/src/css/quiz_passage_short_text.css',
            # Enhanced JavaScript
            'quiz_engine_pro/static/src/js/quiz_enhanced_interaction.js',
            'quiz_engine_pro/static/src/js/quiz_fill_blanks.js',
            'quiz_engine_pro/static/src/js/quiz_sentence_completion.js',
            'quiz_engine_pro/static/src/js/quiz_passage.js',
            # Original JS files (keep for compatibility)
            'quiz_engine_pro/static/src/js/sequence_buttons.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
