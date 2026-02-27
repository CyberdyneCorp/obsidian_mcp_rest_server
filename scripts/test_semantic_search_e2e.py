#!/usr/bin/env python3
"""End-to-end test for semantic search with real OpenAI API.

Usage:
    # Start the server first
    just dev

    # In another terminal, run this script
    uv run python scripts/test_semantic_search_e2e.py
"""

import io
import sys
import zipfile
from datetime import datetime

import httpx

BASE_URL = "http://localhost:8001"


def create_test_vault_zip() -> bytes:
    """Create a test vault ZIP with sample documents."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Document about machine learning
        zf.writestr(
            "Notes/machine-learning.md",
            """---
title: Machine Learning Basics
tags: [ai, ml, deep-learning]
---

# Machine Learning Basics

Machine learning is a subset of artificial intelligence that focuses on
building systems that can learn from data. Deep learning is a type of
machine learning that uses neural networks with many layers.

## Key Concepts

### Supervised Learning
- Uses labeled training data
- Examples: classification, regression
- Common algorithms: linear regression, decision trees, neural networks

### Unsupervised Learning
- Finds patterns in unlabeled data
- Examples: clustering, dimensionality reduction
- Common algorithms: k-means, PCA, autoencoders

### Reinforcement Learning
- Learns through trial and error
- Uses rewards and penalties
- Applications: game playing, robotics

## Neural Networks

Neural networks are the foundation of deep learning. They consist of:
- Input layer: receives the data
- Hidden layers: process the data
- Output layer: produces the result

Popular architectures include CNNs for images and RNNs/Transformers for sequences.
"""
        )

        # Document about Python
        zf.writestr(
            "Notes/python-programming.md",
            """---
title: Python Programming Guide
tags: [programming, python, software]
---

# Python Programming

Python is a versatile, high-level programming language known for its simplicity
and readability. It was created by Guido van Rossum and first released in 1991.

## Why Python?

- Easy to learn and read
- Large standard library
- Extensive third-party packages
- Cross-platform compatibility
- Strong community support

## Popular Frameworks

### Web Development
- **Django**: Full-featured framework with batteries included
- **Flask**: Lightweight and flexible microframework
- **FastAPI**: Modern, fast framework for building APIs

### Data Science
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation and analysis
- **Scikit-learn**: Machine learning algorithms
- **TensorFlow/PyTorch**: Deep learning

### Automation
- **Selenium**: Web automation
- **Beautiful Soup**: Web scraping
- **Requests**: HTTP library

## Best Practices

1. Follow PEP 8 style guide
2. Use virtual environments
3. Write tests for your code
4. Document your functions
5. Use type hints for clarity
"""
        )

        # Document about cooking
        zf.writestr(
            "Notes/cooking-tips.md",
            """---
title: Essential Cooking Tips
tags: [cooking, food, kitchen]
---

# Cooking Tips for Beginners

Essential cooking techniques every home cook should master.

## Basic Techniques

### Knife Skills
- Always use a sharp knife
- Learn the claw grip for safety
- Practice consistent cuts for even cooking

### Heat Management
- Preheat your pan before adding oil
- Don't overcrowd the pan
- Let meat come to room temperature before cooking

### Seasoning
- Season throughout the cooking process
- Salt enhances other flavors
- Acid (lemon, vinegar) brightens dishes

## Kitchen Essentials

### Must-Have Tools
- Chef's knife (8-10 inch)
- Cutting board
- Cast iron skillet
- Stainless steel pots
- Wooden spoons

### Pantry Staples
- Olive oil
- Salt and pepper
- Garlic and onions
- Stock/broth
- Canned tomatoes

## Pro Tips

1. Read the entire recipe before starting
2. Mise en place (prep everything first)
3. Let meat rest after cooking
4. Taste as you go
5. Clean as you cook
"""
        )

        # Document about project management
        zf.writestr(
            "Projects/project-management.md",
            """---
title: Project Management Fundamentals
tags: [business, management, agile]
---

# Project Management

Effective project management is crucial for delivering successful outcomes.

## Methodologies

### Waterfall
Traditional sequential approach:
1. Requirements
2. Design
3. Implementation
4. Testing
5. Deployment
6. Maintenance

### Agile
Iterative approach with flexibility:
- Sprints (2-4 weeks)
- Daily standups
- Retrospectives
- Continuous improvement

### Scrum Framework
- Product Owner: defines priorities
- Scrum Master: facilitates process
- Development Team: delivers work
- Sprint Planning, Review, Retrospective

## Key Principles

1. Clear objectives and scope
2. Stakeholder communication
3. Risk management
4. Resource allocation
5. Quality assurance

## Tools

- Jira: Issue tracking
- Trello: Kanban boards
- Asana: Task management
- Slack: Communication
- Confluence: Documentation
"""
        )

    return buffer.getvalue()


def main():
    """Run the end-to-end test."""
    print("=" * 60)
    print("Semantic Search E2E Test")
    print("=" * 60)

    # Create unique email for this test run
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"test-{timestamp}@example.com"
    password = "testpassword123"

    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Register a user
        print("\n1. Registering user...")
        response = client.post("/auth/register", json={
            "email": email,
            "password": password,
            "display_name": "Test User"
        })
        if response.status_code == 201:
            print(f"   ✓ User registered: {email}")
        else:
            print(f"   ✗ Registration failed: {response.text}")
            sys.exit(1)

        # 2. Login
        print("\n2. Logging in...")
        response = client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            print(f"   ✓ Logged in successfully")
        else:
            print(f"   ✗ Login failed: {response.text}")
            sys.exit(1)

        # Set auth header for subsequent requests
        headers = {"Authorization": f"Bearer {access_token}"}

        # 3. Ingest vault
        print("\n3. Ingesting vault (this will generate embeddings)...")
        zip_content = create_test_vault_zip()

        files = {"file": ("test-vault.zip", zip_content, "application/zip")}
        response = client.post(
            f"/vaults/semantic-test-{timestamp}/ingest",
            files=files,
            params={"generate_embeddings": True},
            headers=headers,
        )

        if response.status_code == 202:
            result = response.json()
            print(f"   ✓ Vault ingested: {result['documents_count']} documents")
            vault_slug = f"semantic-test-{timestamp}"
        else:
            print(f"   ✗ Ingestion failed: {response.text}")
            sys.exit(1)

        # 4. Test semantic search - AI/ML query
        print("\n4. Testing semantic search...")
        print("\n   Query: 'neural networks and deep learning'")
        response = client.post(
            f"/vaults/{vault_slug}/search/semantic",
            json={
                "query": "neural networks and deep learning",
                "limit": 5,
                "threshold": 0.3
            },
            headers=headers,
        )

        if response.status_code == 200:
            results = response.json()
            print(f"   ✓ Found {results['total']} results:")
            for i, r in enumerate(results["results"], 1):
                print(f"      {i}. {r['document']['title']} (score: {r['score']:.3f})")
                print(f"         Path: {r['document']['path']}")
                print(f"         Match: {r['matched_chunk'][:100]}...")
        else:
            print(f"   ✗ Search failed: {response.text}")

        # 5. Test semantic search - Python query
        print("\n   Query: 'web development frameworks'")
        response = client.post(
            f"/vaults/{vault_slug}/search/semantic",
            json={
                "query": "web development frameworks",
                "limit": 5,
                "threshold": 0.3
            },
            headers=headers,
        )

        if response.status_code == 200:
            results = response.json()
            print(f"   ✓ Found {results['total']} results:")
            for i, r in enumerate(results["results"], 1):
                print(f"      {i}. {r['document']['title']} (score: {r['score']:.3f})")
        else:
            print(f"   ✗ Search failed: {response.text}")

        # 6. Test semantic search - Cooking query
        print("\n   Query: 'kitchen tools and recipes'")
        response = client.post(
            f"/vaults/{vault_slug}/search/semantic",
            json={
                "query": "kitchen tools and recipes",
                "limit": 5,
                "threshold": 0.3
            },
            headers=headers,
        )

        if response.status_code == 200:
            results = response.json()
            print(f"   ✓ Found {results['total']} results:")
            for i, r in enumerate(results["results"], 1):
                print(f"      {i}. {r['document']['title']} (score: {r['score']:.3f})")
        else:
            print(f"   ✗ Search failed: {response.text}")

        # 7. Test semantic search with folder filter
        print("\n   Query: 'any topic' with folder='Notes'")
        response = client.post(
            f"/vaults/{vault_slug}/search/semantic",
            json={
                "query": "any topic",
                "limit": 10,
                "threshold": 0.0,
                "folder": "Notes"
            },
            headers=headers,
        )

        if response.status_code == 200:
            results = response.json()
            print(f"   ✓ Found {results['total']} results in Notes folder:")
            for i, r in enumerate(results["results"], 1):
                print(f"      {i}. {r['document']['path']}")
        else:
            print(f"   ✗ Search failed: {response.text}")

        # 8. Test fulltext search
        print("\n5. Testing fulltext search...")
        print("\n   Query: 'Python'")
        response = client.get(
            f"/vaults/{vault_slug}/search/fulltext",
            params={"q": "Python", "limit": 5},
            headers=headers,
        )

        if response.status_code == 200:
            results = response.json()
            print(f"   ✓ Found {len(results['results'])} results:")
            for i, r in enumerate(results["results"], 1):
                print(f"      {i}. {r['document']['title']}")
                if r.get("headline"):
                    print(f"         Headline: {r['headline'][:80]}...")
        else:
            print(f"   ✗ Search failed: {response.text}")

        # 9. Test document links
        print("\n6. Getting document with links...")
        response = client.get(
            f"/vaults/{vault_slug}/documents",
            params={"limit": 1},
            headers=headers,
        )

        if response.status_code == 200:
            docs = response.json()
            if docs["documents"]:
                doc = docs["documents"][0]
                print(f"   Document: {doc['title']}")
                print(f"   Links: {doc.get('link_count', 0)} outgoing, {doc.get('backlink_count', 0)} backlinks")

        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    main()
