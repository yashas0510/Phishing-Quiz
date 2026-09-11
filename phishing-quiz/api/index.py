"""Vercel serverless entrypoint: exposes the Flask app as `app`."""
try:
    from app import app  # noqa: F401  (Vercel runs with api/ as workdir)
except ImportError:  # fallback when loaded by absolute path (tests, tooling)
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from app import app  # noqa: F401,E402
