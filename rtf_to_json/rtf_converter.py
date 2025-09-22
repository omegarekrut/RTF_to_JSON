"""RTF to text conversion module with structure preservation."""

import re
from pathlib import Path
from striprtf.striprtf import rtf_to_text


class RTFConverter:
    """Converts RTF files to structured text while preserving hierarchical markers."""

    def __init__(self):
        """Initialize converter with predefined patterns."""
        self._setup_patterns()

    def _setup_patterns(self) -> None:
        """Set up RTF structure preservation patterns - order matters!"""
        self.structure_patterns = [
            # Headers by font size (most specific first)
            (r'\\fs39\\f2\\b\\ul\s*\{\\ltrch ([^}]+)\}', r'<<H1>>\1<</H1>>'),
            (r'\\fs30\\f2\\b\\ul\s*\{\\ltrch ([^}]+)\}', r'<<H2>>\1<</H2>>'),
            (r'\\fs24\\f2\\b\s*\{\\ltrch ([^}]+)\}', r'<<H3>>\1<</H3>>'),
            (r'\\fs21\\f2\\b\s*\{\\ltrch ([^}]+)\}', r'<<H3>>\1<</H3>>'),

            # Table-style bold labels with inline values (stat tables)
            (r'\\fs18\\intbl\s*\{\\b\\ltrch ([^:}]+):\s*\}\s*\{\\ltrch ([^}]+)\}',
             r'<<LABEL>>\1:<</LABEL>><<VALUE>>\2<</VALUE>>'),

            # Table-style bold labels without inline values (stat tables)
            (r'\\fs18\\intbl\s*\{\\b\\ltrch ([^:}]+):\s*\}', r'<<LABEL>>\1:<</LABEL>>'),

            # Bold field labels with inline values
            (r'\\fs18\\f2\s*\{\\b\\ltrch ([^:}]+):\s*\}\s*\{\\ltrch ([^}]+)\}',
             r'<<LABEL>>\1:<</LABEL>><<VALUE>>\2<</VALUE>>'),

            # Bold field labels without inline values
            (r'\\fs18\\f2\s*\{\\b\\ltrch ([^:}]+):\s*\}', r'<<LABEL>>\1:<</LABEL>>'),

            # Bold standalone entity names (but not labels)
            (r'\\f2\\b\s*\{\\ltrch ([^}:]+)\}(?!\s*<<LABEL>>)', r'<<ENTITY>>\1<</ENTITY>>'),

            # Bullet points
            (r'\{\\pntext\s*\\\'B7\\tab\}.*?\{\\ltrch ([^}]+)\}', r'<<BULLET>>\1<</BULLET>>'),

            # Remaining field values (catch-all for unmatched ltrch)
            (r'\{\\ltrch ([^}]+)\}', r'<<VALUE>>\1<</VALUE>>'),
        ]

        self.cleanup_patterns = [
            # Remove an extra < that appears before closing tags
            (r'<(</(H[123]|LABEL|ENTITY|BULLET|VALUE)>>)', r'\1'),
        ]

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
            cleaned_text = self._clean_text(plain_text)
            return self._promote_planet_headers(cleaned_text)
        except Exception as e:
            raise RuntimeError(f"Failed to convert RTF content: {e}") from e

    def _preserve_structure(self, rtf_content: str) -> str:
        """Preserve structural markers before RTF conversion."""
        if not rtf_content.strip():
            return rtf_content

        text = rtf_content
        for pattern, replacement in self.structure_patterns:
            text = re.sub(pattern, replacement, text)

        return text

    def _clean_text(self, text: str) -> str:
        """Clean and normalize the converted text while preserving structure markers."""
        if not text.strip():
            return text

        # Apply cleanup patterns
        cleaned_text = self._remove_rtf_artifacts(text)

        # Normalize line spacing
        return self._normalize_line_spacing(cleaned_text)

    def _remove_rtf_artifacts(self, text: str) -> str:
        """Remove RTF artifacts while preserving our structure tags."""
        for pattern, replacement in self.cleanup_patterns:
            text = re.sub(pattern, replacement, text)
        return text

    def _normalize_line_spacing(self, text: str) -> str:
        """Normalize line spacing by removing consecutive empty lines."""
        lines = [line.rstrip() for line in text.split('\n')]
        normalized_lines = []
        prev_empty = False

        for line in lines:
            if line.strip():
                normalized_lines.append(line)
                prev_empty = False
                continue

            # Only add an empty line if previous wasn't empty
            if not prev_empty:
                normalized_lines.append('')
                prev_empty = True

        return '\n'.join(normalized_lines)

    def _promote_planet_headers(self, text: str) -> str:
        """Promote ENTITY tags to H3 headers when followed by Type: labels."""
        if not text.strip():
            return text

        lines = text.split('\n')
        result_lines = []

        for i, line in enumerate(lines):
            if not self._contains_entity_tag(line):
                result_lines.append(line)
                continue

            if not self._has_type_label_ahead(lines, i):
                result_lines.append(line)
                continue

            converted_line = self._convert_entity_to_h3(line)
            result_lines.append(converted_line)

        return '\n'.join(result_lines)

    def _contains_entity_tag(self, line: str) -> bool:
        """Check if line contains both opening and closing ENTITY tags."""
        return '<<ENTITY>>' in line and '</ENTITY>>' in line

    def _has_type_label_ahead(self, lines: list[str], current_index: int) -> bool:
        """Check if a Type: label appears in the next few lines."""
        LOOKAHEAD_LINES = 3
        TYPE_LABELS = ['<<LABEL>>Type:', '<<LABEL>>type:']
        STRUCTURAL_TAGS = ['<<H1>>', '<<H2>>', '<<H3>>', '<<ENTITY>>']

        end_index = min(current_index + 1 + LOOKAHEAD_LINES, len(lines))

        for j in range(current_index + 1, end_index):
            next_line = lines[j].strip()

            # Found a type label - early return
            if any(label in next_line for label in TYPE_LABELS):
                return True

            # Stop looking if we hit another structural element - early return
            if any(tag in next_line for tag in STRUCTURAL_TAGS):
                return False

        return False

    def _convert_entity_to_h3(self, line: str) -> str:
        """Convert ENTITY tags to H3 tags."""
        return line.replace('<<ENTITY>>', '<<H3>>').replace('</ENTITY>>', '</H3>>')
