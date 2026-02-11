"""RemoteOK Job Spider

This spider scrapes job listings from RemoteOK.io.

RemoteOK provides:
- 10k+ remote job listings
- Global coverage
- Startup + enterprise jobs
- Premium remote-only focus
- Fast updates

Usage:
    scrapy crawl remoteok

Note: RemoteOK uses HTML, not API.
"""

from autointern_scraper.spiders.base_spider import BaseJobSpider
from scrapy import Request


class RemoteOkSpider(BaseJobSpider):
    """
    Spider for scraping jobs from RemoteOK.io

    RemoteOK provides:
    - Remote-only job listings
    - High quality positions
    - Mix of startups & enterprises
    - Global teams

    Configuration is loaded from sites_config.yaml.
    """

    name = 'remoteok'
    site_name = 'remoteok'
    allowed_domains = ['remoteok.io']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info(f"Initializing {self.name} spider")
        self.logger.info(f"  Base URL: {self.site_config['base_url']}")

    def start_requests(self):
        """Generate start requests for RemoteOK search."""
        # RemoteOK doesn't have traditional search - we scrape the main jobs page
        base_url = self.site_config['base_url']

        self.logger.info("Starting RemoteOK crawl")

        yield Request(
            url=base_url,
            callback=self.parse,
            meta={'page': 1},
            headers=self._get_random_headers()
        )

    def parse(self, response):
        """Parse RemoteOK job listings."""
        self.logger.info(f"Parsing RemoteOK main page")

        # RemoteOK uses JavaScript to load jobs, so we parse the HTML for available jobs
        # Extract job items using selector from config
        job_selector = self.site_config['selectors']['job_item']

        if not job_selector or job_selector == "":
            # Fallback: if selector not in config, try common RemoteOK selectors
            job_items = response.css('tr.job')
            if not job_items:
                job_items = response.css('div.job-container')
            if not job_items:
                job_items = response.css('[data-job-id]')
        else:
            job_items = response.css(job_selector)

        self.logger.info(f"Found {len(job_items)} potential jobs")

        for job_elem in job_items:
            try:
                job_data = self._extract_job_data_remoteok(job_elem, response)
                if job_data:
                    self.jobs_scraped += 1
                    self._push_to_queue(job_data)
            except Exception as e:
                self.logger.warning(f"Failed to extract job: {e}")
                self.errors.append(str(e))

    def _extract_job_data_remoteok(self, job_elem, response):
        """Extract job from RemoteOK job element."""
        selectors = self.site_config['selectors']

        try:
            job_data = {
                'title': job_elem.css(selectors.get('job_title', 'h2')).css('::text').get('').strip(),
                'company': job_elem.css(selectors.get('company', '.company')).css('::text').get('').strip(),
                'location': job_elem.css(selectors.get('location', '.location')).css('::text').get('Remote').strip(),
                'description': job_elem.css(selectors.get('job_summary', '.description')).css('::text').get('').strip(),
                'url': response.urljoin(job_elem.css(selectors.get('job_url', 'a')).css('::attr(href)').get('') or ''),
                'salary_min': None,
                'salary_max': None,
                'job_type': 'full-time',
                'source': self.site_name,
                'source_url': response.url,
                'scraped_at': response.meta.get('download_timestamp', ''),
            }

            # RemoteOK focuses on remote, so default location
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
            self.logger.error(f"Error extracting RemoteOK job data: {e}")
            return None

    def _parse_salary(self, salary_text):
        """Parse salary range from RemoteOK format."""
        import re

        # RemoteOK uses formats like: "$80k - $150k"
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
