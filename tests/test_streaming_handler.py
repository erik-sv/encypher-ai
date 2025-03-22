"""
Tests for the StreamingHandler class.
"""
import json
from datetime import datetime, timezone

import pytest

from encypher.core.unicode_metadata import UnicodeMetadata, MetadataTarget
from encypher.streaming.handlers import StreamingHandler


class TestStreamingHandler:
    """Test cases for StreamingHandler class."""

    def test_process_text_chunk(self):
        """Test processing a text chunk."""
        metadata = {
            "model_id": "test-model",
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        }

        handler = StreamingHandler(metadata=metadata, target=MetadataTarget.WHITESPACE)

        # Process a chunk
        chunk = "This is a test chunk with spaces."
        processed_chunk = handler.process_chunk(chunk)

        # Ensure the chunk is modified (metadata added)
        assert processed_chunk != chunk

        # Extract metadata from processed chunk
        extracted_metadata = UnicodeMetadata.extract_metadata(processed_chunk)

        # Verify extracted metadata
        assert extracted_metadata.get("model_id") == metadata["model_id"]
        # Compare timestamps ignoring microseconds
        assert isinstance(extracted_metadata.get("timestamp"), datetime)
        assert int(extracted_metadata.get("timestamp").timestamp()) == metadata["timestamp"]

    def test_encode_first_chunk_only(self):
        """Test encoding only the first chunk."""
        metadata = {
            "model_id": "test-model",
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        }

        handler = StreamingHandler(
            metadata=metadata,
            target=MetadataTarget.WHITESPACE,
            encode_first_chunk_only=True,
        )

        # Process first chunk
        chunk1 = "This is the first chunk."
        processed_chunk1 = handler.process_chunk(chunk1)

        # Ensure the first chunk is modified (metadata added)
        assert processed_chunk1 != chunk1
        assert handler.has_encoded is True

        # Process second chunk
        chunk2 = "This is the second chunk."
        processed_chunk2 = handler.process_chunk(chunk2)

        # Second chunk should not be modified
        assert processed_chunk2 == chunk2

    def test_encode_all_chunks(self):
        """Test encoding all chunks."""
        metadata = {
            "model_id": "test-model",
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        }

        handler = StreamingHandler(
            metadata=metadata,
            target=MetadataTarget.WHITESPACE,
            encode_first_chunk_only=False,
        )

        # Process multiple chunks
        chunks = [
            "This is the first chunk.",
            "This is the second chunk.",
            "This is the third chunk.",
        ]

        for chunk in chunks:
            processed_chunk = handler.process_chunk(chunk)

            # Each chunk should be modified (metadata added)
            assert processed_chunk != chunk

            # Extract metadata from processed chunk
            extracted_metadata = UnicodeMetadata.extract_metadata(processed_chunk)

            # Verify extracted metadata
            assert extracted_metadata.get("model_id") == metadata["model_id"]
            # Compare timestamps ignoring microseconds
            assert isinstance(extracted_metadata.get("timestamp"), datetime)
            assert int(extracted_metadata.get("timestamp").timestamp()) == metadata["timestamp"]

    def test_process_dict_chunk_openai(self):
        """Test processing an OpenAI-style dictionary chunk."""
        metadata = {
            "model_id": "test-model",
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        }

        handler = StreamingHandler(metadata=metadata, target=MetadataTarget.WHITESPACE)

        # Create an OpenAI-style chunk
        original_content = "This is a test chunk with spaces."
        chunk = {
            "id": "chatcmpl-123",
            "object": "chat.completion.chunk",
            "created": 1677858242,
            "model": "gpt-3.5-turbo-0613",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": original_content},
                    "finish_reason": None,
                }
            ],
        }

        # Process the chunk
        processed_chunk = handler.process_chunk(chunk)

        # Extract the processed content
        processed_content = processed_chunk["choices"][0]["delta"]["content"]

        # Ensure the content was modified (metadata added)
        assert processed_content != original_content
        assert len(processed_content) > len(original_content)

        # Verify other parts of the chunk remain unchanged
        assert processed_chunk["id"] == chunk["id"]
        assert processed_chunk["created"] == chunk["created"]
        assert processed_chunk["model"] == chunk["model"]

    def test_process_dict_chunk_anthropic(self):
        """Test processing an Anthropic-style dictionary chunk."""
        metadata = {
            "model_id": "test-model",
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        }

        handler = StreamingHandler(metadata=metadata, target=MetadataTarget.WHITESPACE)

        # Create an Anthropic-style chunk
        chunk = {
            "completion": "This is a test chunk with spaces.",
            "stop_reason": None,
            "model": "claude-2",
        }

        # Process the chunk
        processed_chunk = handler.process_chunk(chunk)

        # Ensure the chunk is modified (metadata added)
        assert processed_chunk != chunk

        # Extract the content from the processed chunk
        content = processed_chunk["completion"]

        # Extract metadata from the content
        extracted_metadata = UnicodeMetadata.extract_metadata(content)

        # Verify extracted metadata
        assert extracted_metadata.get("model_id") == metadata["model_id"]
        # Compare timestamps ignoring microseconds
        assert isinstance(extracted_metadata.get("timestamp"), datetime)
        assert int(extracted_metadata.get("timestamp").timestamp()) == metadata["timestamp"]

    def test_reset(self):
        """Test resetting the handler."""
        metadata = {
            "model_id": "test-model",
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
        }

        handler = StreamingHandler(metadata=metadata, target=MetadataTarget.WHITESPACE)

        # Process a chunk
        chunk = "This is a test chunk."
        handler.process_chunk(chunk)

        # Handler should have encoded metadata
        assert handler.has_encoded is True

        # Reset the handler
        handler.reset()

        # Handler should be reset
        assert handler.has_encoded is False
        assert handler.accumulated_text == ""

        # Process another chunk
        chunk2 = "This is another test chunk."
        processed_chunk2 = handler.process_chunk(chunk2)

        # Handler should encode metadata again
        assert handler.has_encoded is True
        assert processed_chunk2 != chunk2
