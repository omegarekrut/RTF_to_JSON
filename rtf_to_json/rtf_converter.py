"""RTF to text conversion module using striprtf."""

from pathlib import Path
from striprtf.striprtf import rtf_to_text


class RTFConverter:
    """Converts RTF files to structured text."""

    def __init__(self) -> None:
        pass

    def convert_file(self, rtf_path: Path) -> str:
        """Convert RTF file to plain text."""
        if not rtf_path.exists():
            raise FileNotFoundError(f"RTF file not found: {rtf_path}")

        with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as file:
            rtf_content = file.read()

        return self.convert_rtf_content(rtf_content)

    def convert_rtf_content(self, rtf_content: str) -> str:
        """Convert the RTF content string to plain text."""
        try:
            text = rtf_to_text(rtf_content)
            return self._clean_text(text)
        except Exception as e:
            raise RuntimeError(f"Failed to convert RTF content: {e}")

    def _clean_text(self, text: str) -> str:
        """Clean and normalize the converted text."""
        lines = [line.rstrip() for line in text.split('\n')]
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True

        return '\n'.join(cleaned_lines)