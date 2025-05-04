# ruff: noqa: E501
import json
import os
import zlib
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple, cast

import pytest
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes

from encypher.core.crypto_utils import load_private_key, load_public_key  # Needed for manual verification check
from encypher.core.unicode_metadata import MetadataTarget, UnicodeMetadata

# --- Test Fixtures ---


@pytest.fixture(scope="module")
def key_pair_1() -> Tuple[PrivateKeyTypes, PublicKeyTypes]:
    """Load first key pair for tests from .env.test."""
    priv_pem = os.environ["PRIVATE_KEY_PEM"].replace("\\n", "\n")
    pub_pem = os.environ["PUBLIC_KEY_PEM"].replace("\\n", "\n")
    private_key = load_private_key(priv_pem)
    public_key = load_public_key(pub_pem)
    return private_key, public_key


@pytest.fixture(scope="module")
def key_pair_2() -> Tuple[PrivateKeyTypes, PublicKeyTypes]:
    """Load second key pair for tests from .env.test (reuse same for now)."""
    priv_pem = os.environ["PRIVATE_KEY_PEM"].replace("\\n", "\n")
    pub_pem = os.environ["PUBLIC_KEY_PEM"].replace("\\n", "\n")
    private_key = load_private_key(priv_pem)
    public_key = load_public_key(pub_pem)
    return private_key, public_key


@pytest.fixture
def sample_text() -> str:
    """Provides a much longer sample text with abundant targets for embedding metadata."""
    # This text needs to be significantly long and varied to ensure enough targets
    # of both whitespace and punctuation types for ~500 bytes of payload.
    # Let's add multiple paragraphs and different styles.
    paragraph1 = (
        "This is the first paragraph of a substantially longer sample text document, meticulously crafted for testing metadata embedding procedures. "
        "Our primary objective is to guarantee a sufficient quantity of 'target' characters—such as spaces, commas, periods, newlines (though maybe not embeddable), question marks, exclamation points, and semicolons—within this block. "
        "These targets are essential for successfully embedding the necessary metadata payload. This payload encompasses not merely the original data but also a robust cryptographic signature and associated signer identification. Punctuation, indeed, helps significantly! "
        "Consider these numbers: 123, 45.67, -890. Is variability not the spice of life? Yes! Yes, it is! "
    )
    paragraph2 = (
        "Moving to the second paragraph, we explore the intricacies of the embedding process itself. It involves meticulously scanning the text to identify suitable locations (the aforementioned targets). "
        "Once identified, the compressed and serialized metadata payload is encoded using specific Unicode variation selectors or similar techniques. Then, it's subtly inserted into the text at these target locations. "
        "The key is to make these insertions minimally disruptive to the original text's appearance and flow. Think about that; it's quite clever, right? What about a list? Item 1; Item 2; Item 3. "
    )
    paragraph3 = (
        "Finally, the third paragraph focuses on the verification stage. This critical step involves extracting the embedded bytes from their hidden locations within the text. "
        "The extracted bytes are then decoded, decompressed, and deserialized to reconstruct the original payload structure. The most crucial part follows: checking the cryptographic signature. "
        "This involves using the public key associated with the claimed signer ID (retrieved from a trusted provider) to validate the signature against the reconstructed payload data. If they match, the metadata is authentic! "
        "We sincerely hope this greatly extended version provides more than ample space for all test cases. Let's add one more: 987-654-3210. Success? We hope so..."
    )
    return f"{paragraph1}\n\n{paragraph2}\n\n{paragraph3}"


@pytest.fixture
def basic_metadata() -> Dict[str, Any]:
    """Sample basic metadata."""
    return {
        "model_id": "test_basic_model_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "custom_metadata": {"source": "test", "run_id": 123},
    }


@pytest.fixture
def manifest_metadata() -> Dict[str, Any]:
    """Sample manifest metadata."""
    now = datetime.now(timezone.utc)
    return {
        "claim_generator": "pytest-encypher/1.0",
        "timestamp": now.isoformat(),
        "actions": [
            {
                "action": "c2pa.created",
                "when": (now - timedelta(seconds=10)).isoformat(),
            },
            {
                "action": "c2pa.edited",
                "when": now.isoformat(),
                "softwareAgent": "pytest",
            },
        ],
        "ai_info": {"model_id": "test_manifest_model_v2", "version": "2.1-beta"},
        "custom_claims": {"project": "refactor", "verified": False},
    }


# --- Public Key Provider Fixture ---


@pytest.fixture
def public_key_provider(key_pair_1, key_pair_2) -> Callable[[str], Optional[PublicKeyTypes]]:
    """Provides a function to resolve signer IDs to public keys."""
    priv1, pub1 = key_pair_1
    priv2, pub2 = key_pair_2

    key_map = {
        "signer_1": pub1,
        "signer_2": pub2,
    }

    def resolver(signer_id: str) -> Optional[PublicKeyTypes]:
        return key_map.get(signer_id)

    return resolver


# --- Helper Function ---


def decode_and_deserialize(text: str) -> Optional[Dict[str, Any]]:
    """Helper to extract bytes, decompress, and deserialize for inspection."""
    # --- Updated ZWSP/ZWNJ Extraction --- 
    binary_string = UnicodeMetadata._extract_binary_string_from_zw_chars(text)
    if not binary_string:
        return None
    raw_bytes = UnicodeMetadata._binary_string_to_bytes(binary_string)
    # --- End Update --- 
    # raw_bytes = UnicodeMetadata.extract_bytes(text) # Deprecated VS logic
    if not raw_bytes:
        return None
    try:
        # Assume compression header if first byte is 'z'
        if raw_bytes.startswith(b"z"):
            decompressed_bytes = zlib.decompress(raw_bytes[1:])
        else:
            decompressed_bytes = raw_bytes
        # Cast the result of json.loads to Dict[str, Any] to satisfy mypy
        deserialized_data = json.loads(decompressed_bytes.decode("utf-8"))
        return cast(Dict[str, Any], deserialized_data)
    except (zlib.error, json.JSONDecodeError, UnicodeDecodeError):
        return None


class TestUnicodeMetadata:
    """Tests for the UnicodeMetadata class using signatures."""

    # --- Test Cases ---

    @pytest.mark.parametrize(
        "metadata_format, metadata_fixture",
        [("basic", "basic_metadata"), ("manifest", "manifest_metadata")],
    )
    def test_embed_verify_extract_success(
        self,
        key_pair_1,
        sample_text,
        metadata_format,
        metadata_fixture,
        public_key_provider,
        request,  # Required to use fixture names indirectly
    ):
        """Test successful embedding, verification, and extraction."""
        private_key, public_key = key_pair_1
        signer_id = "signer_1"
        metadata = request.getfixturevalue(metadata_fixture)

        # Store original payload for comparison (handle TypedDict conversion if needed)
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

        original_payload = metadata.copy()

        embedded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key,
            signer_id=signer_id,
            metadata_format=metadata_format,
            target=MetadataTarget.PUNCTUATION,  # Use punctuation
            **metadata,
        )

        assert embedded_text != sample_text

        # Add debug information
        print(f"\nEmbedded text length: {len(embedded_text)}")
        print(f"Original text length: {len(sample_text)}")

        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(embedded_text, public_key_provider)

        # Add more debug information
        print(f"Verification result: {is_valid}")
        print(f"Extracted signer ID: {extracted_signer_id}")
        print(f"Extracted payload: {extracted_payload}")

        assert is_valid is True
        assert extracted_signer_id == signer_id
        # Compare extracted payload with the original input metadata
        # Note: Timestamp formatting might differ slightly if not ISO string initially
        # We compare the core content
        assert extracted_payload is not None
        assert extracted_payload.get("format") == metadata_format

        # Compare relevant fields based on format
        if metadata_format == "basic":
            assert extracted_payload.get("model_id") == original_payload.get("model_id")
            assert "timestamp" in extracted_payload
            assert extracted_payload.get("custom_metadata") == original_payload.get("custom_metadata")
        elif metadata_format == "manifest":
            # Access nested manifest fields
            manifest_payload = extracted_payload.get("manifest", {})
            assert manifest_payload.get("claim_generator") == original_payload.get("claim_generator")
            # Compare actions - might need careful comparison due to structure/order
            assert manifest_payload.get("actions") == original_payload.get("actions")
            assert manifest_payload.get("ai_info") == original_payload.get("ai_info")
            assert manifest_payload.get("custom_claims") == original_payload.get("custom_claims")

    def test_embed_metadata_raises_error_if_timestamp_missing(
        self,
        key_pair_1,
        sample_text,
    ):
        """Test ValueError is raised if timestamp is not provided."""
        private_key, _ = key_pair_1
        signer_id = "signer_1"

        with pytest.raises(ValueError) as excinfo:
            UnicodeMetadata.embed_metadata(
                text=sample_text,
                private_key=private_key,
                signer_id=signer_id,
                metadata_format="basic",  # Can be basic or manifest
                model_id="test_model",
                timestamp=None,  # Explicitly missing
                custom_metadata={"data": "value"},
            )
        # Check if the error message is as expected
        assert "'timestamp' must be provided" in str(excinfo.value)

    def test_verify_wrong_key(
        self,
        key_pair_1,
        key_pair_2,
        sample_text,
        basic_metadata,
        public_key_provider,
    ):
        """Test verification failure when the wrong public key is used (via provider)."""
        private_key_signer1, _ = key_pair_1
        _, public_key_signer2 = key_pair_2
        signer_id = "signer_1"

        # Define a provider that returns the wrong key
        def wrong_key_provider(s_id: str) -> Optional[PublicKeyTypes]:
            if s_id == "signer_1":
                return cast(PublicKeyTypes, public_key_signer2)  # Return signer 2's key for signer 1's ID
            return None

        # Embed with key 1
        embedded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key_signer1,
            signer_id=signer_id,
            metadata_format="basic",
            target=MetadataTarget.PUNCTUATION,  # Use punctuation
            **basic_metadata,
        )

        # Verify with wrong key provider
        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(
            embedded_text,
            wrong_key_provider,
            return_payload_on_failure=True,  # Return payload even when verification fails
        )

        assert is_valid is False
        assert extracted_signer_id == signer_id
        assert extracted_payload is not None  # Payload is extracted, but verification fails

    def test_verify_tampered_data(
        self,
        key_pair_1,
        key_pair_2,
        sample_text,
        basic_metadata,
        public_key_provider,
    ):
        """Test verification failure when the embedded data is altered."""
        private_key_1, _ = key_pair_1
        private_key_2, _ = key_pair_2
        signer_id = "signer_1"

        # First, embed metadata with key_pair_1
        embedded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key_1,
            signer_id=signer_id,
            metadata_format="basic",
            target=MetadataTarget.PUNCTUATION,  # Use punctuation
            **basic_metadata,
        )

        # Create tampered text by re-embedding the same metadata with a different key
        # This simulates tampering with the data while keeping the same signer_id
        tampered_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key_2,  # Use a different key
            signer_id=signer_id,  # But claim to be the same signer
            metadata_format="basic",
            target=MetadataTarget.PUNCTUATION,
            **basic_metadata,
        )

        assert tampered_text != embedded_text

        # Verify the tampered text with the original signer's public key
        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(
            tampered_text,
            public_key_provider,
            return_payload_on_failure=True,  # Return payload even when verification fails
        )

        # Verification should fail due to tampered data (wrong key used)
        assert is_valid is False
        # Payload should still be extracted since we're using return_payload_on_failure=True
        assert extracted_payload is not None

    def test_verify_failure_wrong_key(
        self,
        key_pair_1,
        key_pair_2,
        sample_text,
        public_key_provider,
    ):
        """Test verification failure with the wrong public key."""
        private_key_1, _ = key_pair_1
        signer_id = "signer_2"  # ID associated with key_pair_2 in the provider

        encoded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key_1,
            signer_id=signer_id,  # Sign with key 1, but claim to be signer 2
            metadata_format="basic",
            model_id="wrong_key_test",
            timestamp=datetime.now(timezone.utc).isoformat(),
            target=MetadataTarget.PUNCTUATION,  # Use punctuation
        )

        # Verification should fail because signature doesn't match public key for signer_id
        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(encoded_text, public_key_provider)

        assert not is_valid
        assert extracted_payload is None

    def test_verify_failure_invalid_signature_format(
        self,
        key_pair_1,
        sample_text,
        public_key_provider,
    ):
        """Test verification failure with a malformed signature string."""
        private_key, _ = key_pair_1
        signer_id = "signer_1"
        encoded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key,
            signer_id=signer_id,
            metadata_format="basic",
            model_id="bad_sig_test",
            timestamp=datetime.now(timezone.utc).isoformat(),
            target=MetadataTarget.PUNCTUATION,  # Use punctuation
        )

        # With the new embedding approach, we'll just modify a few variation selectors
        # Find the first variation selector and change it
        for i, char in enumerate(encoded_text):
            code_point = ord(char)
            if UnicodeMetadata.VARIATION_SELECTOR_START <= code_point <= UnicodeMetadata.VARIATION_SELECTOR_END:
                # Replace this variation selector with a different one
                corrupted_text = encoded_text[:i] + chr(code_point + 1) + encoded_text[i + 1 :]
                break
            elif UnicodeMetadata.VARIATION_SELECTOR_SUPPLEMENT_START <= code_point <= UnicodeMetadata.VARIATION_SELECTOR_SUPPLEMENT_END:
                # Replace this variation selector with a different one
                corrupted_text = encoded_text[:i] + chr(code_point + 1) + encoded_text[i + 1 :]
                break
        else:
            # If no variation selectors found, just append an invalid one
            corrupted_text = encoded_text + chr(UnicodeMetadata.VARIATION_SELECTOR_START)

        # Verify the corrupted text
        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(corrupted_text, public_key_provider)

        assert not is_valid
        assert extracted_payload is None

    def test_verify_failure_unknown_signer_id(
        self,
        key_pair_1,
        sample_text,
        public_key_provider,
    ):
        """Test verification failure when signer_id is unknown to the provider."""
        private_key, _ = key_pair_1
        signer_id = "signer_unknown"  # This ID is not in the provider map

        encoded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key,
            signer_id=signer_id,
            metadata_format="basic",
            model_id="unknown_signer_test",
            timestamp=datetime.now(timezone.utc).isoformat(),
            target=MetadataTarget.PUNCTUATION,  # Use punctuation
        )

        # Verification should fail as provider returns None
        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(encoded_text, public_key_provider)

        assert not is_valid
        assert extracted_payload is None

    def test_verify_failure_key_mismatch(self, key_pair_1, sample_text):
        """Test verification failure when provider returns wrong key type."""
        private_key, public_key = key_pair_1  # Correctly unpack public_key
        signer_id = "signer_1"
        encoded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key,
            signer_id=signer_id,
            metadata_format="basic",
            model_id="key_mismatch_test",
            timestamp=datetime.now(timezone.utc).isoformat(),
            target=MetadataTarget.PUNCTUATION,  # Use punctuation
        )

        # Provider returns a private key instead of public
        def wrong_key_provider(s_id: str) -> Optional[PublicKeyTypes]:
            if s_id == "signer_1":
                return cast(PublicKeyTypes, private_key)  # Return private key for signer 1
            return None  # Original for others

        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(encoded_text, wrong_key_provider)

        assert not is_valid
        assert extracted_payload is None

    def test_verify_failure_provider_error(self, key_pair_1, sample_text):
        """Test verification failure when provider raises an exception."""
        private_key, _ = key_pair_1
        signer_id = "signer_1"
        encoded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key,
            signer_id=signer_id,
            metadata_format="basic",
            model_id="provider_error_test",
            timestamp=datetime.now(timezone.utc).isoformat(),
            target=MetadataTarget.PUNCTUATION,  # Use punctuation
        )

        # Provider raises an error
        def error_provider(s_id: str) -> Optional[PublicKeyTypes]:
            raise Exception("Mock provider error")

        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(encoded_text, error_provider)

        assert not is_valid
        assert extracted_payload is None

    def test_unicode_metadata_extract_metadata(self, sample_text, basic_metadata, key_pair_1):
        """Test extracting metadata without verification."""
        private_key, public_key = key_pair_1
        signer_id_to_use = "test-key-1"
        # Ensure timestamp is in basic_metadata fixture before using it
        if "timestamp" not in basic_metadata:
            basic_metadata["timestamp"] = datetime.now(timezone.utc).isoformat()
        metadata_to_embed = basic_metadata  # Use the basic_metadata fixture directly

        # Embed metadata - Corrected call
        encoded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key,
            signer_id=signer_id_to_use,  # Pass the signer_id
            metadata_format="basic",  # Specify format
            target=MetadataTarget.WHITESPACE,
            **metadata_to_embed,  # Unpack the metadata dictionary
        )

        # Extract metadata
        extracted_metadata = UnicodeMetadata.extract_metadata(encoded_text)
        assert extracted_metadata is not None, "Metadata should be extracted"
        # Check some key metadata fields (excluding signature/key_id if not needed)
        # Compare against metadata_to_embed
        assert extracted_metadata.get("model_id") == metadata_to_embed.get("model_id")
        assert extracted_metadata.get("timestamp") is not None  # Just check presence
        assert extracted_metadata.get("custom_metadata") == metadata_to_embed.get("custom_metadata")

    def test_unicode_metadata_extract_metadata_no_metadata(self, sample_text):
        """Test extracting metadata when none is present."""
        extracted_metadata = UnicodeMetadata.extract_metadata(sample_text)
        assert extracted_metadata is None, "Should return None when no metadata is embedded"

    def test_unicode_metadata_extract_metadata_corrupted(self, sample_text, basic_metadata, key_pair_1):
        """Test extracting metadata when the embedded data is corrupted."""
        private_key, public_key = key_pair_1
        signer_id_to_use = "test-key-1"

        # Ensure timestamp is included in the metadata
        metadata_to_embed = {**basic_metadata}
        if "timestamp" not in metadata_to_embed:
            metadata_to_embed["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Embed metadata
        encoded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key,
            signer_id=signer_id_to_use,
            metadata_format="basic",
            target=MetadataTarget.WHITESPACE,
            **metadata_to_embed,
        )

        # Create corrupted text by replacing some characters
        # This will corrupt any embedded variation selectors
        corrupted_text = ""
        for i, char in enumerate(encoded_text):
            # Replace every 10th character to corrupt the data
            if i % 10 == 0 and i > 0:
                corrupted_text += "X"
            else:
                corrupted_text += char

        # Try to extract metadata from the corrupted text
        extracted_metadata = UnicodeMetadata.extract_metadata(corrupted_text)
        assert extracted_metadata is None, "Should return None for corrupted data"

    def test_unicode_metadata_verify_with_manifest(self, manifest_metadata, key_pair_1, sample_text, public_key_provider):
        """Test verification with manifest metadata."""
        private_key, public_key = key_pair_1
        signer_id = "signer_1"

        encoded_text = UnicodeMetadata.embed_metadata(
            text=sample_text,
            private_key=private_key,
            signer_id=signer_id,
            metadata_format="manifest",
            **manifest_metadata,
        )

        # Verify the encoded text
        extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(encoded_text, public_key_provider)

        assert is_valid
        assert extracted_signer_id == signer_id
        assert extracted_payload is not None
        assert extracted_payload.get("format") == "manifest"
        # Access nested manifest fields
        manifest_payload = extracted_payload.get("manifest", {})
        assert manifest_payload.get("claim_generator") == manifest_metadata.get("claim_generator")
        assert manifest_payload.get("actions") == manifest_metadata.get("actions")
        assert manifest_payload.get("ai_info") == manifest_metadata.get("ai_info")
        assert manifest_payload.get("custom_claims") == manifest_metadata.get("custom_claims")

    @pytest.mark.skip(reason=("Test based on old embed_metadata signature (HMAC), incompatible " "with new signature-based method."))
    def test_embed_extract_metadata(self):
        pass

    @pytest.mark.skip(reason=("Test based on old embed_metadata signature (HMAC), incompatible " "with new signature-based method."))
    def test_custom_metadata(self):
        pass

    @pytest.mark.skip(reason=("Test based on old embed_metadata signature (HMAC), incompatible " "with new signature-based method."))
    def test_no_metadata_target(self):
        pass

    @pytest.mark.skip(reason=("Test based on old embed_metadata signature (HMAC), incompatible " "with new signature-based method."))
    def test_datetime_timestamp(self):
        pass

    @pytest.fixture
    def sample_text(self) -> str:
        """Provides a much longer sample text with abundant targets for embedding metadata."""
        # This text needs to be significantly long and varied to ensure enough targets
        # of both whitespace and punctuation types for ~500 bytes of payload.
        # Let's add multiple paragraphs and different styles.
        paragraph1 = (
            "This is the first paragraph of a substantially longer sample text document, meticulously crafted for testing metadata embedding procedures. "
            "Our primary objective is to guarantee a sufficient quantity of 'target' characters—such as spaces, commas, periods, newlines (though maybe not embeddable), question marks, exclamation points, and semicolons—within this block. "
            "These targets are essential for successfully embedding the necessary metadata payload. This payload encompasses not merely the original data but also a robust cryptographic signature and associated signer identification. Punctuation, indeed, helps significantly! "
            "Consider these numbers: 123, 45.67, -890. Is variability not the spice of life? Yes! Yes, it is! "
        )
        paragraph2 = (
            "Moving to the second paragraph, we explore the intricacies of the embedding process itself. It involves meticulously scanning the text to identify suitable locations (the aforementioned targets). "
            "Once identified, the compressed and serialized metadata payload is encoded using specific Unicode variation selectors or similar techniques. Then, it's subtly inserted into the text at these target locations. "
            "The key is to make these insertions minimally disruptive to the original text's appearance and flow. Think about that; it's quite clever, right? What about a list? Item 1; Item 2; Item 3. "
        )
        paragraph3 = (
            "Finally, the third paragraph focuses on the verification stage. This critical step involves extracting the embedded bytes from their hidden locations within the text. "
            "The extracted bytes are then decoded, decompressed, and deserialized to reconstruct the original payload structure. The most crucial part follows: checking the cryptographic signature. "
            "This involves using the public key associated with the claimed signer ID (retrieved from a trusted provider) to validate the signature against the reconstructed payload data. If they match, the metadata is authentic! "
            "We sincerely hope this greatly extended version provides more than ample space for all test cases. Let's add one more: 987-654-3210. Success? We hope so..."  # noqa: E501
        )
        return f"{paragraph1}\n\n{paragraph2}\n\n{paragraph3}"  # noqa: E501

    from tests.integration.test_llm_outputs import STREAMING_CHUNKS # Import test data

    def test_embed_extract_openai_chunk_whitespace_single_point(self, key_pair_1):
        """Tests embedding/extraction specifically on the problematic OpenAI chunk 1 scenario."""
        private_key, public_key = key_pair_1
        signer_id = "test_signer_complex"
        original_text = STREAMING_CHUNKS['openai'][0] # The problematic long chunk
        payload_dict = {"user_id": "user_123", "session_id": "session_abc", "timestamp": 1678886400}
        target = MetadataTarget.WHITESPACE
        distribute = False # Force single-point insertion

        print(f"\n--- Testing OpenAI Chunk 1 (Whitespace, Single-Point) ---")
        print(f"Original Text Length: {len(original_text)}")

        # Embed
        try:
            embedded_text = UnicodeMetadata.embed_metadata(
                text=original_text,
                private_key=private_key,
                signer_id=signer_id,
                payload_data=payload_dict,
                target=target,
                distribute_across_targets=distribute,
                payload_type="basic"
            )
            print(f"Embedded Text Length: {len(embedded_text)}")

            # --- DEBUG: Print snippet around the first whitespace --- 
            first_whitespace_index = -1
            for i, char in enumerate(original_text):
                if char.isspace():
                    first_whitespace_index = i
                    break
            if first_whitespace_index != -1:
                start_print = max(0, first_whitespace_index - 20)
                # Estimate end based on expected marker/payload length (crude)
                end_print = first_whitespace_index + 1 + 500 # Print first whitespace + 1 (insertion point) + estimate
                print(f"Snippet around first whitespace (index {first_whitespace_index}) after embedding:\n'''{embedded_text[start_print:end_print]}'''")
            else:
                print("Could not find first whitespace in original text for debug snippet.")
            # --- END DEBUG --- 

        except Exception as e:
            pytest.fail(f"Embedding failed unexpectedly: {e}")

        # Verify
        def public_key_provider(s_id):
            if s_id == signer_id:
                return public_key
            return None

        try:
            extracted_payload, is_valid, extracted_signer_id = UnicodeMetadata.verify_and_extract_metadata(
                text=embedded_text,
                public_key_provider=public_key_provider
            )
        except Exception as e:
            pytest.fail(f"Verification/Extraction failed unexpectedly: {e}")

        # Assertions
        assert is_valid is True, "Signature verification failed"
        assert extracted_signer_id == signer_id, f"Expected signer ID {signer_id}, got {extracted_signer_id}"
        assert isinstance(extracted_payload, BasicPayload), "Extracted payload is not BasicPayload"
        assert extracted_payload.data == payload_dict, "Extracted payload data does not match original"
        print("--- Test Passed ---")

    def test_binary_string_conversion():
        """Tests the conversion between binary strings and ZWSP/ZWNJ characters."""
        # Test cases
        test_cases = [
            ("", []),
            ("0", [0]),
            ("1", [1]),
            ("10", [1, 0]),
            ("11111111", [255]),
            ("10000000", [128]),
            ("01111111", [127]),
            ("10101010", [170]),
            ("11001100", [204]),
            ("11110000", [240]),
            ("00001111", [15]),
            ("00110011", [51]),
            ("01010101", [85]),
            ("01101010", [106]),
            ("10010101", [149]),
            ("10100110", [166]),
            ("11001001", [209]),
            ("11100111", [231]),
            ("00010001", [17]),
            ("00100010", [34]),
            ("01000011", [67]),
            ("01100001", [97]),
            ("10000010", [130]),
            ("10100000", [160]),
            ("11000001", [193]),
            ("11100000", [224]),
            ("00001001", [9]),
            ("00100100", [36]),
            ("01000111", [71]),
            ("01100101", [101]),
            ("10000110", [134]),
            ("10100100", [164]),
            ("11000101", [197]),
            ("11100100", [228]),
            ("00000101", [5]),
            ("00100001", [33]),
            ("01000011", [67]),
            ("01100001", [97]),
            ("10000010", [130]),
            ("10100000", [160]),
            ("11000001", [193]),
            ("11100000", [224]),
            ("00000011", [3]),
            ("00100000", [32]),
            ("01000001", [65]),
            ("01100000", [96]),
            ("10000000", [128]),
            ("10100000", [160]),
            ("11000000", [192]),
            ("11100000", [224]),
            ("00000001", [1]),
            ("00100000", [32]),
            ("01000000", [64]),
            ("01100000", [96]),
            ("10000000", [128]),
            ("10100000", [160]),
            ("11000000", [192]),
            ("11100000", [224]),
        ]

        for binary_string, expected_bytes in test_cases:
            # Convert binary string to bytes
            bytes_from_binary = UnicodeMetadata._binary_string_to_bytes(binary_string)
            assert bytes_from_binary == bytes(expected_bytes), f"Expected {expected_bytes}, got {bytes_from_binary}"

            # Convert bytes back to binary string
            binary_from_bytes = UnicodeMetadata._bytes_to_binary_string(bytes_from_binary)
            assert binary_from_bytes == binary_string, f"Expected {binary_string}, got {binary_from_bytes}"

    # --- ZWSP/ZWNJ Specific Tests ---
