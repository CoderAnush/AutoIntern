import sys
import os

# Add project root to path
sys.path.insert(0, ".")

print("🔍 Checking imports...")

try:
    print("Attempting to import app.routes.admin...")
    from app.routes import admin
    print("✅ Successfully imported app.routes.admin")
except Exception as e:
    print(f"❌ Failed to import app.routes.admin: {e}")
    import traceback
    traceback.print_exc()

print("\nChecking other routes...")
routes = ["auth", "jobs", "resumes", "applications", "recommendations"]
for route in routes:
    try:
        module_name = f"app.routes.{route}"
        __import__(module_name)
        print(f"✅ Imported {module_name}")
    except Exception as e:
        print(f"❌ Failed to import {module_name}: {e}")
