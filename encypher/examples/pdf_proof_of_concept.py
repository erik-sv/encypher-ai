"""Proof-of-concept PDF generation with embedded metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from encypher.core.crypto_utils import generate_key_pair
from encypher.core.unicode_metadata import MetadataTarget, UnicodeMetadata
from encypher.pdf import EncypherPDF


if __name__ == "__main__":
    private_key, public_key = generate_key_pair()
    text = "Hello World from EncypherAI"
    pdf_path = Path("demo_output.pdf")
    EncypherPDF.from_text(
        text=text,
        output_path=pdf_path,
        private_key=private_key,
        signer_id="demo-signer",
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata_format="basic",
        model_id="demo-model",
        target=MetadataTarget.WHITESPACE,
    )

    extracted_text = EncypherPDF.extract_text(pdf_path)
    payload, valid, signer_id = UnicodeMetadata.verify_metadata(extracted_text, lambda sid: public_key if sid == "demo-signer" else None)

    print(f"Verification valid: {valid}")
    print(f"Signer ID: {signer_id}")
    print(f"Payload: {payload}")
