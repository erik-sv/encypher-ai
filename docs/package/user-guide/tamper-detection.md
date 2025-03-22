# Tamper Detection

One of EncypherAI's key security features is its ability to detect when AI-generated content has been tampered with. This is achieved through HMAC (Hash-based Message Authentication Code) verification.

## How HMAC Verification Works

When metadata is embedded in text, EncypherAI creates an HMAC signature using:

1. The metadata content
2. A secret key known only to the encoder/verifier

This signature is embedded alongside the metadata. When the content is later verified:

- The same secret key must be used
- The metadata must not have been altered
- The text content must not have been modified

If any of these conditions are not met, verification will fail, indicating that tampering has occurred.

## Implementation Details

The HMAC generation and verification process uses the following approach:

```python
import hmac
import hashlib
import json

def create_hmac(data_bytes, secret_key):
    """Create an HMAC signature for the provided data."""
    return hmac.new(
        secret_key.encode('utf-8'),
        data_bytes,
        hashlib.sha256
    ).hexdigest()

# When embedding metadata
metadata_bytes = json.dumps(metadata).encode('utf-8')
hmac_signature = create_hmac(metadata_bytes, secret_key)

# When verifying
extracted_signature = # (from embedded data)
recalculated_signature = create_hmac(metadata_bytes, secret_key)
is_valid = hmac.compare_digest(extracted_signature, recalculated_signature)
```

## Preventing Tampering Attacks

EncypherAI protects against several types of attacks:

### 1. Content Modification

If someone modifies the visible text content while preserving the invisible metadata:

```python
from encypher.core.metadata_encoder import MetadataEncoder
import time

# Original with metadata
encoder = MetadataEncoder(secret_key="your-secure-secret-key")
metadata = {"model_id": "gpt-4", "timestamp": int(time.time())}
encoded_text = encoder.encode_metadata("This is the original AI-generated content.", metadata)

# Modified text (with preserved metadata)
tampered_text = "This has been changed but still has the metadata."

# Verification will fail
is_valid, _, _ = encoder.verify_text(tampered_text)  # is_valid will be False
```

### 2. Metadata Forgery

If an attacker tries to create their own metadata with a different key:

```python
from encypher.core.metadata_encoder import MetadataEncoder
import time

# Attacker creates their own metadata
attacker_encoder = MetadataEncoder(secret_key="different-key")
fake_metadata = {"model_id": "fake-model", "timestamp": int(time.time())}
fake_encoded_text = attacker_encoder.encode_metadata("This is fake content.", fake_metadata)

# Verification with the correct key will fail
original_encoder = MetadataEncoder(secret_key="original-key")
is_valid, _, _ = original_encoder.verify_text(fake_encoded_text)  # is_valid will be False
```

## Example Usage

Here's how to implement tamper detection in your application:

```python
from encypher.core.metadata_encoder import MetadataEncoder
import time

# Initialization
encoder = MetadataEncoder(secret_key="your-secure-secret-key")

# Embedding metadata
original_text = "Content authenticity is crucial in the age of AI-generated media."
metadata = {"model_id": "gpt-4", "timestamp": int(time.time())}
encoded_text = encoder.encode_metadata(original_text, metadata)

# Verifying untampered text
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
if is_valid:
    print("✅ Verification successful!")
    print(f"Metadata: {extracted_metadata}")
else:
    print("🚨 Tampering detected!")

# Simulating tampering by modifying text
tampered_text = encoded_text.replace("authenticity", "integrity")
is_valid, extracted_metadata, clean_text = encoder.verify_text(tampered_text)
if not is_valid:
    print("🚨 Tampering detected! The content has been modified.")
```

## Best Practices

To ensure effective tamper detection:

1. **Secure your secret key**:
   - Store it in environment variables or a secure vault
   - Rotate keys periodically
   - Never expose keys in client-side code

2. **Implement additional verification**:
   - Check timestamps are recent
   - Verify model IDs match expected values
   - Validate organization fields

3. **Handle verification failures gracefully**:
   - Log verification failures with relevant context
   - Consider implementing rate limiting for verification attempts
   - Provide clear user feedback when tampering is detected

## Reference Implementation

For a complete demonstration of tamper detection, see the [YouTube Demo Script](../examples/youtube-demo.md) which provides an interactive example of how tampering is detected in EncypherAI.
