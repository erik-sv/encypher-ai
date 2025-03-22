# EncypherAI

<div align="center">
  <img src="../../assets/horizontal-logo.png" alt="EncypherAI Logo" width="600"/>
  <h2>Invisible Metadata for AI-Generated Text</h2>
</div>

## Overview

EncypherAI is an open-source Python package that enables invisible metadata embedding in AI-generated text using zero-width characters.

With EncypherAI, you can:

- **Embed invisible metadata** in AI-generated text without altering its visible appearance
- **Verify content authenticity** using HMAC signatures
- **Detect tampering** of AI-generated content
- **Support streaming** responses from LLM providers
- **Track provenance** of AI-generated content

## Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **Invisible Embedding** | Add metadata without changing visible content |
| 🔐 **HMAC Verification** | Ensure data integrity and detect tampering |
| 🌊 **Streaming Support** | Compatible with chunk-by-chunk streaming |
| 🔄 **Extensible API** | Easily integrate with any LLM provider |

## Quick Links

- [Installation](getting-started/installation.md)
- [Quick Start Guide](getting-started/quickstart.md)
- [Examples](examples/jupyter.md)
- [GitHub Repository](https://github.com/erik-sv/encypher_ai)

## Why EncypherAI?

As AI-generated content becomes more prevalent, establishing provenance and ensuring integrity becomes critical. EncypherAI addresses these needs by providing a simple way to invisibly embed metadata that can later be verified.

```python
from encypher.core import MetadataEncoder

# Initialize encoder with a secret key for HMAC verification
encoder = MetadataEncoder(secret_key="your-secret-key")

# Embed metadata in AI-generated text
metadata = {
    "model_id": "gpt-4",
    "timestamp": "2023-10-15T14:30:00Z",
    "organization": "EncypherAI"
}
text = "This is AI-generated content with invisible metadata."
encoded_text = encoder.encode_metadata(text, metadata)

# Later, verify and extract metadata
is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)
```

## License

EncypherAI is released under the GNU Affero General Public License v3.0 (AGPL-3.0).
