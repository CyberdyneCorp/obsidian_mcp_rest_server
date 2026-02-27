#!/usr/bin/env python3
"""Test graph building with AGE after fixing quote escaping."""

import sys
from datetime import datetime

import httpx

BASE_URL = "http://localhost:8001"
VAULT_ZIP = "/Users/leonardoaraujo/work/obsidian_MCP/LeoVaultTest.zip"


def main():
    """Test graph building with fixed quote escaping."""
    print("=" * 60)
    print("Leo Vault - Graph Building Test (with AGE)")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"leo-graph-{timestamp}@example.com"
    password = "testpassword123"
    vault_slug = f"leo-graph-{timestamp}"

    # Longer timeout for large vault processing
    with httpx.Client(base_url=BASE_URL, timeout=600.0) as client:
        # 1. Register user
        print("\n1. Registering user...")
        response = client.post("/auth/register", json={
            "email": email,
            "password": password,
            "display_name": "Leo Graph Test"
        })
        if response.status_code != 201:
            print(f"   x Registration failed: {response.text}")
            sys.exit(1)
        print(f"   + User registered")

        # 2. Login
        print("\n2. Logging in...")
        response = client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code != 200:
            print(f"   x Login failed: {response.text}")
            sys.exit(1)
        tokens = response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("   + Logged in")

        # 3. Import vault WITHOUT embeddings (faster, just test graph)
        print("\n3. Importing vault (without embeddings, testing graph)...")
        print(f"   File: {VAULT_ZIP}")

        with open(VAULT_ZIP, "rb") as f:
            files = {"file": (f"vault-{timestamp}.zip", f, "application/zip")}
            response = client.post(
                f"/vaults/{vault_slug}/ingest",
                files=files,
                params={"generate_embeddings": False},  # Skip embeddings for speed
                headers=headers,
            )

        if response.status_code == 202:
            result = response.json()
            print(f"   + Vault imported!")
            print(f"   - Documents: {result.get('documents_count')}")
        else:
            print(f"   x Import failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            sys.exit(1)

        # 4. Test graph connections for a document
        print("\n4. Testing graph connections...")

        # First get a document
        response = client.get(
            f"/vaults/{vault_slug}/documents",
            params={"limit": 5},
            headers=headers,
        )
        if response.status_code == 200:
            docs = response.json()
            if docs.get("documents"):
                doc_id = docs["documents"][0]["id"]
                doc_title = docs["documents"][0]["title"]
                print(f"   Testing connections for: {doc_title}")

                # Get connections via graph
                response = client.get(
                    f"/vaults/{vault_slug}/graph/connections/{doc_id}",
                    params={"depth": 2},
                    headers=headers,
                )
                if response.status_code == 200:
                    connections = response.json()
                    print(f"   + Found {len(connections.get('connections', []))} connections")
                    for conn in connections.get("connections", [])[:5]:
                        print(f"      - {conn.get('title')}")
                else:
                    print(f"   x Graph query failed: {response.text[:200]}")
        else:
            print(f"   x Could not list documents: {response.text}")

        # 5. Test getting graph hubs
        print("\n5. Testing graph hubs (most connected docs)...")
        response = client.get(
            f"/vaults/{vault_slug}/graph/hubs",
            params={"limit": 5},
            headers=headers,
        )
        if response.status_code == 200:
            hubs = response.json()
            print(f"   + Top connected documents:")
            for hub in hubs.get("hubs", [])[:5]:
                print(f"      - {hub.get('title')} ({hub.get('connections', 0)} connections)")
        else:
            print(f"   x Hubs query failed: {response.text[:200]}")

        # 6. Test getting orphan documents
        print("\n6. Testing orphan documents (no connections)...")
        response = client.get(
            f"/vaults/{vault_slug}/graph/orphans",
            headers=headers,
        )
        if response.status_code == 200:
            orphans = response.json()
            print(f"   + Found {len(orphans.get('orphans', []))} orphan documents")
            for orphan in orphans.get("orphans", [])[:3]:
                print(f"      - {orphan.get('title')}")
        else:
            print(f"   x Orphans query failed: {response.text[:200]}")

        print("\n" + "=" * 60)
        print("+ Graph building test completed!")
        print("=" * 60)


if __name__ == "__main__":
    main()
