# Streaming Handlers

The streaming module in EncypherAI provides specialized handlers for working with streaming content from LLMs and other sources. These handlers make it easy to embed metadata in content that arrives chunk by chunk.

## StreamingHandler

The `StreamingHandler` class is the primary interface for handling streaming content. It provides a simple API for processing chunks of text and embedding metadata.

### Class Definition

```python
class StreamingHandler:
    def __init__(
        self, 
        metadata: Optional[Dict[str, Any]] = None, 
        target: Union[str, MetadataTarget] = "whitespace",
        secret_key: Optional[str] = None,
        buffer_size: int = 1024,
        encode_first_chunk_only: bool = True
    ):
        """
        Initialize a StreamingHandler for processing streaming content.
        
        Args:
            metadata: Dictionary containing the metadata to embed. If not provided,
                     an empty dictionary will be used with only a timestamp.
            target: Where to embed metadata. Can be a string ("whitespace", "punctuation", 
                   "first_letter", "last_letter", "all_characters") or a MetadataTarget enum.
            secret_key: Optional secret key for HMAC verification. If not provided,
                        a random key will be generated.
            buffer_size: Maximum size of the internal buffer for accumulating chunks.
            encode_first_chunk_only: If True, metadata will only be embedded in the first
                                    suitable chunk. If False, metadata will be distributed
                                    across multiple chunks as needed.
        """
```

### Methods

#### process_chunk

```python
def process_chunk(
    self, 
    chunk: str,
    is_final: bool = False
) -> str:
    """
    Process a chunk of streaming content.
    
    Args:
        chunk: The text chunk to process
        is_final: Whether this is the final chunk in the stream
        
    Returns:
        The processed chunk with metadata embedded (if applicable)
    """
```

#### finalize

```python
def finalize(self) -> Dict[str, Any]:
    """
    Finalize the streaming session and return information about the completed stream.
    
    This should be called after all chunks have been processed, unless the last chunk
    was processed with is_final=True.
    
    Returns:
        A dictionary containing information about the completed stream
    """
```

#### get_metadata

```python
def get_metadata(self) -> Dict[str, Any]:
    """
    Get the current metadata being used by the handler.
    
    Returns:
        The metadata dictionary
    """
```

#### update_metadata

```python
def update_metadata(
    self, 
    metadata: Dict[str, Any]
) -> None:
    """
    Update the metadata used by the handler.
    
    Args:
        metadata: New metadata dictionary to use
    """
```

### Usage Example

```python
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone

# Create metadata
metadata = {
    "model": "gpt-4",
    "organization": "MyCompany",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "version": "1.0.0"
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
for i, chunk in enumerate(chunks):
    is_final = i == len(chunks) - 1
    
    processed_chunk = handler.process_chunk(
        chunk=chunk,
        is_final=is_final
    )
    
    processed_chunks.append(processed_chunk)
    print(f"Processed chunk {i+1}: {processed_chunk}")

# If the last chunk wasn't marked as is_final=True, finalize the stream
if not chunks:  # If no chunks were processed with is_final=True
    handler.finalize()

# Combine all processed chunks
full_text = "".join(processed_chunks)

# Now you can extract and verify the metadata using the standard MetadataEncoder
from encypher.core import MetadataEncoder

encoder = MetadataEncoder()
extracted_metadata = encoder.decode_metadata(full_text)
verification_result = encoder.verify_text(full_text)

print(f"Extracted metadata: {extracted_metadata}")
print(f"Verification result: {verification_result}")
```

## Streaming with OpenAI

```python
import openai
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone

# Initialize OpenAI client
client = openai.OpenAI(api_key="your-api-key")

# Create metadata
metadata = {
    "model": "gpt-4",
    "organization": "MyCompany",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "version": "1.0.0"
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

## Streaming with Anthropic

```python
import anthropic
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone

# Initialize Anthropic client
client = anthropic.Anthropic(api_key="your-api-key")

# Create metadata
metadata = {
    "model": "claude-3-opus-20240229",
    "organization": "MyCompany",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "version": "1.0.0"
}

# Initialize the streaming handler
handler = StreamingHandler(metadata=metadata)

# Create a streaming completion
with client.messages.stream(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "Write a short paragraph about AI ethics."}
    ]
) as stream:
    full_response = ""
    for text in stream.text_stream:
        # Process the chunk
        processed_chunk = handler.process_chunk(chunk=text)
        
        # Print and accumulate the processed chunk
        print(processed_chunk, end="", flush=True)
        full_response += processed_chunk

# Finalize the stream
handler.finalize()

print("\n\nStreaming completed!")
```

## LiteLLM Integration

EncypherAI works seamlessly with [LiteLLM](https://github.com/BerriAI/litellm), which provides a unified interface for multiple LLM providers:

```python
import litellm
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone

# Configure LiteLLM
litellm.api_key = "your-api-key"

# Create metadata
metadata = {
    "model": "gpt-4",
    "provider": "openai",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "version": "1.0.0"
}

# Initialize the streaming handler
handler = StreamingHandler(metadata=metadata)

# Create a streaming completion
response = litellm.completion(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a short paragraph about AI ethics."}
    ],
    stream=True
)

# Process each chunk
full_response = ""
for chunk in response:
    if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
        content = chunk.choices[0].delta.content
        if content:
            # Process the chunk
            processed_chunk = handler.process_chunk(chunk=content)
            
            # Print and accumulate the processed chunk
            print(processed_chunk, end="", flush=True)
            full_response += processed_chunk

# Finalize the stream
handler.finalize()

print("\n\nStreaming completed!")
```

## Implementation Details

### Buffering Strategy

The `StreamingHandler` uses an internal buffer to accumulate chunks until there are enough suitable targets for embedding metadata:

1. When a chunk arrives, it's added to the buffer
2. If there are enough targets in the buffer, metadata is embedded
3. The processed buffer is returned, and the buffer is cleared
4. If there aren't enough targets, the chunk is kept in the buffer until more chunks arrive

### Metadata Distribution

The handler uses different strategies for embedding metadata depending on the `encode_first_chunk_only` setting:

- When `encode_first_chunk_only=True` (default), it waits for a chunk with suitable targets and embeds all metadata there
- When `encode_first_chunk_only=False`, it distributes metadata across multiple chunks as needed

### HMAC Verification

The HMAC signature is calculated based on the entire content, not just individual chunks. This ensures that the verification will detect if any part of the content is modified.

## Advanced Usage: Custom Streaming Handler

You can create a custom streaming handler by extending the `StreamingHandler` class:

```python
from encypher.streaming import StreamingHandler
from encypher.core import MetadataTarget
import json

class CustomStreamingHandler(StreamingHandler):
    def __init__(self, *args, **kwargs):
        # Add custom tracking
        self.chunks_processed = 0
        self.total_characters = 0
        
        # Initialize the parent class
        super().__init__(*args, **kwargs)
    
    def process_chunk(self, chunk, is_final=False):
        # Track statistics
        self.chunks_processed += 1
        self.total_characters += len(chunk)
        
        # Add chunk number to metadata
        self.metadata["chunk_number"] = self.chunks_processed
        self.metadata["total_characters"] = self.total_characters
        
        # Use the parent implementation to process the chunk
        return super().process_chunk(chunk, is_final)
    
    def finalize(self):
        # Add final statistics to metadata
        self.metadata["final_chunk_count"] = self.chunks_processed
        self.metadata["final_character_count"] = self.total_characters
        
        # Use the parent implementation to finalize
        return super().finalize()
    
    def get_statistics(self):
        """Custom method to get processing statistics"""
        return {
            "chunks_processed": self.chunks_processed,
            "total_characters": self.total_characters,
            "average_chunk_size": self.total_characters / max(1, self.chunks_processed)
        }

# Usage example
handler = CustomStreamingHandler(metadata={"model": "custom-model"})

# Process chunks
for chunk in chunks:
    processed = handler.process_chunk(chunk)
    # ...

# Get statistics
stats = handler.get_statistics()
print(f"Streaming statistics: {json.dumps(stats, indent=2)}")
```

## Related Classes

- [`MetadataEncoder`](../api-reference/metadata-encoder.md) - Base class for embedding and extracting metadata
- [`StreamingMetadataEncoder`](../api-reference/streaming-metadata-encoder.md) - Lower-level interface for streaming scenarios
- [`UnicodeMetadata`](../api-reference/unicode-metadata.md) - Low-level utilities for working with Unicode variation selectors
