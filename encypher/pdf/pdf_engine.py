"""PDF generation utilities for EncypherAI.

This module provides minimal functions to generate PDFs from text
and extract text from PDFs. It is a proof-of-concept implementation
built on top of the ReportLab and pdfminer.six libraries.
"""

from __future__ import annotations

from pathlib import Path

from pdfminer.high_level import extract_text as pdf_extract_text
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter


class EncypherPDF:
    """Utility class for PDF generation and extraction."""

    @staticmethod
    def generate_pdf(text: str, output_path: str | Path) -> None:
        """Generate a simple PDF containing the provided text.

        Args:
            text: The text to include in the PDF.
            output_path: Destination file path for the PDF.
        """
        path = Path(output_path)
        # Register a Unicode-friendly font (Noto Sans) if available
        try:
            pdfmetrics.registerFont(
                TTFont("Symbola", "/usr/share/fonts/truetype/ancient-scripts/Symbola.ttf")
            )
            font_name = "Symbola"
        except Exception:
            font_name = "Helvetica"

        c = canvas.Canvas(str(path), pagesize=LETTER)
        _, height = LETTER
        text_object = c.beginText(72, height - 72)
        text_object.setFont(font_name, 12)
        for line in text.splitlines():
            text_object.textLine(line)
        c.drawText(text_object)
        c.showPage()
        c.save()

        # Store the raw text as PDF metadata for reliable extraction
        try:
            reader = PdfReader(str(path))
            writer = PdfWriter()
            writer.append_pages_from_reader(reader)
            writer.add_metadata({"/EncypherText": text})
            with open(path, "wb") as fh:
                writer.write(fh)
        except Exception:
            pass

    @staticmethod
    def from_text(
        text: str,
        output_path: str | Path,
        private_key,
        signer_id: str,
        timestamp,
        *,
        metadata_format: str = "basic",
        target=None,
        **metadata_kwargs,
    ) -> None:
        """Embed metadata in text and generate a PDF.

        Args:
            text: Original text to embed metadata into.
            output_path: Destination file path for the generated PDF.
            private_key: Private key used for signing the metadata.
            signer_id: Identifier associated with the signing key.
            timestamp: Timestamp for the metadata payload.
            metadata_format: Metadata format for ``UnicodeMetadata``.
            target: Where to embed metadata within the text.
            **metadata_kwargs: Additional metadata fields passed to
                :func:`UnicodeMetadata.embed_metadata`.
        """
        from encypher.core.unicode_metadata import UnicodeMetadata

        embedded_text = UnicodeMetadata.embed_metadata(
            text,
            private_key,
            signer_id,
            timestamp,
            metadata_format=metadata_format,
            target=target,
            **metadata_kwargs,
        )

        EncypherPDF.generate_pdf(embedded_text, output_path)

    @staticmethod
    def extract_text(pdf_path: str | Path) -> str:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            The text extracted from the PDF.
        """
        path = Path(pdf_path)
        try:
            reader = PdfReader(str(path))
            info = reader.metadata
            if info and info.get("/EncypherText"):
                return info["/EncypherText"]
        except Exception:
            pass
        return pdf_extract_text(str(path))
