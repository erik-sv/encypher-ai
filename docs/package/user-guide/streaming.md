# Streaming Support

EncypherAI provides robust support for embedding metadata in streaming content, such as text generated chunk by chunk from Large Language Models (LLMs). This guide explains how to use EncypherAI's streaming capabilities effectively.

## Understanding Streaming Challenges

When working with streaming content, embedding metadata presents unique challenges:

1. **Partial Content**: Content arrives in chunks, not all at once
2. **Target Availability**: Individual chunks may not have suitable locations for embedding metadata
3. **Verification Integrity**: HMAC verification must work on the complete content
4. **Consistent Extraction**: Metadata must be extractable from the final combined content

EncypherAI addresses these challenges through specialized streaming handlers and encoders.

## Using the StreamingHandler

The `StreamingHandler` class provides a simple interface for processing streaming content:

```python
from encypher.streaming.handlers import StreamingHandler
import time

# Create metadata
metadata = {
    "model_id": "gpt-4",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),  # Unix/Epoch timestamp
    "version": "1.0.0"
}

# Initialize the streaming handler
handler = StreamingHandler(
    metadata=metadata,
    target="whitespace",  # Where to embed metadata
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
    processed_chunk = handler.process_chunk(chunk=chunk)
    
    processed_chunks.append(processed_chunk)
    print(f"Processed chunk: {processed_chunk}")

# Combine all processed chunks
full_text = "".join(processed_chunks)

# Extract and verify the metadata
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import UnicodeMetadata

# Extract metadata
is_valid, extracted_metadata = UnicodeMetadata.extract_metadata(full_text)
print(f"Metadata extraction successful: {is_valid}")
print(f"Extracted metadata: {extracted_metadata}")

# Verify with encoder if needed
encoder = MetadataEncoder()
is_valid, metadata_dict, clean_text = encoder.verify_text(full_text)
print(f"Verification result: {is_valid}")
```

## How Streaming Works

The `StreamingHandler` uses an intelligent buffering strategy:

1. **Buffering**: Accumulates chunks until there are enough suitable targets for embedding metadata
2. **Embedding**: Embeds metadata when sufficient targets are available
3. **Flushing**: Returns processed content and clears the buffer
4. **Finalization**: Ensures all metadata is properly embedded by the end of the stream

## Integration with LLM Providers

### OpenAI

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
handler = StreamingHandler(
    metadata=metadata,
    target="whitespace",
    encode_first_chunk_only=True
)

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

print("\n\nStreaming completed!")
```

### Anthropic

```python
import anthropic
from encypher.streaming.handlers import StreamingHandler
import time

# Initialize Anthropic client
client = anthropic.Anthropic(api_key="your-api-key")

# Create metadata
metadata = {
    "model_id": "claude-3-opus-20240229",
    "organization": "EncypherAI",
    "timestamp": int(time.time())  # Unix/Epoch timestamp
}

# Initialize the streaming handler
handler = StreamingHandler(
    metadata=metadata,
    target="whitespace",
    encode_first_chunk_only=True
)

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

print("\n\nStreaming completed!")
```

### LiteLLM (Multi-Provider)

```python
import litellm
from encypher.streaming.handlers import StreamingHandler
import time

# Configure LiteLLM
litellm.api_key = "your-api-key"

# Create metadata
metadata = {
    "model_id": "gpt-4",
    "provider": "openai",
    "timestamp": int(time.time())  # Unix/Epoch timestamp
}

# Initialize the streaming handler
handler = StreamingHandler(
    metadata=metadata,
    target="whitespace",
    encode_first_chunk_only=True
)

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
    if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        
        # Process the chunk
        processed_chunk = handler.process_chunk(chunk=content)
        
        # Print and accumulate the processed chunk
        print(processed_chunk, end="", flush=True)
        full_response += processed_chunk

print("\n\nStreaming completed!")
```

## Advanced Configuration

### Customizing Target Selection

You can customize where metadata is embedded in the streaming text:

```python
from encypher.streaming.handlers import StreamingHandler
from encypher.core.unicode_metadata import MetadataTarget
import time

# Create metadata
metadata = {
    "model_id": "gpt-4",
    "timestamp": int(time.time())  # Unix/Epoch timestamp
}

# Initialize with custom target
handler = StreamingHandler(
    metadata=metadata,
    target=MetadataTarget.PUNCTUATION,  # Embed after punctuation
    encode_first_chunk_only=True
)
```

### Controlling Embedding Strategy

The `encode_first_chunk_only` parameter determines whether metadata is embedded only in the first chunk or throughout the stream:

```python
# Embed only in the first chunk (default)
handler1 = StreamingHandler(
    metadata=metadata,
    encode_first_chunk_only=True
)

# Embed throughout the stream
handler2 = StreamingHandler(
    metadata=metadata,
    encode_first_chunk_only=False
)
```

### Custom Buffering Strategy

You can control the buffering behavior:

```python
# Wait for at least 50 characters before embedding
handler = StreamingHandler(
    metadata=metadata,
    min_buffer_size=50,
    encode_first_chunk_only=True
)
```

## Web Integration Examples

### FastAPI Streaming Endpoint

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from openai import OpenAI
from encypher.streaming.handlers import StreamingHandler
import time
import asyncio

app = FastAPI()

@app.post("/generate-stream")
async def generate_stream(request: Request):
    # Parse request
    data = await request.json()
    prompt = data.get("prompt", "Write something interesting.")
    
    # Initialize OpenAI client
    client = OpenAI(api_key="your-api-key")
    
    # Create metadata
    metadata = {
        "model_id": "gpt-4",
        "timestamp": int(time.time()),  # Unix/Epoch timestamp
        "request_id": data.get("request_id", str(time.time()))
    }
    
    # Initialize the streaming handler
    handler = StreamingHandler(
        metadata=metadata,
        target="whitespace",
        encode_first_chunk_only=True
    )
    
    async def generate():
        # Create a streaming completion
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        # Process each chunk
        for chunk in completion:
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                
                # Process the chunk
                processed_chunk = handler.process_chunk(chunk=content)
                
                # Yield the processed chunk
                yield processed_chunk
                
                # Add a small delay to simulate real-time streaming
                await asyncio.sleep(0.01)
    
    return StreamingResponse(generate(), media_type="text/plain")
```

### Flask Streaming Example

```python
from flask import Flask, Response, request, stream_with_context
from openai import OpenAI
from encypher.streaming.handlers import StreamingHandler
import time
import json

app = Flask(__name__)

@app.route("/generate-stream", methods=["POST"])
def generate_stream():
    # Parse request
    data = request.json
    prompt = data.get("prompt", "Write something interesting.")
    
    # Initialize OpenAI client
    client = OpenAI(api_key="your-api-key")
    
    # Create metadata
    metadata = {
        "model_id": "gpt-4",
        "timestamp": int(time.time()),  # Unix/Epoch timestamp
        "request_id": data.get("request_id", str(time.time()))
    }
    
    # Initialize the streaming handler
    handler = StreamingHandler(
        metadata=metadata,
        target="whitespace",
        encode_first_chunk_only=True
    )
    
    def generate():
        # Create a streaming completion
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        # Process each chunk
        for chunk in completion:
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                
                # Process the chunk
                processed_chunk = handler.process_chunk(chunk=content)
                
                # Yield the processed chunk
                yield processed_chunk
    
    return Response(stream_with_context(generate()), mimetype="text/plain")

if __name__ == "__main__":
    app.run(debug=True)
```
