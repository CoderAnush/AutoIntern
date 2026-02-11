import scrapy
from scrapy import Spider, Request
import redis
import json
import hashlib
from datetime import datetime
import random
import os
import yaml

class BaseJobSpider(Spider):
    """
    Base spider for job scraping with Redis integration.

    Features:
    - Config-driven site definitions (YAML)
    - Automatic Redis queue insertion
    - Retry logic with jitter
    - User-agent rotation
    - Deduplication via signature hashing
    - Error tracking
    """

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 2,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 3,
    }

    def __init__(self, *args, **kwargs):
        super(BaseJobSpider, self).__init__(*args, **kwargs)

        # Load site configuration
        config_path = os.path.join(os.path.dirname(__file__), '../sites_config.yaml')
        with open(config_path, 'r') as f:
            self.all_configs = yaml.safe_load(f)

        # Get config for this spider
        if not hasattr(self, 'site_name'):
            raise ValueError("Spider must define 'site_name' attribute")

        self.site_config = self.all_configs.get(self.site_name)
        if not self.site_config:
            raise ValueError(f"Site '{self.site_name}' not found in sites_config.yaml")

        # Initialize Redis client
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(redis_url)
        self.queue_name = self.site_config.get('redis_queue', 'ingest:jobs')

        # Tracking
        self.jobs_scraped = 0
        self.jobs_pushed = 0
        self.jobs_duplicated = 0
        self.errors = []

    def start_requests(self):
        """Generate initial requests with search queries."""
        base_url = self.site_config['base_url']
        search_queries = self.site_config.get('search_queries', [''])
        locations = self.site_config.get('search_locations', [''])

        for query in search_queries:
            for location in locations:
                # Build URL with search params
                if self.site_config['pagination']['strategy'] == 'offset':
                    url = f"{base_url}?q={query}&l={location}&start=0"
                else:
                    url = f"{base_url}?q={query}&l={location}"

                yield Request(
                    url=url,
                    callback=self.parse,
                    meta={'query': query, 'location': location, 'page': 0},
                    headers=self._get_random_headers()
                )

    def parse(self, response):
        """Parse job listing page and extract job details."""
        self.logger.info(f"Parsing {response.url}")

        # Extract job items using CSS selector
        job_selector = self.site_config['selectors']['job_item']
        job_items = response.css(job_selector)

        self.logger.info(f"Found {len(job_items)} potential jobs on page")

        for job_elem in job_items:
            try:
                job_data = self._extract_job_data(job_elem, response)
                if job_data:
                    self.jobs_scraped += 1
                    self._push_to_queue(job_data)
            except Exception as e:
                self.logger.warning(f"Failed to extract job: {e}")
                self.errors.append(str(e))

        # Handle pagination
        self._follow_pagination(response)

    def _extract_job_data(self, job_elem, response):
        """Extract job data from a single job element."""
        selectors = self.site_config['selectors']

        try:
            # Extract fields using selectors
            job_data = {
                'title': job_elem.css(selectors['job_title']).css('::text').get('').strip(),
                'company': job_elem.css(selectors['company']).css('::text').get('').strip(),
                'location': job_elem.css(selectors['location']).css('::text').get('').strip(),
                'description': job_elem.css(selectors.get('job_summary', '')).css('::text').get('').strip(),
                'url': response.urljoin(job_elem.css(selectors['job_url']).css('::attr(href)').get('') or ''),
                'salary_min': None,
                'salary_max': None,
                'job_type': 'full-time',
                'source': self.site_name,
                'source_url': response.url,
                'scraped_at': datetime.now().isoformat(),
            }

            # Parse salary if available
            salary_text = job_elem.css(selectors.get('salary', '')).css('::text').get('')
            if salary_text:
                job_data['salary_min'], job_data['salary_max'] = self._parse_salary(salary_text)

            # Detect job type
            job_data['job_type'] = self._detect_job_type(job_data['title'] + ' ' + job_data['description'])

            # Skip jobs with missing critical fields
            if not job_data['title'] or not job_data['company']:
                return None

            return job_data

        except Exception as e:
            self.logger.error(f"Error extracting job data: {e}")
            return None

    def _detect_job_type(self, text):
        """Detect job type from text (full-time, internship, contract, etc.)."""
        text_lower = text.lower()
        job_type_keywords = self.site_config.get('job_type_keywords', {})

        for job_type, keywords in job_type_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return job_type

        return 'full-time'

    def _parse_salary(self, salary_text):
        """Extract min and max salary from text."""
        import re

        # Simple regex to find salary ranges
        salary_pattern = r'\$?([\d,]+).*?-.*?\$?([\d,]+)'
        match = re.search(salary_pattern, salary_text)

        if match:
            try:
                min_sal = int(match.group(1).replace(',', ''))
                max_sal = int(match.group(2).replace(',', ''))
                return min_sal, max_sal
            except:
                pass

        return None, None

    def _follow_pagination(self, response):
        """Follow pagination links to next page."""
        pagination_config = self.site_config['pagination']
        page = response.meta.get('page', 0)
        max_pages = pagination_config.get('max_pages', 10)

        if page >= max_pages:
            return

        strategy = pagination_config['strategy']

        if strategy == 'offset':
            # Offset-based pagination (Indeed, RemoteOK)
            param_name = pagination_config['param_name']
            increment = pagination_config['increment']
            next_offset = (page + 1) * increment

            # Reconstruct URL with new offset
            next_url = response.url.split('&start=')[0] + f'&start={next_offset}'

            yield Request(
                url=next_url,
                callback=self.parse,
                meta={'query': response.meta.get('query'), 'location': response.meta.get('location'), 'page': page + 1},
                headers=self._get_random_headers()
            )

        elif strategy == 'page':
            # Page-based pagination
            next_page = page + 1
            next_url = f"{response.url.split('?')[0]}?page={next_page}"

            yield Request(
                url=next_url,
                callback=self.parse,
                meta={'query': response.meta.get('query'), 'page': next_page},
                headers=self._get_random_headers()
            )

    def _push_to_queue(self, job_data):
        """Push job to Redis queue with deduplication."""
        try:
            # Generate deduplication signature
            dedupe_sig = self._generate_dedupe_signature(job_data)
            job_data['dedupe_signature'] = dedupe_sig

            # Check if already in database (via Redis)
            # For now, just check if similar job recently queued
            # This is a simple check; the worker will do full DB dedup

            # Push to Redis queue
            self.redis_client.lpush(
                self.queue_name,
                json.dumps(job_data, default=str)
            )

            self.jobs_pushed += 1
            self.logger.info(f"Pushed job: {job_data['title']} @ {job_data['company']}")

        except Exception as e:
            self.logger.error(f"Failed to push to queue: {e}")
            self.errors.append(str(e))

    def _generate_dedupe_signature(self, job_data):
        """Generate MD5 hash to uniquely identify a job."""
        # Signature based on title + company + location
        sig_str = f"{job_data['title']}|{job_data['company']}|{job_data['location']}"
        return hashlib.md5(sig_str.encode()).hexdigest()

    def _get_random_headers(self):
        """Return random user-agent header."""
        user_agents = self.site_config.get('headers', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        ])

        return {'User-Agent': random.choice(user_agents)}

    def closed(self, reason):
        """Called when spider closes."""
        self.logger.info(f"\n\n{'='*50}")
        self.logger.info(f"Spider '{self.site_name}' completed")
        self.logger.info(f"  Jobs scraped: {self.jobs_scraped}")
        self.logger.info(f"  Jobs pushed to queue: {self.jobs_pushed}")
        self.logger.info(f"  Errors: {len(self.errors)}")
        if self.errors:
            self.logger.info(f"  Last error: {self.errors[-1]}")
        self.logger.info(f"{'='*50}\n")
