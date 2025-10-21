```mermaid
flowchart TD
    A[Start] --> B{Is user an Admin?}
    B -->|Yes| C[Access Quiz Menu]
    B -->|No| D[Access Public Quiz URL]
    
    C --> C1[Create New Quiz]
    C1 --> C2[Add Questions]
    C2 --> C3[Toggle Published ON]
    C3 --> C4[Share Quiz URL]
    
    D --> D1[Enter Name/Email]
    D1 --> D2[Start Quiz]
    D2 --> D3[Answer Questions]
    D3 --> D4[Submit Quiz]
    D4 --> D5[View Results]
    
    C4 --> D
    
    C --> E[View Quiz Sessions]
    E --> E1[Analyze Results]
    
    C --> F[Manage Questions]
    F --> F1[Add/Edit Questions]
    
    C --> G[Toggle Published Status]
    G -->|ON| G1[Quiz Available to Users]
    G -->|OFF| G2[Quiz Hidden from Users]
```

# Quiz Module Workflow

The diagram above illustrates the primary workflows for administrators and end users within the Quiz module.

## Administrator Workflow

Administrators follow this process:
1. Access the Quiz menu
2. Create a new quiz with settings
3. Add various types of questions
4. Toggle the Published status ON
5. Share the quiz URL with users
6. View and analyze quiz sessions

## End User Workflow

Users follow this process:
1. Access the public quiz URL
2. Enter their name and email
3. Start the quiz
4. Answer each question
5. Submit the quiz
6. View their results

## Enabling/Disabling Quiz Workflow

The administrator can easily control quiz availability:
- Toggle Published ON: Quiz becomes available to all users
- Toggle Published OFF: Quiz becomes hidden from all users

This simple control allows for preparing quizzes in advance and making them available only when needed.
