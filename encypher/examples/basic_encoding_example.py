import json
import os
from encypher.core.unicode_metadata import UnicodeMetadata
from cryptography.hazmat.primitives.asymmetric import ed25519
from datetime import datetime, timezone

# --- Configuration ---
# Define the metadata to encode
example_metadata = {
    "source": "Example Script",
    "timestamp": "2025-05-03T19:45:00Z",
    "model": "ExampleModel_v1.0",
    "data_version": "1.1",
    "custom_info": {
        "purpose": "Demonstration of basic encoding",
        "user": "developer"
    }
}

# Define the sentences to encode
sentence1 = "This is the first sentence containing hidden metadata."
sentence2 = "Here is the second sentence, also with embedded information."

# Define the output filename
output_filename = "encoded_output.txt"

# Define a placeholder signer ID (required by the method)
signer_id = "example_key_001"

# --- Encoding Process ---

# Generate a private key (required by embed_metadata)
# In a real scenario, load this securely, don't generate every time.
private_key = ed25519.Ed25519PrivateKey.generate()

# Initialize the metadata handler
metadata_encoder = UnicodeMetadata()

# Get current timestamp (mandatory for embed_metadata)
current_timestamp = datetime.now(timezone.utc).isoformat()

# Encode metadata into the sentences using correct signature
encoded_sentence1 = metadata_encoder.embed_metadata(
    sentence1,           # text (pos 1)
    private_key,         # private_key (pos 2)
    signer_id,           # signer_id (pos 3)
    timestamp=current_timestamp, # timestamp (keyword, mandatory)
    custom_metadata=example_metadata # custom_metadata (keyword)
)
encoded_sentence2 = metadata_encoder.embed_metadata(
    sentence2,           # text (pos 1)
    private_key,         # private_key (pos 2)
    signer_id,           # signer_id (pos 3)
    timestamp=current_timestamp, # timestamp (keyword, mandatory)
    custom_metadata=example_metadata # custom_metadata (keyword)
)

# Combine the encoded sentences
full_encoded_text = encoded_sentence1 + "\n" + encoded_sentence2

# --- Save to File ---

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, output_filename)

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_encoded_text)
    print(f"Successfully encoded metadata into sentences.")
    print(f"Output saved to: {output_path}")

    # --- Verification (Using verify_metadata) ---
    # Define a simple resolver function to provide the public key
    def example_public_key_resolver(key_id_to_resolve):
        if key_id_to_resolve == signer_id:
            # In a real app, fetch the key securely based on key_id
            return private_key.public_key()
        return None

    # Let's read it back and verify the first sentence's metadata
    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Verify metadata (includes signature check)
    verified_metadata_s1, verification_result_s1, _signer_id = metadata_encoder.verify_metadata(
        lines[0].strip(),
        public_key_provider=example_public_key_resolver # Corrected argument name
    )
    # Deprecated: extracted_metadata_s1 = metadata_encoder.extract_metadata(lines[0].strip())

    print("\n--- Verification --- (First Sentence)")
    # Use the verification status bool directly
    print(f"Verification Result: {'SUCCESS' if verification_result_s1 else 'FAILURE'}")

    if verified_metadata_s1:
        print("Successfully verified and extracted metadata:")
        # The verified metadata might be structured differently (e.g., under a 'payload' key)
        # depending on the 'basic' format structure. Let's print the whole thing.
        print(json.dumps(verified_metadata_s1, indent=2))

        # Check if the original custom data is present
        # Adjust the access path based on actual structure if needed
        payload = verified_metadata_s1.get("payload", verified_metadata_s1)
        if payload.get("custom_metadata", {}).get("source") == example_metadata["source"]:
            print("\nSource field matches the original metadata.")
        else:
            print("\nSource field does NOT match or is not found in expected structure!")
    else:
        print("Could not verify or extract metadata from the first sentence.")

except IOError as e:
    print(f"Error writing to file {output_path}: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
