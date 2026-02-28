Feature: Structured Data Tables
  As a user
  I want to create and manage structured data tables
  So that I can organize tabular data within my vault

  Background:
    Given a registered user exists
    And the user is authenticated
    And a vault "my-vault" exists

  # Table CRUD Operations

  Scenario: Create a simple table
    When I create a table named "Contacts"
    Then the table "contacts" is created successfully

  Scenario: Delete a table
    Given a table "ToDelete" exists
    When I delete the table "todelete"
    Then the table "todelete" no longer exists

  Scenario: List tables in vault
    Given a table "Contacts" exists
    And a table "Products" exists
    And a table "Orders" exists
    When I list all tables in the vault
    Then I receive 3 tables

  # Row Operations

  Scenario: Create a row in table
    Given a table "Items" with columns name and value exists
    When I create a row with name "Widget" and value 100
    Then the row is created successfully

  Scenario: List rows with pagination
    Given a table "Items" exists with 50 rows
    When I list rows with limit 10 and offset 0
    Then I receive 10 rows
    And the total count is 50

  # Filtering and Sorting

  Scenario: Filter rows by status
    Given a table "Contacts" with status column exists
    And there are rows with different status values
    When I list rows where status equals "active"
    Then only active rows are returned

  Scenario: Sort rows by price ascending
    Given a table "Products" with price column exists
    And there are rows with different prices
    When I list rows sorted by price ascending
    Then rows are sorted by price in ascending order

  # CSV Operations

  Scenario: Import CSV creates table
    Given CSV content with headers name and email
    When I import the CSV as a new table "imported_contacts"
    Then the table "imported_contacts" is created

  Scenario: Export table to CSV
    Given a table "Contacts" exists with 2 rows
    When I export the table "contacts" as CSV
    Then I receive valid CSV content

  # Query Language

  Scenario: Execute simple query
    Given a table "Items" with sample data
    When I execute query "TABLE * FROM items"
    Then I receive query results

  Scenario: Execute query with filter
    Given a table "Items" with sample data
    When I execute query "TABLE * FROM items WHERE status = 'active'"
    Then I receive filtered results

  Scenario: Execute query with limit
    Given a table "Items" exists with 100 rows
    When I execute query "TABLE * FROM items LIMIT 10"
    Then the results have 10 rows
