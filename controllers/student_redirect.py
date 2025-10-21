from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website
from odoo.addons.portal.controllers.portal import CustomerPortal

class QuizStudentRedirect(Website):
    """Redirect quiz student users directly to quiz list after login.

    Any authenticated user belonging to the quiz student group will see the quiz
    list (/quiz) as their site root. Public users and all other groups retain the
    normal website homepage behavior.
    """
    @http.route('/', type='http', auth='public', website=True)
    def index(self, **kw):
        user = request.env.user
        # Only redirect logged-in non-public users who are quiz students
        if not user._is_public() and user.has_group('quiz_engine_pro.group_quiz_student'):
            # Preserve optional mode query selection if passed
            mode = kw.get('mode')
            target = '/quiz'
            if mode:
                target += f'?mode={mode}'
            return request.redirect(target)
        return super().index(**kw)

    @http.route(['/page/<string:page>'], type='http', auth='public', website=True)
    def page(self, page, **kw):
        """Intercept CMS pages for student users and send them to /quiz."""
        user = request.env.user
        if not user._is_public() and user.has_group('quiz_engine_pro.group_quiz_student'):
            return request.redirect('/quiz')
        return super().page(page, **kw)


class QuizStudentPortal(CustomerPortal):
    """Redirect portal 'My Account' home to /quiz for student users."""
    @http.route(['/my'], type='http', auth='user', website=True)
    def home(self, **kw):
        user = request.env.user
        if not user._is_public() and user.has_group('quiz_engine_pro.group_quiz_student'):
            return request.redirect('/quiz')
        return super().home(**kw)
