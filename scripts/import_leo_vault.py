#!/usr/bin/env python3
"""Import Leo's vault for testing."""

import sys
from datetime import datetime

import httpx

BASE_URL = "http://localhost:8001"
VAULT_ZIP = "/Users/leonardoaraujo/work/obsidian_MCP/LeoVaultTest.zip"


def main():
    """Import the vault."""
    print("=" * 60)
    print("Leo Vault Import Test")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"leo-{timestamp}@example.com"
    password = "testpassword123"

    # Increase timeout for large file upload
    with httpx.Client(base_url=BASE_URL, timeout=300.0) as client:
        # 1. Register user
        print("\n1. Registering user...")
        response = client.post("/auth/register", json={
            "email": email,
            "password": password,
            "display_name": "Leo Test"
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
            print("   ✓ Logged in successfully")
        else:
            print(f"   ✗ Login failed: {response.text}")
            sys.exit(1)

        headers = {"Authorization": f"Bearer {access_token}"}

        # 3. Import vault (without embeddings first for speed)
        print("\n3. Importing vault (without embeddings for speed test)...")
        print(f"   File: {VAULT_ZIP}")

        with open(VAULT_ZIP, "rb") as f:
            files = {"file": ("LeoVaultTest.zip", f, "application/zip")}
            response = client.post(
                "/vaults/leo-knowledge/ingest",
                files=files,
                params={"generate_embeddings": False},  # Disable for speed
                headers=headers,
            )

        if response.status_code == 202:
            result = response.json()
            print(f"   ✓ Vault imported!")
            print(f"   - Vault ID: {result.get('vault_id')}")
            print(f"   - Documents: {result.get('documents_count')}")
            print(f"   - Status: {result.get('status')}")
        else:
            print(f"   ✗ Import failed: {response.status_code}")
            print(f"   Response: {response.text}")
            sys.exit(1)

        # 4. List documents
        print("\n4. Listing documents...")
        response = client.get(
            "/vaults/leo-knowledge/documents",
            params={"limit": 10},
            headers=headers,
        )
        if response.status_code == 200:
            docs = response.json()
            print(f"   ✓ Found {docs.get('total', len(docs.get('documents', [])))} documents")
            print("   Sample documents:")
            for doc in docs.get("documents", [])[:5]:
                print(f"      - {doc['path']}")
        else:
            print(f"   ✗ List failed: {response.text}")

        # 5. Test fulltext search
        print("\n5. Testing fulltext search...")
        response = client.get(
            "/vaults/leo-knowledge/search/fulltext",
            params={"q": "machine learning", "limit": 5},
            headers=headers,
        )
        if response.status_code == 200:
            results = response.json()
            print(f"   ✓ Found {len(results.get('results', []))} results for 'machine learning'")
            for r in results.get("results", [])[:3]:
                print(f"      - {r['document']['title']}")
        else:
            print(f"   ✗ Search failed: {response.text}")

        # 6. Get a document with links
        print("\n6. Checking document links...")
        if docs and docs.get("documents"):
            doc_id = docs["documents"][0]["id"]
            response = client.get(
                f"/vaults/leo-knowledge/documents/{doc_id}",
                headers=headers,
            )
            if response.status_code == 200:
                doc = response.json()
                print(f"   Document: {doc['title']}")
                print(f"   - Outgoing links: {doc.get('link_count', 0)}")
                print(f"   - Backlinks: {doc.get('backlink_count', 0)}")
                print(f"   - Tags: {doc.get('tags', [])}")

        print("\n" + "=" * 60)
        print("✓ Import test completed!")
        print("=" * 60)
        print(f"\nVault slug: leo-knowledge")
        print(f"User email: {email}")


if __name__ == "__main__":
    main()
