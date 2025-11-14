"""Presentation layer middleware."""

from app.presentation.middleware.exception_handler import domain_exception_handler

__all__ = ["domain_exception_handler"]
