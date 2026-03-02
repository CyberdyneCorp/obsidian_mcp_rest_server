"""Query parser service for dataview-style queries."""

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.exceptions import QueryParseError


class QueryOperator(StrEnum):
    """Comparison operators for WHERE clauses."""

    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    LIKE = "LIKE"
    IN = "IN"


class SortOrder(StrEnum):
    """Sort order direction."""

    ASC = "ASC"
    DESC = "DESC"


@dataclass
class WhereCondition:
    """A WHERE clause condition."""

    column: str
    operator: QueryOperator
    value: Any


@dataclass
class SortClause:
    """A SORT clause."""

    column: str
    order: SortOrder = SortOrder.ASC


@dataclass
class ParsedQuery:
    """Result of parsing a dataview-style query."""

    columns: list[str] = field(default_factory=list)  # Empty = SELECT *
    table_name: str = ""
    where_conditions: list[WhereCondition] = field(default_factory=list)
    sort_clauses: list[SortClause] = field(default_factory=list)
    limit: int | None = None
    offset: int | None = None


class QueryParserService:
    """Service for parsing dataview-style queries.

    Supported syntax:
        TABLE col1, col2 FROM table_name
        TABLE * FROM table_name WHERE column = 'value'
        TABLE col1, col2 FROM table_name WHERE col > 10 SORT col ASC LIMIT 10
        TABLE * FROM table_name WHERE col IN ('a', 'b', 'c')
        TABLE * FROM table_name WHERE col LIKE '%pattern%'
    """

    # Patterns
    _TABLE_PATTERN = re.compile(
        r"^\s*TABLE\s+(.+?)\s+FROM\s+(\w+)",
        re.IGNORECASE,
    )

    _WHERE_PATTERN = re.compile(
        r"\s+WHERE\s+(.+?)(?=\s+SORT|\s+LIMIT|\s+OFFSET|$)",
        re.IGNORECASE,
    )

    _SORT_PATTERN = re.compile(
        r"\s+SORT\s+(\w+)(?:\s+(ASC|DESC))?",
        re.IGNORECASE,
    )

    _LIMIT_PATTERN = re.compile(
        r"\s+LIMIT\s+(\d+)",
        re.IGNORECASE,
    )

    _OFFSET_PATTERN = re.compile(
        r"\s+OFFSET\s+(\d+)",
        re.IGNORECASE,
    )

    # Condition patterns
    _CONDITION_IN_PATTERN = re.compile(
        r"(\w+)\s+IN\s*\(([^)]+)\)",
        re.IGNORECASE,
    )

    _CONDITION_LIKE_PATTERN = re.compile(
        r"(\w+)\s+LIKE\s+['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    )

    _CONDITION_COMPARISON_PATTERN = re.compile(
        r"(\w+)\s*(=|!=|>=|<=|>|<)\s*(?:['\"]([^'\"]+)['\"]|(\d+(?:\.\d+)?)|(\w+))",
    )

    def parse(self, query: str) -> ParsedQuery:
        """Parse a dataview-style query string.

        Args:
            query: The query string

        Returns:
            ParsedQuery object

        Raises:
            QueryParseError: If query syntax is invalid
        """
        query = query.strip()

        # Parse TABLE ... FROM ...
        table_match = self._TABLE_PATTERN.match(query)
        if not table_match:
            raise QueryParseError(query, "Query must start with 'TABLE ... FROM ...'")

        columns_str = table_match.group(1).strip()
        table_name = table_match.group(2).strip()

        # Parse columns
        columns = [] if columns_str == "*" else [c.strip() for c in columns_str.split(",")]

        # Parse WHERE clause
        where_conditions = []
        where_match = self._WHERE_PATTERN.search(query)
        if where_match:
            where_str = where_match.group(1).strip()
            where_conditions = self._parse_where(where_str, query)

        # Parse SORT clause
        sort_clauses = []
        sort_match = self._SORT_PATTERN.search(query)
        if sort_match:
            column = sort_match.group(1)
            order_str = sort_match.group(2)
            order = SortOrder.DESC if order_str and order_str.upper() == "DESC" else SortOrder.ASC
            sort_clauses.append(SortClause(column=column, order=order))

        # Parse LIMIT
        limit = None
        limit_match = self._LIMIT_PATTERN.search(query)
        if limit_match:
            limit = int(limit_match.group(1))

        # Parse OFFSET
        offset = None
        offset_match = self._OFFSET_PATTERN.search(query)
        if offset_match:
            offset = int(offset_match.group(1))

        return ParsedQuery(
            columns=columns,
            table_name=table_name,
            where_conditions=where_conditions,
            sort_clauses=sort_clauses,
            limit=limit,
            offset=offset,
        )

    def _parse_where(self, where_str: str, full_query: str) -> list[WhereCondition]:
        """Parse WHERE clause conditions.

        Currently supports:
        - column = 'value'
        - column != 'value'
        - column > 10
        - column < 10
        - column >= 10
        - column <= 10
        - column LIKE '%pattern%'
        - column IN ('a', 'b', 'c')
        - AND to combine conditions

        Returns:
            List of WhereCondition objects
        """
        conditions = []

        # Split by AND (case-insensitive)
        parts = re.split(r"\s+AND\s+", where_str, flags=re.IGNORECASE)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            condition = self._parse_condition(part, full_query)
            if condition:
                conditions.append(condition)

        return conditions

    def _parse_condition(self, condition_str: str, full_query: str) -> WhereCondition | None:
        """Parse a single condition."""
        condition_str = condition_str.strip()

        # Try IN pattern
        in_match = self._CONDITION_IN_PATTERN.match(condition_str)
        if in_match:
            column = in_match.group(1)
            values_str = in_match.group(2)
            # Parse comma-separated values
            values = []
            for v in values_str.split(","):
                v = v.strip().strip("'\"")
                values.append(self._convert_value(v))
            return WhereCondition(
                column=column,
                operator=QueryOperator.IN,
                value=values,
            )

        # Try LIKE pattern
        like_match = self._CONDITION_LIKE_PATTERN.match(condition_str)
        if like_match:
            column = like_match.group(1)
            pattern = like_match.group(2)
            return WhereCondition(
                column=column,
                operator=QueryOperator.LIKE,
                value=pattern,
            )

        # Try comparison operators
        comp_match = self._CONDITION_COMPARISON_PATTERN.match(condition_str)
        if comp_match:
            column = comp_match.group(1)
            op_str = comp_match.group(2)
            # Value can be in group 3 (quoted), 4 (number), or 5 (unquoted word)
            value = comp_match.group(3) or comp_match.group(4) or comp_match.group(5)

            # Map operator
            op_map = {
                "=": QueryOperator.EQ,
                "!=": QueryOperator.NE,
                ">": QueryOperator.GT,
                ">=": QueryOperator.GTE,
                "<": QueryOperator.LT,
                "<=": QueryOperator.LTE,
            }
            operator = op_map.get(op_str, QueryOperator.EQ)

            return WhereCondition(
                column=column,
                operator=operator,
                value=self._convert_value(value),
            )

        raise QueryParseError(full_query, f"Invalid condition: {condition_str}")

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type."""
        # Try boolean
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Keep as string
        return value

    def to_filter_dict(self, query: ParsedQuery) -> dict[str, Any]:
        """Convert parsed query to repository filter dict.

        Returns:
            Dictionary suitable for row repository filtering
        """
        filters = {}

        for condition in query.where_conditions:
            if condition.operator == QueryOperator.EQ:
                filters[condition.column] = condition.value
            elif condition.operator == QueryOperator.NE:
                filters[condition.column] = {"ne": condition.value}
            elif condition.operator == QueryOperator.GT:
                filters[condition.column] = {"gt": condition.value}
            elif condition.operator == QueryOperator.GTE:
                filters[condition.column] = {"gte": condition.value}
            elif condition.operator == QueryOperator.LT:
                filters[condition.column] = {"lt": condition.value}
            elif condition.operator == QueryOperator.LTE:
                filters[condition.column] = {"lte": condition.value}
            elif condition.operator == QueryOperator.LIKE:
                filters[condition.column] = {"like": condition.value}
            elif condition.operator == QueryOperator.IN:
                filters[condition.column] = {"in": condition.value}

        return filters
