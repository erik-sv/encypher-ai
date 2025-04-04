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
    "version": "1.1.0"
}

# Embed metadata
encoded_text = encoder.encode_metadata(text, metadata)

print("Original text:")
print(text)
print("\nEncoded text (looks identical but contains invisible zero-width characters that encode the metadata):")
print(encoded_text)

The encoded text will look identical to the original text to human readers, but it contains invisible metadata that can be extracted programmatically.

*Note: For target-based embedding (whitespace, punctuation etc.), use `UnicodeMetadata` instead.*

## Extracting Metadata

To extract metadata from encoded text (without verification):

```python
# Extract metadata using decode_metadata
# Returns: (metadata_dict | None, clean_text)
extracted_metadata, clean_text = encoder.decode_metadata(encoded_text)

if extracted_metadata:
    print("Extracted metadata:")
    print(extracted_metadata)
    print("Clean text:")
    print(clean_text)
else:
    print("No metadata found or failed to decode.")
```

## Verifying Metadata

To verify that the text hasn't been tampered with:

```python
# Verify the text
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
if is_valid:
    print("Metadata:", extracted_metadata)
    print("Clean text:", clean_text)
```

## Combined Extraction and Verification

You can also extract and verify metadata in a single operation using `extract_verified_metadata`:

```python
# Extract and verify metadata using extract_verified_metadata
# Returns: (metadata_dict, is_verified)
# Note: This method requires the encoder to be initialized with the correct secret_key
extracted_metadata, is_verified = encoder.extract_verified_metadata(encoded_text)

if extracted_metadata:
    if is_verified:
        print("✅ Verified metadata:", extracted_metadata)
    else:
        print("❌ Metadata found but verification failed:", extracted_metadata)
else:
    print("No metadata found.")
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

# Verify the text
is_valid, extracted_metadata, clean_text = encoder.verify_text(full_text)
print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
if is_valid:
    print("Metadata:", extracted_metadata)
    print("Clean text:", clean_text)
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
        "version": "1.1.0"
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
        "text_id": i + 1,
        "version": "1.1.0"
    }
    
    # Embed metadata
    encoded_text = encoder.encode_metadata(text, metadata)
    encoded_texts.append(encoded_text)
    
    print(f"Text {i+1} encoded with metadata")

# Later, extract and verify metadata
for i, encoded_text in enumerate(encoded_texts):
    # Use verify_text for combined extraction and verification
    is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
    print(f"Text {i+1}:")
    if is_valid:
        print(f"  Verified: ✅")
        print(f"  Metadata: {extracted_metadata}")
    else:
        # Check if metadata was present but failed verification, or simply not present
        metadata_only, _ = encoder.decode_metadata(encoded_text)
        if metadata_only:
            print(f"  Verified: ❌ (Verification Failed)")
            print(f"  Metadata: {metadata_only}")
        else:
            print(f"  Verified: ❌ (No Metadata Found)")
```

### Error Handling

```python
def safe_process_text(text, encoder):
    """Safely process text, attempting verification."""
    result = {
        "has_metadata": False,
        "metadata": None,
        "verified": False,
        "error": None
    }
    
    # Attempt to verify the text using the encoder's key
    try:
        is_valid, metadata, clean_text = encoder.verify_text(text)
        if metadata: # Metadata was found
            result["has_metadata"] = True
            result["metadata"] = metadata
            result["verified"] = is_valid
        # If metadata is None, it means no valid encoded block was found
    except Exception as e:
        # General error during processing
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
