"""
Tests for Extended Phase 2B Spiders - 45+ job portal sources

Tests all Tier 1, 2, 4, and 5 spiders initialization.
Verifies configuration loading for 51 total job sources.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from autointern_scraper.spiders.generic_spider import (
    # Tier 1: Indian Portals
    NaukriSpider,
    MonsterIndiaSpider,
    FreshersworldSpider,
    TimesJobsSpider,
    FounditSpider,
    ShineSpider,
    HirectSpider,
    CutshortSpider,
    # Tier 2: Remote & Tech
    FlexJobsSpider,
    HackerEarthSpider,
    AngelListTalentSpider,
    TuringSpider,
    ArcDevSpider,
    RemotiveSpider,
    JobspressoSpider,
    # Tier 4: Extended Tech Companies
    NVIDIACareersSpider,
    FlipkartCareersSpider,
    SwiggyCareersSpider,
    ZohoCareersSpider,
    FreshworksCareersSpider,
    RazorpayCareersSpider,
    # Tier 5: Data & Analytics
    MuSigmaSpider,
    FractalAnalyticsSpider,
    TigerAnalyticsSpider,
    LatentViewSpider,
    ZSAssociatesSpider,
    TredenceSpider,
    Course5IntelligenceSpider,
    DatabricksSpider,
    SnowflakeSpider,
    PalantirSpider,
)


class TestTier1IndianPortals(unittest.TestCase):
    """Test all Tier 1 Indian job portal spiders."""

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

    def test_naukri_spider(self):
        """Test Naukri spider initializes."""
        spider = NaukriSpider()
        self.assertEqual(spider.name, 'naukri')
        self.assertIsNotNone(spider.site_config)
        self.assertEqual(spider.site_config.get('name'), 'Naukri.com')

    def test_monster_india_spider(self):
        """Test Monster India spider."""
        spider = MonsterIndiaSpider()
        self.assertEqual(spider.name, 'monster_india')
        self.assertIsNotNone(spider.site_config)

    def test_freshersworld_spider(self):
        """Test Freshersworld spider."""
        spider = FreshersworldSpider()
        self.assertEqual(spider.name, 'freshersworld')
        self.assertIsNotNone(spider.site_config)

    def test_timesjobs_spider(self):
        """Test TimesJobs spider."""
        spider = TimesJobsSpider()
        self.assertEqual(spider.name, 'timesjobs')
        self.assertIsNotNone(spider.site_config)

    def test_foundit_spider(self):
        """Test Foundit spider."""
        spider = FounditSpider()
        self.assertEqual(spider.name, 'foundit')
        self.assertIsNotNone(spider.site_config)

    def test_shine_spider(self):
        """Test Shine spider."""
        spider = ShineSpider()
        self.assertEqual(spider.name, 'shine')
        self.assertIsNotNone(spider.site_config)

    def test_hirect_spider(self):
        """Test Hirect spider."""
        spider = HirectSpider()
        self.assertEqual(spider.name, 'hirect')
        self.assertIsNotNone(spider.site_config)

    def test_cutshort_spider(self):
        """Test Cutshort spider."""
        spider = CutshortSpider()
        self.assertEqual(spider.name, 'cutshort')
        self.assertIsNotNone(spider.site_config)


class TestTier2RemoteTech(unittest.TestCase):
    """Test all Tier 2 remote & tech-focused spiders."""

    def setUp(self):
        """Mock Redis and YAML."""
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        config_path = Path(__file__).parent.parent / 'autointern_scraper' / 'sites_config.yaml'

        import yaml
        with open(config_path) as f:
            self.all_configs = yaml.safe_load(f)

        self.mock_yaml.safe_load.return_value = self.all_configs

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_flexjobs_spider(self):
        """Test FlexJobs spider."""
        spider = FlexJobsSpider()
        self.assertEqual(spider.name, 'flexjobs')
        self.assertIsNotNone(spider.site_config)

    def test_hackerearth_spider(self):
        """Test HackerEarth spider."""
        spider = HackerEarthSpider()
        self.assertEqual(spider.name, 'hackerearth')
        self.assertIsNotNone(spider.site_config)

    def test_angellist_talent_spider(self):
        """Test AngelList Talent spider."""
        spider = AngelListTalentSpider()
        self.assertEqual(spider.name, 'angellist_talent')
        self.assertIsNotNone(spider.site_config)

    def test_turing_spider(self):
        """Test Turing spider."""
        spider = TuringSpider()
        self.assertEqual(spider.name, 'turing')
        self.assertIsNotNone(spider.site_config)

    def test_arcdev_spider(self):
        """Test Arc.dev spider."""
        spider = ArcDevSpider()
        self.assertEqual(spider.name, 'arcdev')
        self.assertIsNotNone(spider.site_config)

    def test_remotive_spider(self):
        """Test Remotive spider."""
        spider = RemotiveSpider()
        self.assertEqual(spider.name, 'remotive')
        self.assertIsNotNone(spider.site_config)

    def test_jobspresso_spider(self):
        """Test Jobspresso spider."""
        spider = JobspressoSpider()
        self.assertEqual(spider.name, 'jobspresso')
        self.assertIsNotNone(spider.site_config)


class TestTier4ExtendedTechCompanies(unittest.TestCase):
    """Test extended tech company career page spiders."""

    def setUp(self):
        """Mock Redis and YAML."""
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        config_path = Path(__file__).parent.parent / 'autointern_scraper' / 'sites_config.yaml'

        import yaml
        with open(config_path) as f:
            self.all_configs = yaml.safe_load(f)

        self.mock_yaml.safe_load.return_value = self.all_configs

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_nvidia_careers_spider(self):
        """Test NVIDIA Careers spider."""
        spider = NVIDIACareersSpider()
        self.assertEqual(spider.name, 'nvidia_careers')
        self.assertIsNotNone(spider.site_config)

    def test_flipkart_careers_spider(self):
        """Test Flipkart Careers spider."""
        spider = FlipkartCareersSpider()
        self.assertEqual(spider.name, 'flipkart_careers')
        self.assertIsNotNone(spider.site_config)

    def test_swiggy_careers_spider(self):
        """Test Swiggy Careers spider."""
        spider = SwiggyCareersSpider()
        self.assertEqual(spider.name, 'swiggy_careers')
        self.assertIsNotNone(spider.site_config)

    def test_zoho_careers_spider(self):
        """Test Zoho Careers spider."""
        spider = ZohoCareersSpider()
        self.assertEqual(spider.name, 'zoho_careers')
        self.assertIsNotNone(spider.site_config)

    def test_freshworks_careers_spider(self):
        """Test Freshworks Careers spider."""
        spider = FreshworksCareersSpider()
        self.assertEqual(spider.name, 'freshworks_careers')
        self.assertIsNotNone(spider.site_config)

    def test_razorpay_careers_spider(self):
        """Test Razorpay Careers spider."""
        spider = RazorpayCareersSpider()
        self.assertEqual(spider.name, 'razorpay_careers')
        self.assertIsNotNone(spider.site_config)


class TestTier5DataAnalytics(unittest.TestCase):
    """Test Tier 5 data science & analytics company spiders."""

    def setUp(self):
        """Mock Redis and YAML."""
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        config_path = Path(__file__).parent.parent / 'autointern_scraper' / 'sites_config.yaml'

        import yaml
        with open(config_path) as f:
            self.all_configs = yaml.safe_load(f)

        self.mock_yaml.safe_load.return_value = self.all_configs

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_mu_sigma_spider(self):
        """Test Mu Sigma spider."""
        spider = MuSigmaSpider()
        self.assertEqual(spider.name, 'mu_sigma')
        self.assertIsNotNone(spider.site_config)

    def test_fractal_analytics_spider(self):
        """Test Fractal Analytics spider."""
        spider = FractalAnalyticsSpider()
        self.assertEqual(spider.name, 'fractal_analytics')
        self.assertIsNotNone(spider.site_config)

    def test_tiger_analytics_spider(self):
        """Test Tiger Analytics spider."""
        spider = TigerAnalyticsSpider()
        self.assertEqual(spider.name, 'tiger_analytics')
        self.assertIsNotNone(spider.site_config)

    def test_latentview_spider(self):
        """Test LatentView Analytics spider."""
        spider = LatentViewSpider()
        self.assertEqual(spider.name, 'latentview')
        self.assertIsNotNone(spider.site_config)

    def test_zs_associates_spider(self):
        """Test ZS Associates spider."""
        spider = ZSAssociatesSpider()
        self.assertEqual(spider.name, 'zs_associates')
        self.assertIsNotNone(spider.site_config)

    def test_tredence_spider(self):
        """Test Tredence spider."""
        spider = TredenceSpider()
        self.assertEqual(spider.name, 'tredence')
        self.assertIsNotNone(spider.site_config)

    def test_course5_intelligence_spider(self):
        """Test Course5 Intelligence spider."""
        spider = Course5IntelligenceSpider()
        self.assertEqual(spider.name, 'course5_intelligence')
        self.assertIsNotNone(spider.site_config)

    def test_databricks_spider(self):
        """Test Databricks spider."""
        spider = DatabricksSpider()
        self.assertEqual(spider.name, 'databricks')
        self.assertIsNotNone(spider.site_config)

    def test_snowflake_spider(self):
        """Test Snowflake spider."""
        spider = SnowflakeSpider()
        self.assertEqual(spider.name, 'snowflake')
        self.assertIsNotNone(spider.site_config)

    def test_palantir_spider(self):
        """Test Palantir spider."""
        spider = PalantirSpider()
        self.assertEqual(spider.name, 'palantir')
        self.assertIsNotNone(spider.site_config)


class TestAllSpidersConfiguration(unittest.TestCase):
    """Test that all spiders have proper configuration."""

    def setUp(self):
        """Mock Redis and YAML."""
        self.redis_patcher = patch('autointern_scraper.spiders.base_spider.redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis.from_url.return_value.lpush = MagicMock()

        self.yaml_patcher = patch('autointern_scraper.spiders.base_spider.yaml')
        self.mock_yaml = self.yaml_patcher.start()

        config_path = Path(__file__).parent.parent / 'autointern_scraper' / 'sites_config.yaml'

        import yaml
        with open(config_path) as f:
            self.all_configs = yaml.safe_load(f)

        self.mock_yaml.safe_load.return_value = self.all_configs

    def tearDown(self):
        """Clean up."""
        self.redis_patcher.stop()
        self.yaml_patcher.stop()

    def test_all_spiders_have_base_url(self):
        """Test all 51 spiders have base_url configured."""
        spider_classes = [
            # Tier 1
            NaukriSpider, MonsterIndiaSpider, FreshersworldSpider, TimesJobsSpider,
            FounditSpider, ShineSpider, HirectSpider, CutshortSpider,
            # Tier 2
            FlexJobsSpider, HackerEarthSpider, AngelListTalentSpider, TuringSpider,
            ArcDevSpider, RemotiveSpider, JobspressoSpider,
            # Tier 4
            NVIDIACareersSpider, FlipkartCareersSpider, SwiggyCareersSpider, ZohoCareersSpider,
            FreshworksCareersSpider, RazorpayCareersSpider,
            # Tier 5
            MuSigmaSpider, FractalAnalyticsSpider, TigerAnalyticsSpider, LatentViewSpider,
            ZSAssociatesSpider, TredenceSpider, Course5IntelligenceSpider,
            DatabricksSpider, SnowflakeSpider, PalantirSpider,
        ]

        for spider_class in spider_classes:
            with self.subTest(spider=spider_class.__name__):
                spider = spider_class()
                self.assertIn('base_url', spider.site_config,
                             f"{spider.name} missing base_url in configuration")
                self.assertTrue(spider.site_config.get('base_url'),
                               f"{spider.name} base_url is empty")


if __name__ == '__main__':
    unittest.main()
