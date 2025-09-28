"""JSON schema validation for campaign data."""

import json
from typing import Dict, Any, List
from jsonschema import validate, ValidationError as JsonSchemaValidationError


class CampaignValidationError(Exception):
    """Custom validation error for campaign data."""
    pass


class CampaignValidator:
    """Validator for Rogue Trader campaign data."""

    def __init__(self):
        self._build_schema_components()
        self._build_main_schema()

    def _build_schema_components(self) -> None:
        """Build reusable schema components."""
        self.resource_level_schema = {
            "type": ["object", "null"],
            "properties": {
                "level": {"type": "string"},
                "quantity": {"type": "integer"}
            }
        }

        self.atmosphere_schema = {
            "type": "object",
            "properties": {
                "presence": {"type": "string"},
                "composition": {"type": "string"}
            }
        }

        self.physical_properties_schema = {
            "type": ["object", "null"],
            "properties": {
                "body": {"type": "string"},
                "gravity": {"type": "string"},
                "atmosphere": self.atmosphere_schema,
                "climate": {"type": "string"},
                "habitability": {"type": "string"}
            }
        }

        self.geography_schema = {
            "type": ["object", "null"],
            "properties": {
                "continents": {"type": "integer"},
                "islands": {"type": "integer"},
                "territories": {"type": "integer"}
            }
        }

        self.mineral_resources_schema = {
            "type": ["object", "null"],
            "properties": {
                "ornamentals": self.resource_level_schema,
                "radioactives": self.resource_level_schema,
                "exotic_materials": self.resource_level_schema
            }
        }

        self.resources_schema = {
            "type": ["object", "null"],
            "properties": {
                "mineral": self.mineral_resources_schema,
                "organic_compounds": {"type": "string"},
                "archeotech_caches": {"type": "string"},
                "xenos_ruins": {"type": "string"}
            }
        }

        self.ship_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "species": {"type": ["string", "null"]},
                "ship_type": {"type": "string"},
                "ship_class": {"type": "string"},
                "modifications": {"type": "string"}
            },
            "required": ["name", "ship_type", "ship_class"]
        }

        self.celestial_body_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "type": {"type": "string"},
                "physical_properties": self.physical_properties_schema,
                "geography": self.geography_schema,
                "resources": self.resources_schema,
                "inhabitants": {"type": "string"},
                "satellites": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/celestial_body"}
                }
            },
            "required": ["id", "name", "type"]
        }

        self.zone_hazard_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["name", "description"]
        }

        self.zone_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "influence": {"type": "string"},
                "celestial_bodies": {
                    "type": "array",
                    "items": self.celestial_body_schema
                },
                "hazards": {
                    "type": "array",
                    "items": self.zone_hazard_schema
                }
            },
            "required": ["name"]
        }

        self.pirate_den_schema = {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "description": {"type": "string"},
                "ship_count": {"type": "integer"},
                "ships": {
                    "type": "array",
                    "items": self.ship_schema
                }
            },
            "required": ["type", "description"]
        }

        self.character_stats_schema = {
            "type": ["object", "null"],
            "properties": {
                stat: {"type": ["integer", "null"]}
                for stat in ["WS", "BS", "S", "T", "Ag", "Int", "Per", "WP", "Fel"]
            }
        }

        self.character_combat_schema = {
            "type": ["object", "null"],
            "properties": {
                "movement": {"type": ["string", "null"]},
                "wounds": {"type": ["integer", "null"]},
                "armour": {"type": "string"},
                "total_tb": {"type": ["integer", "null"]}
            }
        }

        self.character_abilities_schema = {
            "type": ["object", "null"],
            "properties": {
                "skills": {"type": "string"},
                "talents": {"type": "string"},
                "traits": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "weapons": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }

        self.character_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string"},
                "stats": self.character_stats_schema,
                "combat": self.character_combat_schema,
                "abilities": self.character_abilities_schema
            },
            "required": ["name", "type"]
        }

        self.system_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "features": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "additional_rules": {"type": ["string", "null"]},
                "star_type": {"type": ["string", "null"]},
                "zones": {
                    "type": "array",
                    "items": self.zone_schema
                },
                "pirate_dens": {
                    "type": "array",
                    "items": self.pirate_den_schema
                }
            },
            "required": ["id", "name"]
        }

    def _build_main_schema(self) -> None:
        """Build the main campaign data schema."""
        self.campaign_schema = {
            "type": "object",
            "properties": {
                "campaign_data": {
                    "type": "object",
                    "properties": {
                        "systems": {
                            "type": "array",
                            "items": self.system_schema
                        },
                        "characters": {
                            "type": "array",
                            "items": self.character_schema
                        }
                    },
                    "required": ["systems", "characters"]
                }
            },
            "required": ["campaign_data"],
            "$defs": {
                "celestial_body": self.celestial_body_schema
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate campaign data against schema."""
        if not data:
            return ["Empty data provided"]

        try:
            validate(instance=data, schema=self.campaign_schema)
            return []
        except JsonSchemaValidationError as e:
            return [f"Schema validation failed: {e.message}"]
        except Exception as e:
            return [f"Validation error: {str(e)}"]

    def validate_json_string(self, json_string: str) -> List[str]:
        """Validate JSON string against campaign schema."""
        if not json_string.strip():
            return ["Empty JSON string provided"]

        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            return [f"Invalid JSON: {e}"]

        return self.validate_data(data)

    def is_valid_data(self, data: Dict[str, Any]) -> bool:
        """Check if campaign data is valid."""
        return len(self.validate_data(data)) == 0

    def is_valid_json_string(self, json_string: str) -> bool:
        """Check if JSON string is valid campaign data."""
        return len(self.validate_json_string(json_string)) == 0

    def validate_and_raise(self, data: Dict[str, Any]) -> None:
        """Validate data and raise exception if invalid."""
        errors = self.validate_data(data)
        if errors:
            raise CampaignValidationError(f"Validation failed: {'; '.join(errors)}")


# Module-level convenience functions for backward compatibility
_default_validator = CampaignValidator()

def validate_campaign_data(data: Dict[str, Any]) -> List[str]:
    """Validate campaign data against schema."""
    return _default_validator.validate_data(data)

def validate_json_string(json_string: str) -> List[str]:
    """Validate JSON string against campaign schema."""
    return _default_validator.validate_json_string(json_string)

def is_valid_campaign_data(data: Dict[str, Any]) -> bool:
    """Check if campaign data is valid."""
    return _default_validator.is_valid_data(data)

def is_valid_json_string(json_string: str) -> bool:
    """Check if JSON string is valid campaign data."""
    return _default_validator.is_valid_json_string(json_string)