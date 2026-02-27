Feature: Semantic Search
  As a user
  I want to search my vault by meaning
  So that I can find relevant documents even without exact keyword matches

  Background:
    Given a registered user exists
    And the user is authenticated
    And a vault "research" exists with embedded documents

  Scenario: Search documents by semantic meaning
    Given documents about "machine learning" and "deep neural networks"
    When I search for "artificial intelligence concepts"
    Then I receive relevant documents
    And results are ordered by relevance score
    And the matched chunk content is returned

  Scenario: Filter semantic search by folder
    Given documents in "Projects" and "Archive" folders
    When I search for "project updates" in folder "Projects"
    Then only documents from "Projects" folder are returned

  Scenario: Filter semantic search by tags
    Given documents tagged with "active" and "archived"
    When I search for "status report" with tag filter ["active"]
    Then only documents with "active" tag are returned

  Scenario: Full-text search as alternative
    Given a document containing the exact phrase "quarterly review"
    When I perform a full-text search for "quarterly review"
    Then the document is found
    And a headline with highlighted matches is returned

  Scenario: Search returns document metadata
    Given searchable documents in the vault
    When I perform a search
    Then each result includes document id
    And each result includes document title
    And each result includes document path
    And each result includes relevance score

  Scenario: Limit search results
    Given many documents matching a query
    When I search with limit 5
    Then at most 5 results are returned
    And they are the top 5 by relevance

  Scenario: Semantic search with threshold
    Given documents with varying relevance to a query
    When I search with minimum score threshold 0.8
    Then only highly relevant results are returned
    And all results have score >= 0.8
