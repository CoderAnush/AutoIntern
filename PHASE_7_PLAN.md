# PHASE 7: Email Notifications System

## Objective
Implement complete email notification system for:
1. **Welcome emails** on user registration
2. **Job match alerts** when new recommendations available
3. **Resume upload confirmations** after successful upload
4. **Password change notifications** for security
5. **Email notifications settings** (user preferences)

---

## Current Status Analysis

**Completed Prerequisites:**
- ✅ User authentication system (Phase 5) - Users can register, login, manage accounts
- ✅ Resume processing system (Phase 3) - Resumes uploaded + skills extracted
- ✅ Job recommendation engine (Phase 4) - ML embeddings + FAISS similarity search
- ✅ Frontend dashboard (Phase 6) - Full UI for all features
- ✅ Database structure - Users, resumes, jobs tables ready

**What Phase 7 Adds:**
- Email service integration (SMTP or SendGrid)
- Email templates (HTML + plain text)
- Async email queue (Celery or Redis task queue)
- 4 new API endpoints for email preferences
- Email notification models in database

---

## Architecture Diagram

```
Frontend (Phase 6)
        │
        ├── POST /users/register {email, password}
        │   └─→ Backend creates user
        │       └─→ Send welcome email async
        │
        ├── POST /resumes/upload {file}
        │   └─→ Backend processes resume
        │       ├─→ Extract skills
        │       └─→ Send upload confirmation email
        │
        ├── POST /recommendations/batch-index-jobs
        │   └─→ Backend generates embeddings
        │       └─→ Check for new matches
        │           └─→ Send job alert emails
        │
        └── POST /users/change-password {old, new}
            └─→ Backend updates password
                └─→ Send security notification email

Email System:
┌────────────────────────────────────────────┐
│ Frontend Request                           │
└────────────────┬─────────────────────────┘
                 │
┌────────────────┴─────────────────────────┐
│ Backend Route Handler                    │
│ ├─ Process request                       │
│ ├─ Queue email task                      │
│ └─ Return response immediately           │
└────────────────┬─────────────────────────┘
                 │
┌────────────────┴─────────────────────────┐
│ Redis/Celery Queue                       │
│ ├─ email_task_id: {type, user_id, data} │
│ └─ Persists if service crashes           │
└────────────────┬─────────────────────────┘
                 │
┌────────────────┴─────────────────────────┐
│ Background Worker                        │
│ ├─ Dequeue email task                    │
│ ├─ Render template                       │
│ ├─ Send via SMTP/SendGrid                │
│ └─ Mark as sent/failed                   │
└────────────────┬─────────────────────────┘
                 │
┌────────────────┴─────────────────────────┐
│ User Email Inbox                         │
│ ✉️ Welcome email                         │
│ ✉️ Upload confirmation                   │
│ ✉️ Job match alert                       │
│ ✉️ Security notification                 │
└────────────────────────────────────────┘
```

---

## Implementation Plan

### Step 1: Create Email Service
**File**: `services/api/app/services/email_service.py` (NEW - 200 lines)

**Module**: Email sending business logic

**Class: EmailService**
```python
class EmailService:
    def __init__(self, smtp_host: str, smtp_port: int,
                 sender_email: str, sender_password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    async def send_email(self, to_email: str, subject: str,
                        html_content: str, plain_text: str) -> bool:
        """Send email via SMTP"""
        # Validate email format
        # Connect to SMTP server
        # Send with both HTML and plain text versions
        # Handle retries on failure
        # Return success/failure
        pass

    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user"""
        # Render welcome template
        # Use send_email()
        # Log success/failure
        pass

    async def send_resume_upload_confirmation(self, user_email: str,
                                             resume_name: str, skills: List[str]) -> bool:
        """Send resume upload confirmation"""
        # Render upload template
        # Include file name and detected skills
        # Use send_email()
        pass

    async def send_job_match_alert(self, user_email: str,
                                  resume_name: str, matches: List[dict]) -> bool:
        """Send job match alert when new recommendations available"""
        # Render alert template
        # Include top 5 matching jobs
        # Links to dashboard
        # Use send_email()
        pass

    async def send_password_change_notification(self, user_email: str) -> bool:
        """Send security notification when password changed"""
        # Render security email template
        # Include timestamp, IP address if available
        # Use send_email()
        pass
```

**Constants**:
```python
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@autointern.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
```

---

### Step 2: Create Email Queue Service
**File**: `services/api/app/services/email_queue.py` (NEW - 150 lines)

**Module**: Async email task queue (using Redis + Celery or RQ)

**Class: EmailQueue**
```python
class EmailQueue:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.queue_key = "email_queue"

    async def enqueue_welcome_email(self, user_id: str, user_email: str,
                                   user_name: str) -> str:
        """Queue welcome email task"""
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "type": "welcome",
            "user_id": user_id,
            "user_email": user_email,
            "user_name": user_name,
            "created_at": datetime.now().isoformat(),
            "retries": 0,
        }
        await self.redis.lpush(self.queue_key, json.dumps(task))
        return task_id

    async def enqueue_resume_upload_email(self, user_id: str, user_email: str,
                                         resume_name: str, skills: List[str]) -> str:
        """Queue resume upload confirmation email"""
        # Similar structure
        pass

    async def enqueue_job_alert_email(self, user_id: str, user_email: str,
                                     resume_name: str, matches: List[dict]) -> str:
        """Queue job match alert email"""
        # Similar structure
        pass

    async def enqueue_password_change_email(self, user_id: str,
                                           user_email: str) -> str:
        """Queue password change notification email"""
        # Similar structure
        pass

    async def dequeue_email(self) -> Optional[dict]:
        """Get next email task from queue"""
        task_json = await self.redis.rpop(self.queue_key)
        return json.loads(task_json) if task_json else None

    async def mark_sent(self, task_id: str) -> None:
        """Mark email as successfully sent"""
        # Store in sent_emails:{task_id}
        pass

    async def mark_failed(self, task_id: str, error: str, retries: int) -> None:
        """Mark email as failed, retry if retries < max"""
        # If retries < 3, re-queue task
        # If retries >= 3, store in failed_emails
        pass
```

---

### Step 3: Create Email Templates
**Directory**: `services/api/app/templates/emails/`

**Files** (4 templates, each with HTML + plain text):

**1. welcome.html**
```html
<html>
  <body>
    <h1>Welcome to AutoIntern, {{user_name}}!</h1>
    <p>Your account has been created successfully.</p>
    <p>Start your job search journey:</p>
    <ol>
      <li>Upload your resume (PDF, DOCX, or TXT)</li>
      <li>Search for jobs by keyword</li>
      <li>Let our AI recommend perfect matches</li>
      <li>Save your favorite jobs</li>
    </ol>
    <p><a href="{{dashboard_url}}">Go to Dashboard</a></p>
    <p>Best regards,<br>AutoIntern Team</p>
  </body>
</html>
```

**2. resume_upload.html**
```html
<html>
  <body>
    <h1>Resume Upload Confirmed</h1>
    <p>Hi {{user_name}},</p>
    <p>Your resume <strong>{{resume_name}}</strong> has been successfully uploaded!</p>
    <h3>Detected Skills:</h3>
    <ul>
      {{#skills}}<li>{{.}}</li>{{/skills}}
    </ul>
    <p><a href="{{recommendations_url}}">View Job Recommendations</a></p>
    <p>AutoIntern Team</p>
  </body>
</html>
```

**3. job_alert.html**
```html
<html>
  <body>
    <h1>New Job Matches Found!</h1>
    <p>Hi {{user_name}},</p>
    <p>We found {{match_count}} new jobs matching your resume {{resume_name}}:</p>
    <table>
      <tr>
        <th>Job Title</th>
        <th>Company</th>
        <th>Location</th>
        <th>Match Score</th>
      </tr>
      {{#matches}}
      <tr>
        <td>{{job_title}}</td>
        <td>{{company}}</td>
        <td>{{location}}</td>
        <td>{{similarity_score}}%</td>
      </tr>
      {{/matches}}
    </table>
    <p><a href="{{jobs_url}}">View All Matches on Dashboard</a></p>
    <p>AutoIntern Team</p>
  </body>
</html>
```

**4. password_change.html**
```html
<html>
  <body>
    <h1>Password Changed Successfully</h1>
    <p>Hi {{user_name}},</p>
    <p>Your account password was changed on {{timestamp}}.</p>
    <p><strong>If you didn't make this change, please reset your password immediately.</strong></p>
    <p><a href="{{reset_password_url}}">Reset Password</a></p>
    <p>Security team,<br>AutoIntern</p>
  </body>
</html>
```

---

### Step 4: Create Email Models
**File**: `services/api/app/models/models.py` (MODIFY)

Add to User model:
```python
class User(Base):
    # ... existing fields ...

    # Email notification preferences (NEW)
    notify_on_new_jobs = Column(Boolean, default=True)  # Job match alerts
    notify_on_resume_upload = Column(Boolean, default=True)  # Upload confirmation
    notify_on_password_change = Column(Boolean, default=True)  # Security notifications
    weekly_digest = Column(Boolean, default=True)  # Weekly job summary
    email_frequency = Column(String(50), default="weekly")  # daily, weekly, never
```

Add new model:
```python
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email_type = Column(String(50), nullable=False)  # welcome, upload, alert, password_change
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending")  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    retries = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="email_logs")
```

Update User model:
```python
user.email_logs = relationship("EmailLog", back_populates="user", cascade="all, delete-orphan")
```

---

### Step 5: Create Email Schemas
**File**: `services/api/app/schemas/email.py` (NEW - 60 lines)

```python
from pydantic import BaseModel, EmailStr
from typing import List, Optional

class EmailLogResponse(BaseModel):
    id: str
    user_id: str
    email_type: str
    recipient_email: EmailStr
    subject: str
    sent_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    created_at: datetime

class EmailPreferences(BaseModel):
    notify_on_new_jobs: bool
    notify_on_resume_upload: bool
    notify_on_password_change: bool
    weekly_digest: bool
    email_frequency: str  # daily, weekly, never

class EmailPreferencesUpdate(BaseModel):
    notify_on_new_jobs: Optional[bool]
    notify_on_resume_upload: Optional[bool]
    notify_on_password_change: Optional[bool]
    weekly_digest: Optional[bool]
    email_frequency: Optional[str]
```

---

### Step 6: Create Email Routes
**File**: `services/api/app/routes/emails.py` (NEW - 150 lines)

**Endpoints** (4 new):

**Endpoint 1: GET /users/me/email-preferences (Protected)**
```python
@router.get("/me/email-preferences", response_model=EmailPreferences)
async def get_email_preferences(current_user: dict = Depends(get_current_user)):
    """Get user's email notification preferences"""
    # Query user by ID
    # Return preferences
    # 200 OK
```

**Endpoint 2: PUT /users/me/email-preferences (Protected)**
```python
@router.put("/me/email-preferences", response_model=EmailPreferences)
async def update_email_preferences(
    preferences: EmailPreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user's email notification preferences"""
    # Validate email_frequency in [daily, weekly, never]
    # Update user record
    # Return updated preferences
    # 200 OK
```

**Endpoint 3: GET /users/me/email-logs (Protected)**
```python
@router.get("/users/me/email-logs", response_model=List[EmailLogResponse])
async def get_email_logs(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: dict = Depends(get_current_user)
):
    """Get user's email history"""
    # Query email_logs for user
    # Return paginated list (last 50 by default)
    # 200 OK
```

**Endpoint 4: POST /emails/test (Admin only - for testing)**
```python
@router.post("/emails/test")
async def test_email(
    email: EmailStr = Query(..., description="Email to test")
):
    """Send test email (for development)"""
    # Queue test welcome email
    # Return task_id
    # 202 Accepted
```

---

### Step 7: Update Existing Routes
**File**: `services/api/app/routes/users.py` (MODIFY)

Modify `POST /users/register`:
```python
@router.post("/users/register", status_code=201, response_model=UserResponse)
async def register(user_create: UserCreate, session: AsyncSession = Depends(get_session)):
    # ... existing validation ...

    # Create user
    user = User(email=user_create.email, password_hash=hashed_password)
    session.add(user)
    await session.commit()

    # Queue welcome email
    email_queue = EmailQueue(REDIS_URL)
    await email_queue.enqueue_welcome_email(
        user_id=str(user.id),
        user_email=user.email,
        user_name=user.email.split("@")[0]  # First part of email
    )

    return UserResponse(id=user.id, email=user.email, created_at=user.created_at)
```

**File**: `services/api/app/routes/resumes.py` (MODIFY)

Modify `POST /resumes/upload`:
```python
@router.post("/resumes/upload", status_code=201, response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # ... existing resume processing ...

    # Queue upload confirmation email
    email_queue = EmailQueue(REDIS_URL)
    user = await session.get(User, UUID(current_user["user_id"]))
    await email_queue.enqueue_resume_upload_email(
        user_id=current_user["user_id"],
        user_email=user.email,
        resume_name=file.filename,
        skills=resume.skills  # Extracted skills list
    )

    return resume_response
```

**File**: `services/api/app/routes/users.py` (MODIFY - POST /users/change-password)

```python
@router.post("/users/change-password", response_model={"msg": str})
async def change_password(
    password_change: PasswordChange,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # ... existing password change logic ...

    # Queue password change notification email
    email_queue = EmailQueue(REDIS_URL)
    user = await session.get(User, UUID(current_user["user_id"]))
    await email_queue.enqueue_password_change_email(
        user_id=current_user["user_id"],
        user_email=user.email
    )

    return {"msg": "Password changed successfully"}
```

---

### Step 8: Create Background Worker
**File**: `services/api/services/email_worker.py` (NEW - 150 lines)

**Purpose**: Async background process that dequeues and sends emails

```python
class EmailWorker:
    def __init__(self, email_service: EmailService, email_queue: EmailQueue,
                 session_factory):
        self.email_service = email_service
        self.email_queue = email_queue
        self.session_factory = session_factory

    async def process_emails(self):
        """Main worker loop - continuously process email queue"""
        while True:
            try:
                task = await self.email_queue.dequeue_email()

                if not task:
                    await asyncio.sleep(5)  # No tasks, wait 5 seconds
                    continue

                # Route task to appropriate handler
                if task["type"] == "welcome":
                    await self._handle_welcome(task)
                elif task["type"] == "upload":
                    await self._handle_resume_upload(task)
                elif task["type"] == "job_alert":
                    await self._handle_job_alert(task)
                elif task["type"] == "password_change":
                    await self._handle_password_change(task)

                # Mark as sent
                await self.email_queue.mark_sent(task["id"])

            except Exception as e:
                await self.email_queue.mark_failed(
                    task["id"],
                    str(e),
                    task.get("retries", 0) + 1
                )

    async def _handle_welcome(self, task: dict) -> None:
        """Send welcome email"""
        success = await self.email_service.send_welcome_email(
            user_email=task["user_email"],
            user_name=task["user_name"]
        )

        if success:
            await self._log_email(
                task["user_id"],
                "welcome",
                task["user_email"],
                "Welcome to AutoIntern",
                "sent"
            )

    # ... similar handlers for other email types ...

    async def _log_email(self, user_id: str, email_type: str,
                        recipient_email: str, subject: str,
                        status: str, error_message: str = None) -> None:
        """Log email to database"""
        async with self.session_factory() as session:
            log = EmailLog(
                user_id=UUID(user_id),
                email_type=email_type,
                recipient_email=recipient_email,
                subject=subject,
                status=status,
                error_message=error_message,
                sent_at=datetime.now(timezone.utc) if status == "sent" else None
            )
            session.add(log)
            await session.commit()

# Main entry point
async def main():
    email_service = EmailService(
        smtp_host=SMTP_HOST,
        smtp_port=SMTP_PORT,
        sender_email=SENDER_EMAIL,
        sender_password=SENDER_PASSWORD
    )
    email_queue = EmailQueue(REDIS_URL)

    worker = EmailWorker(email_service, email_queue, SessionLocal)
    await worker.process_emails()

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Step 9: Update Configuration
**File**: `services/api/app/core/config.py` (MODIFY)

Add:
```python
# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@autointern.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# Redis Configuration (for email queue)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Email Template Directory
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "../templates/emails")
```

**Create `.env` example:**
```bash
# Email (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password  # Gmail requires app-specific password

# Or use SendGrid instead:
# SENDGRID_API_KEY=SG.xxxxxxxxxxxxxx

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

### Step 10: Database Migration
**File**: `services/api/alembic/versions/0007_phase7_email_notifications.py` (NEW)

```python
def upgrade() -> None:
    # Add email notification columns to users table
    op.add_column('users',
        sa.Column('notify_on_new_jobs', sa.Boolean(), server_default='true')
    )
    op.add_column('users',
        sa.Column('notify_on_resume_upload', sa.Boolean(), server_default='true')
    )
    op.add_column('users',
        sa.Column('notify_on_password_change', sa.Boolean(), server_default='true')
    )
    op.add_column('users',
        sa.Column('weekly_digest', sa.Boolean(), server_default='true')
    )
    op.add_column('users',
        sa.Column('email_frequency', sa.String(50), server_default='weekly')
    )

    # Create email_logs table
    op.create_table(
        'email_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('email_type', sa.String(50), nullable=False),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retries', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_email_logs_user_id', 'email_logs', ['user_id'])
    op.create_index('ix_email_logs_status', 'email_logs', ['status'])
    op.create_index('ix_email_logs_created_at', 'email_logs', ['created_at'])
```

---

### Step 11: Create Tests
**File**: `services/api/tests/test_emails.py` (NEW - 250+ lines, 20+ tests)

**Test Classes:**

**TestEmailService** (8 tests):
```python
def test_send_email_success
def test_send_email_invalid_recipient
def test_send_welcome_email
def test_send_resume_upload_email
def test_send_job_alert_email
def test_send_password_change_email
def test_email_with_special_characters
def test_email_with_unicode_subject
```

**TestEmailQueue** (6 tests):
```python
def test_enqueue_welcome_email
def test_enqueue_resume_upload_email
def test_enqueue_job_alert_email
def test_dequeue_email
def test_mark_sent
def test_mark_failed_with_retry
```

**TestEmailEndpoints** (10+ tests):
```python
def test_get_email_preferences_authenticated
def test_get_email_preferences_unauthenticated
def test_update_email_preferences
def test_update_invalid_frequency
def test_get_email_logs_paginated
def test_email_sent_on_register
def test_email_sent_on_password_change
def test_email_respects_user_preferences
def test_email_retry_on_failure
def test_email_logs_recorded_in_db
```

---

### Step 12: Integration Tests
**File**: `services/api/tests/test_email_integration.py` (NEW - 150+ lines)

**Test Scenarios:**
```python
def test_complete_registration_email_flow()  # Register → Welcome email queued → Sent
def test_resume_upload_email_flow()  # Upload → Confirmation queued → Sent
def test_password_change_email_flow()  # Change password → Notification queued → Sent
def test_email_queue_persistence()  # Queue survives crash → Emails still sent
def test_email_logging_and_history()  # Emails logged → User can view history
```

---

## Technology Choices

### Email Backend Options

**Option 1: SMTP (Gmail/Office365)** ✅ RECOMMENDED
- Free with personal email account
- No API keys needed (just password)
- Works offline if configured locally
- Easy to test with Gmail TLS
- **Setup**: Enable "Less secure apps" or use app-specific password

**Option 2: SendGrid** (Alternative)
- More reliable for production
- Better deliverability rates
- API-based (no SMTP server needed)
- Requires API key ($20-100/month)
- Better tracking and analytics

**Option 3: AWS SES**
- Lower cost at scale
- Integrated with AWS services
- Complex IAM setup
- Better for high volume

### Queue Backend Options

**Option 1: Redis + Custom Worker** ✅ RECOMMENDED (for Phase 7)
- Simple setup, single process
- Good for MVP (< 10k emails/day)
- Persists in Redis
- Works with existing stack

**Option 2: Celery + RabbitMQ**
- Industry standard
- Distributed workers
- Complex setup
- Overkill for MVP

### Template Engine

**Jinja2** for HTML/text template rendering
```bash
pip install jinja2
```

---

## Critical Files to Create (5 files)
1. `services/api/app/services/email_service.py` (200 lines)
2. `services/api/app/services/email_queue.py` (150 lines)
3. `services/api/app/routes/emails.py` (150 lines)
4. `services/api/services/email_worker.py` (150 lines)
5. `services/api/tests/test_emails.py` (250+ lines)

## Critical Files to Modify (5 files)
1. `services/api/app/models/models.py` - Add User email preferences + EmailLog model
2. `services/api/app/core/config.py` - Add email/Redis config
3. `services/api/app/routes/users.py` - Queue email on register/password change
4. `services/api/app/routes/resumes.py` - Queue email on upload
5. `services/api/app/schemas/email.py` - Email-related Pydantic models

## Critical Files to Create (Template files)
1. `services/api/app/templates/emails/welcome.html`
2. `services/api/app/templates/emails/welcome.txt`
3. `services/api/app/templates/emails/resume_upload.html`
4. `services/api/app/templates/emails/resume_upload.txt`
5. `services/api/app/templates/emails/job_alert.html`
6. `services/api/app/templates/emails/job_alert.txt`
7. `services/api/app/templates/emails/password_change.html`
8. `services/api/app/templates/emails/password_change.txt`

---

## Dependencies to Add

```bash
# Add to requirements.txt
jinja2==3.1.2  # Template rendering
aiosmtplib==2.1.1  # Async SMTP
redis==5.0.1  # Redis client (already have aioredis)
email-validator==2.1.0  # Email validation (we have this - pydantic)
```

---

## Configuration & Setup

### Gmail Setup (for testing)

1. **Enable 2FA** on your Google account
2. **Generate App Password**:
   - Go to myaccount.google.com
   - Security → App passwords
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character password

3. **Set environment variables**:
   ```bash
   export SMTP_HOST=smtp.gmail.com
   export SMTP_PORT=587
   export SENDER_EMAIL=your-email@gmail.com
   export SENDER_PASSWORD=xxxx-xxxx-xxxx-xxxx
   export REDIS_URL=redis://localhost:6379/0
   ```

### Redis Setup

```bash
# Start Redis (if not running)
redis-server

# Or in Docker
docker run -d -p 6379:6379 redis:latest
```

### Run Email Worker

```bash
# In separate terminal
cd services/api
python -m services.email_worker
```

---

## Test Coverage

- **Email Service**: 8 tests
- **Email Queue**: 6 tests
- **Email Endpoints**: 10+ tests
- **Integration**: 5+ tests
- **Total**: 30+ test cases

**Run tests**:
```bash
cd services/api
pytest tests/test_emails.py tests/test_email_integration.py -v
```

---

## Verification Checklist

- ✅ Email service connects to SMTP
- ✅ Templates render with variables
- ✅ Emails queued on register/upload/password-change
- ✅ Background worker processes queue
- ✅ Emails logged to database
- ✅ User can view email history
- ✅ User can toggle email preferences
- ✅ Invalid emails rejected
- ✅ Queue persists across restarts
- ✅ Failed emails retry up to 3 times
- ✅ All 30+ tests pass
- ✅ Integration: Register → Welcome email sent

---

## Success Criteria

1. User receives welcome email on registration
2. User receives confirmation email on resume upload
3. User receives notification on password change
4. Job match alerts sent for new recommendations
5. User can view all sent emails in history
6. User can toggle email notification preferences
7. Emails only sent if user has opted in
8. Failed emails automatically retry (max 3 times)
9. Email queue persists in Redis
10. Background worker runs independently
11. All endpoints properly authenticated
12. Test coverage >90%

---

## Not In Scope (Phase 7)

- Email unsubscribe links (would add in Phase 7B)
- Email attachment sending (future enhancement)
- Calendar invites for job deadlines
- A/B testing email templates
- Advanced email analytics
- SMS notifications (Phase 8+)

---

## Next Phases

- **Phase 7B**: Email unsubscribe + frequency preferences (daily digest, weekly digest)
- **Phase 8**: Rate limiting + account security hardening
- **Phase 9**: Production deployment (Docker, Kubernetes)

---

## How to Proceed

1. **Review this plan** ✅ (you are here)
2. **Implement Phase 7** - Create email service, queue, models, routes
3. **Test Phase 7** - Run 30+ tests, verify end-to-end flows
4. **Document** - Create PHASES_1_TO_7_TEST_SUMMARY.md

Ready to implement? Answer any clarifications needed, then I'll proceed with Phase 7 implementation.
