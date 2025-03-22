# FastAPI Example

This example demonstrates how to build a complete FastAPI application that integrates EncypherAI for metadata embedding and verification. The application provides endpoints for encoding, decoding, and verifying metadata in text.

## Prerequisites

Before you begin, make sure you have:

1. FastAPI and its dependencies installed
2. EncypherAI installed
3. (Optional) An LLM provider API key if you're integrating with an LLM

```bash
uv pip install encypher fastapi uvicorn python-multipart
```

## Complete FastAPI Application

Create a file named `app.py` with the following code:

```python
from fastapi import FastAPI, HTTPException, Request, Depends, Form
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import MetadataTarget
from encypher.streaming.handlers import StreamingHandler
import time
import json
import os
import secrets

# Initialize FastAPI app
app = FastAPI(
    title="EncypherAI Demo",
    description="API for embedding and extracting metadata in text",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get secret key from environment or generate a random one
SECRET_KEY = os.getenv("ENCYPHER_SECRET_KEY", secrets.token_hex(32))

# Create a metadata encoder
encoder = MetadataEncoder(secret_key=SECRET_KEY)

# Define request and response models
class EncodeRequest(BaseModel):
    text: str
    metadata: Dict[str, Any]
    target: Optional[str] = "whitespace"

class VerifyRequest(BaseModel):
    text: str

class MetadataResponse(BaseModel):
    has_metadata: bool
    metadata: Optional[Dict[str, Any]] = None
    verified: Optional[bool] = None
    error: Optional[str] = None

# Set up templates
templates = Jinja2Templates(directory="templates")

# Create templates directory and files
os.makedirs("templates", exist_ok=True)

# Create index.html template
with open("templates/index.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>EncypherAI Demo</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .result-box {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            padding: 1rem;
            margin-top: 1rem;
        }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <div class="container my-5">
        <h1 class="mb-4">EncypherAI Demo</h1>
        
        <ul class="nav nav-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="encode-tab" data-bs-toggle="tab" data-bs-target="#encode" type="button" role="tab" aria-controls="encode" aria-selected="true">Encode</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="verify-tab" data-bs-toggle="tab" data-bs-target="#verify" type="button" role="tab" aria-controls="verify" aria-selected="false">Verify</button>
            </li>
        </ul>
        
        <div class="tab-content" id="myTabContent">
            <!-- Encode Tab -->
            <div class="tab-pane fade show active" id="encode" role="tabpanel" aria-labelledby="encode-tab">
                <div class="my-4">
                    <h3>Embed Metadata</h3>
                    <form id="encodeForm">
                        <div class="mb-3">
                            <label for="text" class="form-label">Text</label>
                            <textarea class="form-control" id="text" name="text" rows="5" required>This is a sample text that will have metadata embedded within it.</textarea>
                        </div>
                        <div class="mb-3">
                            <label for="metadata" class="form-label">Metadata (JSON)</label>
                            <textarea class="form-control" id="metadata" name="metadata" rows="5" required>{
    "model": "gpt-4",
    "organization": "EncypherAI",
    "timestamp": 1742713200,
    "version": "1.0.0"
}</textarea>
                        </div>
                        <div class="mb-3">
                            <label for="target" class="form-label">Target</label>
                            <select class="form-select" id="target" name="target">
                                <option value="whitespace">Whitespace</option>
                                <option value="punctuation">Punctuation</option>
                                <option value="first_letter">First Letter</option>
                                <option value="last_letter">Last Letter</option>
                                <option value="all_characters">All Characters</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary">Encode</button>
                    </form>
                    
                    <div id="encodeResult" class="result-box d-none">
                        <h4>Result</h4>
                        <div class="mb-3">
                            <h5>Original Text</h5>
                            <pre id="originalText"></pre>
                        </div>
                        <div class="mb-3">
                            <h5>Encoded Text</h5>
                            <pre id="encodedText"></pre>
                        </div>
                        <div class="mb-3">
                            <h5>Metadata</h5>
                            <pre id="encodedMetadata"></pre>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Verify Tab -->
            <div class="tab-pane fade" id="verify" role="tabpanel" aria-labelledby="verify-tab">
                <div class="my-4">
                    <h3>Extract and Verify Metadata</h3>
                    <form id="verifyForm">
                        <div class="mb-3">
                            <label for="verifyText" class="form-label">Text with Embedded Metadata</label>
                            <textarea class="form-control" id="verifyText" name="text" rows="5" required>Paste text with embedded metadata here...</textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Verify</button>
                    </form>
                    
                    <div id="verifyResult" class="result-box d-none">
                        <h4>Result</h4>
                        <div id="verifyStatus"></div>
                        <div class="mb-3">
                            <h5>Extracted Metadata</h5>
                            <pre id="extractedMetadata"></pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('encodeForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const text = document.getElementById('text').value;
            const metadata = document.getElementById('metadata').value;
            const target = document.getElementById('target').value;
            
            try {
                const response = await fetch('/api/encode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: text,
                        metadata: JSON.parse(metadata),
                        target: target
                    })
                });
                
                const data = await response.json();
                
                document.getElementById('originalText').textContent = text;
                document.getElementById('encodedText').textContent = data.text;
                document.getElementById('encodedMetadata').textContent = JSON.stringify(data.metadata, null, 2);
                document.getElementById('encodeResult').classList.remove('d-none');
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
        
        document.getElementById('verifyForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const text = document.getElementById('verifyText').value;
            
            try {
                const response = await fetch('/api/verify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: text
                    })
                });
                
                const data = await response.json();
                
                let statusHtml = '';
                if (data.has_metadata) {
                    if (data.verified) {
                        statusHtml = '<div class="alert alert-success">✅ Metadata verified successfully!</div>';
                    } else {
                        statusHtml = '<div class="alert alert-warning">⚠️ Metadata found but verification failed. The text may have been tampered with.</div>';
                    }
                    document.getElementById('extractedMetadata').textContent = JSON.stringify(data.metadata, null, 2);
                } else {
                    statusHtml = '<div class="alert alert-danger">❌ No metadata found or extraction failed: ' + data.error + '</div>';
                    document.getElementById('extractedMetadata').textContent = 'No metadata found';
                }
                
                document.getElementById('verifyStatus').innerHTML = statusHtml;
                document.getElementById('verifyResult').classList.remove('d-none');
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    </script>
</body>
</html>
    """)

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/encode")
async def encode_metadata(request: EncodeRequest):
    """Embed metadata into text"""
    try:
        # Add timestamp if not provided
        if "timestamp" not in request.metadata:
            request.metadata["timestamp"] = int(time.time())
        
        # Embed metadata
        encoded_text = encoder.encode_metadata(
            text=request.text,
            metadata=request.metadata,
            target=request.target
        )
        
        return {
            "text": encoded_text,
            "metadata": request.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/decode", response_model=MetadataResponse)
async def decode_metadata(request: VerifyRequest):
    """Extract metadata from text"""
    result = {
        "has_metadata": False,
        "metadata": None,
        "verified": None,
        "error": None
    }
    
    try:
        # Extract metadata
        metadata = encoder.decode_metadata(request.text)
        result["has_metadata"] = True
        result["metadata"] = metadata
    except Exception as e:
        result["error"] = str(e)
    
    return result

@app.post("/api/verify", response_model=MetadataResponse)
async def verify_text(request: VerifyRequest):
    """Extract and verify metadata from text"""
    result = {
        "has_metadata": False,
        "metadata": None,
        "verified": None,
        "error": None
    }
    
    try:
        # Extract metadata
        metadata = encoder.decode_metadata(request.text)
        result["has_metadata"] = True
        result["metadata"] = metadata
        
        # Verify the text
        result["verified"] = encoder.verify_text(request.text)
    except Exception as e:
        result["error"] = str(e)
    
    return result

# Optional: OpenAI integration endpoint
@app.post("/api/generate")
async def generate_with_openai(
    prompt: str = Form(...),
    model: str = Form("gpt-4"),
    stream: bool = Form(False)
):
    """Generate text with OpenAI and embed metadata"""
    try:
        import openai
        
        # Check if API key is set
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return JSONResponse(
                status_code=400,
                content={"error": "OpenAI API key not set. Set the OPENAI_API_KEY environment variable."}
            )
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create metadata
        metadata = {
            "model": model,
            "organization": "EncypherAI",
            "timestamp": int(time.time()),
            "prompt": prompt
        }
        
        # Handle streaming
        if stream:
            return StreamingResponse(
                generate_stream(client, model, prompt, metadata),
                media_type="text/plain"
            )
        
        # Create a completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Get the response text
        text = response.choices[0].message.content
        
        # Update metadata with usage information
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
    except ImportError:
        return JSONResponse(
            status_code=400,
            content={"error": "OpenAI package not installed. Install it with 'uv pip install openai'."}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

async def generate_stream(client, model, prompt, metadata):
    """Generate a streaming response with OpenAI and embed metadata"""
    try:
        # Initialize the streaming handler
        handler = StreamingHandler(metadata=metadata)
        
        # Create a streaming completion
        completion = client.chat.completions.create(
            model=model,
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
        final_chunk = handler.finalize()
        if final_chunk:
            yield final_chunk
    except Exception as e:
        yield f"Error: {str(e)}"

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Running the Application

1. Save the code above to a file named `app.py`
2. Run the application:

```bash
uvicorn app:app --reload
```

3. Open your browser and navigate to `http://localhost:8000`

## Application Features

The application provides:

1. **Web Interface**:
   - A form for embedding metadata into text
   - A form for extracting and verifying metadata from text
   - Visual indicators for verification status

2. **API Endpoints**:
   - `/api/encode` - Embed metadata into text
   - `/api/decode` - Extract metadata from text
   - `/api/verify` - Extract and verify metadata from text
   - `/api/generate` - (Optional) Generate text with OpenAI and embed metadata

## API Usage Examples

### Embedding Metadata

```python
import requests
import json
import time

# Endpoint
url = "http://localhost:8000/api/encode"

# Data
data = {
    "text": "This is a sample text that will have metadata embedded within it.",
    "metadata": {
        "model": "gpt-4",
        "organization": "EncypherAI",
        "timestamp": int(time.time()),
        "version": "1.0.0"
    },
    "target": "whitespace"
}

# Send request
response = requests.post(url, json=data)
result = response.json()

# Print result
print("Encoded text:")
print(result["text"])
print("\nMetadata:")
print(json.dumps(result["metadata"], indent=2))
```

### Verifying Metadata

```python
import requests
import json

# Endpoint
url = "http://localhost:8000/api/verify"

# Data
data = {
    "text": "Your text with embedded metadata here..."
}

# Send request
response = requests.post(url, json=data)
result = response.json()

# Print result
if result["has_metadata"]:
    print(f"Verification result: {'✅ Verified' if result['verified'] else '❌ Failed'}")
    print("\nExtracted metadata:")
    print(json.dumps(result["metadata"], indent=2))
else:
    print(f"No metadata found: {result['error']}")
```

## Customization

### Adding Authentication

To add API key authentication:

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN

# Define API key header
API_KEY = os.getenv("API_KEY", "your-api-key")  # Use environment variable in production
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Dependency for API key validation
async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key"
    )

# Protected endpoint
@app.post("/api/encode", dependencies=[Depends(get_api_key)])
async def encode_metadata(request: EncodeRequest):
    # Your implementation here
    pass
```

### Adding Rate Limiting

To add rate limiting:

```python
from fastapi import Request
from fastapi.middleware.base import BaseHTTPMiddleware
import time

# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_minute: int = 60
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Get current time
        current_time = time.time()
        
        # Clean up old requests
        self.request_counts = {
            ip: [timestamp for timestamp in timestamps if current_time - timestamp < 60]
            for ip, timestamps in self.request_counts.items()
        }
        
        # Check rate limit
        if client_ip in self.request_counts and len(self.request_counts[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded. Try again later."}
            )
        
        # Add request timestamp
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        self.request_counts[client_ip].append(current_time)
        
        # Process request
        return await call_next(request)

# Add middleware to app
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60
)
