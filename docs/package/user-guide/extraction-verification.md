# Metadata Extraction and Verification

This guide explains how to extract embedded metadata from text and verify its authenticity using EncypherAI's built-in HMAC verification system.

## Basic Extraction

Extracting metadata from text that has been encoded with EncypherAI is straightforward:

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder
encoder = MetadataEncoder()

# Text with embedded metadata
encoded_text = "This text contains embedded metadata that is invisible to human readers."

# Extract the metadata
try:
    is_valid, metadata = encoder.extract_metadata(encoded_text)
    if is_valid:
        print("Extracted metadata:", metadata)
    else:
        print("Metadata extraction failed: Invalid metadata")
except Exception as e:
    print("No metadata found or extraction failed:", str(e))
```

The `extract_metadata` method scans the text for a special sequence of Zero-Width Characters (ZWCs) at the beginning of the text that marks the start of the embedded data, reads the header information encoded using ZWCs immediately following the start marker to determine the length of the metadata and HMAC, reads the specified number of ZWC-encoded bytes representing the metadata payload and the HMAC signature, converts the ZWC sequences back into binary data for the metadata (usually JSON) and the HMAC, and returns the extracted metadata as a Python dictionary (after JSON deserialization).

## Understanding the Extraction Process

When extracting metadata, EncypherAI's `MetadataEncoder` performs the following steps:

1. **Locates Data Block**: Identifies a special sequence of Zero-Width Characters (ZWCs) at the beginning of the text that marks the start of the embedded data.
2. **Reads Header**: Parses header information encoded using ZWCs immediately following the start marker to determine the length of the metadata and HMAC.
3. **Extracts Content**: Reads the specified number of ZWC-encoded bytes representing the metadata payload and the HMAC signature.
4. **Decodes**: Converts the ZWC sequences back into binary data for the metadata (usually JSON) and the HMAC.
5. **Returns Metadata**: Returns the extracted metadata as a Python dictionary (after JSON deserialization).

![Metadata Extraction Process](../../assets/metadata-extraction-diagram.png)

## HMAC Verification

EncypherAI uses HMAC (Hash-based Message Authentication Code) to ensure data integrity and detect tampering. The verification process is separate from extraction and can be performed using the `verify_text` method:

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder
encoder = MetadataEncoder()

# Text with embedded metadata
encoded_text = "This text contains embedded metadata that is invisible to human readers."

# Verify the text
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")

# Use metadata only if verification succeeds
if is_valid:
    print("Extracted metadata:", extracted_metadata)
    print("Clean text:", clean_text)
else:
    print("Verification failed, metadata may be compromised")
```

## Using Custom Secret Keys

If the metadata was embedded using a custom secret key, you must use the same key for verification:

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder with the same secret key used for embedding
secret_key = "your-secret-key"
encoder = MetadataEncoder(secret_key=secret_key)

# Verify the text
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

If you use a different secret key, the verification will fail even if the metadata is intact.

## Combined Extraction and Verification

For convenience, you can extract and verify metadata in a single operation using the `verify_text` method:

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder
encoder = MetadataEncoder(secret_key="your-secret-key")

# Extract and verify metadata
try:
    is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
    if is_valid:
        print("✅ Verified metadata:", extracted_metadata)
    else:
        print("❌ Metadata found but verification failed")
except Exception as e:
    print("No metadata found or extraction failed:", str(e))
```

This method returns both the extracted metadata and a boolean indicating whether the verification succeeded.

## Understanding Verification Failures

Verification can fail for several reasons:

1. **Content Modification**: The text has been modified after metadata was embedded
2. **Incorrect Secret Key**: The wrong secret key is being used for verification
3. **Metadata Corruption**: The embedded metadata has been corrupted
4. **Data Block Alteration**: The prepended block containing metadata/HMAC (marked by Zero-Width Characters) has been altered or removed.

### Example: Detecting Modified Text

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder
encoder = MetadataEncoder()

# Original text with embedded metadata
original_encoded_text = "This text contains embedded metadata."

# Simulate tampering by modifying the text
tampered_text = original_encoded_text.replace("contains", "has")

# Try to verify the tampered text
is_valid, extracted_metadata, clean_text = encoder.verify_text(tampered_text)
print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## Handling Extraction Errors

When working with text that may or may not contain metadata, it's essential to handle potential extraction errors:

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder
encoder = MetadataEncoder()

# Function to safely extract metadata
def safe_extract_metadata(text):
    try:
        # Try to extract and verify metadata
        is_valid, extracted_metadata, clean_text = encoder.verify_text(text)
        
        return {
            "has_metadata": True,
            "metadata": extracted_metadata,
            "verified": is_valid,
            "clean_text": clean_text
        }
    except Exception as e:
        # No metadata found or extraction failed
        return {
            "has_metadata": False,
            "metadata": None,
            "verified": False,
            "clean_text": text,
            "error": str(e)
        }

# Example usage
result = safe_extract_metadata(encoded_text)
if result["has_metadata"]:
    if result["verified"]:
        print("✅ Verified metadata:", result["metadata"])
    else:
        print("❌ Metadata found but verification failed:", result["metadata"])
else:
    print("No metadata found:", result.get("error", "Unknown error"))
```

## Batch Processing

For processing multiple texts, you can use a batch approach:

```python
from encypher.core.metadata_encoder import MetadataEncoder
import pandas as pd

# Create a metadata encoder
encoder = MetadataEncoder()

# Sample texts
texts = [
    "This text contains embedded metadata.",
    "This text also contains embedded metadata, but different.",
    "This text doesn't contain any metadata."
]

# Process all texts
results = []
for i, text in enumerate(texts):
    result = {
        "text_id": i,
        "text": text[:50] + "..." if len(text) > 50 else text,
        "has_metadata": False,
        "verified": False,
        "metadata": None,
        "error": None
    }
    
    try:
        # Try to extract and verify metadata
        is_valid, extracted_metadata, clean_text = encoder.verify_text(text)
        
        result["has_metadata"] = True
        result["verified"] = is_valid
        result["metadata"] = extracted_metadata
    except Exception as e:
        # No metadata found or extraction failed
        result["error"] = str(e)
    
    results.append(result)

# Convert to DataFrame for easier analysis
df = pd.DataFrame(results)
print(df[["text_id", "has_metadata", "verified"]].to_string(index=False))
```

## Advanced: Verification with External Keys

In some scenarios, you might want to verify text using a key that's stored externally:

```python
from encypher.core.metadata_encoder import MetadataEncoder
import os
from cryptography.fernet import Fernet

# Function to get or create a secret key
def get_secret_key(key_file="secret_key.key"):
    if os.path.exists(key_file):
        # Load existing key
        with open(key_file, "rb") as f:
            return f.read()
    else:
        # Generate new key
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        return key

# Get the secret key
secret_key = get_secret_key()

# Create a metadata encoder with the secret key
encoder = MetadataEncoder(secret_key=secret_key)

# Verify text
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## Implementation Details

### HMAC Verification Process

The verification process involves:

1. Extracting the embedded metadata and HMAC
2. Recalculating the HMAC using the extracted metadata and the secret key
3. Comparing the recalculated HMAC with the embedded HMAC

If they match, the verification succeeds, indicating the content hasn't been tampered with.

### Metadata Format

The embedded metadata follows this structure:

1. **Header**: Identifies the metadata format and version
2. **Metadata Length**: The size of the metadata in bytes
3. **Metadata Content**: The JSON-serialized metadata
4. **HMAC**: The cryptographic signature for verification

### Handling Unicode and Encoding Issues

When working with text from various sources, you might encounter encoding issues:

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder
encoder = MetadataEncoder()

# Function to safely handle text with potential encoding issues
def safe_process_text(text):
    # Ensure text is properly encoded as UTF-8
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    
    # Replace any problematic characters
    text = ''.join(c if ord(c) < 65536 else ' ' for c in text)
    
    # Try to extract and verify metadata
    try:
        is_valid, extracted_metadata, clean_text = encoder.verify_text(text)
        return extracted_metadata, is_valid
    except Exception as e:
        return None, False

# Example usage
metadata, is_valid = safe_process_text(encoded_text)
```

## Best Practices

1. **Always verify before trusting**: Use `verify_text` before relying on extracted metadata
2. **Handle extraction errors**: Implement proper error handling for cases where metadata is missing or corrupted
3. **Use consistent secret keys**: Store and reuse secret keys for verification across systems
4. **Combine extraction and verification**: Use `verify_text` for a streamlined approach
5. **Consider key management**: Implement secure storage for secret keys
6. **Process in batches**: Use batch processing for efficiency when handling multiple texts

## Common Use Cases

### Content Authentication

```python
from encypher.core.metadata_encoder import MetadataEncoder

def authenticate_content(text, expected_source):
    """Authenticate content based on embedded metadata."""
    encoder = MetadataEncoder()
    
    try:
        # Extract and verify metadata
        is_valid, extracted_metadata, clean_text = encoder.verify_text(text)
        
        if not is_valid:
            return False, "Verification failed, content may be tampered"
        
        # Check source in metadata
        if extracted_metadata.get("organization") != expected_source:
            return False, f"Content source mismatch: expected {expected_source}, got {extracted_metadata.get('organization')}"
        
        return True, extracted_metadata
    except Exception as e:
        return False, f"Authentication failed: {str(e)}"

# Example usage
is_authentic, result = authenticate_content(encoded_text, "EncypherAI")
if is_authentic:
    print("✅ Content authenticated:", result)
else:
    print("❌ Authentication failed:", result)
```

### Timestamp Verification

```python
from encypher.core.metadata_encoder import MetadataEncoder
from datetime import datetime, timezone
import dateutil.parser

def verify_content_age(text, max_age_hours=24):
    """Verify content is not older than specified age."""
    encoder = MetadataEncoder()
    
    try:
        # Extract and verify metadata
        is_valid, extracted_metadata, clean_text = encoder.verify_text(text)
        
        if not is_valid:
            return False, "Verification failed, content may be tampered"
        
        # Check timestamp in metadata
        if "timestamp" not in extracted_metadata:
            return False, "No timestamp in metadata"
        
        # Parse timestamp
        timestamp = dateutil.parser.parse(extracted_metadata["timestamp"])
        
        # Calculate age
        now = datetime.now(timezone.utc)
        age_hours = (now - timestamp).total_seconds() / 3600
        
        if age_hours > max_age_hours:
            return False, f"Content too old: {age_hours:.1f} hours (max {max_age_hours})"
        
        return True, f"Content age: {age_hours:.1f} hours"
    except Exception as e:
        return False, f"Verification failed: {str(e)}"

# Example usage
is_recent, result = verify_content_age(encoded_text, max_age_hours=48)
if is_recent:
    print("✅ Content is recent:", result)
else:
    print("❌ Content is too old:", result)
```

## Related Documentation

- [MetadataEncoder API Reference](../api-reference/metadata-encoder.md)
- [Metadata Encoding Guide](./metadata-encoding.md)
- [Streaming Support Guide](./streaming.md)
- [Jupyter Notebook Examples](../examples/jupyter.md)
- [Streamlit Demo App](../examples/streamlit.md)
