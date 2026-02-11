# Phase 1: Indeed Spider Implementation Guide

## ✅ What's Been Implemented

### Files Created:
1. ✅ `services/scraper/autointern_scraper/sites_config.yaml` — Configuration for Indeed, Wellfound, RemoteOK, WeWorkRemotely
2. ✅ `services/scraper/autointern_scraper/spiders/base_spider.py` — Enhanced base spider with:
   - YAML config loading
   - Redis queue integration
   - Job extraction logic
   - Pagination handling
   - Deduplication via signatures
3. ✅ `services/scraper/autointern_scraper/spiders/indeed_spider.py` — Indeed-specific spider
4. ✅ `services/scraper/tests/test_indeed_spider.py` — Unit tests (10+ test cases)
5. ✅ `services/scraper/tests/fixtures/indeed_sample.html` — Test HTML fixture
6. ✅ Updated `services/scraper/requirements.txt` — Added PyYAML

---

## 🚀 How to Run the Indeed Spider

### Option 1: Local Testing (No Docker)

```bash
cd services/scraper

# Install dependencies
pip install -r requirements.txt

# Setup Playwright (one-time)
playwright install

# Run unit tests
python -m pytest tests/test_indeed_spider.py -v

# Run spider (requires Redis running)
# NOTE: This will try to scrape real Indeed pages
# Make sure Redis is running at localhost:6379
# OR set REDIS_URL env var

REDIS_URL="redis://localhost:6379" scrapy crawl indeed
```

### Option 2: With Docker Compose (Recommended)

```bash
cd /path/to/AutoIntern

# Start all services (including Redis)
docker compose up --build

# In another terminal, run spider inside container
docker compose exec scraper bash

# Inside container:
cd services/scraper
playwright install
scrapy crawl indeed
```

### Option 3: Test Only (No Real Scraping)

```bash
cd services/scraper

# Install dependencies
pip install -r requirements.txt
pip install pytest

# Run unit tests against fixture HTML
python -m pytest tests/test_indeed_spider.py::TestIndeedSpider -v

# Expected output:
# test_spider_initialization PASSED
# test_parse_extracts_correct_number_of_jobs PASSED
# test_job_extraction_fields PASSED
# test_job_title_extraction PASSED
# test_company_extraction PASSED
# test_location_extraction PASSED
# test_salary_parsing PASSED
# test_job_type_detection PASSED
# test_deduplication_signature PASSED
# test_push_to_queue PASSED
```

---

## 📊 What the Spider Does

### 1. **Searches Indeed** for job queries:
   - "software engineer"
   - "full stack developer"
   - "data scientist"
   - "backend engineer"
   - "frontend developer"
   - "devops engineer"
   - "machine learning engineer"
   - "internship"

### 2. **In Locations:**
   - United States
   - Remote

### 3. **Extracts for Each Job:**
   - Job title
   - Company name
   - Location
   - Job URL
   - Job description
   - Salary range (if available)
   - Job type (full-time, internship, contract)
   - Posted date
   - Scraped timestamp

### 4. **Pushes to Redis:**
   - Queue: `ingest:jobs`
   - Format: JSON with all fields
   - Includes deduplication signature

### 5. **Worker Processes:**
   - Stores in PostgreSQL
   - Indexes in Elasticsearch
   - Exports metrics

---

## 🔍 Monitoring Spider Progress

### Check Queue Size
```bash
# Using Redis CLI
docker compose exec redis redis-cli LLEN ingest:jobs

# Or via scraper logs
docker compose logs scraper -f | grep "Pushed job"
```

### Check Jobs in Database
```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U autointern -d autointern

# Inside psql:
SELECT COUNT(*) FROM jobs;
SELECT title, company, location FROM jobs LIMIT 10;
```

### Check Elasticsearch Index
```bash
# Check index health
curl http://localhost:9200/_cluster/health

# Search jobs
curl -X GET "http://localhost:9200/autointern-jobs/_search?q=software"

# Count jobs indexed
curl -X GET "http://localhost:9200/autointern-jobs/_count"
```

### Watch Worker Process Jobs
```bash
docker compose logs worker -f | grep -E "PROCESSED|DLQ|error"
```

---

## 📈 Expected Results

After running the spider for ~5-10 minutes (depending on Indeed's response):

- **Jobs Scraped:** 100-200+ (8 queries × 2 locations × multiple pages)
- **Jobs Pushed to Queue:** 100-200+
- **Jobs in Database:** 80-180+ (some may be duplicated/filtered)
- **Jobs in Elasticsearch:** 80-180+
- **No Errors:** Worker should process queue cleanly

---

## ⚙️ Configuration

### To Modify Search Queries

Edit `services/scraper/autointern_scraper/sites_config.yaml`:

```yaml
indeed:
  search_queries:
    - "your query here"
    - "another query"

  search_locations:
    - "City, State"
```

### To Limit Scraping (for testing)

Change `max_pages` in config:

```yaml
indeed:
  pagination:
    max_pages: 2  # Only scrape 2 pages = ~20 jobs instead of 500
```

### To Change Rate Limiting

```yaml
indeed:
  download_delay: 5  # Wait 5 seconds between requests (default 2)
  randomize_delay: true  # Add random jitter
```

---

## 🐛 Troubleshooting

### Error: "Sites config file not found"
```bash
# Make sure you're in the scraper directory
cd services/scraper

# And the file exists:
ls autointern_scraper/sites_config.yaml
```

### Error: "Redis connection refused"
```bash
# Start Docker services:
docker compose up --build

# Or start Redis locally:
redis-server
```

### Error: "Playwright browsers not installed"
```bash
cd services/scraper
playwright install
```

### Spider runs but pushes 0 jobs
1. Check Indeed's HTML hasn't changed (selectors in config may be outdated)
2. Increase `DOWNLOAD_DELAY` (Indeed may be blocking)
3. Check logs for selector errors:
   ```bash
   docker compose logs scraper | grep -i "error\|failed"
   ```

### Test failures
```bash
# Run with verbose output
python -m pytest tests/test_indeed_spider.py -vv -s
```

---

## 📝 Next Steps After Phase 1

Once Indeed spider is working:

1. ✅ **Verify** jobs are flowing into PostgreSQL + Elasticsearch
2. ✅ **Test** API can search jobs: `GET http://localhost:8000/jobs?q=python`
3. ✅ **Monitor** Prometheus metrics: `curl http://localhost:8000/metrics`
4. ✅ **Create a branch** for Phase 2 (Wellfound spider):
   ```bash
   git checkout -b dev/phase-2-wellfound-spider
   ```

---

## 💡 Key Insights

- **BaseJobSpider handles 90% of work** — New spiders just inherit and set `site_name`
- **sites_config.yaml is the source of truth** — Easy to add new sites
- **Deduplication happens at multiple levels:**
  - Spider: generates signature
  - Worker: checks if signature exists in DB
  - PostgreSQL: unique index on (title, company, location)
- **Worker retries 3 times** — Failed jobs go to DLQ
- **Full monitoring included** — Prometheus metrics tracked automatically

---

## 📞 Need Help?

Check:
1. `IMPLEMENTATION_ROADMAP.md` → Phase 1 section for detailed tasks
2. `.github/copilot-instructions.md` → Scraper development section
3. `services/scraper/README.md` → Scrapy basics
4. `docker compose logs` → See what's happening in real-time
