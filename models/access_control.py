from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class QuestionCategory(models.Model):
    _name = 'quiz.question.category'
    _description = 'Question Access Category'
    _order = 'sequence, name'
    
    name = fields.Char(string='Category Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(default=True)
    question_ids = fields.One2many('quiz.question', 'category_id', string='Questions')
    question_count = fields.Integer(string='Question Count', compute='_compute_question_count')
    
    # Access control fields
    access_mode = fields.Selection([
        ('public', 'Public - Anyone can access'),
        ('portal', 'Portal - Registered users only'),
        ('invitation', 'Invitation - Only invited users'),
        ('internal', 'Internal - Employees only')
    ], string='Access Mode', default='internal', required=True)
    
    # Backward compatibility fields
    public_access = fields.Boolean(string='Public Access', 
                                 help='Allow public users to access questions in this category',
                                 default=False)
    portal_access = fields.Boolean(string='Portal Access', 
                                 help='Allow portal users to access questions in this category',
                                 default=False)
    invited_only = fields.Boolean(string='Invited Only', 
                                help='Questions in this category are only accessible to invited users',
                                default=False)
    
    # Security groups that can access
    group_ids = fields.Many2many('res.groups', string='Authorized Groups')
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Category name must be unique!')
    ]

    @api.depends('question_ids')
    def _compute_question_count(self):
        for category in self:
            category.question_count = len(category.question_ids)

    @api.model_create_multi
    def create(self, vals_list):
        # Set access_mode based on existing fields for backward compatibility
        for vals in vals_list:
            if 'access_mode' not in vals:
                if vals.get('public_access'):
                    vals['access_mode'] = 'public'
                elif vals.get('portal_access'):
                    vals['access_mode'] = 'portal'
                elif vals.get('invited_only'):
                    vals['access_mode'] = 'invitation'
                else:
                    vals['access_mode'] = 'internal'
        return super().create(vals_list)
    
    def write(self, vals):
        # Update old fields when access_mode is updated
        if 'access_mode' in vals:
            access_mode = vals['access_mode']
            vals.update({
                'public_access': access_mode == 'public',
                'portal_access': access_mode in ['public', 'portal'],
                'invited_only': access_mode == 'invitation',
            })
            
        res = super(QuestionCategory, self).write(vals)
        # Clear caches if security-related fields are updated
        if any(field in vals for field in ['access_mode', 'public_access', 'portal_access', 'invited_only', 'group_ids']):
            self.env['ir.rule'].clear_caches()
        return res
    
class QuestionAccessInvitation(models.Model):
    _name = 'quiz.access.invitation'
    _description = 'Quiz Access Invitation'
    
    name = fields.Char(string='Invitation Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Invited Partner', required=True)
    email = fields.Char(string='Email', related='partner_id.email', readonly=True, store=True)
    category_ids = fields.Many2many('quiz.question.category', string='Access Categories')
    quiz_ids = fields.Many2many('quiz.quiz', string='Access Quizzes')
    expiration_date = fields.Date(string='Expires On')
    token = fields.Char(string='Access Token', readonly=True, copy=False)
    access_url = fields.Char(string='Access URL', compute='_compute_access_url', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Invitation Sent'),
        ('used', 'Used'),
        ('expired', 'Expired')
    ], string='Status', default='draft', copy=False)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('token'):
                vals['token'] = self.env['ir.sequence'].next_by_code('quiz.access.token')
                # If sequence not found, generate a random token
                if not vals['token']:
                    import secrets
                    vals['token'] = secrets.token_urlsafe(16)
        return super(QuestionAccessInvitation, self).create(vals_list)
    
    @api.depends('token', 'quiz_ids')
    def _compute_access_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for invitation in self:
            if invitation.token and invitation.quiz_ids:
                # Create URL for the first quiz
                quiz = invitation.quiz_ids[0]
                invitation.access_url = f"{base_url}/quiz/{quiz.slug}?token={invitation.token}"
            else:
                invitation.access_url = False
    
    def action_send_invitation(self):
        """Send access invitation to the partner"""
        self.ensure_one()
        
        # Basic validation
        if not self.partner_id.email:
            raise ValidationError(_("The invited partner must have an email address"))
        
        template_id = self.env.ref('quiz_engine_pro.email_template_quiz_invitation', raise_if_not_found=False)
        if not template_id:
            raise ValidationError(_("Email template not found!"))
            
        # Update state
        self.write({
            'state': 'sent'
        })
        
        # Send email
        template_id.send_mail(self.id, force_send=True)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Invitation sent to %s') % self.partner_id.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def mark_as_used(self):
        self.write({'state': 'used'})
        
    def generate_new_token(self):
        """Generate a new access token for this invitation"""
        import secrets
        self.write({
            'token': secrets.token_urlsafe(16),
            'state': 'draft'
        })
        return True
        
    @api.model
    def validate_token(self, token, quiz_id=None):
        """Validate access token and return the invitation if valid"""
        domain = [
            ('token', '=', token),
            ('state', 'in', ['draft', 'sent']),
            '|',
            ('expiration_date', '>=', fields.Date.today()),
            ('expiration_date', '=', False),
        ]
        
        if quiz_id:
            domain.append(('quiz_ids', 'in', [int(quiz_id)]))
            
        invitation = self.search(domain, limit=1)
        return invitation
