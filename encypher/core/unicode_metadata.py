"""
Unicode Metadata Embedding Utility for EncypherAI

This module provides utilities for embedding metadata (model info, timestamps)
into text using Unicode variation selectors without affecting readability.
"""

import base64
import hashlib
import hmac
import json
import re
import warnings
from datetime import date, datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union, cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import dh, dsa, ec, ed448, ed25519, rsa, x448, x25519
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes
from deprecated import deprecated

from .constants import MetadataTarget
from .crypto_utils import BasicPayload, ManifestPayload, OuterPayload, serialize_payload, sign_payload, verify_signature
from .logging_config import logger


class UnicodeMetadata:
    """
    Utility class for embedding and extracting metadata using Unicode
    variation selectors.
    """

    # --- Character Constants ---
    # Variation selectors block (VS1-VS16: U+FE00 to U+FE0F)
    VARIATION_SELECTOR_START: int = 0xFE00
    VARIATION_SELECTOR_END: int = 0xFE0F

    # Variation selectors supplement (VS17-VS256: U+E0100 to U+E01EF)
    VARIATION_SELECTOR_SUPPLEMENT_START: int = 0xE0100
    VARIATION_SELECTOR_SUPPLEMENT_END: int = 0xE01EF

    # Zero-Width Characters (New approach)
    ZWSP = '\u200B'  # Zero-Width Space (Represents bit '1')
    ZWNJ = '\u200C'  # Zero-Width Non-Joiner (Represents bit '0')

    # Map bits to characters
    BIT_TO_CHAR = {'1': ZWSP, '0': ZWNJ}
    # Map characters back to bits
    CHAR_TO_BIT = {ZWSP: '1', ZWNJ: '0'}

    # --- Start/End Markers ---
    # Using sequences unlikely to appear naturally in payload bits
    START_MARKER_BIN = "11111111" # 8 ZWSPs
    END_MARKER_BIN = "00000000"   # 8 ZWNJs

    # Regular expressions for different target types
    REGEX_PATTERNS: Dict[MetadataTarget, re.Pattern] = {
        MetadataTarget.WHITESPACE: re.compile(r"(\s)"),
        MetadataTarget.PUNCTUATION: re.compile(r"([.,!?;:])"),
        MetadataTarget.FIRST_LETTER: re.compile(r"(\b\w)"),
        MetadataTarget.LAST_LETTER: re.compile(r"(\w\b)"),
        MetadataTarget.ALL_CHARACTERS: re.compile(r"(.)"),
    }

    @classmethod
    def to_variation_selector(cls, byte: int) -> Optional[str]:
        """
        (Deprecated: Use ZWSP/ZWNJ approach) Convert a byte to a variation selector character

        Args:
            byte: Byte value (0-255)

        Returns:
            Unicode variation selector character or None if byte is out of range
        """
        if 0 <= byte < 16:
            return chr(cls.VARIATION_SELECTOR_START + byte)
        elif 16 <= byte < 256:
            return chr(cls.VARIATION_SELECTOR_SUPPLEMENT_START + byte - 16)
        else:
            return None

    @classmethod
    def from_variation_selector(cls, code_point: int) -> Optional[int]:
        """
        (Deprecated: Use ZWSP/ZWNJ approach) Convert a variation selector code point to a byte

        Args:
            code_point: Unicode code point

        Returns:
            Byte value (0-255) or None if not a variation selector
        """
        if cls.VARIATION_SELECTOR_START <= code_point <= cls.VARIATION_SELECTOR_END:
            return code_point - cls.VARIATION_SELECTOR_START
        elif cls.VARIATION_SELECTOR_SUPPLEMENT_START <= code_point <= cls.VARIATION_SELECTOR_SUPPLEMENT_END:
            return (code_point - cls.VARIATION_SELECTOR_SUPPLEMENT_START) + 16
        else:
            return None

    @classmethod
    def encode(cls, emoji: str, text: str) -> str:
        """
        Encode text into an emoji using Unicode variation selectors

        Args:
            emoji: Base character to encode the text into
            text: Text to encode

        Returns:
            Encoded string with the text hidden in variation selectors
        """
        # Convert the string to UTF-8 bytes
        bytes_data = text.encode("utf-8")

        # Start with the emoji
        encoded = emoji

        # Add variation selectors for each byte
        for byte in bytes_data:
            vs = cls.to_variation_selector(byte)
            if vs:
                encoded += vs

        return encoded

    @classmethod
    def decode(cls, text: str) -> str:
        """
        Decode text from Unicode variation selectors

        Args:
            text: Text with embedded variation selectors

        Returns:
            Decoded text
        """
        # Extract bytes from variation selectors
        decoded: List[int] = []

        for char in text:
            code_point = ord(char)
            byte = cls.from_variation_selector(code_point)

            # If we've found a non-variation selector after we've started
            # collecting bytes, we're done
            if byte is None and len(decoded) > 0:
                break
            # If it's not a variation selector and we haven't started collecting
            # bytes yet, it's probably the base character (emoji), so skip it
            elif byte is None:
                continue

            decoded.append(byte)

        # Convert bytes back to text
        if decoded:
            return bytes(decoded).decode("utf-8")
        else:
            return ""

    @classmethod
    def extract_bytes(cls, text: str) -> bytes:
        """
        (Deprecated: Use ZWSP/ZWNJ approach) Extract bytes from Unicode variation selectors

        Args:
            text: Text with embedded variation selectors

        Returns:
            Bytes extracted from variation selectors
        """
        # Extract bytes from variation selectors
        decoded: List[int] = []

        for char in text:
            code_point = ord(char)
            byte = cls.from_variation_selector(code_point)

            # If we've found a non-variation selector after we've started
            # collecting bytes, we're done
            if byte is None and len(decoded) > 0:
                break
            # If it's not a variation selector and we haven't started collecting
            # bytes yet, it's probably the base character (emoji), so skip it
            elif byte is None:
                continue

            decoded.append(byte)

        # Convert bytes back to bytes object
        if decoded:
            return bytes(decoded)
        else:
            return b""

    @classmethod
    def _format_timestamp(cls, ts: Optional[Union[str, datetime, date, int, float]]) -> Optional[str]:
        """Helper to format various timestamp inputs into ISO 8601 UTC string.

        Args:
            ts: The timestamp input. Can be None, an ISO 8601 string,
                a datetime object, a date object, or an int/float epoch
                timestamp.

        Returns:
            The timestamp formatted as an ISO 8601 string in UTC (e.g., "YYYY-MM-DDTHH:MM:SSZ"),
            or None if the input was None.

        Raises:
            ValueError: If the input is an invalid timestamp value or format.
            TypeError: If the input type is not supported.
        """
        if ts is None:
            return None

        dt: Optional[datetime] = None
        if isinstance(ts, datetime):
            dt = ts
        elif isinstance(ts, date):
            # Assume start of day if only date is given
            dt = datetime.combine(ts, datetime.min.time())
        elif isinstance(ts, (int, float)):
            try:
                # Assume UTC if timezone not specified for epoch
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            except (OSError, ValueError):
                # Handle potential errors like invalid timestamp value
                raise ValueError(f"Invalid timestamp value: {ts}")
        elif isinstance(ts, str):
            try:
                # Attempt to parse ISO 8601 format
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                # If parsing fails, raise error - we need a consistent format
                raise ValueError(f"Invalid timestamp string format: {ts}. Use ISO 8601.")
        else:
            raise TypeError(f"Unsupported timestamp type: {type(ts)}")

        # Ensure timezone is UTC
        if dt.tzinfo is None:
            # Assume UTC if naive, or raise error if local timezone is ambiguous?
            # Let's assume UTC for simplicity here, but could be configurable.
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        # Format as ISO 8601 with 'Z' for UTC
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # Simplified ISO format

    @classmethod
    def find_targets(
        cls,
        text: str,
        target: Optional[Union[str, MetadataTarget]] = None,
    ) -> List[int]:
        """
        Find indices of characters in text where metadata can be embedded.

        Args:
            text: The text to find targets in.
            target: Where to embed metadata ('whitespace', 'punctuation', etc.,
                    or MetadataTarget enum).

        Returns:
            List of indices where metadata can be embedded.

        Raises:
            ValueError: If target is an invalid string.
        """
        if target is None:
            target_enum = MetadataTarget.WHITESPACE  # Keep track of the enum value
        elif isinstance(target, MetadataTarget):
            target_enum = target
        elif isinstance(target, str):
            try:
                target_enum = MetadataTarget(target.lower())  # Convert string to enum
            except ValueError:
                valid_targets = [t.name for t in MetadataTarget]
                raise ValueError(f"Invalid target: {target}. Must be one of {valid_targets}.")
        else:
            raise TypeError("'target' must be a string or MetadataTarget enum member.")

        # Use a try-except block for regex compilation robustness
        try:
            pattern = re.compile(cls.REGEX_PATTERNS[target_enum])
            matches = pattern.finditer(text)
            # Extract start indices, ensuring no duplicates if patterns overlap (unlikely but safe)
            indices = sorted(list({match.start() for match in matches}))
        except re.error as e:
            logger.error(f"Regex error for target '{target_enum.name}': {e}")
            raise ValueError(f"Invalid regex pattern for target '{target_enum.name}'.") from e

        return indices

    @classmethod
    def embed_metadata(
        cls,
        text: str,
        private_key: PrivateKeyTypes,
        signer_id: str,
        metadata_format: Literal["basic", "manifest"] = "basic",
        model_id: Optional[str] = None,
        timestamp: Optional[Union[str, datetime, date, int, float]] = None,
        target: Optional[Union[str, MetadataTarget]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
        claim_generator: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        ai_info: Optional[Dict[str, Any]] = None,
        custom_claims: Optional[Dict[str, Any]] = None,
        distribute_across_targets: bool = False,
    ) -> str:
        # DEBUG: Print the type of private_key for troubleshooting
        print(f"[DEBUG] embed_metadata: type(private_key) = {type(private_key)}")
        logger.debug(
            f"embed_metadata called with text (type={type(text).__name__}), signer_id='{signer_id}', "
            f"format='{metadata_format}', target='{target}', distribute={distribute_across_targets}"
        )
        # --- Start: Input Validation ---
        if not isinstance(text, str):
            logger.error("Input validation failed: 'text' is not a string.")
            raise TypeError("Input text must be a string")
        if not isinstance(private_key, ed25519.Ed25519PrivateKey):
            # Note: PrivateKeyTypes is broader, but we specifically need Ed25519 here for signing.
            logger.error("Input validation failed: 'private_key' is not an Ed25519PrivateKey instance.")
            raise TypeError("Input 'private_key' must be an Ed25519PrivateKey instance.")
        if not signer_id or not isinstance(signer_id, str):
            # Enhanced to check type as well
            logger.error("Input validation failed: 'signer_id' is not a non-empty string.")
            raise ValueError("A non-empty string 'signer_id' must be provided.")

        if timestamp is None:
            logger.error("Input validation failed: 'timestamp' is not provided.")
            raise ValueError("A 'timestamp' must be provided for metadata embedding.")

        # Validate target
        _target_enum = MetadataTarget.WHITESPACE  # Initialize with default
        if target is None:
            pass
        elif isinstance(target, MetadataTarget):
            _target_enum = target
        elif isinstance(target, str):
            try:
                _target_enum = MetadataTarget(target.lower())  # Convert string to enum
            except ValueError:
                valid_targets = [t.name for t in MetadataTarget]
                logger.error(f"Invalid target: {target}. Must be one of {valid_targets}.")
                raise ValueError(f"Invalid target: {target}. Must be one of {valid_targets}.")
        else:
             raise TypeError(f"Invalid target type: {type(target)}. Must be string or MetadataTarget enum.")
        # --- End Input Validation ---

        # 1. Prepare Inner Payload:
        formatted_timestamp = cls._format_timestamp(timestamp)

        # Warn if custom keys overlap with standard keys
        standard_keys = {"format", "signer_id", "timestamp"} | (set(custom_claims.keys()) if custom_claims else set())
        overlapping_keys = set(custom_metadata.keys()) & standard_keys if custom_metadata else set()
        if overlapping_keys:
            logger.warning(f"Custom metadata keys overlap with standard keys: {overlapping_keys}")

        if metadata_format == "manifest":
            inner_payload: Union[BasicPayload, ManifestPayload] = ManifestPayload(
                format=metadata_format,
                signer_id=signer_id,
                timestamp=formatted_timestamp,
                claim_generator=claim_generator,
                actions=actions,
                ai_info=ai_info,
                custom_claims=custom_claims,
            )
        else:  # Default to basic format
            inner_payload = BasicPayload(
                format="basic",
                signer_id=signer_id,
                timestamp=formatted_timestamp,
                model_id=model_id,
                custom_metadata=custom_metadata,
            )

        # 2. Serialize Inner Payload:
        try:
            inner_payload_bytes = serialize_payload(inner_payload)
        except Exception as e:
            logger.error(f"Error serializing inner payload: {e}", exc_info=True)
            raise ValueError(f"Error serializing inner payload: {e}") from e

        # 3. Sign Payload:
        try:
            signature_bytes = sign_payload(private_key, inner_payload_bytes)
            logger.info(f"Successfully signed payload (signature length: {len(signature_bytes)} bytes).")
        except Exception as e:
            logger.error(f"Error signing payload: {e}", exc_info=True)
            raise ValueError(f"Error signing payload: {e}") from e

        # 4. Create Outer Payload:
        outer_payload = OuterPayload(
            payload=inner_payload, signature=base64.urlsafe_b64encode(signature_bytes).decode("ascii")
        )
        outer_payload_bytes = serialize_payload(outer_payload)

        # --- NEW: Convert outer payload bytes to ZW chars ---
        # 5. Convert Outer Payload Bytes to Binary String:
        binary_string = cls._bytes_to_binary_string(outer_payload_bytes)

        # 6. Convert Binary String to ZWSP/ZWNJ Characters:
        metadata_chars = cls._binary_string_to_zw_chars(binary_string)

        # --- NEW: Add Start/End Markers --- 
        start_marker_chars = cls._binary_string_to_zw_chars(cls.START_MARKER_BIN)
        end_marker_chars = cls._binary_string_to_zw_chars(cls.END_MARKER_BIN)
        full_metadata_chars = start_marker_chars + metadata_chars + end_marker_chars
        # ----------------------------------

        # 7. Find Embedding Targets:
        target_indices = cls.find_targets(text, _target_enum)

        # Check if enough targets exist
        if len(target_indices) < len(full_metadata_chars):
            error_msg = (
                f"Not enough embeddable targets found in text for the required metadata size. "
                f"Required: {len(full_metadata_chars)}, Found: {len(target_indices)} for target type '{_target_enum.name}'."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 8. Embed Metadata Characters:
        text_list = list(text)
        chars_inserted = 0
        if distribute_across_targets:
            # Use targets needed for the full sequence including markers
            targets_to_use = target_indices[: len(full_metadata_chars)]
        else:
            # Embed all at the first target (if possible)
            targets_to_use = [target_indices[0]] * len(full_metadata_chars)
            # Check if embedding location is valid (not split mid-surrogate pair)
            first_target_index = target_indices[0]
            if 0 < first_target_index < len(text) and \
               0xD800 <= ord(text[first_target_index - 1]) <= 0xDBFF and \
               0xDC00 <= ord(text[first_target_index]) <= 0xDFFF:
                 raise ValueError("Embedding target index splits a surrogate pair, which is invalid.")

        # Sort targets in reverse to avoid messing up indices during insertion
        targets_to_use.sort(reverse=True)

        # Assign metadata chars to targets (reversed for insertion)
        full_metadata_chars_reversed = full_metadata_chars[::-1]

        current_target_index = -1
        inserted_count_at_target = 0

        if distribute_across_targets:
            for i, target_index in enumerate(targets_to_use):
                char_to_insert = full_metadata_chars_reversed[i]
                # Insert *after* the target character index
                text_list.insert(target_index + 1, char_to_insert)
                chars_inserted += 1
        else:
            # Insert all chars after the first target index
            first_target_index = targets_to_use[0] # All elements are the same
            for char_to_insert in full_metadata_chars_reversed:
                 text_list.insert(first_target_index + 1, char_to_insert)
            chars_inserted = len(full_metadata_chars)

        logger.info(
            f"Successfully embedded {chars_inserted} metadata characters (incl. markers) "
            f"({'distributed' if distribute_across_targets else 'single-point'}) for signer '{signer_id}'."
        )
        return "".join(text_list)

    @classmethod
    def _bytes_to_variation_selectors(cls, data: bytes) -> List[str]:
        """(Deprecated: Use ZWSP/ZWNJ approach) Convert bytes into a list of Unicode variation selector characters."""
        # Keep this method for now, but mark as deprecated or remove later
        selectors = [cls.to_variation_selector(byte) for byte in data]
        valid_selectors = [s for s in selectors if s is not None]
        if len(valid_selectors) != len(data):
            # This should theoretically not happen if input is bytes (0-255)
            logger.error("Invalid byte value encountered during selector conversion.")
            raise ValueError("Invalid byte value encountered during selector conversion.")
        return valid_selectors

    @classmethod
    def _bytes_to_binary_string(cls, data: bytes) -> str:
        """Convert bytes to a string of '0's and '1's."""
        return "".join(format(byte, '08b') for byte in data)

    @classmethod
    def _binary_string_to_bytes(cls, bin_string: str) -> bytes:
        """Convert a string of '0's and '1's back to bytes."""
        if len(bin_string) % 8 != 0:
            # This might happen if extraction was incomplete or data corrupted
            logger.warning(f"Binary string length {len(bin_string)} is not a multiple of 8. Padding or truncation might occur.")
            # Optional: Pad with '0's to the nearest multiple of 8, or raise error
            # For now, let's proceed, but be aware of potential issues.

        byte_list = []
        for i in range(0, len(bin_string), 8):
            byte_str = bin_string[i:i+8]
            if len(byte_str) < 8:
                 # Handle potential padding if needed, or log warning if unexpected
                 logger.warning(f"Incomplete byte '{byte_str}' at end of binary string. Skipping.")
                 continue # Or pad: byte_str = byte_str.ljust(8, '0')
            try:
                byte_list.append(int(byte_str, 2))
            except ValueError:
                logger.error(f"Invalid binary segment encountered: '{byte_str}'. Cannot convert to byte.")
                # Decide how to handle: raise error, skip, return partial? Returning empty for now.
                return b""
        return bytes(byte_list)

    @classmethod
    def _binary_string_to_zw_chars(cls, bin_string: str) -> List[str]:
        """Convert a binary string ('0's and '1's) to a list of ZWSP/ZWNJ characters."""
        zw_chars = [cls.BIT_TO_CHAR.get(bit) for bit in bin_string]
        # Filter out None in case of unexpected characters in bin_string (shouldn't happen)
        valid_zw_chars = [ch for ch in zw_chars if ch is not None]
        if len(valid_zw_chars) != len(bin_string):
            logger.error("Invalid bit encountered during ZW character conversion.")
            raise ValueError("Invalid bit encountered during ZW character conversion.")
        return valid_zw_chars

    @classmethod
    def _extract_binary_string_from_zw_chars(cls, text: str) -> str:
        """Extract a binary string ('0's and '1's) from ZWSP/ZWNJ characters embedded in text."""

        start_marker_zw_list = cls._binary_string_to_zw_chars(cls.START_MARKER_BIN)
        end_marker_zw_list = cls._binary_string_to_zw_chars(cls.END_MARKER_BIN)
        len_start = len(start_marker_zw_list)
        len_end = len(end_marker_zw_list)

        extracted_payload_zw_list = []
        current_match_buffer = []
        state = "LOOKING_FOR_START"  # LOOKING_FOR_START, COLLECTING_PAYLOAD, FINISHED

        for char_index, char in enumerate(text):
            is_zw_char = char in cls.CHAR_TO_BIT

            if not is_zw_char:
                # Non-ZW character resets any partial marker match when looking for start
                if state == "LOOKING_FOR_START":
                    current_match_buffer = []
                continue  # Ignore non-ZW chars mostly

            # Add current ZW char to buffer
            current_match_buffer.append(char)

            if state == "LOOKING_FOR_START":
                # Check if buffer ends with start marker
                if len(current_match_buffer) >= len_start:
                    if current_match_buffer[-len_start:] == start_marker_zw_list:
                        logger.info(f"[_extract_binary_string STATE] Found start marker ending at text index {char_index}.")
                        state = "COLLECTING_PAYLOAD"
                        current_match_buffer = []  # Clear buffer, start collecting payload
                    # Keep buffer size limited if not matching
                    elif len(current_match_buffer) > len_start:
                        current_match_buffer.pop(0)

            elif state == "COLLECTING_PAYLOAD":
                # Check if buffer ends with end marker
                if len(current_match_buffer) >= len_end:
                    if current_match_buffer[-len_end:] == end_marker_zw_list:
                        logger.info(f"[_extract_binary_string STATE] Found end marker ending at text index {char_index}.")
                        # Payload is everything collected *before* the end marker started matching
                        # The buffer currently holds payload + end_marker
                        extracted_payload_zw_list.extend(current_match_buffer[:-len_end])
                        state = "FINISHED"
                        break  # Found payload, stop scanning
                    else:
                        # Buffer is full enough to check, but didn't match end marker.
                        # Add the oldest char from buffer to payload, remove it from buffer.
                        extracted_payload_zw_list.append(current_match_buffer.pop(0))
                # else: Buffer not full enough to check for end marker yet, character was added above.

        if state != "FINISHED":
            logger.warning("Extraction scan finished without finding complete start->payload->end sequence.")
            return ""

        # Convert collected ZW chars (payload only) to binary string
        binary_string_list = []
        for char in extracted_payload_zw_list:
            bit = cls.CHAR_TO_BIT.get(char) # Should always be found if logic is correct
            if bit:
                binary_string_list.append(bit)
            else:
                # This indicates an issue, maybe non-ZW char crept in?
                logger.error(f"Non-ZW char found in collected payload sequence: {ord(char)}. This shouldn't happen.")
                return "" # Or raise error

        final_binary_string = "".join(binary_string_list)
        logger.info(f"[_extract_binary_string STATE] Returning Binary String (len={len(final_binary_string)}) based on state machine.")
        return final_binary_string

    @classmethod
    def verify_and_extract_metadata(
        cls,
        text: str,
        public_key_provider: Callable[[str], Optional[PublicKeyTypes]],
        return_payload_on_failure: bool = False,
    ) -> Tuple[Union[BasicPayload, ManifestPayload, None], bool, Optional[str]]:
        """
        Extracts embedded metadata, verifies its signature using a public key,
        and returns the payload, verification status, and signer ID.

        This verification process implements a C2PA-inspired approach for content
        authenticity verification, adapted specifically for plain-text environments
        where traditional file-based embedding methods aren't applicable. The manifest structure
        parallels C2PA's concepts of assertions, claim generators, and cryptographic integrity.

        Args:
            text: Text potentially containing embedded metadata.
            public_key_provider: A callable function that takes a signer_id (str)
                                 and returns the corresponding Ed25519PublicKey
                                 object or None if the key is not found.
                                 This resolver pattern enables flexible key management
                                 similar to C2PA's approach for signature verification.
            return_payload_on_failure: If True, return the payload even when verification fails.
                                      If False (default), return None for the payload when verification fails.

        Returns:
            A tuple containing:
            - The extracted inner payload (Dict[str, Any], basic or manifest) or None
              if extraction/verification fails (unless return_payload_on_failure is True).
            - Verification status (bool): True if the signature is valid, False otherwise.
            - The signer_id (str) found in the metadata, or None if extraction fails.

        Raises:
            TypeError: If public_key_provider returns an invalid key type.
            KeyError: If public_key_provider raises an error (e.g., key not found).
            InvalidSignature: If the signature verification process itself fails.
            Exception: Can propagate errors from base64 decoding or payload serialization.
        """
        logger.debug(f"verify_and_extract_metadata called for text (len={len(text)}).")
        # 1. Extract Outer Payload:
        outer_payload = cls._extract_outer_payload(text)
        logger.info(f"[verify_and_extract DEBUG] Extracted Outer Payload Dict: {outer_payload}")
        if outer_payload is None:
            logger.debug("No outer payload found during extraction.")
            return None, False, None

        # 2. Extract Key Components from Outer Payload:
        signer_id = outer_payload["signer_id"]
        inner_payload = outer_payload["payload"]
        signature_b64 = outer_payload["signature"]

        # Remove modification: The inner_payload should already contain 'format' if it was part of the original signed data.
        # Adding it here causes a mismatch during verification.
        # if "format" in outer_payload and "format" not in inner_payload:
        #     inner_payload["format"] = outer_payload["format"]

        # 3. Look Up Public Key:
        try:
            logger.debug(f"Calling public_key_provider for signer_id: '{signer_id}'")
            public_key = public_key_provider(signer_id)
        except Exception as e:
            # Provider function itself might raise an error
            logger.warning(
                f"public_key_provider raised an exception for signer_id '{signer_id}': {e}",
                exc_info=True,
            )
            return (
                inner_payload if return_payload_on_failure else None,
                False,
                signer_id,
            )

        if public_key is None:
            # Key not found for this signer
            logger.warning(f"Public key not found for signer_id: '{signer_id}'")
            return (
                inner_payload if return_payload_on_failure else None,
                False,
                signer_id,
            )
        if not (
            isinstance(public_key, ed25519.Ed25519PublicKey)
            or isinstance(public_key, rsa.RSAPublicKey)
            or isinstance(public_key, dsa.DSAPublicKey)
            or isinstance(public_key, dh.DHPublicKey)
            or isinstance(public_key, ec.EllipticCurvePublicKey)
            or isinstance(public_key, x25519.X25519PublicKey)
            or isinstance(public_key, x448.X448PublicKey)
            or isinstance(public_key, ed448.Ed448PublicKey)
        ):
            # Provider returned wrong type
            logger.error(f"public_key_provider returned invalid type ({type(public_key)}) for signer_id '{signer_id}'")
            return (
                inner_payload if return_payload_on_failure else None,
                False,
                signer_id,
            )

        # 4. Serialize Inner Payload (Canonical):
        try:
            canonical_payload_bytes = serialize_payload(dict(inner_payload))
        except Exception as e:
            # Failed to re-serialize the extracted payload
            logger.error(
                f"Failed to re-serialize inner payload for verification: {e}",
                exc_info=True,
            )
            return (
                inner_payload if return_payload_on_failure else None,
                False,
                signer_id,
            )

        # 5. Decode Signature:
        try:
            # Add padding if necessary for urlsafe_b64decode
            signature_bytes = base64.urlsafe_b64decode(signature_b64 + "=" * (-len(signature_b64) % 4))
        except (base64.binascii.Error, TypeError) as e:  # type: ignore [attr-defined]
            # Invalid base64 signature string
            logger.warning(f"Failed to decode base64 signature: {e}", exc_info=False)
            return (
                inner_payload if return_payload_on_failure else None,
                False,
                signer_id,
            )

        # 6. Verify Signature:
        try:
            is_valid = verify_signature(public_key, canonical_payload_bytes, signature_bytes)
        except TypeError as e:
            # E.g., verify_signature raises if key type is wrong (though checked above)
            logger.error(
                f"Signature verification failed due to key type mismatch: {e}",
                exc_info=True,
            )
            return (
                inner_payload if return_payload_on_failure else None,
                False,
                signer_id,
            )
        except InvalidSignature:
            # Signature verification failed
            logger.warning(f"Signature verification failed for signer_id '{signer_id}': Invalid signature.")
            return (
                inner_payload if return_payload_on_failure else None,
                False,
                signer_id,
            )
        except Exception as e:
            # Other unexpected errors during verification
            is_valid = False  # Treat unexpected verification errors as invalid
            logger.error(f"Unexpected error during signature verification: {e}", exc_info=True)

        # 7. Return Result:
        if is_valid:
            logger.info(f"Signature verified successfully for signer_id: '{signer_id}'")
            # Verification successful, return payload, status, and signer_id
            return inner_payload, True, signer_id
        else:
            # Verification failed
            logger.warning(f"Signature verification failed for signer_id: '{signer_id}' (reason determined above).")
            return (
                inner_payload if return_payload_on_failure else None,
                False,
                signer_id,
            )

    @classmethod
    def _extract_outer_payload(cls, text: str) -> Optional[OuterPayload]:
        """Extracts the raw OuterPayload dict from embedded ZWSP/ZWNJ characters."""
        # --- NEW: Extract using ZWSP/ZWNJ ---
        # 1. Extract Binary String:
        binary_string = cls._extract_binary_string_from_zw_chars(text)
        if not binary_string:
            logger.debug("No ZWSP/ZWNJ characters found in text.")
            return None

        # 2. Convert Binary String to Bytes:
        outer_payload_bytes = cls._binary_string_to_bytes(binary_string)
        if not outer_payload_bytes:
            logger.warning("Could not convert extracted binary string to bytes.")
            return None
        # --- End NEW ---

        # 3. Deserialize Outer JSON:
        try:
            outer_data = json.loads(outer_payload_bytes.decode("utf-8"))

            # Basic validation for OuterPayload structure
            if (
                not isinstance(outer_data, dict)
                or "payload" not in outer_data
                or not isinstance(outer_data["payload"], dict)
                or "signature" not in outer_data
                or not isinstance(outer_data["signature"], str)
            ):
                logger.warning(
                    "Extracted outer data does not match expected OuterPayload structure."
                )
                return None

            # Type cast for static analysis (actual validation happens during use)
            return cast(OuterPayload, outer_data)

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"Error decoding/parsing outer payload bytes: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing outer payload: {e}", exc_info=True)
            return None

    @classmethod
    def verify_metadata(
        cls,
        text: str,
        public_key_provider: Callable[[str], Optional[PublicKeyTypes]],
        return_payload_on_failure: bool = False,
    ) -> Tuple[Union[BasicPayload, ManifestPayload, None], bool, Optional[str]]:
        """
        Verify and extract metadata from text embedded using Unicode variation selectors and a public key.

        Args:
            text: Text with embedded metadata
            public_key_provider: A callable function that takes a signer_id (str)
                                 and returns the corresponding Ed25519PublicKey
                                 object or None if the key is not found.
            return_payload_on_failure: If True, return the payload even when verification fails.
                                      If False (default), return None for the payload when verification fails.

        Returns:
            A tuple containing:
            - The extracted inner payload (Dict[str, Any], basic or manifest) or None
              if extraction/verification fails (unless return_payload_on_failure is True).
            - Verification status (bool): True if the signature is valid, False otherwise.
            - The signer_id (str) found in the metadata, or None if extraction fails.

        Raises:
            TypeError: If public_key_provider returns an invalid key type.
            KeyError: If public_key_provider raises an error (e.g., key not found).
            InvalidSignature: If the signature verification process itself fails.
            Exception: Can propagate errors from base64 decoding or payload serialization.
        """
        # --- Input Validation ---
        if not isinstance(text, str):
            raise TypeError("Input 'text' must be a string.")
        if not text:
            # Avoid processing empty strings, return None early
            logger.debug("verify_metadata called with empty text, returning None.")
            return None, False, None
        if not callable(public_key_provider):
            raise TypeError("'public_key_provider' must be a callable function.")
        # --- End Input Validation ---

        # This method now simply calls the main verification method
        logger.debug("Forwarding call to verify_and_extract_metadata.")
        return cls.verify_and_extract_metadata(
            text,
            public_key_provider,
            return_payload_on_failure=return_payload_on_failure,
        )

    @classmethod
    def extract_metadata(cls, text: str) -> Union[BasicPayload, ManifestPayload, None]:
        """
        Extracts embedded metadata from text without verifying its signature.

        Finds the metadata markers, extracts the embedded bytes, decodes the
        outer JSON structure, and returns the inner 'payload' dictionary.

        Similar to how C2PA allows for inspection of manifest contents separate
        from verification, this method enables access to the embedded provenance
        information without cryptographic validation. This is useful for debugging,
        analysis, or when working with content where verification isn't the primary goal.
        When using the 'manifest' format, the extracted payload will contain C2PA-inspired
        structured provenance information.

        Args:
            text: The text containing potentially embedded metadata.

        Returns:
            The extracted inner metadata dictionary if found and successfully parsed,
            otherwise None.
        """
        # --- Input Validation ---
        if not isinstance(text, str):
            raise TypeError("Input 'text' must be a string.")
        # --- End Input Validation ---
        logger.debug(f"extract_metadata called for text (len={len(text)}).")

        outer_payload = cls._extract_outer_payload(text)

        if outer_payload and "payload" in outer_payload:
            # Ensure payload is a dict before returning
            payload = outer_payload["payload"]
            return payload if isinstance(payload, dict) else None
        return None

    # --- Deprecated Methods ---

    @classmethod
    @deprecated(
        version="1.1.0",
        reason="HMAC verification is deprecated. Use Ed25519 digital signatures via the primary verify_metadata method.",
    )
    def _verify_metadata_hmac_deprecated(cls, text: str, hmac_secret_key: str) -> Tuple[Dict[str, Any], bool]:  
        """
        Verify and extract metadata from text embedded using Unicode variation selectors and an HMAC secret key.

        Args:
            text: Text with embedded metadata
            hmac_secret_key: HMAC secret key for verification

        Returns:
            A tuple containing:
            - The extracted inner payload (Dict[str, Any], basic or manifest) or empty dict if extraction fails.
            - Verification status (bool): True if the signature is valid, False otherwise.
        """
        # --- Start: Input Validation ---
        if not isinstance(text, str):
            raise TypeError("Input 'text' must be a string.")
        if not isinstance(hmac_secret_key, str):
            raise TypeError("Input 'hmac_secret_key' must be a string.")
        # --- End Input Validation ---

        warnings.warn(
            "verify_metadata with HMAC is deprecated. Use Ed25519 signatures.",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.warning("Deprecated HMAC verify_metadata called.")

        binary_string = cls._extract_binary_string_from_zw_chars(text)
        if not binary_string:
            return {}, False
        outer_bytes = cls._binary_string_to_bytes(binary_string)
        if not outer_bytes:
            return {}, False

        # 3. Deserialize Outer JSON:
        try:
            outer_data = json.loads(outer_bytes.decode("utf-8"))

            # Minimal validation
            if not isinstance(outer_data, dict) or "payload" not in outer_data or "signature" not in outer_data:
                logger.warning("Deprecated HMAC: Extracted outer data missing required keys.")
                return {}, False

            inner_payload = outer_data.get("payload", {})
            signature = outer_data.get("signature", "")

            # Ensure payload is dict for serialization
            if not isinstance(inner_payload, dict):
                logger.warning("Deprecated HMAC: Extracted inner payload is not a dictionary.")
                return {}, False

            # 3. Re-serialize Payload for Verification:
            try:
                canonical_payload_bytes = json.dumps(inner_payload, separators=(",", ":")).encode("utf-8")
            except Exception as e:
                # Failed to re-serialize the extracted payload
                logger.error(
                    f"Failed to re-serialize inner payload for verification: {e}",
                    exc_info=True,
                )
                return {}, False

            # Generate expected HMAC signature
            hmac_obj = hmac.new(
                hmac_secret_key.encode("utf-8"),
                canonical_payload_bytes,
                hashlib.sha256,
            )
            expected_signature = hmac_obj.hexdigest()

            # 5. Compare Signatures:
            is_valid = hmac.compare_digest(expected_signature, signature)

            if is_valid:
                logger.info("Deprecated HMAC: Verification successful.")
                return inner_payload, True
            else:
                logger.warning("Deprecated HMAC: Verification failed.")
                return inner_payload, False  # Return payload even on failure

        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"Deprecated HMAC: Error decoding/parsing metadata: {e}", exc_info=True)
            return {}, False  # Return empty dict and False on error
        except Exception as e:
            logger.error(
                f"Deprecated HMAC: Unexpected error during verification: {e}",
                exc_info=True,
            )
            return {}, False
