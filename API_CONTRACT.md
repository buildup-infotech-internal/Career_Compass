# Career Compass — API Contract

**API Version:** v1  
**Backend:** Python + FastAPI  
**ORM:** SQLAlchemy 2.0  
**Database:** PostgreSQL (Supabase)  
**Validation:** Pydantic  
**Authentication:** Supabase Auth JWT

---

## 1. General API conventions

### Base URL

```text
/api/v1
```

All endpoints will use this prefix.

### Authentication

Authentication and account registration will be handled by Supabase Auth.

The frontend will:

1. Register or log in through Supabase.
2. Receive an access token.
3. Include the access token in requests to FastAPI.

Header:

```http
Authorization: Bearer <supabase_access_token>
```

FastAPI will verify the JWT and identify the authenticated user.

`GET /api/v1/auth/me` returns the verified user UUID and the associated application profile, or `null` when the profile has not yet been initialized. It does not create or modify a profile; use `PUT /api/v1/profiles/me` for idempotent profile initialization/update.

### Standard success response

```json
{
  "success": true,
  "message": "Request completed successfully",
  "data": {}
}
```

### Standard error response

```json
{
  "success": false,
  "message": "Something went wrong",
  "errors": []
}
```

### Pagination

List endpoints that support pagination will use:

```text
?page=1&limit=20
```

Paginated response:

```json
{
  "success": true,
  "message": "Records retrieved successfully",
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

---

# 2. Profile APIs

Base path: `/profiles`

| Method | Endpoint       | Purpose                                                        | Authentication |
| ------ | -------------- | -------------------------------------------------------------- | -------------- |
| GET    | `/profiles/me` | Get current learner profile                                    | Required       |
| PUT    | `/profiles/me` | Create or update learner profile                               | Required       |
| DELETE | `/profiles/me` | Delete current learner profile and associated application data | Required       |

`DELETE /profiles/me` removes the authenticated user's application profile and its dependent application data. It does not delete the user's Supabase Auth identity; identity deletion, if required, must use a trusted Supabase Auth workflow rather than direct database access.

### GET `/profiles/me`

Response:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "full_name": "John Doe",
    "phone": "9876543210",
    "location": "Surat, India",
    "education": [],
    "experience": [],
    "account_role": "learner"
  }
}
```

### PUT `/profiles/me`

Request:

```json
{
  "full_name": "John Doe",
  "phone": "9876543210",
  "location": "Surat, India",
  "education": [
    {
      "degree": "B.Tech",
      "institution": "ABC University",
      "year": 2025
    }
  ],
  "experience": [
    {
      "company": "ABC Technologies",
      "role": "Intern",
      "duration_months": 6,
      "description": "Worked on Python applications"
    }
  ]
}
```

Education and experience are stored as JSONB.

The backend must not allow users to update their own `account_role`.

---

# 3. Resume APIs

Base path: `/resume`

| Method | Endpoint          | Purpose                                      | Authentication |
| ------ | ----------------- | -------------------------------------------- | -------------- |
| POST   | `/resume/extract` | Extract structured information from a resume | Required       |

### POST `/resume/extract`

Content type:

```http
multipart/form-data
```

Request:

```text
file: resume.pdf
```

Supported formats:

- PDF
- DOCX

Maximum file size: 1 MB.

Response:

```json
{
  "success": true,
  "message": "Resume processed successfully",
  "data": {
    "full_name": "John Doe",
    "education": [],
    "experience": [],
    "skills": ["Python", "SQL", "Power BI"]
  }
}
```

**Important behavior:**

- Validate file type and size on the backend.
- Extract text using Python libraries.
- Use Gemini or Groq to structure the extracted information.
- Validate AI output using Pydantic.
- Return extracted information for user review.
- Do not automatically save extracted information to the database.
- Discard the original file and temporary extracted text after processing.

The learner confirms the extracted details using `PUT /profiles/me` and the relevant skill APIs.

---

# 4. Career Role APIs

Base path: `/career-roles`

| Method | Endpoint                         | Purpose                               | Authentication |
| ------ | -------------------------------- | ------------------------------------- | -------------- |
| GET    | `/career-roles`                  | Get available career roles            | Required       |
| GET    | `/career-roles/{role_id}`        | Get career role details               | Required       |
| GET    | `/career-roles/{role_id}/skills` | Get relevant skills for a career role | Required       |

Example response:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Data Analyst",
      "description": "Analyze data and generate insights"
    }
  ]
}
```

---

# 5. Learner Interest APIs

Base path: `/interests`

| Method | Endpoint                   | Purpose                                 | Authentication |
| ------ | -------------------------- | --------------------------------------- | -------------- |
| GET    | `/interests`               | Get learner's selected career interests | Required       |
| POST   | `/interests`               | Add a career interest                   | Required       |
| PUT    | `/interests/{interest_id}` | Update an interest                      | Required       |
| DELETE | `/interests/{interest_id}` | Remove an interest                      | Required       |

### POST `/interests`

Request:

```json
{
  "career_role_id": "uuid",
  "is_primary": true
}
```

A learner can have multiple career interests but only one primary interest at a time.

---

# 6. Skills APIs

Base path: `/skills`

| Method | Endpoint                | Purpose                          | Authentication |
| ------ | ----------------------- | -------------------------------- | -------------- |
| GET    | `/skills`               | Get available skills             | Required       |
| GET    | `/skills/me`            | Get learner's skills             | Required       |
| POST   | `/skills/me`            | Add a learner skill              | Required       |
| PUT    | `/skills/me/{skill_id}` | Update learner skill information | Required       |
| DELETE | `/skills/me/{skill_id}` | Remove learner skill             | Required       |

### POST `/skills/me`

Request:

```json
{
  "skill_id": "uuid",
  "proficiency_level": "intermediate",
  "evidence_source": "manual"
}
```

Possible evidence sources:

- `manual`
- `resume`
- `assessment`

The backend should maintain canonical skill records and prevent duplicate learner-skill associations.

---

# 7. Assessment APIs

Base path: `/assessments`

| Method | Endpoint                              | Purpose                          | Authentication |
| ------ | ------------------------------------- | -------------------------------- | -------------- |
| GET    | `/assessments/questions`              | Get questions for a career role  | Required       |
| POST   | `/assessments/start`                  | Start an assessment              | Required       |
| GET    | `/assessments/{assessment_id}`        | Get assessment details           | Required       |
| POST   | `/assessments/{assessment_id}/submit` | Submit assessment answers        | Required       |
| GET    | `/assessments/history`                | Get previous assessment attempts | Required       |

### POST `/assessments/start`

Request:

```json
{
  "career_role_id": "uuid"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "assessment_id": "uuid",
    "career_role": "Data Analyst",
    "total_questions": 20,
    "questions": [
      {
        "id": "uuid",
        "question_text": "Which SQL command retrieves records?",
        "options": ["SELECT", "INSERT", "UPDATE", "DELETE"],
        "difficulty": "easy"
      }
    ]
  }
}
```

Correct answers must never be returned in the question response.

### POST `/assessments/{assessment_id}/submit`

Request:

```json
{
  "answers": [
    {
      "question_id": "uuid",
      "selected_answer": "SELECT"
    }
  ]
}
```

Response:

```json
{
  "success": true,
  "message": "Assessment submitted successfully",
  "data": {
    "assessment_id": "uuid",
    "total_questions": 20,
    "correct_answers": 15,
    "score": 75,
    "skill_results": [
      {
        "skill": "SQL",
        "score": 80,
        "proficiency_level": "intermediate"
      }
    ]
  }
}
```

Scoring will be performed by Python, not by an AI model.

The backend must verify assessment ownership, validate submitted question IDs and prevent duplicate submissions.

---

# 8. Job APIs

Base path: `/jobs`

| Method | Endpoint         | Purpose                   | Authentication |
| ------ | ---------------- | ------------------------- | -------------- |
| GET    | `/jobs`          | Get available jobs        | Required       |
| GET    | `/jobs/{job_id}` | Get job details           | Required       |
| GET    | `/jobs/filters`  | Get available job filters | Required       |

### GET `/jobs`

Supported query parameters:

```text
/jobs?page=1&limit=20
/jobs?location=Surat
/jobs?employment_type=full_time
/jobs?keyword=Python
/jobs?min_salary=300000
```

Filters can be combined.

Example response:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "Junior Python Developer",
        "company": "ABC Technologies",
        "location": "Ahmedabad",
        "employment_type": "full_time",
        "application_url": "https://example.com/apply",
        "posted_at": "2026-11-20T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

Only active jobs should be returned by default.

Job data will be populated by scheduled ingestion, not by making an external API request every time a learner searches.

---

# 9. Job Matching APIs

Base path: `/matches`

| Method | Endpoint            | Purpose                                | Authentication |
| ------ | ------------------- | -------------------------------------- | -------------- |
| GET    | `/matches`          | Get learner's saved job matches        | Required       |
| GET    | `/matches/{job_id}` | Get match details for a particular job | Required       |
| POST   | `/matches/refresh`  | Recalculate and save job matches       | Required       |

### POST `/matches/refresh`

Request:

```json
{
  "career_role_id": "uuid"
}
```

Response:

```json
{
  "success": true,
  "message": "Job matches generated successfully",
  "data": {
    "total_matches": 25,
    "matches": [
      {
        "job_id": "uuid",
        "job_title": "Junior Python Developer",
        "match_score": 85,
        "matched_skills": ["Python", "SQL"],
        "missing_skills": ["Docker"],
        "explanation": "Your Python and SQL skills align with the main requirements."
      }
    ]
  }
}
```

Matching will be calculated using our custom Python matching engine.

Gemini or Groq may generate explanations, but the numerical score must come from deterministic backend calculations.

Results will be saved in `job_matches` and updated when refreshed.

---

# 10. Learning APIs

Base paths: `/learning-resources` and `/learning-plans`

| Method | Endpoint                                    | Purpose                               | Authentication |
| ------ | ------------------------------------------- | ------------------------------------- | -------------- |
| GET    | `/learning-resources`                       | Get available learning resources      | Required       |
| GET    | `/learning-resources/{resource_id}`         | Get resource details                  | Required       |
| GET    | `/learning-plans`                           | Get learner's learning plans          | Required       |
| POST   | `/learning-plans/generate`                  | Generate a personalized learning plan | Required       |
| GET    | `/learning-plans/{plan_id}`                 | Get a particular learning plan        | Required       |
| PUT    | `/learning-plans/{plan_id}`                 | Update plan information               | Required       |
| PATCH  | `/learning-plans/{plan_id}/steps/{step_id}` | Update learning-step progress         | Required       |
| DELETE | `/learning-plans/{plan_id}`                 | Delete a learning plan                | Required       |

### POST `/learning-plans/generate`

Request:

```json
{
  "career_role_id": "uuid"
}
```

The backend will:

1. Retrieve learner skills.
2. Identify missing or weaker skills for the selected role.
3. Retrieve relevant verified learning resources.
4. Use AI to organize a learning roadmap.
5. Save the plan and its steps.

Response:

```json
{
  "success": true,
  "data": {
    "plan_id": "uuid",
    "title": "Data Analyst Learning Roadmap",
    "steps": [
      {
        "id": "uuid",
        "title": "Learn SQL Fundamentals",
        "skill": "SQL",
        "resource_url": "https://example.com/sql-course",
        "status": "pending"
      }
    ]
  }
}
```

Resource links must come from our verified resource catalogue rather than unverified AI-generated URLs.

### PATCH `/learning-plans/{plan_id}/steps/{step_id}`

Request:

```json
{
  "status": "completed"
}
```

Supported statuses:

- `pending`
- `in_progress`
- `completed`

The backend will set `completed_at` when a step is completed.

---

# 11. Career Assistant APIs

Base path: `/chat`

| Method | Endpoint                               | Purpose                     | Authentication |
| ------ | -------------------------------------- | --------------------------- | -------------- |
| GET    | `/chat/sessions`                       | Get learner's chat sessions | Required       |
| POST   | `/chat/sessions`                       | Create a chat session       | Required       |
| GET    | `/chat/sessions/{session_id}/messages` | Get conversation history    | Required       |
| POST   | `/chat/sessions/{session_id}/messages` | Send a message              | Required       |
| DELETE | `/chat/sessions/{session_id}`          | Delete a conversation       | Required       |

### POST `/chat/sessions`

Request:

```json
{
  "title": "Career Guidance"
}
```

### POST `/chat/sessions/{session_id}/messages`

Request:

```json
{
  "message": "What skills should I learn to become a Data Analyst?"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "message_id": "uuid",
    "reply": "To become a Data Analyst, start with SQL, Excel, Python and statistics...",
    "provider": "gemini",
    "created_at": "2026-11-24T10:00:00Z"
  }
}
```

The assistant will receive relevant learner context, such as:

- Current skills
- Selected career interests
- Assessment results
- Learning plan
- Relevant job recommendations

AI responses will be generated using Gemini primarily, with Groq as fallback when appropriate.

User and assistant messages will be persisted in `chat_messages`.

---

# 12. Feedback APIs

Base path: `/feedback`

| Method | Endpoint       | Purpose                          | Authentication |
| ------ | -------------- | -------------------------------- | -------------- |
| POST   | `/feedback`    | Submit feedback                  | Required       |
| GET    | `/feedback/me` | Get learner's submitted feedback | Required       |

### POST `/feedback`

Request:

```json
{
  "category": "job_recommendations",
  "rating": 4,
  "message": "The recommendations were relevant."
}
```

Possible categories:

- `job_recommendations`
- `learning_roadmap`
- `career_assistant`
- `assessment`
- `general`

---

# 13. Admin APIs

Base path: `/admin`

All endpoints require authenticated administrator authorization.

| Method | Endpoint                        | Purpose                         |
| ------ | ------------------------------- | ------------------------------- |
| GET    | `/admin/analytics`              | Get platform statistics         |
| GET    | `/admin/learners`               | Get learner list                |
| GET    | `/admin/jobs`                   | Manage and inspect job listings |
| GET    | `/admin/ingestion-logs`         | View job ingestion history      |
| GET    | `/admin/feedback`               | Review submitted feedback       |
| POST   | `/admin/career-roles`           | Create a career role            |
| PUT    | `/admin/career-roles/{role_id}` | Update a career role            |
| POST   | `/admin/skills`                 | Add a skill                     |
| POST   | `/admin/assessment-questions`   | Create an assessment question   |
| POST   | `/admin/learning-resources`     | Add a learning resource         |

### GET `/admin/analytics`

Example response:

```json
{
  "success": true,
  "data": {
    "total_learners": 500,
    "total_jobs": 1200,
    "total_assessments": 350,
    "popular_career_roles": [],
    "common_missing_skills": [],
    "learning_plan_completion": {}
  }
}
```

These are illustrative response fields, not actual platform statistics.

Admin access must be verified on the backend. Never trust a role value supplied by the frontend.

---

# 14. System Health API

| Method | Endpoint  | Purpose              | Authentication |
| ------ | --------- | -------------------- | -------------- |
| GET    | `/health` | Check backend health | Public         |

Example response:

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected",
    "version": "1.0.0"
  }
}
```

Do not expose database credentials, internal stack traces or sensitive configuration through this endpoint.

---

# 15. Standard HTTP status codes

| Status | Meaning                | Usage                                     |
| ------ | ---------------------- | ----------------------------------------- |
| 200    | OK                     | Successful GET or update                  |
| 201    | Created                | Resource created                          |
| 204    | No Content             | Successful deletion with no response body |
| 400    | Bad Request            | Invalid request                           |
| 401    | Unauthorized           | Missing or invalid authentication         |
| 403    | Forbidden              | Insufficient permissions                  |
| 404    | Not Found              | Requested resource does not exist         |
| 409    | Conflict               | Duplicate or conflicting operation        |
| 413    | Payload Too Large      | Resume exceeds 1 MB                       |
| 415    | Unsupported Media Type | Unsupported file format                   |
| 422    | Validation Error       | Pydantic validation failure               |
| 429    | Too Many Requests      | Rate limit exceeded                       |
| 500    | Internal Server Error  | Unexpected backend error                  |
| 503    | Service Unavailable    | Required service temporarily unavailable  |

---

# 16. General backend rules

1. All protected endpoints must verify the Supabase JWT.
2. Users can access only their own learner records.
3. Admin endpoints must enforce administrator authorization.
4. Use Pydantic request and response schemas.
5. Use SQLAlchemy for all application database operations.
6. Use Alembic for database schema migrations.
7. Use database transactions for operations involving multiple related records.
8. Never expose API keys or secrets to the frontend.
9. Validate uploaded resumes on the backend.
10. Keep AI provider calls inside backend service modules.
11. Implement consistent exception handling.
12. Add pagination to potentially large list endpoints.
13. Avoid returning unnecessary personal information.
14. Implement proper deletion of related learner data.
15. Use appropriate rate limits for expensive AI endpoints.
16. Keep external job-provider integration separate from job listing and matching APIs.

## 17. Suggested backend module organization

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── profiles.py
│   │       ├── resume.py
│   │       ├── career_roles.py
│   │       ├── interests.py
│   │       ├── skills.py
│   │       ├── assessments.py
│   │       ├── jobs.py
│   │       ├── matches.py
│   │       ├── learning.py
│   │       ├── chat.py
│   │       ├── feedback.py
│   │       ├── admin.py
│   │       └── health.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── core/
│   ├── db/
│   └── utils/
│
├── alembic/
├── scripts/
├── tests/
├── alembic.ini
├── requirements.txt
└── .env.example
```

The directory structure is a proposed implementation layout. It does not introduce additional API requirements.

---

**Document status:** Initial API contract — ready for implementation review.

The contract may evolve during development, but any changes to endpoint paths, request/response structures or authentication behavior should be reflected here and communicated to the frontend.
