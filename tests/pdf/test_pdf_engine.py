from __future__ import annotations

from pathlib import Path

from encypher.core.crypto_utils import generate_key_pair
from encypher.core.unicode_metadata import MetadataTarget, UnicodeMetadata
from encypher.pdf import EncypherPDF


def test_pdf_round_trip(tmp_path: Path) -> None:
    private_key, public_key = generate_key_pair()

    text = "Testing PDF metadata"

    pdf_file = tmp_path / "test.pdf"
    EncypherPDF.from_text(
        text=text,
        output_path=pdf_file,
        private_key=private_key,
        signer_id="test-signer",
        timestamp="2024-01-01T00:00:00Z",
        metadata_format="basic",
        model_id="unit-test-model",
        target=MetadataTarget.WHITESPACE,
    )

    extracted_text = EncypherPDF.extract_text(pdf_file)
    assert "Testing" in extracted_text
    assert "PDF metadata" in extracted_text

    payload, valid, signer_id = UnicodeMetadata.verify_metadata(
        extracted_text,
        lambda sid: public_key if sid == "test-signer" else None,
    )
    assert valid is True
    assert signer_id == "test-signer"
    assert payload is not None
    assert payload.get("model_id") == "unit-test-model"
