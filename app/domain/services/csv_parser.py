"""CSV parsing service with type inference."""

import csv
import io
import re
from typing import Any

from app.domain.exceptions import CsvParseError
from app.domain.value_objects.column_type import ColumnType


class CsvParserService:
    """Service for parsing CSV files and inferring column types."""

    # Patterns for type detection
    UUID_PATTERN = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
    INT_PATTERN = re.compile(r"^-?\d+$")
    FLOAT_PATTERN = re.compile(r"^-?\d+\.?\d*$")
    BOOL_VALUES = {"true", "false", "yes", "no", "1", "0"}

    def parse_csv(
        self,
        content: str | bytes,
        delimiter: str = ",",
        has_header: bool = True,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Parse CSV content into headers and rows.

        Args:
            content: CSV content as string or bytes
            delimiter: Column delimiter
            has_header: Whether first row is header

        Returns:
            Tuple of (column names, list of row dicts)

        Raises:
            CsvParseError: If CSV parsing fails
        """
        if isinstance(content, bytes):
            raw_content = content
            try:
                content = raw_content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    content = raw_content.decode("latin-1")
                except UnicodeDecodeError as e:
                    raise CsvParseError(f"Unable to decode CSV: {e}") from e

        try:
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            rows_raw = list(reader)
        except csv.Error as e:
            raise CsvParseError(str(e)) from e

        if not rows_raw:
            return [], []

        if has_header:
            headers = rows_raw[0]
            data_rows = rows_raw[1:]
        else:
            # Generate column names
            num_cols = len(rows_raw[0]) if rows_raw else 0
            headers = [f"column_{i+1}" for i in range(num_cols)]
            data_rows = rows_raw

        # Sanitize headers
        headers = [self._sanitize_column_name(h) for h in headers]

        # Convert to list of dicts
        rows = []
        for i, row in enumerate(data_rows):
            if len(row) != len(headers):
                raise CsvParseError(
                    f"Row {i+2} has {len(row)} columns, expected {len(headers)}",
                    line=i + 2,
                )
            row_dict = {}
            for j, value in enumerate(row):
                row_dict[headers[j]] = self._convert_value(value)
            rows.append(row_dict)

        return headers, rows

    def infer_column_types(
        self,
        headers: list[str],
        rows: list[dict[str, Any]],
        sample_size: int = 100,
    ) -> list[dict[str, Any]]:
        """Infer column types from data.

        Args:
            headers: Column names
            rows: Row data
            sample_size: Number of rows to sample for type inference

        Returns:
            List of column definitions
        """
        sample = rows[:sample_size]
        column_defs = []

        for header in headers:
            values = [row.get(header) for row in sample if row.get(header) is not None]

            if not values:
                # No data, default to text
                column_defs.append({
                    "name": header,
                    "type": ColumnType.TEXT.value,
                })
                continue

            inferred_type = self._infer_type(values)
            column_defs.append({
                "name": header,
                "type": inferred_type.value,
            })

        return column_defs

    def export_csv(
        self,
        columns: list[str],
        rows: list[dict[str, Any]],
        delimiter: str = ",",
    ) -> str:
        """Export data to CSV format.

        Args:
            columns: Column names (in order)
            rows: Row data
            delimiter: Column delimiter

        Returns:
            CSV content as string
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)

        # Write header
        writer.writerow(columns)

        # Write data rows
        for row in rows:
            values = [self._format_value(row.get(col)) for col in columns]
            writer.writerow(values)

        return output.getvalue()

    def _sanitize_column_name(self, name: str) -> str:
        """Sanitize column name to be a valid identifier."""
        # Remove leading/trailing whitespace
        name = name.strip()

        # Replace spaces and special chars with underscore
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Remove consecutive underscores
        name = re.sub(r"_+", "_", name)

        # Remove leading/trailing underscores
        name = name.strip("_")

        # Ensure starts with letter
        if name and not name[0].isalpha():
            name = "col_" + name

        return name.lower() or "column"

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate Python type."""
        if not value:
            return None

        value = value.strip()

        # Boolean
        if value.lower() in ("true", "yes"):
            return True
        if value.lower() in ("false", "no"):
            return False

        # Integer
        if self.INT_PATTERN.match(value):
            try:
                return int(value)
            except ValueError:
                pass

        # Float
        if self.FLOAT_PATTERN.match(value) and "." in value:
            try:
                return float(value)
            except ValueError:
                pass

        # Keep as string
        return value

    def _infer_type(self, values: list[Any]) -> ColumnType:
        """Infer column type from a list of values."""
        # Check for boolean
        str_values = [str(v).lower() for v in values]
        if all(v in self.BOOL_VALUES for v in str_values):
            return ColumnType.BOOLEAN

        # Check for datetime (before date to catch full timestamps)
        if all(self.DATETIME_PATTERN.match(str(v)) for v in values):
            return ColumnType.DATETIME

        # Check for date
        if all(self.DATE_PATTERN.match(str(v)) for v in values):
            return ColumnType.DATE

        # Check for UUID
        if all(self.UUID_PATTERN.match(str(v)) for v in values):
            return ColumnType.TEXT  # UUIDs stored as text

        # Check for number
        numeric_values = []
        for v in values:
            if isinstance(v, (int, float)):
                numeric_values.append(v)
            elif isinstance(v, str) and self.FLOAT_PATTERN.match(v):
                try:
                    numeric_values.append(float(v))
                except ValueError:
                    break
            else:
                break
        else:
            if len(numeric_values) == len(values):
                return ColumnType.NUMBER

        # Default to text
        return ColumnType.TEXT

    def _format_value(self, value: Any) -> str:
        """Format a value for CSV export."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (dict, list)):
            import json
            return json.dumps(value)
        return str(value)
