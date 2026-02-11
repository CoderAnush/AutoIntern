# AutoIntern AI — Implementation Roadmap

**Status:** MVP Infrastructure Complete (60%) → Feature Implementation (40%)
**Total Phases:** 9 (estimated 8-12 weeks)
**Stack:** FastAPI, Scrapy, React, PostgreSQL, Redis, Elasticsearch, Sentence-BERT, JWT

---

## 📋 PHASE 1: Scraper Infrastructure & Indeed Spider (Week 1-2)

**Goal:** Setup scraper framework and ingest first 10k+ jobs from Indeed

### Tasks

#### 1.1 Setup Scraper Configuration
- [ ] Create `services/scraper/sites_config.yaml` (site definitions)
- [ ] Define site schema:
  ```yaml
  indeed:
    base_url: "https://www.indeed.com/jobs"
    selectors:
      job_title: "h2.jobTitle span"
      company: "span[data-testid='company-name']"
      location: "div[data-testid='job-location']"
      job_url: "a.jcs-JobTitle"
      salary: "span[data-testid='salaryLineItem']"
    pagination: "pagination"
    job_fields:
      - title
      - company
      - location
      - url
      - description
      - salary_min
      - salary_max
      - job_type (full-time/intern)
  ```

#### 1.2 Enhance BaseJobSpider
**File:** `services/scraper/autointern_scraper/spiders/base_spider.py`

Tasks:
- [ ] Add YAML config loading
- [ ] Implement XPath/CSS selector engine
- [ ] Add request headers rotation
- [ ] Implement delay jitter (1-5s random)
- [ ] Add retry middleware (3-5 attempts)
- [ ] Redis push on job parse (auto batching)

```python
class BaseJobSpider(scrapy.Spider):
    def __init__(self, config_file, *args, **kwargs):
        self.config = yaml.safe_load(open(config_file))
        self.redis_client = redis.from_url(os.getenv('REDIS_URL'))
        self.queue_name = 'ingest:jobs'
        self.job_count = 0

    def parse(self, response):
        # Use config selectors to extract jobs
        for job_elem in response.css(self.config['selectors']['job_item']):
            job = {
                'title': job_elem.css(self.config['selectors']['job_title']::text).get(),
                'company': job_elem.css(self.config['selectors']['company']::text).get(),
                'location': job_elem.css(self.config['selectors']['location']::text).get(),
                'url': job_elem.css(self.config['selectors']['job_url']::attr('href')).get(),
                'source': self.name,
                'scraped_at': datetime.now().isoformat(),
            }
            # Push to Redis
            self.redis_client.lpush(self.queue_name, json.dumps(job))
            self.job_count += 1

        # Handle pagination
        next_page = response.css(self.config['selectors']['next_page']::attr('href')).get()
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse)
```

#### 1.3 Implement Indeed Spider
**File:** `services/scraper/autointern_scraper/spiders/indeed_spider.py`

Tasks:
- [ ] Create spider class (subclass BaseJobSpider)
- [ ] Implement search queries (software engineer, internship, etc.)
- [ ] Add location-based crawling (US cities, remote)
- [ ] Implement job description fetcher (2nd request for full details)
- [ ] Add job type detection (full-time, internship, contract)
- [ ] Test with 10 jobs locally
- [ ] Handle anti-bot measures (IP rotation via proxy)

**Config example:**
```yaml
indeed:
  search_queries:
    - "software engineer internship"
    - "full stack developer"
    - "data scientist"
  locations:
    - "San Francisco, CA"
    - "New York, NY"
    - "Remote"
  results_per_page: 50
  max_pages: 20
```

#### 1.4 Create Spider Tests
**File:** `services/scraper/tests/test_indeed_spider.py`

Tasks:
- [ ] Add Indeed sample HTML fixture (`tests/fixtures/indeed_sample.html`)
- [ ] Unit test job extraction from fixture
- [ ] Unit test deduplication via dedupe_signature
- [ ] Test Redis push (mock Redis)
- [ ] Test pagination logic

```python
def test_spider_extracts_jobs_correctly():
    with open('tests/fixtures/indeed_sample.html') as f:
        html = f.read()

    # Parse jobs
    jobs = parse_html(html)
    assert len(jobs) == 10
    assert jobs[0]['title'] == "Software Engineer"
    assert jobs[0]['company'] == "Google"
```

#### 1.5 Add Scraper to CI/CD
**File:** `.github/workflows/ci.yml`

Tasks:
- [ ] Add scraper dep installation
- [ ] Add scraper unit tests to CI
- [ ] Configure Playwright browsers install

---

## 📊 PHASE 2: Additional Job Portals (Week 2-3)

**Goal:** Add Wellfound, RemoteOK, WeWorkRemotely spiders (3-5k more jobs each)

### Tasks

#### 2.1 Wellfound Spider
**File:** `services/scraper/autointern_scraper/spiders/wellfound_spider.py`

- [ ] Scrape startup job listings
- [ ] Extract equity/salary info
- [ ] Handle pagination (API or HTML)
- [ ] Test with 100 jobs
- [ ] Add fixtures and tests

**Key differences:**
- API endpoint available → use API instead of HTML scraping
- Endpoint: `api.wellfound.com/jobs?q=software%20engineer&limit=100`
- Returns JSON directly

#### 2.2 RemoteOK Spider
**File:** `services/scraper/autointern_scraper/spiders/remoteok_spider.py`

- [ ] Scrape remoteok.io
- [ ] Extract remote job listings
- [ ] Handle Cloudflare protection (use Plawright)
- [ ] Parse job slug → fetch full details
- [ ] Test with 100 jobs

#### 2.3 WeWorkRemotely Spider
**File:** `services/scraper/autointern_scraper/spiders/weworkremotely_spider.py`

- [ ] Scrape weworkremotely.com
- [ ] Extract categories, companies
- [ ] Pagination handling
- [ ] Test with 100 jobs

#### 2.4 LinkedIn Spider (Limited)
**File:** `services/scraper/autointern_scraper/spiders/linkedin_spider.py`

⚠️ **Important:** LinkedIn's ToS prohibits scraping; use API only:
- [ ] Setup LinkedIn Recruiter API (if available)
- [ ] OR use RSS feeds (if available)
- [ ] OR document as "manual data source only"
- [ ] Store credentials in env vars

**Document decision in:** `docs/legal.md`

---

## 📝 PHASE 3: Resume Upload & Skill Extraction (Week 3-4)

**Goal:** Enable users to upload resumes and extract skills

### Tasks

#### 3.1 Resume Upload Endpoint
**File:** `services/api/app/routes/resumes.py`

```python
@router.post("/users/{user_id}/resume")
async def upload_resume(
    user_id: UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token)
):
    """Upload and parse resume"""
    # Validate file type (PDF, DOCX, TXT)
    if file.content_type not in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, TXT allowed")

    # Save file to MinIO
    file_key = f"resumes/{user_id}/{file.filename}"
    file_content = await file.read()
    minio_client.put_object('autointern', file_key, BytesIO(file_content), len(file_content))

    # Extract text
    text = extract_text_from_file(file_content, file.content_type)

    # Extract skills
    skills = extract_skills(text)

    # Store in DB
    resume = Resume(
        user_id=user_id,
        file_url=f"s3://autointern/{file_key}",
        raw_text=text,
        extracted_skills=skills,
        updated_at=datetime.now()
    )
    db.add(resume)
    await db.commit()

    return {"skills": skills, "resume_id": resume.id}
```

#### 3.2 Text Extraction Service
**File:** `services/processor/text_extractor.py`

Tasks:
- [ ] Install libraries: `pypdf`, `python-docx`, `pdfplumber`
- [ ] Implement PDF → text (pdfplumber)
- [ ] Implement DOCX → text (python-docx)
- [ ] Implement TXT → text (passthrough)
- [ ] Handle encoding issues (UTF-8, etc.)

```python
from pdfplumber import PDF
from docx import Document

def extract_text_from_file(file_bytes, content_type):
    if content_type == 'application/pdf':
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = '\n'.join([page.extract_text() for page in pdf.pages])
    elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        doc = Document(BytesIO(file_bytes))
        text = '\n'.join([p.text for p in doc.paragraphs])
    else:
        text = file_bytes.decode('utf-8')
    return text
```

#### 3.3 Skill Extraction Service
**File:** `services/processor/skill_extractor.py`

Tasks:
- [ ] Load skill database (YAML or JSON)
- [ ] Use spaCy for NER + keyword matching
- [ ] Extract technical + soft skills
- [ ] Return skill categories [backend, frontend, data, infra, etc.]

**Skill categories:**
```yaml
backend:
  - Python
  - Node.js
  - Java
  - Go
  - Rust
frontend:
  - React
  - Vue
  - Angular
  - TypeScript
data:
  - SQL
  - MongoDB
  - Elasticsearch
  - Spark
ml:
  - TensorFlow
  - PyTorch
  - Scikit-learn
infra:
  - Docker
  - Kubernetes
  - AWS
  - GCP
  - Azure
soft:
  - Leadership
  - Communication
  - Problem-solving
```

```python
import spacy
import json

nlp = spacy.load("en_core_web_sm")
SKILLS_DB = json.load(open('skills.json'))

def extract_skills(text):
    doc = nlp(text.lower())
    found_skills = []

    for skill_category, skills_list in SKILLS_DB.items():
        for skill in skills_list:
            if skill.lower() in text.lower():
                found_skills.append({
                    'name': skill,
                    'category': skill_category
                })

    return found_skills
```

#### 3.4 Update Resume Model
**File:** `services/api/app/models/models.py`

```python
class Resume(Base):
    __tablename__ = 'resumes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    file_url = Column(String, nullable=False)  # MinIO S3 path
    raw_text = Column(Text, nullable=False)
    extracted_skills = Column(JSONB, nullable=False)  # [{'name': 'Python', 'category': 'backend'}, ...]
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
```

#### 3.5 Add Migration
**File:** `services/api/alembic/versions/0004_add_resume_table.py`

- [ ] Create migration using `alembic revision --autogenerate`
- [ ] Test migration locally

#### 3.6 Create Tests
- [ ] Unit test text extraction (PDF, DOCX, TXT)
- [ ] Unit test skill extraction
- [ ] Integration test `POST /users/{id}/resume`

---

## 🧠 PHASE 4: Embeddings & Recommendation Engine (Week 4-5)

**Goal:** Generate Sentence-BERT embeddings → Job recommendations

### Tasks

#### 4.1 Setup Sentence-BERT Service
**File:** `services/ai_engine/embeddings.py`

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_job_embedding(job):
    """Generate embedding for a job"""
    text = f"{job['title']} {job['description']} {job['company']} {' '.join(job.get('skills', []))}"
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()

def get_candidate_embedding(resume_skills, resume_text):
    """Generate embedding for a candidate's resume"""
    text = f"{resume_text} {' '.join([s['name'] for s in resume_skills])}"
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()
```

#### 4.2 Create Embeddings Table & Migration
**File:** `services/api/app/models/models.py`

```python
class JobEmbedding(Base):
    __tablename__ = 'job_embeddings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=False)
    embedding = Column(JSONB, nullable=False)  # List[float], 384-dim
    created_at = Column(DateTime, default=datetime.now)

class ResumeEmbedding(Base):
    __tablename__ = 'resume_embeddings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), nullable=False)
    embedding = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
```

#### 4.3 Add Embeddings to Worker Pipeline
**File:** `services/worker/processor.py`

Tasks:
- [ ] After job inserted to DB, generate embedding
- [ ] Store embedding in `job_embeddings` table
- [ ] Catch failures (don't fail job if embedding fails)

```python
async def process_message(message, db, elastic_url):
    # ... existing code ...

    # Insert job
    job = Job(
        title=message['title'],
        # ... other fields ...
    )
    db.add(job)
    await db.flush()

    # Generate embedding
    try:
        from ai_engine.embeddings import get_job_embedding
        embedding = get_job_embedding({
            'title': message['title'],
            'description': message.get('description', ''),
            'company': message.get('company', ''),
            'skills': message.get('skills', [])
        })
        job_emb = JobEmbedding(job_id=job.id, embedding=embedding)
        db.add(job_emb)
    except Exception as e:
        logger.warning(f"Failed to generate embedding for job {job.id}: {e}")

    await db.commit()
```

#### 4.4 Add Resume Embedding Generation
**File:** `services/processor/skill_extractor.py`

Tasks:
- [ ] After resume upload, generate embedding
- [ ] Store in `resume_embeddings` table

#### 4.5 Create Recommendation Endpoint
**File:** `services/api/app/routes/recommendations.py`

```python
@router.get("/users/{user_id}/recommendations")
async def get_job_recommendations(
    user_id: UUID,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token)
):
    """Get top-N job recommendations for user based on resume"""

    # Get user's resume embedding
    resume = await db.execute(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.updated_at.desc())
    )
    resume = resume.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_emb = await db.execute(
        select(ResumeEmbedding).where(ResumeEmbedding.resume_id == resume.id)
    )
    resume_emb = resume_emb.scalar_one_or_none()
    if not resume_emb:
        raise HTTPException(status_code=404, detail="Embedding not found")

    # Get all job embeddings
    job_embs = await db.execute(select(JobEmbedding))
    job_embs = job_embs.scalars().all()

    # Compute cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    user_vec = np.array(resume_emb.embedding)

    scores = []
    for job_emb in job_embs:
        job_vec = np.array(job_emb.embedding)
        sim = cosine_similarity([user_vec], [job_vec])[0][0]
        scores.append({'job_id': job_emb.job_id, 'score': sim})

    # Sort by score, top N
    scores = sorted(scores, key=lambda x: x['score'], reverse=True)[:limit]

    # Fetch jobs
    job_ids = [s['job_id'] for s in scores]
    jobs = await db.execute(select(Job).where(Job.id.in_(job_ids)))
    jobs_dict = {j.id: j for j in jobs.scalars()}

    # Return with scores
    results = []
    for s in scores:
        job = jobs_dict[s['job_id']]
        results.append({
            'job_id': s['job_id'],
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'match_score': round(s['score'], 2),
            'url': job.url
        })

    return results
```

#### 4.6 Add Tests
- [ ] Unit test embedding generation
- [ ] Unit test cosine similarity calculation
- [ ] Integration test `GET /users/{id}/recommendations`

---

## 🔐 PHASE 5: JWT Authentication & Login UI (Week 5-6)

**Goal:** Enable user registration, login, token management

### Tasks

#### 5.1 JWT Token Generation & Verification
**File:** `services/api/app/routes/auth.py`

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Header()):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### 5.2 User Registration Endpoint
**File:** `services/api/app/routes/users.py`

```python
@router.post("/register")
async def register(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Register new user"""
    # Check if user exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash password
    hashed_password = pwd_context.hash(password)

    # Create user
    user = User(
        email=email,
        password_hash=hashed_password,
        created_at=datetime.now()
    )
    db.add(user)
    await db.commit()

    # Generate token
    token = create_access_token({"sub": str(user.id)})

    return {
        "user_id": str(user.id),
        "email": email,
        "token": token
    }
```

#### 5.3 User Login Endpoint
**File:** `services/api/app/routes/auth.py`

```python
@router.post("/login")
async def login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Login user"""
    user = await db.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()

    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})

    return {
        "user_id": str(user.id),
        "email": email,
        "token": token
    }
```

#### 5.4 React Login Component
**File:** `frontend/admin/src/pages/Login.jsx`

```jsx
import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/auth/login', {
        email,
        password
      });
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('user_id', res.data.user_id);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div className="flex justify-center items-center h-screen bg-gray-100">
      <form className="bg-white p-8 rounded shadow-lg w-96" onSubmit={handleLogin}>
        <h1 className="text-2xl font-bold mb-4">Login</h1>
        {error && <div className="text-red-500 mb-4">{error}</div>}

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full p-2 border mb-4"
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-2 border mb-4"
        />

        <button className="w-full bg-blue-500 text-white p-2 rounded" type="submit">
          Login
        </button>
      </form>
    </div>
  );
}
```

#### 5.5 Update Main.js Router
**File:** `frontend/admin/src/App.jsx`

```jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}
```

#### 5.6 Add Tests
- [ ] Unit test password hashing
- [ ] Unit test token generation/verification
- [ ] Integration test register endpoint
- [ ] Integration test login endpoint
- [ ] E2E test login flow (Cypress)

---

## 🎨 PHASE 6: User Dashboard & Job Browsing (Week 6-7)

**Goal:** Build job search, filter, bookmark UI

### Tasks

#### 6.1 Job Search Endpoint
**File:** `services/api/app/routes/jobs.py` (enhance existing)

```python
@router.get("/jobs/search")
async def search_jobs(
    q: str = "",
    location: str = "",
    job_type: str = "",
    salary_min: int = 0,
    limit: int = 20,
    skip: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Search jobs with filters"""
    query = select(Job)

    if q:
        query = query.where(Job.title.ilike(f"%{q}%") | Job.description.ilike(f"%{q}%"))

    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))

    if job_type:
        query = query.where(Job.job_type == job_type)

    if salary_min:
        query = query.where(Job.salary_min >= salary_min)

    result = await db.execute(query.limit(limit).offset(skip))
    jobs = result.scalars().all()

    return {
        "total": len(jobs),
        "jobs": [
            {
                "id": str(job.id),
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_min": job.salary_min,
                "job_type": job.job_type,
                "url": job.url
            }
            for job in jobs
        ]
    }
```

#### 6.2 Saved Jobs / Bookmarks Model
**File:** `services/api/app/models/models.py`

```python
class SavedJob(Base):
    __tablename__ = 'saved_jobs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), nullable=False)
    saved_at = Column(DateTime, default=datetime.now)
    note = Column(String, nullable=True)
```

#### 6.3 Save/Unsave Job Endpoints
**File:** `services/api/app/routes/jobs.py`

```python
@router.post("/users/{user_id}/saved-jobs/{job_id}")
async def save_job(
    user_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token)
):
    """Save job to bookmarks"""
    saved_job = SavedJob(user_id=user_id, job_id=job_id)
    db.add(saved_job)
    await db.commit()
    return {"message": "Job saved"}

@router.get("/users/{user_id}/saved-jobs")
async def get_saved_jobs(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(verify_token)
):
    """Get user's saved jobs"""
    result = await db.execute(
        select(SavedJob).where(SavedJob.user_id == user_id)
    )
    saved = result.scalars().all()

    # Fetch full job details
    job_ids = [s.job_id for s in saved]
    jobs = await db.execute(select(Job).where(Job.id.in_(job_ids)))

    return {
        "saved_jobs": [
            {
                "id": str(j.id),
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "saved_at": next(s.saved_at for s in saved if s.job_id == j.id)
            }
            for j in jobs.scalars()
        ]
    }
```

#### 6.4 Job Search & Browse Component
**File:** `frontend/admin/src/pages/Dashboard.jsx`

```jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');

  useEffect(() => {
    searchJobs();
  }, []);

  const searchJobs = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://localhost:8000/jobs/search', {
        params: { q: searchQuery, location },
        headers: { Authorization: `Bearer ${token}` }
      });
      setJobs(res.data.jobs);
    } catch (err) {
      console.error('Search failed:', err);
    }
    setLoading(false);
  };

  const saveJob = async (jobId) => {
    try {
      const userId = localStorage.getItem('user_id');
      await axios.post(
        `http://localhost:8000/users/${userId}/saved-jobs/${jobId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Job saved!');
    } catch (err) {
      console.error('Failed to save:', err);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Job Search</h1>

      <div className="flex gap-4 mb-6">
        <input
          type="text"
          placeholder="Search jobs..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 p-2 border rounded"
        />
        <input
          type="text"
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="flex-1 p-2 border rounded"
        />
        <button
          onClick={searchJobs}
          className="bg-blue-500 text-white px-6 py-2 rounded"
        >
          Search
        </button>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job) => (
            <div key={job.id} className="p-4 border rounded shadow">
              <h2 className="text-xl font-bold">{job.title}</h2>
              <p className="text-gray-600">{job.company} • {job.location}</p>
              <p className="text-sm text-gray-500 mt-2">{job.url}</p>
              <button
                onClick={() => saveJob(job.id)}
                className="mt-4 bg-green-500 text-white px-4 py-2 rounded"
              >
                Save Job
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 6.5 Add Tests
- [ ] Unit test job search filtering
- [ ] Integration test search endpoint
- [ ] E2E test job search UI

---

## 📧 PHASE 7: Email Notifications & Job Alerts (Week 7-8)

**Goal:** Send job alerts to users based on preferences

### Tasks

#### 7.1 Job Alert Model
**File:** `services/api/app/models/models.py`

```python
class JobAlert(Base):
    __tablename__ = 'job_alerts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    keywords = Column(ARRAY(String), nullable=False)  # ['Python', 'Django']
    locations = Column(ARRAY(String), nullable=False)  # ['San Francisco', 'Remote']
    frequency = Column(String, default='daily')  # daily, weekly
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
```

#### 7.2 Job Alert CRUD Endpoints
**File:** `services/api/app/routes/alerts.py`

```python
@router.post("/users/{user_id}/alerts")
async def create_alert(
    user_id: UUID,
    keywords: list[str],
    locations: list[str],
    frequency: str = "daily",
    db: AsyncSession = Depends(get_db)
):
    """Create job alert"""
    alert = JobAlert(
        user_id=user_id,
        keywords=keywords,
        locations=locations,
        frequency=frequency
    )
    db.add(alert)
    await db.commit()
    return {"alert_id": str(alert.id)}

@router.get("/users/{user_id}/alerts")
async def get_alerts(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get user's job alerts"""
    result = await db.execute(
        select(JobAlert).where(JobAlert.user_id == user_id)
    )
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "keywords": a.keywords,
            "locations": a.locations,
            "frequency": a.frequency
        }
        for a in alerts
    ]
```

#### 7.3 Email Notification Service
**File:** `services/notifications/email_service.py`

```python
import smtplib
from email.mime.text import MIMEText

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")

    def send_job_alert(self, recipient_email, jobs, keywords):
        """Send job alert email"""
        subject = f"New jobs matching {', '.join(keywords)}"

        html = f"""
        <h2>New Job Matches!</h2>
        <p>Hi, we found {len(jobs)} new jobs matching your criteria:</p>
        <ul>
        """

        for job in jobs:
            html += f"""
            <li>
                <h3>{job['title']}</h3>
                <p>{job['company']} • {job['location']}</p>
                <a href="{job['url']}">View Job</a>
            </li>
            """

        html += "</ul>"

        msg = MIMEText(html, 'html')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient_email

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
```

#### 7.4 Alert Processing Worker
**File:** `services/notifications/alert_worker.py`

```python
import asyncio
from datetime import datetime, timedelta

async def process_alerts():
    """Check all active alerts and send emails"""
    alerts = await db.execute(select(JobAlert).where(JobAlert.is_active == True))
    alerts = alerts.scalars().all()

    email_service = EmailService()

    for alert in alerts:
        # Get new jobs matching alert criteria
        matching_jobs = await get_matching_jobs(
            alert.keywords,
            alert.locations,
            alert.user_id
        )

        if matching_jobs:
            user = await db.execute(select(User).where(User.id == alert.user_id))
            user = user.scalar_one()

            email_service.send_job_alert(
                user.email,
                matching_jobs,
                alert.keywords
            )

async def get_matching_jobs(keywords, locations, user_id, limit=5):
    """Find jobs matching alert criteria"""
    query = select(Job)

    for keyword in keywords:
        query = query.where(
            Job.title.ilike(f"%{keyword}%") |
            Job.description.ilike(f"%{keyword}%")
        )

    if locations:
        location_conditions = [Job.location.ilike(f"%{loc}%") for loc in locations]
        query = query.where(or_(*location_conditions))

    result = await db.execute(query.limit(limit))
    return result.scalars().all()
```

#### 7.5 Update .env.example
**File:** `.env.example`

```env
# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

#### 7.6 Add Tests
- [ ] Unit test alert filtering logic
- [ ] Unit test email template generation
- [ ] Integration test alert creation endpoint

---

## 🔒 PHASE 8: Production Hardening (Week 8-9)

**Goal:** Security, rate limiting, error handling, monitoring

### Tasks

#### 8.1 Add Rate Limiting
**File:** `services/api/app/main.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

@app.get("/jobs", dependencies=[Depends(limiter.limit("100/minute"))])
async def list_jobs(...):
    ...
```

#### 8.2 Add CORS
**File:** `services/api/app/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 8.3 Add Input Validation
**File:** `services/api/app/schemas/job.py`

```python
from pydantic import BaseModel, validator

class JobCreateRequest(BaseModel):
    title: str
    company: str
    location: str
    url: str
    description: str

    @validator('title')
    def title_not_empty(cls, v):
        assert len(v) > 0, 'Title cannot be empty'
        return v
```

#### 8.4 Add Error Tracking (Sentry)
**File:** `services/api/app/main.py`

```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0
)
```

#### 8.5 Add Logging
**File:** `services/api/app/core/logger.py`

```python
import logging

logger = logging.getLogger(__name__)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
```

#### 8.6 Add Request/Response Schema Validation
- [ ] Validate all user inputs (email format, password length, etc.)
- [ ] Validate response schemas (prevent unintended data leaks)
- [ ] Add 404/5xx error handlers

#### 8.7 Database Connection Pooling
**File:** `services/api/app/db/session.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={
        "server_settings": {"application_name": "autointern_api"},
        "ssl": "require" if "prod" in os.getenv("ENV", "") else None,
    },
    poolclass=StaticPool if settings.testing else QueuePool,
    pool_size=20,
    max_overflow=10,
)
```

#### 8.8 Add Tests & Documentation
- [ ] Add hidden 30s API response timeout
- [ ] Document all security measures in README
- [ ] Add production checklist

---

## ☸️ PHASE 9: Kubernetes Deployment (Week 9-10)

**Goal:** Production-grade Kubernetes setup

### Tasks

#### 9.1 Create Helm Chart
**Directory:** `infra/helm/autointern/`

Files to create:
- [ ] `Chart.yaml`
- [ ] `values.yaml`
- [ ] `templates/deployment.yaml` (API, Worker, Scraper)
- [ ] `templates/service.yaml`
- [ ] `templates/ingress.yaml`
- [ ] `templates/configmap.yaml` (env vars)
- [ ] `templates/secret.yaml` (secrets)

#### 9.2 Create K8s Manifests
**Directory:** `infra/k8s/`

Production manifests:
- [ ] `api-deployment.yaml`
- [ ] `worker-deployment.yaml`
- [ ] `scraper-cronjob.yaml`
- [ ] `postgres-statefulset.yaml`
- [ ] `redis-statefulset.yaml`
- [ ] `elasticsearch-statefulset.yaml`

#### 9.3 Setup Secrets Management
**Options:**
- [ ] Kubernetes Secrets + external secret operator
- [ ] HashiCorp Vault
- [ ] AWS Secrets Manager

#### 9.4 Setup Monitoring (Production)
- [ ] Prometheus scraper for K8s metrics
- [ ] Custom dashboards in Grafana
- [ ] Alert rules for SLA

#### 9.5 Setup CI/CD (GitOps)
- [ ] GitHub Actions → build images → push to registry (DockerHub/ECR)
- [ ] ArgoCD for GitOps deployment

#### 9.6 Deployment Instructions
**File:** `docs/kubernetes_deployment.md`

- [ ] Create namespace
- [ ] Apply secrets
- [ ] Install Helm chart
- [ ] Verify pods running
- [ ] Test endpoints

---

## 🧪 TESTING STRATEGY (All Phases)

### Unit Tests
- Skill extraction logic
- Embedding generation
- Alert matching logic
- Email template rendering

### Integration Tests
- Resume upload → skill extraction
- Job spider → Redis queue
- Worker → PostgreSQL + Elasticsearch
- Job alert matching

### E2E Tests (Cypress)
- User registration → login → job search → save → recommendations
- Admin DLQ workflow (existing)
- Alert management

### Load Tests
- 1000 concurrent users searching jobs
- Worker processing 100 jobs/sec
- Scraper handling 10k jobs/hour

---

## 📚 DOCUMENTATION (All Phases)

Create/Update:
- [ ] `docs/architecture.md` — System design
- [ ] `docs/api.md` — API reference (auto-generated from OpenAPI)
- [ ] `docs/scraping.md` — Scraper development guide
- [ ] `docs/deployment.md` — Setup instructions
- [ ] `docs/legal.md` — Terms of service compliance
- [ ] `CONTRIBUTING.md` — Dev guidelines
- [ ] Update `.github/copilot-instructions.md` (done!)

---

## 🚀 DEPLOYMENT & LAUNCH CHECKLIST

Before production:
- [ ] SSL/TLS certificates
- [ ] Database backups configured
- [ ] Monitoring & alerting live
- [ ] Rate limiting + CORS locks down
- [ ] Admin accounts secured
- [ ] Scraper ToS compliance reviewed
- [ ] GDPR/privacy policy drafted
- [ ] API versioning scheme finalized
- [ ] Load testing complete (1000+ concurrent users)
- [ ] Disaster recovery plan documented

---

## 📊 Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1 | Week 1-2 | Indeed spider + 10k jobs |
| 2 | Week 2-3 | Wellfound, RemoteOK, WWR spiders |
| 3 | Week 3-4 | Resume upload & skill extraction |
| 4 | Week 4-5 | BERT embeddings + recommendations |
| 5 | Week 5-6 | JWT auth + login UI |
| 6 | Week 6-7 | Job dashboard + search UI |
| 7 | Week 7-8 | Email alerts + notifications |
| 8 | Week 8-9 | Security hardening |
| 9 | Week 9-10 | Kubernetes deployment |
| **Total** | **10 weeks** | **Production-ready platform** |

---

## 🎯 Success Metrics

By end of Phase 9, you should have:
- ✅ 50k+ tech job listings in database
- ✅ 1000+ users registered
- ✅ Job recommendations working (>80% relevance)
- ✅ Email alerts being sent (>90% delivery)
- ✅ API running on Kubernetes (99.9% uptime SLA)
- ✅ <2s median response time
- ✅ <1% error rate

---

## Next Steps

1. **Approve this roadmap** — Any changes?
2. **Choose a phase to start** — I recommend Phase 1 (Indeed spider)
3. **Begin development** — I can help write code for each phase

Ready to begin Phase 1? 🚀
