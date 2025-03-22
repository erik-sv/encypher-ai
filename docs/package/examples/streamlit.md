# Streamlit Demo App

The EncypherAI Streamlit demo provides an interactive web-based interface for exploring and testing EncypherAI's functionality. This demo allows users to experiment with metadata embedding, extraction, and verification in real-time through a user-friendly interface.

![Streamlit Demo Preview](../../assets/streamlit-demo-preview.png)

## Features

The Streamlit demo showcases all key EncypherAI capabilities:

1. **Interactive Metadata Embedding**
   - Embed custom metadata into text
   - Choose different embedding targets (whitespace, punctuation, etc.)
   - See real-time results

2. **Metadata Extraction and Visualization**
   - Extract embedded metadata from text
   - View formatted JSON output
   - Compare original and embedded text

3. **HMAC Verification**
   - Test content integrity verification
   - Experiment with secret key management
   - Simulate tampering to see detection in action

4. **Streaming Simulation**
   - Visualize chunk-by-chunk processing
   - See how metadata is distributed in streaming scenarios
   - Understand the streaming workflow

## Running the Demo

To run the Streamlit demo:

```bash
# Install required dependencies
pip install encypher streamlit

# Run the demo app
streamlit run https://raw.githubusercontent.com/EncypherAI/encypher/main/examples/streamlit_app.py
```

Alternatively, you can run it from a local copy:

```bash
# Clone the repository
git clone https://github.com/EncypherAI/encypher.git
cd encypher

# Run the demo app
streamlit run examples/streamlit_app.py
```

## Demo Structure

The Streamlit app is organized into several tabs:

### Basic Embedding

![Basic Embedding Tab](../../assets/streamlit-basic-embedding.png)

This tab allows users to:
- Enter or generate sample text
- Define custom metadata fields
- Choose embedding targets
- See a side-by-side comparison of original and encoded text
- Copy the encoded text to clipboard

### Metadata Extraction

![Metadata Extraction Tab](../../assets/streamlit-extraction.png)

This tab enables users to:
- Paste text containing embedded metadata
- Extract and view the metadata
- See a formatted JSON representation
- Verify the content integrity

### HMAC Verification

![HMAC Verification Tab](../../assets/streamlit-verification.png)

This tab demonstrates security features:
- Configure secret keys for HMAC verification
- Test verification on embedded content
- Simulate tampering and see detection
- Understand how HMAC protects content integrity

### Streaming Demo

![Streaming Demo Tab](../../assets/streamlit-streaming.png)

This tab simulates streaming scenarios:
- See text generated chunk by chunk
- Observe how metadata is handled in streaming
- Control streaming speed and chunk size
- Compare different streaming strategies

## Code Structure

The Streamlit app is built with a modular structure:

```
examples/
└── streamlit_app.py       # Main Streamlit application
    ├── basic_embedding()  # Basic embedding tab
    ├── extraction()       # Metadata extraction tab
    ├── verification()     # HMAC verification tab
    └── streaming_demo()   # Streaming simulation tab
```

## Example Code

Here's a simplified version of the code that powers the basic embedding tab:

```python
def basic_embedding():
    st.header("Basic Metadata Embedding")
    
    # Text input
    sample_text = st.text_area(
        "Enter text to embed metadata into:",
        value="This is a sample text that will have metadata embedded within it. "
              "The metadata will be invisible to human readers but can be extracted "
              "programmatically.",
        height=150
    )
    
    # Metadata input
    with st.expander("Configure Metadata", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            model = st.text_input("Model Name:", value="gpt-4")
            org = st.text_input("Organization:", value="EncypherAI")
        
        with col2:
            timestamp = st.text_input(
                "Timestamp:", 
                value=str(int(time.time()))
            )
            version = st.text_input("Version:", value="1.0.0")
        
        # Additional custom fields
        custom_fields = {}
        if st.checkbox("Add custom metadata fields"):
            for i in range(3):
                c1, c2 = st.columns(2)
                key = c1.text_input(f"Key {i+1}:", key=f"key_{i}")
                value = c2.text_input(f"Value {i+1}:", key=f"value_{i}")
                if key and value:
                    custom_fields[key] = value
    
    # Target selection
    target_options = {
        "Whitespace": "whitespace",
        "Punctuation": "punctuation",
        "First Letter of Words": "first_letter",
        "Last Letter of Words": "last_letter",
        "All Characters": "all_characters"
    }
    
    target = st.selectbox(
        "Where to embed metadata:",
        options=list(target_options.keys()),
        index=0
    )
    
    # Create metadata dictionary
    metadata = {
        "model": model,
        "organization": org,
        "timestamp": int(timestamp) if timestamp.isdigit() else timestamp,
        "version": version,
        **custom_fields
    }
    
    # Secret key for HMAC
    use_custom_key = st.checkbox("Use custom secret key")
    secret_key = None
    if use_custom_key:
        secret_key = st.text_input(
            "Secret Key (for HMAC verification):",
            type="password"
        )
    
    # Embed metadata
    if st.button("Embed Metadata"):
        from encypher.core.metadata_encoder import MetadataEncoder
        
        encoder = MetadataEncoder(secret_key=secret_key)
        
        try:
            with st.spinner("Embedding metadata..."):
                encoded_text = encoder.encode_metadata(
                    sample_text,
                    metadata,
                    target=target_options[target]
                )
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Text")
                st.text_area("", sample_text, height=200, disabled=True)
            
            with col2:
                st.subheader("Encoded Text")
                st.text_area("", encoded_text, height=200, disabled=True)
            
            # Metadata display
            st.subheader("Embedded Metadata")
            st.json(metadata)
            
            # Copy button
            st.button(
                "Copy Encoded Text to Clipboard",
                on_click=lambda: st.write(
                    f'<script>navigator.clipboard.writeText("{encoded_text}");</script>',
                    unsafe_allow_html=True
                )
            )
            
            # Verification status
            verification = encoder.verify_text(encoded_text)
            if verification:
                st.success("✅ Verification successful: Content integrity confirmed")
            else:
                st.error("❌ Verification failed: Content may have been tampered with")
                
        except Exception as e:
            st.error(f"Error embedding metadata: {str(e)}")
```

## Complete Streamlit App

Here's a more complete example of a Streamlit app that demonstrates EncypherAI's capabilities:

```python
import streamlit as st
import time
import json
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import MetadataTarget
from encypher.streaming.handlers import StreamingHandler

# App title and description
st.set_page_config(
    page_title="EncypherAI Demo",
    page_icon="🔐",
    layout="wide"
)

st.title("EncypherAI Demo")
st.markdown(
    "This demo showcases the capabilities of EncypherAI for embedding, "
    "extracting, and verifying metadata in text."
)

# Create tabs
tabs = st.tabs([
    "Basic Embedding", 
    "Metadata Extraction", 
    "HMAC Verification", 
    "Streaming Demo"
])

# Basic Embedding Tab
with tabs[0]:
    st.header("Basic Metadata Embedding")
    
    # Text input
    sample_text = st.text_area(
        "Enter text to embed metadata into:",
        value="This is a sample text that will have metadata embedded within it.",
        height=150
    )
    
    # Metadata configuration
    col1, col2 = st.columns(2)
    
    with col1:
        model = st.text_input("Model:", value="gpt-4")
        org = st.text_input("Organization:", value="EncypherAI")
    
    with col2:
        timestamp = st.text_input("Timestamp:", value=str(int(time.time())))
        version = st.text_input("Version:", value="1.0.0")
    
    # Target selection
    target = st.selectbox(
        "Where to embed metadata:",
        options=["whitespace", "punctuation", "first_letter", "last_letter", "all_characters"],
        index=0
    )
    
    # Create metadata
    metadata = {
        "model": model,
        "organization": org,
        "timestamp": int(timestamp) if timestamp.isdigit() else timestamp,
        "version": version
    }
    
    # Embed button
    if st.button("Embed Metadata", key="embed_btn"):
        encoder = MetadataEncoder()
        
        try:
            encoded_text = encoder.encode_metadata(sample_text, metadata, target=target)
            
            st.subheader("Results")
            st.text_area("Encoded Text:", encoded_text, height=150)
            st.json(metadata)
            
            # Verification
            verified = encoder.verify_text(encoded_text)
            if verified:
                st.success("✅ Verification successful")
            else:
                st.error("❌ Verification failed")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Metadata Extraction Tab
with tabs[1]:
    st.header("Metadata Extraction")
    
    # Text input
    encoded_text = st.text_area(
        "Paste text with embedded metadata:",
        height=150
    )
    
    # Extract button
    if st.button("Extract Metadata", key="extract_btn") and encoded_text:
        encoder = MetadataEncoder()
        
        try:
            # Extract metadata
            extracted_metadata = encoder.decode_metadata(encoded_text)
            
            # Display results
            st.subheader("Extracted Metadata")
            st.json(extracted_metadata)
            
            # Verify
            verified = encoder.verify_text(encoded_text)
            if verified:
                st.success("✅ Content integrity verified")
            else:
                st.warning("⚠️ Content may have been tampered with")
                
        except Exception as e:
            st.error(f"Error extracting metadata: {str(e)}")

# HMAC Verification Tab
with tabs[2]:
    st.header("HMAC Verification")
    
    # Secret key
    secret_key = st.text_input(
        "Secret Key (for HMAC verification):",
        value="my-secret-key",
        type="password"
    )
    
    # Text input
    text = st.text_area(
        "Enter text to embed and verify:",
        value="This text will be protected with HMAC verification.",
        height=100
    )
    
    # Create metadata
    metadata = {
        "model": "verification-demo",
        "timestamp": int(time.time()),
        "version": "1.0.0"
    }
    
    # Embed and verify
    if st.button("Embed and Verify", key="verify_btn"):
        encoder = MetadataEncoder(secret_key=secret_key)
        
        try:
            # Embed metadata
            encoded_text = encoder.encode_metadata(text, metadata)
            
            # Display original text
            st.subheader("Original Text with Metadata")
            st.text_area("", encoded_text, height=100, disabled=True)
            
            # Simulate tampering
            tampered_text = encoded_text + " This text was added after embedding."
            st.subheader("Tampered Text")
            st.text_area("", tampered_text, height=100, disabled=True)
            
            # Verify both versions
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Original Verification")
                verified = encoder.verify_text(encoded_text)
                if verified:
                    st.success("✅ Verification successful")
                else:
                    st.error("❌ Verification failed")
            
            with col2:
                st.subheader("Tampered Verification")
                verified = encoder.verify_text(tampered_text)
                if verified:
                    st.success("✅ Verification successful")
                else:
                    st.error("❌ Verification failed")
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Streaming Demo Tab
with tabs[3]:
    st.header("Streaming Demo")
    
    # Streaming parameters
    st.subheader("Configure Streaming")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chunk_size = st.slider("Chunk Size (words):", 1, 10, 3)
        delay = st.slider("Chunk Delay (seconds):", 0.1, 2.0, 0.5)
    
    with col2:
        metadata = {
            "model": "streaming-demo",
            "timestamp": int(time.time()),
            "version": "1.0.0"
        }
        st.json(metadata)
    
    # Start streaming
    if st.button("Start Streaming Simulation", key="stream_btn"):
        # Sample text split into words
        text = "The quick brown fox jumps over the lazy dog. This is an example of streaming text generation with embedded metadata."
        words = text.split()
        
        # Create chunks
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            if i + chunk_size < len(words):
                chunk += " "
            chunks.append(chunk)
        
        # Initialize streaming handler
        handler = StreamingHandler(metadata=metadata)
        
        # Display streaming progress
        st.subheader("Streaming Progress")
        progress_bar = st.progress(0)
        
        # Container for streaming output
        stream_container = st.empty()
        accumulated_text = ""
        
        # Process chunks
        for i, chunk in enumerate(chunks):
            # Process chunk
            processed_chunk = handler.process_chunk(chunk)
            accumulated_text += processed_chunk
            
            # Update display
            stream_container.text_area("", accumulated_text, height=150, disabled=True)
            progress_bar.progress((i + 1) / len(chunks))
            
            # Delay
            time.sleep(delay)
        
        # Finalize
        final_chunk = handler.finalize()
        if final_chunk:
            accumulated_text += final_chunk
            stream_container.text_area("", accumulated_text, height=150, disabled=True)
        
        # Verify the result
        encoder = MetadataEncoder()
        try:
            extracted_metadata = encoder.decode_metadata(accumulated_text)
            verified = encoder.verify_text(accumulated_text)
            
            st.subheader("Streaming Results")
            st.json(extracted_metadata)
            
            if verified:
                st.success("✅ Streaming metadata verified successfully")
            else:
                st.error("❌ Streaming metadata verification failed")
                
        except Exception as e:
            st.error(f"Error extracting metadata: {str(e)}")
```

## Customizing the Demo

You can customize the Streamlit demo by:

1. **Adding more tabs** for additional functionality
2. **Integrating with LLM APIs** to generate content in real-time
3. **Creating visualization components** to better illustrate how metadata is embedded
4. **Adding file upload/download** capabilities for processing documents

For more information on building Streamlit apps, see the [Streamlit documentation](https://docs.streamlit.io/).
