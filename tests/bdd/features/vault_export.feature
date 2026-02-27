Feature: Vault Export
  As a user
  I want to export my vault as a ZIP file
  So that I can backup or migrate my notes

  Background:
    Given a registered user exists
    And the user is authenticated

  Scenario: Export vault as ZIP file
    Given a vault "my-notes" exists with documents
    When I export the vault "my-notes"
    Then I receive a ZIP file
    And the ZIP contains all documents from the vault
    And the folder structure is preserved in the ZIP

  Scenario: Exported documents include frontmatter
    Given a vault with documents containing frontmatter
    When I export the vault
    Then each document in the ZIP includes its YAML frontmatter
    And tags are preserved in frontmatter
    And custom fields are preserved

  Scenario: Export empty vault
    Given an empty vault "empty-vault" exists
    When I export the vault "empty-vault"
    Then I receive a valid but empty ZIP file

  Scenario: Export vault with nested folders
    Given a vault with deeply nested folder structure
    When I export the vault
    Then all nested paths are preserved in the ZIP
    And documents can be found at their original paths

  Scenario: Export non-existent vault fails
    When I try to export a non-existent vault "ghost-vault"
    Then I receive a not found error

  Scenario: Round-trip import and export
    Given a vault "roundtrip" was imported from a ZIP file
    When I export the vault "roundtrip"
    Then the exported ZIP has the same structure as the original
    And document content matches the original
