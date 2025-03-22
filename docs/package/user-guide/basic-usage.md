# Basic Usage

This guide covers the fundamental operations of EncypherAI, providing a quick overview of how to embed, extract, and verify metadata in text.

## Installation

Before using EncypherAI, make sure it's installed in your environment:

```bash
uv pip install encypher-ai
```

For more installation options, see the [Installation Guide](../getting-started/installation.md).

## Importing EncypherAI

To use EncypherAI in your Python code, import the necessary components:

```python
# Import the core modules
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import UnicodeMetadata, MetadataTarget

# For streaming support
from encypher.streaming.handlers import StreamingHandler

# For timestamp handling
import time
```

## Creating a Metadata Encoder

The `MetadataEncoder` is the primary class for embedding and extracting metadata:

```python
# Create a metadata encoder with default settings
encoder = MetadataEncoder()

# Or with a custom secret key for HMAC verification
encoder_with_key = MetadataEncoder(secret_key="your-secret-key")
```

## Embedding Metadata

To embed metadata into text:

```python
# Sample text
text = "This is a sample text that will have metadata embedded within it."

# Create metadata dictionary
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
```

The encoded text will look identical to the original text to human readers, but it contains invisible metadata that can be extracted programmatically.

## Choosing Embedding Targets

You can specify where to embed metadata using the `target` parameter:

```python
# Embed metadata after whitespace (default)
whitespace_encoded = encoder.encode_metadata(text, metadata, target="whitespace")

# Embed metadata after punctuation
punctuation_encoded = encoder.encode_metadata(text, metadata, target="punctuation")

# Embed metadata after the first letter of each word
first_letter_encoded = encoder.encode_metadata(text, metadata, target="first_letter")

# Embed metadata after the last letter of each word
last_letter_encoded = encoder.encode_metadata(text, metadata, target="last_letter")

# Embed metadata after any character
all_chars_encoded = encoder.encode_metadata(text, metadata, target="all_characters")
```

You can also use the `MetadataTarget` enum:

```python
from encypher.core.unicode_metadata import MetadataTarget

# Embed metadata after whitespace
whitespace_encoded = encoder.encode_metadata(text, metadata, target=MetadataTarget.WHITESPACE)
```

## Extracting Metadata

To extract metadata from encoded text:

```python
# Extract metadata
try:
    is_valid, extracted_metadata = encoder.extract_metadata(encoded_text)
    if is_valid:
        print("Extracted metadata:")
        print(extracted_metadata)
    else:
        print("Metadata extraction failed: Invalid metadata")
except Exception as e:
    print("No metadata found or extraction failed:", str(e))
```

## Verifying Metadata

To verify that the text hasn't been tampered with:

```python
# Verify the text
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## Combined Extraction and Verification

For convenience, you can extract and verify metadata in a single operation:

```python
# Extract and verify metadata
try:
    is_valid, extracted_metadata, clean_text = encoder.extract_verified_metadata(encoded_text)
    if is_valid:
        print("✅ Verified metadata:", extracted_metadata)
    else:
        print("❌ Metadata found but verification failed:", extracted_metadata)
except Exception as e:
    print("No metadata found or extraction failed:", str(e))
```

## Working with Streaming Content

For content that arrives in chunks (e.g., from an LLM), use the `StreamingHandler`:

```python
from encypher.streaming.handlers import StreamingHandler
import time

# Create metadata
metadata = {
    "model_id": "gpt-4",
    "organization": "EncypherAI",
    "timestamp": int(time.time())  # Unix/Epoch timestamp
}

# Initialize the streaming handler
handler = StreamingHandler(
    metadata=metadata,
    target="whitespace",
    encode_first_chunk_only=True
)

# Process chunks as they arrive
chunks = [
    "This is the first chunk of text. ",
    "This is the second chunk. ",
    "And this is the final chunk."
]

processed_chunks = []
for chunk in chunks:
    # Process the chunk
    processed_chunk = handler.process_chunk(chunk)
    
    processed_chunks.append(processed_chunk)
    print(f"Processed chunk: {processed_chunk}")

# Combine all processed chunks
full_text = "".join(processed_chunks)

# Extract and verify the metadata
is_valid, extracted_metadata = UnicodeMetadata.extract_metadata(full_text)
if is_valid:
    print(f"Extracted metadata: {extracted_metadata}")
else:
    print("Metadata extraction failed")
```

## Integration with OpenAI

```python
from openai import OpenAI
from encypher.streaming.handlers import StreamingHandler
import time

# Initialize OpenAI client
client = OpenAI(api_key="your-api-key")

# Create metadata
metadata = {
    "model_id": "gpt-4",
    "organization": "EncypherAI",
    "timestamp": int(time.time())  # Unix/Epoch timestamp
}

# Initialize the streaming handler
handler = StreamingHandler(metadata=metadata)

# Create a streaming completion
completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a short paragraph about AI ethics."}
    ],
    stream=True
)

# Process each chunk
full_response = ""
for chunk in completion:
    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        
        # Process the chunk
        processed_chunk = handler.process_chunk(chunk=content)
        
        # Print and accumulate the processed chunk
        print(processed_chunk, end="", flush=True)
        full_response += processed_chunk

# Finalize the stream
handler.finalize()

print("\n\nStreaming completed!")
```

## Common Patterns

### Adding Timestamp Automatically

```python
import time

# Create metadata with automatic timestamp
def create_metadata(model_id="gpt-4", organization="EncypherAI"):
    return {
        "model_id": model_id,
        "organization": organization,
        "timestamp": int(time.time()),  # Unix/Epoch timestamp
        "version": "1.0.0"
    }

# Use the function
metadata = create_metadata()
encoded_text = encoder.encode_metadata(text, metadata)
```

### Handling Multiple Texts

```python
# Process multiple texts
texts = [
    "This is the first text.",
    "This is the second text.",
    "This is the third text."
]

# Embed metadata in all texts
encoded_texts = []
for i, text in enumerate(texts):
    # Create unique metadata for each text
    metadata = {
        "model_id": "gpt-4",
        "organization": "EncypherAI",
        "timestamp": int(time.time()),  # Unix/Epoch timestamp
        "text_id": i + 1
    }
    
    # Embed metadata
    encoded_text = encoder.encode_metadata(text, metadata)
    encoded_texts.append(encoded_text)
    
    print(f"Text {i+1} encoded with metadata")

# Later, extract and verify metadata
for i, encoded_text in enumerate(encoded_texts):
    try:
        is_valid, extracted_metadata = encoder.extract_metadata(encoded_text)
        if is_valid:
            print(f"Text {i+1}:")
            print(f"  Verified: {'✅' if is_valid else '❌'}")
            print(f"  Metadata: {extracted_metadata}")
        else:
            print(f"Text {i+1}: Metadata extraction failed: Invalid metadata")
    except Exception as e:
        print(f"Text {i+1}: No metadata found or extraction failed - {str(e)}")
```

### Error Handling

```python
def safe_process_text(text, encoder):
    """Safely process text with proper error handling."""
    result = {
        "has_metadata": False,
        "metadata": None,
        "verified": False,
        "error": None
    }
    
    try:
        # Try to extract metadata
        is_valid, extracted_metadata = encoder.extract_metadata(text)
        result["has_metadata"] = True
        result["metadata"] = extracted_metadata
        
        # Try to verify the text
        result["verified"] = is_valid
    except Exception as e:
        # No metadata found or extraction failed
        result["error"] = str(e)
    
    return result

# Example usage
result = safe_process_text(encoded_text, encoder)
if result["has_metadata"]:
    if result["verified"]:
        print("✅ Verified metadata:", result["metadata"])
    else:
        print("❌ Metadata found but verification failed:", result["metadata"])
else:
    print("No metadata found:", result["error"])
```

## Next Steps

Now that you understand the basics of EncypherAI, you can explore more advanced topics:

- [Metadata Encoding](./metadata-encoding.md) - Learn more about how metadata is embedded
- [Extraction and Verification](./extraction-verification.md) - Dive deeper into extracting and verifying metadata
- [Tamper Detection](./tamper-detection.md) - Understand how EncypherAI detects tampering
- [Streaming Support](./streaming.md) - Learn more about working with streaming content

For practical examples, check out:

- [Jupyter Notebook Examples](../examples/jupyter.md)
- [Streamlit Demo App](../examples/streamlit.md)
- [YouTube Demo](../examples/youtube-demo.md)
