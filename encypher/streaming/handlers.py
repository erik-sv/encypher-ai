"""
Streaming handlers for EncypherAI metadata encoding.

This module provides utilities for handling streaming responses from LLMs
and encoding metadata into the streaming chunks.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Any

from encypher.core.unicode_metadata import UnicodeMetadata, MetadataTarget


class StreamingHandler:
    """
    Handler for processing streaming chunks from LLM providers and encoding metadata.

    This class ensures that metadata is properly encoded in streaming responses,
    handling the complexities of partial text chunks while maintaining consistency.
    """

    def __init__(
        self,
        metadata: Optional[Dict[str, Any]] = None,
        target: Union[str, MetadataTarget] = "whitespace",
        encode_first_chunk_only: bool = True,
    ):
        """
        Initialize the streaming handler.

        Args:
            metadata: Dictionary of metadata to encode (model_id, timestamp, etc.)
            target: Where to embed the metadata (whitespace, punctuation, etc.)
            encode_first_chunk_only: Whether to encode metadata only in the first non-empty chunk
        """
        self.metadata = metadata or {}

        # Ensure we have a timestamp if not provided
        if "timestamp" not in self.metadata:
            self.metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Parse target
        if isinstance(target, str):
            try:
                self.target = MetadataTarget(target)
            except ValueError:
                self.target = MetadataTarget.WHITESPACE
        else:
            self.target = (
                target
                if isinstance(target, MetadataTarget)
                else MetadataTarget.WHITESPACE
            )

        self.encode_first_chunk_only = encode_first_chunk_only
        self.has_encoded = False
        self.accumulated_text = ""

    def process_chunk(
        self, chunk: Union[str, Dict[str, Any]]
    ) -> Union[str, Dict[str, Any]]:
        """
        Process a streaming chunk and encode metadata if needed.

        This method handles both raw text chunks and structured chunks (like those from OpenAI).

        Args:
            chunk: Text chunk or dictionary containing a text chunk

        Returns:
            Processed chunk with encoded metadata
        """
        # Handle different chunk formats
        if isinstance(chunk, str):
            return self._process_text_chunk(chunk)
        elif isinstance(chunk, dict):
            return self._process_dict_chunk(chunk)
        else:
            # If we don't recognize the format, return as is
            return chunk

    def _process_text_chunk(self, chunk: str) -> str:
        """
        Process a text chunk and encode metadata if needed.

        Args:
            chunk: Text chunk

        Returns:
            Processed text chunk with encoded metadata
        """
        # Skip empty chunks
        if not chunk.strip():
            return chunk

        # If we're only encoding the first chunk and we've already done so, return as is
        if self.encode_first_chunk_only and self.has_encoded:
            return chunk

        # Encode metadata
        model_id = self.metadata.get("model_id")
        timestamp = self.metadata.get("timestamp")

        encoded_chunk = UnicodeMetadata.embed_metadata(
            text=chunk,
            model_id=model_id if model_id is not None else "",
            timestamp=(
                timestamp
                if timestamp is not None
                else datetime.now(timezone.utc).isoformat()
            ),
            target=self.target,
            custom_metadata={
                k: v
                for k, v in self.metadata.items()
                if k not in ["model_id", "timestamp"]
            },
        )

        # Mark that we've encoded metadata
        self.has_encoded = True

        return encoded_chunk

    def _process_dict_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a dictionary chunk and encode metadata if needed.

        This handles structured chunks like those from OpenAI's streaming API.

        Args:
            chunk: Dictionary containing a text chunk

        Returns:
            Processed dictionary with encoded metadata
        """
        # Make a copy to avoid modifying the original
        processed_chunk = chunk.copy()

        # Handle OpenAI-style chunks
        if "choices" in processed_chunk and isinstance(
            processed_chunk["choices"], list
        ):
            for choice in processed_chunk["choices"]:
                # Handle delta format (OpenAI chat completions)
                if (
                    "delta" in choice
                    and "content" in choice["delta"]
                    and choice["delta"]["content"]
                ):
                    content = choice["delta"]["content"]

                    # Skip empty content
                    if not content.strip():
                        continue

                    # If we're only encoding the first chunk and we've already done so, continue
                    if self.encode_first_chunk_only and self.has_encoded:
                        continue

                    # Encode metadata
                    model_id = self.metadata.get("model_id")
                    timestamp = self.metadata.get("timestamp")

                    encoded_content = UnicodeMetadata.embed_metadata(
                        text=content,
                        model_id=model_id if model_id is not None else "",
                        timestamp=(
                            timestamp
                            if timestamp is not None
                            else datetime.now(timezone.utc).isoformat()
                        ),
                        target=self.target,
                        custom_metadata={
                            k: v
                            for k, v in self.metadata.items()
                            if k not in ["model_id", "timestamp"]
                        },
                    )

                    # Update the chunk with encoded content
                    choice["delta"]["content"] = encoded_content

                    # Mark that we've encoded metadata
                    self.has_encoded = True

                # Handle text format (older APIs)
                elif "text" in choice and choice["text"]:
                    content = choice["text"]

                    # Skip empty content
                    if not content.strip():
                        continue

                    # If we're only encoding the first chunk and we've already done so, continue
                    if self.encode_first_chunk_only and self.has_encoded:
                        continue

                    # Encode metadata
                    model_id = self.metadata.get("model_id")
                    timestamp = self.metadata.get("timestamp")

                    encoded_content = UnicodeMetadata.embed_metadata(
                        text=content,
                        model_id=model_id if model_id is not None else "",
                        timestamp=(
                            timestamp
                            if timestamp is not None
                            else datetime.now(timezone.utc).isoformat()
                        ),
                        target=self.target,
                        custom_metadata={
                            k: v
                            for k, v in self.metadata.items()
                            if k not in ["model_id", "timestamp"]
                        },
                    )

                    # Update the chunk with encoded content
                    choice["text"] = encoded_content

                    # Mark that we've encoded metadata
                    self.has_encoded = True

        # Handle Anthropic-style chunks
        elif "completion" in processed_chunk and processed_chunk["completion"]:
            content = processed_chunk["completion"]

            # Skip empty content
            if not content.strip():
                return processed_chunk

            # If we're only encoding the first chunk and we've already done so, return as is
            if self.encode_first_chunk_only and self.has_encoded:
                return processed_chunk

            # Encode metadata
            model_id = self.metadata.get("model_id")
            timestamp = self.metadata.get("timestamp")

            encoded_content = UnicodeMetadata.embed_metadata(
                text=content,
                model_id=model_id if model_id is not None else "",
                timestamp=(
                    timestamp
                    if timestamp is not None
                    else datetime.now(timezone.utc).isoformat()
                ),
                target=self.target,
                custom_metadata={
                    k: v
                    for k, v in self.metadata.items()
                    if k not in ["model_id", "timestamp"]
                },
            )

            # Update the chunk with encoded content
            processed_chunk["completion"] = encoded_content

            # Mark that we've encoded metadata
            self.has_encoded = True

        return processed_chunk

    def reset(self) -> None:
        """
        Reset the handler state.

        This is useful when starting a new streaming session.
        """
        self.has_encoded = False
        self.accumulated_text = ""
