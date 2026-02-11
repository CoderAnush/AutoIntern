"""Generic Job Spider

This spider works with ANY site configured in sites_config.yaml.
It reads configuration dynamically and adapts to each site's structure.

Supports:
- Company career pages (Google, Microsoft, Meta, Apple, Amazon, Netflix, etc.)
- Indian IT companies (TCS, Infosys, Wipro)
- Tech job boards (GitHub Jobs, Stack Overflow, HackerRank, LeetCode, etc.)
- Startup job boards (Y Combinator)
- Niche boards (Dribbble for design, ProductManagerHQ for PM)

Usage:
    scrapy crawl google_careers
    scrapy crawl meta_careers
    scrapy crawl github_jobs
    ... or any site in sites_config.yaml
"""

from autointern_scraper.spiders.base_spider import BaseJobSpider
from scrapy import Request
import json


class GenericJobSpider(BaseJobSpider):
    """
    Generic spider that works for ANY site defined in sites_config.yaml

    No code changes needed - just add your site to YAML config:

    Example:
        mycompany_careers:
          name: "My Company"
          base_url: "https://mycompany.com/careers"
          selectors:
            job_item: "div.job-card"
            job_title: "h2.title"
            company: "span.company"
            location: "span.location"
    """

    # These will be set dynamically by the caller
    name = None
    site_name = None

    def __init__(self, site_name=None, *args, **kwargs):
        """Initialize with dynamic site name."""
        if site_name:
            self.site_name = site_name
            self.name = site_name

        super().__init__(*args, **kwargs)

        self.logger.info(f"Generic spider initialized for: {self.site_name}")
        self.logger.info(f"  URL: {self.site_config.get('base_url', 'N/A')}")
        self.logger.info(f"  Company: {self.site_config.get('company', 'All')}")

    def start_requests(self):
        """Generate start requests based on config."""
        base_url = self.site_config.get('base_url', '')

        # For sites with search queries
        search_queries = self.site_config.get('search_queries', [])
        if search_queries:
            for query in search_queries:
                url = f"{base_url}?q={query}" if '?' not in base_url else f"{base_url}&q={query}"
                self.logger.info(f"Starting search for: {query}")

                yield Request(
                    url=url,
                    callback=self.parse,
                    meta={'query': query, 'page': 0},
                    headers=self._get_random_headers()
                )
        else:
            # Direct URL without search
            self.logger.info("Starting direct crawl")

            yield Request(
                url=base_url,
                callback=self.parse,
                meta={'page': 0},
                headers=self._get_random_headers()
            )

    def parse(self, response):
        """Parse job listings using config selectors."""
        self.logger.info(f"Parsing {response.url}")

        selectors = self.site_config.get('selectors', {})
        job_selector = selectors.get('job_item', '')

        if not job_selector:
            self.logger.warning(f"No job_item selector configured for {self.site_name}")
            return

        job_items = response.css(job_selector)
        self.logger.info(f"Found {len(job_items)} potential jobs")

        for job_elem in job_items:
            try:
                job_data = self._extract_job(job_elem, response)
                if job_data:
                    self.jobs_scraped += 1
                    self._push_to_queue(job_data)
            except Exception as e:
                self.logger.warning(f"Failed to extract job: {e}")
                self.errors.append(str(e))

        # Handle pagination
        self._handle_pagination(response)

    def _extract_job(self, job_elem, response):
        """Extract job from element using config selectors."""
        selectors = self.site_config.get('selectors', {})

        try:
            title = job_elem.css(selectors.get('job_title', 'h2')).css('::text').get('').strip()
            company = job_elem.css(selectors.get('company', '.company')).css('::text').get('').strip()
            location = job_elem.css(selectors.get('location', '.location')).css('::text').get('').strip()
            job_url = job_elem.css(selectors.get('job_url', 'a')).css('::attr(href)').get('')

            # If company not found in listing, use config default
            if not company:
                company = self.site_config.get('company', '')

            job_data = {
                'title': title,
                'company': company,
                'location': location or 'Not specified',
                'description': job_elem.css(selectors.get('job_summary', '.description')).css('::text').get('').strip(),
                'url': response.urljoin(job_url) if job_url else '',
                'salary_min': None,
                'salary_max': None,
                'job_type': 'full-time',
                'source': self.site_name,
                'source_url': response.url,
                'scraped_at': response.meta.get('download_timestamp', ''),
            }

            # Parse salary if present
            salary_text = job_elem.css(selectors.get('salary', '.salary')).css('::text').get('')
            if salary_text:
                job_data['salary_min'], job_data['salary_max'] = self._parse_salary(salary_text)

            # Detect job type
            job_data['job_type'] = self._detect_job_type(job_data['title'] + ' ' + job_data['description'])

            # Skip jobs missing critical fields
            if not job_data['title'] or not job_data['company']:
                return None

            return job_data

        except Exception as e:
            self.logger.error(f"Error extracting job: {e}")
            return None

    def _parse_salary(self, salary_text):
        """Parse salary range from text."""
        import re

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

    def _handle_pagination(self, response):
        """Follow pagination based on config strategy."""
        pagination_config = self.site_config.get('pagination', {})
        strategy = pagination_config.get('strategy', 'none')

        if strategy == 'none':
            return  # No pagination

        page = response.meta.get('page', 0)
        max_pages = pagination_config.get('max_pages', 5)

        if page >= max_pages:
            return

        query = response.meta.get('query', '')
        base_url = self.site_config.get('base_url', '')

        if strategy == 'offset':
            param_name = pagination_config.get('param_name', 'start')
            increment = pagination_config.get('increment', 10)
            next_offset = (page + 1) * increment

            next_url = f"{base_url}?{param_name}={next_offset}"
            if query:
                next_url += f"&q={query}"

        elif strategy == 'page':
            param_name = pagination_config.get('param_name', 'page')
            next_page = page + 1

            next_url = f"{base_url}?{param_name}={next_page}"
            if query:
                next_url += f"&q={query}"

        else:
            return

        self.logger.info(f"Following to page {page + 1}: {next_url}")

        yield response.follow(
            next_url,
            callback=self.parse,
            meta={'query': query, 'page': page + 1},
            headers=self._get_random_headers()
        )


# ===== INDIVIDUAL SPIDER CLASSES (inherit from generic) =====
# Each one is just 5 lines - they set the site_name and that's it!

class GoogleCareersSpider(GenericJobSpider):
    name = 'google_careers'
    site_name = 'google_careers'


class MicrosoftCareersSpider(GenericJobSpider):
    name = 'microsoft_careers'
    site_name = 'microsoft_careers'


class MetaCareersSpider(GenericJobSpider):
    name = 'meta_careers'
    site_name = 'meta_careers'


class AmazonCareersSpider(GenericJobSpider):
    name = 'amazon_careers'
    site_name = 'amazon_careers'


class AppleCareersSpider(GenericJobSpider):
    name = 'apple_careers'
    site_name = 'apple_careers'


class NetflixCareersSpider(GenericJobSpider):
    name = 'netflix_careers'
    site_name = 'netflix_careers'


class TCSCareersSpider(GenericJobSpider):
    name = 'tcs_careers'
    site_name = 'tcs_careers'


class InfosysCareersSpider(GenericJobSpider):
    name = 'infosys_careers'
    site_name = 'infosys_careers'


class WiproCareersSpider(GenericJobSpider):
    name = 'wipro_careers'
    site_name = 'wipro_careers'


class GitHubJobsSpider(GenericJobSpider):
    name = 'github_jobs'
    site_name = 'github_jobs'


class StackOverflowJobsSpider(GenericJobSpider):
    name = 'stackoverflow_jobs'
    site_name = 'stackoverflow_jobs'


class HackerRankJobsSpider(GenericJobSpider):
    name = 'hackerrank_jobs'
    site_name = 'hackerrank_jobs'


class LeetCodeDiscussSpider(GenericJobSpider):
    name = 'leetcode_discuss'
    site_name = 'leetcode_discuss'


class YCombinatorJobsSpider(GenericJobSpider):
    name = 'ycombinator_jobs'
    site_name = 'ycombinator_jobs'


class ProductManagerHQSpider(GenericJobSpider):
    name = 'productmanagerhq'
    site_name = 'productmanagerhq'


class DribbbleJobsSpider(GenericJobSpider):
    name = 'dribbble_jobs'
    site_name = 'dribbble_jobs'


# ===== TIER 1: INDIAN JOB PORTALS =====

class NaukriSpider(GenericJobSpider):
    name = 'naukri'
    site_name = 'naukri'


class MonsterIndiaSpider(GenericJobSpider):
    name = 'monster_india'
    site_name = 'monster_india'


class FreshersworldSpider(GenericJobSpider):
    name = 'freshersworld'
    site_name = 'freshersworld'


class TimesJobsSpider(GenericJobSpider):
    name = 'timesjobs'
    site_name = 'timesjobs'


class FounditSpider(GenericJobSpider):
    name = 'foundit'
    site_name = 'foundit'


class ShineSpider(GenericJobSpider):
    name = 'shine'
    site_name = 'shine'


class HirectSpider(GenericJobSpider):
    name = 'hirect'
    site_name = 'hirect'


class CutshortSpider(GenericJobSpider):
    name = 'cutshort'
    site_name = 'cutshort'


# ===== TIER 2: REMOTE & TECH-FOCUSED =====

class FlexJobsSpider(GenericJobSpider):
    name = 'flexjobs'
    site_name = 'flexjobs'


class HackerEarthSpider(GenericJobSpider):
    name = 'hackerearth'
    site_name = 'hackerearth'


class AngelListTalentSpider(GenericJobSpider):
    name = 'angellist_talent'
    site_name = 'angellist_talent'


class TuringSpider(GenericJobSpider):
    name = 'turing'
    site_name = 'turing'


class ArcDevSpider(GenericJobSpider):
    name = 'arcdev'
    site_name = 'arcdev'


class RemotiveSpider(GenericJobSpider):
    name = 'remotive'
    site_name = 'remotive'


class JobspressoSpider(GenericJobSpider):
    name = 'jobspresso'
    site_name = 'jobspresso'


# ===== TIER 4: ADDITIONAL TECH COMPANIES =====

class NVIDIACareersSpider(GenericJobSpider):
    name = 'nvidia_careers'
    site_name = 'nvidia_careers'


class FlipkartCareersSpider(GenericJobSpider):
    name = 'flipkart_careers'
    site_name = 'flipkart_careers'


class SwiggyCareersSpider(GenericJobSpider):
    name = 'swiggy_careers'
    site_name = 'swiggy_careers'


class ZohoCareersSpider(GenericJobSpider):
    name = 'zoho_careers'
    site_name = 'zoho_careers'


class FreshworksCareersSpider(GenericJobSpider):
    name = 'freshworks_careers'
    site_name = 'freshworks_careers'


class RazorpayCareersSpider(GenericJobSpider):
    name = 'razorpay_careers'
    site_name = 'razorpay_careers'


# ===== TIER 5: DATA & ANALYTICS COMPANIES =====

class MuSigmaSpider(GenericJobSpider):
    name = 'mu_sigma'
    site_name = 'mu_sigma'


class FractalAnalyticsSpider(GenericJobSpider):
    name = 'fractal_analytics'
    site_name = 'fractal_analytics'


class TigerAnalyticsSpider(GenericJobSpider):
    name = 'tiger_analytics'
    site_name = 'tiger_analytics'


class LatentViewSpider(GenericJobSpider):
    name = 'latentview'
    site_name = 'latentview'


class ZSAssociatesSpider(GenericJobSpider):
    name = 'zs_associates'
    site_name = 'zs_associates'


class TredenceSpider(GenericJobSpider):
    name = 'tredence'
    site_name = 'tredence'


class Course5IntelligenceSpider(GenericJobSpider):
    name = 'course5_intelligence'
    site_name = 'course5_intelligence'


class DatabricksSpider(GenericJobSpider):
    name = 'databricks'
    site_name = 'databricks'


class SnowflakeSpider(GenericJobSpider):
    name = 'snowflake'
    site_name = 'snowflake'


class PalantirSpider(GenericJobSpider):
    name = 'palantir'
    site_name = 'palantir'
