"""Finite State Machine parser for structured RTF text."""

import re
from enum import Enum
from typing import List, Optional, Any
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
        self.pending_label: Optional[str] = None
        self.ship_modifications: List[str] = []

        self._setup_handlers()

    def _reset_current_entities(self) -> None:
        """Reset all current entity references."""
        self.current_system: Optional[System] = None
        self.current_zone: Optional[Zone] = None
        self.current_planet: Optional[CelestialBody] = None
        self.current_pirate_den: Optional[PirateDen] = None
        self.current_ship: Optional[Ship] = None
        self.current_character: Optional[Character] = None

    def _setup_handlers(self) -> None:
        """Set up all dispatch handlers."""
        # Line processors - keep simple for prefix matching
        self.line_processors = [
            ('<<H1>>', self._handle_system_header),
            ('<<H2>>', self._handle_zone_header),
            ('<<H3>>', self._handle_moon_header),
            ('<<ENTITY>>', self._handle_entity_name),
            ('<<LABEL>>', self._handle_label_line),
            ('<<BULLET>>', self._handle_bullet_line),
            ('<<VALUE>>', self._handle_standalone_value),
        ]

        # State-based field processors using dictionaries
        self.state_processors = {
            ParserState.SYSTEM_HEADER: self._process_system_field,
            ParserState.ZONE_HEADER: self._process_zone_field,
            ParserState.SHIP_DETAILS: self._process_ship_field,
            ParserState.PIRATE_DEN: self._process_pirate_den_field,
            ParserState.PLANET_DETAILS: self._process_planet_field,
            ParserState.CHARACTER_STATS: self._process_character_field,
        }

        # Planet field processors
        self.planet_processors = {
            # Direct assignments
            'type': lambda v: setattr(self.current_planet, 'type', v),
            'inhabitants': lambda v: setattr(self.current_planet, 'inhabitants', v),

            # Physical properties
            'body': self._set_physical_body,
            'gravity': self._set_physical_gravity,
            'atmospheric presence': self._set_atmospheric_presence,
            'atmospheric composition': self._set_atmospheric_composition,
            'climate': self._set_physical_climate,
            'habitability': self._set_physical_habitability,

            # Geography
            'major continents or archipelagos': self._set_continents,
            'smaller islands': self._set_islands,
            'territories': self._set_territories,

            # Resources
            'organic compounds': self._set_organic_compounds,
            'archeotech caches': self._set_archeotech_caches,
            'xenos ruins': self._set_xenos_ruins,
        }

        # Character field processors
        self.character_processors = {
            # Stats
            'ws': lambda v: self._set_character_stat('WS', v),
            'bs': lambda v: self._set_character_stat('BS', v),
            's': lambda v: self._set_character_stat('S', v),
            't': lambda v: self._set_character_stat('T', v),
            'ag': lambda v: self._set_character_stat('Ag', v),
            'int': lambda v: self._set_character_stat('Int', v),
            'per': lambda v: self._set_character_stat('Per', v),
            'wp': lambda v: self._set_character_stat('WP', v),
            'fel': lambda v: self._set_character_stat('Fel', v),

            # Combat
            'movement': lambda v: self._set_character_combat('movement', v),
            'wounds': lambda v: self._set_character_combat('wounds', self._parse_int_or_zero(v)),
            'armour': lambda v: self._set_character_combat('armour', v),
            'total tb': lambda v: self._set_character_combat('total_tb', self._parse_int_or_zero(v)),

            # Abilities
            'skills': lambda v: self._set_character_ability('skills', v),
            'talents': lambda v: self._set_character_ability('talents', v),
            'traits': lambda v: self._set_character_ability('traits', self._parse_list(v)),
            'weapons': lambda v: self._set_character_ability('weapons', self._parse_list(v)),
        }

        self.resource_bullet_mapping = {
            "ornamental": "ornamentals",
            "radioactive": "radioactives",
            "exotic": "exotic_materials",
        }

    def parse(self, structured_text: str) -> CampaignData:
        """Parse structured text and return campaign data."""
        if not structured_text.strip():
            return CampaignData(systems=[], characters=[])

        for line in structured_text.split('\n'):
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
        label_match = re.search(r'<<LABEL>>(.*?)</LABEL>>', line)
        value_match = re.search(r'<<VALUE>>(.*?)</VALUE>>', line)

        label = label_match.group(1).strip() if label_match else ""
        value = value_match.group(1).strip() if value_match else ""
        return label, value

    def _extract_all_label_value_pairs(self, line: str) -> List[tuple[str, str]]:
        """Extract all label-value pairs from a line."""
        # Find all LABEL tags and their positions
        label_matches = list(re.finditer(r'<<LABEL>>(.*?)</LABEL>>', line))
        if not label_matches:
            return []

        pairs = []
        for label_match in label_matches:
            label = label_match.group(1).strip()
            # Find the next VALUE tag after this LABEL
            search_start = label_match.end()
            value_match = re.search(r'<<VALUE>>(.*?)</VALUE>>', line[search_start:])

            if value_match:
                value = value_match.group(1).strip()
                pairs.append((label, value))
            else:
                pairs.append((label, ""))

        return pairs

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
            self.current_pirate_den = PirateDen(type="unknown", description=zone_name)
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

        if self.state in (ParserState.PIRATE_DEN, ParserState.SHIP_DETAILS):
            self._finalize_ship()
            self.current_ship = Ship(name=entity_name, ship_type=entity_name, ship_class="Unknown")
            self.state = ParserState.SHIP_DETAILS
            return

        if self._should_treat_as_character(entity_name):
            self._finalize_character()
            self.current_character = Character(name=entity_name, type="NPC")
            self.state = ParserState.CHARACTER_STATS

    def _handle_label_line(self, line: str) -> None:
        """Handle label-value pairs."""
        # Extract all label-value pairs on the line
        pairs = self._extract_all_label_value_pairs(line)
        if not pairs:
            return

        # Process each pair
        for label, value in pairs:
            label_lower = label.lower().replace(':', '').strip()

            if value.strip():
                self._process_label_value_pair(label_lower, value)
                self.pending_label = None
            else:
                self.pending_label = label_lower

    def _handle_standalone_value(self, line: str) -> None:
        """Handle standalone VALUE tags."""
        # Check for character stat header pattern first
        if self._is_character_stat_header(line):
            self._convert_current_entity_to_character()
            return

        # Check for character stat values (pipe-separated numbers)
        if self.state == ParserState.CHARACTER_STATS and self._is_character_stat_values(line):
            self._process_character_stat_values(line)
            return

        if not self.pending_label:
            return

        value = self._extract_text(line, 'VALUE')
        if value.strip():
            self._process_label_value_pair(self.pending_label, value)
            self.pending_label = None

    def _process_label_value_pair(self, label: str, value: str) -> None:
        """Process a complete label-value pair using state dispatch."""
        processor = self.state_processors.get(self.state)
        if processor:
            processor(label, value)

    # State-specific field processors
    def _process_system_field(self, label: str, value: str) -> None:
        """Process-system-specific fields."""
        if not self.current_system:
            return

        match label:
            case "additional special rule":
                self.current_system.additional_rules = value
            case "star type":
                self.current_system.star_type = value

    def _process_zone_field(self, label: str, value: str) -> None:
        """Process-zone-specific fields."""
        if not self.current_zone:
            return

        match label:
            case "system influence":
                self.current_zone.influence = value

    def _process_ship_field(self, label: str, value: str) -> None:
        """Process ship-specific fields."""
        if not self.current_ship:
            return

        match label:
            case "species":
                self.current_ship.species = value
            case "ship type":
                self.current_ship.ship_type = value
            case "ship class":
                self.current_ship.ship_class = value
            case "orky ship modifications":
                self.current_ship.modifications = value

    def _process_pirate_den_field(self, label: str, value: str) -> None:
        """Process pirate den-specific fields."""
        if not self.current_pirate_den:
            return

        match label:
            case "pirate den":
                self.current_pirate_den.description = value
                self.current_pirate_den.type = self._extract_pirate_den_type(value)
            case "number of pirate ships present":
                try:
                    self.current_pirate_den.ship_count = int(value)
                except ValueError:
                    pass

    def _extract_pirate_den_type(self, description: str) -> str:
        """Extract pirate den type from description text."""
        desc_lower = description.lower()

        # Common pirate den types in priority order
        type_patterns = [
            ("space station", "space_station"),
            ("orbital platform", "orbital_platform"),
            ("asteroid base", "asteroid_base"),
            ("mining facility", "mining_facility"),
            ("derelict ship", "derelict_ship"),
            ("hidden base", "hidden_base"),
            ("outpost", "outpost"),
            ("station", "space_station"),  # fallback for generic "station"
        ]

        for pattern, type_name in type_patterns:
            if pattern in desc_lower:
                return type_name

        return "unknown"

    def _process_planet_field(self, label: str, value: str) -> None:
        """Process planet-specific fields using dictionary dispatch."""
        if not self.current_planet:
            return

        processor = self.planet_processors.get(label)
        if processor:
            processor(value)

    def _process_character_field(self, label: str, value: str) -> None:
        """Process character-specific fields using dictionary dispatch."""
        if not self.current_character:
            return

        processor = self.character_processors.get(label)
        if processor:
            processor(value)

    # Planet field setters
    def _set_physical_body(self, value: str) -> None:
        self._ensure_physical_properties()
        self.current_planet.physical_properties.body = value

    def _set_physical_gravity(self, value: str) -> None:
        self._ensure_physical_properties()
        self.current_planet.physical_properties.gravity = value

    def _set_atmospheric_presence(self, value: str) -> None:
        self._ensure_physical_properties()
        self.current_planet.physical_properties.atmosphere["presence"] = value

    def _set_atmospheric_composition(self, value: str) -> None:
        self._ensure_physical_properties()
        self.current_planet.physical_properties.atmosphere["composition"] = value

    def _set_physical_climate(self, value: str) -> None:
        self._ensure_physical_properties()
        self.current_planet.physical_properties.climate = value

    def _set_physical_habitability(self, value: str) -> None:
        self._ensure_physical_properties()
        self.current_planet.physical_properties.habitability = value

    def _set_continents(self, value: str) -> None:
        self._ensure_geography()
        self.current_planet.geography.continents = self._parse_int_or_zero(value)

    def _set_islands(self, value: str) -> None:
        self._ensure_geography()
        self.current_planet.geography.islands = self._parse_int_or_zero(value)

    def _set_territories(self, value: str) -> None:
        self._ensure_geography()
        self.current_planet.geography.territories = self._parse_int_or_zero(value)

    def _set_organic_compounds(self, value: str) -> None:
        self._ensure_resources()
        self.current_planet.resources.organic_compounds = value

    def _set_archeotech_caches(self, value: str) -> None:
        self._ensure_resources()
        self.current_planet.resources.archeotech_caches = value

    def _set_xenos_ruins(self, value: str) -> None:
        self._ensure_resources()
        self.current_planet.resources.xenos_ruins = value

    def _handle_bullet_line(self, line: str) -> None:
        """Handle bullet point items."""
        bullet_text = self._extract_text(line, 'BULLET')

        match self.state:
            case ParserState.SYSTEM_HEADER if self.current_system:
                self.current_system.features.append(bullet_text)
            case ParserState.PLANET_DETAILS if self.current_planet:
                self._parse_resource_bullet(bullet_text)
            case ParserState.SHIP_DETAILS if self.current_ship:
                self.ship_modifications.append(bullet_text)

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

        for keyword, field_name in self.resource_bullet_mapping.items():
            if keyword in resource_type.lower():
                setattr(self.current_planet.resources.mineral, field_name, resource_level)
                return

    def _should_treat_as_character(self, entity_name: str) -> bool:
        """Determine if an entity should be treated as a character."""
        name_lower = entity_name.lower()

        # Early return for obvious non-characters
        header_keywords = {
            "asteroid cluster", "asteroid belt", "debris field", "gas giant",
            "space station", "orbital platform", "mining facility", "trading post",
            "inner cauldron", "primary biosphere", "outer reaches", "system edge",
            "void station", "orbital structure", "dust cloud", "unnamed system"
        }

        if any(keyword in name_lower for keyword in header_keywords):
            return False

        if re.match(r'unnamed system \d+', name_lower):
            return False

        # Positive indicators
        character_indicators = {"scavenger", "captain", "warrior", "pilot", "navigator", "tech", "enginseer"}
        if any(indicator in name_lower for indicator in character_indicators):
            return True

        # Restrictive fallback
        return self.state == ParserState.CHARACTER_STATS and len(entity_name.split()) <= 2

    def _is_character_stat_header(self, line: str) -> bool:
        """Check if a line contains character stat headers (WS, BS, etc.)."""
        return ("<<VALUE>>WS</VALUE>>" in line and
                "<<VALUE>>BS</VALUE>>" in line and
                "<<VALUE>>S</VALUE>>" in line and
                "<<VALUE>>T</VALUE>>" in line)

    def _convert_current_entity_to_character(self) -> None:
        """Convert the current planet / entity to character when stat block detected."""
        # If we have a current planet, use its name for the character
        if self.current_planet and self.current_planet.name:
            self._finalize_character()
            self.current_character = Character(name=self.current_planet.name, type="NPC")
            self.current_planet = None  # Clear the planet since it's now a character
            self.state = ParserState.CHARACTER_STATS

    def _is_character_stat_values(self, line: str) -> bool:
        """Check if line contains character stat values (pipe-separated numbers)."""
        # Look for pattern like: <<VALUE>>40</VALUE>>|<<VALUE>>-</VALUE>>|<<VALUE>>70</VALUE>>
        # Must have multiple VALUE tags with digits or dashes
        value_matches = re.findall(r'<<VALUE>>([^<]*)</VALUE>>', line)
        if len(value_matches) >= 3:  # At least 3 stat values
            # Check if any of the values contain digits (actual stats)
            return any(re.search(r'\d', val) for val in value_matches)
        return False

    def _process_character_stat_values(self, line: str) -> None:
        """Process character stat values from pipe-separated line."""
        if not self.current_character:
            return

        # Extract all VALUE tags and split by pipe
        values = []
        value_matches = re.findall(r'<<VALUE>>(.*?)</VALUE>>', line)

        # Join all matches and split by pipe
        all_values = '|'.join(value_matches) if value_matches else ''
        stat_values = all_values.split('|')

        # Map to stat names: WS, BS, S, T, Ag, Int, Per, WP, Fel
        stat_names = ['WS', 'BS', 'S', 'T', 'Ag', 'Int', 'Per', 'WP', 'Fel']

        for i, value in enumerate(stat_values[:len(stat_names)]):
            if value.strip() and value.strip() != '-':
                # Extract number from value (handle parentheses)
                clean_value = re.sub(r'[^\d]', '', value)
                if clean_value:
                    self._set_character_stat(stat_names[i], clean_value)

    # Entity management methods
    def _set_character_stat(self, stat_name: str, value: str) -> None:
        """Set a character stat value."""
        self._ensure_character_stats()
        try:
            stat_value = int(value) if value.strip() and value.lower() != "none" else None
            setattr(self.current_character.stats, stat_name, stat_value)
        except ValueError:
            pass

    def _set_character_combat(self, field_name: str, value: Any) -> None:
        """Set a character combat field."""
        self._ensure_character_combat()
        setattr(self.current_character.combat, field_name, value)

    def _set_character_ability(self, field_name: str, value: Any) -> None:
        """Set a character ability field."""
        self._ensure_character_abilities()
        setattr(self.current_character.abilities, field_name, value)

    # Utility methods
    def _parse_int_or_zero(self, value: str) -> int:
        """Parse integer value or return 0 for 'none'."""
        try:
            return 0 if value.lower() == "none" else int(value)
        except ValueError:
            return 0

    def _parse_list(self, value: str) -> List[str]:
        """Parse a comma-separated list value."""
        if not value or value.lower() == "none":
            return []
        return [item.strip() for item in value.split(',') if item.strip()]

    # Object creation helpers
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

    def _ensure_character_stats(self) -> None:
        """Ensure character stats object exists."""
        if not self.current_character.stats:
            self.current_character.stats = CharacterStats()

    def _ensure_character_combat(self) -> None:
        """Ensure character combat object exists."""
        if not self.current_character.combat:
            self.current_character.combat = CombatInfo()

    def _ensure_character_abilities(self) -> None:
        """Ensure character abilities object exists."""
        if not self.current_character.abilities:
            self.current_character.abilities = CharacterAbilities()

    # Finalization methods
    def _finalize_character(self) -> None:
        """Finalize current character."""
        if self.current_character:
            self.characters.append(self.current_character)
            self.current_character = None

    def _finalize_ship(self) -> None:
        """Finalize current ship."""
        if self.current_ship and self.current_pirate_den:
            # Apply accumulated ship modifications
            if self.ship_modifications:
                self.current_ship.modifications = ", ".join(self.ship_modifications)
            self.ship_modifications.clear()

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
        self._finalize_ship()  # Finalize ship before nulling pirate den

        if self.current_zone and self.current_system:
            self.current_system.zones.append(self.current_zone)
            self.current_zone = None

        if self.current_pirate_den and self.current_system:
            self.current_system.pirate_dens.append(self.current_pirate_den)
            self.current_pirate_den = None

    def _finalize_all_entities(self) -> None:
        """Finalize and store all current entities."""
        self._finalize_character()
        self._finalize_zone_entities()

        if self.current_system:
            self.systems.append(self.current_system)
            self.current_system = None
