odoo.define('quiz_engine_pro.drag_functionality', [
    'web.public.widget',
    'web.ajax'
], function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.QuizDragDrop = publicWidget.Widget.extend({
        selector: '.question-form',
        events: {
            'dragstart .drag-token': '_onDragStart',
            'dragover .drop-zone, .text-with-blanks .blank-drop': '_onDragOver',
            'drop .drop-zone, .text-with-blanks .blank-drop': '_onDrop',
            'dragover .match-drop-zone': '_onDragOver',
            'drop .match-drop-zone': '_onMatchDrop',
            'click #next-btn': '_onNextQuestion',
            'click #prev-btn': '_onPrevQuestion',
            'click #submit-btn': '_onSubmitQuiz',
        },

        start: function() {
            this._super.apply(this, arguments);
            this.currentQuestionIndex = 0;
            this.totalQuestions = parseInt(window.totalQuestions || 0);
            this.sessionToken = window.sessionToken;
            this.answers = {};
            this._initializeDragIntoText();
            this._updateNavigation();
            return Promise.resolve();
        },

        _initializeDragIntoText: function () {
            var self = this;
            
            // Process drag-into-text questions
            this.$('.text-with-blanks').each(function () {
                var $container = $(this);
                self._setupDragIntoText($container);
            });
        },

        _setupDragIntoText: function ($container) {
            var self = this;
            
            // Convert {{1}}, {{2}} placeholders to drop zones
            var $questionText = $container.find('.question-with-blanks');
            var html = $questionText.html();
            html = html.replace(/\{\{(\d+)\}\}/g, function(match, blankNumber) {
                return '<span class="blank-drop" data-blank="' + blankNumber + '" style="display: inline-block; min-width: 100px; min-height: 30px; border: 2px dashed #007bff; margin: 0 5px; padding: 5px; background-color: #f8f9fa; text-align: center;">[Drop Here]</span>';
            });
            $questionText.html(html);

            // Make tokens draggable
            $container.find('.drag-token').each(function () {
                var $token = $(this);
                $token.attr('draggable', true);
                
                $token.on('dragstart', function (e) {
                    e.originalEvent.dataTransfer.setData('text/plain', JSON.stringify({
                        text: $token.data('token'),
                        correctZone: $token.data('correct-zone'),
                        correctBlank: $token.data('correct-blank'),
                        pairId: $token.data('pair-id'),
                        leftText: $token.data('left-text')
                    }));
                });
                
                $token.on('dragend', function (e) {
                    $token.removeClass('dragging');
                });
            });

            // Setup drop zones
            $container.find('.drop-zone, .blank-drop').each(function () {
                var $dropzone = $(this);
                
                $dropzone.on('dragover', function (e) {
                    e.preventDefault();
                    $dropzone.addClass('drag-over');
                });
                
                $dropzone.on('dragleave', function (e) {
                    $dropzone.removeClass('drag-over');
                });
                
                $dropzone.on('drop', function (e) {
                    e.preventDefault();
                    $dropzone.removeClass('drag-over');
                    
                    try {
                        var data = JSON.parse(e.originalEvent.dataTransfer.getData('text/plain'));
                        
                        if ($dropzone.hasClass('drop-zone')) {
                            // Drag into zones
                            self._handleZoneDrop($dropzone, data);
                        } else if ($dropzone.hasClass('blank-drop')) {
                            // Drag into text
                            self._handleTextDrop($dropzone, data);
                        }
                    } catch (ex) {
                        console.error('Error processing drop:', ex);
                    }
                });
            });
        },

        _handleZoneDrop: function ($dropZone, data) {
            var $droppedItems = $dropZone.find('.dropped-items');
            $droppedItems.append('<div class="dropped-token badge badge-primary m-1" data-token="' + data.text + '">' + data.text + '</div>');
            this._updateZoneAnswer();
        },

        _handleTextDrop: function ($dropZone, data) {
            $dropZone.text(data.text);
            $dropZone.addClass('filled');
            $dropZone.css('background-color', '#d4edda');
            this._updateTextAnswer();
        },

        _handleMatchDrop: function ($dropZone, data) {
            var $droppedMatch = $dropZone.find('.dropped-match');
            $droppedMatch.html('<div class="matched-item badge badge-success">' + data.leftText + '</div>');
            this._updateMatchAnswer();
        },

        _updateZoneAnswer: function () {
            var answer = {};
            this.$('.drop-zone').each(function () {
                var zone = $(this).data('zone');
                var tokens = [];
                $(this).find('.dropped-token').each(function () {
                    tokens.push($(this).data('token'));
                });
                answer[zone] = tokens;
            });
            this.$('#drag_zone_answer').val(JSON.stringify(answer));
        },

        _updateTextAnswer: function () {
            var answer = {};
            this.$('.blank-drop').each(function () {
                var blank = $(this).data('blank');
                var text = $(this).text();
                if (text !== '[Drop Here]') {
                    answer[blank] = text;
                }
            });
            this.$('#drag_text_answer').val(JSON.stringify(answer));
        },

        _updateMatchAnswer: function () {
            var answer = {};
            this.$('.match-drop-zone').each(function () {
                var pairId = $(this).data('pair-id');
                var rightText = $(this).data('right-text');
                var $matchedItem = $(this).find('.matched-item');
                if ($matchedItem.length) {
                    var leftText = $matchedItem.text();
                    answer['pair_' + pairId] = {
                        left: leftText,
                        right: rightText
                    };
                }
            });
            this.$('#matching_answer').val(JSON.stringify(answer));
        },

        _onNextQuestion: function (e) {
            e.preventDefault();
            this._saveCurrentAnswer();
            
            if (this.currentQuestionIndex < this.totalQuestions - 1) {
                this.currentQuestionIndex++;
                this._showQuestion(this.currentQuestionIndex);
                this._updateNavigation();
            }
        },

        _onPrevQuestion: function (e) {
            e.preventDefault();
            this._saveCurrentAnswer();
            
            if (this.currentQuestionIndex > 0) {
                this.currentQuestionIndex--;
                this._showQuestion(this.currentQuestionIndex);
                this._updateNavigation();
            }
        },

        _showQuestion: function (index) {
            this.$('.question-container').addClass('d-none');
            this.$('.question-container').eq(index).removeClass('d-none');
            this.$('#current-question').text(index + 1);
        },

        _updateNavigation: function () {
            this.$('#prev-btn').prop('disabled', this.currentQuestionIndex === 0);
            
            if (this.currentQuestionIndex === this.totalQuestions - 1) {
                this.$('#next-btn').addClass('d-none');
                this.$('#submit-btn').removeClass('d-none');
            } else {
                this.$('#next-btn').removeClass('d-none');
                this.$('#submit-btn').addClass('d-none');
            }
        },

        _saveCurrentAnswer: function () {
            var $currentQuestion = this.$('.question-container').eq(this.currentQuestionIndex);
            var questionId = $currentQuestion.data('question-id');
            var questionType = $currentQuestion.find('[class*="mcq-"], [class*="drag-"]').attr('class');
            
            if ($currentQuestion.find('.mcq-options').length > 0) {
                this._saveMCQAnswer($currentQuestion, questionId);
            }
            // Drag into text answers are saved in real-time
        },

        _saveMCQAnswer: function ($question, questionId) {
            var answerData = {};
            
            if ($question.find('input[type="radio"]').length > 0) {
                // Single choice
                var selectedChoice = $question.find('input[type="radio"]:checked').val();
                if (selectedChoice) {
                    answerData = { type: 'mcq_single', choice_id: parseInt(selectedChoice) };
                }
            } else if ($question.find('input[type="checkbox"]').length > 0) {
                // Multiple choice
                var selectedChoices = [];
                $question.find('input[type="checkbox"]:checked').each(function () {
                    selectedChoices.push(parseInt($(this).val()));
                });
                answerData = { type: 'mcq_multi', choice_ids: selectedChoices };
            }
            
            if (Object.keys(answerData).length > 0) {
                this.answers[questionId] = answerData;
            }
        },

        _onSubmitQuiz: function (e) {
            e.preventDefault();
            this._saveCurrentAnswer();
            
            // Submit all answers
            var self = this;
            var promises = [];
            
            Object.keys(this.answers).forEach(function (questionId) {
                var promise = ajax.jsonRpc('/quiz/session/' + self.sessionToken + '/answer', 'call', {
                    question_id: parseInt(questionId),
                    answer_data: self.answers[questionId]
                });
                promises.push(promise);
            });
            
            Promise.all(promises).then(function () {
                // Complete the quiz
                window.location.href = '/quiz/session/' + self.sessionToken + '/complete';
            }).catch(function (error) {
                console.error('Error submitting answers:', error);
                alert('Error submitting quiz. Please try again.');
            });
        },
    });

    return publicWidget.registry.QuizDragDrop;
});
