# LiteLLM Integration

This guide explains how to integrate EncypherAI with LiteLLM to embed metadata in AI-generated content from various LLM providers through a unified interface.

## Prerequisites

Before you begin, make sure you have:

1. API keys for the LLM providers you want to use
2. The LiteLLM Python package installed
3. EncypherAI installed

```bash
uv pip install encypher-ai litellm
```

## Basic Integration

LiteLLM provides a unified interface to multiple LLM providers, making it easy to switch between different models while maintaining the same code structure.

### Non-Streaming Response

For standard (non-streaming) responses using LiteLLM:

```python
import litellm
from encypher.core import MetadataEncoder
from datetime import datetime, timezone
import json
import os

# Set up your API keys
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-api-key"

# Create a metadata encoder
encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

# Create a completion using OpenAI
response = litellm.completion(
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
    "provider": "openai",  # Determined based on the model
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
verification_result = encoder.verify_text(encoded_text, secret_key="your-secret-key")

print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))
print(f"Verification result: {'✅ Verified' if verification_result else '❌ Failed'}")
```

### Streaming Response

For streaming responses, use the `StreamingHandler` with LiteLLM:

```python
import litellm
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone
import os

# Set up your API keys
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-api-key"

# Create metadata
metadata = {
    "model": "gpt-4",
    "provider": "openai",
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat()
}

# Initialize the streaming handler
handler = StreamingHandler(metadata=metadata, secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

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

encoder = MetadataEncoder(secret_key="your-secret-key")
extracted_metadata = encoder.decode_metadata(full_response)
verification_result = encoder.verify_text(full_response, secret_key="your-secret-key")

print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))
print(f"Verification result: {'✅ Verified' if verification_result else '❌ Failed'}")
```

## Advanced Integration

### Using Different LLM Providers

LiteLLM makes it easy to switch between different providers:

```python
import litellm
from encypher.core import MetadataEncoder
from datetime import datetime, timezone
import json
import os

# Set up your API keys
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-api-key"

# Create a metadata encoder
encoder = MetadataEncoder(secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

# Function to generate text with metadata using any LLM provider
def generate_with_metadata(model, prompt, system_prompt=None):
    # Determine provider based on model prefix
    if model.startswith("gpt"):
        provider = "openai"
    elif model.startswith("claude"):
        provider = "anthropic"
    else:
        provider = "unknown"
    
    # Create messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # Create a completion
    response = litellm.completion(
        model=model,
        messages=messages
    )
    
    # Get the response text
    text = response.choices[0].message.content
    
    # Create metadata
    metadata = {
        "model": response.model,
        "provider": provider,
        "organization": "YourOrganization",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Add usage information if available
    if hasattr(response, "usage"):
        metadata.update({
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        })
    
    # Embed metadata
    encoded_text = encoder.encode_metadata(text, metadata)
    
    return {
        "text": encoded_text,
        "metadata": metadata,
        "original_text": text
    }

# Example usage with different models
openai_response = generate_with_metadata(
    model="gpt-4",
    prompt="Write a short paragraph about AI ethics.",
    system_prompt="You are a helpful assistant."
)

anthropic_response = generate_with_metadata(
    model="claude-3-opus-20240229",
    prompt="Write a short paragraph about AI ethics."
)

print("OpenAI Response:")
print(openai_response["text"])
print("\nMetadata:", openai_response["metadata"])

print("\nAnthropic Response:")
print(anthropic_response["text"])
print("\nMetadata:", anthropic_response["metadata"])
```

### Function Calling with LiteLLM

Using function calling with LiteLLM and EncypherAI:

```python
import litellm
import json
from encypher.core import MetadataEncoder
from datetime import datetime, timezone
import os

# Set up your API keys
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

# Define functions
functions = [
    {
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
]

# Create a completion with function calling
response = litellm.completion(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ],
    functions=functions,
    function_call="auto"
)

# Get the response
message = response.choices[0].message

# Check if the model wants to call a function
if hasattr(message, "function_call") and message.function_call:
    # Get the function call
    function_call = message.function_call
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
    response = litellm.completion(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather like in San Francisco?"},
            message,
            {
                "role": "function",
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
    "provider": "openai",
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "function_call": message.function_call.name if hasattr(message, "function_call") and message.function_call else None
}

# Add usage information if available
if hasattr(response, "usage"):
    metadata.update({
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens
    })

# Embed metadata
encoder = MetadataEncoder(secret_key="your-secret-key")
encoded_text = encoder.encode_metadata(text, metadata)

print("\nFinal response with embedded metadata:")
print(encoded_text)
```

## LiteLLM Proxy Integration

If you're using LiteLLM as a proxy server, you can integrate EncypherAI on the server side:

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from litellm.proxy.proxy_server import router as litellm_router
from encypher.core import MetadataEncoder
from datetime import datetime, timezone
import json

app = FastAPI()
security = HTTPBearer()
encoder = MetadataEncoder(secret_key="your-secret-key")

# Add LiteLLM router
app.include_router(litellm_router)

# Middleware to process responses
@app.middleware("http")
async def add_metadata_middleware(request, call_next):
    # Process the request normally
    response = await call_next(request)
    
    # Check if this is a completion response
    if request.url.path == "/v1/chat/completions" and response.status_code == 200:
        # Get the response body
        body = await response.body()
        data = json.loads(body)
        
        # Check if this is a streaming response
        if "choices" in data and len(data["choices"]) > 0:
            # Get the response text
            if "message" in data["choices"][0] and "content" in data["choices"][0]["message"]:
                text = data["choices"][0]["message"]["content"]
                
                # Create metadata
                metadata = {
                    "model": data.get("model", "unknown"),
                    "organization": "YourOrganization",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Add usage information if available
                if "usage" in data:
                    metadata.update({
                        "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                        "completion_tokens": data["usage"].get("completion_tokens", 0),
                        "total_tokens": data["usage"].get("total_tokens", 0)
                    })
                
                # Embed metadata
                encoded_text = encoder.encode_metadata(text, metadata)
                
                # Update the response
                data["choices"][0]["message"]["content"] = encoded_text
                
                # Return the modified response
                return JSONResponse(
                    content=data,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
    
    return response

# Authentication endpoint
@app.post("/auth")
async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Validate the token
    token = credentials.credentials
    if token != "your-api-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {"authenticated": True}

# Verification endpoint
@app.post("/verify")
async def verify(request: Request):
    data = await request.json()
    text = data.get("text", "")
    
    # Extract and verify metadata
    try:
        metadata = encoder.decode_metadata(text)
        verified = encoder.verify_text(text, secret_key="your-secret-key")
        
        return {
            "has_metadata": True,
            "metadata": metadata,
            "verified": verified
        }
    except Exception as e:
        return {
            "has_metadata": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Client-Side Integration

When using LiteLLM as a client to a proxy server:

```python
import litellm
from encypher.streaming import StreamingHandler
from datetime import datetime, timezone

# Configure LiteLLM to use a proxy
litellm.api_base = "http://localhost:8000"
litellm.api_key = "your-api-key"

# Create metadata
metadata = {
    "model": "gpt-4",
    "organization": "YourOrganization",
    "timestamp": datetime.now(timezone.utc).isoformat()
}

# Initialize the streaming handler
handler = StreamingHandler(metadata=metadata, secret_key="your-secret-key")  # Optional: secret_key is only needed if you want HMAC verification

# Create a streaming completion
response = litellm.completion(
    model="gpt-4",  # This will be routed through the proxy
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a short paragraph about AI ethics."}
    ],
    stream=True
)

# Process each chunk
full_response = ""
for chunk in response:
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

## Best Practices

1. **Provider-Agnostic Code**: Use LiteLLM to write provider-agnostic code that works with multiple LLM providers.

2. **Include Provider Information**: Always include the provider name in the metadata to track which service generated the content.

3. **Fallback Mechanisms**: Implement fallback mechanisms to switch between providers if one fails.

4. **Consistent Metadata**: Maintain a consistent metadata schema across different providers to simplify downstream processing.

5. **API Key Management**: Use environment variables or a secure key management system to store API keys for different providers.

6. **Error Handling**: Implement proper error handling for both LiteLLM and EncypherAI operations.

7. **Model Selection**: Use LiteLLM's model selection capabilities to choose the most appropriate model for each task.

## Troubleshooting

### API Key Issues

If you encounter authentication errors with LiteLLM:

```python
import os

# Set API keys as environment variables
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-api-key"

# Or configure LiteLLM directly
litellm.set_api_key(api_key="your-api-key", key_type="openai")
litellm.set_api_key(api_key="your-api-key", key_type="anthropic")
```

### Provider-Specific Issues

If you encounter issues with a specific provider:

```python
# Configure provider-specific settings
litellm.set_provider_config(provider="openai", config={
    "timeout": 30,
    "max_retries": 3
})

# Or use a different provider
try:
    response = litellm.completion(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
except Exception as e:
    print(f"OpenAI failed: {str(e)}")
    # Fallback to Anthropic
    response = litellm.completion(
        model="claude-3-opus-20240229",
        messages=[{"role": "user", "content": "Hello"}]
    )
```

### Metadata Extraction Failures

If metadata extraction fails:

1. Ensure the text hasn't been modified after embedding
2. Check if the text has enough suitable targets for embedding
3. Verify you're using the same secret key for embedding and extraction

## Related Documentation

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [EncypherAI Streaming Support](../user-guide/streaming.md)
- [Metadata Encoding Guide](../user-guide/metadata-encoding.md)
- [Extraction and Verification](../user-guide/extraction-verification.md)
