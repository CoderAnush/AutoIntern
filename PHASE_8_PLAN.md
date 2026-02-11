# PHASE 8: Security Hardening & Monitoring

## Objective

Implement comprehensive security hardening to protect against common attacks and improve observability:
1. **Rate Limiting** - Prevent brute force attacks on auth endpoints
2. **Account Lockout** - Lock accounts after failed login attempts
3. **Security Headers** - OWASP security headers (CSP, X-Frame-Options, HSTS)
4. **Request Logging** - Audit trail for compliance
5. **Monitoring** - Health checks and performance metrics
6. **Rate Limiting** - Global rate limiting on all endpoints

---

## Current Status Analysis

**Completed (Phases 1-7)**:
- ✅ User authentication with JWT
- ✅ Password hashing with Argon2
- ✅ Email notifications
- ✅ API endpoints (17 total)
- ✅ 100% test coverage for critical paths

**Security Gaps to Address**:
- ❌ No rate limiting (brute force possible)
- ❌ No account lockout (failed attempts not tracked)
- ❌ No security headers (XSS, clickjacking vulnerabilities)
- ❌ No request logging (no audit trail)
- ❌ No monitoring (can't detect attacks)
- ❌ CORS allows "*" (should restrict in production)

---

## Implementation Plan

### Step 1: Create Rate Limiting Service

**File**: `services/api/app/services/rate_limiter.py` (NEW - 150 lines)

**Purpose**: Redis-based rate limiting using sliding window algorithm

**Key Methods**:
```python
class RateLimiter:
    async def is_allowed(key: str, max_requests: int, window_seconds: int) -> bool
        # Check if request allowed (returns True/False)
        # Uses Redis INCR with expiry
        # Returns: (is_allowed, current_count, reset_after_seconds)

    async def get_request_count(key: str) -> int
        # Get current request count for key

    async def reset(key: str) -> None
        # Manually reset rate limit counter

    async def clear_all() -> None
        # Clear all rate limiters (for testing/admin)
```

**Algorithm**: Sliding Window Counter
- Store counter in Redis with expiry
- Each request increments counter
- If counter > limit, reject
- Counter resets after window expires

**Configuration**:
```python
# Auth endpoints (strict)
LOGIN_MAX_REQUESTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 per 5 minutes

REGISTER_MAX_REQUESTS = 3
REGISTER_WINDOW_SECONDS = 3600  # 3 per hour

PASSWORD_CHANGE_MAX_REQUESTS = 3
PASSWORD_CHANGE_WINDOW_SECONDS = 3600  # 3 per hour

# General API endpoints (moderate)
API_MAX_REQUESTS = 100
API_WINDOW_SECONDS = 60  # 100 per minute

# Upload endpoints (more lenient)
UPLOAD_MAX_REQUESTS = 10
UPLOAD_WINDOW_SECONDS = 60  # 10 per minute
```

**Example Usage**:
```python
# In login endpoint
@router.post("/login")
async def login(credentials: UserLogin):
    # Check rate limit (key: email address)
    is_allowed, count, reset_seconds = await rate_limiter.is_allowed(
        key=f"login:{credentials.email}",
        max_requests=5,
        window_seconds=300
    )

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {reset_seconds}s",
            headers={"Retry-After": str(reset_seconds)}
        )

    # ... rest of login logic ...
```

---

### Step 2: Create Account Lockout Service

**File**: `services/api/app/services/account_lockout.py` (NEW - 150 lines)

**Purpose**: Track failed login attempts and lock accounts

**Key Methods**:
```python
class AccountLockout:
    async def record_failed_attempt(user_id: str) -> int
        # Record failed login attempt
        # Returns: number of failed attempts

    async def get_failed_attempts(user_id: str) -> int
        # Get current failed attempt count

    async def is_locked(user_id: str) -> bool
        # Check if account is locked

    async def get_lockout_time_remaining(user_id: str) -> int
        # Get seconds until account unlocked

    async def unlock_account(user_id: str) -> None
        # Manual unlock (admin/account recovery)

    async def reset_attempts(user_id: str) -> None
        # Reset failed attempts counter (after successful login)
```

**Database Addition**:
Add to User model:
```python
class User(Base):
    # ... existing fields ...

    # Account lockout (Phase 8)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)  # NULL = not locked
    last_login_attempt = Column(DateTime(timezone=True), nullable=True)
```

**Configuration**:
```python
MAX_FAILED_ATTEMPTS = 5  # Lock after 5 failed logins
LOCKOUT_DURATION_MINUTES = 15  # Lock for 15 minutes
RESET_ATTEMPTS_AFTER_MINUTES = 30  # Reset counter if no login for 30 min
```

**Logic Flow**:
```
User attempts login
    ↓
Check if account locked
    ├─ YES: Return 403 Forbidden, lockout time remaining
    └─ NO: Continue
    ↓
Validate credentials
    ├─ CORRECT:
    │   ├─ Reset failed attempts counter
    │   ├─ Update last_login_attempt
    │   └─ Return tokens
    │
    └─ INCORRECT:
        ├─ Increment failed_login_attempts
        ├─ If >= MAX_FAILED_ATTEMPTS:
        │   ├─ Set locked_until = now + LOCKOUT_DURATION
        │   └─ Return 403 Forbidden
        └─ Return 401 Unauthorized
```

---

### Step 3: Create Security Headers Middleware

**File**: `services/api/app/middleware/security_headers.py` (NEW - 80 lines)

**Purpose**: Add security headers to all responses

**Headers to Add**:
```python
# Prevent XSS attacks
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
X-Frame-Options: DENY  # Clickjacking protection

# Content Security Policy
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'

# HTTPS enforcement
Strict-Transport-Security: max-age=31536000; includeSubDomains  # HSTS: 1 year
Referrer-Policy: strict-origin-when-cross-origin

# Permissions
Permissions-Policy: geolocation=(), camera=(), microphone=(), accelerometer=(), magnetometer=(), gyroscope=()

# Remove server version info
Server: AutoIntern

# CORS (already in place)
Access-Control-Allow-Origin: [configured]
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

**Implementation**:
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Server"] = "AutoIntern"

    return response
```

---

### Step 4: Create Request Logging Service

**File**: `services/api/app/services/request_logger.py` (NEW - 120 lines)

**Purpose**: Log all API requests and responses for audit trail

**Database Addition**:
```python
class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL for unauthenticated
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    path = Column(String(512), nullable=False)  # /users/login, /resumes, etc
    status_code = Column(Integer, nullable=False)  # 200, 401, 500, etc
    response_time_ms = Column(Integer, nullable=False)  # Milliseconds
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    user_agent = Column(String(512), nullable=True)
    request_body_hash = Column(String(64), nullable=True)  # SHA256 hash (don't store passwords)
    error_message = Column(Text, nullable=True)  # Error details if status >= 400
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Indices for fast queries
    __table_args__ = (
        Index("ix_request_logs_user_id", user_id),
        Index("ix_request_logs_status", status_code),
        Index("ix_request_logs_created_at", created_at),
        Index("ix_request_logs_path_status", path, status_code),
    )
```

**Middleware**:
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Call endpoint
    response = await call_next(request)

    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)

    # Log to database (async, non-blocking)
    try:
        await log_request_async(
            user_id=request.state.user_id if hasattr(request.state, 'user_id') else None,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent")
        )
    except Exception as e:
        logger.error(f"Failed to log request: {e}")
        # Don't fail the request if logging fails

    return response
```

---

### Step 5: Create Monitoring Service

**File**: `services/api/app/services/monitoring.py` (NEW - 100 lines)

**Purpose**: Health checks and performance monitoring

**Endpoints to Add**:
```python
# 1. Health Check
GET /health (no auth required)
Response: {"status": "healthy", "timestamp": "2024-02-11T10:30:00Z"}

# 2. Liveness Check (for Kubernetes)
GET /health/live (no auth required)
Response: {"status": "live"} (200 OK if server is running)

# 3. Readiness Check (for Kubernetes)
GET /health/ready (no auth required)
Response: {"status": "ready", "db": "ok", "redis": "ok"} (200 if ready to receive traffic)

# 4. Metrics Summary (protected)
GET /metrics/summary (auth required)
Response: {
    "requests_total": 1500,
    "requests_per_minute": 25,
    "error_rate": 0.02,  # 2%
    "average_response_time_ms": 150,
    "database_connections": 10,
    "cache_hit_rate": 0.85,  # 85%
}

# 5. Error Rate Alert
GET /metrics/errors/recent (protected)
Response: {
    "errors_last_hour": [
        {"timestamp": "...", "status": 500, "path": "/recommendations/...", "count": 3},
        {"timestamp": "...", "status": 401, "path": "/users/login", "count": 12}
    ]
}
```

**Implementation**:
```python
class HealthMonitor:
    async def check_database() -> bool
        # Try SELECT 1 query
        # Return True if healthy

    async def check_redis() -> bool
        # Try PING command
        # Return True if healthy

    async def check_server() -> bool
        # Check if server is running
        # Always returns True in this process

    async def get_metrics() -> dict
        # Return performance metrics
```

---

### Step 6: Update Rate Limiting in Routes

**File**: `services/api/app/routes/users.py` (MODIFY - Add rate limiting)

**Modified Endpoints**:

**POST /users/register**:
```python
@router.post("/users/register", status_code=201, response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Rate limiting (3 per hour)
    is_allowed, count, reset_seconds = await rate_limiter.is_allowed(
        key=f"register:{user_data.email}",
        max_requests=3,
        window_seconds=3600
    )

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Registration limit exceeded. Try again in {reset_seconds}s",
            headers={"Retry-After": str(reset_seconds)}
        )

    # ... rest of registration ...
```

**POST /users/login**:
```python
@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    # Rate limiting (5 per 5 minutes per email)
    is_allowed, count, reset_seconds = await rate_limiter.is_allowed(
        key=f"login:{credentials.email.lower()}",
        max_requests=5,
        window_seconds=300
    )

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {reset_seconds}s",
            headers={"Retry-After": str(reset_seconds)}
        )

    # Find user
    user = await db.get(UserModel, ...)

    # Check account lockout (NEW - Phase 8)
    if await account_lockout.is_locked(user.id):
        remaining_seconds = await account_lockout.get_lockout_time_remaining(user.id)
        raise HTTPException(
            status_code=403,
            detail=f"Account locked. Try again in {remaining_seconds} seconds",
            headers={"Retry-After": str(remaining_seconds)}
        )

    # Verify password
    if not AuthService.verify_password(credentials.password, user.password_hash):
        # Record failed attempt (NEW - Phase 8)
        failed_attempts = await account_lockout.record_failed_attempt(user.id)

        is_locked = await account_lockout.is_locked(user.id)
        if is_locked:
            remaining_seconds = await account_lockout.get_lockout_time_remaining(user.id)
            raise HTTPException(
                status_code=403,
                detail=f"Too many failed attempts. Account locked for {remaining_seconds} seconds",
                headers={"Retry-After": str(remaining_seconds)}
            )

        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Successful login - reset failed attempts (NEW - Phase 8)
    await account_lockout.reset_attempts(user.id)

    # ... rest of login ...
```

**POST /users/change-password**:
```python
@router.post("/users/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Rate limiting (3 per hour per user)
    is_allowed = await rate_limiter.is_allowed(
        key=f"change_password:{current_user['user_id']}",
        max_requests=3,
        window_seconds=3600
    )

    if not is_allowed:
        raise HTTPException(status_code=429, detail="Too many password change attempts")

    # ... rest of password change ...
```

---

### Step 7: Update Main App

**File**: `services/api/app/main.py` (MODIFY - Add middlewares and endpoints)

**Add Imports**:
```python
from app.middleware.security_headers import add_security_headers_middleware
from app.services.monitoring import HealthMonitor
```

**Add Middleware**:
```python
# Add security headers middleware (must be after CORS)
app.add_middleware(SecurityHeadersMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)
```

**Add Health/Monitoring Routes**:
```python
health_monitor = HealthMonitor()

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/live")
async def health_live():
    return {"status": "live"}

@app.get("/health/ready")
async def health_ready():
    db_ok = await health_monitor.check_database()
    redis_ok = await health_monitor.check_redis()

    if not (db_ok and redis_ok):
        raise HTTPException(status_code=503, detail="Service not ready")

    return {
        "status": "ready",
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error"
    }

@app.get("/metrics/summary")
async def metrics_summary(current_user: dict = Depends(get_current_user)):
    """Protected metrics endpoint"""
    return await health_monitor.get_metrics()
```

---

### Step 8: Update Configuration

**File**: `services/api/app/core/config.py` (MODIFY - Add Phase 8 settings)

**Add**:
```python
# Rate Limiting Configuration (Phase 8)
rate_limit_enabled: bool = True
login_rate_limit: int = 5  # 5 attempts
login_rate_limit_window: int = 300  # 5 minutes
register_rate_limit: int = 3  # 3 registrations
register_rate_limit_window: int = 3600  # 1 hour

# Account Lockout Configuration (Phase 8)
max_failed_attempts: int = 5
lockout_duration_minutes: int = 15
reset_attempts_after_minutes: int = 30

# Security Headers (Phase 8)
security_headers_enabled: bool = True

# Request Logging (Phase 8)
request_logging_enabled: bool = True
log_request_body: bool = False  # Don't log request body (contains passwords)
log_response_body: bool = False  # Don't log response body (contains sensitive data)

# Monitoring (Phase 8)
metrics_enabled: bool = True
metrics_export_interval_seconds: int = 60

# HTTPS Configuration (Phase 8)
enforce_https: bool = False  # Set to True in production
```

---

### Step 9: Create Database Migration

**File**: `services/api/alembic/versions/0008_phase8_security_hardening.py` (NEW)

**Changes**:
```python
def upgrade() -> None:
    # Add account lockout columns to users table
    op.add_column('users',
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False)
    )
    op.add_column('users',
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column('users',
        sa.Column('last_login_attempt', sa.DateTime(timezone=True), nullable=True)
    )

    # Create request_logs table
    op.create_table(
        'request_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('path', sa.String(512), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('request_body_hash', sa.String(64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indices on request_logs
    op.create_index('ix_request_logs_user_id', 'request_logs', ['user_id'])
    op.create_index('ix_request_logs_status', 'request_logs', ['status_code'])
    op.create_index('ix_request_logs_created_at', 'request_logs', ['created_at'])

def downgrade() -> None:
    # Drop indices
    op.drop_index('ix_request_logs_created_at')
    op.drop_index('ix_request_logs_status')
    op.drop_index('ix_request_logs_user_id')

    # Drop request_logs table
    op.drop_table('request_logs')

    # Drop account lockout columns
    op.drop_column('users', 'last_login_attempt')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
```

---

### Step 10: Create Tests

**File**: `services/api/tests/test_security.py` (NEW - 300+ lines, 30+ tests)

**Test Classes**:

**TestRateLimiter** (10 tests):
```python
def test_rate_limiter_allows_requests_within_limit
def test_rate_limiter_blocks_requests_over_limit
def test_rate_limiter_resets_after_window
def test_rate_limiter_different_keys_independent
def test_rate_limiter_redis_persistence
def test_rate_limiter_concurrent_requests
def test_rate_limiter_get_request_count
def test_rate_limiter_manual_reset
def test_rate_limiter_returns_reset_time
def test_rate_limiter_handles_redis_errors
```

**TestAccountLockout** (10 tests):
```python
def test_record_failed_attempt
def test_lockout_after_max_attempts
def test_lockout_duration
def test_unlock_manual
def test_reset_attempts_after_successful_login
def test_is_locked_before_lockout
def test_is_locked_after_lockout
def test_get_lockout_time_remaining
def test_failed_attempts_reset_after_window
def test_failed_attempts_per_user_isolated
```

**TestSecurityHeaders** (5 tests):
```python
def test_x_content_type_options_header
def test_x_xss_protection_header
def test_x_frame_options_header
def test_strict_transport_security_header
def test_referrer_policy_header
```

**TestRequestLogging** (5 tests):
```python
def test_request_logged_to_database
def test_request_log_contains_correct_fields
def test_request_log_includes_status_code
def test_request_log_includes_response_time
def test_request_log_hides_sensitive_data
```

**TestLoginRateLimit** (5 tests):
```python
def test_login_rate_limit_allows_5_attempts
def test_login_rate_limit_blocks_6th_attempt
def test_login_different_users_independent
def test_login_rate_limit_per_email
def test_login_rate_limit_429_response
```

**TestAccountLockoutIntegration** (5 tests):
```python
def test_failed_login_increments_counter
def test_5_failed_logins_locks_account
def test_403_on_locked_account
def test_successful_login_resets_counter
def test_lockout_expires_after_duration
```

---

## Dependencies to Add

```bash
# Already have Redis, just need:
# No new dependencies (using existing: redis, SQLAlchemy, FastAPI)
```

---

## Configuration Example (.env)

```bash
# Phase 8 Security Settings
RATE_LIMIT_ENABLED=true
LOGIN_RATE_LIMIT=5
LOGIN_RATE_LIMIT_WINDOW=300
REGISTER_RATE_LIMIT=3
REGISTER_RATE_LIMIT_WINDOW=3600

MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

SECURITY_HEADERS_ENABLED=true
REQUEST_LOGGING_ENABLED=true
METRICS_ENABLED=true

ENFORCE_HTTPS=false  # Set to true in production
```

---

## Verification Checklist

- ✅ Rate limiting works on login/register/password-change
- ✅ Account locks after 5 failed attempts
- ✅ Account unlocks after 15 minutes
- ✅ Security headers present in all responses
- ✅ Requests logged to database
- ✅ Health endpoints working (/health, /health/ready, /health/live)
- ✅ Metrics endpoint returns correct statistics
- ✅ Retry-After header included in 429 responses
- ✅ All 30+ security tests passing
- ✅ No performance regression

---

## Success Criteria

1. ✅ Login endpoint rejects 6th attempt with 429 Too Many Requests
2. ✅ Account locks after 5 failed login attempts
3. ✅ Locked account returns 403 Forbidden for 15 minutes
4. ✅ Successful login resets failed attempt counter
5. ✅ Security headers present in all responses
6. ✅ Request logging captures all API calls
7. ✅ Health endpoints working for Kubernetes
8. ✅ Metrics endpoint provides performance data
9. ✅ Rate limit errors include Retry-After header
10. ✅ All 30+ security tests passing

---

## Not In Scope (Phase 8)

- Web Application Firewall (WAF)
- DDoS protection
- Certificate pinning
- Two-factor authentication (2FA)
- OAuth2 social login
- API key management
- Encryption at rest (database encryption)
- Secret rotation
- PCI DSS compliance

---

## Next Steps

1. **Review & Approve Plan** - Phase 8 security hardening strategy
2. **Implement Phase 8** - Create rate limiting, account lockout, security headers
3. **Test Phase 8** - Run 30+ security tests
4. **Document & Deploy** - Create summary and prepare for production

---

## Architecture Diagram

```
Request Comes In
        ↓
Security Headers Middleware
        ├─ Add HSTS, CSP, X-Frame-Options, etc
        └─ Pass to next middleware
        ↓
Request Logging Middleware
        ├─ Log request start time, IP, method, path
        └─ Pass to endpoint
        ↓
Rate Limiting Check (if auth endpoint)
        ├─ Check Redis counter: login:{email}
        ├─ If counter > limit: Return 429 Too Many Requests
        └─ If allowed: Increment counter, continue
        ↓
Account Lockout Check (if login)
        ├─ Query users.locked_until
        ├─ If locked: Return 403 Forbidden
        └─ If not locked: Continue
        ↓
Authentication Check
        ├─ Validate JWT token (if protected endpoint)
        └─ Continue to endpoint handler
        ↓
Endpoint Handler
        ├─ Process request
        └─ Return response
        ↓
Request Logging Middleware (after response)
        ├─ Calculate response time
        ├─ Log status code, duration, user_id to database
        └─ Return response
        ↓
Security Headers Middleware (final step)
        ├─ Add all security headers
        └─ Send response to client
        ↓
Client Receives Response (with security headers)
```

---

## Critical Files to Create (5 files)
1. `services/api/app/services/rate_limiter.py` (150 lines)
2. `services/api/app/services/account_lockout.py` (150 lines)
3. `services/api/app/middleware/security_headers.py` (80 lines)
4. `services/api/app/services/request_logger.py` (120 lines)
5. `services/api/app/services/monitoring.py` (100 lines)

## Critical Files to Modify (4 files)
1. `services/api/app/routes/users.py` - Add rate limiting & lockout checks
2. `services/api/app/main.py` - Add middlewares and health endpoints
3. `services/api/app/models/models.py` - Add lockout columns, RequestLog table
4. `services/api/app/core/config.py` - Add Phase 8 configuration

## Critical Files to Create (Database & Tests)
1. `services/api/alembic/versions/0008_phase8_security_hardening.py` (migration)
2. `services/api/tests/test_security.py` (30+ tests)

---

## Total Implementation

- **Files to Create**: 6 files (~600 lines)
- **Files to Modify**: 4 files (~200 lines of modifications)
- **Tests**: 30+ comprehensive security tests
- **Database Changes**: 2 migrations (add columns, create table)
- **New API Endpoints**: 5 endpoints (/health, /live, /ready, /metrics/summary, /metrics/errors)

---

Ready to implement Phase 8? Answer any clarifications, then I'll proceed with implementation.
