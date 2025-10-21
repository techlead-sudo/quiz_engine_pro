from odoo import models, fields


class QuizMode(models.Model):
    _name = 'quiz.mode'
    _description = 'Quiz Mode'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    key = fields.Char(required=True, help="Technical key used in URLs (e.g. tutor, readiness, exam, cat)")
    description = fields.Text()
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    supports_rationales = fields.Boolean(default=False, help="If enabled, rationales (explanations) can be shown during or after attempt.")
    is_adaptive = fields.Boolean(default=False, help="Indicates this mode uses adaptive (dynamic) question selection.")
    default_question_limit = fields.Integer(string='Default Question Limit', help="Optional default limit applied when starting in this mode if quiz has none.")
    icon_class = fields.Char(string='Icon CSS Class', help="Optional CSS class for front-end icon (e.g. fa fa-graduation-cap)")
    color_class = fields.Char(string='Color Style', help="Optional extra CSS color utility class for the mode card.")
    quiz_ids = fields.Many2many('quiz.quiz', 'quiz_mode_rel', 'mode_id', 'quiz_id', string='Quizzes')
    # Behavior / presentation configuration
    immediate_feedback = fields.Boolean(string='Immediate Feedback', help='Show correctness instantly after answering.')
    explanation_policy = fields.Selection([
        ('none', 'No Explanations'),
        ('immediate', 'Show With Feedback'),
        ('after_answer', 'Reveal After Each Answer'),
        ('after_completion', 'Reveal After Completion')
    ], string='Explanation Policy', default='after_completion')
    time_limit_enforced = fields.Boolean(string='Enforce Time Limit')
    time_limit_minutes = fields.Integer(string='Time Limit (Minutes)', help='If set and enforced, overrides quiz time limit when starting in this mode.')
    feedback_mode = fields.Selection([
        ('immediate', 'Immediate'),
        ('completion', 'After Completion')
    ], string='Overall Feedback Release', default='completion')
    readiness_default_length = fields.Integer(string='Readiness Length', help='Default number of questions for readiness diagnostic (mode-level).')
    exam_full_length = fields.Boolean(string='Full-Length Exam', help='If enabled, use entire quiz bank (unless quiz-level simulated length overrides).')
    _sql_constraints = [
        ('quiz_mode_key_unique', 'unique(key)', 'Mode key must be unique.'),
    ]
