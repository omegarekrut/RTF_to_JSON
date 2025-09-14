"""Tests for Pydantic data models."""

import pytest
from rtf_to_json.models import (
    CampaignData, System, Zone, CelestialBody, Ship, PirateDen,
    Character, CharacterStats, PhysicalProperties, Resources
)


class TestModels:
    """Test cases for Pydantic models."""

    def test_campaign_data_creation(self):
        """Test that CampaignData model can be created."""
        campaign = CampaignData()
        assert campaign.systems == []
        assert campaign.characters == []

    def test_system_creation(self):
        """Test that System model can be created with required fields."""
        system = System(id="sys_001", name="Test System")
        assert system.id == "sys_001"
        assert system.name == "Test System"
        assert system.features == []
        assert system.zones == []

    def test_celestial_body_creation(self):
        """Test that CelestialBody model can be created."""
        body = CelestialBody(
            id="planet_001",
            name="Test Planet",
            type="Planet"
        )
        assert body.id == "planet_001"
        assert body.name == "Test Planet"
        assert body.type == "Planet"
        assert body.inhabitants == "None"

    def test_character_stats(self):
        """Test that CharacterStats model works correctly."""
        stats = CharacterStats(WS=40, BS=35, S=30)
        assert stats.WS == 40
        assert stats.BS == 35
        assert stats.S == 30
        assert stats.T is None

    def test_ship_creation(self):
        """Test that Ship model can be created."""
        ship = Ship(
            name="Test Ship",
            ship_type="Cruiser",
            ship_class="Imperial"
        )
        assert ship.name == "Test Ship"
        assert ship.ship_type == "Cruiser"
        assert ship.ship_class == "Imperial"
        assert ship.modifications == "None"