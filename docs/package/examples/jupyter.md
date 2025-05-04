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
from encypher.core.unicode_metadata import UnicodeMetadata
from encypher.core.keys import generate_key_pair
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from typing import Optional, Dict
import time
import json

# Display the version
print(f"EncypherAI version: {encypher.__version__}")

# Generate a key pair for digital signatures
private_key, public_key = generate_key_pair()
key_id = "jupyter-example-key"

# Store public key (in a real application, use a secure database)
public_keys = {key_id: public_key}

# Create a resolver function
def resolve_public_key(key_id: str) -> Optional[PublicKeyTypes]:
    return public_keys.get(key_id)

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
    "version": "2.1.0",
    "key_id": key_id  # Required for verification
}

# Display the metadata
print("Metadata to embed:")
print(json.dumps(metadata, indent=2))

# Embed metadata
encoded_text = UnicodeMetadata.embed_metadata(
    text=original_text,
    metadata=metadata,
    private_key=private_key,
    target="whitespace"
)

# Display the original and encoded text
print("\nOriginal text:")
print(original_text)

print("\nEncoded text (looks identical but contains embedded metadata):")
print(encoded_text)

# Extract metadata
extracted_metadata = UnicodeMetadata.extract_metadata(encoded_text)

# Display the extracted metadata
print("\nExtracted metadata:")
print(json.dumps(extracted_metadata, indent=2))

# Verify the text hasn't been tampered with
is_valid, verified_metadata = UnicodeMetadata.verify_metadata(
    text=encoded_text,
    public_key_resolver=resolve_public_key
)

print(f"\nVerification result: {'✅ Verified' if is_valid else '❌ Failed'}")
```

## Interactive Visualization Notebook

This more advanced notebook demonstrates how to visualize the embedded metadata:

```python
# Import necessary libraries
import encypher
from encypher.core.unicode_metadata import MetadataTarget, UnicodeMetadata
from encypher.core.keys import generate_key_pair
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from typing import Optional, Dict
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display, HTML
import pandas as pd
import time
import json

# Generate a key pair for digital signatures
private_key, public_key = generate_key_pair()
key_id = "jupyter-viz-key"

# Store public key (in a real application, use a secure database)
public_keys = {key_id: public_key}

# Create a resolver function
def resolve_public_key(key_id: str) -> Optional[PublicKeyTypes]:
    return public_keys.get(key_id)

# Sample text
original_text = "This is a sample text that will have metadata embedded within it."

# Create metadata
metadata = {
    "model": "example-model",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "2.1.0",
    "key_id": key_id  # Required for verification
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
    encoded_texts[target.name] = UnicodeMetadata.embed_metadata(
        text=original_text,
        metadata=metadata,
        private_key=private_key,
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
    extracted = UnicodeMetadata.extract_metadata(encoded_texts[target.name])
    is_valid, verified_metadata = UnicodeMetadata.verify_metadata(
        text=encoded_texts[target.name],
        public_key_resolver=resolve_public_key
    )

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
from encypher.core.unicode_metadata import MetadataTarget, UnicodeMetadata
from encypher.core.keys import generate_key_pair
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from typing import Optional, Dict
import json
import time
from IPython.display import clear_output

# Generate a key pair for digital signatures
private_key, public_key = generate_key_pair()
key_id = "jupyter-stream-key"

# Store public key (in a real application, use a secure database)
public_keys = {key_id: public_key}

# Create a resolver function
def resolve_public_key(key_id: str) -> Optional[PublicKeyTypes]:
    return public_keys.get(key_id)

# Create metadata
metadata = {
    "model": "streaming-example",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "2.1.0",
    "key_id": key_id  # Required for verification
}

# Create a streaming handler
streaming_handler = StreamingHandler(
    metadata=metadata,
    private_key=private_key,
    target=MetadataTarget.WHITESPACE,
    encode_first_chunk_only=True
)

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
    processed_chunk = streaming_handler.process_chunk(chunk)

    # Accumulate the text
    full_text += processed_chunk

    # Display progress
    clear_output(wait=True)
    print(f"Processed {i+1}/{len(chunks)} chunks")
    print(f"Current text: {full_text}")

    # Simulate delay
    time.sleep(0.5)

# Finalize the stream
final_chunk = streaming_handler.finalize()
if final_chunk:
    full_text += final_chunk

# Display the final text
clear_output(wait=True)
print("Final text with embedded metadata:")
print(full_text)

# Verify the complete response
is_valid, verified_metadata = UnicodeMetadata.verify_metadata(
    text=full_text,
    public_key_resolver=resolve_public_key
)

print(f"\nVerification result: {'✅ Verified' if is_valid else '❌ Failed'}")
if is_valid:
    print(f"Verified metadata: {json.dumps(verified_metadata, indent=2)}")
```

## Tamper Detection Notebook

This notebook demonstrates how EncypherAI can detect tampering:

```python
# Import necessary libraries
import encypher
from encypher.core.unicode_metadata import UnicodeMetadata
from encypher.core.keys import generate_key_pair
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from typing import Optional, Dict
import json
import time
import pandas as pd
from IPython.display import display, HTML

# Generate a key pair for digital signatures
private_key, public_key = generate_key_pair()
key_id = "jupyter-tamper-key"

# Store public key (in a real application, use a secure database)
public_keys = {key_id: public_key}

# Create a resolver function
def resolve_public_key(key_id: str) -> Optional[PublicKeyTypes]:
    return public_keys.get(key_id)

# Sample text
original_text = "This is a sample text that will be used to demonstrate tamper detection."

# Create metadata
metadata = {
    "model": "tamper-detection-demo",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "2.1.0",
    "key_id": key_id  # Required for verification
}

# Embed metadata
encoded_text = UnicodeMetadata.embed_metadata(
    text=original_text,
    metadata=metadata,
    private_key=private_key
)

# Create tampered versions
tampered_versions = {
    "Original (No Tampering)": encoded_text,
    "Content Changed": encoded_text.replace("sample", "modified"),
    "Metadata Removed": original_text,
    "Partial Metadata": encoded_text[:len(encoded_text)//2] + original_text[len(original_text)//2:]
}

# Test each version
results = []
for name, text in tampered_versions.items():
    # Try to extract metadata
    try:
        extracted = UnicodeMetadata.extract_metadata(text)
        metadata_found = bool(extracted)
    except:
        extracted = None
        metadata_found = False

    # Try to verify
    try:
        is_valid, verified_metadata = UnicodeMetadata.verify_metadata(
            text=text,
            public_key_resolver=resolve_public_key
        )
    except:
        is_valid = False
        verified_metadata = None

    results.append({
        "Version": name,
        "Metadata Found": "✅ Yes" if metadata_found else "❌ No",
        "Verification Passed": "✅ Passed" if is_valid else "❌ Failed",
        "Extracted Metadata": json.dumps(extracted, indent=2) if extracted else "None"
    })

# Display results
df = pd.DataFrame(results)
display(HTML("<h3>Tamper Detection Results</h3>"))
display(df)
```

## Advanced: Custom Metadata Encoder

This notebook demonstrates how to create a custom metadata encoder:

```python
# Import necessary libraries
import encypher
from encypher.core.unicode_metadata import UnicodeMetadata
from encypher.core.keys import generate_key_pair
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from typing import Optional, Dict
import time
import json
import hashlib

# Create a custom metadata encoder class
class CustomMetadataEncoder:
    def __init__(self, private_key, custom_prefix="custom"):
        self.private_key = private_key
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
        return UnicodeMetadata.embed_metadata(
            text=text,
            metadata=metadata,
            private_key=self.private_key,
            target=target
        )

    def decode_metadata(self, text):
        # Extract metadata using parent class
        metadata = UnicodeMetadata.extract_metadata(text)

        # Filter out non-custom fields
        return {k.replace(f"{self.custom_prefix}_", ""): v
                for k, v in metadata.items()
                if k.startswith(f"{self.custom_prefix}_")}

# Create an instance of the custom encoder
private_key, _ = generate_key_pair()
custom_encoder = CustomMetadataEncoder(private_key, custom_prefix="myapp")

# Sample text
text = "This text will have custom metadata embedded."

# Create metadata
metadata = {
    "model": "custom-example",
    "user_id": "user123",
    "version": "2.1.0"
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
