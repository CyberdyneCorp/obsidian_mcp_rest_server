"""Tests for QueryParserService."""

import pytest

from app.domain.services.query_parser import (
    QueryParserService,
    SortOrder,
    QueryOperator,
    ParsedQuery,
)
from app.domain.exceptions import QueryParseError


class TestQueryParserService:
    """Tests for QueryParserService."""

    @pytest.fixture
    def parser(self):
        """Create query parser instance."""
        return QueryParserService()

    # Basic SELECT tests

    def test_parse_simple_select_all(self, parser):
        """Test parsing simple SELECT * query."""
        result = parser.parse("TABLE * FROM contacts")

        assert result.table_name == "contacts"
        assert result.columns == []  # Empty means all columns

    def test_parse_select_specific_columns(self, parser):
        """Test parsing SELECT with specific columns."""
        result = parser.parse("TABLE name, email, phone FROM contacts")

        assert result.table_name == "contacts"
        assert result.columns == ["name", "email", "phone"]

    def test_parse_case_insensitive(self, parser):
        """Test query parsing is case insensitive for keywords."""
        result = parser.parse("table Name, Email from Contacts")

        assert result.table_name == "Contacts"
        assert "Name" in result.columns
        assert "Email" in result.columns

    # WHERE clause tests

    def test_parse_where_equals(self, parser):
        """Test parsing WHERE with equals condition."""
        result = parser.parse("TABLE * FROM contacts WHERE status = 'active'")

        assert len(result.where_conditions) == 1
        assert result.where_conditions[0].column == "status"
        assert result.where_conditions[0].operator == QueryOperator.EQ
        assert result.where_conditions[0].value == "active"

    def test_parse_where_not_equals(self, parser):
        """Test parsing WHERE with not equals condition."""
        result = parser.parse("TABLE * FROM contacts WHERE status != 'deleted'")

        assert result.where_conditions[0].operator == QueryOperator.NE
        assert result.where_conditions[0].value == "deleted"

    def test_parse_where_greater_than(self, parser):
        """Test parsing WHERE with greater than condition."""
        result = parser.parse("TABLE * FROM products WHERE price > 100")

        assert result.where_conditions[0].column == "price"
        assert result.where_conditions[0].operator == QueryOperator.GT
        assert result.where_conditions[0].value == 100  # Converted to int

    def test_parse_where_less_than(self, parser):
        """Test parsing WHERE with less than condition."""
        result = parser.parse("TABLE * FROM products WHERE quantity < 10")

        assert result.where_conditions[0].operator == QueryOperator.LT

    def test_parse_where_greater_equals(self, parser):
        """Test parsing WHERE with >= condition."""
        result = parser.parse("TABLE * FROM items WHERE count >= 5")

        assert result.where_conditions[0].operator == QueryOperator.GTE

    def test_parse_where_less_equals(self, parser):
        """Test parsing WHERE with <= condition."""
        result = parser.parse("TABLE * FROM items WHERE count <= 100")

        assert result.where_conditions[0].operator == QueryOperator.LTE

    def test_parse_where_like(self, parser):
        """Test parsing WHERE with LIKE condition."""
        result = parser.parse("TABLE * FROM contacts WHERE name LIKE 'John%'")

        assert result.where_conditions[0].operator == QueryOperator.LIKE
        assert result.where_conditions[0].value == "John%"

    def test_parse_where_in(self, parser):
        """Test parsing WHERE with IN condition."""
        result = parser.parse(
            "TABLE * FROM contacts WHERE status IN ('active', 'pending')"
        )

        assert result.where_conditions[0].operator == QueryOperator.IN
        assert result.where_conditions[0].value == ["active", "pending"]

    def test_parse_multiple_where_conditions(self, parser):
        """Test parsing multiple WHERE conditions with AND."""
        result = parser.parse(
            "TABLE * FROM contacts WHERE status = 'active' AND age > 21"
        )

        assert len(result.where_conditions) == 2
        assert result.where_conditions[0].column == "status"
        assert result.where_conditions[1].column == "age"

    def test_parse_where_with_numeric_value(self, parser):
        """Test parsing WHERE with numeric value."""
        result = parser.parse("TABLE * FROM products WHERE price = 99")

        assert result.where_conditions[0].value == 99

    # SORT clause tests

    def test_parse_sort_ascending(self, parser):
        """Test parsing SORT ascending."""
        result = parser.parse("TABLE * FROM contacts SORT name ASC")

        assert len(result.sort_clauses) == 1
        assert result.sort_clauses[0].column == "name"
        assert result.sort_clauses[0].order == SortOrder.ASC

    def test_parse_sort_descending(self, parser):
        """Test parsing SORT descending."""
        result = parser.parse("TABLE * FROM contacts SORT created_at DESC")

        assert result.sort_clauses[0].column == "created_at"
        assert result.sort_clauses[0].order == SortOrder.DESC

    def test_parse_sort_default_ascending(self, parser):
        """Test SORT defaults to ascending."""
        result = parser.parse("TABLE * FROM contacts SORT name")

        assert result.sort_clauses[0].order == SortOrder.ASC

    # LIMIT and OFFSET tests

    def test_parse_limit(self, parser):
        """Test parsing LIMIT clause."""
        result = parser.parse("TABLE * FROM contacts LIMIT 10")

        assert result.limit == 10

    def test_parse_offset(self, parser):
        """Test parsing OFFSET clause."""
        result = parser.parse("TABLE * FROM contacts OFFSET 20")

        assert result.offset == 20

    def test_parse_limit_and_offset(self, parser):
        """Test parsing both LIMIT and OFFSET."""
        result = parser.parse("TABLE * FROM contacts LIMIT 10 OFFSET 20")

        assert result.limit == 10
        assert result.offset == 20

    # Complex query tests

    def test_parse_full_query(self, parser):
        """Test parsing a full complex query."""
        query = """
        TABLE name, email, status
        FROM contacts
        WHERE status = 'active' AND age > 18
        SORT name ASC
        LIMIT 50
        OFFSET 0
        """
        result = parser.parse(query)

        assert result.table_name == "contacts"
        assert result.columns == ["name", "email", "status"]
        assert len(result.where_conditions) == 2
        assert result.sort_clauses[0].column == "name"
        assert result.limit == 50
        assert result.offset == 0

    # to_filter_dict tests

    def test_to_filter_dict_simple(self, parser):
        """Test converting parsed query to filter dict."""
        result = parser.parse("TABLE * FROM contacts WHERE status = 'active'")
        filters = parser.to_filter_dict(result)

        assert filters == {"status": "active"}

    def test_to_filter_dict_multiple_conditions(self, parser):
        """Test filter dict with multiple conditions."""
        result = parser.parse(
            "TABLE * FROM contacts WHERE status = 'active' AND type = 'customer'"
        )
        filters = parser.to_filter_dict(result)

        assert filters["status"] == "active"
        assert filters["type"] == "customer"

    def test_to_filter_dict_operators(self, parser):
        """Test filter dict preserves operators."""
        result = parser.parse("TABLE * FROM products WHERE price > 100")
        filters = parser.to_filter_dict(result)

        # Implementation uses nested dict for non-EQ operators
        assert "price" in filters
        assert filters["price"] == {"gt": 100}

    def test_to_filter_dict_like(self, parser):
        """Test filter dict for LIKE operator."""
        result = parser.parse("TABLE * FROM contacts WHERE name LIKE 'John%'")
        filters = parser.to_filter_dict(result)

        assert filters["name"] == {"like": "John%"}

    def test_to_filter_dict_in(self, parser):
        """Test filter dict for IN operator."""
        result = parser.parse(
            "TABLE * FROM contacts WHERE status IN ('a', 'b')"
        )
        filters = parser.to_filter_dict(result)

        assert filters["status"] == {"in": ["a", "b"]}

    # Error handling tests

    def test_parse_missing_table_name(self, parser):
        """Test parsing query without FROM raises error."""
        with pytest.raises(QueryParseError):
            parser.parse("TABLE *")

    def test_parse_empty_query(self, parser):
        """Test parsing empty query raises error."""
        with pytest.raises(QueryParseError):
            parser.parse("")

    def test_parse_invalid_syntax(self, parser):
        """Test parsing invalid syntax raises error."""
        with pytest.raises(QueryParseError):
            parser.parse("SELECT * FROM contacts")  # SELECT not TABLE

    # Edge cases

    def test_parse_table_name_with_underscore(self, parser):
        """Test parsing table name with underscore."""
        result = parser.parse("TABLE * FROM user_contacts")

        assert result.table_name == "user_contacts"

    def test_parse_column_name_with_underscore(self, parser):
        """Test parsing column names with underscores."""
        result = parser.parse("TABLE first_name, last_name FROM contacts")

        assert "first_name" in result.columns
        assert "last_name" in result.columns

    def test_parse_where_value_with_spaces(self, parser):
        """Test parsing WHERE with quoted value containing spaces."""
        result = parser.parse("TABLE * FROM contacts WHERE name = 'John Doe'")

        assert result.where_conditions[0].value == "John Doe"

    def test_parse_single_quotes(self, parser):
        """Test single quotes work."""
        result = parser.parse("TABLE * FROM t WHERE x = 'value'")

        assert result.where_conditions[0].value == "value"

    def test_parse_double_quotes(self, parser):
        """Test double quotes work."""
        result = parser.parse('TABLE * FROM t WHERE x = "value"')

        assert result.where_conditions[0].value == "value"

    def test_parse_boolean_values(self, parser):
        """Test boolean values are converted."""
        result = parser.parse("TABLE * FROM t WHERE active = true")

        assert result.where_conditions[0].value is True

    def test_parse_float_values(self, parser):
        """Test float values are converted."""
        result = parser.parse("TABLE * FROM t WHERE price = 99.99")

        assert result.where_conditions[0].value == 99.99
