# Jupyter Notebook Examples

This page provides examples of using EncypherAI in Jupyter Notebooks, allowing you to interactively explore and experiment with the library's features.

## Getting Started with Jupyter

If you don't already have Jupyter installed, you can install it along with EncypherAI:

```bash
pip install encypher jupyter
```

## Basic Example Notebook

Below is a basic example of using EncypherAI in a Jupyter notebook. You can copy this code into a new notebook to get started.

```python
# Import necessary libraries
import encypher
from encypher.core.metadata_encoder import MetadataEncoder
import time
import json

# Display the version
print(f"EncypherAI version: {encypher.__version__}")

# Create a metadata encoder
encoder = MetadataEncoder()

# Sample text
original_text = """
Artificial intelligence (AI) is intelligence demonstrated by machines, 
as opposed to natural intelligence displayed by animals including humans. 
AI research has been defined as the field of study of intelligent agents, 
which refers to any system that perceives its environment and takes actions 
that maximize its chance of achieving its goals.
"""

# Create metadata
metadata = {
    "model": "example-model",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "1.1.0"
}

# Display the metadata
print("Metadata to embed:")
print(json.dumps(metadata, indent=2))

# Embed metadata
encoded_text = encoder.encode_metadata(original_text, metadata)

# Display the original and encoded text
print("\nOriginal text:")
print(original_text)

print("\nEncoded text (looks identical but contains embedded metadata):")
print(encoded_text)

# Extract metadata
extracted_metadata = encoder.decode_metadata(encoded_text)

# Display the extracted metadata
print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))

# Verify the text hasn't been tampered with
is_valid, verified_metadata = UnicodeMetadata.verify_metadata(encoded_text, hmac_secret_key="your-secret-key")

print(f"\nVerification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## Interactive Visualization Notebook

This more advanced notebook demonstrates how to visualize the embedded metadata:

```python
# Import necessary libraries
import encypher
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import MetadataTarget, UnicodeMetadata
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display, HTML
import pandas as pd
import time
import json

# Create a metadata encoder
encoder = MetadataEncoder()

# Sample text
original_text = "This is a sample text that will have metadata embedded within it."

# Create metadata
metadata = {
    "model": "example-model",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "1.1.0"
}

# Embed metadata with different targets
targets = [
    MetadataTarget.WHITESPACE,
    MetadataTarget.PUNCTUATION,
    MetadataTarget.FIRST_LETTER,
    MetadataTarget.LAST_LETTER,
    MetadataTarget.ALL_CHARACTERS
]

encoded_texts = {}
for target in targets:
    encoded_texts[target.name] = encoder.encode_metadata(
        original_text, 
        metadata, 
        target=target
    )

# Create a DataFrame to compare
df = pd.DataFrame({
    'Target': [target.name for target in targets],
    'Text Length (Original)': [len(original_text)] * len(targets),
    'Text Length (Encoded)': [len(encoded_texts[target.name]) for target in targets],
    'Unicode Characters Added': [len(encoded_texts[target.name]) - len(original_text) for target in targets]
})

# Display the comparison table
display(HTML("<h3>Comparison of Encoding Targets</h3>"))
display(df)

# Visualize the character distribution
def visualize_unicode_distribution(text, title):
    # Get the Unicode code points
    code_points = [ord(c) for c in text]
    
    # Create a histogram
    plt.figure(figsize=(12, 6))
    plt.hist(code_points, bins=50, alpha=0.7)
    plt.title(title)
    plt.xlabel('Unicode Code Point')
    plt.ylabel('Frequency')
    plt.yscale('log')  # Log scale for better visualization
    plt.grid(True, alpha=0.3)
    plt.show()

# Visualize the original and encoded text
visualize_unicode_distribution(original_text, 'Unicode Distribution in Original Text')
visualize_unicode_distribution(
    encoded_texts[MetadataTarget.WHITESPACE.name], 
    'Unicode Distribution in Encoded Text (WHITESPACE target)'
)

# Highlight the variation selectors
def highlight_variation_selectors(text):
    html_parts = []
    for char in text:
        code_point = ord(char)
        if UnicodeMetadata.is_variation_selector(char):
            # Highlight variation selectors in red
            html_parts.append(f'<span style="color:red;background-color:#ffeeee;" title="U+{code_point:04X}">VS</span>')
        else:
            # Regular characters
            html_parts.append(char)
    return ''.join(html_parts)

# Display the highlighted text
display(HTML("<h3>Visualization of Embedded Metadata</h3>"))
display(HTML("<p>Characters in red (VS) represent Unicode variation selectors used to embed metadata.</p>"))

for target in targets:
    display(HTML(f"<h4>Target: {target.name}</h4>"))
    display(HTML(highlight_variation_selectors(encoded_texts[target.name])))

# Extract and verify metadata
for target in targets:
    extracted = encoder.decode_metadata(encoded_texts[target.name])
    is_valid, verified_metadata = UnicodeMetadata.verify_metadata(encoded_texts[target.name], hmac_secret_key="your-secret-key")
    
    print(f"\nTarget: {target.name}")
    print(f"Metadata extracted: {json.dumps(extracted, indent=2)}")
    print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## Streaming Example Notebook

This notebook demonstrates how to use EncypherAI with streaming content:

```python
# Import necessary libraries
import encypher
from encypher.streaming.handlers import StreamingHandler
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import MetadataTarget
import json
import time
from IPython.display import clear_output

# Create metadata
metadata = {
    "model": "streaming-example",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "1.1.0"
}

# Create a streaming handler
handler = StreamingHandler(metadata=metadata)

# Simulate a streaming response
chunks = [
    "The quick ",
    "brown fox ",
    "jumps over ",
    "the lazy dog. ",
    "This is an example ",
    "of streaming text ",
    "with embedded metadata."
]

# Process the stream
print("Processing stream...")
full_text = ""
for i, chunk in enumerate(chunks):
    # Process the chunk
    processed_chunk = handler.process_chunk(chunk)
    
    # Accumulate the text
    full_text += processed_chunk
    
    # Display progress
    clear_output(wait=True)
    print(f"Processed {i+1}/{len(chunks)} chunks")
    print(f"Current text: {full_text}")
    
    # Simulate delay
    time.sleep(0.5)

# Finalize the stream
final_chunk = handler.finalize()
if final_chunk:
    full_text += final_chunk

# Display the final text
clear_output(wait=True)
print("Final text with embedded metadata:")
print(full_text)

# Extract and verify the metadata
encoder = MetadataEncoder()
extracted_metadata = encoder.decode_metadata(full_text)
is_valid, verified_metadata = UnicodeMetadata.verify_metadata(full_text, hmac_secret_key="your-secret-key")

print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))
print(f"\nVerification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## Tamper Detection Example

This notebook demonstrates how EncypherAI can detect tampering with AI-generated content:

```python
# Import necessary libraries
import encypher
from encypher.core.metadata_encoder import MetadataEncoder
import time
import json

# Create a metadata encoder
encoder = MetadataEncoder(secret_key="my-secret-key")

# Original text
original_text = "This is an example of AI-generated content that will be protected against tampering."

# Create metadata
metadata = {
    "model": "tamper-detection-example",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "1.1.0"
}

# Embed metadata
encoded_text = encoder.encode_metadata(original_text, metadata)

print("Original text with embedded metadata:")
print(encoded_text)
print("\nMetadata:")
print(json.dumps(metadata, indent=2))

# Verify the original text
is_valid, verified_metadata = UnicodeMetadata.verify_metadata(encoded_text, hmac_secret_key="my-secret-key")
print(f"\nVerification result (original): {'✅ Verified' if is_valid else '❌ Failed'}")

# Create tampered versions
tampered_versions = {
    "Addition": encoded_text + " This text was added.",
    "Deletion": encoded_text[:len(encoded_text)//2],
    "Modification": encoded_text.replace("AI-generated", "human-written"),
    "Untampered": encoded_text
}

# Check each version
print("\nTamper Detection Results:")
print("-" * 50)

for name, text in tampered_versions.items():
    # Try to extract metadata
    try:
        extracted = encoder.decode_metadata(text)
        metadata_found = bool(extracted)
    except:
        metadata_found = False
    
    # Try to verify
    try:
        is_valid, verified_metadata = UnicodeMetadata.verify_metadata(text, hmac_secret_key="my-secret-key")
    except:
        is_valid = False
    
    # Print results
    print(f"\n{name}:")
    print(f"Text: {text[:50]}..." if len(text) > 50 else f"Text: {text}")
    print(f"Metadata found: {'Yes' if metadata_found else 'No'}")
    print(f"Verification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## Advanced: Custom Metadata Encoder

This notebook demonstrates how to create a custom metadata encoder:

```python
# Import necessary libraries
import encypher
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.core.unicode_metadata import UnicodeMetadata, MetadataTarget
import time
import json
import hashlib

# Create a custom metadata encoder class
class CustomMetadataEncoder(MetadataEncoder):
    def __init__(self, secret_key=None, custom_prefix="custom"):
        super().__init__(secret_key=secret_key)
        self.custom_prefix = custom_prefix
    
    def encode_metadata(self, text, metadata, target="whitespace"):
        # Add custom prefix to metadata
        metadata = {f"{self.custom_prefix}_{k}": v for k, v in metadata.items()}
        
        # Add timestamp if not present
        if f"{self.custom_prefix}_timestamp" not in metadata:
            metadata[f"{self.custom_prefix}_timestamp"] = int(time.time())
        
        # Add a hash of the text
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        metadata[f"{self.custom_prefix}_text_hash"] = text_hash
        
        # Use the parent class to encode
        return super().encode_metadata(text, metadata, target)
    
    def decode_metadata(self, text):
        # Extract metadata using parent class
        metadata = super().decode_metadata(text)
        
        # Filter out non-custom fields
        return {k.replace(f"{self.custom_prefix}_", ""): v 
                for k, v in metadata.items() 
                if k.startswith(f"{self.custom_prefix}_")}

# Create an instance of the custom encoder
custom_encoder = CustomMetadataEncoder(secret_key="my-custom-key", custom_prefix="myapp")

# Sample text
text = "This text will have custom metadata embedded."

# Create metadata
metadata = {
    "model": "custom-example",
    "user_id": "user123",
    "version": "1.1.0"
}

# Embed metadata
encoded_text = custom_encoder.encode_metadata(text, metadata)

print("Text with custom metadata:")
print(encoded_text)

# Extract metadata
extracted = custom_encoder.decode_metadata(encoded_text)

print("\nExtracted custom metadata:")
print(json.dumps(extracted, indent=2))
```

These examples should help you get started with EncypherAI in Jupyter notebooks. Feel free to modify and experiment with them to explore the library's capabilities.