"""Tests for column type value objects."""

import pytest
from datetime import date, datetime
from uuid import uuid4

from app.domain.value_objects.column_type import (
    ColumnType,
    ColumnDefinition,
    TableSchema,
)


class TestColumnType:
    """Tests for ColumnType enum."""

    def test_all_column_types_exist(self):
        """Test all expected column types are defined."""
        assert ColumnType.TEXT == "text"
        assert ColumnType.NUMBER == "number"
        assert ColumnType.BOOLEAN == "boolean"
        assert ColumnType.DATE == "date"
        assert ColumnType.DATETIME == "datetime"
        assert ColumnType.JSON == "json"
        assert ColumnType.ARRAY == "array"
        assert ColumnType.REFERENCE == "reference"
        assert ColumnType.DOCUMENT == "document"
        assert ColumnType.COMPUTED == "computed"
        assert ColumnType.RICHTEXT == "richtext"

    def test_column_type_from_string(self):
        """Test creating ColumnType from string."""
        assert ColumnType("text") == ColumnType.TEXT
        assert ColumnType("number") == ColumnType.NUMBER
        assert ColumnType("boolean") == ColumnType.BOOLEAN

    def test_invalid_column_type_raises(self):
        """Test invalid column type raises ValueError."""
        with pytest.raises(ValueError):
            ColumnType("invalid_type")


class TestColumnDefinition:
    """Tests for ColumnDefinition value object."""

    def test_create_simple_column(self):
        """Test creating a simple text column."""
        col = ColumnDefinition(
            name="title",
            type=ColumnType.TEXT,
        )

        assert col.name == "title"
        assert col.type == ColumnType.TEXT
        assert col.required is False
        assert col.unique is False
        assert col.default is None

    def test_create_required_column(self):
        """Test creating a required column."""
        col = ColumnDefinition(
            name="email",
            type=ColumnType.TEXT,
            required=True,
        )

        assert col.required is True

    def test_create_unique_column(self):
        """Test creating a unique column."""
        col = ColumnDefinition(
            name="username",
            type=ColumnType.TEXT,
            unique=True,
        )

        assert col.unique is True

    def test_create_column_with_default(self):
        """Test creating a column with default value."""
        col = ColumnDefinition(
            name="status",
            type=ColumnType.TEXT,
            default="active",
        )

        assert col.default == "active"

    def test_create_reference_column(self):
        """Test creating a reference column."""
        col = ColumnDefinition(
            name="category_id",
            type=ColumnType.REFERENCE,
            reference_table="categories",
        )

        assert col.type == ColumnType.REFERENCE
        assert col.reference_table == "categories"

    def test_create_computed_column(self):
        """Test creating a computed column."""
        col = ColumnDefinition(
            name="full_name",
            type=ColumnType.COMPUTED,
            formula="CONCAT({first_name}, ' ', {last_name})",
        )

        assert col.type == ColumnType.COMPUTED
        assert col.formula == "CONCAT({first_name}, ' ', {last_name})"

    def test_create_array_column(self):
        """Test creating an array column."""
        col = ColumnDefinition(
            name="tags",
            type=ColumnType.ARRAY,
            array_type=ColumnType.TEXT,
        )

        assert col.type == ColumnType.ARRAY
        assert col.array_type == ColumnType.TEXT

    def test_validate_text_value(self):
        """Test validating text values."""
        col = ColumnDefinition(name="name", type=ColumnType.TEXT)

        is_valid, error = col.validate_value("Hello World")
        assert is_valid is True
        assert error is None

        # Numbers are NOT valid for text columns (strict validation)
        is_valid, error = col.validate_value(123)
        assert is_valid is False

    def test_validate_number_value(self):
        """Test validating number values."""
        col = ColumnDefinition(name="age", type=ColumnType.NUMBER)

        is_valid, error = col.validate_value(25)
        assert is_valid is True

        is_valid, error = col.validate_value(3.14)
        assert is_valid is True

        # String numbers are NOT valid (strict validation)
        is_valid, error = col.validate_value("42")
        assert is_valid is False

        is_valid, error = col.validate_value("not a number")
        assert is_valid is False
        assert error is not None

    def test_validate_boolean_value(self):
        """Test validating boolean values."""
        col = ColumnDefinition(name="active", type=ColumnType.BOOLEAN)

        is_valid, error = col.validate_value(True)
        assert is_valid is True

        is_valid, error = col.validate_value(False)
        assert is_valid is True

        # String booleans are NOT valid (strict validation)
        is_valid, error = col.validate_value("true")
        assert is_valid is False

    def test_validate_date_value(self):
        """Test validating date values."""
        col = ColumnDefinition(name="birthday", type=ColumnType.DATE)

        is_valid, error = col.validate_value("2024-01-15")
        assert is_valid is True

        is_valid, error = col.validate_value("invalid-date")
        assert is_valid is False

    def test_validate_datetime_value(self):
        """Test validating datetime values."""
        col = ColumnDefinition(name="created_at", type=ColumnType.DATETIME)

        is_valid, error = col.validate_value("2024-01-15T10:30:00")
        assert is_valid is True

        is_valid, error = col.validate_value("2024-01-15T10:30:00Z")
        assert is_valid is True

    def test_validate_json_value(self):
        """Test validating JSON values."""
        col = ColumnDefinition(name="metadata", type=ColumnType.JSON)

        is_valid, error = col.validate_value({"key": "value"})
        assert is_valid is True

        is_valid, error = col.validate_value([1, 2, 3])
        assert is_valid is True

    def test_validate_array_value(self):
        """Test validating array values."""
        col = ColumnDefinition(
            name="tags", type=ColumnType.ARRAY, array_type=ColumnType.TEXT
        )

        is_valid, error = col.validate_value(["a", "b", "c"])
        assert is_valid is True

        is_valid, error = col.validate_value("not an array")
        assert is_valid is False

    def test_to_dict(self):
        """Test converting column to dictionary."""
        col = ColumnDefinition(
            name="email",
            type=ColumnType.TEXT,
            required=True,
            unique=True,
            description="User email address",
        )

        data = col.to_dict()

        assert data["name"] == "email"
        assert data["type"] == "text"
        assert data["required"] is True
        assert data["unique"] is True
        assert data["description"] == "User email address"

    def test_from_dict(self):
        """Test creating column from dictionary."""
        data = {
            "name": "status",
            "type": "text",
            "required": True,
            "default": "pending",
        }

        col = ColumnDefinition.from_dict(data)

        assert col.name == "status"
        assert col.type == ColumnType.TEXT
        assert col.required is True
        assert col.default == "pending"


class TestTableSchema:
    """Tests for TableSchema value object."""

    def test_create_empty_schema(self):
        """Test creating an empty schema."""
        schema = TableSchema(columns=())

        assert len(schema.columns) == 0
        assert schema.column_names == []

    def test_create_schema_with_columns(self):
        """Test creating a schema with columns."""
        columns = (
            ColumnDefinition(name="id", type=ColumnType.TEXT, required=True),
            ColumnDefinition(name="name", type=ColumnType.TEXT),
            ColumnDefinition(name="age", type=ColumnType.NUMBER),
        )

        schema = TableSchema(columns=columns)

        assert len(schema.columns) == 3
        assert schema.column_names == ["id", "name", "age"]

    def test_get_column_by_name(self):
        """Test getting a column by name."""
        columns = (
            ColumnDefinition(name="id", type=ColumnType.TEXT),
            ColumnDefinition(name="name", type=ColumnType.TEXT),
        )
        schema = TableSchema(columns=columns)

        col = schema.get_column("name")
        assert col is not None
        assert col.name == "name"

        col = schema.get_column("nonexistent")
        assert col is None

    def test_has_column(self):
        """Test checking if column exists."""
        schema = TableSchema(columns=(
            ColumnDefinition(name="id", type=ColumnType.TEXT),
        ))

        assert schema.has_column("id") is True
        assert schema.has_column("nonexistent") is False

    def test_required_columns(self):
        """Test getting required column names."""
        schema = TableSchema(columns=(
            ColumnDefinition(name="id", type=ColumnType.TEXT, required=True),
            ColumnDefinition(name="name", type=ColumnType.TEXT, required=True),
            ColumnDefinition(name="optional", type=ColumnType.TEXT),
        ))

        required = schema.required_columns
        assert len(required) == 2
        # required_columns returns column names, not ColumnDefinition objects
        assert "id" in required
        assert "name" in required
        assert "optional" not in required

    def test_reference_columns(self):
        """Test getting reference columns."""
        schema = TableSchema(columns=(
            ColumnDefinition(name="id", type=ColumnType.TEXT),
            ColumnDefinition(
                name="category_id",
                type=ColumnType.REFERENCE,
                reference_table="categories",
            ),
            ColumnDefinition(name="name", type=ColumnType.TEXT),
        ))

        refs = schema.reference_columns
        assert len(refs) == 1
        assert refs[0].name == "category_id"

    def test_get_computed_columns_manually(self):
        """Test finding computed columns by filtering."""
        schema = TableSchema(columns=(
            ColumnDefinition(name="first", type=ColumnType.TEXT),
            ColumnDefinition(name="last", type=ColumnType.TEXT),
            ColumnDefinition(
                name="full",
                type=ColumnType.COMPUTED,
                formula="CONCAT({first}, ' ', {last})",
            ),
        ))

        computed = [c for c in schema.columns if c.type == ColumnType.COMPUTED]
        assert len(computed) == 1
        assert computed[0].name == "full"

    def test_add_column(self):
        """Test adding a column to schema."""
        schema = TableSchema(columns=(
            ColumnDefinition(name="id", type=ColumnType.TEXT),
        ))

        new_col = ColumnDefinition(name="name", type=ColumnType.TEXT)
        new_schema = schema.add_column(new_col)

        assert len(schema.columns) == 1  # Original unchanged
        assert len(new_schema.columns) == 2
        assert new_schema.has_column("name")

    def test_remove_column(self):
        """Test removing a column from schema."""
        schema = TableSchema(columns=(
            ColumnDefinition(name="id", type=ColumnType.TEXT),
            ColumnDefinition(name="name", type=ColumnType.TEXT),
        ))

        new_schema = schema.remove_column("name")

        assert len(schema.columns) == 2  # Original unchanged
        assert len(new_schema.columns) == 1
        assert not new_schema.has_column("name")

    def test_to_dict(self):
        """Test converting schema to dictionary."""
        schema = TableSchema(columns=(
            ColumnDefinition(name="id", type=ColumnType.TEXT, required=True),
            ColumnDefinition(name="value", type=ColumnType.NUMBER),
        ))

        data = schema.to_dict()

        assert "columns" in data
        assert len(data["columns"]) == 2
        assert data["columns"][0]["name"] == "id"

    def test_from_dict(self):
        """Test creating schema from dictionary."""
        data = {
            "columns": [
                {"name": "id", "type": "text", "required": True},
                {"name": "count", "type": "number"},
            ]
        }

        schema = TableSchema.from_dict(data)

        assert len(schema.columns) == 2
        assert schema.columns[0].name == "id"
        assert schema.columns[0].required is True
        assert schema.columns[1].type == ColumnType.NUMBER
