import os
import sys

# Ensure Supabase environment variables exist for modules under test
os.environ.setdefault("VITE_SUPABASE_PROJECT_URL", "https://example.supabase.co")
os.environ.setdefault("VITE_SUPABASE_API_KEY", "test-api-key")

# Add project root so `utils` package can be imported when tests run from scripts directory
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
