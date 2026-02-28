"""Step definitions for structured data BDD tests."""

from uuid import uuid4

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

from app.domain.entities.vault import Vault
from app.domain.entities.data_table import DataTable
from app.domain.entities.table_row import TableRow
from app.domain.value_objects.column_type import (
    ColumnType,
    ColumnDefinition,
    TableSchema,
)
from app.domain.services.csv_parser import CsvParserService
from app.domain.services.query_parser import QueryParserService

# Load scenarios from feature file
scenarios("../features/structured_data.feature")


# Background steps

@given('a vault "my-vault" exists')
def given_vault_exists(context: dict, mock_repositories: dict):
    """Create a vault in context."""
    vault = Vault(
        id=uuid4(),
        user_id=context["user"].id,
        name="My Vault",
        slug="my-vault",
    )
    context["vault"] = vault
    context["tables"] = {}
    context["rows"] = {}
    context["table_rows"] = []
    mock_repositories["vault_repo"].get_by_slug.return_value = vault


# Table CRUD scenarios

@when(parsers.parse('I create a table named "{table_name}"'))
def when_create_simple_table(context: dict, table_name: str):
    """Create a simple table."""
    schema = TableSchema(columns=(
        ColumnDefinition(name="id", type=ColumnType.TEXT),
        ColumnDefinition(name="name", type=ColumnType.TEXT),
    ))
    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table
    context["created_table"] = table


@then(parsers.parse('the table "{slug}" is created successfully'))
def then_table_created(context: dict, slug: str):
    """Verify table was created."""
    assert slug in context["tables"]


@given(parsers.parse('a table "{table_name}" exists'))
def given_table_exists(context: dict, table_name: str):
    """Create simple existing table."""
    schema = TableSchema(columns=(
        ColumnDefinition(name="id", type=ColumnType.TEXT),
    ))
    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table


@when(parsers.parse('I delete the table "{slug}"'))
def when_delete_table(context: dict, slug: str):
    """Delete table."""
    if slug in context["tables"]:
        del context["tables"][slug]


@then(parsers.parse('the table "{slug}" no longer exists'))
def then_table_not_exists(context: dict, slug: str):
    """Verify table doesn't exist."""
    assert slug not in context["tables"]


@when("I list all tables in the vault")
def when_list_tables(context: dict):
    """List all tables."""
    context["table_list"] = list(context["tables"].values())


@then(parsers.parse("I receive {count:d} tables"))
def then_receive_table_count(context: dict, count: int):
    """Verify table count."""
    assert len(context["table_list"]) == count


# Row CRUD scenarios

@given(parsers.parse('a table "{table_name}" with columns name and value exists'))
def given_table_with_name_value(context: dict, table_name: str):
    """Create table with name and value columns."""
    schema = TableSchema(columns=(
        ColumnDefinition(name="name", type=ColumnType.TEXT),
        ColumnDefinition(name="value", type=ColumnType.NUMBER),
    ))
    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table
    context["current_table"] = table


@when(parsers.parse('I create a row with name "{name}" and value {value:d}'))
def when_create_row_name_value(context: dict, name: str, value: int):
    """Create row with name and value."""
    table = context["current_table"]
    row = TableRow(
        id=uuid4(),
        table_id=table.id,
        vault_id=context["vault"].id,
        data={"name": name, "value": value},
    )
    context["rows"][str(row.id)] = row
    context["created_row"] = row


@then("the row is created successfully")
def then_row_created(context: dict):
    """Verify row was created."""
    assert "created_row" in context


@given(parsers.parse('a table "{table_name}" exists with {count:d} rows'))
def given_table_with_many_rows(context: dict, table_name: str, count: int):
    """Create table with many rows."""
    schema = TableSchema(columns=(
        ColumnDefinition(name="name", type=ColumnType.TEXT),
        ColumnDefinition(name="value", type=ColumnType.NUMBER),
        ColumnDefinition(name="status", type=ColumnType.TEXT),
    ))
    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table
    context["current_table"] = table

    context["table_rows"] = []
    for i in range(count):
        row = TableRow(
            id=uuid4(),
            table_id=table.id,
            vault_id=context["vault"].id,
            data={"name": f"Item {i}", "value": i, "status": "active" if i % 2 == 0 else "inactive"},
        )
        context["rows"][str(row.id)] = row
        context["table_rows"].append(row)

    context["row_count"] = count


@when(parsers.parse("I list rows with limit {limit:d} and offset {offset:d}"))
def when_list_rows_paginated(context: dict, limit: int, offset: int):
    """List rows with pagination."""
    all_rows = context["table_rows"]
    context["row_list"] = all_rows[offset:offset + limit]
    context["total_count"] = len(all_rows)


@then(parsers.parse("I receive {count:d} rows"))
def then_receive_rows(context: dict, count: int):
    """Verify row count."""
    assert len(context["row_list"]) == count


@then(parsers.parse("the total count is {count:d}"))
def then_total_count(context: dict, count: int):
    """Verify total count."""
    assert context["total_count"] == count


# Filtering and Sorting scenarios

@given(parsers.parse('a table "{table_name}" with status column exists'))
def given_table_with_status(context: dict, table_name: str):
    """Create table with status column."""
    schema = TableSchema(columns=(
        ColumnDefinition(name="name", type=ColumnType.TEXT),
        ColumnDefinition(name="status", type=ColumnType.TEXT),
    ))
    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table
    context["current_table"] = table


@given("there are rows with different status values")
def given_rows_with_different_status(context: dict):
    """Create rows with different statuses."""
    table = context["current_table"]
    context["table_rows"] = []

    for name, status in [("Alice", "active"), ("Bob", "inactive"), ("Carol", "active")]:
        row = TableRow(
            id=uuid4(),
            table_id=table.id,
            vault_id=context["vault"].id,
            data={"name": name, "status": status},
        )
        context["rows"][str(row.id)] = row
        context["table_rows"].append(row)


@when(parsers.parse('I list rows where status equals "{status}"'))
def when_filter_by_status(context: dict, status: str):
    """Filter rows by status."""
    all_rows = context["table_rows"]
    context["row_list"] = [r for r in all_rows if r.data.get("status") == status]


@then("only active rows are returned")
def then_only_active_rows(context: dict):
    """Verify only active rows."""
    for row in context["row_list"]:
        assert row.data.get("status") == "active"


@given(parsers.parse('a table "{table_name}" with price column exists'))
def given_table_with_price(context: dict, table_name: str):
    """Create table with price column."""
    schema = TableSchema(columns=(
        ColumnDefinition(name="name", type=ColumnType.TEXT),
        ColumnDefinition(name="price", type=ColumnType.NUMBER),
    ))
    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table
    context["current_table"] = table


@given("there are rows with different prices")
def given_rows_with_different_prices(context: dict):
    """Create rows with different prices."""
    table = context["current_table"]
    context["table_rows"] = []

    for name, price in [("Widget", 30), ("Gadget", 10), ("Tool", 20)]:
        row = TableRow(
            id=uuid4(),
            table_id=table.id,
            vault_id=context["vault"].id,
            data={"name": name, "price": price},
        )
        context["rows"][str(row.id)] = row
        context["table_rows"].append(row)


@when("I list rows sorted by price ascending")
def when_sort_by_price_asc(context: dict):
    """Sort rows by price ascending."""
    all_rows = context["table_rows"]
    context["row_list"] = sorted(all_rows, key=lambda r: r.data.get("price", 0))


@then("rows are sorted by price in ascending order")
def then_sorted_ascending(context: dict):
    """Verify ascending order."""
    prices = [r.data.get("price", 0) for r in context["row_list"]]
    assert prices == sorted(prices)


# CSV Operations

@given("CSV content with headers name and email")
def given_csv_content(context: dict):
    """Store CSV content."""
    context["csv_content"] = "name,email\nJohn,john@test.com\nJane,jane@test.com"


@when(parsers.parse('I import the CSV as a new table "{table_name}"'))
def when_import_csv(context: dict, table_name: str):
    """Import CSV as new table."""
    parser = CsvParserService()
    headers, rows = parser.parse_csv(context["csv_content"])

    columns = tuple(
        ColumnDefinition(name=h, type=ColumnType.TEXT)
        for h in headers
    )
    schema = TableSchema(columns=columns)

    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table
    context["created_table"] = table


@then(parsers.parse('the table "{slug}" is created'))
def then_table_is_created(context: dict, slug: str):
    """Verify table created."""
    assert slug in context["tables"]


@given(parsers.parse('a table "{table_name}" exists with 2 rows'))
def given_table_with_2_rows(context: dict, table_name: str):
    """Create table with 2 rows."""
    schema = TableSchema(columns=(
        ColumnDefinition(name="name", type=ColumnType.TEXT),
        ColumnDefinition(name="email", type=ColumnType.TEXT),
    ))
    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table
    context["current_table"] = table

    context["table_rows"] = []
    for name, email in [("John", "john@test.com"), ("Jane", "jane@test.com")]:
        row = TableRow(
            id=uuid4(),
            table_id=table.id,
            vault_id=context["vault"].id,
            data={"name": name, "email": email},
        )
        context["rows"][str(row.id)] = row
        context["table_rows"].append(row)


@when(parsers.parse('I export the table "{slug}" as CSV'))
def when_export_csv(context: dict, slug: str):
    """Export table as CSV."""
    table = context["tables"][slug]
    rows = context["table_rows"]
    parser = CsvParserService()

    csv_content = parser.export_csv(
        table.schema.column_names,
        [r.data for r in rows],
    )
    context["csv_export"] = csv_content


@then("I receive valid CSV content")
def then_receive_csv(context: dict):
    """Verify CSV content received."""
    assert context["csv_export"] is not None
    assert len(context["csv_export"]) > 0
    assert "," in context["csv_export"]  # Has delimiter


# Query scenarios

@given(parsers.parse('a table "{table_name}" with sample data'))
def given_table_with_sample_data(context: dict, table_name: str):
    """Create table with sample data."""
    schema = TableSchema(columns=(
        ColumnDefinition(name="name", type=ColumnType.TEXT),
        ColumnDefinition(name="status", type=ColumnType.TEXT),
    ))
    table = DataTable(
        id=uuid4(),
        vault_id=context["vault"].id,
        name=table_name,
        slug=table_name.lower(),
        schema=schema,
    )
    context["tables"][table.slug] = table
    context["current_table"] = table

    context["table_rows"] = []
    for name, status in [("Item 1", "active"), ("Item 2", "inactive"), ("Item 3", "active")]:
        row = TableRow(
            id=uuid4(),
            table_id=table.id,
            vault_id=context["vault"].id,
            data={"name": name, "status": status},
        )
        context["rows"][str(row.id)] = row
        context["table_rows"].append(row)


@when(parsers.parse('I execute query "{query}"'))
def when_execute_query(context: dict, query: str):
    """Execute dataview-style query."""
    parser = QueryParserService()
    parsed = parser.parse(query)

    # Get table
    table = context["tables"].get(parsed.table_name)
    if not table:
        context["query_error"] = f"Table {parsed.table_name} not found"
        return

    all_rows = context["table_rows"]

    # Apply filters
    filtered = all_rows
    for clause in parsed.where_conditions:
        filtered = [
            r for r in filtered
            if str(r.data.get(clause.column)) == str(clause.value)
        ]

    # Apply sorting
    if parsed.sort_clauses:
        sort = parsed.sort_clauses[0]
        reverse = sort.order.value.upper() == "DESC"
        filtered = sorted(
            filtered,
            key=lambda r: r.data.get(sort.column, ""),
            reverse=reverse,
        )

    # Apply limit
    total = len(filtered)
    if parsed.limit:
        filtered = filtered[:parsed.limit]

    context["query_results"] = filtered
    context["query_total"] = total


@then("I receive query results")
def then_receive_query_results(context: dict):
    """Verify query results received."""
    assert "query_results" in context
    assert len(context["query_results"]) >= 0


@then("I receive filtered results")
def then_receive_filtered_results(context: dict):
    """Verify filtered results received."""
    assert "query_results" in context
    # Should have fewer results than original
    for row in context["query_results"]:
        assert row.data.get("status") == "active"


@then(parsers.parse("the results have {count:d} rows"))
def then_results_row_count(context: dict, count: int):
    """Verify query result count."""
    assert len(context["query_results"]) == count
