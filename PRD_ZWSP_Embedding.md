# PRD: Use Zero-Width Characters for Metadata Embedding

**Status:** Completed (2025-05-03)

**Branch:** `feature/use-zwsp-embedding`

## 1. Goal

Improve the visual compatibility of EncypherAI-encoded text across different applications and fonts (especially word processors) by replacing the current Variation Selector characters (U+FE0E/U+FE0F) with more widely supported zero-width characters like Zero-Width Space (ZWSP - U+200B) and Zero-Width Non-Joiner (ZWNJ - U+200C). This aims to significantly reduce the appearance of "missing glyph" artifacts (e.g., �).

## 2. Scope

- Modify the core metadata embedding logic within `encypher/core/unicode_metadata.py`.
- Modify the core metadata extraction logic within `encypher/core/unicode_metadata.py`.
- Update existing unit tests in `tests/test_unicode_metadata.py` to reflect the changes.
- Add new unit tests specifically for ZWSP/ZWNJ embedding/extraction.
- Perform manual testing across different applications/fonts.

## 3. Proposed Technical Approach

- **Character Selection:** Replace the current Unicode characters used to represent '0' and '1' metadata bits. Proposed pair:
    - `'1'` -> Zero-Width Space (ZWSP - `\u200B`)
    - `'0'` -> Zero-Width Non-Joiner (ZWNJ - `\u200C`)
- **Target File:** Primary changes expected in `encypher/core/unicode_metadata.py`, impacting methods related to binary-to-Unicode conversion and vice-versa (e.g., `_embed_binary_data`, `_extract_binary_data`).

## 4. Implementation Tasks

- [x] **Analysis:** Locate the exact code sections (constants, functions) in `unicode_metadata.py` defining and using the current Variation Selector embedding characters.
- [x] **Modification:** Replace the existing character definitions/usage with `\u200B` (ZWSP) and `\u200C` (ZWNJ).
- [x] **Modification:** Update the corresponding extraction logic to correctly identify and interpret ZWSP and ZWNJ as '1' and '0' bits.
- [x] **Review:** Ensure calculations related to embedding capacity, character locations, and string manipulation remain correct with the new characters.

## 5. Testing Tasks

- [x] **Unit Tests - Update:** Run `pytest tests/`. Update failing tests in `test_unicode_metadata.py` to expect ZWSP/ZWNJ characters and verify data correctly.
- [x] **Unit Tests - Add:** Create new test cases specifically verifying:
    - Correct insertion of ZWSP ('1') and ZWNJ ('0').
    - Successful extraction and data reconstruction.
    - Behavior at edge cases (start/end of string, empty metadata).
- [x] **Manual Testing - Verification:**
    - Run the `basic_encoding_example.py` script (or similar).
    - Copy/paste output into Notepad, VS Code, Word/LibreOffice, Browser Textarea.
    - Apply various fonts in word processor (Liberation Serif, Times New Roman, Arial, Segoe UI, Noto Sans).
    - **Goal:** Confirm significant reduction/elimination of `�` symbols.
- [x] **Functional Testing:** Ensure `verify_metadata` (signature check) still functions correctly.

## 6. Potential Issues & Considerations

- **Line Breaking:** ZWSP (`\u200B`) indicates a line break opportunity. Monitor for unintended visual side effects.
- **Normalization:** Risk (though lower than with VS) of ZWSP/ZWNJ being altered by aggressive text normalization.
- **Backwards Compatibility:** This is a **breaking change**. Text encoded with this new version will not be compatible with older versions, and vice-versa. Requires clear communication and version bump (minor or major).

## 7. Open Questions / Future Work

- Consider if offering *both* methods (VS and ZWSP) via a configuration flag is feasible or desirable (adds complexity).
- How to handle embedding in very short texts where capacity is insufficient? (Error? Skip? Partial embed?) **(Decision: Fails if capacity insufficient)**
- Explore alternative invisible characters if ZWSP/ZWNJ cause issues in specific environments. **(Low Priority)**
- Benchmark performance impact of embedding/extraction. **(Future Task)**
- **(New):** Consider enhancing `StreamingHandler` to accumulate chunks to ensure sufficient capacity before attempting embedding, even when `encode_first_chunk_only=True`. **(Future Task)**

## 8. Blockers and Resolutions

- **Blocker 1:** `ValueError: Key is not an Ed25519PrivateKey instance` during signing in tests.
  - **Resolution:** Corrected argument order in `sign_payload` call within `UnicodeMetadata.embed_metadata`. **(Resolved)**
- **Blocker 2:** `NameError: name 'os' is not defined` in `test_unicode_metadata.py` fixtures.
  - **Resolution:** Added `import os`. **(Resolved)**
- **Blocker 3:** Initial key loading issues with PEM format from environment variables.
  - **Resolution:** Ensured correct newline handling (`.replace("\\n", "\n")`) when loading PEM strings. **(Resolved)**
- **Blocker 4:** Streaming/Integration tests failing due to insufficient embedding capacity in small test chunks.
  - **Resolution:** Increased the length of test chunks (specifically the first chunk when `encode_first_chunk_only=True`) to provide enough whitespace targets (~400+) for the ZWSP/ZWNJ payload. Documented this requirement. **(Resolved)**

## 9. Status

- **Overall:** **Completed** (Core ZWSP embedding feature implemented and tested).
- **Unit Tests:** **Passing**
- **Integration Tests:** **Passing**
- **Documentation (PRD):** **Updated**
- **Code Quality:** **Improved** (Refactoring, comments added).
