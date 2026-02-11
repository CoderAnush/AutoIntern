"""
Unit tests for Indeed spider

Tests the parsing logic against sample HTML fixture.
Does NOT make real HTTP requests.
"""

import unittest
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from scrapy.http import HtmlResponse
from scrapy.selector import Selector
from autointern_scraper.spiders.indeed_spider import IndeedSpider


class TestIndeedSpider(unittest.TestCase):
    """Test Indeed spider with fixture HTML."""

    def setUp(self):
        """Set up test fixtures."""
        # Load sample HTML
        fixture_path = Path(__file__).parent / 'fixtures' / 'indeed_sample.html'
        with open(fixture_path, 'r') as f:
            self.html_content = f.read()

        # Mock Redis
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        # Mock YAML load
        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        # Create minimal spider config
        self.spider_config = {
            'indeed': {
                'name': 'Indeed',
                'base_url': 'https://www.indeed.com/jobs',
                'pagination': {
                    'strategy': 'offset',
                    'param_name': 'start',
                    'increment': 10,
                    'max_pages': 50
                },
                'selectors': {
                    'job_item': "div[data-testid='result']",
                    'job_title': 'h2.jobTitle span',
                    'company': "span[data-testid='company-name']",
                    'location': "div[data-testid='job-location']",
                    'job_url': 'a.jcs-JobTitle',
                    'salary': "span[data-testid='salaryLineItem']",
                    'job_summary': 'div.job-snippet'
                },
                'job_type_keywords': {
                    'full_time': ['full-time', 'full time'],
                    'internship': ['internship', 'intern'],
                    'contract': ['contract', 'freelance']
                },
                'redis_queue': 'ingest:jobs'
            }
        }

        self.mock_yaml.safe_load.return_value = self.spider_config

        # Create spider instance
        self.spider = IndeedSpider()

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_spider_initialization(self):
        """Test spider initializes correctly."""
        self.assertEqual(self.spider.name, 'indeed')
        self.assertEqual(self.spider.site_name, 'indeed')
        self.assertIsNotNone(self.spider.site_config)

    def test_parse_extracts_correct_number_of_jobs(self):
        """Test that spider extracts all jobs from sample HTML."""
        # Create mock response
        response = HtmlResponse(
            url='https://www.indeed.com/jobs?q=software+engineer&l=Remote&start=0',
            body=self.html_content.encode('utf-8')
        )

        # Mock pagination to not follow
        with patch.object(self.spider, '_follow_pagination'):
            self.spider.parse(response)

        # Check that 4 jobs were scraped from fixture
        self.assertEqual(self.spider.jobs_scraped, 4)

    def test_job_extraction_fields(self):
        """Test that extracted job has all required fields."""
        response = HtmlResponse(
            url='https://www.indeed.com/jobs?q=software+engineer',
            body=self.html_content.encode('utf-8')
        )

        # Extract first job item
        selector = Selector(text=self.html_content)
        job_items = selector.css("div[data-testid='result']")
        first_job = job_items[0]

        # Extract job data
        job_data = self.spider._extract_job_data(first_job, response)

        # Verify required fields
        self.assertIsNotNone(job_data)
        self.assertIn('title', job_data)
        self.assertIn('company', job_data)
        self.assertIn('location', job_data)
        self.assertIn('url', job_data)
        self.assertIn('source', job_data)
        self.assertIn('scraped_at', job_data)
        self.assertEqual(job_data['source'], 'indeed')

    def test_job_title_extraction(self):
        """Test that job title is correctly extracted."""
        response = HtmlResponse(
            url='https://www.indeed.com/jobs',
            body=self.html_content.encode('utf-8')
        )

        selector = Selector(text=self.html_content)
        job_items = selector.css("div[data-testid='result']")

        # Test first job
        job_data = self.spider._extract_job_data(job_items[0], response)
        self.assertEqual(job_data['title'], 'Software Engineer')

        # Test second job
        job_data = self.spider._extract_job_data(job_items[1], response)
        self.assertEqual(job_data['title'], 'Full Stack Developer')

    def test_company_extraction(self):
        """Test that company name is correctly extracted."""
        response = HtmlResponse(
            url='https://www.indeed.com/jobs',
            body=self.html_content.encode('utf-8')
        )

        selector = Selector(text=self.html_content)
        job_items = selector.css("div[data-testid='result']")

        self.assertEqual(
            self.spider._extract_job_data(job_items[0], response)['company'],
            'Google'
        )
        self.assertEqual(
            self.spider._extract_job_data(job_items[1], response)['company'],
            'Facebook'
        )

    def test_location_extraction(self):
        """Test that location is correctly extracted."""
        response = HtmlResponse(
            url='https://www.indeed.com/jobs',
            body=self.html_content.encode('utf-8')
        )

        selector = Selector(text=self.html_content)
        job_items = selector.css("div[data-testid='result']")

        self.assertEqual(
            self.spider._extract_job_data(job_items[0], response)['location'],
            'San Francisco, CA'
        )
        self.assertEqual(
            self.spider._extract_job_data(job_items[1], response)['location'],
            'Remote'
        )

    def test_salary_parsing(self):
        """Test that salary range is correctly parsed."""
        # Test valid salary
        min_sal, max_sal = self.spider._parse_salary('$150,000 - $200,000 a year')
        self.assertEqual(min_sal, 150000)
        self.assertEqual(max_sal, 200000)

        # Test invalid salary
        min_sal, max_sal = self.spider._parse_salary('Competitive salary')
        self.assertIsNone(min_sal)
        self.assertIsNone(max_sal)

    def test_job_type_detection(self):
        """Test that job type is correctly detected."""
        # Test internship detection
        job_type = self.spider._detect_job_type('Software Engineer Internship Program')
        self.assertEqual(job_type, 'internship')

        # Test full-time detection
        job_type = self.spider._detect_job_type('Full-time Software Engineer')
        self.assertEqual(job_type, 'full_time')

        # Test contract detection
        job_type = self.spider._detect_job_type('Contract Frontend Developer')
        self.assertEqual(job_type, 'contract')

        # Test default
        job_type = self.spider._detect_job_type('Some Random Job')
        self.assertEqual(job_type, 'full-time')

    def test_deduplication_signature(self):
        """Test that deduplication signature is generated correctly."""
        job_data = {
            'title': 'Software Engineer',
            'company': 'Google',
            'location': 'San Francisco, CA'
        }

        signature = self.spider._generate_dedupe_signature(job_data)

        # Should be MD5 hash
        self.assertEqual(len(signature), 32)  # MD5 hash is 32 chars
        self.assertTrue(all(c in '0123456789abcdef' for c in signature))

        # Same data should produce same signature
        signature2 = self.spider._generate_dedupe_signature(job_data)
        self.assertEqual(signature, signature2)

        # Different data should produce different signature
        job_data['title'] = 'Different Title'
        signature3 = self.spider._generate_dedupe_signature(job_data)
        self.assertNotEqual(signature, signature3)

    def test_push_to_queue(self):
        """Test that jobs are pushed to Redis queue."""
        job_data = {
            'title': 'Software Engineer',
            'company': 'Google',
            'location': 'San Francisco, CA',
            'url': 'https://google.com/jobs/1',
            'source': 'indeed'
        }

        self.spider._push_to_queue(job_data)

        # Verify Redis lpush was called
        self.spider.redis_client.lpush.assert_called_once()

        # Get the call arguments
        call_args = self.spider.redis_client.lpush.call_args
        queue_name = call_args[0][0]
        job_json = call_args[0][1]

        # Verify queue name
        self.assertEqual(queue_name, 'ingest:jobs')

        # Verify JSON can be parsed
        parsed_job = json.loads(job_json)
        self.assertEqual(parsed_job['title'], 'Software Engineer')
        self.assertIn('dedupe_signature', parsed_job)

    def test_missing_fields_filtered(self):
        """Test that jobs with missing critical fields are filtered."""
        # Create response with job missing company name
        html_no_company = """
        <html>
        <body>
            <div data-testid="result">
                <h2 class="jobTitle"><span>Software Engineer</span></h2>
                <span data-testid="company-name"></span>
                <div data-testid="job-location">SF</div>
            </div>
        </body>
        </html>
        """

        response = HtmlResponse(
            url='https://www.indeed.com/jobs',
            body=html_no_company.encode('utf-8')
        )

        selector = Selector(text=html_no_company)
        job_item = selector.css("div[data-testid='result']")[0]

        # Extract should return None (filtered) because company is empty
        job_data = self.spider._extract_job_data(job_item, response)
        self.assertIsNone(job_data)


if __name__ == '__main__':
    unittest.main()
