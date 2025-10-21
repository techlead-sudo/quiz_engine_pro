from odoo import api, fields, models, _


class QuizPortalAccess(models.Model):
    """Model for simplified portal user access to quizzes"""
    _name = 'quiz.portal.access'
    _description = 'Quiz Portal User Access'
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    quiz_id = fields.Many2one('quiz.quiz', string='Quiz', required=True)
    portal_group_id = fields.Many2one('res.groups', string='Portal Group', 
                                    default=lambda self: self.env.ref('base.group_portal'))
    user_id = fields.Many2one('res.users', string='Portal User', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', 
                                related='user_id.partner_id', store=True)
    email = fields.Char(string='Email', related='partner_id.email', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('invited', 'Invited'),
        ('accessed', 'Accessed'),
        ('revoked', 'Revoked')
    ], string='Status', default='draft')
    invitation_id = fields.Many2one('quiz.access.invitation', string='Invitation')
    invitation_token = fields.Char(string='Token', related='invitation_id.token')
    last_access = fields.Datetime(string='Last Access')
    
    _sql_constraints = [
        ('quiz_user_uniq', 'unique(quiz_id, user_id)', 'A user can only have one access entry per quiz!')
    ]
    
    @api.depends('quiz_id', 'user_id')
    def _compute_name(self):
        for record in self:
            if record.quiz_id and record.user_id:
                record.name = f"{record.user_id.name} - {record.quiz_id.name}"
            else:
                record.name = _("New Access")
    
    @api.model
    def create(self, vals):
        """Override to automatically create invitation on creation"""
        res = super(QuizPortalAccess, self).create(vals)
        if res:
            res._create_invitation()
        return res
    
    def _create_invitation(self):
        """Create an access invitation for the user"""
        for record in self:
            if not record.invitation_id and record.partner_id:
                invitation = self.env['quiz.access.invitation'].create({
                    'name': record.name,
                    'partner_id': record.partner_id.id,
                    'quiz_ids': [(4, record.quiz_id.id)]
                })
                record.invitation_id = invitation
                record.state = 'draft'
                
    def action_send_invitation(self):
        """Send invitation to the user"""
        for record in self:
            if record.invitation_id:
                record.invitation_id.action_send_invitation()
                record.state = 'invited'
    
    def action_revoke_access(self):
        """Revoke user's access to the quiz"""
        for record in self:
            if record.invitation_id:
                record.invitation_id.write({
                    'state': 'expired'
                })
            record.state = 'revoked'
    
    @api.model
    def register_access(self, invitation_token):
        """Register that the user has accessed the quiz"""
        invitation = self.env['quiz.access.invitation'].search([
            ('token', '=', invitation_token)
        ], limit=1)
        
        if invitation and invitation.partner_id:
            access_records = self.search([
                ('invitation_id', '=', invitation.id)
            ])
            
            for record in access_records:
                record.write({
                    'state': 'accessed',
                    'last_access': fields.Datetime.now()
                })
                
    def action_reset_access(self):
        """Reset access and generate a new token"""
        for record in self:
            if record.invitation_id:
                record.invitation_id.generate_new_token()
                record.state = 'draft'


class QuizPortalAccessWizard(models.TransientModel):
    """Wizard for bulk managing portal user access"""
    _name = 'quiz.portal.access.wizard'
    _description = 'Portal Access Wizard'
    
    quiz_id = fields.Many2one('quiz.quiz', string='Quiz', required=True)
    portal_group_id = fields.Many2one('res.groups', string='Portal Group', 
                                    default=lambda self: self.env.ref('base.group_portal'))
    user_ids = fields.Many2many('res.users', string='Portal Users')
    action = fields.Selection([
        ('grant', 'Grant Access'),
        ('revoke', 'Revoke Access')
    ], string='Action', default='grant', required=True)
    
    def action_apply(self):
        """Apply the selected action to the users"""
        self.ensure_one()
        
        if self.action == 'grant':
            for user in self.user_ids:
                # Check if access already exists
                existing = self.env['quiz.portal.access'].search([
                    ('quiz_id', '=', self.quiz_id.id),
                    ('user_id', '=', user.id)
                ], limit=1)
                
                if not existing:
                    # Create new access
                    access = self.env['quiz.portal.access'].create({
                        'quiz_id': self.quiz_id.id,
                        'user_id': user.id
                    })
                    access.action_send_invitation()
                elif existing.state == 'revoked':
                    # Reset revoked access
                    existing.action_reset_access()
                    existing.action_send_invitation()
                    
        elif self.action == 'revoke':
            for user in self.user_ids:
                access = self.env['quiz.portal.access'].search([
                    ('quiz_id', '=', self.quiz_id.id),
                    ('user_id', '=', user.id)
                ], limit=1)
                
                if access:
                    access.action_revoke_access()
        
        # Return to the quiz form view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'quiz.quiz',
            'res_id': self.quiz_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
