#!/usr/bin/env python
"""Run database migrations."""
import os
import sys
from pathlib import Path

# Set the DATABASE_URL environment variable with the Neon connection
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://neondb_owner:npg_DouesGVE9c4P@ep-orange-paper-a1gxf86x-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

# Add the api directory to the path
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

from alembic.config import Config
from alembic import command

if __name__ == "__main__":
    # Create the config with correct path
    alembic_ini = api_dir / "alembic.ini"
    cfg = Config(str(alembic_ini))
    
    # Set the script location relative to the alembic.ini location
    cfg.set_main_option("sqlalchemy.url", os.environ['DATABASE_URL'])
    cfg.set_main_option("script_location", str(api_dir / "alembic"))
    
    print(f"Running migrations against Neon database...")
    command.upgrade(cfg, "head")
    print("✓ Migrations completed successfully!")
