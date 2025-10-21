from odoo.tests.common import TransactionCase, Form
import json

class TestMatrixQuestion(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a quiz
        self.quiz = self.env['quiz.quiz'].create({
            'name': 'Test Matrix Quiz',
            'description': '<p>Test Matrix Quiz Description</p>',
        })
        
    def test_matrix_question_creation(self):
        """Test the creation of a matrix question with rows and columns"""
        # Create a matrix question using Form to simulate the UI
        with Form(self.env['quiz.question']) as form:
            form.quiz_id = self.quiz
            form.type = 'matrix'
            form.question_html = "<p>Select the correct options in the matrix:</p>"
            form.points = 2.0
            
        question = form.save()
        
        # Add rows, columns, and cells
        row1 = self.env['quiz.matrix.row'].create({
            'question_id': question.id,
            'name': 'Row 1',
            'sequence': 1,
        })
        
        row2 = self.env['quiz.matrix.row'].create({
            'question_id': question.id,
            'name': 'Row 2',
            'sequence': 2,
        })
        
        col1 = self.env['quiz.matrix.column'].create({
            'question_id': question.id,
            'name': 'Column 1',
            'sequence': 1,
        })
        
        col2 = self.env['quiz.matrix.column'].create({
            'question_id': question.id,
            'name': 'Column 2',
            'sequence': 2,
        })
        
        # Create cells with correct values
        cell1 = self.env['quiz.matrix.cell'].create({
            'row_id': row1.id,
            'column_id': col1.id,
            'is_correct': True,
        })
        
        cell2 = self.env['quiz.matrix.cell'].create({
            'row_id': row1.id,
            'column_id': col2.id,
            'is_correct': False,
        })
        
        cell3 = self.env['quiz.matrix.cell'].create({
            'row_id': row2.id,
            'column_id': col1.id,
            'is_correct': False,
        })
        
        cell4 = self.env['quiz.matrix.cell'].create({
            'row_id': row2.id,
            'column_id': col2.id,
            'is_correct': True,
        })
        
        # Verify the created question and components
        self.assertEqual(question.type, 'matrix')
        self.assertEqual(len(question.matrix_row_ids), 2)
        self.assertEqual(len(question.matrix_column_ids), 2)
        self.assertEqual(len(question.matrix_cell_ids), 4)
        
        # Verify that the correct cells are marked
        self.assertTrue(cell1.is_correct)
        self.assertFalse(cell2.is_correct)
        self.assertFalse(cell3.is_correct)
        self.assertTrue(cell4.is_correct)
        
    def test_matrix_question_evaluation(self):
        """Test the evaluation of matrix question answers"""
        # Create a question with rows, columns, and cells
        question = self.env['quiz.question'].create({
            'quiz_id': self.quiz.id,
            'type': 'matrix',
            'question_html': '<p>Select the correct options in the matrix:</p>',
            'points': 2.0,
        })
        
        row1 = self.env['quiz.matrix.row'].create({
            'question_id': question.id,
            'name': 'Row 1',
        })
        
        row2 = self.env['quiz.matrix.row'].create({
            'question_id': question.id,
            'name': 'Row 2',
        })
        
        col1 = self.env['quiz.matrix.column'].create({
            'question_id': question.id,
            'name': 'Column 1',
        })
        
        col2 = self.env['quiz.matrix.column'].create({
            'question_id': question.id,
            'name': 'Column 2',
        })
        
        # Configure correct answers (Row 1 + Column 1, Row 2 + Column 2)
        self.env['quiz.matrix.cell'].create({
            'row_id': row1.id,
            'column_id': col1.id,
            'is_correct': True,
        })
        
        self.env['quiz.matrix.cell'].create({
            'row_id': row1.id,
            'column_id': col2.id,
            'is_correct': False,
        })
        
        self.env['quiz.matrix.cell'].create({
            'row_id': row2.id,
            'column_id': col1.id,
            'is_correct': False,
        })
        
        self.env['quiz.matrix.cell'].create({
            'row_id': row2.id,
            'column_id': col2.id,
            'is_correct': True,
        })
        
        # Test perfect answer (all cells correct)
        perfect_answer = json.dumps({
            f'cell_{row1.id}_{col1.id}': True,
            f'cell_{row1.id}_{col2.id}': False,
            f'cell_{row2.id}_{col1.id}': False,
            f'cell_{row2.id}_{col2.id}': True,
        })
        score = question.evaluate_answer(perfect_answer)
        self.assertEqual(score, 2.0)  # Full points
        
        # Test partially correct answer (75% correct)
        partial_answer = json.dumps({
            f'cell_{row1.id}_{col1.id}': True,
            f'cell_{row1.id}_{col2.id}': False,
            f'cell_{row2.id}_{col1.id}': True,  # Incorrect selection
            f'cell_{row2.id}_{col2.id}': True,
        })
        score = question.evaluate_answer(partial_answer)
        self.assertEqual(score, 1.5)  # 75% of 2.0 = 1.5
        
        # Test incorrect answer
        wrong_answer = json.dumps({
            f'cell_{row1.id}_{col1.id}': False,
            f'cell_{row1.id}_{col2.id}': True,
            f'cell_{row2.id}_{col1.id}': True,
            f'cell_{row2.id}_{col2.id}': False,
        })
        score = question.evaluate_answer(wrong_answer)
        self.assertEqual(score, 0.0)  # No points
