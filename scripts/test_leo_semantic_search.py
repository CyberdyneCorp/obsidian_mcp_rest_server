#!/usr/bin/env python3
"""Test semantic search on Leo's vault with embeddings."""

import sys
from datetime import datetime

import httpx

BASE_URL = "http://localhost:8001"
VAULT_ZIP = "/Users/leonardoaraujo/work/obsidian_MCP/LeoVaultTest.zip"


def main():
    """Test semantic search with embeddings."""
    print("=" * 60)
    print("Leo Vault - Semantic Search Test (with Embeddings)")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"leo-semantic-{timestamp}@example.com"
    password = "testpassword123"
    vault_slug = f"leo-semantic-{timestamp}"

    # Longer timeout for embedding generation
    with httpx.Client(base_url=BASE_URL, timeout=600.0) as client:
        # 1. Register user
        print("\n1. Registering user...")
        response = client.post("/auth/register", json={
            "email": email,
            "password": password,
            "display_name": "Leo Semantic Test"
        })
        if response.status_code != 201:
            print(f"   ✗ Registration failed: {response.text}")
            sys.exit(1)
        print(f"   ✓ User registered")

        # 2. Login
        print("\n2. Logging in...")
        response = client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code != 200:
            print(f"   ✗ Login failed: {response.text}")
            sys.exit(1)
        tokens = response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("   ✓ Logged in")

        # 3. Import vault WITH embeddings (this will take time)
        print("\n3. Importing vault WITH embeddings (this may take a few minutes)...")
        print(f"   File: {VAULT_ZIP}")

        with open(VAULT_ZIP, "rb") as f:
            files = {"file": (f"vault-{timestamp}.zip", f, "application/zip")}
            response = client.post(
                f"/vaults/{vault_slug}/ingest",
                files=files,
                params={"generate_embeddings": True},  # ENABLED
                headers=headers,
            )

        if response.status_code == 202:
            result = response.json()
            print(f"   ✓ Vault imported with embeddings!")
            print(f"   - Documents: {result.get('documents_count')}")
        else:
            print(f"   ✗ Import failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            sys.exit(1)

        # 4. Test semantic search
        print("\n4. Testing semantic search...")

        queries = [
            "machine learning and neural networks",
            "blockchain cryptocurrency",
            "electronics circuit design",
            "Python programming",
            "physics mechanics",
        ]

        for query in queries:
            print(f"\n   Query: '{query}'")
            response = client.post(
                f"/vaults/{vault_slug}/search/semantic",
                json={
                    "query": query,
                    "limit": 5,
                    "threshold": 0.5
                },
                headers=headers,
            )
            if response.status_code == 200:
                results = response.json()
                print(f"   ✓ Found {results['total']} results")
                for i, r in enumerate(results["results"][:3], 1):
                    print(f"      {i}. {r['document']['title']} (score: {r['score']:.3f})")
            else:
                print(f"   ✗ Search failed: {response.text[:200]}")

        print("\n" + "=" * 60)
        print("✓ Semantic search test completed!")
        print("=" * 60)


if __name__ == "__main__":
    main()
