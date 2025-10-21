from odoo import models, fields, api, _
import json


class QuizResponse(models.Model):
    _name = 'quiz.response'
    _description = 'Quiz Response'

    session_id = fields.Many2one('quiz.session', required=True, ondelete='cascade')
    question_id = fields.Many2one('quiz.question', required=True, ondelete='cascade')
    answer_data = fields.Text(string='Answer Data')
    score = fields.Float(string='Score', default=0.0)
    is_correct = fields.Boolean(string='Is Correct', compute='_compute_is_correct', store=True)

    # Score is now set by the controller at creation/update. No automatic recomputation here to avoid recursion.

    @api.depends('score', 'question_id.points')
    def _compute_is_correct(self):
        for record in self:
            if record.question_id and record.question_id.points > 0:
                record.is_correct = record.score >= record.question_id.points
            else:
                record.is_correct = False
