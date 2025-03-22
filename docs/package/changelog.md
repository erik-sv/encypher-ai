# Changelog

This document provides a chronological list of notable changes for each version of EncypherAI.

## 1.0.0 (03-22-2025)

### Added
- Initial stable release of EncypherAI
- Core metadata encoding and decoding functionality
- HMAC verification for tamper detection
- Support for multiple embedding targets:
  - Whitespace (default)
  - Punctuation
  - First letter of words
  - Last letter of words
  - All characters
- Streaming support for handling content from LLMs
- Integration with popular LLM providers:
  - OpenAI
  - Anthropic
  - LiteLLM
- Comprehensive documentation and examples
- Interactive demos:
  - Jupyter Notebook demo
  - Streamlit web app
  - FastAPI example application
- Python client library
- JavaScript client library

### Security
- Secure HMAC verification using SHA-256
- Secret key management for verification
- Tamper detection capabilities

## Future Plans

### Upcoming in 1.1.0
- Enhanced performance for large texts
- Advanced tamper detection features
- Extended LLM provider integrations

### Planned for 2.0.0
- Binary data embedding support
- Advanced compression for metadata
- Multi-language client libraries
- Enhanced security features
- Real-time verification API
- Blockchain verification support
