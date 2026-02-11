"""
Tests for Generic Spider - Verifies all 16 new sources initialize correctly

This tests that the generic spider can handle all configured sites.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from autointern_scraper.spiders.generic_spider import (
    GenericJobSpider,
    GoogleCareersSpider,
    MicrosoftCareersSpider,
    MetaCareersSpider,
    AmazonCareersSpider,
    AppleCareersSpider,
    NetflixCareersSpider,
    TCSCareersSpider,
    InfosysCareersSpider,
    WiproCareersSpider,
    GitHubJobsSpider,
    StackOverflowJobsSpider,
    HackerRankJobsSpider,
    LeetCodeDiscussSpider,
    YCombinatorJobsSpider,
    ProductManagerHQSpider,
    DribbbleJobsSpider,
)


class TestGenericSpiderInitialization(unittest.TestCase):
    """Test that all 16 company spiders initialize correctly."""

    def setUp(self):
        """Mock Redis and YAML."""
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        # Load all sites configuration
        config_path = Path(__file__).parent.parent / 'autointern_scraper' / 'sites_config.yaml'

        import yaml
        with open(config_path) as f:
            self.all_configs = yaml.safe_load(f)

        self.mock_yaml.safe_load.return_value = self.all_configs

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_google_careers_spider(self):
        """Test Google Careers spider initializes."""
        spider = GoogleCareersSpider()
        self.assertEqual(spider.name, 'google_careers')
        self.assertEqual(spider.site_name, 'google_careers')
        self.assertIsNotNone(spider.site_config)

    def test_microsoft_careers_spider(self):
        """Test Microsoft Careers spider."""
        spider = MicrosoftCareersSpider()
        self.assertEqual(spider.name, 'microsoft_careers')
        self.assertIn('microsoft', spider.site_config.get('name', '').lower())

    def test_meta_careers_spider(self):
        """Test Meta Careers spider."""
        spider = MetaCareersSpider()
        self.assertEqual(spider.name, 'meta_careers')
        self.assertIsNotNone(spider.site_config)

    def test_amazon_careers_spider(self):
        """Test Amazon Careers spider."""
        spider = AmazonCareersSpider()
        self.assertEqual(spider.name, 'amazon_careers')
        self.assertIsNotNone(spider.site_config)

    def test_apple_careers_spider(self):
        """Test Apple Careers spider."""
        spider = AppleCareersSpider()
        self.assertEqual(spider.name, 'apple_careers')
        self.assertIsNotNone(spider.site_config)

    def test_netflix_careers_spider(self):
        """Test Netflix Careers spider."""
        spider = NetflixCareersSpider()
        self.assertEqual(spider.name, 'netflix_careers')
        self.assertIsNotNone(spider.site_config)

    def test_tcs_careers_spider(self):
        """Test TCS Careers spider."""
        spider = TCSCareersSpider()
        self.assertEqual(spider.name, 'tcs_careers')
        self.assertIsNotNone(spider.site_config)

    def test_infosys_careers_spider(self):
        """Test Infosys Careers spider."""
        spider = InfosysCareersSpider()
        self.assertEqual(spider.name, 'infosys_careers')
        self.assertIsNotNone(spider.site_config)

    def test_wipro_careers_spider(self):
        """Test Wipro Careers spider."""
        spider = WiproCareersSpider()
        self.assertEqual(spider.name, 'wipro_careers')
        self.assertIsNotNone(spider.site_config)

    def test_github_jobs_spider(self):
        """Test GitHub Jobs spider."""
        spider = GitHubJobsSpider()
        self.assertEqual(spider.name, 'github_jobs')
        self.assertIsNotNone(spider.site_config)

    def test_stackoverflow_jobs_spider(self):
        """Test Stack Overflow Jobs spider."""
        spider = StackOverflowJobsSpider()
        self.assertEqual(spider.name, 'stackoverflow_jobs')
        self.assertIsNotNone(spider.site_config)

    def test_hackerrank_jobs_spider(self):
        """Test HackerRank Jobs spider."""
        spider = HackerRankJobsSpider()
        self.assertEqual(spider.name, 'hackerrank_jobs')
        self.assertIsNotNone(spider.site_config)

    def test_leetcode_discuss_spider(self):
        """Test LeetCode Discuss spider."""
        spider = LeetCodeDiscussSpider()
        self.assertEqual(spider.name, 'leetcode_discuss')
        self.assertIsNotNone(spider.site_config)

    def test_ycombinator_jobs_spider(self):
        """Test Y Combinator Jobs spider."""
        spider = YCombinatorJobsSpider()
        self.assertEqual(spider.name, 'ycombinator_jobs')
        self.assertIsNotNone(spider.site_config)

    def test_productmanagerhq_spider(self):
        """Test Product Manager HQ spider."""
        spider = ProductManagerHQSpider()
        self.assertEqual(spider.name, 'productmanagerhq')
        self.assertIsNotNone(spider.site_config)

    def test_dribbble_jobs_spider(self):
        """Test Dribbble Jobs spider."""
        spider = DribbbleJobsSpider()
        self.assertEqual(spider.name, 'dribbble_jobs')
        self.assertIsNotNone(spider.site_config)

    def test_all_spiders_have_base_url(self):
        """Test all spiders have a base URL configured."""
        spiders = [
            GoogleCareersSpider(),
            MicrosoftCareersSpider(),
            MetaCareersSpider(),
            AmazonCareersSpider(),
            AppleCareersSpider(),
            NetflixCareersSpider(),
            TCSCareersSpider(),
            InfosysCareersSpider(),
            WiproCareersSpider(),
            GitHubJobsSpider(),
            StackOverflowJobsSpider(),
            HackerRankJobsSpider(),
            LeetCodeDiscussSpider(),
            YCombinatorJobsSpider(),
            ProductManagerHQSpider(),
            DribbbleJobsSpider(),
        ]

        for spider in spiders:
            self.assertIn('base_url', spider.site_config, f"{spider.name} missing base_url")

    def test_generic_spider_salary_parsing(self):
        """Test generic spider salary parsing logic."""
        spider = GoogleCareersSpider()

        # Test valid salary
        min_sal, max_sal = spider._parse_salary('$100,000 - $150,000')
        self.assertEqual(min_sal, 100000)
        self.assertEqual(max_sal, 150000)

        # Test invalid salary
        min_sal, max_sal = spider._parse_salary('Competitive')
        self.assertIsNone(min_sal)
        self.assertIsNone(max_sal)


if __name__ == '__main__':
    unittest.main()
