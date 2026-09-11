"""Vercel serverless entrypoint: exposes the Flask app as `app`."""
try:
    from app import app  # noqa: F401  (Vercel runs with api/ as workdir)
except ImportError:  # fallback when loaded by absolute path (tests, tooling)
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from app import app  # noqa: F401,E402

_FLASK_ROUTES_APP = app

_original_wsgi_app = _FLASK_ROUTES_APP.wsgi_app


def _vercel_wsgi_app(environ, start_response):
    """Restore the original request path.

    Current Vercel rewrite behavior forwards the *rewritten* destination path
    (``/api/index...``) to the function, so Flask would 404 every route.
    Strip that prefix so ``/``, ``/check``, ``/health`` and ``/static/*``
    route normally. Requests that already carry the original path pass through
    untouched, so this is safe under both old and new routing behavior.
    """
    path = environ.get("PATH_INFO", "") or ""
    if path == "/api/index" or path.startswith("/api/index/"):
        environ["PATH_INFO"] = path[len("/api/index"):] or "/"
    return _original_wsgi_app(environ, start_response)


_FLASK_ROUTES_APP.wsgi_app = _vercel_wsgi_app
