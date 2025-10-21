from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class MatrixRow(models.Model):
    _name = 'quiz.matrix.row'
    _description = 'Matrix Question Row'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one('quiz.question', string='Question', required=True, ondelete='cascade')
    name = fields.Char(string='Row Label', required=True)
    description = fields.Text(string='Description', help='Optional description or context for this row')
    
    @api.model_create_multi
    def create(self, vals_list):
        rows = super(MatrixRow, self).create(vals_list)
        # Create matrix cells for each new row
        for row in rows:
            columns = self.env['quiz.matrix.column'].search([('question_id', '=', row.question_id.id)])
            for column in columns:
                self.env['quiz.matrix.cell'].create({
                    'row_id': row.id,
                    'column_id': column.id,
                    'is_correct': False
                })
        return rows

class MatrixColumn(models.Model):
    _name = 'quiz.matrix.column'
    _description = 'Matrix Question Column'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one('quiz.question', string='Question', required=True, ondelete='cascade')
    name = fields.Char(string='Column Label', required=True)
    description = fields.Text(string='Description', help='Optional description or context for this column')
    
    @api.model_create_multi
    def create(self, vals_list):
        columns = super(MatrixColumn, self).create(vals_list)
        # Create matrix cells for each new column
        for column in columns:
            rows = self.env['quiz.matrix.row'].search([('question_id', '=', column.question_id.id)])
            for row in rows:
                self.env['quiz.matrix.cell'].create({
                    'row_id': row.id,
                    'column_id': column.id,
                    'is_correct': False
                })
        return columns

class MatrixCell(models.Model):
    _name = 'quiz.matrix.cell'
    _description = 'Matrix Question Cell'
    
    question_id = fields.Many2one('quiz.question', string='Question', related='row_id.question_id', store=True)
    row_id = fields.Many2one('quiz.matrix.row', string='Row', required=True, ondelete='cascade')
    column_id = fields.Many2one('quiz.matrix.column', string='Column', required=True, ondelete='cascade')
    is_correct = fields.Boolean(string='Is Correct', default=False,
                               help='Mark as correct if this cell should be selected for the correct answer')
    
    _sql_constraints = [
        ('unique_row_col_per_question', 
         'UNIQUE(row_id, column_id)',
         'Each cell in the matrix must be unique')
    ]
    
    @api.model
    def ensure_matrix_cells(self, question_id):
        """Ensure that all matrix cells exist for a given question"""
        question = self.env['quiz.question'].browse(question_id)
        rows = self.env['quiz.matrix.row'].search([('question_id', '=', question_id)])
        columns = self.env['quiz.matrix.column'].search([('question_id', '=', question_id)])
        
        # Create missing cells
        for row in rows:
            for column in columns:
                cell = self.search([
                    ('row_id', '=', row.id),
                    ('column_id', '=', column.id)
                ], limit=1)
                
                if not cell:
                    self.create({
                        'row_id': row.id,
                        'column_id': column.id,
                        'is_correct': False
                    })
        
        return True
