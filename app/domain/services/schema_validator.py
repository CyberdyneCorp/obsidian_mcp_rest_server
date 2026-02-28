"""Schema validator service for row data validation."""

from typing import Any
from uuid import UUID

from app.domain.entities.data_table import DataTable
from app.domain.services.formula_evaluator import FormulaEvaluatorService
from app.domain.value_objects.column_type import ColumnType


class SchemaValidatorService:
    """Service for validating and transforming row data against table schema.

    Handles:
    - Type validation
    - Required field checking
    - Default value application
    - Computed column evaluation
    - Reference validation (basic)
    """

    def __init__(self) -> None:
        self.formula_evaluator = FormulaEvaluatorService()

    def validate_and_transform(
        self,
        table: DataTable,
        data: dict[str, Any],
        is_update: bool = False,
    ) -> tuple[dict[str, Any], list[str]]:
        """Validate and transform row data.

        Args:
            table: The table definition
            data: Row data to validate
            is_update: If True, required fields are optional (for partial updates)

        Returns:
            Tuple of (transformed_data, error_messages)
        """
        errors: list[str] = []
        transformed = dict(data)

        for column in table.schema.columns:
            col_name = column.name

            # Skip computed columns - they'll be calculated
            if column.type == ColumnType.COMPUTED:
                continue

            # Check if value is provided
            if col_name not in data or data[col_name] is None:
                # Apply default if available
                if column.default is not None:
                    transformed[col_name] = column.default
                elif column.required and not is_update:
                    errors.append(f"Required column '{col_name}' is missing")
                continue

            # Validate the value
            value = data[col_name]
            is_valid, error = column.validate_value(value)
            if not is_valid and error:
                errors.append(error)
            else:
                # Type coercion if needed
                transformed[col_name] = self._coerce_value(value, column.type)

        # Evaluate computed columns after all other columns are processed
        for column in table.schema.columns:
            if column.type == ColumnType.COMPUTED and column.formula:
                try:
                    computed_value = self.formula_evaluator.evaluate(
                        column.formula,
                        transformed,
                    )
                    transformed[column.name] = computed_value
                except Exception as e:
                    errors.append(f"Error evaluating computed column '{column.name}': {e}")

        return transformed, errors

    def _coerce_value(self, value: Any, column_type: ColumnType) -> Any:
        """Coerce a value to the expected type."""
        if value is None:
            return None

        if column_type == ColumnType.NUMBER:
            if isinstance(value, str):
                try:
                    if "." in value:
                        return float(value)
                    return int(value)
                except ValueError:
                    return value
            return value

        if column_type == ColumnType.BOOLEAN:
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1")
            return bool(value)

        return value

    def check_unique_constraints(
        self,
        table: DataTable,
        data: dict[str, Any],
        existing_values: dict[str, set[Any]],
        exclude_row_id: UUID | None = None,
    ) -> list[str]:
        """Check unique constraints.

        Args:
            table: The table definition
            data: Row data to check
            existing_values: Dict of column_name -> set of existing values
            exclude_row_id: Row ID to exclude (for updates)

        Returns:
            List of error messages
        """
        errors: list[str] = []

        for column in table.schema.columns:
            if column.unique and column.name in data:
                value = data[column.name]
                if value is not None:
                    existing = existing_values.get(column.name, set())
                    if value in existing:
                        errors.append(
                            f"Value '{value}' already exists in unique column '{column.name}'"
                        )

        return errors
