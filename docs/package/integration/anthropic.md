# Anthropic Integration

This guide explains how to integrate EncypherAI with Anthropic's Claude models to embed metadata in AI-generated content.

## Prerequisites

Before you begin, make sure you have:

1. An Anthropic API key
2. The Anthropic Python package installed
3. EncypherAI installed

```bash
uv pip install encypher-ai anthropic
```

## Basic Integration

### Non-Streaming Response

For standard (non-streaming) responses from Anthropic:

```python
import anthropic
from encypher.core import MetadataEncoder
from datetime import datetime, timezone
import json

# Initialize Anthropic client
client = anthropic.Anthropic(api_key="your-api-key")

# Create a metadata encoder
encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

# Create a message
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "Write a short paragraph about AI ethics."}
    ]
)

# Get the response text
text = response.content[0].text

# Create metadata
metadata = {
    "model": response.model,
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "input_tokens": response.usage.input_tokens,
    "output_tokens": response.usage.output_tokens
}

# Embed metadata
encoded_text = encoder.encode_metadata(text, metadata)

print("Original response:")
print(text)
print("\nResponse with embedded metadata:")
print(encoded_text)

# Later, extract and verify the metadata
extracted_metadata = encoder.decode_metadata(encoded_text)
verification_result = encoder.verify_text(encoded_text)

print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))
print(f"Verification result: {'✅ Verified' if verification_result else '❌ Failed'}")
```

### Streaming Response

For streaming responses, use the `StreamingHandler`:

```python
import anthropic
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone

# Initialize Anthropic client
client = anthropic.Anthropic(api_key="your-api-key")

# Create metadata
metadata = {
    "model": "claude-3-opus-20240229",
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat()
}

# Initialize the streaming handler
handler = StreamingHandler(metadata=metadata, secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

# Create a streaming message
with client.messages.stream(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "Write a short paragraph about AI ethics."}
    ]
) as stream:
    # Process each chunk
    full_response = ""
    for text_delta in stream.text_deltas:
        # Process the chunk
        processed_chunk = handler.process_chunk(chunk=text_delta)
        
        # Print and accumulate the processed chunk
        print(processed_chunk, end="", flush=True)
        full_response += processed_chunk

# Finalize the stream
final_chunk = handler.finalize()
if final_chunk:
    full_response += final_chunk

print("\n\nStreaming completed!")

# Extract and verify the metadata
from encypher.core import MetadataEncoder

encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification
extracted_metadata = encoder.decode_metadata(full_response)
verification_result = encoder.verify_text(full_response)

print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))
print(f"Verification result: {'✅ Verified' if verification_result else '❌ Failed'}")
```

## Advanced Integration

### Tool Use (Function Calling)

When using Anthropic's tool use feature:

```python
import anthropic
import json
from encypher.core import MetadataEncoder
from datetime import datetime, timezone

# Initialize Anthropic client
client = anthropic.Anthropic(api_key="your-api-key")

# Define tools
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature"
                }
            },
            "required": ["location"]
        }
    }
]

# Create a message with tool use
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ],
    tools=tools
)

# Get the response
content = response.content

# Check if the model wants to use a tool
tool_use = None
for item in content:
    if item.type == "tool_use":
        tool_use = item
        break

if tool_use:
    # Get the tool call
    tool_name = tool_use.name
    tool_input = json.loads(tool_use.input)
    
    print(f"Tool call: {tool_name}")
    print(f"Input: {tool_input}")
    
    # Simulate tool response
    tool_response = {
        "location": tool_input["location"],
        "temperature": 72,
        "unit": tool_input.get("unit", "fahrenheit"),
        "condition": "sunny"
    }
    
    # Continue the conversation with the tool result
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": "What's the weather like in San Francisco?"},
            {
                "role": "assistant",
                "content": [tool_use]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(tool_response)
                    }
                ]
            }
        ]
    )
    
    # Get the final response text
    text = response.content[0].text
else:
    # Get the response text from the first response
    text = content[0].text

# Create metadata
metadata = {
    "model": response.model,
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tool_use": tool_name if tool_use else None,
    "input_tokens": response.usage.input_tokens,
    "output_tokens": response.usage.output_tokens
}

# Embed metadata
encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification
encoded_text = encoder.encode_metadata(text, metadata)

print("\nFinal response with embedded metadata:")
print(encoded_text)
```

### Custom Metadata Extraction

You can create a helper function to extract metadata from Anthropic responses:

```python
def extract_anthropic_metadata(response):
    """Extract metadata from an Anthropic API response."""
    metadata = {
        "model": response.model,
        "organization": "YourOrganization",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Add usage information if available
    if hasattr(response, "usage"):
        metadata.update({
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        })
    
    # Add tool use information if available
    tool_use = None
    for item in response.content:
        if hasattr(item, "type") and item.type == "tool_use":
            tool_use = item
            break
    
    if tool_use:
        metadata.update({
            "tool_use": tool_use.name,
            "tool_input": json.loads(tool_use.input)
        })
    
    return metadata
```

## Web Application Integration

Here's an example of integrating Anthropic and EncypherAI in a Flask web application:

```python
from flask import Flask, request, jsonify
import anthropic
from encypher.core import MetadataEncoder
from datetime import datetime, timezone

app = Flask(__name__)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key="your-api-key")

# Create a metadata encoder
encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

@app.route('/generate', methods=['POST'])
def generate():
    # Get request data
    data = request.json
    prompt = data.get('prompt', '')
    
    # Create a message
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Get the response text
    text = response.content[0].text
    
    # Create metadata
    metadata = {
        "model": response.model,
        "organization": "YourOrganization",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "user_id": data.get('user_id', 'anonymous')
    }
    
    # Embed metadata
    encoded_text = encoder.encode_metadata(text, metadata)
    
    # Return the response
    return jsonify({
        "text": encoded_text,
        "metadata": metadata
    })

@app.route('/verify', methods=['POST'])
def verify():
    # Get request data
    data = request.json
    text = data.get('text', '')
    
    # Extract and verify metadata
    try:
        metadata = encoder.decode_metadata(text)
        verified = encoder.verify_text(text)
        
        return jsonify({
            "has_metadata": True,
            "metadata": metadata,
            "verified": verified
        })
    except Exception as e:
        return jsonify({
            "has_metadata": False,
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
```

## Streaming in Web Applications

For streaming responses in a web application:

```python
from flask import Flask, Response, request, stream_with_context
import anthropic
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone

app = Flask(__name__)

@app.route('/stream', methods=['POST'])
def stream():
    # Get request data
    data = request.json
    prompt = data.get('prompt', '')
    
    # Create metadata
    metadata = {
        "model": "claude-3-opus-20240229",
        "organization": "YourOrganization",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": data.get('user_id', 'anonymous')
    }
    
    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key="your-api-key")
    
    # Initialize the streaming handler
    handler = StreamingHandler(metadata=metadata, secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification
    
    def generate_stream():
        # Create a streaming message
        with client.messages.stream(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ) as stream:
            # Process each chunk
            for text_delta in stream.text_deltas:
                # Process the chunk
                processed_chunk = handler.process_chunk(chunk=text_delta)
                
                # Yield the processed chunk
                yield processed_chunk
        
        # Finalize the stream
        final_chunk = handler.finalize()
        if final_chunk:
            yield final_chunk
    
    # Return a streaming response
    return Response(stream_with_context(generate_stream()), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
```

## Best Practices

1. **Include Model Information**: Always include the model name, version, and other relevant information in the metadata.

2. **Add Timestamps**: Include a UTC timestamp to track when the content was generated.

3. **Track Token Usage**: Include token counts to monitor API usage and costs.

4. **Use Secure Keys**: Store your Anthropic API key and EncypherAI secret key securely, using environment variables or a secure key management system.

5. **Handle Errors Gracefully**: Implement proper error handling for both Anthropic API calls and EncypherAI operations.

6. **Verify Before Trusting**: Always verify the metadata before relying on it, especially for security-sensitive applications.

7. **Choose Appropriate Targets**: For longer responses, using `whitespace` as the embedding target is usually sufficient. For shorter responses, consider using `all_characters` to ensure enough targets are available.

## Troubleshooting

### API Key Issues

If you encounter authentication errors with the Anthropic API:

```python
import os

# Set API key as environment variable
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

# Or configure the client with the key
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
```

### Rate Limiting

If you hit rate limits, implement exponential backoff:

```python
import time
import random

def call_with_retry(func, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except anthropic.RateLimitError:
            retries += 1
            if retries == max_retries:
                raise
            # Exponential backoff with jitter
            sleep_time = (2 ** retries) + random.random()
            print(f"Rate limited, retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

# Example usage
def make_anthropic_call():
    return client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": "Write a short paragraph about AI ethics."}
        ]
    )

response = call_with_retry(make_anthropic_call)
```

### Metadata Extraction Failures

If metadata extraction fails:

1. Ensure the text hasn't been modified after embedding
2. Check if the text has enough suitable targets for embedding
3. Verify you're using the same secret key for embedding and extraction

## Related Documentation

- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [EncypherAI Streaming Support](../user-guide/streaming.md)
- [Metadata Encoding Guide](../user-guide/metadata-encoding.md)
- [Extraction and Verification](../user-guide/extraction-verification.md)
