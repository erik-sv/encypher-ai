# OpenAI Integration

This guide explains how to integrate EncypherAI with OpenAI's API to embed metadata in AI-generated content from models like GPT-3.5 and GPT-4.

## Prerequisites

Before you begin, make sure you have:

1. An OpenAI API key
2. The OpenAI Python package installed
3. EncypherAI installed

```bash
uv pip install encypher-ai openai
```

## Basic Integration

### Non-Streaming Response

For standard (non-streaming) responses from OpenAI:

```python
import openai
from encypher.core import MetadataEncoder
from datetime import datetime, timezone
import json

# Initialize OpenAI client
client = openai.OpenAI(api_key="your-api-key")

# Create a metadata encoder
encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

# Create a completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a short paragraph about AI ethics."}
    ]
)

# Get the response text
text = response.choices[0].message.content

# Create metadata
metadata = {
    "model": response.model,
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "total_tokens": response.usage.total_tokens
}

# Embed metadata
encoded_text = encoder.encode_metadata(text, metadata)

print("Original response:")
print(text)
print("\nResponse with embedded metadata:")
print(encoded_text)

# Later, extract and verify the metadata
extracted_metadata = encoder.decode_metadata(encoded_text)
verification_result = encoder.verify_text(encoded_text, secret_key="your-secret-key")  # Pass the same secret_key used during encoding

print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))
print(f"Verification result: {'✅ Verified' if verification_result else '❌ Failed'}")
```

### Streaming Response

For streaming responses, use the `StreamingHandler`:

```python
import openai
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone

# Initialize OpenAI client
client = openai.OpenAI(api_key="your-api-key")

# Create metadata
metadata = {
    "model": "gpt-4",
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat()
}

# Initialize the streaming handler
handler = StreamingHandler(metadata=metadata, secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

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

# Extract and verify the metadata
from encypher.core import MetadataEncoder

encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification
extracted_metadata = encoder.decode_metadata(full_response)
verification_result = encoder.verify_text(full_response, secret_key="your-secret-key")  # Pass the same secret_key used during encoding

print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))
print(f"Verification result: {'✅ Verified' if verification_result else '❌ Failed'}")
```

## Advanced Integration

### Function Calling

When using OpenAI's function calling feature:

```python
import openai
from encypher.core import MetadataEncoder
from datetime import datetime, timezone
import json

# Initialize OpenAI client
client = openai.OpenAI(api_key="your-api-key")

# Define functions
functions = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Create a completion with function calling
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ],
    tools=functions,
    tool_choice="auto"
)

# Get the response
message = response.choices[0].message

# Check if the model wants to call a function
if message.tool_calls:
    # Get the function call
    function_call = message.tool_calls[0].function
    function_name = function_call.name
    function_args = json.loads(function_call.arguments)
    
    print(f"Function call: {function_name}")
    print(f"Arguments: {function_args}")
    
    # Simulate function response
    function_response = {
        "location": function_args["location"],
        "temperature": 72,
        "unit": function_args.get("unit", "fahrenheit"),
        "condition": "sunny"
    }
    
    # Continue the conversation with the function result
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather like in San Francisco?"},
            message,
            {
                "role": "tool",
                "tool_call_id": message.tool_calls[0].id,
                "name": function_name,
                "content": json.dumps(function_response)
            }
        ]
    )
    
    # Get the final response text
    text = response.choices[0].message.content
else:
    # Get the response text
    text = message.content

# Create metadata
metadata = {
    "model": response.model,
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "function_call": message.tool_calls[0].function.name if message.tool_calls else None,
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "total_tokens": response.usage.total_tokens
}

# Embed metadata
encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification
encoded_text = encoder.encode_metadata(text, metadata)

print("\nFinal response with embedded metadata:")
print(encoded_text)
```

### Custom Metadata Extraction

You can create a helper function to extract metadata from OpenAI responses:

```python
def extract_openai_metadata(response):
    """Extract metadata from an OpenAI API response."""
    metadata = {
        "model": response.model,
        "organization": "YourOrganization",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Add usage information if available
    if hasattr(response, "usage"):
        metadata.update({
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        })
    
    # Add function call information if available
    message = response.choices[0].message
    if hasattr(message, "tool_calls") and message.tool_calls:
        function_call = message.tool_calls[0].function
        metadata.update({
            "function_call": function_call.name,
            "function_args": json.loads(function_call.arguments)
        })
    
    return metadata
```

## Web Application Integration

Here's an example of integrating OpenAI and EncypherAI in a Flask web application:

```python
from flask import Flask, request, jsonify
import openai
from encypher.core import MetadataEncoder
from datetime import datetime, timezone

app = Flask(__name__)

# Initialize OpenAI client
client = openai.OpenAI(api_key="your-api-key")

# Create a metadata encoder
encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

@app.route('/generate', methods=['POST'])
def generate():
    # Get request data
    data = request.json
    prompt = data.get('prompt', '')
    
    # Create a completion
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Get the response text
    text = response.choices[0].message.content
    
    # Create metadata
    metadata = {
        "model": response.model,
        "organization": "YourOrganization",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
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
        verified = encoder.verify_text(text, secret_key="your-secret-key")  # Pass the same secret_key used during encoding
        
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
import openai
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
        "model": "gpt-4",
        "organization": "YourOrganization",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": data.get('user_id', 'anonymous')
    }
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key="your-api-key")
    
    # Initialize the streaming handler
    handler = StreamingHandler(metadata=metadata, secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification
    
    def generate_stream():
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
        
        # Finalize the stream
        handler.finalize()
    
    # Return a streaming response
    return Response(stream_with_context(generate_stream()), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
```

## Best Practices

1. **Include Model Information**: Always include the model name, version, and other relevant information in the metadata.

2. **Add Timestamps**: Include a UTC timestamp to track when the content was generated.

3. **Track Token Usage**: Include token counts to monitor API usage and costs.

4. **Use Secure Keys**: Store your OpenAI API key and EncypherAI secret key securely, using environment variables or a secure key management system.

5. **Handle Errors Gracefully**: Implement proper error handling for both OpenAI API calls and EncypherAI operations.

6. **Verify Before Trusting**: Always verify the metadata before relying on it, especially for security-sensitive applications.

7. **Choose Appropriate Targets**: For longer responses, using `whitespace` as the embedding target is usually sufficient. For shorter responses, consider using `all_characters` to ensure enough targets are available.

## Troubleshooting

### API Key Issues

If you encounter authentication errors with the OpenAI API:

```python
import os

# Set API key as environment variable
os.environ["OPENAI_API_KEY"] = "your-api-key"

# Or configure the client with the key
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
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
        except openai.RateLimitError:
            retries += 1
            if retries == max_retries:
                raise
            # Exponential backoff with jitter
            sleep_time = (2 ** retries) + random.random()
            print(f"Rate limited, retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)

# Example usage
def make_openai_call():
    return client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a short paragraph about AI ethics."}
        ]
    )

response = call_with_retry(make_openai_call)
```

### Metadata Extraction Failures

If metadata extraction fails:

1. Ensure the text hasn't been modified after embedding
2. Check if the text has enough suitable targets for embedding
3. Verify you're using the same secret key for embedding and extraction

## Related Documentation

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [EncypherAI Streaming Support](../user-guide/streaming.md)
- [Metadata Encoding Guide](../user-guide/metadata-encoding.md)
- [Extraction and Verification](../user-guide/extraction-verification.md)
