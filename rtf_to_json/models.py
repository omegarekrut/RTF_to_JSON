"""Pydantic data models for Rogue Trader entities."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class PhysicalProperties(BaseModel):
    """Physical properties of celestial bodies."""
    body: str
    gravity: str
    atmosphere: Dict[str, str]
    climate: str
    habitability: str


class Geography(BaseModel):
    """Geographic information."""
    continents: int = 0
    islands: int = 0
    territories: int = 0


class ResourceLevel(BaseModel):
    """Resource level and quantity."""
    level: str
    quantity: int


class MineralResources(BaseModel):
    """Mineral resources."""
    ornamentals: Optional[ResourceLevel] = None
    radioactives: Optional[ResourceLevel] = None
    exotic_materials: Optional[ResourceLevel] = None


class Resources(BaseModel):
    """Resource information."""
    mineral: Optional[MineralResources] = None
    organic_compounds: str = "None"
    archeotech_caches: str = "None"
    xenos_ruins: str = "None"


class CelestialBody(BaseModel):
    """Represents a planet, moon, or other celestial body."""
    id: str
    name: str
    type: str
    physical_properties: Optional[PhysicalProperties] = None
    geography: Optional[Geography] = None
    resources: Optional[Resources] = None
    inhabitants: str = "None"
    inhabitant_development: str = "None"
    warp_storm: str = "None"
    satellites: List['CelestialBody'] = Field(default_factory=list)


class ZoneHazard(BaseModel):
    """Represents a hazard or anomaly within a zone."""
    name: str
    description: str


class Zone(BaseModel):
    """Represents an orbital zone within a system."""
    name: str
    influence: str = "Normal"
    celestial_bodies: List[CelestialBody] = Field(default_factory=list)
    hazards: List[ZoneHazard] = Field(default_factory=list)


class Ship(BaseModel):
    """Represents a ship or vessel."""
    name: str
    species: Optional[str] = None
    ship_type: str
    ship_class: str
    modifications: str = "None"


class PirateDen(BaseModel):
    """Represents a pirate den or station."""
    type: str
    description: str
    ship_count: int = 0
    ships: List[Ship] = Field(default_factory=list)


class System(BaseModel):
    """Represents a star system."""
    id: str
    name: str
    features: List[str] = Field(default_factory=list)
    additional_rules: Optional[str] = None
    star_type: Optional[str] = None
    zones: List[Zone] = Field(default_factory=list)
    pirate_dens: List[PirateDen] = Field(default_factory=list)


class CharacterStats(BaseModel):
    """Character statistics."""
    WS: Optional[int] = None  # Weapon Skill
    BS: Optional[int] = None  # Ballistic Skill
    S: Optional[int] = None   # Strength
    T: Optional[int] = None   # Toughness
    Ag: Optional[int] = None  # Agility
    Int: Optional[int] = None # Intelligence
    Per: Optional[int] = None # Perception
    WP: Optional[int] = None  # Willpower
    Fel: Optional[int] = None # Fellowship


class CombatInfo(BaseModel):
    """Combat-related information."""
    movement: Optional[str] = None
    wounds: Optional[int] = None
    armour: str = "None"
    total_tb: Optional[int] = None


class CharacterAbilities(BaseModel):
    """Character abilities and traits."""
    skills: str = "None"
    talents: str = "None"
    traits: List[str] = Field(default_factory=list)
    weapons: List[str] = Field(default_factory=list)


class Character(BaseModel):
    """Represents a character or NPC."""
    name: str
    type: str = "NPC"
    stats: Optional[CharacterStats] = None
    combat: Optional[CombatInfo] = None
    abilities: Optional[CharacterAbilities] = None


class CampaignData(BaseModel):
    """Root model for all campaign data."""
    systems: List[System] = Field(default_factory=list)
    characters: List[Character] = Field(default_factory=list)