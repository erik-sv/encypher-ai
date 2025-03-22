"""
UTF Metadata Encoding System for EncypherAI

This module implements the core encoding system that invisibly embeds
metadata within AI-generated text responses.
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any


class MetadataEncoder:
    """
    MetadataEncoder implements invisible UTF encoding of metadata
    into AI-generated text while preserving visual appearance.

    The encoding uses zero-width characters (ZWCs) to encode binary data
    within text without changing its visible appearance:
    - Zero-width space (U+200B): Binary 0
    - Zero-width non-joiner (U+200C): Binary 1

    A checksum is added to ensure data integrity.
    """

    # Zero-width characters for binary encoding
    ZERO_WIDTH_SPACE = "\u200b"  # Binary 0
    ZERO_WIDTH_NON_JOINER = "\u200c"  # Binary 1

    # Signature marker to identify encoded content
    SIGNATURE = "EAIM"  # EncypherAI Metadata

    def __init__(self, secret_key: str = ""):
        """
        Initialize the encoder with a secret key for HMAC verification.

        Args:
            secret_key: Secret key used for HMAC verification
        """
        self.secret_key = secret_key

    def _bytes_to_zwc(self, data: bytes) -> str:
        """
        Convert bytes to zero-width characters.

        Args:
            data: Bytes to convert

        Returns:
            String of zero-width characters
        """
        result = []
        for byte in data:
            for i in range(8):
                bit = (byte >> i) & 1
                if bit == 0:
                    result.append(self.ZERO_WIDTH_SPACE)
                else:
                    result.append(self.ZERO_WIDTH_NON_JOINER)
        return "".join(result)

    def _zwc_to_bytes(self, zwc_str: str) -> bytes:
        """
        Convert zero-width characters back to bytes.

        Args:
            zwc_str: String of zero-width characters

        Returns:
            Decoded bytes
        """
        if not zwc_str:
            return b""

        result = bytearray()
        i = 0

        while i < len(zwc_str):
            byte = 0
            for bit_position in range(8):
                if i >= len(zwc_str):
                    break

                char = zwc_str[i]
                if char == self.ZERO_WIDTH_SPACE:
                    bit = 0
                elif char == self.ZERO_WIDTH_NON_JOINER:
                    bit = 1
                else:
                    # Skip non-ZWC characters
                    i += 1
                    continue

                byte |= bit << bit_position
                i += 1

            result.append(byte)

        return bytes(result)

    def _create_hmac(self, data: bytes) -> bytes:
        """
        Create HMAC for data verification.

        Args:
            data: Data to create HMAC for

        Returns:
            HMAC digest
        """
        return hmac.new(self.secret_key.encode(), data, hashlib.sha256).digest()[
            :8
        ]  # Use first 8 bytes of HMAC for compactness

    def _verify_hmac(self, data: bytes, signature: bytes) -> bool:
        """
        Verify HMAC signature.

        Args:
            data: Data to verify
            signature: HMAC signature to check against

        Returns:
            True if signature is valid, False otherwise
        """
        calculated = self._create_hmac(data)
        return hmac.compare_digest(calculated, signature)

    def encode_metadata(self, text: str, metadata: Dict[str, Any]) -> str:
        """
        Encode metadata into text using zero-width characters.

        Args:
            text: Text to encode metadata into
            metadata: Dictionary of metadata to encode

        Returns:
            Text with encoded metadata
        """
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = int(time.time())

        # Convert metadata to JSON and then to bytes
        metadata_json = json.dumps(metadata, separators=(",", ":"))
        metadata_bytes = metadata_json.encode("utf-8")

        # Create signature (HMAC)
        hmac_digest = self._create_hmac(metadata_bytes)

        # Add signature marker bytes
        signature_bytes = self.SIGNATURE.encode("utf-8")

        # Combine all bytes
        combined = signature_bytes + hmac_digest + metadata_bytes

        # Convert to base64 first for efficiency
        b64_data = base64.b64encode(combined)

        # Convert to zero-width characters
        zwc_encoded = self._bytes_to_zwc(b64_data)

        # Position the encoded data at start of the text
        # This could be customized based on preference
        return zwc_encoded + text

    def decode_metadata(self, text: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Extract and decode metadata from text.

        Args:
            text: Text that may contain encoded metadata

        Returns:
            Tuple of (metadata dict or None if not found/invalid, clean text)
        """
        # Extract zero-width characters
        zwc_chars = "".join(
            c for c in text if c in (self.ZERO_WIDTH_SPACE, self.ZERO_WIDTH_NON_JOINER)
        )

        if not zwc_chars:
            return None, text

        # Convert ZWC to bytes
        try:
            b64_data = self._zwc_to_bytes(zwc_chars)
            combined = base64.b64decode(b64_data)
        except Exception:
            # If decoding fails, return original text
            return None, text

        # Check for signature marker
        sig_len = len(self.SIGNATURE)
        if (
            len(combined) < sig_len
            or combined[:sig_len].decode("utf-8", errors="ignore") != self.SIGNATURE
        ):
            return None, text

        # Extract parts
        signature_offset = sig_len
        hmac_offset = signature_offset + 8

        signature = combined[signature_offset:hmac_offset]
        metadata_bytes = combined[hmac_offset:]

        # Verify HMAC
        if not self._verify_hmac(metadata_bytes, signature):
            return None, text

        # Decode metadata JSON
        try:
            metadata = json.loads(metadata_bytes.decode("utf-8"))
            # Remove all ZWC from text to get clean text
            clean_text = "".join(
                c
                for c in text
                if c not in (self.ZERO_WIDTH_SPACE, self.ZERO_WIDTH_NON_JOINER)
            )
            return metadata, clean_text
        except json.JSONDecodeError:
            return None, text

    def verify_text(self, text: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Verify if text contains valid encoded metadata.

        Args:
            text: Text to verify

        Returns:
            Tuple of (is_valid, metadata if valid else None, clean text)
        """
        metadata, clean_text = self.decode_metadata(text)
        return metadata is not None, metadata, clean_text
