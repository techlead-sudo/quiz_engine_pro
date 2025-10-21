from odoo import models
import json

class QuestionEvaluation(models.Model):
    import logging
    _logger = logging.getLogger(__name__)
    _inherit = 'quiz.question'
    
    def evaluate_answer(self, answer_data):
        """Evaluate answer based on question type"""
        if self.type == 'mcq_single':
            return self._evaluate_mcq_single(answer_data)
        elif self.type == 'mcq_multiple':
            return self._evaluate_mcq_multi(answer_data)
        elif self.type == 'fill_blank':
            return self._evaluate_fill_blank(answer_data)
        elif self.type == 'match':
            return self._evaluate_match(answer_data)
        elif self.type in ['drag_zone', 'drag_text']:
            return self._evaluate_drag_drop(answer_data)
        elif self.type == 'sentence_completion':
            return self._evaluate_sentence_completion(answer_data)
        elif self.type == 'text_box':
            return self._evaluate_text_box(answer_data)
        elif self.type == 'numerical':
            return self._evaluate_numerical(answer_data)
        elif self.type == 'matrix':
            return self._evaluate_matrix(answer_data)
        elif self.type == 'dropdown_blank':
            return self._evaluate_dropdown_blank(answer_data)
        elif self.type == 'passage':
            return self._evaluate_passage(answer_data)
        return 0.0

    def _evaluate_mcq_single(self, answer_data):
        """Evaluate single choice MCQ"""
        if not answer_data or answer_data in ('null', 'None', None, ''):
            return 0.0
        try:
            selected_choice_id = int(answer_data)
        except (ValueError, TypeError):
            return 0.0
        correct_choice = self.choice_ids.filtered('is_correct')
        if correct_choice and selected_choice_id == correct_choice[0].id:
            return self.points
        return 0.0

    def _evaluate_mcq_multi(self, answer_data):
        """Evaluate multiple choice MCQ"""
        if not answer_data:
            return 0.0
        # Accept JSON string or list-like
        try:
            if isinstance(answer_data, str):
                parsed = json.loads(answer_data)
                selected_ids = [int(x) for x in parsed if x]
            else:
                selected_ids = [int(x) for x in answer_data if x]
        except Exception:
            return 0.0
        correct_ids = self.choice_ids.filtered('is_correct').ids
        
        if set(selected_ids) == set(correct_ids):
            return self.points
        return 0.0

    def _evaluate_fill_blank(self, answer_data):
        """Evaluate fill in the blanks robustly"""
        if not answer_data:
            return 0.0
        try:
            answers = json.loads(answer_data) if isinstance(answer_data, str) else answer_data
        except Exception:
            return 0.0
        total_blanks = len(self.fill_blank_answer_ids)
        if total_blanks == 0:
            return 0.0
        correct_count = 0
        for blank_answer in self.fill_blank_answer_ids:
            blank_key = str(blank_answer.blank_number)
            user_answer = answers.get(blank_key, None)
            if user_answer is None or str(user_answer).strip().lower() in ('', 'null', 'none'):
                continue
            correct_answer = blank_answer.answer_text.strip().lower()
            if str(user_answer).strip().lower() == correct_answer:
                correct_count += 1
        return (correct_count / total_blanks) * self.points

    def _evaluate_match(self, answer_data):
        """Evaluate matching questions (by ID or by text)"""
        if not answer_data:
            self._logger.debug("No answer_data provided for match question.")
            return 0.0
        try:
            matches = json.loads(answer_data) if isinstance(answer_data, str) else answer_data
        except Exception as e:
            self._logger.error(f"Failed to parse answer_data: {answer_data}, error: {e}")
            return 0.0
        self._logger.debug(f"Evaluating match question {self.id}: answer_data={matches}")
        total_pairs = len(self.match_pair_ids)
        if total_pairs == 0:
            self._logger.debug("No match pairs defined for question.")
            return 0.0
        correct_count = 0
        if isinstance(matches, list):
            for entry in matches:
                if not isinstance(entry, dict):
                    continue
                lid = entry.get('left_id')
                rid = entry.get('right_id')
                left_pair = self.match_pair_ids.filtered(lambda p: p.id == lid)
                right_pair = self.match_pair_ids.filtered(lambda p: p.id == rid)
                if left_pair and right_pair:
                    left_text = left_pair[0].right_text.strip().lower()
                    right_text = right_pair[0].right_text.strip().lower()
                    self._logger.debug(f"Comparing left_id={lid} right_id={rid}: left_text='{left_text}' right_text='{right_text}'")
                    if left_text == right_text:
                        correct_count += 1
        else:
            for pair in self.match_pair_ids:
                left_key = f"left_{pair.id}"
                right_key = f"right_{pair.id}"
                if left_key in matches and right_key in matches:
                    left_val = matches[left_key].strip().lower()
                    right_val = matches[right_key].strip().lower()
                    self._logger.debug(f"Comparing legacy left_key={left_key} right_key={right_key}: left_val='{left_val}' right_val='{right_val}'")
                    if left_val == right_val:
                        correct_count += 1
        self._logger.debug(f"Match question {self.id}: correct_count={correct_count} / total_pairs={total_pairs}")
        return (correct_count / total_pairs) * self.points

    def _evaluate_drag_drop(self, answer_data):
        """Evaluate drag and drop questions"""
        if not answer_data:
            return 0.0
        
        try:
            placements = json.loads(answer_data) if isinstance(answer_data, str) else answer_data
        except Exception:
            return 0.0
        
        total_tokens = len(self.drag_token_ids)
        if total_tokens == 0:
            return 0.0
        
        correct_count = 0
        # Support three formats:
        # 1. List of {zone: n, token_id: id}
        # 2. Dict {"1": "Token Text"}
        # 3. Dict {"0": "Token Text"} (legacy 0-based)
        token_map_by_id = {t.id: t for t in self.drag_token_ids}
        if isinstance(placements, list):
            # Build a quick lookup keyed by zone (both 0- and 1-based) -> token_id
            zone_to_token_id = {}
            for entry in placements:
                if not isinstance(entry, dict):
                    continue
                z = entry.get('zone')
                tid = entry.get('token_id')
                if isinstance(z, int) and isinstance(tid, int):
                    zone_to_token_id[z] = tid
                    zone_to_token_id[z-1] = tid  # also expose 0-based variant
            for token in self.drag_token_ids:
                tid = token.id
                # Accept correct_position (0-based) OR +1 (1-based UI)
                if zone_to_token_id.get(token.correct_position) == tid or zone_to_token_id.get(token.correct_position + 1) == tid:
                    correct_count += 1
        else:
            # Dict/text mapping variant
            for token in self.drag_token_ids:
                base_key = str(token.correct_position)
                alt_key = str(token.correct_position + 1)
                matched = False
                if base_key in placements and placements[base_key] == token.text:
                    matched = True
                elif alt_key in placements and placements[alt_key] == token.text:
                    matched = True
                if matched:
                    correct_count += 1
        
        return (correct_count / total_tokens) * self.points

    def _evaluate_text_box(self, answer_data):
        """Evaluate text box answers"""
        if not answer_data or not self.correct_text_answer:
            return 0.0
        
        user_answer = answer_data.strip()
        correct_answer = self.correct_text_answer.strip()
        
        # Apply case sensitivity
        if not self.case_sensitive:
            user_answer = user_answer.lower()
            correct_answer = correct_answer.lower()
        
        # Exact match
        if user_answer == correct_answer:
            return self.points
        
        # Partial match if allowed
        if self.allow_partial_match:
            if self.keywords:
                keywords = [k.strip() for k in self.keywords.split(',')]
                # Convert to lowercase if not case sensitive
                if not self.case_sensitive:
                    keywords = [k.lower() for k in keywords]
                
                # Check if all keywords are present
                keywords_found = sum(1 for k in keywords if k in user_answer)
                if keywords_found > 0:
                    return (keywords_found / len(keywords)) * self.points
            else:
                # Simple partial match calculation if no specific keywords
                ratio = len(set(user_answer.split()) & set(correct_answer.split())) / len(set(correct_answer.split()))
                if ratio > 0.5:  # More than half the words match
                    return ratio * self.points
        
        return 0.0

    def _evaluate_numerical(self, answer_data):
        """Evaluate numerical answers"""
        if not answer_data:
            return 0.0
        
        try:
            user_value = float(answer_data)
        except (ValueError, TypeError):
            return 0.0
        
        # Exact value with tolerance
        if self.numerical_exact_value is not False:
            if abs(user_value - self.numerical_exact_value) <= self.numerical_tolerance:
                return self.points
        
        # Range check
        if self.numerical_min_value is not False and self.numerical_max_value is not False:
            if self.numerical_min_value <= user_value <= self.numerical_max_value:
                return self.points
        
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
    
    def _evaluate_dropdown_blank(self, answer_data):
        """Evaluate dropdown in text questions"""
        if not answer_data:
            return 0.0
        
        try:
            answers = json.loads(answer_data) if isinstance(answer_data, str) else answer_data
        except Exception:
            return 0.0
        
        total_blanks = len(self.blank_ids)
        if total_blanks == 0:
            return 0.0
        
        correct_count = 0
        
        # Process each answer
        for entry in answers:
            if 'blank_id' not in entry or 'option_id' not in entry:
                continue
                
            blank_id = entry['blank_id']
            option_id = entry['option_id']
            
            # Check if the selected option is correct
            option = self.env['quiz.option'].sudo().browse(option_id)
            if option and option.is_correct and option.blank_id.id == blank_id:
                correct_count += 1
        
        return (correct_count / total_blanks) * self.points
        
    def _evaluate_sentence_completion(self, answer_data):
        """Evaluate sentence completion questions"""
        if not answer_data:
            return 0.0
        
        try:
            placement_data = json.loads(answer_data) if isinstance(answer_data, str) else answer_data
        except Exception:
            return 0.0
        
        # Check if we have tokens and blanks
        total_blanks = self.question_html.count('{blank}') if self.question_html else 0
        if total_blanks == 0 or not self.drag_token_ids:
            return 0.0
            
        # Create mapping for correct positions
        correct_positions = {}
        
        # Find correct positions based on the {blank} placeholders and tokens' correct_position
        for token in self.drag_token_ids:
            if token.correct_position >= 0 and token.correct_position < total_blanks:
                correct_positions[f"blank_{token.correct_position}"] = token.id
        
        # Count correct placements
        correct_count = self._count_correct_placements(placement_data, correct_positions)
        
        # Calculate score proportionally to correct answers
        return (correct_count / total_blanks) * self.points
        
    def _count_correct_placements(self, placement_data, correct_positions):
        """Helper method to count correct token placements"""
        correct_count = 0
        processed_blanks = set()
        
        for placement in placement_data:
            if 'zone_id' not in placement or 'token_id' not in placement:
                continue
                
            zone_id = placement['zone_id']
            token_id = int(placement['token_id'])
            
            # Prevent counting the same blank multiple times
            if zone_id in processed_blanks:
                continue
                
            processed_blanks.add(zone_id)
            
            # Check if this is the correct token for this zone
            if zone_id in correct_positions and correct_positions[zone_id] == token_id:
                correct_count += 1
                
        return correct_count
        
    def _evaluate_passage(self, answer_data):
        """Evaluate reading passage with multiple questions"""
        if not answer_data:
            return 0.0
        
        try:
            answers = json.loads(answer_data) if isinstance(answer_data, str) else answer_data
        except Exception:
            return 0.0
        
        # Get all passages and sub-questions
        if not self.passage_ids:
            return 0.0
            
        passage = self.passage_ids[0]  # Currently supporting one passage per question
        sub_questions = passage.sub_question_ids
        
        if not sub_questions:
            return 0.0
        
        # Calculate total possible points from all sub-questions
        total_points = sum(q.points for q in sub_questions)
        if total_points == 0:
            return 0.0
        
        # Calculate earned points
        earned_points = 0.0
        
        for sub_q in sub_questions:
            # Accept keys either as raw id ("123") or prefixed ("sub_q_123")
            sub_q_id = str(sub_q.id)
            pref_key = f"sub_q_{sub_q_id}"
            key = sub_q_id if sub_q_id in answers else (pref_key if pref_key in answers else None)
            if not key:
                continue
            sub_answer = answers[key]
            
            # Evaluate based on sub-question type
            if sub_q.question_type == 'mcq_single':
                earned_points += self._evaluate_passage_mcq_single(sub_q, sub_answer)
            elif sub_q.question_type == 'mcq_multiple':
                earned_points += self._evaluate_passage_mcq_multiple(sub_q, sub_answer)
            elif sub_q.question_type in ['text_short', 'text_long']:
                earned_points += self._evaluate_passage_text(sub_q, sub_answer)
        
        # Scale the points to the question's total points
        return (earned_points / total_points) * self.points
    
    def _evaluate_passage_mcq_single(self, sub_q, answer_data):
        """Evaluate single choice MCQ within a passage"""
        if not answer_data:
            return 0.0
        
        selected_choice_id = int(answer_data)
        correct_choice = sub_q.choice_ids.filtered('is_correct')
        
        if correct_choice and selected_choice_id == correct_choice[0].id:
            return sub_q.points
        return 0.0
    
    def _evaluate_passage_mcq_multiple(self, sub_q, answer_data):
        """Evaluate multiple choice MCQ within a passage"""
        if not answer_data:
            return 0.0
        
        selected_ids = [int(x) for x in answer_data if x]
        correct_ids = sub_q.choice_ids.filtered('is_correct').ids
        
        if set(selected_ids) == set(correct_ids):
            return sub_q.points
        return 0.0
    
    def _evaluate_passage_text(self, sub_q, answer_data):
        """Evaluate text answer within a passage"""
        if not answer_data or not sub_q.correct_answer:
            return 0.0
        
        user_answer = answer_data.strip().lower()
        correct_answer = sub_q.correct_answer.strip().lower()
        
        # For short answers, check for exact match or keyword presence
        if sub_q.question_type == 'text_short':
            if user_answer == correct_answer:
                return sub_q.points
                
            # Check for keywords
            keywords = [k.strip().lower() for k in correct_answer.split(',')]
            for keyword in keywords:
                if keyword in user_answer:
                    return sub_q.points
        
        # For long answers, do a more lenient check based on keyword presence
        elif sub_q.question_type == 'text_long':
            keywords = [k.strip().lower() for k in correct_answer.split(',')]
            if not keywords:
                return 0.0
                
            # Calculate how many keywords are present
            keywords_found = sum(1 for k in keywords if k in user_answer)
            if keywords_found > 0:
                return (keywords_found / len(keywords)) * sub_q.points
        
        return 0.0
