# Quiz Module - Quick Start Guide

This quick reference guide will help you get started with the Quiz module in just a few minutes.

## For Quiz Administrators

### Creating Your First Quiz

1. **Access the Quiz Module**
   - Go to the main menu and click on "Quiz"
   - Select "Quizzes" from the dropdown

2. **Create a New Quiz**
   - Click "Create" button
   - Enter a title (e.g., "Product Knowledge Test")
   - The URL slug will be auto-generated (e.g., "product-knowledge-test")
   - Set passing score (e.g., 70%)
   - Optionally set a time limit
   - Click "Save"

3. **Add Questions**
   - Click "Manage Questions" button
   - Click "Create" to add a question
   - Choose a question type
   - Enter question text
   - Configure answers/options
   - Click "Save"
   - Repeat for additional questions

4. **Publish Your Quiz**
   - Toggle "Published" button to ON (green) 
   - Your quiz is now available to users

### Quick Question Creation Examples

#### Multiple Choice
```
Question: What is the capital of France?
Type: MCQ Single
Options: 
- Paris (Correct)
- London
- Berlin
- Madrid
```

#### Fill in the Blanks
```
Question: The capital of France is {{1}} and the capital of Germany is {{2}}.
Type: Fill Blank
Answers:
1: Paris
2: Berlin
```

### Enabling/Disabling a Quiz

**To Enable:**
- Open the quiz
- Toggle "Published" to ON (green)

**To Disable:**
- Open the quiz
- Toggle "Published" to OFF (gray)

### View Results
- Go to Quiz → Quiz Sessions
- View all attempts and scores
- Click on any session for detailed responses

## For Quiz Takers

### Taking a Quiz

1. **Access the Quiz**
   - Go to: https://your-domain.com/quiz/[quiz-slug]
   - Or browse all quizzes at: https://your-domain.com/quiz

2. **Start the Quiz**
   - Enter your name and email
   - Click "Start Quiz"

3. **Answer Questions**
   - Read each question carefully
   - Submit your answer
   - Click "Next" to proceed

4. **Complete the Quiz**
   - After the last question, click "Submit"
   - View your results and feedback

## Reference Guide

### Question Types Available

1. **Multiple Choice (Single Answer)** - Select one correct option
2. **Multiple Choice (Multiple Answers)** - Select one or more correct options
3. **Fill in the Blanks** - Type missing words in the blanks
4. **Match the Following** - Match items from left and right columns
5. **Drag and Drop into Text** - Place tokens into the correct positions in text
6. **Drag and Drop into Zones** - Place items into designated zones
7. **Dropdown in Text** - Select correct options from dropdown menus in text

### Public URLs

- Quiz List: https://your-domain.com/quiz
- Specific Quiz: https://your-domain.com/quiz/[quiz-slug]
- Results: https://your-domain.com/quiz/session/[session-token]/results

For more detailed instructions, refer to the complete User Guide.
