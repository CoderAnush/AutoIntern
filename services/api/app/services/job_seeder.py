"""
India-first job seeder — sample data from top Indian IT companies.

Salaries are expressed in INR (Indian Rupees) using LPA (Lakh Per Annum) format.
Apply URLs point to the actual careers pages of each company.
This is seed / demo data, not live job postings.
"""

import uuid
from datetime import datetime, timedelta
import random

# Indian IT companies with verified careers pages
COMPANIES = [
    {
        "name": "TCS",
        "career_url": "https://www.tcs.com/careers",
        "locations": ["Mumbai, India", "Pune, India", "Bengaluru, India", "Chennai, India", "Hyderabad, India"],
        "is_india": True,
    },
    {
        "name": "Infosys",
        "career_url": "https://career.infosys.com",
        "locations": ["Bengaluru, India", "Pune, India", "Hyderabad, India", "Chennai, India", "Mysuru, India"],
        "is_india": True,
    },
    {
        "name": "Wipro",
        "career_url": "https://careers.wipro.com",
        "locations": ["Bengaluru, India", "Hyderabad, India", "Pune, India", "Chennai, India", "Kolkata, India"],
        "is_india": True,
    },
    {
        "name": "HCLTech",
        "career_url": "https://www.hcltech.com/careers",
        "locations": ["Noida, India", "Chennai, India", "Bengaluru, India", "Hyderabad, India", "Pune, India"],
        "is_india": True,
    },
    {
        "name": "Tech Mahindra",
        "career_url": "https://careers.techmahindra.com",
        "locations": ["Pune, India", "Hyderabad, India", "Bengaluru, India", "Noida, India", "Chennai, India"],
        "is_india": True,
    },
    {
        "name": "Freshworks",
        "career_url": "https://www.freshworks.com/company/careers",
        "locations": ["Chennai, India", "Bengaluru, India", "Hyderabad, India"],
        "is_india": True,
    },
    {
        "name": "Zoho",
        "career_url": "https://www.zoho.com/careers.html",
        "locations": ["Chennai, India", "Bengaluru, India", "Coimbatore, India"],
        "is_india": True,
    },
    {
        "name": "Razorpay",
        "career_url": "https://razorpay.com/jobs",
        "locations": ["Bengaluru, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "CRED",
        "career_url": "https://careers.cred.club",
        "locations": ["Bengaluru, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "BrowserStack",
        "career_url": "https://www.browserstack.com/careers",
        "locations": ["Mumbai, India", "Bengaluru, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "Postman",
        "career_url": "https://www.postman.com/company/careers",
        "locations": ["Bengaluru, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "Swiggy",
        "career_url": "https://careers.swiggy.com",
        "locations": ["Bengaluru, India", "Hyderabad, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "Zomato",
        "career_url": "https://www.zomato.com/careers",
        "locations": ["Gurugram, India", "Bengaluru, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "Meesho",
        "career_url": "https://meesho.io/jobs",
        "locations": ["Bengaluru, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "PhonePe",
        "career_url": "https://www.phonepe.com/en/careers.html",
        "locations": ["Bengaluru, India", "Pune, India"],
        "is_india": True,
    },
    {
        "name": "Delhivery",
        "career_url": "https://www.delhivery.com/careers",
        "locations": ["Gurugram, India", "Bengaluru, India", "Delhi, India"],
        "is_india": True,
    },
    {
        "name": "Druva",
        "career_url": "https://www.druva.com/company/careers",
        "locations": ["Pune, India", "Bengaluru, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "Chargebee",
        "career_url": "https://www.chargebee.com/careers",
        "locations": ["Chennai, India", "Bengaluru, India", "Remote - India"],
        "is_india": True,
    },
    {
        "name": "Persistent Systems",
        "career_url": "https://www.persistent.com/careers",
        "locations": ["Pune, India", "Nagpur, India", "Bengaluru, India", "Hyderabad, India"],
        "is_india": True,
    },
    {
        "name": "Mphasis",
        "career_url": "https://careers.mphasis.com",
        "locations": ["Bengaluru, India", "Pune, India", "Chennai, India"],
        "is_india": True,
    },
]

# India-appropriate job templates with INR salaries
JOB_TEMPLATES = [
    {
        "title": "Software Engineer — Fresher",
        "job_type": "Full-time",
        "salary_range": "₹3.5–6 LPA",
        "description": (
            "We are hiring B.E./B.Tech/MCA graduates (2024 or 2025 passout) to join our software engineering team. "
            "You will work on building and maintaining production systems alongside senior engineers.\n\n"
            "Requirements:\n"
            "- B.E./B.Tech in Computer Science, IT, or Electronics (2024/2025 batch)\n"
            "- Strong fundamentals in data structures and algorithms\n"
            "- Proficiency in at least one language: Java, Python, or C++\n"
            "- Familiarity with SQL and basic DBMS concepts\n"
            "- CGPA 6.5 and above preferred\n\n"
            "Bond: No bond. Permanent employment from day one."
        ),
    },
    {
        "title": "Software Development Engineer (SDE-1)",
        "job_type": "Full-time",
        "salary_range": "₹8–14 LPA",
        "description": (
            "Looking for 0–2 years of experience engineers for our product engineering team. "
            "You will design, build, and ship features used by millions of users.\n\n"
            "Requirements:\n"
            "- 0–2 years of software engineering experience\n"
            "- Strong problem-solving and data structures skills\n"
            "- Experience with Java, Python, or Go\n"
            "- Familiarity with REST APIs and microservices\n"
            "- Experience with Git and CI/CD pipelines\n"
        ),
    },
    {
        "title": "Software Development Engineer (SDE-2)",
        "job_type": "Full-time",
        "salary_range": "₹18–30 LPA",
        "description": (
            "We are looking for a mid-level SDE to join our engineering team. "
            "You will lead feature development, mentor junior engineers, and drive technical decisions.\n\n"
            "Requirements:\n"
            "- 2–5 years of software engineering experience\n"
            "- Strong system design and distributed systems knowledge\n"
            "- Proficiency in Java, Python, Go, or Kotlin\n"
            "- Experience with cloud platforms (AWS, GCP, or Azure)\n"
            "- Experience with Docker and Kubernetes\n"
        ),
    },
    {
        "title": "Frontend Engineer",
        "job_type": "Full-time",
        "salary_range": "₹12–22 LPA",
        "description": (
            "Build beautiful, performant web experiences for our users. "
            "You will work with React, TypeScript, and our design system to ship product features.\n\n"
            "Requirements:\n"
            "- 1–4 years of frontend development experience\n"
            "- Strong JavaScript/TypeScript skills\n"
            "- Proficiency with React or Vue\n"
            "- Understanding of web performance (Core Web Vitals)\n"
            "- Experience with CSS frameworks and responsive design\n"
        ),
    },
    {
        "title": "Backend Engineer — Python",
        "job_type": "Full-time",
        "salary_range": "₹14–25 LPA",
        "description": (
            "Design and build scalable backend services. "
            "You will work with Python, PostgreSQL, and cloud infrastructure to power our platform.\n\n"
            "Requirements:\n"
            "- 2–5 years of backend engineering experience\n"
            "- Strong Python skills (FastAPI, Django, or Flask)\n"
            "- PostgreSQL/MySQL database design experience\n"
            "- Knowledge of Redis, Celery, and message queues\n"
            "- Experience deploying on AWS or GCP\n"
        ),
    },
    {
        "title": "Data Engineer",
        "job_type": "Full-time",
        "salary_range": "₹15–28 LPA",
        "description": (
            "Build and maintain data pipelines that power our analytics and ML systems.\n\n"
            "Requirements:\n"
            "- 2–4 years of data engineering experience\n"
            "- Strong SQL and Python skills\n"
            "- Experience with Apache Spark, Airflow, or Flink\n"
            "- Familiarity with BigQuery, Redshift, or Snowflake\n"
            "- Understanding of data modelling and ETL patterns\n"
        ),
    },
    {
        "title": "Machine Learning Engineer",
        "job_type": "Full-time",
        "salary_range": "₹20–40 LPA",
        "description": (
            "Build and deploy ML models at scale for recommendation, search, and fraud detection.\n\n"
            "Requirements:\n"
            "- M.Tech/M.S. in CS/AI/ML or 3+ years practical ML experience\n"
            "- Strong Python and PyTorch/TensorFlow skills\n"
            "- Experience with ML pipelines and MLOps (MLflow, SageMaker, or Vertex AI)\n"
            "- Solid statistics and probability foundation\n"
            "- Experience with large-scale data processing (Spark, Beam)\n"
        ),
    },
    {
        "title": "DevOps / Platform Engineer",
        "job_type": "Full-time",
        "salary_range": "₹16–28 LPA",
        "description": (
            "Manage and improve our cloud infrastructure, CI/CD pipelines, and developer tooling.\n\n"
            "Requirements:\n"
            "- 2–5 years of DevOps / SRE experience\n"
            "- Strong Kubernetes and Helm chart experience\n"
            "- AWS/GCP/Azure certified preferred\n"
            "- Proficiency with Terraform and infrastructure-as-code\n"
            "- Experience with Prometheus, Grafana, and on-call workflows\n"
        ),
    },
    {
        "title": "Mobile Engineer — Android",
        "job_type": "Full-time",
        "salary_range": "₹14–24 LPA",
        "description": (
            "Build native Android experiences for millions of users in India.\n\n"
            "Requirements:\n"
            "- 2–4 years of Android development (Kotlin/Java)\n"
            "- Experience with Jetpack Compose and MVVM architecture\n"
            "- Strong understanding of Android performance optimisation\n"
            "- Familiarity with Firebase, Retrofit, and Room\n"
            "- Published apps on the Play Store preferred\n"
        ),
    },
    {
        "title": "Product Manager",
        "job_type": "Full-time",
        "salary_range": "₹22–40 LPA",
        "description": (
            "Drive product strategy and execution for one of our core product areas.\n\n"
            "Requirements:\n"
            "- MBA or B.Tech with 2+ years PM experience\n"
            "- Strong analytical and data-driven decision-making skills\n"
            "- Excellent cross-functional communication\n"
            "- Experience with A/B testing and growth metrics\n"
            "- Prior engineering or design background is a plus\n"
        ),
    },
    {
        "title": "Software Engineering Intern",
        "job_type": "Internship",
        "salary_range": "₹40,000–80,000/mo",
        "description": (
            "6-month internship for pre-final or final year B.Tech/BE students. "
            "Work on real product features alongside full-time engineers.\n\n"
            "Requirements:\n"
            "- Pre-final or final year B.Tech/BE/MCA\n"
            "- Good DSA fundamentals (LeetCode medium level)\n"
            "- At least one language: Python, Java, or C++\n"
            "- Prior project work or open-source contributions are a plus\n"
            "- Minimum 6 months availability\n"
        ),
    },
    {
        "title": "Data Science Intern",
        "job_type": "Internship",
        "salary_range": "₹30,000–60,000/mo",
        "description": (
            "6-month data science internship for M.Tech/M.S./final-year students.\n\n"
            "Requirements:\n"
            "- Pursuing M.Tech, M.S., or final-year B.Tech in CS/AI/Statistics\n"
            "- Proficiency in Python, pandas, scikit-learn\n"
            "- Experience with SQL and data analysis\n"
            "- Familiarity with NLP or computer vision is a plus\n"
            "- Strong communication skills for presenting findings\n"
        ),
    },
    {
        "title": "Site Reliability Engineer (SRE)",
        "job_type": "Full-time",
        "salary_range": "₹18–32 LPA",
        "description": (
            "Ensure reliability, availability, and performance of our systems at scale.\n\n"
            "Requirements:\n"
            "- 2–5 years of SRE or infrastructure engineering experience\n"
            "- Strong Linux and networking fundamentals\n"
            "- Experience with incident management and postmortem culture\n"
            "- Proficiency in Python or Go for automation\n"
            "- Kubernetes, Prometheus, and distributed tracing experience\n"
        ),
    },
    {
        "title": "Security Engineer",
        "job_type": "Full-time",
        "salary_range": "₹20–38 LPA",
        "description": (
            "Protect our platform, users, and data from security threats.\n\n"
            "Requirements:\n"
            "- 3+ years in application or cloud security\n"
            "- Experience with VAPT, threat modelling, and secure code review\n"
            "- OSCP, CEH, or equivalent certification preferred\n"
            "- Knowledge of OWASP Top 10 and CWE standards\n"
            "- Familiarity with AWS/GCP security controls\n"
        ),
    },
    {
        "title": "UX Designer",
        "job_type": "Full-time",
        "salary_range": "₹12–22 LPA",
        "description": (
            "Design intuitive, delightful user experiences for millions of users.\n\n"
            "Requirements:\n"
            "- 2–4 years of UX/product design experience\n"
            "- Strong portfolio demonstrating end-to-end design process\n"
            "- Proficiency in Figma\n"
            "- Experience conducting user research and usability testing\n"
            "- Good understanding of accessibility standards (WCAG)\n"
        ),
    },
]


def generate_seed_jobs() -> list[dict]:
    """Generate seed jobs from Indian IT companies with INR salaries."""
    jobs = []
    now = datetime.utcnow()

    for company in COMPANIES:
        num_jobs = random.randint(3, 5)
        templates = random.sample(JOB_TEMPLATES, min(num_jobs, len(JOB_TEMPLATES)))
        for tmpl in templates:
            location = random.choice(company["locations"])
            days_ago = random.randint(0, 21)
            jobs.append({
                "id": str(uuid.uuid4()),
                "source": "seed",
                "external_id": f"seed-{uuid.uuid4().hex[:8]}",
                "title": tmpl["title"],
                "description": (
                    f"{tmpl['description']}\n\n"
                    f"About {company['name']}: This role is based in {location}. "
                    f"Apply at: {company['career_url']}"
                ),
                "location": location,
                "company_name": company["name"],
                "apply_url": company["career_url"],
                "salary_range": tmpl["salary_range"],
                "job_type": tmpl["job_type"],
                "posted_at": (now - timedelta(days=days_ago)).isoformat(),
                "is_india_job": company["is_india"],
            })

    return jobs
