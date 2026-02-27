Feature: Document Linking
  As a user
  I want to navigate between connected documents
  So that I can explore my knowledge graph

  Background:
    Given a registered user exists
    And the user is authenticated
    And a vault "knowledge-base" exists with documents

  Scenario: Get outgoing links from a document
    Given a document "Project Planning" with links to other documents
    When I request outgoing links for "Project Planning"
    Then I receive a list of links
    And each link contains target document information
    And resolved links show the target document title and path

  Scenario: Get backlinks (incoming links) to a document
    Given multiple documents link to "Reference"
    When I request backlinks for "Reference"
    Then I receive a list of source documents
    And each backlink includes the link text used
    And context around the link is provided

  Scenario: Handle links with display text aliases
    Given a document links using [[Target|Custom Display]]
    When I get the link details
    Then the link_text is "Target"
    And the display_text is "Custom Display"

  Scenario: Sync links after document update
    Given a document "Source" with a link to "Target A"
    When I update "Source" to link to "Target B" instead
    Then the old link to "Target A" is removed
    And a new link to "Target B" is created
    And backlink counts are updated correctly

  Scenario: Track link types
    Given a document with various link types
    When I get the document's outgoing links
    Then wikilinks have type "wikilink"
    And embeds have type "embed"
    And header links have type "header"

  Scenario: Resolve links by alias
    Given a document "Notes" has alias "Quick Notes"
    And another document links to [[Quick Notes]]
    When links are resolved
    Then the link resolves to the "Notes" document
