from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class QuizQuestion(models.Model):
    _inherit = 'quiz.question'
    
    # Additional fields for matrix questions
    matrix_row_ids = fields.One2many('quiz.matrix.row', 'question_id', string="Matrix Rows")
    matrix_column_ids = fields.One2many('quiz.matrix.column', 'question_id', string="Matrix Columns")
    
    # Fields for text box answers
    correct_text_answer = fields.Char(string="Correct Text Answer")
    case_sensitive = fields.Boolean(string="Case Sensitive", default=False)
    allow_partial_match = fields.Boolean(string="Allow Partial Match", default=False)
    keywords = fields.Text(string="Keywords for Partial Match")
    
    # Fields for numerical answers
    numerical_exact_value = fields.Float(string="Exact Value")
    numerical_tolerance = fields.Float(string="Tolerance", default=0.0)
    numerical_min_value = fields.Float(string="Minimum Value")
    numerical_max_value = fields.Float(string="Maximum Value")
    
    @api.model_create_multi
    def create(self, vals_list):
        # Process each vals individually if needed
        for vals in vals_list:
            """Create a new question and add blank rows/columns for matrix questions"""
            # Process individual vals if needed
            
        # Call super with the full vals_list
        res = super().create(vals_list)
        
        # Process each record if needed
        for record in res:
            if record.type == 'matrix' and not record.matrix_row_ids and not record.matrix_column_ids:
                # Add default rows and columns for new matrix questions
                self.env['quiz.matrix.row'].create({'question_id': record.id, 'name': 'Row 1'})
                self.env['quiz.matrix.row'].create({'question_id': record.id, 'name': 'Row 2'})
                self.env['quiz.matrix.column'].create({'question_id': record.id, 'name': 'Column 1'})
                self.env['quiz.matrix.column'].create({'question_id': record.id, 'name': 'Column 2'})
        
        return res
    
    def action_open_matrix_cells(self):
        """Open a view to edit matrix cells"""
        self.ensure_one()
        action = {
            'name': _('Matrix Cells'),
            'type': 'ir.actions.act_window',
            'res_model': 'quiz.matrix.cell',
            'view_mode': 'tree',
            'views': [(self.env.ref('quiz_engine_pro.matrix_cell_view_tree').id, 'tree')],
            'domain': [('question_id', '=', self.id)],
            'context': {'default_question_id': self.id},
        }
        return action

class QuizMatrixRow(models.Model):
    _name = 'quiz.matrix.row'
    _description = 'Matrix Question Row'
    _order = 'sequence, id'
    
    name = fields.Char(string="Row Label", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    question_id = fields.Many2one('quiz.question', string="Question", required=True, ondelete='cascade')
    
class QuizMatrixColumn(models.Model):
    _name = 'quiz.matrix.column'
    _description = 'Matrix Question Column'
    _order = 'sequence, id'
    
    name = fields.Char(string="Column Label", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    question_id = fields.Many2one('quiz.question', string="Question", required=True, ondelete='cascade')

class QuizMatrixCell(models.Model):
    _name = 'quiz.matrix.cell'
    _description = 'Matrix Question Cell'
    
    row_id = fields.Many2one('quiz.matrix.row', string="Row", required=True, ondelete='cascade')
    column_id = fields.Many2one('quiz.matrix.column', string="Column", required=True, ondelete='cascade')
    is_correct = fields.Boolean(string="Is Correct", default=False)
    question_id = fields.Many2one('quiz.question', string="Question", required=True, ondelete='cascade')
    
    _sql_constraints = [
        ('unique_cell', 'unique(row_id, column_id, question_id)', 'Each cell must be unique per question.')
    ]
