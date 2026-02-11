"""WeWorkRemotely Job Spider

This spider scrapes job listings from WeWorkRemotely.com.

WeWorkRemotely provides:
- 50k+ remote job listings
- Tech-focused (engineering, product, design, marketing)
- Premium job board (curated listings)
- Global remote work opportunities
- Startup + enterprise jobs

Usage:
    scrapy crawl weworkremotely

Note: WeWorkRemotely uses HTML with API fallback.
"""

from autointern_scraper.spiders.base_spider import BaseJobSpider
from scrapy import Request
import json


class WeworkremotellySpider(BaseJobSpider):
    """
    Spider for scraping jobs from WeWorkRemotely.com

    WeWorkRemotely provides:
    - Premium remote job listings
    - Tech-focused roles
    - Curated employer list
    - High-quality applications from candidates

    Uses HTML parsing with category-based crawling.
    """

    name = 'weworkremotely'
    site_name = 'weworkremotely'
    allowed_domains = ['weworkremotely.com']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info(f"Initializing {self.name} spider")
        self.logger.info(f"  Base URL: {self.site_config['base_url']}")
        self.logger.info(f"  Search queries: {len(self.site_config.get('search_queries', []))}")

    def start_requests(self):
        """Generate requests for different job categories."""
        base_url = self.site_config['base_url']
        search_queries = self.site_config.get('search_queries', ['engineering'])

        for query in search_queries:
            # WeWorkRemotely uses category URLs
            # Examples: /engineering, /product, /design, /marketing
            url = f"{base_url}?category={query}"

            self.logger.info(f"Starting search for category: {query}")

            yield Request(
                url=url,
                callback=self.parse,
                meta={'category': query, 'page': 1},
                headers=self._get_random_headers()
            )

    def parse(self, response):
        """Parse WeWorkRemotely job listings."""
        self.logger.info(f"Parsing WeWorkRemotely for category: {response.meta.get('category')}")

        # Extract job items
        job_selector = self.site_config['selectors'].get('job_item', 'div.job-listing')

        if not job_selector:
            # Fallback selectors for WeWorkRemotely
            job_items = response.css('div[class*="job"]')
        else:
            job_items = response.css(job_selector)

        self.logger.info(f"Found {len(job_items)} potential jobs")

        for job_elem in job_items:
            try:
                job_data = self._extract_job_data_weworkremotely(job_elem, response)
                if job_data:
                    self.jobs_scraped += 1
                    self._push_to_queue(job_data)
            except Exception as e:
                self.logger.warning(f"Failed to extract job: {e}")
                self.errors.append(str(e))

        # Follow pagination
        self._follow_pagination_weworkremotely(response)

    def _extract_job_data_weworkremotely(self, job_elem, response):
        """Extract job from WeWorkRemotely listing element."""
        selectors = self.site_config['selectors']

        try:
            job_data = {
                'title': job_elem.css(selectors.get('job_title', 'h2')).css('::text').get('').strip(),
                'company': job_elem.css(selectors.get('company', '.company-name')).css('::text').get('').strip(),
                'location': job_elem.css(selectors.get('location', '.location')).css('::text').get('Remote').strip(),
                'description': job_elem.css(selectors.get('job_summary', '.job-description')).css('::text').get('').strip(),
                'url': response.urljoin(job_elem.css(selectors.get('job_url', 'a')).css('::attr(href)').get('') or ''),
                'salary_min': None,
                'salary_max': None,
                'job_type': selectors.get('job_type', 'full-time'),
                'source': self.site_name,
                'source_url': response.url,
                'scraped_at': response.meta.get('download_timestamp', ''),
            }

            # WeWorkRemotely is remote-focused
            if not job_data['location'] or 'remote' not in job_data['location'].lower():
                job_data['location'] = 'Remote'

            # Parse salary if available
            salary_text = job_elem.css(selectors.get('salary', '.salary')).css('::text').get('')
            if salary_text:
                job_data['salary_min'], job_data['salary_max'] = self._parse_salary(salary_text)

            # Detect job type
            job_data['job_type'] = self._detect_job_type(
                job_data['title'] + ' ' + job_data['description']
            )

            # Skip jobs with missing critical fields
            if not job_data['title'] or not job_data['company']:
                return None

            return job_data

        except Exception as e:
            self.logger.error(f"Error extracting WeWorkRemotely job data: {e}")
            return None

    def _follow_pagination_weworkremotely(self, response):
        """Handle pagination for WeWorkRemotely."""
        pagination_config = self.site_config['pagination']
        page = response.meta.get('page', 1)
        max_pages = pagination_config.get('max_pages', 5)

        if page >= max_pages:
            return

        category = response.meta.get('category', 'engineering')
        next_page = page + 1
        base_url = self.site_config['base_url']

        # Build next page URL
        next_url = f"{base_url}?category={category}&page={next_page}"

        self.logger.info(f"Following to page {next_page}")

        yield response.follow(
            next_url,
            callback=self.parse,
            meta={'category': category, 'page': next_page},
            headers=self._get_random_headers()
        )

    def _parse_salary(self, salary_text):
        """Parse salary range from WeWorkRemotely format."""
        import re

        # Format: "$80,000 - $150,000"
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
