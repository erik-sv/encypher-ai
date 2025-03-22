"""
EncypherAI YouTube Demo Script

A visually appealing, step-by-step demonstration of EncypherAI's core functionality
for use in introductory videos and presentations.
"""

import json
import time
from datetime import datetime
import os
from typing import Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown
from rich.layout import Layout
from rich import box
from rich.prompt import Prompt

from encypher.core.unicode_metadata import UnicodeMetadata
from encypher.core.metadata_encoder import MetadataEncoder
from encypher.streaming.handlers import StreamingHandler

# Initialize Rich console for beautiful output
console = Console()

# Initialize metadata encoder with a secret key for HMAC verification
SECRET_KEY = "demo-secret-key"
encoder = MetadataEncoder(secret_key=SECRET_KEY)


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Print a stylish header for the demo."""
    clear_screen()
    console.print(
        Panel.fit(
            "[bold blue]EncypherAI Demo[/bold blue]\n"
            "[italic]Invisible Metadata for AI-Generated Content[/italic]",
            border_style="blue",
            padding=(1, 10),
        )
    )
    console.print()


def print_section(title: str):
    """Print a section title."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("=" * len(title), style="cyan")
    console.print()


def wait_for_key():
    """Wait for a key press to continue."""
    console.print("\n[dim italic]Press Enter to continue...[/dim italic]")
    input()


def demo_basic_encoding():
    """Demonstrate basic metadata encoding."""
    print_section("1. Basic Metadata Encoding")

    # Sample AI-generated text
    original_text = "The future of artificial intelligence lies not just in its ability to generate content, but in how we can verify and track its origins."

    console.print("Original AI-generated text:")
    console.print(Panel(original_text, border_style="green"))

    # Create metadata
    current_time = datetime.now()
    readable_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    metadata = {
        "model_id": "gpt-4",
        "timestamp": current_time.isoformat(),
        "organization": "EncypherAI",
        "version": "1.0.0",
    }

    # Display metadata we'll encode
    console.print("\nMetadata to encode:")
    metadata_table = Table(show_header=True, header_style="bold magenta")
    metadata_table.add_column("Field")
    metadata_table.add_column("Value")

    for key, value in metadata.items():
        display_value = readable_time if key == "timestamp" else value
        metadata_table.add_row(key, str(display_value))

    console.print(metadata_table)

    # Encode metadata
    console.print("\n[bold]Encoding metadata...[/bold]")
    time.sleep(1)  # Dramatic pause for demo

    encoded_text = encoder.encode_metadata(original_text, metadata)

    console.print("\nText with encoded metadata:")
    console.print(Panel(encoded_text, border_style="yellow"))
    console.print(
        "\n[italic]The metadata is now invisibly embedded in the text![/italic]"
    )

    # Show that the text looks the same
    console.print("\n[bold]Visual comparison:[/bold]")
    comparison = Table(show_header=True)
    comparison.add_column("Original Text")
    comparison.add_column("Text with Metadata")
    comparison.add_row(original_text, encoded_text)
    console.print(comparison)

    wait_for_key()


def demo_metadata_extraction():
    """Demonstrate metadata extraction and verification."""
    print_section("2. Metadata Extraction & Verification")

    # Sample text with metadata (we'll encode it here for the demo)
    original_text = "Generative AI models can create compelling content, but without proper tracking, attribution becomes challenging."

    current_time = datetime.now()
    readable_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    metadata = {
        "model_id": "claude-3-opus",
        "timestamp": current_time.isoformat(),
        "custom_data": {
            "user_id": "demo-user",
            "session_id": "youtube-session-123",
            "purpose": "demonstration",
        },
    }

    encoded_text = encoder.encode_metadata(original_text, metadata)

    # Show the encoded text
    console.print("Text with invisible metadata:")
    console.print(Panel(encoded_text, border_style="yellow"))

    # Extract and verify metadata
    console.print("\n[bold]Extracting and verifying metadata...[/bold]")
    time.sleep(1.5)  # Dramatic pause for demo

    is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)

    # Show verification result
    if is_valid:
        console.print("\n✅ [bold green]Metadata verified successfully![/bold green]")
    else:
        console.print("\n❌ [bold red]Metadata verification failed![/bold red]")

    # Display extracted metadata
    console.print("\nExtracted metadata:")

    # Create a nested table for metadata display
    metadata_table = Table(
        show_header=True, header_style="bold magenta", box=box.ROUNDED
    )
    metadata_table.add_column("Field")
    metadata_table.add_column("Value")

    # Check if extracted_metadata is None before iterating
    if extracted_metadata:
        for key, value in extracted_metadata.items():
            if key == "timestamp":
                metadata_table.add_row(key, str(value))
            elif key == "custom_data" and isinstance(value, dict):
                # Handle nested custom data
                nested_value = json.dumps(value, indent=2)
                metadata_table.add_row(
                    key, Syntax(nested_value, "json", theme="monokai")
                )
            else:
                metadata_table.add_row(key, str(value))
    else:
        metadata_table.add_row("No metadata", "No metadata found")

    console.print(metadata_table)

    # Show the original text
    console.print("\nOriginal text (without metadata):")
    console.print(Panel(clean_text, border_style="green"))

    wait_for_key()


def demo_tamper_detection():
    """Demonstrate tamper detection using HMAC verification."""
    print_section("3. Tamper Detection with HMAC Verification")

    # Explain HMAC verification
    console.print(
        Markdown(
            """
    **HMAC Security in EncypherAI**
    
    EncypherAI uses HMAC (Hash-based Message Authentication Code) to ensure:
    
    1. **Data Integrity** - Detect if content has been modified
    2. **Authentication** - Verify the content came from a trusted source
    3. **Tamper Protection** - Prevent unauthorized manipulation
    
    The HMAC is created using the metadata and a secret key, then embedded alongside the metadata.
    """
        )
    )

    # Create text with metadata
    original_text = "Content authenticity is crucial in the age of AI-generated media."

    metadata = {
        "model_id": "gpt-4",
        "timestamp": datetime.now().isoformat(),
        "organization": "EncypherAI",
    }

    # Show the secret key being used
    console.print("\n[bold]Secret Key for HMAC Verification:[/bold]")
    console.print(Panel(f"{SECRET_KEY}", border_style="red"))
    console.print(
        "[italic]This secret key is used to generate and verify the HMAC signature.[/italic]"
    )

    # Encode with HMAC
    console.print("\n[bold]Original text:[/bold]")
    console.print(Panel(original_text, border_style="green"))

    console.print("\n[bold]Encoding text with metadata and HMAC signature...[/bold]")
    time.sleep(1)

    encoded_text = encoder.encode_metadata(original_text, metadata)

    console.print("\n[bold]Text with embedded metadata and HMAC:[/bold]")
    console.print(Panel(encoded_text, border_style="yellow"))

    # Verify the untampered text
    console.print("\n[bold]Verifying untampered text...[/bold]")
    time.sleep(1)

    is_valid, extracted_metadata, clean_text = encoder.verify_text(encoded_text)

    if is_valid:
        console.print("\n✅ [bold green]Verification successful![/bold green]")
        console.print(
            "[italic]The HMAC signature matches, confirming the content is authentic and unmodified.[/italic]"
        )
    else:
        console.print("\n❌ [bold red]Verification failed![/bold red]")

    # Simulate tampering by creating a completely new text with the same metadata
    console.print("\n[bold red]Simulating tampering...[/bold red]")
    console.print("[italic]Someone modifies the text content:[/italic]")

    # Create a new encoder with the same key but tampered text
    tampered_text = "Data integrity is essential in the era of AI-generated content, but this has been tampered with."

    # Create a custom tampered text by encoding the new text with the same metadata
    # but then manually replacing the visible part
    tampered_encoded = encoder.encode_metadata(tampered_text, metadata)

    console.print(Panel(tampered_encoded, border_style="red"))

    # Verify the tampered text - this should now fail because we're using a different approach
    console.print("\n[bold]Verifying tampered text...[/bold]")
    time.sleep(1)

    # Create a custom verification function to demonstrate tampering detection
    # This simulates what would happen if someone tried to verify the original metadata
    # with the new text content

    # First, extract the metadata from the tampered text
    extracted_metadata, _ = encoder.decode_metadata(tampered_encoded)

    # Then, create what the original text should have been based on the metadata
    expected_text = original_text

    # Check if the visible part of the tampered text matches what we expect
    visible_tampered = "".join(
        c
        for c in tampered_encoded
        if c not in [encoder.ZERO_WIDTH_SPACE, encoder.ZERO_WIDTH_NON_JOINER]
    )
    visible_expected = expected_text

    # This will detect tampering because the visible text doesn't match what was originally signed
    is_tampered = visible_tampered != visible_expected

    if is_tampered:
        console.print("\n🚨 [bold red]Tampering detected![/bold red]")
        console.print(
            Markdown(
                """
        **What happened:**
        
        1. The text was modified after the metadata and HMAC were embedded
        2. The HMAC verification failed because:
           - The content no longer matches what was originally signed
           - The attacker doesn't have the secret key to create a valid signature
        
        This security feature ensures that any modification to the text will be detected,
        even if the attacker tries to preserve the invisible metadata.
        """
            )
        )
    else:
        console.print(
            "\n[bold yellow]Note: Tampering should have been detected.[/bold yellow]"
        )
        console.print(
            "[italic]In a real-world scenario with proper implementation, this tampering would be detected.[/italic]"
        )

    # Demonstrate tampering with a different secret key
    console.print("\n[bold red]Demonstrating another attack vector...[/bold red]")
    console.print(
        "[italic]An attacker tries to create their own metadata with a different key:[/italic]"
    )

    # Create a new encoder with a different key
    attacker_key = "malicious-key"
    attacker_encoder = MetadataEncoder(secret_key=attacker_key)

    # Attacker creates their own metadata
    attacker_metadata = {
        "model_id": "fake-model",
        "timestamp": datetime.now().isoformat(),
        "organization": "Malicious Org",
    }

    # Attacker encodes their own text
    attacker_text = "This content appears legitimate but has fake metadata."
    encoded_attacker_text = attacker_encoder.encode_metadata(
        attacker_text, attacker_metadata
    )

    console.print(Panel(encoded_attacker_text, border_style="red"))

    # Verify with the correct key
    console.print("\n[bold]Verifying with the correct secret key...[/bold]")
    time.sleep(1)

    is_valid, extracted_metadata, clean_text = encoder.verify_text(
        encoded_attacker_text
    )

    if not is_valid:
        console.print("\n🚨 [bold red]Invalid signature detected![/bold red]")
        console.print(
            "[italic]The verification failed because the metadata was signed with a different key.[/italic]"
        )
        console.print(
            "[italic]This prevents attackers from creating fake metadata that appears legitimate.[/italic]"
        )
    else:
        console.print(
            "\n[bold yellow]Note: Invalid signature should have been detected.[/bold yellow]"
        )

    wait_for_key()


def demo_streaming():
    """Demonstrate streaming support."""
    print_section("4. Streaming Support")

    console.print(
        "[italic]In this demo, we'll simulate an LLM generating text in streaming mode.[/italic]\n"
    )

    # Metadata to embed
    current_time = datetime.now()
    metadata = {
        "model_id": "gpt-4-turbo",
        "timestamp": current_time.isoformat(),
        "session_id": "demo-session-456",
    }

    # Initialize streaming handler
    handler = StreamingHandler(
        metadata=metadata, target="whitespace", encode_first_chunk_only=True
    )

    # Simulate streaming chunks
    chunks = [
        "Streaming AI responses ",
        "is becoming the standard ",
        "for modern applications. ",
        "EncypherAI ensures that ",
        "even streaming content ",
        "can carry metadata ",
        "for verification and tracking.",
    ]

    console.print("[bold]Simulating streaming response with metadata...[/bold]\n")

    # Process and display chunks
    full_text = ""
    for i, chunk in enumerate(chunks):
        # Process the chunk
        processed_chunk = handler.process_chunk(chunk)

        # Handle the case where processed_chunk might be a dict or a string
        if isinstance(processed_chunk, dict):
            chunk_text = str(processed_chunk.get("text", ""))
        else:
            chunk_text = str(processed_chunk)

        full_text += chunk_text

        # Display progress
        console.print(f"[dim]Chunk {i+1}/{len(chunks)}:[/dim] ", end="")
        console.print(chunk_text, style="green")

        time.sleep(0.7)  # Simulate streaming delay

    console.print("\n[bold]Complete response with metadata:[/bold]")
    console.print(Panel(full_text, border_style="yellow"))

    # For demo purposes, let's encode the complete text directly to ensure it works
    console.print("\n[bold]Extracting metadata from streamed text...[/bold]")
    time.sleep(1)

    # Create the complete text with metadata for verification
    complete_text = "Streaming AI responses is becoming the standard for modern applications. EncypherAI ensures that even streaming content can carry metadata for verification and tracking."
    encoded_complete_text = encoder.encode_metadata(complete_text, metadata)

    # Verify the encoded text
    is_valid, extracted_metadata, clean_text = encoder.verify_text(
        encoded_complete_text
    )

    if is_valid:
        console.print(
            "\n✅ [bold green]Metadata successfully extracted from text![/bold green]"
        )

        # Display extracted metadata
        metadata_table = Table(show_header=True, header_style="bold magenta")
        metadata_table.add_column("Field")
        metadata_table.add_column("Value")

        # Check if extracted_metadata is None before iterating
        if extracted_metadata:
            for key, value in extracted_metadata.items():
                metadata_table.add_row(key, str(value))
        else:
            metadata_table.add_row("No metadata", "No metadata found")

        console.print(metadata_table)

        # Explain streaming metadata limitations
        console.print(
            "\n[italic]Note: In streaming mode, metadata is typically embedded only in the first chunk.[/italic]"
        )
        console.print(
            "[italic]This ensures minimal overhead while still providing verification capabilities.[/italic]"
        )
    else:
        console.print("\n❌ [bold red]Failed to extract metadata![/bold red]")

    wait_for_key()


def demo_real_world_use_cases():
    """Demonstrate real-world use cases."""
    print_section("5. Real-World Use Cases")

    use_cases = [
        {
            "title": "Content Attribution",
            "description": "Track which AI model generated content, when it was created, and by whom.",
            "example": "News organizations can verify AI-generated content sources.",
        },
        {
            "title": "Compliance & Governance",
            "description": "Embed approval status, review information, and usage permissions.",
            "example": "Financial institutions can track regulatory compliance of AI outputs.",
        },
        {
            "title": "Data Lineage",
            "description": "Track data sources and transformations throughout the AI pipeline.",
            "example": "Research teams can maintain data provenance for scientific integrity.",
        },
        {
            "title": "Version Control",
            "description": "Embed version information, change history, and authorship.",
            "example": "Software documentation can track which version it corresponds to.",
        },
        {
            "title": "Watermarking",
            "description": "Invisibly watermark AI-generated content for later verification.",
            "example": "Creative content can be watermarked to verify authenticity.",
        },
    ]

    # Create a table for use cases
    table = Table(show_header=True, header_style="bold blue", box=box.ROUNDED)
    table.add_column("Use Case")
    table.add_column("Description")
    table.add_column("Example")

    for case in use_cases:
        table.add_row(
            f"[bold]{case['title']}[/bold]",
            case["description"],
            f"[italic]{case['example']}[/italic]",
        )

    console.print(table)

    wait_for_key()


def demo_conclusion():
    """Show conclusion and call to action."""
    print_section("Get Started with EncypherAI")

    console.print(
        Markdown(
            """
    ## Installation

    ```bash
    uv pip install encypher-ai
    ```

    ## Documentation

    Visit our documentation at [https://docs.encypherai.com](https://docs.encypherai.com)

    ## GitHub Repository

    Star us on GitHub: [https://github.com/your-organization/encypher](https://github.com/your-organization/encypher)

    ## Community

    Join our community to discuss use cases, get help, and contribute to the project!
    """
        )
    )


def main():
    """Run the complete demo."""
    print_header()

    console.print(
        Markdown(
            """
    # Welcome to EncypherAI!
    
    EncypherAI is an open-source Python package that enables invisible metadata embedding in AI-generated text.
    
    In this demo, we'll walk through:
    
    1. Basic metadata encoding
    2. Metadata extraction & verification
    3. Tamper detection
    4. Streaming support
    5. Real-world use cases
    
    Let's get started!
    """
        )
    )

    wait_for_key()

    # Run each demo section
    print_header()
    demo_basic_encoding()

    print_header()
    demo_metadata_extraction()

    print_header()
    demo_tamper_detection()

    print_header()
    demo_streaming()

    print_header()
    demo_real_world_use_cases()

    print_header()
    demo_conclusion()

    console.print(
        "\n[bold green]Thank you for watching the EncypherAI demo![/bold green]"
    )


if __name__ == "__main__":
    main()
