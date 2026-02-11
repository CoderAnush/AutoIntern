# Phase 6: User Dashboard & Job Browsing UI

## Overview

**Phase 6** implements a complete **React + TypeScript** frontend for the AutoIntern platform with:
- Type-safe API client SDK (`@autointern/client`)
- User authentication (register, login, logout)
- Job search and browsing
- Resume management (upload, list, delete)
- Responsive dashboard UI

## Architecture

```
services/web/
├── packages/
│   └── client/                  # TypeScript API Client Library
│       ├── src/
│       │   ├── types.ts         # Type definitions
│       │   └── index.ts         # AutoInternClient class
│       ├── package.json
│       └── tsconfig.json
│
└── apps/
    └── dashboard/               # React Dashboard App
        ├── src/
        │   ├── context/
        │   │   └── AuthContext.tsx      # Auth state management
        │   ├── pages/
        │   │   ├── LoginPage.tsx        # Login page
        │   │   ├── RegisterPage.tsx     # Register page
        │   │   └── DashboardPage.tsx    # Main dashboard
        │   ├── App.tsx                  # Main app with routing
        │   ├── index.tsx                # Entry point
        │   └── index.css                # Global styles
        ├── public/
        │   └── index.html               # HTML template
        ├── package.json
        └── tsconfig.json
```

## Features Implemented

### 1. TypeScript API Client (`@autointern/client`)

**Type-safe wrapper for all API endpoints:**

```typescript
// Authentication
apiClient.register(userData)       // Register new user
apiClient.login(credentials)       // Login and get tokens
apiClient.refreshAccessToken()     // Refresh expired access token
apiClient.getCurrentUser()         // Get current user profile
apiClient.changePassword(data)     // Change password
apiClient.logout()                 // Logout

// Resumes
apiClient.uploadResume(file)       // Upload resume (protected)
apiClient.listResumes()            // List user's resumes (protected)
apiClient.getResume(id)            // Get single resume (protected)
apiClient.deleteResume(id)         // Delete resume (protected)

// Jobs
apiClient.listJobs()               // List all jobs
apiClient.searchJobs(query)        // Search jobs by query
apiClient.getJob(id)               // Get job details

// Recommendations
apiClient.getRecommendedJobs(resumeId)      // Get recommended jobs (protected)
apiClient.getRecommendedResumes(jobId)      // Get recommended resumes (protected)
apiClient.getResumeQuality(resumeId)        // Get resume quality scores (protected)
```

**Features:**
- Automatic token refresh on 401 errors
- localStorage persistence of tokens
- Automatic Authorization header injection
- Type-safe response/request models
- Error handling with APIError interface

### 2. Authentication System

**Login/Register Pages:**
- Email validation (EmailStr format)
- Password strength requirements display
- Real-time password validation feedback
- Error messages from API
- Token storage and retrieval
- Automatic redirect on authentication state change

**Protected Routes:**
- Dashboard requires authentication
- Automatic redirect to login if not authenticated
- Auth context for global user state

### 3. Dashboard (Main Page)

**Two-tab interface:**

**Tab 1: Job Search**
- Search jobs by query
- List all jobs with pagination
- Job cards showing:
  - Title, source, location
  - Description preview (first 200 chars)
  - Posted date
- Reset button to view all jobs
- Loading states

**Tab 2: Resume Management**
- Upload resume (PDF, DOCX, TXT)
- List all user resumes
- Resume cards showing:
  - File name
  - Extracted skills
  - Upload date
  - Delete button
- Upload loading states

**Header:**
- App title (AutoIntern)
- Current user email
- Logout button

## Running the Application

### Prerequisites

```bash
# Install Node.js 18+ and npm
node -v  # v18.0.0 or higher
npm -v   # 9.0.0 or higher
```

### Setup

```bash
# 1. Install dependencies
cd services/web/packages/client
npm install
npm run build

# 2. Install dashboard dependencies
cd ../../../apps/dashboard
npm install

# 3. Create .env file
cp .env.example .env

# 4. Start the React app
npm start
```

The app will open at `http://localhost:3000`

### Environment Variables

**`.env` file:**
```bash
# API endpoint (adjust if backend running on different port)
REACT_APP_API_URL=http://localhost:8000
```

**If backend is on different machine:**
```bash
# For production
REACT_APP_API_URL=https://api.autointern.com

# For development on different machine
REACT_APP_API_URL=http://192.168.1.100:8000
```

## API Client Usage

### Standalone SDK Usage (in other projects)

```typescript
import { AutoInternClient } from "@autointern/client";

const client = new AutoInternClient("http://localhost:8000");

// Register
const user = await client.register({
  email: "user@example.com",
  password: "SecurePass123!"
});

// Login
const tokens = await client.login({
  email: "user@example.com",
  password: "SecurePass123!"
});

// Use protected endpoints
const resumes = await client.listResumes();
const jobs = await client.getRecommendedJobs(resumeId);

// Check auth status
if (client.isAuthenticated()) {
  console.log("User is logged in");
}
```

### Building the Client Package

```bash
cd services/web/packages/client

# Build TypeScript
npm run build

# Output: dist/
#   ├── index.js
#   ├── index.d.ts     # TypeScript definitions
#   ├── types.js
#   └── types.d.ts
```

## Component Architecture

### AuthProvider + useAuth Hook

**Global authentication state:**
```typescript
const { user, isAuthenticated, isLoading, register, login, logout, error } = useAuth();
```

Manages:
- User profile data
- Authentication status
- Loading states
- Error messages
- Token persistence

### API Client Initialization

```typescript
const apiClient = new AutoInternClient(process.env.REACT_APP_API_URL);
```

Automatically:
- Injects Bearer tokens
- Handles token refresh
- Persists tokens to localStorage
- Manages CORS headers

## Error Handling

**API errors returned as APIError:**
```typescript
interface APIError {
  status: number;        // HTTP status code
  detail: string;        // Error message from backend
}
```

**Example error handling:**
```typescript
try {
  await apiClient.login(credentials);
} catch (err: any) {
  // err.status = 401
  // err.detail = "Invalid email or password"
}
```

## Styling

**Inline CSS objects** for MVP simplicity:
- No CSS framework dependency (styled-components, Tailwind, etc.)
- Easy to migrate to CSS modules later
- Responsive grid layouts for job/resume lists
- Mobile-friendly design

**To migrate to CSS modules:**
1. Create `.module.css` files in each component directory
2. Import styles: `import styles from './Component.module.css'`
3. Replace inline style objects with class names

## Testing the Frontend

### Manual Testing Checklist

```
## Authentication
☐ Register with valid email/password
☐ Register with weak password (rejected)
☐ Register with existing email (rejected)
☐ Login with valid credentials
☐ Login with invalid password (rejected)
☐ Auto-redirect to login if unauthenticated
☐ Logout button clears tokens
☐ Tokens persist after page refresh

## Job Search
☐ Load all jobs on page load
☐ Search jobs by query
☐ Reset button shows all jobs again
☐ Job cards display all fields correctly
☐ Loading state appears during search

## Resume Management
☐ Upload valid resume (PDF/DOCX/TXT)
☐ Upload invalid file type (rejected)
☐ List all uploaded resumes
☐ Delete resume functionality
☐ Delete confirmation dialog appears
☐ Resume list updates after upload/delete

## Navigation
☐ Switch between Jobs and Resumes tabs
☐ Header shows current user email
☐ Logout redirects to login page
```

### Integration Testing with Backend

Start both services:

```bash
# Terminal 1: Backend API
cd services/api
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd services/web/apps/dashboard
npm start
```

Then:
1. Register a new account
2. Upload a resume (PDF/DOCX)
3. Search for jobs
4. (In Phase 6A) View job recommendations for resume

## Phase 6 Completion Status

**Phase 6B: API Client Library** ✅
- AutoInternClient with all methods
- Type definitions for all models
- Token management
- Error handling

**Phase 6C: Minimal MVP Frontend** ✅
- Login/Register pages
- Dashboard with tabs
- Job search
- Resume management
- Auth state management

**Phase 6A: Full Features** (Next - if needed)
- Job recommendations widget
- Resume quality scores
- Saved jobs/bookmarks
- Advanced filtering
- User settings page

## Next Steps

After Phase 6, proceed to:

**Phase 7: Email Notifications**
- Send email when new jobs match profile
- Resume upload confirmation emails
- Password change notifications

**Phase 8: Security Hardening**
- Rate limiting on login attempts
- Account lockout after failed attempts
- Token blacklist for logout
- HTTPS enforcement
- Security headers

## File Count

**Phase 6 Total Files Created:**
- 8 TypeScript source files
- 3 configuration files (package.json, tsconfig.json, .env)
- 2 HTML/CSS files
- **Total: 13 files**

**Total Code Lines (Phases 1-6):**
- Backend (Phases 1-5): ~4000 lines
- Frontend (Phase 6): ~1200 lines
- **Grand Total: ~5200 lines**
