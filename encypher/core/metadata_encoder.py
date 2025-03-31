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

    def __init__(self, hmac_secret_key: Optional[str] = None):
        """
        Initialize the encoder with a secret key for HMAC verification.

        Args:
            hmac_secret_key: Optional secret key used for HMAC verification
        """
        self.hmac_secret_key = hmac_secret_key

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

    def _create_hmac(self, data_bytes: bytes) -> str:
        """
        Create an HMAC signature for the given data.

        Args:
            data_bytes: The data to sign

        Returns:
            HMAC signature as a hex string
        """
        if self.hmac_secret_key is None:
            return ""

        return hmac.new(
            self.hmac_secret_key.encode("utf-8"),
            data_bytes,
            hashlib.sha256,
        ).hexdigest()

    def _verify_hmac(self, data: bytes, signature: str) -> bool:
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
        combined = signature_bytes + hmac_digest.encode("utf-8") + metadata_bytes

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
            Tuple of (metadata, clean_text) where metadata is None if no metadata was found
        """
        # Handle empty or very short text
        if not text:
            return None, text

        # Extract zero-width characters
        zwc_chars = ""
        clean_chars = []

        for char in text:
            if char in (self.ZERO_WIDTH_SPACE, self.ZERO_WIDTH_NON_JOINER):
                zwc_chars += char
            else:
                clean_chars.append(char)

        # If no zero-width characters found, return None
        if not zwc_chars:
            return None, text

        # Convert zero-width characters back to bytes
        try:
            b64_data = self._zwc_to_bytes(zwc_chars)
            combined = base64.b64decode(b64_data)
        except Exception:
            return None, text

        # Check signature
        sig_len = len(self.SIGNATURE)
        if (
            len(combined) < sig_len
            or combined[:sig_len].decode("utf-8", errors="ignore") != self.SIGNATURE
        ):
            return None, text

        # Extract parts
        signature_offset = sig_len
        hmac_offset = signature_offset + 64  # Changed from 8 to 64

        signature = combined[signature_offset:hmac_offset]
        metadata_bytes = combined[hmac_offset:]

        # Verify HMAC
        if not self._verify_hmac(metadata_bytes, signature.decode("utf-8")):
            return None, text

        # Decode metadata JSON
        try:
            metadata_json = metadata_bytes.decode("utf-8")
            metadata = json.loads(metadata_json)
            return metadata, "".join(clean_chars)
        except json.JSONDecodeError:
            return None, text

    def verify_text(
        self, text: str, hmac_secret_key: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Verify the integrity of text with embedded metadata using HMAC.

        Args:
            text: Text with embedded metadata
            hmac_secret_key: Optional secret key to override the instance's key

        Returns:
            Tuple of (is_valid, metadata if valid else None, clean text)
        """
        # Use provided key or instance key
        key = hmac_secret_key or self.hmac_secret_key

        # If no key is available, we can't verify
        if not key:
            return False, None, text

        # Use instance's decode_metadata method
        metadata, clean_text = self.decode_metadata(text)
        return metadata is not None, metadata, clean_text

    def extract_verified_metadata(
        self, text: str, hmac_secret_key: Optional[str] = None
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Extract metadata from text and verify its integrity using HMAC.

        Args:
            text: Text with embedded metadata
            hmac_secret_key: Optional HMAC secret key for verification

        Returns:
            Tuple containing the extracted metadata and a boolean indicating
            whether the metadata was successfully verified
        """
        # Use provided key or instance key
        key = hmac_secret_key or self.hmac_secret_key

        # If no key is available, extract without verification
        if not key:
            metadata, _ = self.decode_metadata(text)
            return metadata or {"model_id": "", "timestamp": None}, False

        # Use instance's verify_text method
        is_valid, metadata, _ = self.verify_text(text, key)
        return metadata or {"model_id": "", "timestamp": None}, is_valid
