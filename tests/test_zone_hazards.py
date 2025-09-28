"""Tests for zone hazard parsing functionality."""

import pytest

from rtf_to_json.parser import CampaignParser


def _parse_and_get_zone(parser, structured_text):
    """Parse text and return the first zone."""
    campaign_data = parser.parse(structured_text)
    assert len(campaign_data.systems) == 1
    system = campaign_data.systems[0]
    assert len(system.zones) >= 1
    return system.zones[0]


def _create_system_text(zone_name, zone_content):
    """Helper to create structured text with a system and zone."""
    return f"""
<<H1>>Test System</H1>>
<<H2>>{zone_name}</H2>>
<<LABEL>>System Influence:</LABEL>><<VALUE>>Normal</VALUE>>
{zone_content}
""".strip()


class TestZoneHazards:
    """Test zone hazard parsing functionality."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for tests."""
        return CampaignParser()

    def test_dust_cloud_hazard_parsing(self, parser):
        """Test parsing of Dust Cloud hazards."""
        zone_content = """
<<ENTITY>>Dust Cloud</ENTITY>>
<<VALUE>>Dust Clouds follow the rules for Nebulae on page 227 of the Rogue Trader Core Rulebook.</VALUE>>
"""
        text = _create_system_text("Outer Reaches", zone_content)
        zone = _parse_and_get_zone(parser, text)

        assert zone.name == "Outer Reaches"
        assert len(zone.hazards) == 1

        hazard = zone.hazards[0]
        assert hazard.name == "Dust Cloud"
        assert "Dust Clouds follow the rules for Nebulae" in hazard.description

    def test_multiple_hazards_in_zone(self, parser):
        """Test parsing multiple hazards in a single zone."""
        zone_content = """
<<ENTITY>>Solar Flares</ENTITY>>
<<VALUE>>Solar flares description.</VALUE>>
<<ENTITY>>Gravity Riptide</ENTITY>>
<<VALUE>>Gravity riptide description.</VALUE>>
"""
        text = _create_system_text("Inner Cauldron", zone_content)
        zone = _parse_and_get_zone(parser, text)

        assert len(zone.hazards) == 2
        assert zone.hazards[0].name == "Solar Flares"
        assert zone.hazards[1].name == "Gravity Riptide"

    def test_hazard_without_description(self, parser):
        """Test parsing hazards without descriptions."""
        zone_content = """
<<ENTITY>>Asteroid Belt</ENTITY>>
<<H3>>Unnamed Planet 1</H3>>
"""
        text = _create_system_text("Primary Biosphere", zone_content)
        zone = _parse_and_get_zone(parser, text)

        assert len(zone.hazards) == 1
        hazard = zone.hazards[0]
        assert hazard.name == "Asteroid Belt"
        assert hazard.description == ""

    def test_hazard_identification(self, parser):
        """Test the _is_zone_hazard method."""
        known_hazards = [
            "Dust Cloud", "Gravity Riptide", "Solar Flare", "Solar Flares",
            "Radiation Burst", "Radiation Bursts", "Gravity Tide", "Gravity Tides",
            "Asteroid Belt", "Derelict Station"
        ]

        non_hazards = ["Unnamed System 1", "Kill Kroozer", "Imperial Captain"]

        for hazard in known_hazards:
            assert parser._is_zone_hazard(hazard), f"{hazard} should be identified as a hazard"

        for non_hazard in non_hazards:
            assert not parser._is_zone_hazard(non_hazard), f"{non_hazard} should not be identified as a hazard"

    def test_zone_with_celestial_bodies_and_hazards(self, parser):
        """Test zone containing both celestial bodies and hazards."""
        zone_content = """
<<ENTITY>>Dust Cloud</ENTITY>>
<<VALUE>>Dust cloud description.</VALUE>>
<<H3>>Unnamed System 1</H3>>
<<LABEL>>Type:</LABEL>><<VALUE>>Planet</VALUE>>
"""
        text = _create_system_text("Outer Reaches", zone_content)
        zone = _parse_and_get_zone(parser, text)

        assert len(zone.hazards) == 1
        assert len(zone.celestial_bodies) == 1
        assert zone.hazards[0].name == "Dust Cloud"
        assert zone.celestial_bodies[0].name == "Unnamed System 1"

    def test_singular_and_plural_hazard_parsing(self, parser):
        """Test parsing both singular and plural forms of hazards."""
        structured_text = """
<<H1>>Test System</H1>>
<<H2>>Inner Cauldron</H2>>
<<LABEL>>System Influence:</LABEL>><<VALUE>>Normal</VALUE>>
<<ENTITY>>Solar Flare</ENTITY>>
<<VALUE>>Single solar flare description.</VALUE>>
<<H2>>Primary Biosphere</H2>>
<<LABEL>>System Influence:</LABEL>><<VALUE>>Normal</VALUE>>
<<ENTITY>>Radiation Bursts</ENTITY>>
<<VALUE>>Multiple radiation bursts description.</VALUE>>
""".strip()

        campaign_data = parser.parse(structured_text)
        system = campaign_data.systems[0]
        assert len(system.zones) == 2

        # First zone with singular hazard
        zone1 = system.zones[0]
        assert zone1.name == "Inner Cauldron"
        assert len(zone1.hazards) == 1
        assert zone1.hazards[0].name == "Solar Flare"

        # Second zone with plural hazard
        zone2 = system.zones[1]
        assert zone2.name == "Primary Biosphere"
        assert len(zone2.hazards) == 1
        assert zone2.hazards[0].name == "Radiation Bursts"
