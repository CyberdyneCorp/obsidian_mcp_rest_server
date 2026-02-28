"""Column type value objects for structured data tables."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self


class ColumnType(str, Enum):
    """Column data types for table columns."""

    TEXT = "text"  # String values
    NUMBER = "number"  # Integer or float
    BOOLEAN = "boolean"  # True/False
    DATE = "date"  # Date only
    DATETIME = "datetime"  # Date and time
    JSON = "json"  # Nested objects/arrays
    ARRAY = "array"  # List of values
    REFERENCE = "reference"  # FK to another table
    DOCUMENT = "document"  # Link to vault document
    COMPUTED = "computed"  # Formula-based (stored expression)
    RICHTEXT = "richtext"  # Markdown content


@dataclass(frozen=True)
class ColumnDefinition:
    """Value object representing a column definition in a table schema.

    Attributes:
        name: Column name (identifier)
        type: Column data type
        required: Whether the column is required (non-null)
        default: Default value for the column
        unique: Whether values must be unique across all rows
        description: Optional description of the column
        reference_table: For REFERENCE type, the target table slug
        reference_column: For REFERENCE type, the target column (default: 'id')
        array_type: For ARRAY type, the type of array elements
        formula: For COMPUTED type, the formula expression
    """

    name: str
    type: ColumnType
    required: bool = False
    default: Any = None
    unique: bool = False
    description: str | None = None
    reference_table: str | None = None
    reference_column: str = "id"
    array_type: ColumnType | None = None
    formula: str | None = None

    def __post_init__(self) -> None:
        """Validate column definition."""
        if not self.name:
            raise ValueError("Column name cannot be empty")

        if self.type == ColumnType.REFERENCE and not self.reference_table:
            raise ValueError("REFERENCE columns must specify reference_table")

        if self.type == ColumnType.COMPUTED and not self.formula:
            raise ValueError("COMPUTED columns must specify formula")

        if self.type == ColumnType.ARRAY and not self.array_type:
            raise ValueError("ARRAY columns must specify array_type")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create ColumnDefinition from dictionary."""
        column_type = data.get("type", "text")
        if isinstance(column_type, str):
            column_type = ColumnType(column_type)

        array_type = data.get("array_type")
        if array_type and isinstance(array_type, str):
            array_type = ColumnType(array_type)

        return cls(
            name=data["name"],
            type=column_type,
            required=data.get("required", False),
            default=data.get("default"),
            unique=data.get("unique", False),
            description=data.get("description"),
            reference_table=data.get("reference_table"),
            reference_column=data.get("reference_column", "id"),
            array_type=array_type,
            formula=data.get("formula"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert ColumnDefinition to dictionary."""
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type.value,
            "required": self.required,
            "unique": self.unique,
        }

        if self.default is not None:
            result["default"] = self.default

        if self.description:
            result["description"] = self.description

        if self.type == ColumnType.REFERENCE:
            result["reference_table"] = self.reference_table
            result["reference_column"] = self.reference_column

        if self.type == ColumnType.ARRAY and self.array_type:
            result["array_type"] = self.array_type.value

        if self.type == ColumnType.COMPUTED:
            result["formula"] = self.formula

        return result

    def validate_value(self, value: Any) -> tuple[bool, str | None]:
        """Validate a value against this column definition.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Handle None values
        if value is None:
            if self.required:
                return False, f"Column '{self.name}' is required"
            return True, None

        # Type-specific validation
        if self.type == ColumnType.TEXT:
            if not isinstance(value, str):
                return False, f"Column '{self.name}' must be a string"

        elif self.type == ColumnType.NUMBER:
            if not isinstance(value, (int, float)):
                return False, f"Column '{self.name}' must be a number"

        elif self.type == ColumnType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"Column '{self.name}' must be a boolean"

        elif self.type == ColumnType.DATE:
            if not isinstance(value, str):
                return False, f"Column '{self.name}' must be a date string (YYYY-MM-DD)"
            # Basic date format validation
            import re

            if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                return False, f"Column '{self.name}' must be in YYYY-MM-DD format"

        elif self.type == ColumnType.DATETIME:
            if not isinstance(value, str):
                return False, f"Column '{self.name}' must be a datetime string"
            # Basic ISO datetime validation
            import re

            if not re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", value):
                return (
                    False,
                    f"Column '{self.name}' must be in ISO datetime format",
                )

        elif self.type == ColumnType.JSON:
            if not isinstance(value, (dict, list)):
                return False, f"Column '{self.name}' must be a JSON object or array"

        elif self.type == ColumnType.ARRAY:
            if not isinstance(value, list):
                return False, f"Column '{self.name}' must be an array"

        elif self.type == ColumnType.REFERENCE:
            # UUID validation
            if not isinstance(value, str):
                return False, f"Column '{self.name}' must be a UUID string"
            import re

            uuid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
            if not re.match(uuid_pattern, value):
                return False, f"Column '{self.name}' must be a valid UUID"

        elif self.type == ColumnType.DOCUMENT:
            # Document reference - should be a UUID string
            if not isinstance(value, str):
                return False, f"Column '{self.name}' must be a UUID string"

        elif self.type == ColumnType.RICHTEXT:
            if not isinstance(value, str):
                return False, f"Column '{self.name}' must be a string"

        elif self.type == ColumnType.COMPUTED:
            # Computed columns are read-only
            return False, f"Column '{self.name}' is computed and cannot be set"

        return True, None


@dataclass(frozen=True)
class TableSchema:
    """Value object representing a table's complete schema.

    Attributes:
        columns: Ordered list of column definitions
    """

    columns: tuple[ColumnDefinition, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create TableSchema from dictionary."""
        columns_data = data.get("columns", [])
        columns = tuple(ColumnDefinition.from_dict(col) for col in columns_data)
        return cls(columns=columns)

    @classmethod
    def from_list(cls, columns: list[dict[str, Any]]) -> Self:
        """Create TableSchema from a list of column dictionaries."""
        return cls(columns=tuple(ColumnDefinition.from_dict(col) for col in columns))

    def to_dict(self) -> dict[str, Any]:
        """Convert TableSchema to dictionary."""
        return {
            "columns": [col.to_dict() for col in self.columns],
        }

    def get_column(self, name: str) -> ColumnDefinition | None:
        """Get a column definition by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def has_column(self, name: str) -> bool:
        """Check if a column exists."""
        return self.get_column(name) is not None

    @property
    def column_names(self) -> list[str]:
        """Get list of column names."""
        return [col.name for col in self.columns]

    @property
    def required_columns(self) -> list[str]:
        """Get list of required column names."""
        return [col.name for col in self.columns if col.required]

    @property
    def reference_columns(self) -> list[ColumnDefinition]:
        """Get list of reference columns (for FK handling)."""
        return [col for col in self.columns if col.type == ColumnType.REFERENCE]

    def add_column(self, column: ColumnDefinition) -> "TableSchema":
        """Return new schema with added column."""
        if self.has_column(column.name):
            raise ValueError(f"Column '{column.name}' already exists")
        return TableSchema(columns=self.columns + (column,))

    def remove_column(self, name: str) -> "TableSchema":
        """Return new schema with column removed."""
        return TableSchema(
            columns=tuple(col for col in self.columns if col.name != name)
        )

    def validate_row_data(
        self, data: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate row data against schema.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: list[str] = []

        # Check required columns
        for col in self.columns:
            if col.required and col.name not in data:
                errors.append(f"Missing required column: {col.name}")

        # Validate each provided value
        for key, value in data.items():
            col = self.get_column(key)
            if col is None:
                # Unknown column - could be ignored or treated as error
                continue

            is_valid, error = col.validate_value(value)
            if not is_valid and error:
                errors.append(error)

        return len(errors) == 0, errors
