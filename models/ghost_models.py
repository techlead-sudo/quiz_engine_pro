from odoo import models, fields

class QuizDragZone(models.Model):
    """Ghost model to satisfy security references"""
    _name = 'quiz.drag.zone'
    _description = 'Quiz Drag Zone (Legacy)'
    
    name = fields.Char('Name', required=True, default='Legacy Zone')
    active = fields.Boolean('Active', default=False)
