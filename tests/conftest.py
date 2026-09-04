"""
Pytest configuration for Fena Calculator test suite.
Sets required environment variables before agent modules are imported.
"""
import os

# Set required environment variables before any agent imports
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-not-for-production")
os.environ.setdefault("MODEL_PROVIDER", "mock")
