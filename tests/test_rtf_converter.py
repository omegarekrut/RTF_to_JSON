"""Tests for RTF conversion functionality."""

import pytest
from pathlib import Path
from rtf_to_json.rtf_converter import RTFConverter


class TestRTFConverter:
    """Test cases for RTFConverter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = RTFConverter()

    def test_converter_initialization(self):
        """Test that converter initializes correctly."""
        assert self.converter is not None

    def test_convert_simple_rtf_content(self):
        """Test conversion of simple RTF content."""
        rtf_content = r"{\rtf1\ansi Hello World}"
        result = self.converter.convert_rtf_content(rtf_content)
        assert "Hello World" in result

    def test_convert_nonexistent_file(self):
        """Test handling of nonexistent file."""
        fake_path = Path("/nonexistent/file.rtf")
        with pytest.raises(FileNotFoundError):
            self.converter.convert_file(fake_path)

    def test_clean_text_removes_excess_whitespace(self):
        """Test that text cleaning works properly."""
        dirty_text = "Line 1\n\n\n\nLine 2\n   \n\nLine 3"
        cleaned = self.converter._clean_text(dirty_text)
        lines = cleaned.split('\n')
        assert len([line for line in lines if line.strip()]) == 3
        assert "Line 1" in cleaned
        assert "Line 2" in cleaned
        assert "Line 3" in cleaned