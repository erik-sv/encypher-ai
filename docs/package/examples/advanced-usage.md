# Advanced Usage Examples

This guide provides advanced examples for using the EncypherAI package in various scenarios.

## Custom Metadata Handling

### Creating a Custom Metadata Encoder

You can extend the base `MetadataEncoder` class to create custom encoders with specialized functionality:

```python
from encypher.core.metadata_encoder import MetadataEncoder
import hashlib
import time
import json

class EnhancedMetadataEncoder(MetadataEncoder):
    """Custom metadata encoder with enhanced features."""
    
    def __init__(self, secret_key=None, include_hash=True):
        super().__init__(secret_key=secret_key)
        self.include_hash = include_hash
    
    def encode_metadata(self, text, metadata, target="whitespace"):
        """Encode metadata with additional content hash."""
        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = int(time.time())
        
        # Add content hash if enabled
        if self.include_hash:
            content_hash = hashlib.sha256(text.encode()).hexdigest()
            metadata["content_hash"] = content_hash
        
        # Use parent class to perform the encoding
        return super().encode_metadata(text, metadata, target)
    
    def verify_text(self, text, verify_hash=True):
        """Enhanced verification that also checks content hash."""
        # Extract metadata
        metadata = self.decode_metadata(text)
        if not metadata:
            return False
        
        # Perform standard HMAC verification
        standard_verification = super().verify_text(text)
        
        # Optionally verify content hash
        if verify_hash and self.include_hash and "content_hash" in metadata:
            # Extract text without metadata
            clean_text = self.strip_metadata(text)
            
            # Calculate hash of clean text
            current_hash = hashlib.sha256(clean_text.encode()).hexdigest()
            
            # Compare with stored hash
            hash_verification = current_hash == metadata["content_hash"]
            
            # Both verifications must pass
            return standard_verification and hash_verification
        
        return standard_verification

# Example usage
encoder = EnhancedMetadataEncoder(secret_key="my-secret-key")
text = "This is a sample text for advanced encoding."
metadata = {
    "model": "gpt-4",
    "organization": "EncypherAI",
    "version": "1.1.0"
}

# Encode with enhanced metadata
encoded_text = encoder.encode_metadata(text, metadata)
print(f"Encoded text: {encoded_text}")

# Verify with enhanced verification
verification_result = encoder.verify_text(encoded_text)
print(f"Verification result: {verification_result}")
```

## Batch Processing

For processing large volumes of text, you can implement batch processing:

```python
from encypher.core.metadata_encoder import MetadataEncoder
import time
import concurrent.futures
import json

def process_batch(texts, metadata_template, encoder=None, max_workers=4):
    """Process a batch of texts with metadata embedding."""
    if encoder is None:
        encoder = MetadataEncoder()
    
    results = []
    
    # Define processing function
    def process_item(item):
        text = item["text"]
        # Create a copy of the template and add item-specific fields
        metadata = metadata_template.copy()
        metadata["item_id"] = item.get("id", f"item_{len(results)}")
        metadata["timestamp"] = int(time.time())
        
        try:
            # Encode metadata
            encoded_text = encoder.encode_metadata(text, metadata)
            return {
                "success": True,
                "original_text": text,
                "encoded_text": encoded_text,
                "metadata": metadata
            }
        except Exception as e:
            return {
                "success": False,
                "original_text": text,
                "error": str(e)
            }
    
    # Process items in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_item, item) for item in texts]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    return results

# Example usage
texts = [
    {"id": "item1", "text": "This is the first text item."},
    {"id": "item2", "text": "This is the second text item."},
    {"id": "item3", "text": "This is the third text item."}
]

metadata_template = {
    "model": "gpt-4",
    "organization": "EncypherAI",
    "version": "1.1.0"
}

# Process batch
results = process_batch(texts, metadata_template)

# Print results
for result in results:
    if result["success"]:
        print(f"Successfully processed item: {result['metadata']['item_id']}")
    else:
        print(f"Failed to process item: {result.get('error', 'Unknown error')}")
```

## Advanced Streaming Techniques

### Custom Streaming Handler

You can create a custom streaming handler with specialized behavior:

```python
from encypher.streaming.handlers import StreamingHandler
from encypher.core.unicode_metadata import MetadataTarget
import time
import json

class EnhancedStreamingHandler(StreamingHandler):
    """Enhanced streaming handler with additional features."""
    
    def __init__(self, metadata=None, target=MetadataTarget.WHITESPACE, 
                 secret_key=None, chunk_threshold=100, log_chunks=False):
        super().__init__(metadata=metadata, target=target, secret_key=secret_key)
        self.chunk_threshold = chunk_threshold
        self.log_chunks = log_chunks
        self.chunks_processed = 0
        self.total_length = 0
    
    def process_chunk(self, chunk):
        """Process a chunk with enhanced logging and analytics."""
        self.chunks_processed += 1
        self.total_length += len(chunk)
        
        if self.log_chunks:
            print(f"Processing chunk {self.chunks_processed}: {len(chunk)} chars")
        
        # Add dynamic metadata if needed
        if self.metadata and "chunks_processed" not in self.metadata:
            self.metadata["chunks_processed"] = 0
        
        if self.metadata:
            self.metadata["chunks_processed"] = self.chunks_processed
        
        # Use standard processing
        processed_chunk = super().process_chunk(chunk)
        
        # Apply special handling for large chunks
        if len(chunk) > self.chunk_threshold and self.chunks_processed > 1:
            # For large chunks after the first, we might want special handling
            # This is just an example - you could implement custom logic here
            pass
            
        return processed_chunk
    
    def finalize(self):
        """Finalize the stream with enhanced metadata."""
        if self.metadata:
            self.metadata["total_chunks"] = self.chunks_processed
            self.metadata["total_length"] = self.total_length
            self.metadata["finalized_at"] = int(time.time())
        
        return super().finalize()

# Example usage
metadata = {
    "model": "streaming-demo",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "1.1.0"
}

handler = EnhancedStreamingHandler(
    metadata=metadata,
    log_chunks=True,
    chunk_threshold=50
)

# Simulate streaming
chunks = [
    "The quick ",
    "brown fox jumps ",
    "over the lazy dog. ",
    "This is an example of streaming text with embedded metadata."
]

full_text = ""
for chunk in chunks:
    processed = handler.process_chunk(chunk)
    full_text += processed
    print(f"Accumulated text: {full_text}")

# Finalize
final_chunk = handler.finalize()
if final_chunk:
    full_text += final_chunk

print(f"Final text: {full_text}")

# Extract metadata
from encypher.core.unicode_metadata import UnicodeMetadata
extracted = UnicodeMetadata.extract_metadata(full_text)
print(f"Extracted metadata: {json.dumps(extracted, indent=2)}")
```

## Custom Verification Logic

You can implement custom verification logic for specific use cases:

```python
from encypher.core.metadata_encoder import MetadataEncoder
import time

def verify_content_with_custom_logic(text, expected_organization=None, max_age_hours=24):
    """
    Verify content with custom logic beyond the standard verification.
    
    Args:
        text: Text with embedded metadata to verify
        expected_organization: If set, verify the organization matches
        max_age_hours: Maximum age of content in hours
        
    Returns:
        dict: Verification results with detailed information
    """
    encoder = MetadataEncoder()
    
    # Standard verification
    hmac_verified = encoder.verify_text(text)
    
    # Extract metadata for custom checks
    metadata = encoder.decode_metadata(text)
    
    # Initialize results
    results = {
        "hmac_verified": hmac_verified,
        "metadata_present": bool(metadata),
        "custom_checks": {}
    }
    
    # If metadata is present, perform custom checks
    if metadata:
        # Check organization if specified
        if expected_organization:
            org_match = metadata.get("organization") == expected_organization
            results["custom_checks"]["organization_match"] = org_match
        
        # Check age if timestamp is present
        if "timestamp" in metadata:
            try:
                # Get timestamp as int
                timestamp = metadata["timestamp"]
                if isinstance(timestamp, str) and timestamp.isdigit():
                    timestamp = int(timestamp)
                
                # Calculate age in hours
                current_time = int(time.time())
                age_seconds = current_time - timestamp
                age_hours = age_seconds / 3600
                
                results["custom_checks"]["age_hours"] = age_hours
                results["custom_checks"]["age_within_limit"] = age_hours <= max_age_hours
            except Exception as e:
                results["custom_checks"]["timestamp_error"] = str(e)
    
    # Overall verification result
    results["verified"] = (
        hmac_verified and 
        bool(metadata) and
        all(results["custom_checks"].values())
    )
    
    return results

# Example usage
encoder = MetadataEncoder()
text = "This is a sample text for verification."
metadata = {
    "model": "gpt-4",
    "organization": "EncypherAI",
    "timestamp": int(time.time()),
    "version": "1.1.0"
}

# Encode metadata
encoded_text = encoder.encode_metadata(text, metadata)

# Verify with custom logic
verification_results = verify_content_with_custom_logic(
    encoded_text,
    expected_organization="EncypherAI",
    max_age_hours=48
)

print(f"Verification results: {json.dumps(verification_results, indent=2)}")
```

These advanced examples demonstrate how to extend and customize EncypherAI's functionality for various use cases.
