"""Finite State Machine parser for structured RTF text."""

import re
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from .models import (
    System, Zone, CelestialBody, Ship, PirateDen, Character,
    PhysicalProperties, Geography, Resources, MineralResources, ResourceLevel,
    CharacterStats, CombatInfo, CharacterAbilities, CampaignData
)


class ParserState(Enum):
    """Parser states for the finite state machine."""
    SYSTEM_HEADER = "system_header"
    SYSTEM_FEATURES = "system_features"
    SYSTEM_DETAILS = "system_details"
    PIRATE_DEN = "pirate_den"
    SHIP_DETAILS = "ship_details"
    ZONE_HEADER = "zone_header"
    PLANET_DETAILS = "planet_details"
    MOON_DETAILS = "moon_details"
    CHARACTER_STATS = "character_stats"
    UNKNOWN = "unknown"


class CampaignParser:
    """Finite State Machine parser for Rogue Trader campaign data."""

    def __init__(self) -> None:
        self.state = ParserState.UNKNOWN
        self._reset_current_entities()
        self.systems: List[System] = []
        self.characters: List[Character] = []
        self.system_counter = 1
        self.planet_counter = 1
        self.character_counter = 1

        # Initialize dispatch tables
        self._setup_line_processors()
        self._setup_field_handlers()

    def _reset_current_entities(self) -> None:
        """Reset all current entity references."""
        self.current_system: Optional[System] = None
        self.current_zone: Optional[Zone] = None
        self.current_planet: Optional[CelestialBody] = None
        self.current_pirate_den: Optional[PirateDen] = None
        self.current_ship: Optional[Ship] = None
        self.current_character: Optional[Character] = None

    def _setup_line_processors(self) -> None:
        """Setup line processing dispatch table."""
        self.line_processors = [
            ('<<H1>>', self._handle_system_header),
            ('<<H2>>', self._handle_zone_header),
            ('<<H3>>', self._handle_moon_header),
            ('<<ENTITY>>', self._handle_entity_name),
            ('<<LABEL>>', self._handle_label_line),
            ('<<BULLET>>', self._handle_bullet_line),
        ]

    def _setup_field_handlers(self) -> None:
        """Setup field handling dispatch tables."""
        # System field handlers
        self.system_field_handlers = {
            "additional special rule": lambda v: setattr(self.current_system, 'additional_rules', v),
            "star type": lambda v: setattr(self.current_system, 'star_type', v),
        }

        # Zone field handlers
        self.zone_field_handlers = {
            "system influence": lambda v: setattr(self.current_zone, 'influence', v),
        }

        # Ship field handlers
        self.ship_field_handlers = {
            "species": lambda v: setattr(self.current_ship, 'species', v),
            "ship type": lambda v: setattr(self.current_ship, 'ship_type', v),
            "ship class": lambda v: setattr(self.current_ship, 'ship_class', v),
            "orky ship modifications": lambda v: setattr(self.current_ship, 'modifications', v),
        }

        # Pirate den field handlers
        self.pirate_den_field_handlers = {
            "pirate den": lambda v: setattr(self.current_pirate_den, 'description', v),
            "number of pirate ships present": self._set_pirate_ship_count,
        }

        # Planet field categories
        self.planet_physical_fields = {
            "body", "gravity", "atmospheric presence",
            "atmospheric composition", "climate", "habitability"
        }

        self.planet_geography_fields = {
            "major continents or archipelagos", "smaller islands", "territories"
        }

        self.planet_resource_fields = {
            "organic compounds", "archeotech caches", "xenos ruins"
        }

        # Physical properties field handlers
        self.physical_property_handlers = {
            "body": lambda v: setattr(self.current_planet.physical_properties, 'body', v),
            "gravity": lambda v: setattr(self.current_planet.physical_properties, 'gravity', v),
            "atmospheric presence": lambda v: self.current_planet.physical_properties.atmosphere.update({"presence": v}),
            "atmospheric composition": lambda v: self.current_planet.physical_properties.atmosphere.update({"composition": v}),
            "climate": lambda v: setattr(self.current_planet.physical_properties, 'climate', v),
            "habitability": lambda v: setattr(self.current_planet.physical_properties, 'habitability', v),
        }

        # Geography field handlers
        self.geography_handlers = {
            "major continents or archipelagos": lambda v: setattr(self.current_planet.geography, 'continents', self._parse_int_or_zero(v)),
            "smaller islands": lambda v: setattr(self.current_planet.geography, 'islands', self._parse_int_or_zero(v)),
            "territories": lambda v: setattr(self.current_planet.geography, 'territories', self._parse_int_or_zero(v)),
        }

        # Resource field handlers
        self.resource_handlers = {
            "organic compounds": lambda v: setattr(self.current_planet.resources, 'organic_compounds', v),
            "archeotech caches": lambda v: setattr(self.current_planet.resources, 'archeotech_caches', v),
            "xenos ruins": lambda v: setattr(self.current_planet.resources, 'xenos_ruins', v),
        }

        # Resource bullet mapping
        self.resource_bullet_mapping = {
            "ornamental": "ornamentals",
            "radioactive": "radioactives",
            "exotic": "exotic_materials",
        }

    def parse(self, structured_text: str) -> CampaignData:
        """Parse structured text and return campaign data."""
        if not structured_text.strip():
            return CampaignData(systems=[], characters=[])

        lines = structured_text.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                self._process_line(line)

        self._finalize_all_entities()
        return CampaignData(systems=self.systems, characters=self.characters)

    def _process_line(self, line: str) -> None:
        """Process a single line using a dispatch table."""
        for prefix, handler in self.line_processors:
            if line.startswith(prefix):
                handler(line)
                return

    def _extract_text(self, line: str, tag: str) -> str:
        """Extract text content from the tagged line."""
        pattern = f'<<{tag}>>(.*?)</{tag}>>'
        match = re.search(pattern, line)
        return match.group(1).strip() if match else ""

    def _extract_label_and_value(self, line: str) -> tuple[str, str]:
        """Extract label and value from a line."""
        label_match = re.search(r'<<LABEL>>(.*?)<</LABEL>>', line)
        value_match = re.search(r'<<VALUE>>(.*?)<</VALUE>>', line)

        label = label_match.group(1).strip() if label_match else ""
        value = value_match.group(1).strip() if value_match else ""
        return label, value

    def _handle_system_header(self, line: str) -> None:
        """Handle system header and transition to system processing."""
        self._finalize_all_entities()

        system_name = self._extract_text(line, 'H1')
        self.current_system = System(
            id=f"system_{self.system_counter:03d}",
            name=system_name
        )
        self.system_counter += 1
        self.state = ParserState.SYSTEM_HEADER

    def _handle_zone_header(self, line: str) -> None:
        """Handle zone header and transition to zone processing."""
        self._finalize_zone_entities()

        zone_name = self._extract_text(line, 'H2')

        if zone_name == "Pirate Den":
            self.state = ParserState.PIRATE_DEN
            self.current_pirate_den = PirateDen(
                type="space_station",
                description=zone_name
            )
            return

        self.state = ParserState.ZONE_HEADER
        self.current_zone = Zone(name=zone_name)

    def _handle_moon_header(self, line: str) -> None:
        """Handle moon/planet header."""
        self._finalize_planet_entities()

        body_name = self._extract_text(line, 'H3')
        self.current_planet = CelestialBody(
            id=f"planet_{self.planet_counter:03d}",
            name=body_name,
            type="Planet"
        )
        self.planet_counter += 1
        self.state = ParserState.PLANET_DETAILS

    def _handle_entity_name(self, line: str) -> None:
        """Handle entity names (ships, characters)."""
        entity_name = self._extract_text(line, 'ENTITY')

        if self.state == ParserState.PIRATE_DEN:
            self._finalize_ship()
            self.current_ship = Ship(
                name=entity_name,
                ship_type=entity_name,
                ship_class="Unknown"
            )
            self.state = ParserState.SHIP_DETAILS
            return

        self.current_character = Character(
            name=entity_name,
            type="NPC"
        )
        self.state = ParserState.CHARACTER_STATS

    def _handle_label_line(self, line: str) -> None:
        """Handle label-value pairs using dispatch tables."""
        label, value = self._extract_label_and_value(line)
        if not label:
            return

        label_lower = label.lower().replace(':', '').strip()

        # State-based handler dispatch
        state_handlers = {
            ParserState.SYSTEM_HEADER: (self.current_system, self.system_field_handlers),
            ParserState.ZONE_HEADER: (self.current_zone, self.zone_field_handlers),
            ParserState.SHIP_DETAILS: (self.current_ship, self.ship_field_handlers),
            ParserState.PIRATE_DEN: (self.current_pirate_den, self.pirate_den_field_handlers),
            ParserState.PLANET_DETAILS: (self.current_planet, None),  # Special handling
        }

        entity, handlers = state_handlers.get(self.state, (None, None))
        if not entity:
            return

        # Special handling for planet details
        if self.state == ParserState.PLANET_DETAILS:
            self._handle_planet_field(label_lower, value)
            return

        # Regular handler dispatch
        if handlers and label_lower in handlers:
            handlers[label_lower](value)

    def _handle_bullet_line(self, line: str) -> None:
        """Handle bullet point items."""
        bullet_text = self._extract_text(line, 'BULLET')

        if self.state == ParserState.SYSTEM_HEADER and self.current_system:
            self.current_system.features.append(bullet_text)
            return

        if self.state == ParserState.PLANET_DETAILS and self.current_planet:
            self._parse_resource_bullet(bullet_text)

    def _handle_planet_field(self, label: str, value: str) -> None:
        """Handle planet-specific fields using category dispatch."""
        # Direct field assignment
        if label == "type":
            self.current_planet.type = value
            return
        if label == "inhabitants":
            self.current_planet.inhabitants = value
            return

        # Category-based handling
        if label in self.planet_physical_fields:
            self._ensure_physical_properties()
            self.physical_property_handlers[label](value)
            return

        if label in self.planet_geography_fields:
            self._ensure_geography()
            self.geography_handlers[label](value)
            return

        if label in self.planet_resource_fields:
            self._ensure_resources()
            self.resource_handlers[label](value)

    def _parse_resource_bullet(self, bullet_text: str) -> None:
        """Parse resource bullet points like 'Major (91) ornamentals'."""
        match = re.match(r'(\w+)\s*\((\d+)\)\s*(.+)', bullet_text)
        if not match:
            return

        level, quantity_str, resource_type = match.groups()
        try:
            quantity = int(quantity_str)
        except ValueError:
            return

        self._ensure_mineral_resources()
        resource_level = ResourceLevel(level=level, quantity=quantity)

        # Find matching resource type
        for keyword, field_name in self.resource_bullet_mapping.items():
            if keyword in resource_type.lower():
                setattr(self.current_planet.resources.mineral, field_name, resource_level)
                return

    def _ensure_physical_properties(self) -> None:
        """Ensure physical properties object exists."""
        if not self.current_planet.physical_properties:
            self.current_planet.physical_properties = PhysicalProperties(
                body="", gravity="", atmosphere={}, climate="", habitability=""
            )

    def _ensure_geography(self) -> None:
        """Ensure geography object exists."""
        if not self.current_planet.geography:
            self.current_planet.geography = Geography()

    def _ensure_resources(self) -> None:
        """Ensure resources object exists."""
        if not self.current_planet.resources:
            self.current_planet.resources = Resources()

    def _ensure_mineral_resources(self) -> None:
        """Ensure mineral resources object exists."""
        self._ensure_resources()
        if not self.current_planet.resources.mineral:
            self.current_planet.resources.mineral = MineralResources()

    def _parse_int_or_zero(self, value: str) -> int:
        """Parse integer value or return 0 for 'none'."""
        try:
            return 0 if value.lower() == "none" else int(value)
        except ValueError:
            return 0

    def _set_pirate_ship_count(self, value: str) -> None:
        """Set pirate ship count with error handling."""
        try:
            self.current_pirate_den.ship_count = int(value)
        except ValueError:
            pass

    def _finalize_ship(self) -> None:
        """Finalize current ship."""
        if not (self.current_ship and self.current_pirate_den):
            return
        self.current_pirate_den.ships.append(self.current_ship)
        self.current_ship = None

    def _finalize_planet_entities(self) -> None:
        """Finalize planet-level entities."""
        if self.current_planet and self.current_zone:
            self.current_zone.celestial_bodies.append(self.current_planet)
            self.current_planet = None

    def _finalize_zone_entities(self) -> None:
        """Finalize zone-level entities."""
        self._finalize_planet_entities()

        if self.current_zone and self.current_system:
            self.current_system.zones.append(self.current_zone)
            self.current_zone = None

        if self.current_pirate_den and self.current_system:
            self.current_system.pirate_dens.append(self.current_pirate_den)
            self.current_pirate_den = None

    def _finalize_all_entities(self) -> None:
        """Finalize and store all current entities."""
        self._finalize_ship()
        self._finalize_zone_entities()

        if self.current_system:
            self.systems.append(self.current_system)
            self.current_system = None

        if self.current_character:
            self.characters.append(self.current_character)
            self.current_character = None