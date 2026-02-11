"""
Unit tests for Phase 2 spiders: Wellfound, RemoteOK, WeWorkRemotely

Tests basic initialization and parsing logic.
Does NOT make real HTTP requests.
"""

import unittest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from autointern_scraper.spiders.wellfound_spider import WellfoundSpider
from autointern_scraper.spiders.remoteok_spider import RemoteOkSpider
from autointern_scraper.spiders.weworkremotely_spider import WeworkremotellySpider


class TestWellfoundSpider(unittest.TestCase):
    """Test Wellfound spider initialization and parsing."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / 'fixtures' / 'wellfound_sample.json'
        with open(fixture_path, 'r') as f:
            self.json_content = json.load(f)

        # Mock Redis and YAML
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        self.spider_config = {
            'wellfound': {
                'name': 'Wellfound',
                'base_url': 'https://wellfound.com/api/v3/jobs',
                'pagination': {'strategy': 'page', 'max_pages': 20},
                'selectors': {},
                'redis_queue': 'ingest:jobs'
            }
        }

        self.mock_yaml.safe_load.return_value = self.spider_config
        self.spider = WellfoundSpider()

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_spider_initialization(self):
        """Test spider initializes correctly."""
        self.assertEqual(self.spider.name, 'wellfound')
        self.assertEqual(self.spider.site_name, 'wellfound')

    def test_wellfound_job_extraction_fields(self):
        """Test all fields extracted from Wellfound API response."""
        response = MagicMock()
        response.url = 'test_url'

        job = self.json_content['jobs'][0]
        extracted = self.spider._extract_job_from_api(job, response)

        self.assertIsNotNone(extracted)
        self.assertEqual(extracted['title'], 'Full Stack Engineer')
        self.assertEqual(extracted['company'], 'TechStartup Inc')
        self.assertEqual(extracted['location'], 'San Francisco, CA')
        self.assertEqual(extracted['salary_min'], 120000)
        self.assertEqual(extracted['salary_max'], 150000)
        self.assertEqual(extracted['source'], 'wellfound')

    def test_wellfound_job_type_detection(self):
        """Test job level to type mapping."""
        # Test Intern level
        job_type = self.spider._detect_job_type_from_level('Intern')
        self.assertEqual(job_type, 'internship')

        # Test Mid level defaults to full-time
        job_type = self.spider._detect_job_type_from_level('Mid')
        self.assertEqual(job_type, 'full-time')

    def test_wellfound_missing_fields_filtered(self):
        """Test that jobs missing critical fields are filtered."""
        incomplete_job = {
            'title': 'Test Job',
            'startup_name': '',  # Missing company
            'location': 'Remote',
            'description': 'Test',
            'url': 'https://test.com'
        }

        response = MagicMock()
        extracted = self.spider._extract_job_from_api(incomplete_job, response)
        self.assertIsNone(extracted)

    def test_wellfound_salary_parsing(self):
        """Test salary parsing."""
        min_sal = self.spider._parse_salary_min(120000)
        max_sal = self.spider._parse_salary_max(150000)
        self.assertEqual(min_sal, 120000)
        self.assertEqual(max_sal, 150000)


class TestRemoteOkSpider(unittest.TestCase):
    """Test RemoteOK spider initialization."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / 'fixtures' / 'remoteok_sample.html'
        with open(fixture_path, 'r') as f:
            self.html_content = f.read()

        # Mock Redis and YAML
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        self.spider_config = {
            'remoteok': {
                'name': 'RemoteOK',
                'base_url': 'https://remoteok.io/api/jobs',
                'pagination': {'strategy': 'none', 'max_pages': 1},
                'selectors': {
                    'job_item': 'tr.job',
                    'job_title': 'h2',
                    'company': '.company',
                    'location': '.location'
                },
                'redis_queue': 'ingest:jobs'
            }
        }

        self.mock_yaml.safe_load.return_value = self.spider_config
        self.spider = RemoteOkSpider()

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_spider_initialization(self):
        """Test spider initializes correctly."""
        self.assertEqual(self.spider.name, 'remoteok')
        self.assertEqual(self.spider.site_name, 'remoteok')

    def test_remoteok_salary_parsing(self):
        """Test salary parsing for RemoteOK format."""
        min_sal, max_sal = self.spider._parse_salary('$100,000 - $150,000')
        self.assertEqual(min_sal, 100000)
        self.assertEqual(max_sal, 150000)

    def test_remoteok_no_salary(self):
        """Test salary parsing with no valid salary."""
        min_sal, max_sal = self.spider._parse_salary('Competitive')
        self.assertIsNone(min_sal)
        self.assertIsNone(max_sal)


class TestWeWorkRemotellySpider(unittest.TestCase):
    """Test WeWorkRemotely spider initialization."""

    def setUp(self):
        """Set up test fixtures."""
        fixture_path = Path(__file__).parent / 'fixtures' / 'weworkremotely_sample.html'
        with open(fixture_path, 'r') as f:
            self.html_content = f.read()

        # Mock Redis and YAML
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        self.spider_config = {
            'weworkremotely': {
                'name': 'WeWorkRemotely',
                'base_url': 'https://weworkremotely.com/remote-jobs',
                'pagination': {'strategy': 'page', 'max_pages': 5},
                'selectors': {
                    'job_item': 'div.job-listing',
                    'job_title': 'h2',
                    'company': '.company-name',
                    'location': '.location'
                },
                'redis_queue': 'ingest:jobs'
            }
        }

        self.mock_yaml.safe_load.return_value = self.spider_config
        self.spider = WeworkremotellySpider()

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_spider_initialization(self):
        """Test spider initializes correctly."""
        self.assertEqual(self.spider.name, 'weworkremotely')
        self.assertEqual(self.spider.site_name, 'weworkremotely')

    def test_weworkremotely_salary_parsing(self):
        """Test salary parsing."""
        min_sal, max_sal = self.spider._parse_salary('$130,000 - $170,000')
        self.assertEqual(min_sal, 130000)
        self.assertEqual(max_sal, 170000)

    def test_weworkremotely_remote_location(self):
        """Test Remote location handling."""
        # All WeWorkRemotely jobs are remote
        self.assertEqual(self.spider.site_name, 'weworkremotely')


if __name__ == '__main__':
    unittest.main()
