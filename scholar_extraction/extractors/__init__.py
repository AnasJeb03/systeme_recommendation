"""Module d'extraction de données depuis différentes sources académiques."""

from .google_scholar import GoogleScholarExtractor
from .hal import HALExtractor # type: ignore

__all__ = ['GoogleScholarExtractor', 'HALExtractor']