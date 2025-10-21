from odoo import http, fields, _
from odoo.http import request
import json
import uuid
import logging
from datetime import timedelta

# Model and group constants
QUIZ_MODEL = 'quiz.quiz'
SESSION_MODEL = 'quiz.session'
RESPONSE_MODEL = 'quiz.response'
INVITATION_MODEL = 'quiz.access.invitation'
PORTAL_ACCESS_MODEL = 'quiz.portal.access'
QUIZ_MODE_MODEL = 'quiz.mode'
TEMPLATE_ACCESS_DENIED = 'quiz_engine_pro.quiz_access_denied'
GROUP_PORTAL = 'base.group_portal'
ROUTE_QUIZ = '/quiz'

_logger = logging.getLogger(__name__)


class QuizController(http.Controller):
    @http.route(['/quiz'], type='http', auth='public', website=True)
    def quiz_list(self, **kwargs):
        """List all published quizzes that the user has access to"""
        # Show only published quizzes filtered by user access
        user = request.env.user
        is_public = user._is_public()
        is_portal = not is_public and user.has_group(GROUP_PORTAL)
        domain = [('published', '=', True)]
        if is_public:
            domain += [('access_mode', '=', 'public')]
        elif is_portal:
            domain += [('access_mode', 'in', ['public', 'portal'])]
        
        # Check for token-based access
        token = kwargs.get('token')
        if token:
            invitation = request.env[INVITATION_MODEL].sudo().validate_token(token)
            if invitation:
                # Include invitation quizzes alongside domain
                invited_quiz_ids = invitation.quiz_ids.filtered(lambda q: q.published).ids
                if invited_quiz_ids:
                    domain = ['|', ('id', 'in', invited_quiz_ids)] + domain
        
        active_mode_key = kwargs.get('mode')
        mode_env = request.env[QUIZ_MODE_MODEL].sudo()
        modes = mode_env.search([('active', '=', True)])
        quizzes = request.env[QUIZ_MODEL].sudo().search(domain)
        active_mode = None
        if active_mode_key:
            active_mode = mode_env.search([('key', '=', active_mode_key)], limit=1)
            if active_mode:
                quizzes = quizzes.filtered(lambda q: active_mode in q.mode_ids)
        values = {
            'quizzes': quizzes,
            'modes': modes,
            'active_mode': active_mode,
            'token': token,
        }
        return request.render('quiz_engine_pro.quiz_list_template', values)

    @http.route(['/quiz/<string:slug>'], type='http', auth='public', website=True)
    def quiz_detail(self, slug, **kwargs):
        """Show quiz details and start form"""
        quiz = request.env[QUIZ_MODEL].sudo().search([('slug', '=', slug), ('published', '=', True)], limit=1)
        if not quiz:
            fallback = request.env[QUIZ_MODEL].sudo().search([('slug', '=', slug)], limit=1)
            if fallback:
                return request.render(TEMPLATE_ACCESS_DENIED, {
                    'quiz': fallback,
                    'login_required': fallback.access_mode in ['portal', 'internal', 'invitation'],
                    'message': _('This quiz exists but is not available to view publicly.')
                })
            return request.not_found()
        can_access = False
        token = kwargs.get('token')
        invitation = None
        user = request.env.user
        is_public = user._is_public()
        is_portal = not is_public and user.has_group(GROUP_PORTAL)
    # is_student not needed here; portal check is sufficient for frontend access

        # Primary access rules
        if quiz.access_mode == 'public':
            can_access = True
        elif quiz.access_mode == 'portal':
            # All portal users (including students) can access portal quizzes
            if is_portal:
                can_access = True
                # Optional: register access if portal_access record exists
                portal_access = request.env[PORTAL_ACCESS_MODEL].sudo().search([
                    ('quiz_id', '=', quiz.id),
                    ('user_id', '=', user.id),
                ], limit=1)
                if portal_access:
                    portal_access.write({'state': 'accessed', 'last_access': fields.Datetime.now()})
        elif quiz.access_mode == 'internal':
            can_access = user.has_group('base.group_user')
        if not can_access and token:
            invitation = request.env[INVITATION_MODEL].sudo().validate_token(token, quiz.id)
            if invitation:
                can_access = True
        if not can_access:
            return request.render(TEMPLATE_ACCESS_DENIED, {
                'quiz': quiz,
                'login_required': quiz.access_mode in ['portal', 'internal', 'invitation']
            })
        # Prepare questions (respect randomization + limit) only for single-page mode
        mode_key = kwargs.get('mode') or request.params.get('mode')
        mode_env = request.env[QUIZ_MODE_MODEL].sudo()
        active_mode = None
        if mode_key:
            m = mode_env.search([('key', '=', mode_key)], limit=1)
            if m and m in quiz.mode_ids:
                active_mode = m

        questions = quiz.question_ids
        if quiz.randomize_questions or (active_mode and active_mode.is_adaptive):
            # Build a randomized ordering safely by browsing shuffled IDs
            import random
            q_ids = list(questions.ids)
            random.shuffle(q_ids)
            questions = questions.browse(q_ids)
        # Determine limit precedence
        limit = quiz.question_limit or 0
        if active_mode:
            if active_mode.key == 'readiness' and active_mode.readiness_default_length:
                limit = active_mode.readiness_default_length
            elif active_mode.key in ('exam','simulated') and active_mode.exam_full_length:
                limit = 0  # use all
            elif active_mode.default_question_limit and not limit:
                limit = active_mode.default_question_limit
        if limit and limit > 0:
            questions = questions[:limit]
        values = {
            'token': token,
            'quiz': quiz,
            'questions': questions,
            'active_mode': active_mode,
            'show_rationales': bool(active_mode and active_mode.supports_rationales and quiz.allow_rationales),
            'immediate_feedback': bool(active_mode and active_mode.immediate_feedback),
        }
        return request.render('quiz_engine_pro.quiz_play_template', values)
    @http.route(['/quiz/<string:slug>/submit'], type='http', auth='public', methods=['POST'], csrf=True, website=True)
    def quiz_submit(self, slug, **kwargs):
        """Handle submission of all questions on one page"""
        quiz = request.env[QUIZ_MODEL].sudo().search([('slug', '=', slug), ('published', '=', True)], limit=1)
        if not quiz:
            return request.not_found()
        participant_name = request.env.user.name if not request.env.user._is_public() else 'Anonymous'
        participant_email = request.env.user.email if not request.env.user._is_public() else ''
        session_token = str(uuid.uuid4())
        session = request.env[SESSION_MODEL].sudo().create({
            'quiz_id': quiz.id,
            'participant_name': participant_name,
            'participant_email': participant_email,
            'session_token': session_token,
            'state': 'completed',
            'start_time': fields.Datetime.now(),
            'end_time': fields.Datetime.now(),
        })
        total_score = 0.0
        max_score = sum(quiz.question_ids.mapped('points'))
        for question in quiz.question_ids:
            # Extract raw answers for our one-page form
            if question.type == 'mcq_multiple':
                raw_answer = request.httprequest.form.getlist('question_' + str(question.id))
            else:
                raw_answer = kwargs.get('question_' + str(question.id))
                if raw_answer is None:
                    raw_answer = request.httprequest.form.get('question_' + str(question.id))

            # Always serialize answer as JSON for consistency
            answer_json = json.dumps(raw_answer)
            # Evaluate using model logic for consistency across types
            try:
                # If answer is a stringified list/dict, parse it before evaluation
                eval_answer = raw_answer
                if isinstance(raw_answer, str):
                    try:
                        eval_answer = json.loads(raw_answer)
                    except Exception:
                        pass
                computed = self._evaluate_answer(question, eval_answer)
            except Exception as e:
                _logger.exception("Evaluation failed for question %s: %s", question.id, e)
                computed = 0.0

            total_score += float(computed or 0.0)

            request.env[RESPONSE_MODEL].sudo().create({
                'session_id': session.id,
                'question_id': question.id,
                'answer_data': answer_json,
                'score': computed,
            })
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= quiz.passing_score if hasattr(quiz, 'passing_score') else False
        session.write({'total_score': total_score, 'max_score': max_score, 'percentage': percentage, 'passed': passed})
        results_url = f'/quiz/session/{session.session_token}/results'
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(f"quiz_submit: score={total_score} max_score={max_score} percentage={percentage} passed={passed}")
        return request.redirect(results_url)

    @http.route(['/quiz/<string:slug>/start'], type='http', auth='public', methods=['POST'], csrf=False, website=True)
    def quiz_start(self, slug, **kwargs):
        """Start a quiz session"""
        quiz = request.env[QUIZ_MODEL].sudo().search([('slug', '=', slug), ('published', '=', True)], limit=1)
        if not quiz:
            return request.not_found()
        # Consistent access check for start
        token = kwargs.get('token')
        user = request.env.user
        is_public = user._is_public()
        is_portal = not is_public and user.has_group(GROUP_PORTAL)
        can_access = False
        if quiz.access_mode == 'public':
            can_access = True
        elif quiz.access_mode == 'portal' and is_portal:
            can_access = True
        elif quiz.access_mode == 'internal' and user.has_group('base.group_user'):
            can_access = True
        if not can_access and token:
            invitation = request.env[INVITATION_MODEL].sudo().validate_token(token, quiz.id)
            if invitation:
                can_access = True
        if not can_access:
            return request.render('quiz_engine_pro.quiz_access_denied', {
                'quiz': quiz,
                'login_required': quiz.access_mode in ['portal', 'internal', 'invitation']
            })
        participant_name = kwargs.get('participant_name', 'Anonymous')
        participant_email = kwargs.get('participant_email', '')
        session_token = str(uuid.uuid4())
        # Build question order (randomize + limit) for per-question navigation mode
        questions = quiz.question_ids
        if quiz.randomize_questions:
            import random
            q_ids = list(questions.ids)
            random.shuffle(q_ids)
            questions = questions.browse(q_ids)
        if quiz.question_limit and quiz.question_limit > 0:
            questions = questions[:quiz.question_limit]
        question_order = ','.join(str(q.id) for q in questions)

        # Mode handling
        mode_key = kwargs.get('mode') or kwargs.get('mode_key') or request.params.get('mode')
        mode_env = request.env[QUIZ_MODE_MODEL].sudo()
        mode = None
        if mode_key:
            mode = mode_env.search([('key', '=', mode_key)], limit=1)
            if mode and mode not in quiz.mode_ids:
                mode = None  # disallow modes not assigned to quiz

        # Derive selection length overrides
        # Derive effective limit if needed (currently handled inline when building order)

        # Apply mode-specific time limit override
        time_limit_minutes = quiz.time_limit
        if mode and mode.time_limit_enforced and mode.time_limit_minutes:
            time_limit_minutes = mode.time_limit_minutes

        session_vals = {
            'quiz_id': quiz.id,
            'participant_name': participant_name,
            'participant_email': participant_email,
            'session_token': session_token,
            'state': 'in_progress',
            'start_time': fields.Datetime.now(),
            'question_order': question_order,
            'mode_id': mode.id if mode else False,
            'show_rationales': bool(mode and mode.supports_rationales and quiz.allow_rationales),
            'immediate_feedback': bool(mode and mode.immediate_feedback),
            'explanation_policy': mode.explanation_policy if mode else 'after_completion',
        }
        if time_limit_minutes and time_limit_minutes > 0:
            session_vals['time_limit'] = time_limit_minutes
            session_vals['time_limit_end'] = fields.Datetime.now() + timedelta(minutes=time_limit_minutes)
        session = request.env[SESSION_MODEL].sudo().create(session_vals)
        access_token = kwargs.get('token')
        if access_token:
            invitation = request.env[INVITATION_MODEL].sudo().validate_token(access_token, quiz.id)
            if invitation:
                # Register that the invitation was used
                invitation.sudo().mark_as_used()
                # Register access in portal access model if applicable
                request.env[PORTAL_ACCESS_MODEL].sudo().register_access(access_token)
        elif not request.env.user._is_public() and request.env.user.has_group('base.group_portal'):
            # Find portal access record for this user and mark it accessed
            portal_access = request.env[PORTAL_ACCESS_MODEL].sudo().search([
                ('quiz_id', '=', quiz.id),
                ('user_id', '=', request.env.user.id),
            ], limit=1)
            if portal_access:
                portal_access.write({
                    'state': 'accessed',
                    'last_access': fields.Datetime.now()
                })
        
        # Include access token if provided (keep original token value)
        redirect_url = f'/quiz/{slug}/question/1?session={session.session_token}'
        if mode:
            redirect_url += f'&mode={mode.key}'
        if kwargs.get('token'):
            redirect_url += f'&token={kwargs.get("token")}'

        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug("quiz_start redirect -> %s", redirect_url)
        return request.redirect(redirect_url)

    def _diagnose_question_type_field(self, question):
        """Helper method to diagnose issues with the question type field"""
        try:
            # Get all fields from the model
            model_fields = request.env['quiz.question']._fields
            field_names = list(model_fields.keys())
            
            # Get the type field's technical details
            type_field = model_fields.get('type')
            type_field_info = {
                'name': 'type',
                'type': type_field.type if type_field else 'not found',
                'selection': dict(type_field.selection) if type_field and hasattr(type_field, 'selection') else {},
                'stored': type_field.store if type_field else False,
                'required': type_field.required if type_field else False,
            }
            
            # Check for potential alternative/conflicting fields
            alt_fields = []
            for name in field_names:
                if name != 'type' and ('type' in name or name.endswith('_type')):
                    field = model_fields.get(name)
                    alt_fields.append({
                        'name': name,
                        'type': field.type if field else 'unknown',
                        'selection': dict(field.selection) if field and hasattr(field, 'selection') else {},
                        'value': getattr(question, name, None),
                    })
            
            # Get actual value
            type_value = getattr(question, 'type', 'not accessible')
            
            return {
                'field_info': type_field_info,
                'field_value': type_value,
                'field_value_type': type(type_value).__name__,
                'alternative_fields': alt_fields,
                'all_fields': field_names[:30],  # Just show first 30 fields
                'model_name': question._name,
                'record_id': question.id,
            }
        except Exception as e:
            return {'error': str(e)}
    
    @http.route(['/quiz/<string:slug>/question/<int:question_num>'], type='http', auth='public', methods=['GET', 'POST'], csrf=False, website=True)
    def quiz_question(self, slug, question_num, **kwargs):
        """Display or process a quiz question"""
        session_token = request.params.get('session')
        session = request.env['quiz.session'].sudo().search([('session_token', '=', session_token)], limit=1)
        
        if not session or session.state != 'in_progress':
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug("quiz_question: invalid session redirect -> %s (session=%s, state=%s)", ROUTE_QUIZ, getattr(session, 'session_token', None), getattr(session, 'state', None))
            return request.redirect(ROUTE_QUIZ)
        
        quiz = session.quiz_id
        # Reconstruct ordered question list from stored order for consistency
        if session.question_order:
            id_order = [int(x) for x in session.question_order.split(',') if x]
            existing_ids = [qid for qid in id_order if qid in quiz.question_ids.ids]
            if existing_ids:
                questions = quiz.question_ids.browse(existing_ids)
            else:
                questions = quiz.question_ids
        else:
            questions = quiz.question_ids.sorted(lambda q: q.sequence)
        
        # Apply access filters based on user type
        if request.env.user._is_public():
            # Public users can only access public questions
            questions = questions.filtered(lambda q: 
                q.access_mode == 'public' or 
                (q.access_mode == 'inherit' and q.category_id and q.category_id.access_mode == 'public'))
        elif request.env.user.has_group(GROUP_PORTAL):
            # Portal users can access public and portal questions
            questions = questions.filtered(lambda q: 
                q.access_mode in ['public', 'portal'] or 
                (q.access_mode == 'inherit' and q.category_id and q.category_id.access_mode in ['public', 'portal']))
        
        # Check for token-based access to question categories
        token = kwargs.get('token')
        if token:
            invitation = request.env[INVITATION_MODEL].sudo().validate_token(token)
            if invitation and invitation.category_ids:
                # Include questions from allowed categories
                category_ids = invitation.category_ids.ids
                more_questions = quiz.question_ids.filtered(
                    lambda q: q.category_id and q.category_id.id in category_ids
                )
                questions |= more_questions
        
        # Sort questions by sequence
        questions = questions.sorted(lambda q: q.sequence)
        
        # Get the requested question by position
        question = questions[question_num - 1] if questions and len(questions) >= question_num else None
        
        if not question:
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug("quiz_question: missing question redirect -> %s (question_num=%s)", ROUTE_QUIZ, question_num)
            return request.redirect(ROUTE_QUIZ)
        
        if request.httprequest.method == 'POST':
            # Handle answer submission
            answer_data = request.params.get('answer_data')
            request.env[RESPONSE_MODEL].sudo().create({
                'session_id': session.id,
                'question_id': question.id,
                'answer_data': json.dumps(answer_data) if answer_data else '{}',
            })
            
            # Get access token if provided
            access_token = kwargs.get('token')

            if len(questions) == question_num:
                # Last question, complete the quiz
                session.write({'state': 'completed', 'end_time': fields.Datetime.now()})

                # Include access token in results URL if provided
                results_url = f'/quiz/session/{session.session_token}/results'
                if access_token:
                    results_url += f'?token={access_token}'
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug("quiz_question (last) redirect -> %s", results_url)
                return request.redirect(results_url)
            else:
                # Next question with access token if provided
                next_url = f'/quiz/{slug}/question/{question_num + 1}?session={session.session_token}'
                if access_token:
                    next_url += f'&token={access_token}'
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug("quiz_question (next) redirect -> %s", next_url)
                return request.redirect(next_url)
        
        values = {
            'quiz': quiz,
            'session': session,
            'question': question,
            'question_index': question_num - 1,
            'token': token,  # Pass token to templates
        }
        
        # Special handling for passage questions
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(f"Question info: ID={question.id}, type={question.type}, type_class={type(question.type).__name__}")
        
        # Detailed field diagnostics
        field_diagnostics = self._diagnose_question_type_field(question)
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug(f"Field diagnostics: {field_diagnostics}")
        
        if question.type == 'passage':
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug(f"Passage question found (ID: {question.id}). Passages: {question.passage_ids}. " +
                        f"First passage has {len(question.passage_ids[0].sub_question_ids) if question.passage_ids else 0} sub-questions.")
        else:
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug(f"Non-passage question detected. Has attributes: passage_ids={hasattr(question, 'passage_ids')}, " +
                        f"available fields={dir(question)[:30]}")
            
        # Add diagnostics to template values
        values['field_diagnostics'] = field_diagnostics
        
        # Add this code to change the message display
        if question.type == 'step_sequence':
            sequence_items = question.sequence_item_ids
            if not sequence_items:
                values['error_message'] = _("This question doesn't have any sequence steps defined.")
        
        return request.render('quiz_engine_pro.quiz_question', values)

    @http.route('/quiz/session/<string:token>/results', type='http', auth='public', website=True)
    def quiz_results(self, token, **kwargs):
        """View quiz results"""
        session = request.env[SESSION_MODEL].sudo().search([('session_token', '=', token)], limit=1)
        if not session:
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug("quiz_results: session not found redirect -> %s (token=%s)", ROUTE_QUIZ, token)
            return request.redirect(ROUTE_QUIZ)
        
        # Calculate results if not already calculated
        if session.state == 'completed' and not session.total_score:
            responses = request.env[RESPONSE_MODEL].sudo().search([('session_id', '=', session.id)])
            total_score = 0
            max_score = sum(session.quiz_id.question_ids.mapped('points'))
            for response in responses:
                # Use _evaluate_answer for accurate scoring
                score = self._evaluate_answer(response.question_id, response.answer_data)
                total_score += score
            percentage = (total_score / max_score * 100) if max_score > 0 else 0
            session.write({
                'total_score': total_score,
                'percentage': percentage,
                'passed': percentage >= session.quiz_id.passing_score,
            })
        
        values = {
            'session': session,
            'quiz': session.quiz_id,
            'score': session.total_score,
            'max_score': sum(session.quiz_id.question_ids.mapped('points')),
        }
        return request.render('quiz_engine_pro.quiz_results_custom', values)

    def _evaluate_answer(self, question, answer_data):
        """Evaluate answer based on question type"""
        if not answer_data:
            return 0
            
        try:
            # Convert answer_data to proper format if needed
            if isinstance(answer_data, str):
                answer_data = json.loads(answer_data)

            # MCQ Single: answer_data is choice id (str or int)
            if question.type == 'mcq_single':
                correct_choice = question.choice_ids.filtered(lambda c: c.is_correct)
                correct_id = str(correct_choice[0].id) if correct_choice else None
                user_choice = str(answer_data) if answer_data is not None else None
                if correct_id and user_choice == correct_id:
                    return question.points
                return 0

            # MCQ Multiple: answer_data is list of choice ids
            elif question.type == 'mcq_multiple':
                correct_choices = {str(c.id) for c in question.choice_ids.filtered(lambda c: c.is_correct)}
                user_choices = {str(cid) for cid in (answer_data or [])}
                if user_choices == correct_choices:
                    return question.points
                return 0
                
            # Passage Question: evaluate each sub-question
            elif question.type == 'passage':
                if not question.passage_ids or not answer_data:
                    return 0
                
                # Total points is sum of sub-question points
                total_score = 0
                
                # Process each sub-question answer
                for passage in question.passage_ids:
                    for sub_q in passage.sub_question_ids:
                        sub_q_key = f'sub_q_{sub_q.id}'
                        if sub_q_key in answer_data:
                            sub_answer = answer_data[sub_q_key]
                            
                            # Evaluate based on sub-question type
                            if sub_q.question_type == 'mcq_single':
                                correct_choice = sub_q.choice_ids.filtered(lambda c: c.is_correct)
                                correct_id = str(correct_choice[0].id) if correct_choice else None
                                user_choice = str(sub_answer) if sub_answer is not None else None
                                if correct_id and user_choice == correct_id:
                                    total_score += sub_q.points
                                    
                            elif sub_q.question_type == 'mcq_multiple':
                                correct_choices = {str(c.id) for c in sub_q.choice_ids.filtered(lambda c: c.is_correct)}
                                user_choices = {str(cid) for cid in (sub_answer or [])}
                                if user_choices == correct_choices:
                                    total_score += sub_q.points
                                    
                            elif sub_q.question_type in ['text_short', 'text_long']:
                                # Simple text match or keywords check
                                if sub_q.correct_answer and isinstance(sub_answer, str):
                                    # Check for exact match or keywords
                                    correct_keywords = [k.strip().lower() for k in sub_q.correct_answer.split(',')]
                                    user_answer = sub_answer.lower()
                                    
                                    if any(kw in user_answer for kw in correct_keywords if kw):
                                        total_score += sub_q.points
                
                return total_score
            
            # ...other question types...
                
            elif question.type == 'step_sequence':
                try:
                    if not answer_data or not question.sequence_item_ids:
                        return 0.0
                        
                    data = json.loads(answer_data) if isinstance(answer_data, str) else answer_data
                    total_steps = len(question.sequence_item_ids)
                    
                    # Get correct positions from question
                    correct_positions = {}
                    for item in question.sequence_item_ids:
                        correct_positions[item.id] = item.correct_position
                    
                    # Get the user's sequence
                    user_sequence = {}
                    for entry in data:
                        step_id = entry.get('step_id')
                        position = entry.get('position')
                        if step_id is not None and position is not None:
                            user_sequence[step_id] = position  # Already 0-indexed from frontend
                    
                    # Count correct positions
                    correct_count = 0
                    for step_id, correct_pos in correct_positions.items():
                        if step_id in user_sequence and user_sequence[step_id] == correct_pos:
                            correct_count += 1
                    
                    # Calculate score as percentage of correct positions
                    return (correct_count / total_steps) * question.points
                    
                except Exception as e:
                    _logger.exception("Error evaluating sequence question: %s", e)
                    return 0.0
            
            return 0
            
        except Exception as e:
            _logger.error(f"Error evaluating answer: {e}")
            return 0
