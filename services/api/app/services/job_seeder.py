"""Job seeder with realistic jobs from top-tier companies."""

import uuid
from datetime import datetime, timedelta
import random

COMPANIES = [
    {"name": "Google", "career_url": "https://careers.google.com", "locations": ["Mountain View, CA", "New York, NY", "London, UK", "Bangalore, India"]},
    {"name": "Microsoft", "career_url": "https://careers.microsoft.com", "locations": ["Redmond, WA", "New York, NY", "Bangalore, India", "Dublin, Ireland"]},
    {"name": "Amazon", "career_url": "https://www.amazon.jobs", "locations": ["Seattle, WA", "Arlington, VA", "Austin, TX", "Vancouver, Canada"]},
    {"name": "Meta", "career_url": "https://www.metacareers.com", "locations": ["Menlo Park, CA", "New York, NY", "London, UK", "Singapore"]},
    {"name": "Apple", "career_url": "https://jobs.apple.com", "locations": ["Cupertino, CA", "Austin, TX", "London, UK", "Shanghai, China"]},
    {"name": "Netflix", "career_url": "https://jobs.netflix.com", "locations": ["Los Gatos, CA", "Los Angeles, CA", "London, UK", "Remote"]},
    {"name": "Tesla", "career_url": "https://www.tesla.com/careers", "locations": ["Austin, TX", "Fremont, CA", "Berlin, Germany", "Shanghai, China"]},
    {"name": "NVIDIA", "career_url": "https://www.nvidia.com/en-us/about-nvidia/careers", "locations": ["Santa Clara, CA", "Austin, TX", "Bangalore, India", "Remote"]},
    {"name": "Stripe", "career_url": "https://stripe.com/jobs", "locations": ["San Francisco, CA", "New York, NY", "Dublin, Ireland", "Remote"]},
    {"name": "Spotify", "career_url": "https://www.lifeatspotify.com", "locations": ["Stockholm, Sweden", "New York, NY", "London, UK", "Remote"]},
    {"name": "Salesforce", "career_url": "https://careers.salesforce.com", "locations": ["San Francisco, CA", "Indianapolis, IN", "London, UK", "Hyderabad, India"]},
    {"name": "Adobe", "career_url": "https://careers.adobe.com", "locations": ["San Jose, CA", "New York, NY", "Bangalore, India", "Remote"]},
    {"name": "Uber", "career_url": "https://www.uber.com/careers", "locations": ["San Francisco, CA", "New York, NY", "Amsterdam, Netherlands", "Bangalore, India"]},
    {"name": "Airbnb", "career_url": "https://careers.airbnb.com", "locations": ["San Francisco, CA", "Remote"]},
    {"name": "Goldman Sachs", "career_url": "https://www.goldmansachs.com/careers", "locations": ["New York, NY", "London, UK", "Bangalore, India", "Dallas, TX"]},
    {"name": "JPMorgan Chase", "career_url": "https://careers.jpmorgan.com", "locations": ["New York, NY", "Chicago, IL", "London, UK", "Bangalore, India"]},
    {"name": "Deloitte", "career_url": "https://www2.deloitte.com/careers", "locations": ["New York, NY", "Chicago, IL", "London, UK", "Hyderabad, India"]},
]

JOB_TEMPLATES = [
    {
        "title": "Software Engineer Intern",
        "job_type": "Internship",
        "salary_range": "$30-50/hr",
        "description": "Join our engineering team as a Software Engineer Intern. You'll work on real production systems, collaborate with senior engineers, and contribute to projects used by millions. Requirements: Currently pursuing a BS/MS in Computer Science or related field. Proficiency in at least one programming language (Python, Java, C++, JavaScript). Strong problem-solving skills. Experience with data structures and algorithms. Familiarity with version control (Git)."
    },
    {
        "title": "Data Science Intern",
        "job_type": "Internship",
        "salary_range": "$35-55/hr",
        "description": "As a Data Science Intern, you'll analyze large datasets, build machine learning models, and derive actionable insights. Requirements: Pursuing MS/PhD in Statistics, Computer Science, or related quantitative field. Proficiency in Python and SQL. Experience with pandas, scikit-learn, or TensorFlow. Strong statistical analysis skills. Excellent communication skills for presenting findings."
    },
    {
        "title": "Frontend Developer",
        "job_type": "Full-time",
        "salary_range": "$120k-160k/yr",
        "description": "Build beautiful, responsive user interfaces that delight millions of users. You'll work with React, TypeScript, and modern web technologies. Requirements: 2+ years experience with React or similar frameworks. Strong TypeScript/JavaScript skills. Experience with CSS-in-JS, Tailwind, or similar. Understanding of web performance optimization. Experience with testing frameworks (Jest, Cypress)."
    },
    {
        "title": "Backend Engineer",
        "job_type": "Full-time",
        "salary_range": "$130k-180k/yr",
        "description": "Design and build scalable backend services that power our platform. You'll work with microservices, databases, and cloud infrastructure. Requirements: 3+ years experience with Python, Go, or Java. Experience with PostgreSQL, Redis, or MongoDB. Familiarity with Docker, Kubernetes, and CI/CD. Understanding of RESTful API design. Experience with distributed systems."
    },
    {
        "title": "Machine Learning Engineer",
        "job_type": "Full-time",
        "salary_range": "$150k-220k/yr",
        "description": "Develop and deploy ML models at scale. You'll work on recommendation systems, NLP, or computer vision. Requirements: MS/PhD in ML, AI, or related field. 3+ years experience with PyTorch or TensorFlow. Strong Python skills. Experience with ML infrastructure (MLflow, Kubeflow). Published research is a plus."
    },
    {
        "title": "Product Manager Intern",
        "job_type": "Internship",
        "salary_range": "$35-50/hr",
        "description": "Drive product strategy and execution as a PM Intern. You'll work with engineering, design, and business teams. Requirements: Pursuing MBA or BS in technical/business field. Strong analytical and communication skills. Experience with data analysis tools. Ability to define product requirements. Interest in technology and user experience."
    },
    {
        "title": "DevOps Engineer",
        "job_type": "Full-time",
        "salary_range": "$125k-170k/yr",
        "description": "Build and maintain our cloud infrastructure and deployment pipelines. Requirements: 2+ years experience with AWS, GCP, or Azure. Proficiency in Terraform, Ansible, or CloudFormation. Experience with Docker and Kubernetes. Strong Linux administration skills. Experience with monitoring tools (Prometheus, Grafana, Datadog)."
    },
    {
        "title": "Mobile Developer",
        "job_type": "Full-time",
        "salary_range": "$130k-175k/yr",
        "description": "Build native mobile experiences for iOS and Android. Requirements: 2+ years experience with Swift/Kotlin or React Native/Flutter. Understanding of mobile UI/UX best practices. Experience with RESTful APIs. App Store/Play Store publishing experience. Strong debugging and optimization skills."
    },
    {
        "title": "Security Engineer",
        "job_type": "Full-time",
        "salary_range": "$140k-200k/yr",
        "description": "Protect our platform and users from security threats. Requirements: 3+ years in cybersecurity or application security. Experience with penetration testing, vulnerability assessment. Knowledge of OWASP Top 10. Familiarity with security tools (Burp Suite, Nessus). Experience with cloud security (AWS/GCP)."
    },
    {
        "title": "UX Designer Intern",
        "job_type": "Internship",
        "salary_range": "$28-45/hr",
        "description": "Design intuitive user experiences for our products. Requirements: Pursuing degree in Design, HCI, or related field. Proficiency in Figma or Sketch. Strong portfolio demonstrating UX process. Understanding of user research methods. Basic prototyping skills."
    },
    {
        "title": "Data Engineer",
        "job_type": "Full-time",
        "salary_range": "$130k-175k/yr",
        "description": "Build and maintain data pipelines that power our analytics and ML systems. Requirements: 2+ years experience with Python and SQL. Experience with Apache Spark, Airflow, or similar. Proficiency with cloud data services (BigQuery, Redshift). Understanding of data modeling and ETL. Experience with streaming data (Kafka, Kinesis)."
    },
    {
        "title": "Cloud Solutions Architect",
        "job_type": "Full-time",
        "salary_range": "$160k-230k/yr",
        "description": "Design cloud-native architectures for enterprise customers. Requirements: 5+ years cloud architecture experience. AWS/GCP/Azure certifications preferred. Experience with serverless, containers, and microservices. Strong communication and client-facing skills. Experience with cost optimization strategies."
    },
]


def generate_seed_jobs():
    """Generate a list of job dicts ready for DB insertion."""
    jobs = []
    now = datetime.utcnow()

    for company in COMPANIES:
        # Each company gets 3-4 random job templates
        templates = random.sample(JOB_TEMPLATES, min(random.randint(3, 4), len(JOB_TEMPLATES)))
        for tmpl in templates:
            location = random.choice(company["locations"])
            days_ago = random.randint(0, 30)
            jobs.append({
                "id": str(uuid.uuid4()),
                "source": "seed",
                "external_id": f"seed-{uuid.uuid4().hex[:8]}",
                "title": tmpl["title"],
                "description": f"{tmpl['description']}\n\nAbout {company['name']}: We're looking for talented individuals to join our team at {company['name']}. This role is based in {location}.",
                "location": location,
                "company_name": company["name"],
                "apply_url": company["career_url"],
                "salary_range": tmpl["salary_range"],
                "job_type": tmpl["job_type"],
                "posted_at": (now - timedelta(days=days_ago)).isoformat(),
            })

    return jobs
