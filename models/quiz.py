from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Quiz(models.Model):
    _name = 'quiz.quiz'
    _description = 'Quiz'
    _order = 'create_date desc'

    name = fields.Char(string='Title', required=True)
    description = fields.Html(string='Description')
    slug = fields.Char(string='URL Slug', required=True, help="Used in public URL")
    published = fields.Boolean(string='Published', default=False)
    randomize_questions = fields.Boolean(string='Randomize Questions', default=False)
    time_limit = fields.Integer(string='Time Limit (minutes)', default=0, help='0 = No time limit')
    max_attempts = fields.Integer(string='Maximum Attempts', default=1)
    show_results = fields.Boolean(string='Show Results After Completion', default=True)
    passing_score = fields.Float(string='Passing Score (%)', default=60.0)
    question_limit = fields.Integer(string='Question Limit', default=0,
                                    help='If > 0, restrict the number of questions delivered (after optional randomization). 0 means use all questions.')
    mode_ids = fields.Many2many('quiz.mode', 'quiz_mode_rel', 'quiz_id', 'mode_id', string='Available Modes')
    mode_count = fields.Integer(string='Mode Count', compute='_compute_mode_count', help='Number of modes this quiz is available in.')
    allow_rationales = fields.Boolean(string='Allow Rationales', default=True,
                                      help='If enabled, explanation/rationale can be shown depending on mode settings.')
    readiness_length = fields.Integer(string='Readiness Length', default=0,
                                      help='If > 0, overrides question_limit when starting in Readiness mode.')
    simulated_exam_length = fields.Integer(string='Simulated Exam Length', default=0,
                                           help='If > 0, overrides question_limit for simulated exam mode.')
    enable_adaptive = fields.Boolean(string='Enable Adaptive Mode', default=False,
                                     help='Allow adaptive (CAT) mode for this quiz.')
    
    # Access control fields
    access_mode = fields.Selection([
        ('public', 'Public - Anyone can access'),
        ('portal', 'Portal - Registered users only'),
        ('invitation', 'Invitation - Only invited users'),
        ('internal', 'Internal - Employees only')
    ], string='Access Mode', default='internal', required=True,
        help="Controls who can access this quiz")
        
    allowed_category_ids = fields.Many2many('quiz.question.category', 
                                         string='Allowed Categories',
                                         help="Only questions from these categories will be included")
    
    invitation_ids = fields.One2many('quiz.access.invitation', 'quiz_ids', 
                                  string='Access Invitations')
                                  
    # Simplified Portal access management
    portal_access_ids = fields.One2many('quiz.portal.access', 'quiz_id', 
                                     string='Portal User Access')
    portal_user_count = fields.Integer(string='Portal Users', compute='_compute_portal_user_count')
    
    @api.depends('portal_access_ids')
    def _compute_portal_user_count(self):
        for quiz in self:
            quiz.portal_user_count = len(quiz.portal_access_ids)
    
    def action_open_portal_users(self):
        """Open portal users view for this quiz"""
        self.ensure_one()
        return {
            'name': _('Portal Users'),
            'type': 'ir.actions.act_window',
            'res_model': 'quiz.portal.access',
            'view_mode': 'tree,form',
            'domain': [('quiz_id', '=', self.id)],
            'context': {'default_quiz_id': self.id},
            'target': 'current',
        }

    @api.depends('mode_ids')
    def _compute_mode_count(self):
        for quiz in self:
            quiz.mode_count = len(quiz.mode_ids)

    def action_view_modes(self):
        """Open the modes this quiz is linked to (or all modes if none yet)."""
        self.ensure_one()
        domain = []
        if self.mode_ids:
            domain = [('id', 'in', self.mode_ids.ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Modes'),
            'res_model': 'quiz.mode',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_quiz_ids': [(6, 0, [self.id])]},
            'target': 'current',
        }
        
    def action_add_portal_users(self):
        """Open wizard to add portal users"""
        self.ensure_one()
        return {
            'name': _('Add Portal Users'),
            'type': 'ir.actions.act_window',
            'res_model': 'quiz.portal.access.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_quiz_id': self.id, 'default_action': 'grant'},
        }
    
    # Relationships
    question_ids = fields.One2many('quiz.question', 'quiz_id', string='Questions')
    session_ids = fields.One2many('quiz.session', 'quiz_id', string='Quiz Sessions')
    
    # Computed fields
    total_questions = fields.Integer(string='Total Questions', compute='_compute_total_questions', search='_search_total_questions')
    total_points = fields.Float(string='Total Points', compute='_compute_total_points', search='_search_total_points')
    
    @api.depends('question_ids')
    def _compute_total_questions(self):
        for quiz in self:
            quiz.total_questions = len(quiz.question_ids)
            
    def _search_total_questions(self, operator, value):
        """Search method for total_questions field"""
        quizzes = self.search([])
        quiz_ids = []
        
        # Find quizzes matching the condition
        for quiz in quizzes:
            question_count = len(quiz.question_ids)
            
            # Compare using eval for cleaner code
            if eval(f"{question_count} {operator} {value}"):
                quiz_ids.append(quiz.id)
        
        return [('id', 'in', quiz_ids)]
    
    @api.depends('question_ids.points')
    def _compute_total_points(self):
        for quiz in self:
            quiz.total_points = sum(quiz.question_ids.mapped('points'))
            
    def _search_total_points(self, operator, value):
        """Search method for total_points field"""
        quizzes = self.search([])
        quiz_ids = []
        
        # Find quizzes matching the condition
        for quiz in quizzes:
            total_points = sum(quiz.question_ids.mapped('points'))
            
            # Compare using eval for cleaner code
            if eval(f"{total_points} {operator} {value}"):
                quiz_ids.append(quiz.id)
        
        return [('id', 'in', quiz_ids)]
    
    @api.constrains('slug')
    def _check_slug_unique(self):
        for quiz in self:
            if self.search([('slug', '=', quiz.slug), ('id', '!=', quiz.id)]):
                raise ValidationError(_('URL Slug must be unique.'))
    
    @api.model
    def create(self, vals):
        if not vals.get('slug'):
            vals['slug'] = self._generate_slug(vals.get('name', ''))
        return super().create(vals)
    
    def _generate_slug(self, name):
        """Generate URL-friendly slug from name"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def action_view_public_url(self):
        """Open the public quiz URL in a new tab"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        quiz_url = f"{base_url}/quiz/{self.slug}"
        
        return {
            'type': 'ir.actions.act_url',
            'url': quiz_url,
            'target': 'new',
        }
