Feature: Knowledge Graph Queries
  As a user
  I want to explore document connections in my vault
  So that I can discover relationships and navigate my knowledge base

  Background:
    Given a registered user exists
    And the user is authenticated
    And a vault "knowledge" exists with linked documents

  Scenario: Get document connections
    Given a document "Hub Note" with links to multiple documents
    When I request connections for "Hub Note" with depth 2
    Then I receive the center document info
    And I receive a list of connected documents
    And each connection includes distance from center
    And each connection includes link type

  Scenario: Connections respect depth parameter
    Given a chain of linked documents A -> B -> C -> D
    When I request connections for "A" with depth 1
    Then only "B" is in the connections
    When I request connections for "A" with depth 3
    Then "B", "C", and "D" are in the connections

  Scenario: Find orphan documents
    Given documents with no incoming or outgoing links
    When I request orphan documents
    Then I receive a list of unconnected documents
    And connected documents are not included

  Scenario: Find hub documents
    Given documents with varying connection counts
    When I request hub documents with limit 5
    Then I receive the top 5 most connected documents
    And results are ordered by connection count descending

  Scenario: Get shortest path between documents
    Given documents "Start" and "End" connected through intermediate docs
    When I request the shortest path from "Start" to "End"
    Then I receive the path as a list of documents
    And the path length is returned

  Scenario: No path exists between documents
    Given isolated document groups with no cross-links
    When I request a path between documents in different groups
    Then a not found response is returned

  Scenario: Connections for document with no links
    Given an isolated document with no links
    When I request connections for the isolated document
    Then the center document is returned
    And the connections list is empty

  Scenario: Graph query on non-existent vault
    When I request graph data for a non-existent vault
    Then a vault not found error is returned

  Scenario: Graph query for non-existent document
    Given a vault exists
    When I request connections for a non-existent document
    Then a document not found error is returned
