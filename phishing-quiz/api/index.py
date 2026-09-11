"""Vercel serverless entrypoint: exposes the Flask app as `app`.

Request-path normalization for Vercel rewrites is applied in app.py itself,
so this module stays a thin re-export regardless of which file the runtime
loads as the entrypoint.
"""
try:
    from app import app  # noqa: F401  (Vercel runs with api/ as workdir)
except ImportError:  # fallback when loaded by absolute path (tests, tooling)
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from app import app  # noqa: F401,E402
