"""
EncypherAI Core Package

A Python package for embedding and extracting metadata in text using Unicode variation selectors.
This package provides tools for invisible metadata encoding in AI-generated text.
"""

__version__ = "1.0.0"

from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import UnicodeMetadata, MetadataTarget

__all__ = ["MetadataEncoder", "UnicodeMetadata", "MetadataTarget"]
