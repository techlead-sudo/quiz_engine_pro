from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import logging
import json

_logger = logging.getLogger(__name__)


class Question(models.Model):
    _name = 'quiz.question'
    _description = 'Quiz Question'
    _order = 'sequence, id'
    
    # Basic fields
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Title', compute='_compute_name', store=True)
    quiz_id = fields.Many2one('quiz.quiz', string='Quiz', required=True, ondelete='cascade')
    question_html = fields.Html(string='Question Text', sanitize=True, required=False)
    explanation = fields.Html(string='Explanation', sanitize=True,
                              help="Shown after answering the question")
    points = fields.Float(string='Points', default=1.0)
    rationale_html = fields.Html(string='Rationale / Explanation', sanitize=True,
                                 help='Displayed in modes that allow rationales (e.g., Tutor). If empty, falls back to Explanation.')
    difficulty_level = fields.Selection([
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], string='Difficulty Level', default='medium', help='Used by adaptive and readiness modes.')
    
    # Access control fields
    category_id = fields.Many2one('quiz.question.category', string='Access Category',
                               help="Control who can access this question")
    access_mode = fields.Selection([
        ('inherit', 'Inherit from Category'),
        ('public', 'Public - Anyone can access'),
        ('portal', 'Portal - Registered users only'),
        ('invitation', 'Invitation - Only invited users'),
        ('internal', 'Internal - Employees only')
    ], string='Access Mode', default='inherit', required=True,
        help="Controls who can access this question")
    
    # Backward compatibility fields
    is_public = fields.Boolean(string='Public Access', related='category_id.public_access', store=True, readonly=True)
    is_portal = fields.Boolean(string='Portal Access', related='category_id.portal_access', store=True, readonly=True)
    is_invited_only = fields.Boolean(string='Invited Only', related='category_id.invited_only', store=True, readonly=True)
    
    # Direct access fields
    allowed_group_ids = fields.Many2many('res.groups', string='Allowed User Groups',
                                       help="Specific user groups that can access this question")
    
    def generate_matrix_cells(self):
        """Generate the matrix cells based on rows and columns"""
        self.ensure_one()
        if self.type != 'matrix':
            return False
            
        # Get all rows and columns
        rows = self.matrix_row_ids
        columns = self.matrix_column_ids
        
        if not rows or not columns:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Rows or Columns',
                    'message': 'Please add at least one row and one column before generating the cell configuration.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
            
        # Generate cells for each row-column combination
        for row in rows:
            for column in columns:
                # Check if the cell already exists
                cell = self.env['quiz.matrix.cell'].search([
                    ('row_id', '=', row.id),
                    ('column_id', '=', column.id)
                ], limit=1)
                
                # Create the cell if it doesn't exist
                if not cell:
                    self.env['quiz.matrix.cell'].create({
                        'row_id': row.id,
                        'column_id': column.id,
                        'is_correct': False
                    })
                    
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Cell Configuration Generated',
                'message': 'Matrix cells have been generated. You can now configure which cells are correct.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    # Question type selection
    type = fields.Selection([
        ('mcq_single', 'Multiple Choice (Single)'),
        ('mcq_multiple', 'Multiple Choice (Multiple)'),
        ('fill_blank', 'Fill in the Blanks'),
        ('match', 'Match the Following'),
        ('drag_text', 'Drag into Text'),
        ('drag_zone', 'Drag into Zones'),
        ('dropdown_blank', 'Dropdown in Text'),
        ('step_sequence', 'Drag and Drop - Step Sequencing'),
        ('sentence_completion', 'Sentence Completion'),
        ('matrix', 'Matrix Question'),
        ('passage', 'Reading Passage with Questions')
    ], string='Type', default='mcq_single', required=True)
    
    # Text template for dropdown_blank type
    text_template = fields.Html(string='Text with Blanks', 
                             help="Use {{1}}, {{2}}, etc. to mark where dropdowns should appear")
    
    # Define relationships
    choice_ids = fields.One2many('quiz.choice', 'question_id', string='Choices')
    match_pair_ids = fields.One2many('quiz.match.pair', 'question_id', string='Match Pairs')
    drag_token_ids = fields.One2many('quiz.drag.token', 'question_id', string='Drag Tokens')
    fill_blank_answer_ids = fields.One2many('quiz.fill.blank.answer', 'question_id', string='Fill Blank Answers')
    blank_ids = fields.One2many('quiz.blank', 'question_id', string='Dropdown Blanks')
    sequence_item_ids = fields.One2many('quiz.sequence.item', 'question_id', string='Sequence Items')
    
    # Matrix question fields
    matrix_row_ids = fields.One2many('quiz.matrix.row', 'question_id', string='Matrix Rows')
    matrix_column_ids = fields.One2many('quiz.matrix.column', 'question_id', string='Matrix Columns')
    matrix_cell_ids = fields.One2many('quiz.matrix.cell', 'question_id', string='Matrix Cells')
    
    # Passage question fields
    passage_ids = fields.One2many('quiz.passage', 'question_id', string='Reading Passages')
    active_passage_id = fields.Many2one('quiz.passage', string='Selected Passage', compute='_compute_active_passage')
    sub_question_ids = fields.One2many(related='active_passage_id.sub_question_ids', string='Sub Questions')
    
    @api.depends('passage_ids')
    def _compute_active_passage(self):
        for question in self:
            if question.passage_ids:
                question.active_passage_id = question.passage_ids[0]
            else:
                question.active_passage_id = False
    
    @api.depends('question_html', 'text_template', 'type')
    def _compute_name(self):
        for question in self:
            if question.type == 'dropdown_blank' and question.text_template:
                text = question.text_template or ''
                # Strip tags to get plain text
                text = re.sub(r'<[^>]*>', '', text)
            else:
                text = question.question_html or ''
                # Strip tags to get plain text
                text = re.sub(r'<[^>]*>', '', text)
                
            # Limit length for display
            if len(text) > 50:
                text = text[:50] + '...'
            question.name = text or _('New Question')
    
    @api.constrains('type')
    def _check_required_fields(self):
        for question in self:
            if question.type == 'mcq_single' or question.type == 'mcq_multiple':
                if not question.choice_ids:
                    raise ValidationError(_('Multiple choice questions must have choices defined.'))
            elif question.type == 'fill_blank':
                if not question.fill_blank_answer_ids:
                    raise ValidationError(_('Fill in the blanks questions must have blank answers defined.'))
            elif question.type == 'match':
                if not question.match_pair_ids:
                    raise ValidationError(_('Match questions must have match pairs defined.'))
            elif question.type in ['drag_text', 'drag_zone', 'sentence_completion']:
                if not question.drag_token_ids:
                    raise ValidationError(_('Drag and drop questions must have tokens defined.'))
            elif question.type == 'dropdown_blank':
                if not question.text_template:
                    raise ValidationError(_('Dropdown in Text questions must have a text template defined.'))
                if not question.blank_ids:
                    raise ValidationError(_('Dropdown in Text questions must have blanks with options defined.'))
            elif question.type == 'step_sequence':
                if not question.sequence_item_ids:
                    raise ValidationError(_('Step Sequencing questions must have sequence steps defined.'))
            elif question.type == 'matrix':
                if not question.matrix_row_ids or not question.matrix_column_ids:
                    raise ValidationError(_('Matrix questions must have both rows and columns defined.'))
            elif question.type == 'passage':
                if not question.passage_ids:
                    raise ValidationError(_('Reading Passage questions must have at least one passage defined.'))
    
    # This method will auto-fill question_html from text_template for dropdown_blank questions
    @api.onchange('text_template', 'type')
    def _onchange_text_template(self):
        if self.type == 'dropdown_blank' and self.text_template:
            # Copy text template to question_html to satisfy requirements in other parts of code
            self.question_html = self.text_template
            
    def auto_set_positions(self):
        """
        Automatically set the correct positions for sequence steps
        based on their current order in the UI
        """
        self.ensure_one()
        if self.type == 'step_sequence' and self.sequence_item_ids:
            # Get sorted items based on sequence field
            sorted_items = self.sequence_item_ids.sorted(lambda r: r.sequence)
            
            # Set correct positions from 0 to N
            for i, item in enumerate(sorted_items):
                item.correct_position = i
                
        return True


class Choice(models.Model):
    _name = 'quiz.choice'
    _description = 'Multiple Choice Option'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one('quiz.question', string='Question', ondelete='cascade', required=True)
    text = fields.Char(string='Choice Text', required=True)
    is_correct = fields.Boolean(string='Is Correct', default=False)


class MatchPair(models.Model):
    _name = 'quiz.match.pair'
    _description = 'Match Pair'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one('quiz.question', string='Question', ondelete='cascade', required=True)
    left_text = fields.Char(string='Left Item', required=True)
    right_text = fields.Char(string='Right Item', required=True)


class DragToken(models.Model):
    _name = 'quiz.drag.token'
    _description = 'Drag and Drop Token'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one('quiz.question', string='Question', ondelete='cascade', required=True)
    text = fields.Char(string='Token Text', required=True)
    is_correct = fields.Boolean(string='Is Correct Answer', default=False)
    correct_position = fields.Integer(string='Correct Position', default=0)


class FillBlankAnswer(models.Model):
    _name = 'quiz.fill.blank.answer'
    _description = 'Fill in the Blank Answer'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one('quiz.question', string='Question', ondelete='cascade', required=True)
    blank_number = fields.Integer(string='Blank Number', required=True,
                               help="The number in the {{n}} placeholder")
    answer_text = fields.Char(string='Answer', required=True)
    
    _sql_constraints = [
        ('unique_blank_num_per_question', 
         'UNIQUE(question_id, blank_number)',
         'Each blank number must be unique within a question')
    ]


class QuizBlank(models.Model):
    _name = 'quiz.blank'
    _description = 'Question Blank'
    _order = 'blank_number, id'
    
    question_id = fields.Many2one('quiz.question', string='Question', ondelete='cascade', required=True)
    blank_number = fields.Integer(string='Blank Number', required=True, 
                                 help="The number in the {{n}} placeholder")
    input_type = fields.Selection([
        ('text', 'Text Input'),
        ('dropdown', 'Dropdown Menu')
    ], string='Input Type', default='dropdown', required=True)
    option_ids = fields.One2many('quiz.option', 'blank_id', string='Options')
    
    _sql_constraints = [
        ('unique_blank_number_per_question', 
         'UNIQUE(question_id, blank_number)',
         'Each blank number must be unique within a question')
    ]
    
    @api.constrains('input_type', 'option_ids')
    def _check_dropdown_options(self):
        for blank in self:
            if blank.input_type == 'dropdown' and not blank.option_ids:
                raise ValidationError(_("Dropdown blanks must have at least one option defined"))


class QuizOption(models.Model):
    _name = 'quiz.option'
    _description = 'Dropdown Option'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    blank_id = fields.Many2one('quiz.blank', string='Blank', ondelete='cascade', required=True)
    label = fields.Char(string='Option Text', required=True)
    is_correct = fields.Boolean(string='Is Correct Answer', default=False)
    
    @api.constrains('blank_id', 'is_correct')
    def _check_one_correct_answer(self):
        for option in self:
            if option.is_correct:
                correct_count = self.search_count([
                    ('blank_id', '=', option.blank_id.id),
                    ('is_correct', '=', True),
                    ('id', '!=', option.id)
                ])
                if correct_count > 0:
                    raise ValidationError(_("Each dropdown blank can have only one correct answer"))


class SequenceItem(models.Model):
    _name = 'quiz.sequence.item'
    _description = 'Sequence Item for Ordering Questions'
    _order = 'correct_position, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    question_id = fields.Many2one('quiz.question', string='Question', ondelete='cascade', required=True)
    label = fields.Char('Step Label', required=True)
    content = fields.Text('Content')
    correct_position = fields.Integer('Correct Position', required=True, help="The correct position in the sequence (0, 1, 2, etc.)")
    # Add type field to fix the attribute error
    type = fields.Char('Type', default='sequence_item', help="Technical field for compatibility")
    
    _sql_constraints = [
        ('unique_position_per_question', 
         'UNIQUE(question_id, correct_position)',
         'Each correct position must be unique within a question')
    ]
    
    @api.onchange('correct_position')
    def _onchange_correct_position(self):
        """Ensure correct_position is a non-negative integer"""
        if self.correct_position < 0:
            self.correct_position = 0
            return 0.0
    def _evaluate_matrix(self, answer_data):
        """Evaluate matrix questions"""
        if not answer_data:
            return 0.0
        
        try:
            answers = json.loads(answer_data) if isinstance(answer_data, str) else answer_data
        except Exception:
            return 0.0
        
        total_cells = len(self.matrix_row_ids) * len(self.matrix_column_ids)
        if total_cells == 0:
            return 0.0
        
        correct_count = 0
        
        for row in self.matrix_row_ids:
            for col in self.matrix_column_ids:
                cell_key = f"cell_{row.id}_{col.id}"
                expected_value = self._get_matrix_correct_value(row, col)
                
                if cell_key in answers and answers[cell_key] == expected_value:
                    correct_count += 1
        
        return (correct_count / total_cells) * self.points
    @api.model
    def _get_matrix_correct_value(self, row, col):
        """Get the correct value for a matrix cell"""
        # Find the correct cell value from the matrix_cell model
        cell = self.env['quiz.matrix.cell'].search([
            ('row_id', '=', row.id),
            ('column_id', '=', col.id),
            ('question_id', '=', self.id)
        ], limit=1)
        
        return cell.is_correct if cell else False
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Process each vals individually
            res = super().create([vals])
            
            # Handle individual records after creation
            for record in res:
                if record._name == 'quiz.question':  # Only apply to question records
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
            'name': 'Matrix Cells',
            'type': 'ir.actions.act_window',
            'res_model': 'quiz.matrix.cell',
            'view_mode': 'tree',
            'views': [(self.env.ref('quiz_engine_pro.matrix_cell_view_tree').id, 'tree')],
            'domain': [('question_id', '=', self.id)],
            'context': {'default_question_id': self.id},
        }
        return action
    @api.constrains('type', 'question_html', 'text_template', 'sequence_item_ids')
    def _check_required_question_content(self):
        for question in self:
            # Make sure we're only validating quiz.question records, not sequence items
            if question._name != 'quiz.question':
                continue
                
            if question.type == 'dropdown_blank':
                if not question.text_template:
                    raise ValidationError(_("Text template is required for Dropdown in Text questions"))
            elif question.type == 'step_sequence':
                if not question.sequence_item_ids:
                    raise ValidationError(_("Step Sequencing questions must have sequence steps defined."))
            else:
                if not question.question_html:
                    raise ValidationError(_("Question Text is required"))

    @api.onchange('text_template', 'type')
    def _onchange_text_template(self):
        # This method will auto-fill question_html from text_template for dropdown_blank questions
        if self.type == 'dropdown_blank' and self.text_template:
            # Copy text template to question_html to satisfy requirements in other parts of code
            self.question_html = self.text_template

@api.constrains('type')
def _check_required_fields(self):
    for question in self:
        if question.type == 'mcq_single' or question.type == 'mcq_multiple':
            if not question.choice_ids:
                raise ValidationError(_('Multiple choice questions must have choices defined.'))
                
@api.constrains('type', 'question_html', 'text_template', 'sequence_item_ids')
def _check_required_question_content(self):
    for question in self:
        if question.type == 'dropdown_blank':
            if not question.text_template:
                raise ValidationError(_("Text template is required for Dropdown in Text questions"))
            if not question.blank_ids:
                raise ValidationError(_("Dropdown in Text questions must have blanks defined"))
        elif question.type == 'step_sequence':
            if not question.sequence_item_ids:
                raise ValidationError(_("Step Sequencing questions must have sequence steps defined."))
        else:
            if not question.question_html:
                raise ValidationError(_("Question Text is required"))

class SequenceStep(models.Model):
    _name = 'quiz.sequence.step'
    _description = 'Legacy Sequence Step'
    
    # Minimum required fields 
    name = fields.Char('Name')
    active = fields.Boolean('Active', default=False)
