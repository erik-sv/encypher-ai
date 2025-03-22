"""
Tests for the MetadataEncoder class.
"""
import json
import time
from typing import Dict, Any

import pytest

from encypher.core.metadata_encoder import MetadataEncoder


class TestMetadataEncoder:
    """Test cases for MetadataEncoder class."""

    def test_encode_decode_metadata(self):
        """Test encoding and decoding metadata."""
        encoder = MetadataEncoder(secret_key="test-secret")
        text = "This is a test text."
        metadata = {
            "model_id": "test-model",
            "timestamp": int(time.time()),
            "request_id": "test-request",
        }

        # Encode metadata
        encoded_text = encoder.encode_metadata(text, metadata)

        # Ensure the text is modified (metadata added)
        assert encoded_text != text

        # Decode metadata
        extracted_metadata, clean_text = encoder.decode_metadata(encoded_text)

        # Verify extracted metadata
        assert extracted_metadata is not None
        assert extracted_metadata.get("model_id") == metadata["model_id"]
        assert int(extracted_metadata.get("timestamp")) == metadata["timestamp"]
        assert extracted_metadata.get("request_id") == metadata["request_id"]

        # Verify clean text
        assert clean_text == text

    def test_verify_text(self):
        """Test verifying text with metadata."""
        encoder = MetadataEncoder(secret_key="test-secret")
        text = "This is a test text."
        metadata = {"model_id": "test-model", "timestamp": int(time.time())}

        # Encode metadata
        encoded_text = encoder.encode_metadata(text, metadata)

        # Verify text
        is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)

        # Check results
        assert is_valid is True
        assert extracted_metadata is not None
        assert extracted_metadata.get("model_id") == metadata["model_id"]
        # Fix: Compare integers directly
        assert int(extracted_metadata.get("timestamp")) == metadata["timestamp"]
        assert clean_text == text

    def test_invalid_hmac(self):
        """Test with invalid HMAC."""
        # Create two encoders with different secret keys
        encoder1 = MetadataEncoder(secret_key="secret1")
        encoder2 = MetadataEncoder(secret_key="secret2")

        text = "This is a test text."
        metadata = {"model_id": "test-model", "timestamp": int(time.time())}

        # Encode with first encoder
        encoded_text = encoder1.encode_metadata(text, metadata)

        # Try to verify with second encoder (should fail)
        is_valid, extracted_metadata, clean_text = encoder2.verify_text(encoded_text)

        # Check results
        assert is_valid is False
        assert extracted_metadata is None

    def test_bytes_to_zwc_conversion(self):
        """Test conversion between bytes and zero-width characters."""
        encoder = MetadataEncoder()

        # Test with simple byte sequences
        test_bytes = b"test"
        zwc_str = encoder._bytes_to_zwc(test_bytes)

        # Ensure conversion produces only zero-width characters
        for char in zwc_str:
            assert char in (encoder.ZERO_WIDTH_SPACE, encoder.ZERO_WIDTH_NON_JOINER)

        # Convert back
        bytes_back = encoder._zwc_to_bytes(zwc_str)
        assert bytes_back == test_bytes

    def test_empty_text(self):
        """Test with empty text."""
        encoder = MetadataEncoder()
        text = ""
        metadata = {"model_id": "test-model", "timestamp": int(time.time())}

        # Encode metadata
        encoded_text = encoder.encode_metadata(text, metadata)

        # Ensure the text is modified (metadata added)
        assert encoded_text != text

        # Decode metadata
        extracted_metadata, clean_text = encoder.decode_metadata(encoded_text)

        # Verify extracted metadata
        assert extracted_metadata is not None
        assert extracted_metadata.get("model_id") == metadata["model_id"]
        # Fix: Compare integers directly
        assert int(extracted_metadata.get("timestamp")) == metadata["timestamp"]

    def test_no_metadata(self):
        """Test decoding text without metadata."""
        encoder = MetadataEncoder()
        text = "This is a test text without metadata."

        # Try to decode
        extracted_metadata, clean_text = encoder.decode_metadata(text)

        # Check results
        assert extracted_metadata is None
        assert clean_text == text
