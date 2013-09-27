"""
All framework-specific dependencies should live in this submodule and be
exported in a framework-agnostic way.
"""

from .setup import setup_wsgi, setup_shell, setup_testing
from .setup import httpexceptions

from .request import Request
from .response import Response, render, render_to_response
