# Metadata Encoding

This guide explains how EncypherAI embeds metadata into text using Unicode variation selectors, providing a detailed overview of the encoding process, available options, and best practices.

## How Metadata Encoding Works

EncypherAI embeds metadata into text using Unicode variation selectors (VS), which are special characters designed to modify the appearance of the preceding character. These selectors are typically invisible or have minimal visual impact, making them ideal for embedding metadata without changing the visible appearance of the text.

### The Encoding Process

1. **Metadata Preparation**: The metadata (a JSON-serializable dictionary) is converted to a binary format
2. **HMAC Generation**: A cryptographic signature is created to ensure data integrity
3. **Target Selection**: Suitable characters in the text are identified as targets for embedding
4. **Embedding**: Variation selectors representing the metadata and HMAC are inserted after target characters

![Metadata Encoding Process](../../assets/metadata-encoding-diagram.png)

## Metadata Targets

EncypherAI provides several options for where to embed metadata in text:

| Target Type | Description | Example |
|-------------|-------------|---------|
| `whitespace` | After spaces, tabs, and newlines | "Hello world" → "Hello␣world" (VS after space) |
| `punctuation` | After punctuation marks | "Hello, world!" → "Hello,␣world!" (VS after comma) |
| `first_letter` | After the first letter of each word | "Hello world" → "H␣ello w␣orld" (VS after H and w) |
| `last_letter` | After the last letter of each word | "Hello world" → "Hello␣ world␣" (VS after o and d) |
| `all_characters` | After any character | "Hello" → "H␣e␣l␣l␣o␣" (VS after each letter) |

The default target is `whitespace`, which provides a good balance between robustness and minimal impact on the text.

## Basic Usage

```python
from encypher.core.metadata_encoder import MetadataEncoder
import time

# Create a metadata encoder
encoder = MetadataEncoder()

# Sample text
text = "This is a sample text that will have metadata embedded within it."

# Create metadata
metadata = {
    "model_id": "gpt-4",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),  # Unix/Epoch timestamp
    "version": "1.0.0"
}

# Embed metadata
encoded_text = encoder.encode_metadata(text, metadata)

print("Original text:")
print(text)
print("\nEncoded text (looks identical but contains embedded metadata):")
print(encoded_text)

# Extract metadata
is_valid, extracted_metadata = encoder.extract_metadata(encoded_text)
print("\nExtracted metadata:")
print(extracted_metadata)

# Verify the text hasn't been tampered with
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
print(f"\nVerification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## HMAC Verification

EncypherAI uses HMAC (Hash-based Message Authentication Code) to ensure data integrity and detect tampering. When metadata is embedded, an HMAC signature is created using:

1. The metadata content
2. A secret key (either provided or randomly generated)

This signature is embedded alongside the metadata. When extracting metadata, the HMAC is verified to ensure the content hasn't been modified.

### Using a Custom Secret Key

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder with a custom secret key
encoder = MetadataEncoder(secret_key="your-secret-key")

# Embed metadata
encoded_text = encoder.encode_metadata(text, metadata)

# Verify using the same secret key
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
```

### Verification Process

The verification process involves:

1. Extracting the embedded metadata and HMAC
2. Recalculating the HMAC using the extracted metadata and the secret key
3. Comparing the recalculated HMAC with the embedded HMAC

If they match, the verification succeeds, indicating the content hasn't been tampered with.

## Advanced Configuration

### Custom Target Selection

You can specify where to embed metadata using either a string or the `MetadataTarget` enum:

```python
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import MetadataTarget

# Using a string
encoder1 = MetadataEncoder()
encoded_text1 = encoder1.encode_metadata(text, metadata, target="punctuation")

# Using the enum
encoder2 = MetadataEncoder()
encoded_text2 = encoder2.encode_metadata(text, metadata, target=MetadataTarget.PUNCTUATION)
```

### Metadata Size Considerations

The amount of metadata you can embed depends on:

1. The length of the text
2. The number of suitable targets in the text
3. The chosen target type

Each byte of metadata requires one suitable target character. If there aren't enough targets, an error will be raised.

```python
# Check if text has enough targets for metadata
from encypher.core.unicode_metadata import UnicodeMetadata, MetadataTarget
import json

# Estimate metadata size (in bytes)
metadata_json = json.dumps(metadata).encode('utf-8')
metadata_size = len(metadata_json)

# Find available targets
targets = UnicodeMetadata.find_targets(text, MetadataTarget.WHITESPACE)
available_targets = len(targets)

print(f"Metadata size: {metadata_size} bytes")
print(f"Available targets: {available_targets}")
print(f"Sufficient targets: {'Yes' if available_targets >= metadata_size else 'No'}")
```

### Handling Target Limitations

If you have limited targets but need to embed larger metadata:

1. **Use a more inclusive target type**: `all_characters` provides the most targets
2. **Reduce metadata size**: Include only essential information
3. **Increase text length**: Add more content to provide more targets
4. **Compress metadata**: Use shorter field names or compress values

## Comparing Target Types

Different target types offer different trade-offs between capacity and robustness:

| Target Type | Capacity | Robustness | Visual Impact | Use Case |
|-------------|----------|------------|---------------|----------|
| `whitespace` | Medium | High | Minimal | General purpose |
| `punctuation` | Low-Medium | High | Minimal | Short texts with punctuation |
| `first_letter` | Medium | Medium | Minimal | Texts with many words |
| `last_letter` | Medium | Medium | Minimal | Texts with many words |
| `all_characters` | High | Low | Minimal | Maximum capacity needed |

```python
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import UnicodeMetadata, MetadataTarget
import pandas as pd
import time

# Sample text
text = "This is a sample text that will have metadata embedded within it."

# Create metadata
metadata = {
    "model_id": "gpt-4",
    "timestamp": int(time.time()),  # Unix/Epoch timestamp
    "version": "1.0.0"
}

# Test different targets
results = []
for target in [t for t in MetadataTarget]:
    # Count available targets
    targets = UnicodeMetadata.find_targets(text, target)
    
    # Try to embed metadata
    encoder = MetadataEncoder()
    try:
        encoded = encoder.encode_metadata(text, metadata, target=target)
        success = True
    except ValueError:
        success = False
    
    results.append({
        "Target": target.value,
        "Available Targets": len(targets),
        "Embedding Successful": "Yes" if success else "No",
        "Encoded Length": len(encoded) if success else None,
        "Added Characters": len(encoded) - len(text) if success else None
    })

# Display results
pd.DataFrame(results)
```

## Tamper Detection

EncypherAI's HMAC verification can detect various types of tampering:

### Example: Detecting Modified Text

```python
from encypher.core.metadata_encoder import MetadataEncoder

# Create a metadata encoder
encoder = MetadataEncoder()

# Embed metadata
encoded_text = encoder.encode_metadata(text, metadata)

# Simulate tampering by modifying the text
tampered_text = encoded_text.replace("sample", "modified")

# Try to verify the tampered text
is_valid, extracted_metadata, clean_text = encoder.verify_text(tampered_text)
print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

### Example: Detecting Removed Metadata

```python
import re

# Simulate tampering by removing variation selectors
tampered_text = re.sub(r'[\uFE00-\uFE0F\U000E0100-\U000E01EF]', '', encoded_text)

# Try to extract metadata
try:
    is_valid, extracted = encoder.extract_metadata(tampered_text)
    print("Metadata found:", extracted)
except Exception as e:
    print("Metadata extraction failed:", str(e))
```

## Best Practices

1. **Choose appropriate targets**: Use `whitespace` for general purposes, `all_characters` for maximum capacity
2. **Limit metadata size**: Include only necessary information to minimize embedding overhead
3. **Use consistent secret keys**: Store and reuse secret keys for verification across systems
4. **Handle extraction errors**: Implement proper error handling for cases where metadata is missing or corrupted
5. **Verify before trusting**: Always verify the HMAC before trusting extracted metadata
6. **Test with your content**: Different content types may require different target strategies

## Implementation Details

### Unicode Variation Selectors

Unicode defines two ranges of variation selectors:

1. VS1-VS16: U+FE00 to U+FE0F (16 selectors)
2. VS17-VS256: U+E0100 to U+E01EF (240 selectors)

EncypherAI uses both ranges to encode a full byte (0-255).

### Metadata Format

The embedded metadata follows this structure:

1. **Header**: Identifies the metadata format and version
2. **Metadata Length**: The size of the metadata in bytes
3. **Metadata Content**: The JSON-serialized metadata
4. **HMAC**: The cryptographic signature for verification

### Encoding Algorithm

1. Convert metadata to JSON
2. Calculate HMAC using the metadata and secret key
3. Find suitable targets in the text
4. Convert each byte of the header, metadata, and HMAC to variation selectors
5. Insert variation selectors after target characters

### Decoding Algorithm

1. Scan the text for variation selectors
2. Convert variation selectors back to bytes
3. Parse the header to identify the format and version
4. Extract the metadata content and HMAC
5. Verify the HMAC using the extracted metadata and secret key

## Related Documentation

- [MetadataEncoder API Reference](../api-reference/metadata-encoder.md)
- [UnicodeMetadata API Reference](../api-reference/unicode-metadata.md)
- [Streaming Support Guide](./streaming.md)
- [Jupyter Notebook Examples](../examples/jupyter.md)
- [Streamlit Demo App](../examples/streamlit.md)
