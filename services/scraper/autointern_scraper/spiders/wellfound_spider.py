"""Wellfound Job Spider

This spider scrapes job listings from Wellfound.com (formerly AngelList).

Wellfound provides:
- 50k+ startup job listings
- Global coverage (US, Europe, Asia, etc.)
- Startup equity + salary info
- Internship focus
- Job levels: Junior, Mid, Senior

Usage:
    scrapy crawl wellfound

Note: Wellfound uses an API, not HTML scraping.
URL format: https://wellfound.com/api/v3/jobs?q=software%20engineer&page=1
"""

from autointern_scraper.spiders.base_spider import BaseJobSpider
from scrapy import Request
import json


class WellfoundSpider(BaseJobSpider):
    """
    Spider for scraping jobs from Wellfound (AngelList)

    Wellfound provides:
    - Early-stage startup jobs
    - Equity compensation
    - Remote-friendly positions
    - Internship opportunities

    Uses API endpoint instead of HTML scraping for reliability.
    """

    name = 'wellfound'
    site_name = 'wellfound'
    allowed_domains = ['wellfound.com']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info(f"Initializing {self.name} spider")
        self.logger.info(f"  API Endpoint: {self.site_config['base_url']}")
        self.logger.info(f"  Search queries: {len(self.site_config.get('search_queries', []))}")
        self.logger.info(f"  Max pages: {self.site_config['pagination'].get('max_pages', 10)}")

    def start_requests(self):
        """Generate API requests for job search."""
        base_url = self.site_config['base_url']
        search_queries = self.site_config.get('search_queries', ['software engineer'])

        for query in search_queries:
            # Wellfound API uses pagination with page numbers
            url = f"{base_url}?q={query}&page=1"

            self.logger.info(f"Starting search for: {query}")

            yield Request(
                url=url,
                callback=self.parse,
                meta={'query': query, 'page': 1},
                headers=self._get_random_headers()
            )

    def parse(self, response):
        """Parse JSON API response."""
        self.logger.info(f"Parsing Wellfound response for page {response.meta.get('page')}")

        try:
            # Wellfound returns JSON
            data = json.loads(response.text)

            # Extract jobs from API response
            jobs = data.get('jobs', [])
            self.logger.info(f"Found {len(jobs)} jobs in page")

            for job in jobs:
                try:
                    job_data = self._extract_job_from_api(job, response)
                    if job_data:
                        self.jobs_scraped += 1
                        self._push_to_queue(job_data)
                except Exception as e:
                    self.logger.warning(f"Failed to extract API job: {e}")
                    self.errors.append(str(e))

            # Handle pagination
            self._follow_api_pagination(response, data)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.errors.append(f"JSON decode error: {str(e)}")

    def _extract_job_from_api(self, job, response):
        """Extract job data from JSON API response."""
        try:
            job_data = {
                'title': job.get('title', '').strip(),
                'company': job.get('startup_name', job.get('company', '')).strip(),
                'location': job.get('location', '').strip(),
                'description': job.get('description', '').strip(),
                'url': job.get('url', ''),
                'salary_min': self._parse_salary_min(job.get('salary_min')),
                'salary_max': self._parse_salary_max(job.get('salary_max')),
                'job_type': self._detect_job_type_from_level(job.get('level', 'Mid')),
                'source': self.site_name,
                'source_url': response.url,
                'scraped_at': response.meta.get('download_timestamp', ''),
            }

            # Add equity info if available
            equity = job.get('equity')
            if equity:
                job_data['equity_percentage'] = equity

            # Skip if missing critical fields
            if not job_data['title'] or not job_data['company']:
                return None

            return job_data

        except Exception as e:
            self.logger.error(f"Error extracting API job data: {e}")
            return None

    def _parse_salary_min(self, salary):
        """Convert salary to integer."""
        if not salary:
            return None
        try:
            return int(salary) if salary else None
        except:
            return None

    def _parse_salary_max(self, salary):
        """Convert salary to integer."""
        if not salary:
            return None
        try:
            return int(salary) if salary else None
        except:
            return None

    def _detect_job_type_from_level(self, level):
        """Map Wellfound job level to job type."""
        level_lower = (level or '').lower()

        if 'intern' in level_lower:
            return 'internship'
        elif 'contract' in level_lower:
            return 'contract'
        elif 'part' in level_lower:
            return 'part_time'

        return 'full-time'

    def _follow_api_pagination(self, response, data):
        """Follow pagination in API responses."""
        pagination_config = self.site_config['pagination']
        page = response.meta.get('page', 1)
        max_pages = pagination_config.get('max_pages', 20)

        if page >= max_pages:
            self.logger.info(f"Reached max pages ({max_pages})")
            return

        # Check if there are more results
        has_more = data.get('has_more', False)
        if not has_more:
            self.logger.info("No more pages available")
            return

        # Build next page URL
        query = response.meta.get('query', 'software engineer')
        next_page = page + 1
        base_url = self.site_config['base_url']
        next_url = f"{base_url}?q={query}&page={next_page}"

        self.logger.info(f"Following to page {next_page}")

        yield response.follow(
            next_url,
            callback=self.parse,
            meta={'query': query, 'page': next_page},
            headers=self._get_random_headers()
        )
