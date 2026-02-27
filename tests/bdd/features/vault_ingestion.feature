Feature: Vault Ingestion
  As a user
  I want to upload my Obsidian vault as a ZIP file
  So that my notes are stored and searchable in the system

  Background:
    Given a registered user exists
    And the user is authenticated

  Scenario: Ingest vault from ZIP file
    Given a valid ZIP file containing an Obsidian vault
    When the user uploads the ZIP file to create a new vault "My Knowledge Base"
    Then a new vault "My Knowledge Base" is created
    And the vault contains all documents from the ZIP
    And the folder structure is preserved

  Scenario: Parse wiki-links from documents
    Given a vault with a document containing wiki-links
    When the vault is ingested
    Then all wiki-links are extracted
    And links with aliases have correct display text
    And embed links are marked as embeds

  Scenario: Resolve wiki-links to target documents
    Given a vault with interconnected documents
    When the vault is ingested
    Then links pointing to existing documents are resolved
    And resolved links have target_document_id set
    And the is_resolved flag is true

  Scenario: Handle unresolved wiki-links
    Given a vault with a document linking to a non-existent document
    When the vault is ingested
    Then the link is stored with target_document_id as null
    And the is_resolved flag is false

  Scenario: Extract frontmatter metadata
    Given a document with YAML frontmatter
    When the document is ingested
    Then frontmatter fields are extracted as JSON
    And tags from frontmatter are associated with the document
    And aliases are stored for link resolution

  Scenario: Extract inline tags
    Given a document with inline hashtag tags
    When the document is ingested
    Then all inline tags are extracted
    And nested tags create hierarchy
    And tags are associated with the document

  Scenario: Generate document embeddings
    Given a vault with documents
    When the vault is ingested with embeddings enabled
    Then document content is chunked appropriately
    And embeddings are generated for each chunk
    And embeddings are stored in the vector table

  Scenario: Build knowledge graph
    Given a vault with linked documents
    When the vault is ingested
    Then document nodes are created in the graph
    And link edges connect related documents
    And the graph can be queried for connections
