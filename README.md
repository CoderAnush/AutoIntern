# AutoIntern AI

AutoIntern AI is an AI-powered job & internship aggregation and recommendation platform for students and entry-level engineers.

This repository is a monorepo with microservices scaffolding (FastAPI backend, Scrapy scrapers, AI engine, React frontend).

Goals:
- Scrape 100+ job sites, company career pages
- Parse resumes & extract skills
- Build semantic matching (Sentence-BERT + FAISS)
- Provide dashboard and notifications

Next steps:
1. Review initial scaffold
2. Approve changes to commit
3. Implement services incrementally per roadmap

For development:
- Copy `.env.example` to `.env`
- `docker compose up --build`

See `docs/` for architecture and design notes.
