# Quick Start Guide

This guide will help you get started with EncypherAI for embedding and extracting metadata from AI-generated text.

## Basic Usage

### 1. Import the Package

```python
from encypher.core.metadata_encoder import MetadataEncoder
```

### 2. Initialize the Encoder

```python
# Create an encoder with a secret key for HMAC verification
encoder = MetadataEncoder(secret_key="your-secret-key")
```

### 3. Embed Metadata in Text

```python
import time

# Define your metadata
metadata = {
    "model_id": "gpt-4",
    "timestamp": int(time.time()),  # Unix/Epoch timestamp
    "version": "1.1.0",
    "organization": "EncypherAI"
}

# Original AI-generated text
text = "This is AI-generated content that will contain invisible metadata."

# Embed metadata into the text
encoded_text = encoder.encode_metadata(text, metadata)

# The encoded_text looks identical to the original text when displayed,
# but contains invisible zero-width characters that encode the metadata
```

### 4. Extract and Verify Metadata

```python
# Later, extract and verify the metadata
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)

if is_valid:
    print("Metadata is valid and has not been tampered with.")
    print(f"Extracted metadata: {extracted_metadata}")
    print(f"Clean text: {clean_text}")
else:
    print("Metadata validation failed - content may have been tampered with.")
```

## Streaming Support

EncypherAI also supports streaming responses from LLM providers:

```python
from encypher.streaming.handlers import StreamingHandler
import time

# Initialize the streaming handler
metadata = {
    "model_id": "gpt-4", 
    "timestamp": int(time.time())  # Unix/Epoch timestamp
}

streaming_handler = StreamingHandler(
    metadata=metadata,
    target="whitespace",
    encode_first_chunk_only=True
)

# Process chunks as they arrive
encoded_chunks = []
for chunk in streaming_response_chunks:  # From your LLM provider
    encoded_chunk = streaming_handler.process_chunk(chunk)
    encoded_chunks.append(encoded_chunk)
    # Send to client or process as needed

# The complete encoded text with metadata
complete_encoded_text = "".join(encoded_chunks)
```

## Integrating with OpenAI

Here's a quick example with OpenAI:

```python
from openai import OpenAI
from encypher.core.metadata_encoder import MetadataEncoder
import time

# Set up OpenAI client
client = OpenAI(api_key="your-openai-api-key")

# Create encoder
encoder = MetadataEncoder(secret_key="your-secret-key")

# Get response from OpenAI
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Write a short poem about technology."}]
)
text = response.choices[0].message.content

# Add metadata
metadata = {
    "model_id": "gpt-4",
    "timestamp": int(time.time()),  # Unix/Epoch timestamp
    "organization": "Your Organization"
}
encoded_text = encoder.encode_metadata(text, metadata)

# The encoded_text now contains invisible metadata
print(encoded_text)  # Looks just like the original text
```

## Next Steps

Explore more advanced features in the User Guide:

- [Metadata Encoding](../user-guide/metadata-encoding.md)
- [Extraction and Verification](../user-guide/extraction-verification.md)
- [Tamper Detection](../user-guide/tamper-detection.md)
- [Streaming Support](../user-guide/streaming.md)
