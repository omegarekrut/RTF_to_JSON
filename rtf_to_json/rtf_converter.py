"""RTF to text conversion module with structure preservation."""

import re
from pathlib import Path
from striprtf.striprtf import rtf_to_text


class RTFConverter:
    """Converts RTF files to structured text while preserving hierarchical markers."""

    def convert_file(self, rtf_path: Path) -> str:
        """Convert RTF file to structured text."""
        if not rtf_path.exists():
            raise FileNotFoundError(f"RTF file not found: {rtf_path}")

        rtf_content = rtf_path.read_text(encoding='utf-8', errors='ignore')
        return self.convert_rtf_content(rtf_content)

    def convert_rtf_content(self, rtf_content: str) -> str:
        """Convert RTF content to structured text with preserved hierarchy."""
        if not rtf_content.strip():
            return ""

        try:
            structured_text = self._preserve_structure(rtf_content)
            plain_text = rtf_to_text(structured_text)
            return self._clean_text(plain_text)
        except Exception as e:
            raise RuntimeError(f"Failed to convert RTF content: {e}") from e

    def _preserve_structure(self, rtf_content: str) -> str:
        """Preserve structural markers before RTF conversion."""
        if not rtf_content.strip():
            return rtf_content

        # Define structure preservation patterns
        patterns = [
            # Headers by font size
            (r'\\fs39\\f2\\b\\ul\s*\{\\ltrch ([^}]+)\}', r'<<H1>>\1<</H1>>'),
            (r'\\fs30\\f2\\b\\ul\s*\{\\ltrch ([^}]+)\}', r'<<H2>>\1<</H2>>'),
            (r'\\fs21\\f2\\b\s*\{\\ltrch ([^}]+)\}', r'<<H3>>\1<</H3>>'),
            # Bold field labels
            (r'\\fs18\\f2\s*\{\\b\\ltrch ([^:}]+):\s*\}', r'<<LABEL>>\1:<</LABEL>>'),
            # Bold standalone entity names
            (r'\\f2\\b\s*\{\\ltrch ([^}]+)\}', r'<<ENTITY>>\1<</ENTITY>>'),
            # Bullet points
            (r'\{\\pntext\s*\\\'B7\\tab\}.*?\{\\ltrch ([^}]+)\}', r'<<BULLET>>\1<</BULLET>>'),
            # Field values
            (r'\{\\ltrch ([^}]+)\}', r'<<VALUE>>\1<</VALUE>>'),
        ]

        text = rtf_content
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)

        return text

    def _clean_text(self, text: str) -> str:
        """Clean and normalize the converted text while preserving structure markers."""
        if not text.strip():
            return text

        # Remove specific RTF artifacts while preserving our tags
        # Remove extra < that appears before closing tags
        text = re.sub(r'<(</(H[123]|LABEL|ENTITY|BULLET|VALUE)>>)', r'\1', text)

        lines = [line.rstrip() for line in text.split('\n')]
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            # Handle non-empty lines
            if line.strip():
                cleaned_lines.append(line)
                prev_empty = False
                continue

            # Handle empty lines (avoid consecutive empty lines)
            if not prev_empty:
                cleaned_lines.append('')
                prev_empty = True

        return '\n'.join(cleaned_lines)
