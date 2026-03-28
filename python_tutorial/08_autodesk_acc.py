"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 8: Autodesk ACC Build — Two-Legged OAuth        ║
║                                                          ║
║   Learn:                                                 ║
║   • Two-legged OAuth 2.0 authentication flow             ║
║   • Getting an access token with client credentials      ║
║   • Listing ACC Build projects                           ║
║   • Working with Issues (list + create)                  ║
║   • Working with RFIs                                    ║
║                                                          ║
║   No extra dependencies — uses Python stdlib only.       ║
║   Set APS_CLIENT_ID and APS_CLIENT_SECRET in .env        ║
╚══════════════════════════════════════════════════════════╝

Run: python 08_autodesk_acc.py
"""

import os
import json
import base64
import urllib.request
import urllib.error
import urllib.parse

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass


# ══════════════════════════════════════════════════════════════════════════════
#  Configuration
# ══════════════════════════════════════════════════════════════════════════════

APS_AUTH_URL = "https://developer.api.autodesk.com/authentication/v2/token"
APS_BASE_URL = "https://developer.api.autodesk.com"

CLIENT_ID = os.environ.get("APS_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("APS_CLIENT_SECRET", "")


def _request(method, url, headers=None, body=None):
    """Make an HTTP request and return (status, response_dict)."""
    hdrs = headers or {}
    data = None
    if body is not None:
        if isinstance(body, str):
            data = body.encode("utf-8")
        elif isinstance(body, bytes):
            data = body
        else:
            data = json.dumps(body).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(text)
        except json.JSONDecodeError:
            return e.code, {"error": text}


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1: Two-Legged OAuth — Get Access Token
# ══════════════════════════════════════════════════════════════════════════════

def demo_two_legged_auth():
    """Demonstrate the two-legged OAuth 2.0 flow."""
    print("\n📋 Demo 1: Two-Legged OAuth 2.0 Authentication\n")

    print("  Two-legged OAuth is for server-to-server communication.")
    print("  No user login is needed — your app authenticates with its own credentials.\n")

    print("  ┌─────────────────────────────────────────────────────────────────┐")
    print("  │  TWO-LEGGED OAUTH FLOW                                         │")
    print("  ├─────────────────────────────────────────────────────────────────┤")
    print("  │                                                                 │")
    print("  │  Your Server                  Autodesk Auth Server              │")
    print("  │      │                              │                           │")
    print("  │      │  POST /authentication/v2/token                           │")
    print("  │      │  Authorization: Basic base64(id:secret)                  │")
    print("  │      │  Body: grant_type=client_credentials&scope=...           │")
    print("  │      │─────────────────────────────►│                           │")
    print("  │      │                              │                           │")
    print("  │      │  { access_token, expires_in, token_type }                │")
    print("  │      │◄─────────────────────────────│                           │")
    print("  │      │                              │                           │")
    print("  │  Use access_token as Bearer token for all ACC API calls         │")
    print("  │                                                                 │")
    print("  └─────────────────────────────────────────────────────────────────┘\n")

    if not CLIENT_ID or not CLIENT_SECRET:
        print("  ⚠  APS_CLIENT_ID and APS_CLIENT_SECRET not set.")
        print("     Set them in your .env file or environment variables.")
        print("     Get credentials at: https://aps.autodesk.com/myapps\n")
        print("  Here's what the request would look like:\n")
        print("    POST https://developer.api.autodesk.com/authentication/v2/token")
        print("    Authorization: Basic <base64(client_id:client_secret)>")
        print("    Content-Type: application/x-www-form-urlencoded")
        print("    Body: grant_type=client_credentials&scope=data:read data:write\n")
        print("    Expected response:")
        print('    { "access_token": "eyJ...", "expires_in": 3600, "token_type": "Bearer" }\n')
        return None

    # Build the Basic auth header: base64(client_id:client_secret)
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()

    # Request body — URL-encoded form data
    scopes = "data:read data:write data:create account:read"
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "scope": scopes
    })

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_credentials}"
    }

    print("  Requesting access token...")
    print(f"    POST {APS_AUTH_URL}")
    print(f"    Authorization: Basic <base64(client_id:client_secret)>")
    print(f"    Scopes: {scopes}\n")

    status, data = _request("POST", APS_AUTH_URL, headers=headers, body=body)

    if status == 200 and "access_token" in data:
        token = data["access_token"]
        expires = data.get("expires_in", "?")
        print(f"  ✅ Token received!")
        print(f"    Token (first 40 chars): {token[:40]}...")
        print(f"    Expires in: {expires} seconds ({int(expires)//60} minutes)")
        print(f"    Token type: {data.get('token_type', 'Bearer')}")
        return token
    else:
        print(f"  ✗ Authentication failed! Status: {status}")
        print(f"    Response: {json.dumps(data, indent=2)[:300]}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2: List ACC Build Projects
# ══════════════════════════════════════════════════════════════════════════════

def demo_list_projects(token):
    """List projects from ACC Build."""
    print("\n\n📋 Demo 2: List ACC Build Projects\n")

    if not token:
        print("  ⚠  No token available. Showing expected request format.\n")
        print("    GET https://developer.api.autodesk.com/construction/admin/v1/projects")
        print("    Authorization: Bearer <access_token>\n")
        print("    Expected response:")
        print("    {")
        print('      "pagination": { "limit": 20, "offset": 0, "totalResults": 5 },')
        print('      "results": [')
        print('        { "id": "abc-123", "name": "Project Alpha", "status": "active" },')
        print('        { "id": "def-456", "name": "Project Beta", "status": "active" }')
        print("      ]")
        print("    }\n")
        return None

    url = f"{APS_BASE_URL}/construction/admin/v1/projects"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"  GET {url}")
    print(f"  Authorization: Bearer <token>\n")

    status, data = _request("GET", url, headers=headers)

    if status == 200:
        results = data.get("results", [])
        total = data.get("pagination", {}).get("totalResults", len(results))
        print(f"  ✅ Found {total} project(s)\n")

        for i, proj in enumerate(results[:5]):  # Show first 5
            print(f"    {i+1}. {proj.get('name', 'Unnamed')}")
            print(f"       ID:     {proj.get('id', 'N/A')}")
            print(f"       Status: {proj.get('status', 'N/A')}")
            print(f"       Type:   {proj.get('type', 'N/A')}")
            print()

        if total > 5:
            print(f"    ... and {total - 5} more project(s)")

        # Return first project ID for subsequent demos
        if results:
            return results[0].get("id")
    else:
        print(f"  ✗ Failed! Status: {status}")
        print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    return None


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3: List Issues for a Project
# ══════════════════════════════════════════════════════════════════════════════

def demo_list_issues(token, project_id):
    """List issues from a specific ACC Build project."""
    print("\n\n📋 Demo 3: List Project Issues\n")

    if not token or not project_id:
        print("  ⚠  No token or project ID. Showing expected request format.\n")
        print("    GET https://developer.api.autodesk.com/construction/issues/v1/projects/{projectId}/issues")
        print("    Authorization: Bearer <access_token>\n")
        print("    Expected response:")
        print("    {")
        print('      "pagination": { "limit": 25, "offset": 0, "totalResults": 12 },')
        print('      "results": [')
        print("        {")
        print('          "id": "issue-001",')
        print('          "title": "Concrete crack in foundation",')
        print('          "status": "open",')
        print('          "issueType": "Safety",')
        print('          "dueDate": "2025-06-15"')
        print("        }")
        print("      ]")
        print("    }\n")
        return

    url = f"{APS_BASE_URL}/construction/issues/v1/projects/{project_id}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"  GET {url}")
    print(f"  Authorization: Bearer <token>\n")

    status, data = _request("GET", url, headers=headers)

    if status == 200:
        results = data.get("results", [])
        total = data.get("pagination", {}).get("totalResults", len(results))
        print(f"  ✅ Found {total} issue(s)\n")

        for i, issue in enumerate(results[:5]):
            print(f"    {i+1}. {issue.get('title', 'Untitled')}")
            print(f"       ID:     {issue.get('id', 'N/A')}")
            print(f"       Status: {issue.get('status', 'N/A')}")
            print(f"       Type:   {issue.get('issueType', 'N/A')}")
            due = issue.get("dueDate", "N/A")
            print(f"       Due:    {due}")
            print()
    else:
        print(f"  ✗ Failed! Status: {status}")
        print(f"    Response: {json.dumps(data, indent=2)[:300]}")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4: Create an Issue
# ══════════════════════════════════════════════════════════════════════════════

def demo_create_issue(token, project_id):
    """Create a new issue in an ACC Build project."""
    print("\n\n📋 Demo 4: Create a New Issue\n")

    if not token or not project_id:
        print("  ⚠  No token or project ID. Showing expected request format.\n")
        print("    POST https://developer.api.autodesk.com/construction/issues/v1/projects/{projectId}/issues")
        print("    Authorization: Bearer <access_token>")
        print("    Content-Type: application/json\n")
        print("    Request body:")
        print("    {")
        print('      "title": "Safety railing missing on level 3",')
        print('      "description": "The safety railing near stairwell B is missing.",')
        print('      "status": "open",')
        print('      "issueType": "Safety"')
        print("    }\n")
        print("    Expected response (201 Created):")
        print("    {")
        print('      "id": "new-issue-789",')
        print('      "title": "Safety railing missing on level 3",')
        print('      "status": "open",')
        print('      "createdAt": "2025-03-28T10:00:00Z"')
        print("    }\n")
        return

    url = f"{APS_BASE_URL}/construction/issues/v1/projects/{project_id}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    issue_data = {
        "title": "Tutorial Test Issue — Safe to Delete",
        "description": "This issue was created by the API tutorial script. You can safely delete it.",
        "status": "open"
    }

    print(f"  POST {url}")
    print(f"  Body: {json.dumps(issue_data, indent=2)}\n")

    status, data = _request("POST", url, headers=headers, body=issue_data)

    if status in (200, 201):
        print(f"  ✅ Issue created!")
        print(f"    ID:      {data.get('id', 'N/A')}")
        print(f"    Title:   {data.get('title', 'N/A')}")
        print(f"    Status:  {data.get('status', 'N/A')}")
        print(f"    Created: {data.get('createdAt', 'N/A')}")
    else:
        print(f"  ✗ Failed! Status: {status}")
        print(f"    Response: {json.dumps(data, indent=2)[:300]}")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5: List RFIs
# ══════════════════════════════════════════════════════════════════════════════

def demo_list_rfis(token, project_id):
    """List RFIs from a specific ACC Build project."""
    print("\n\n📋 Demo 5: List RFIs (Requests for Information)\n")

    if not token or not project_id:
        print("  ⚠  No token or project ID. Showing expected request format.\n")
        print("    GET https://developer.api.autodesk.com/construction/rfis/v2/projects/{projectId}/rfis")
        print("    Authorization: Bearer <access_token>\n")
        print("    Expected response:")
        print("    {")
        print('      "pagination": { "limit": 25, "offset": 0, "totalResults": 3 },')
        print('      "results": [')
        print("        {")
        print('          "id": "rfi-001",')
        print('          "title": "Clarification on structural beam specs",')
        print('          "status": "open",')
        print('          "priority": "high",')
        print('          "assignedTo": "john@example.com"')
        print("        }")
        print("      ]")
        print("    }\n")
        return

    url = f"{APS_BASE_URL}/construction/rfis/v2/projects/{project_id}/rfis"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"  GET {url}")
    print(f"  Authorization: Bearer <token>\n")

    status, data = _request("GET", url, headers=headers)

    if status == 200:
        results = data.get("results", [])
        total = data.get("pagination", {}).get("totalResults", len(results))
        print(f"  ✅ Found {total} RFI(s)\n")

        for i, rfi in enumerate(results[:5]):
            print(f"    {i+1}. {rfi.get('title', 'Untitled')}")
            print(f"       ID:       {rfi.get('id', 'N/A')}")
            print(f"       Status:   {rfi.get('status', 'N/A')}")
            print(f"       Priority: {rfi.get('priority', 'N/A')}")
            print()
    else:
        print(f"  ✗ Failed! Status: {status}")
        print(f"    Response: {json.dumps(data, indent=2)[:300]}")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 6: Submittals — Full Workflow
# ══════════════════════════════════════════════════════════════════════════════

def demo_submittals(token, project_id):
    """Demonstrate the full submittals workflow: list, create, submit, check status."""
    print("\n\n📋 Demo 6: Submittals — Full Workflow\n")

    print("  Submittals are formal document submissions for review/approval.")
    print("  Workflow: draft → submitted_for_review → reviewed → approved/rejected\n")

    base_url = f"{APS_BASE_URL}/construction/submittals/v2/projects/{project_id}" if project_id else None

    # ── 6a: List submittals ──────────────────────────────────────────────
    print("  ─── 6a: List Submittals ───\n")

    if not token or not project_id:
        print("  ⚠  No token or project ID. Showing expected request format.\n")
        print("    GET https://developer.api.autodesk.com/construction/submittals/v2/projects/{projectId}/items")
        print("    Authorization: Bearer <access_token>\n")
        print("    Expected response:")
        print("    {")
        print('      "pagination": { "limit": 25, "offset": 0, "totalResults": 10 },')
        print('      "results": [')
        print("        {")
        print('          "id": "sub-001",')
        print('          "title": "Shop Drawings — Steel Structure",')
        print('          "status": "submitted",')
        print('          "customIdentifier": "SUB-001"')
        print("        }")
        print("      ]")
        print("    }\n")
    else:
        url = f"{base_url}/items"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        print(f"  GET {url}\n")
        status, data = _request("GET", url, headers=headers)

        if status == 200:
            results = data.get("results", [])
            total = data.get("pagination", {}).get("totalResults", len(results))
            print(f"  ✅ Found {total} submittal(s)\n")
            for i, sub in enumerate(results[:5]):
                print(f"    {i+1}. {sub.get('title', 'Untitled')}")
                print(f"       ID: {sub.get('id')}  Status: {sub.get('status')}")
                print()
        else:
            print(f"  ✗ Failed! Status: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    # ── 6b: Create a submittal ───────────────────────────────────────────
    print("\n  ─── 6b: Create Submittal (draft) ───\n")

    if not token or not project_id:
        print("    POST .../items")
        print("    Body:")
        print("    {")
        print('      "title": "Shop Drawings — HVAC Ductwork",')
        print('      "description": "Ductwork shop drawings for review",')
        print('      "status": "draft"')
        print("    }\n")
        print("    Expected response (201):")
        print('    { "id": "sub-new-123", "title": "...", "status": "draft" }\n')
        submittal_id = None
    else:
        url = f"{base_url}/items"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        submittal_data = {
            "title": "Tutorial Test Submittal — Safe to Delete",
            "description": "Created by API tutorial script.",
            "status": "draft"
        }

        print(f"  POST {url}")
        print(f"  Body: {json.dumps(submittal_data, indent=2)}\n")

        status, data = _request("POST", url, headers=headers, body=submittal_data)
        submittal_id = data.get("id") if status in (200, 201) else None

        if status in (200, 201):
            print(f"  ✅ Submittal created!")
            print(f"    ID:     {data.get('id')}")
            print(f"    Status: {data.get('status')}")
        else:
            print(f"  ✗ Failed! Status: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    # ── 6c: Submit for review ────────────────────────────────────────────
    print("\n  ─── 6c: Submit for Review (state transition) ───\n")

    if not token or not submittal_id:
        print("    POST .../items/{itemId}:transition")
        print('    Body: { "toState": "submitted" }\n')
        print("    This moves the submittal from 'draft' to 'submitted' for reviewer action.\n")
    else:
        url = f"{base_url}/items/{submittal_id}:transition"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        transition_data = {"toState": "submitted"}

        print(f"  POST {url}")
        print(f"  Body: {json.dumps(transition_data)}\n")

        status, data = _request("POST", url, headers=headers, body=transition_data)

        if status in (200, 201):
            print(f"  ✅ Submitted for review!")
            print(f"    New status: {data.get('status', 'submitted')}")
        else:
            print(f"  ✗ Transition failed: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    # ── 6d: Check approval status ────────────────────────────────────────
    print("\n  ─── 6d: Check Approval Status ───\n")

    if not token or not submittal_id:
        print("    GET .../items/{itemId}")
        print("    Returns full item details including approval status.\n")
        print("    Response fields: id, title, status, reviewers, responses, dueDate\n")
    else:
        url = f"{base_url}/items/{submittal_id}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        print(f"  GET {url}\n")
        status, data = _request("GET", url, headers=headers)

        if status == 200:
            print(f"  ✅ Submittal status:")
            print(f"    ID:      {data.get('id')}")
            print(f"    Title:   {data.get('title')}")
            print(f"    Status:  {data.get('status')}")
        else:
            print(f"  ✗ Failed! Status: {status}")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 7: Assets — Full CRUD
# ══════════════════════════════════════════════════════════════════════════════

def demo_assets(token, project_id):
    """Demonstrate full CRUD operations on ACC Build assets."""
    print("\n\n📋 Demo 7: Assets — Full CRUD\n")

    print("  Assets track physical equipment, materials, and components on a project.")
    print("  The API uses batch operations for efficiency.\n")

    assets_base = f"{APS_BASE_URL}/construction/assets/v2/projects/{project_id}" if project_id else None

    # ── 7a: List asset categories ────────────────────────────────────────
    print("  ─── 7a: List Asset Categories ───\n")

    category_id = None

    if not token or not project_id:
        print("  ⚠  No token/project. Showing expected format.\n")
        print("    GET .../assets/v2/projects/{projectId}/categories")
        print("    Response: [{ id, name, parentId, ... }]\n")
    else:
        url = f"{assets_base}/categories"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        print(f"  GET {url}\n")
        status, data = _request("GET", url, headers=headers)

        if status == 200:
            categories = data if isinstance(data, list) else data.get("results", [])
            print(f"  ✅ Found {len(categories)} categor(ies)\n")
            for i, cat in enumerate(categories[:5]):
                print(f"    {i+1}. {cat.get('name', 'Unnamed')} (ID: {cat.get('id', 'N/A')})")
            if categories:
                category_id = categories[0].get("id")
        else:
            print(f"  ✗ Failed! Status: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    # ── 7b: List assets ──────────────────────────────────────────────────
    print("\n  ─── 7b: List Assets ───\n")

    if not token or not project_id:
        print("    POST .../assets/v2/projects/{projectId}/assets:search")
        print("    Body: { }")
        print("    Response: { results: [{ id, displayName, categoryId, ... }] }\n")
    else:
        url = f"{assets_base}/assets:search"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        print(f"  POST {url}")
        print(f"  Body: {{}}\n")

        status, data = _request("POST", url, headers=headers, body={})

        if status == 200:
            results = data.get("results", [])
            print(f"  ✅ Found {len(results)} asset(s)\n")
            for i, asset in enumerate(results[:5]):
                print(f"    {i+1}. {asset.get('displayName', 'Unnamed')}")
                print(f"       ID: {asset.get('id')}  Category: {asset.get('categoryId', 'N/A')}")
                print()
        else:
            print(f"  ✗ Failed! Status: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    # ── 7c: Create an asset ──────────────────────────────────────────────
    print("\n  ─── 7c: Create Asset ───\n")

    created_asset_id = None

    if not token or not project_id:
        print("    POST .../assets/v2/projects/{projectId}/assets:batch-create")
        print("    Body:")
        print("    {")
        print('      "items": [{')
        print('        "displayName": "HVAC Unit - Floor 3",')
        print('        "categoryId": "cat-id",')
        print('        "description": "Main HVAC unit for third floor"')
        print("      }]")
        print("    }\n")
    else:
        url = f"{assets_base}/assets:batch-create"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        asset_data = {
            "items": [{
                "displayName": "Tutorial Test Asset — Safe to Delete",
                "description": "Created by API tutorial script.",
                **({"categoryId": category_id} if category_id else {})
            }]
        }

        print(f"  POST {url}")
        print(f"  Body: {json.dumps(asset_data, indent=2)}\n")

        status, data = _request("POST", url, headers=headers, body=asset_data)

        if status in (200, 201):
            results = data.get("results", [data] if "id" in data else [])
            if results:
                created_asset_id = results[0].get("id")
                print(f"  ✅ Asset created!")
                print(f"    ID:   {created_asset_id}")
                print(f"    Name: {results[0].get('displayName', 'N/A')}")
            else:
                print(f"  ✅ Response: {json.dumps(data, indent=2)[:200]}")
        else:
            print(f"  ✗ Failed! Status: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    # ── 7d: Update an asset ──────────────────────────────────────────────
    print("\n  ─── 7d: Update Asset ───\n")

    if not token or not created_asset_id:
        print("    PATCH .../assets/v2/projects/{projectId}/assets:batch-patch")
        print("    Body:")
        print("    {")
        print('      "items": [{')
        print('        "id": "asset-id",')
        print('        "displayName": "HVAC Unit - Floor 3 (Updated)",')
        print('        "description": "Updated description"')
        print("      }]")
        print("    }\n")
    else:
        url = f"{assets_base}/assets:batch-patch"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        update_data = {
            "items": [{
                "id": created_asset_id,
                "displayName": "Tutorial Asset (Updated)",
                "description": "Updated by API tutorial."
            }]
        }

        print(f"  PATCH {url}")
        print(f"  Body: {json.dumps(update_data, indent=2)}\n")

        status, data = _request("PATCH", url, headers=headers, body=update_data)

        if status == 200:
            print(f"  ✅ Asset updated!")
        else:
            print(f"  ✗ Failed! Status: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    # ── 7e: Delete an asset ──────────────────────────────────────────────
    print("\n  ─── 7e: Delete Asset ───\n")

    if not token or not created_asset_id:
        print("    POST .../assets/v2/projects/{projectId}/assets:batch-delete")
        print('    Body: { "ids": ["asset-id-1", "asset-id-2"] }\n')
    else:
        url = f"{assets_base}/assets:batch-delete"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        delete_data = {"ids": [created_asset_id]}

        print(f"  POST {url}")
        print(f"  Body: {json.dumps(delete_data)}\n")

        status, data = _request("POST", url, headers=headers, body=delete_data)

        if status in (200, 204):
            print(f"  ✅ Asset deleted!")
        else:
            print(f"  ✗ Failed! Status: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 8: Assets with Revit — Extract & Link
# ══════════════════════════════════════════════════════════════════════════════

def demo_revit_assets(token, project_id):
    """Demonstrate extracting Revit model data and linking to ACC assets."""
    print("\n\n📋 Demo 8: Assets with Revit — Extract & Link\n")

    print("  This shows how to extract element data from a Revit (.rvt) file")
    print("  using the Model Derivative API, then link elements to ACC assets.\n")

    print("  ┌──────────────────────────────────────────────────────────────────┐")
    print("  │  REVIT → ACC ASSET WORKFLOW                                      │")
    print("  ├──────────────────────────────────────────────────────────────────┤")
    print("  │                                                                  │")
    print("  │  1. Upload .rvt file to ACC / OSS bucket → get URN              │")
    print("  │  2. POST /modelderivative/v2/designdata/job → start translation │")
    print("  │  3. GET  .../designdata/{urn}/manifest → poll until 'success'   │")
    print("  │  4. GET  .../designdata/{urn}/metadata → get model GUIDs        │")
    print("  │  5. GET  .../designdata/{urn}/metadata/{guid}/properties        │")
    print("  │     → extract externalId, properties (dimensions, materials)    │")
    print("  │  6. Create/update ACC assets with revitElementId custom attr    │")
    print("  │                                                                  │")
    print("  └──────────────────────────────────────────────────────────────────┘\n")

    md_base = f"{APS_BASE_URL}/modelderivative/v2"

    # ── 8a: Submit translation job ───────────────────────────────────────
    print("  ─── 8a: Submit Translation Job ───\n")

    print("    POST https://developer.api.autodesk.com/modelderivative/v2/designdata/job")
    print("    Headers:")
    print("      Authorization: Bearer <token>")
    print("      Content-Type: application/json")
    print("      x-ads-force: true  (optional, forces re-translation)\n")
    print("    Body:")
    print("    {")
    print('      "input": {')
    print('        "urn": "<base64-encoded-URN-of-rvt-file>",')
    print('        "compressedUrn": false,')
    print('        "rootFilename": "model.rvt"')
    print("      },")
    print('      "output": {')
    print('        "formats": [{')
    print('          "type": "svf2",')
    print('          "views": ["2d", "3d"]')
    print("        }]")
    print("      }")
    print("    }\n")
    print("    Response: { result: 'created', urn: '...', acceptedJobs: {...} }\n")

    if token:
        # Show how you'd actually make this call
        print("  To try this with a real file, you need a URN from an uploaded .rvt file.")
        print("  Upload via Data Management API or ACC UI, then base64-encode the URN.\n")

    # ── 8b: Check translation status ─────────────────────────────────────
    print("  ─── 8b: Check Translation Status ───\n")

    print("    GET https://developer.api.autodesk.com/modelderivative/v2/designdata/{urn}/manifest")
    print("    Authorization: Bearer <token>\n")
    print("    Response:")
    print("    {")
    print('      "type": "manifest",')
    print('      "status": "success",       ← wait for this')
    print('      "progress": "complete",')
    print('      "derivatives": [')
    print('        { "outputType": "svf2", "status": "success", "children": [...] }')
    print("      ]")
    print("    }\n")
    print("    Status values: pending → inprogress → success (or failed)\n")

    # ── 8c: Extract Revit element properties ─────────────────────────────
    print("  ─── 8c: Extract Revit Element Properties ───\n")

    print("    Step 1 — Get model GUIDs:")
    print("    GET .../designdata/{urn}/metadata")
    print("    Response: { data: { metadata: [{ guid: '...', name: 'Model' }] } }\n")

    print("    Step 2 — Get properties for a GUID:")
    print("    GET .../designdata/{urn}/metadata/{guid}/properties")
    print("    Response:")
    print("    {")
    print('      "data": {')
    print('        "collection": [')
    print("          {")
    print('            "objectid": 12345,')
    print('            "name": "HVAC Supply Duct [654321]",')
    print('            "externalId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",')
    print('            "properties": {')
    print('              "Dimensions": { "Width": "600 mm", "Height": "400 mm" },')
    print('              "Identity Data": { "Type Name": "Rectangular Duct" },')
    print('              "Mechanical": { "Flow": "1200 CFM" }')
    print("            }")
    print("          }")
    print("        ]")
    print("      }")
    print("    }\n")

    # ── 8d: Link Revit elements to ACC assets ────────────────────────────
    print("  ─── 8d: Link Revit Elements to ACC Assets ───\n")

    print("  Once you have the externalId from Revit, link it to an ACC asset:")
    print("  Use a custom attribute to store the Revit element reference.\n")

    if not token or not project_id:
        print("    POST .../assets/v2/projects/{projectId}/assets:batch-create")
        print("    Body:")
        print("    {")
        print('      "items": [{')
        print('        "displayName": "HVAC Supply Duct - Floor 3",')
        print('        "categoryId": "category-id",')
        print('        "description": "Extracted from Revit model",')
        print('        "clientAssetId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",')
        print('        "customAttributes": [')
        print("          {")
        print('            "attributeDefinitionId": "revit-element-id-attr-def",')
        print('            "value": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"')
        print("          },")
        print("          {")
        print('            "attributeDefinitionId": "revit-type-attr-def",')
        print('            "value": "Rectangular Duct"')
        print("          }")
        print("        ]")
        print("      }]")
        print("    }\n")
    else:
        # With real credentials, demonstrate a partial version
        assets_base = f"{APS_BASE_URL}/construction/assets/v2/projects/{project_id}"
        url = f"{assets_base}/assets:batch-create"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Example: create an asset linked to a hypothetical Revit element
        asset_data = {
            "items": [{
                "displayName": "Revit-Linked Asset (Tutorial Demo)",
                "description": "Linked to Revit externalId: a1b2c3d4-e5f6-7890",
                "clientAssetId": "tutorial-revit-demo-001"
            }]
        }

        print(f"  POST {url}")
        print(f"  Body: {json.dumps(asset_data, indent=2)}\n")

        status, data = _request("POST", url, headers=headers, body=asset_data)

        if status in (200, 201):
            print(f"  ✅ Revit-linked asset created!")
            results = data.get("results", [data] if "id" in data else [])
            if results:
                print(f"    ID: {results[0].get('id', 'N/A')}")
        else:
            print(f"  ✗ Failed! Status: {status}")
            print(f"    Response: {json.dumps(data, indent=2)[:300]}")

    print("\n  Complete Revit → ACC workflow in code:\n")
    print("    # 1. Upload .rvt and get URN")
    print("    # 2. Translate: POST /modelderivative/v2/designdata/job")
    print("    # 3. Poll: GET .../manifest until status == 'success'")
    print("    # 4. Get GUIDs: GET .../metadata")
    print("    # 5. Get props: GET .../metadata/{guid}/properties")
    print("    # 6. For each element:")
    print("    #    Create ACC asset with externalId as custom attribute")
    print("    #    → Now your assets are linked to the BIM model!")


# ══════════════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n🏗️  LESSON 8: Autodesk ACC Build — Two-Legged OAuth\n" + "─" * 50)

    print("\n  This lesson teaches you to authenticate with Autodesk's API")
    print("  and interact with ACC Build (projects, issues, RFIs,")
    print("  submittals, assets, and Revit model integration).\n")
    print("  ┌──────────────────────────────────────────────────────────┐")
    print("  │  Prerequisites:                                          │")
    print("  │  1. An Autodesk Platform Services (APS) app              │")
    print("  │     → Create at: https://aps.autodesk.com/myapps         │")
    print("  │  2. Set environment variables:                           │")
    print("  │     APS_CLIENT_ID=your_client_id                        │")
    print("  │     APS_CLIENT_SECRET=your_client_secret                │")
    print("  │  3. App must have ACC Build API access enabled           │")
    print("  └──────────────────────────────────────────────────────────┘")

    # Demo 1: Get access token
    token = demo_two_legged_auth()

    # Demo 2: List projects (returns first project ID)
    project_id = demo_list_projects(token)

    # Demo 3: List issues
    demo_list_issues(token, project_id)

    # Demo 4: Create an issue
    demo_create_issue(token, project_id)

    # Demo 5: List RFIs
    demo_list_rfis(token, project_id)

    # Demo 6: Submittals workflow
    demo_submittals(token, project_id)

    # Demo 7: Assets CRUD
    demo_assets(token, project_id)

    # Demo 8: Assets with Revit
    demo_revit_assets(token, project_id)

    # Summary
    print("\n\n💡 Key Concepts:")
    print("  • Two-legged OAuth: server-to-server, no user login needed")
    print("  • Auth URL: https://developer.api.autodesk.com/authentication/v2/token")
    print("  • Authorization header: Basic base64(client_id:client_secret)")
    print("  • Scopes control what your app can access (data:read, data:write, etc.)")
    print("  • Token expires in 3600s (1 hour) — cache and refresh before expiry")
    print("  • All ACC API calls use: Authorization: Bearer <access_token>")
    print("  • Submittals: draft → submitted → reviewed → approved/rejected")
    print("  • Assets use batch operations: batch-create, batch-patch, batch-delete")
    print("  • Revit integration: Model Derivative API → extract → link to assets")

    print("\n  ┌──────────────────────────────────────────────────────────────┐")
    print("  │  ACC Build API Endpoints:                                    │")
    print("  ├──────────────────────────────────────────────────────────────┤")
    print("  │  Auth:       POST /authentication/v2/token                   │")
    print("  │  Projects:   GET  /construction/admin/v1/projects            │")
    print("  │  Issues:     GET  /construction/issues/v1/.../issues         │")
    print("  │  Issues:     POST /construction/issues/v1/.../issues         │")
    print("  │  RFIs:       GET  /construction/rfis/v2/.../rfis             │")
    print("  │  Submittals: GET  /construction/submittals/v2/.../items      │")
    print("  │  Submittals: POST /construction/submittals/v2/.../items      │")
    print("  │  Assets:     POST .../assets/v2/.../assets:search            │")
    print("  │  Assets:     POST .../assets/v2/.../assets:batch-create      │")
    print("  │  Assets:     PATCH .../assets/v2/.../assets:batch-patch      │")
    print("  │  Assets:     POST .../assets/v2/.../assets:batch-delete      │")
    print("  │  Revit:      POST /modelderivative/v2/designdata/job         │")
    print("  │  Revit:      GET  .../designdata/{urn}/metadata/.../props    │")
    print("  └──────────────────────────────────────────────────────────────┘")

    print("\n" + "─" * 50)
    print("🎯 YOUR TURN — Exercises:")
    print("  1. Add token caching — store token and reuse until expired")
    print("  2. Build a full Revit→Asset pipeline with a real .rvt file")
    print("  3. Add pagination support — fetch all pages of results")
    print("  4. Create submittal templates and reuse them")
    print("  5. Add custom attributes to assets and search by them\n")


if __name__ == "__main__":
    main()
