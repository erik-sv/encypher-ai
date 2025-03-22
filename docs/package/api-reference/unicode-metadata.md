# UnicodeMetadata

The `UnicodeMetadata` class provides low-level utilities for embedding and extracting metadata using Unicode variation selectors. This class is primarily used internally by the `MetadataEncoder` but can be used directly for advanced customization.

## Overview

Unicode variation selectors are special characters that modify the appearance of the preceding character. EncypherAI uses a specific range of these selectors (VS1-VS256) to encode binary data within text without changing its visible appearance.

The `UnicodeMetadata` class provides methods to:

1. Convert binary data to and from variation selectors
2. Find suitable targets in text for embedding metadata
3. Embed and extract metadata at the character level

## Class Definition

```python
class UnicodeMetadata:
    """
    Utilities for embedding and extracting metadata using Unicode variation selectors.
    """
    
    # Unicode variation selector range (VS1-VS256)
    VARIATION_SELECTOR_START = 0xFE00  # VS1
    VARIATION_SELECTOR_END = 0xFE0F    # VS16 (first range)
    VARIATION_SELECTOR_START_2 = 0xE0100  # VS17
    VARIATION_SELECTOR_END_2 = 0xE01EF    # VS256 (second range)
```

## Class Methods

### to_variation_selector

```python
@classmethod
def to_variation_selector(cls, byte: int) -> Optional[str]:
    """
    Convert a byte value (0-255) to a Unicode variation selector.
    
    Args:
        byte: Integer value between 0-255
        
    Returns:
        Unicode variation selector character or None if the byte is out of range
    """
```

### from_variation_selector

```python
@classmethod
def from_variation_selector(cls, char: str) -> Optional[int]:
    """
    Convert a Unicode variation selector to its byte value.
    
    Args:
        char: Unicode variation selector character
        
    Returns:
        Integer value between 0-255 or None if the character is not a variation selector
    """
```

### is_variation_selector

```python
@classmethod
def is_variation_selector(cls, char: str) -> bool:
    """
    Check if a character is a Unicode variation selector.
    
    Args:
        char: Character to check
        
    Returns:
        True if the character is a variation selector, False otherwise
    """
```

### find_targets

```python
@classmethod
def find_targets(
    cls, 
    text: str, 
    target: Union[str, MetadataTarget] = "whitespace"
) -> List[int]:
    """
    Find suitable target positions in text for embedding metadata.
    
    Args:
        text: The text to analyze
        target: Where to embed metadata. Can be a string ("whitespace", "punctuation", 
               "first_letter", "last_letter", "all_characters") or a MetadataTarget enum.
        
    Returns:
        List of character indices that are suitable for embedding metadata
    """
```

### embed_bytes

```python
@classmethod
def embed_bytes(
    cls, 
    text: str, 
    data: bytes, 
    target: Union[str, MetadataTarget] = "whitespace"
) -> str:
    """
    Embed binary data into text using Unicode variation selectors.
    
    Args:
        text: The text to embed data into
        data: Binary data to embed
        target: Where to embed data. Can be a string ("whitespace", "punctuation", 
               "first_letter", "last_letter", "all_characters") or a MetadataTarget enum.
        
    Returns:
        Text with embedded data
    
    Raises:
        ValueError: If there are not enough targets to embed all data
    """
```

### extract_bytes

```python
@classmethod
def extract_bytes(cls, text: str) -> bytes:
    """
    Extract binary data embedded in text using Unicode variation selectors.
    
    Args:
        text: Text with embedded data
        
    Returns:
        Extracted binary data
    """
```

## MetadataTarget Enum

The `MetadataTarget` enum defines the possible targets for embedding metadata:

```python
class MetadataTarget(Enum):
    """
    Enum for specifying where to embed metadata in text.
    """
    WHITESPACE = "whitespace"
    PUNCTUATION = "punctuation"
    FIRST_LETTER = "first_letter"
    LAST_LETTER = "last_letter"
    ALL_CHARACTERS = "all_characters"
```

## Usage Example

```python
from encypher.core.unicode_metadata import UnicodeMetadata, MetadataTarget
import time

# Sample text
text = "This is a sample text for embedding metadata."

# Find suitable targets for embedding
whitespace_targets = UnicodeMetadata.find_targets(text, MetadataTarget.WHITESPACE)
punctuation_targets = UnicodeMetadata.find_targets(text, MetadataTarget.PUNCTUATION)

print(f"Whitespace targets: {len(whitespace_targets)} positions")
print(f"Punctuation targets: {len(punctuation_targets)} positions")

# Embed binary data
data = b"Hello, world!"
encoded_text = UnicodeMetadata.embed_bytes(text, data, MetadataTarget.WHITESPACE)

print("\nOriginal text:")
print(text)
print("\nEncoded text (looks identical but contains embedded data):")
print(encoded_text)

# Extract the embedded data
extracted_data = UnicodeMetadata.extract_bytes(encoded_text)
print(f"\nExtracted data: {extracted_data.decode('utf-8')}")

# Demonstrate variation selector conversion
byte_value = 65  # ASCII 'A'
vs_char = UnicodeMetadata.to_variation_selector(byte_value)
print(f"\nByte value {byte_value} converted to variation selector: U+{ord(vs_char):04X}")
back_to_byte = UnicodeMetadata.from_variation_selector(vs_char)
print(f"Variation selector converted back to byte: {back_to_byte}")
```

## Implementation Details

### Variation Selector Ranges

Unicode defines two ranges of variation selectors:

1. VS1-VS16: Code points U+FE00 to U+FE0F
2. VS17-VS256: Code points U+E0100 to U+E01EF

EncypherAI uses these ranges to encode binary data, allowing for up to 256 different values (0-255) to be encoded.

### Embedding Process

When embedding metadata, the `UnicodeMetadata` class:

1. Converts the metadata to a JSON string
2. Compresses the JSON string using zlib
3. Finds suitable targets in the text based on the specified target type
4. Embeds each byte of the compressed data as a variation selector after a suitable target character

### Extraction Process

When extracting metadata, the `UnicodeMetadata` class:

1. Scans the text for variation selectors
2. Converts each variation selector back to its byte value
3. Reconstructs the compressed data
4. Decompresses the data using zlib
5. Parses the JSON string to recover the original metadata

## Advanced: Embedding Timestamps

The `UnicodeMetadata` class provides special handling for timestamps:

```python
from encypher.core.unicode_metadata import UnicodeMetadata
import time

# Sample text
text = "This is a sample text for embedding metadata with timestamps."

# Create metadata with a timestamp
metadata = {
    "model_id": "gpt-4",
    "timestamp": int(time.time()),  # Unix/Epoch timestamp
    "version": "1.0.0"
}

# Embed metadata
is_valid, encoded_text = UnicodeMetadata.embed_metadata(
    text=text,
    model_id=metadata["model_id"],
    timestamp=metadata["timestamp"],
    custom_metadata={"version": metadata["version"]}
)

print(f"Embedding successful: {is_valid}")
print(f"Encoded text: {encoded_text}")

# Extract metadata
is_valid, extracted_metadata = UnicodeMetadata.extract_metadata(encoded_text)

print(f"Extraction successful: {is_valid}")
print(f"Extracted metadata: {extracted_metadata}")
```

## Related Classes

- [`MetadataEncoder`](./metadata-encoder.md): Higher-level interface for embedding and extracting metadata
- [`StreamingMetadataEncoder`](./streaming-metadata-encoder.md): For handling streaming content
