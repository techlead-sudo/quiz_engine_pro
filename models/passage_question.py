from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import json

_logger = logging.getLogger(__name__)

class PassageQuestion(models.Model):
    _name = 'quiz.passage'
    _description = 'Reading Passage with Multiple Questions'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Title', required=True)
    question_id = fields.Many2one('quiz.question', string='Parent Question', required=True, ondelete='cascade')
    passage_content = fields.Html(string='Passage Content', sanitize=True, required=True,
                                help="The reading passage or material that students will refer to")
    
    # Sub-questions that refer to this passage
    sub_question_ids = fields.One2many('quiz.passage.sub.question', 'passage_id', string='Questions')
    
    @api.constrains('sub_question_ids')
    def _check_sub_questions(self):
        for passage in self:
            if not passage.sub_question_ids:
                raise ValidationError(_('A passage must have at least one question.'))


class PassageSubQuestion(models.Model):
    _name = 'quiz.passage.sub.question'
    _description = 'Sub-question for a Reading Passage'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    passage_id = fields.Many2one('quiz.passage', string='Passage', required=True, ondelete='cascade')
    question_text = fields.Html(string='Question Text', sanitize=True, required=True)
    question_type = fields.Selection([
        ('mcq_single', 'Multiple Choice (Single)'),
        ('mcq_multiple', 'Multiple Choice (Multiple)'),
        ('text_short', 'Short Text Answer'),
        ('text_long', 'Long Text Answer'),
    ], string='Question Type', default='mcq_single', required=True)
    points = fields.Float(string='Points', default=1.0)
    
    # For multiple choice questions
    choice_ids = fields.One2many('quiz.passage.choice', 'sub_question_id', string='Choices')
    
    # For text answers
    correct_answer = fields.Text(string='Correct Answer', 
                                help="For text answers, enter keywords or the expected answer")
    
    @api.constrains('question_type', 'choice_ids', 'correct_answer')
    def _check_required_fields(self):
        for question in self:
            if question.question_type in ['mcq_single', 'mcq_multiple'] and not question.choice_ids:
                raise ValidationError(_('Multiple choice questions must have choices defined.'))
            elif question.question_type in ['text_short', 'text_long'] and not question.correct_answer:
                raise ValidationError(_('Text answer questions must have a correct answer defined.'))


class PassageChoice(models.Model):
    _name = 'quiz.passage.choice'
    _description = 'Choice for Passage Sub-question'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    sub_question_id = fields.Many2one('quiz.passage.sub.question', string='Sub Question', 
                                    ondelete='cascade', required=True)
    text = fields.Char(string='Choice Text', required=True)
    is_correct = fields.Boolean(string='Is Correct', default=False)
    
    @api.constrains('is_correct', 'sub_question_id')
    def _check_correct_choices(self):
        for choice in self:
            if choice.sub_question_id.question_type == 'mcq_single':
                # For single choice questions, ensure only one option is correct
                correct_choices = self.search([
                    ('sub_question_id', '=', choice.sub_question_id.id),
                    ('is_correct', '=', True)
                ])
                if len(correct_choices) > 1:
                    raise ValidationError(_('A single choice question can have only one correct answer.'))
