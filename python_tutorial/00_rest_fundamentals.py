"""
╔══════════════════════════════════════════════════════════╗
║   LESSON 0: REST API Fundamentals                        ║
║                                                          ║
║   Learn:                                                 ║
║   • What REST APIs are and how they work                 ║
║   • All HTTP methods: GET, POST, PUT, PATCH, DELETE      ║
║   • Status codes, headers, and JSON payloads             ║
║   • Hands-on practice with a real public API             ║
║                                                          ║
║   Uses: https://jsonplaceholder.typicode.com (free)      ║
║   No API key needed!                                     ║
╚══════════════════════════════════════════════════════════╝

Run: python 00_rest_fundamentals.py
"""

import json

# We use Python's built-in urllib so there are NO dependencies for this lesson.
# In real projects you'd use the 'requests' library for cleaner code.
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = "https://jsonplaceholder.typicode.com"


# ── Helper ─────────────────────────────────────────────────────────────────────
def api_call(method: str, path: str, body: dict = None) -> tuple[int, dict | list | str]:
    """
    Make an HTTP request and return (status_code, parsed_json).
    Uses only Python standard library — no 'requests' needed.
    """
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body else None

    req = Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                result = raw
            return status, result
    except HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = raw
        return e.code, result


def print_request(method: str, path: str, body: dict = None):
    """Pretty-print what we're about to send."""
    print(f"\n  ──────────────────────────────────────────────")
    print(f"  📤 REQUEST:  {method} {BASE_URL}{path}")
    if body:
        print(f"  📦 BODY:     {json.dumps(body, indent=2)[:200]}")


def print_response(status: int, data, truncate: int = 300):
    """Pretty-print the response."""
    color = "✅" if 200 <= status < 300 else "⚠️" if 300 <= status < 400 else "❌"
    print(f"  📥 RESPONSE: {color} Status {status}")
    text = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
    if len(text) > truncate:
        text = text[:truncate] + f"\n  ... (truncated, {len(json.dumps(data, indent=2))} chars total)"
    for line in text.split("\n"):
        print(f"  {line}")


# ══════════════════════════════════════════════════════════════════════════════
#  CONCEPT: What is REST?
# ══════════════════════════════════════════════════════════════════════════════

def explain_rest():
    print("""
  ╔══════════════════════════════════════════════════════════════╗
  ║                    WHAT IS A REST API?                       ║
  ╚══════════════════════════════════════════════════════════════╝

  REST (Representational State Transfer) is a way to build web APIs using
  standard HTTP methods. Think of it like a menu at a restaurant:

  ┌───────────┬───────────────────┬──────────────────────────────┐
  │  Method   │  CRUD Operation   │  What It Does                │
  ├───────────┼───────────────────┼──────────────────────────────┤
  │  GET      │  Read             │  Fetch data (no changes)     │
  │  POST     │  Create           │  Create new data             │
  │  PUT      │  Update (full)    │  Replace entire resource     │
  │  PATCH    │  Update (partial) │  Update specific fields      │
  │  DELETE   │  Delete           │  Remove data                 │
  └───────────┴───────────────────┴──────────────────────────────┘

  Every REST API works with RESOURCES identified by URLs:

    GET    /users        → List all users
    GET    /users/1      → Get user #1
    POST   /users        → Create a new user
    PUT    /users/1      → Replace user #1 entirely
    PATCH  /users/1      → Update some fields of user #1
    DELETE /users/1      → Delete user #1

  The API returns HTTP STATUS CODES to tell you what happened:

  ┌───────────┬───────────────────────────────────────────────┐
  │  Code     │  Meaning                                      │
  ├───────────┼───────────────────────────────────────────────┤
  │  200 OK   │  Request succeeded                            │
  │  201 Created │  New resource created (after POST)          │
  │  204 No Content │  Success but no body (after DELETE)      │
  │  400 Bad Request │  Your request is malformed              │
  │  401 Unauthorized │  Invalid or missing credentials        │
  │  404 Not Found │  Resource doesn't exist                   │
  │  429 Rate Limit │  Too many requests, slow down            │
  │  500 Server Error │  Something broke on the server         │
  └───────────┴───────────────────────────────────────────────┘

  We'll practice ALL of these using JSONPlaceholder, a free fake REST API.
  No API key needed — just run this script!
""")


# ══════════════════════════════════════════════════════════════════════════════
#  1. GET — Read / Fetch Data
# ══════════════════════════════════════════════════════════════════════════════

def demo_get():
    print("\n" + "═" * 60)
    print("  📖 1. GET — Read Data")
    print("═" * 60)
    print("""
  GET is the most common HTTP method. It FETCHES data without
  changing anything on the server. It's safe to call repeatedly.

  Think: "Show me the data"
  """)

    # ── GET a list of resources ────────────────────────────────────────────
    print("  ── Example 1a: GET a list of posts ──")
    print_request("GET", "/posts?_limit=3")
    status, data = api_call("GET", "/posts?_limit=3")
    print_response(status, data)

    print(f"\n  → Got {len(data)} posts. Each has: id, title, body, userId")

    # ── GET a single resource by ID ────────────────────────────────────────
    print("\n  ── Example 1b: GET a single user by ID ──")
    print_request("GET", "/users/1")
    status, data = api_call("GET", "/users/1")
    print_response(status, data)

    print(f"\n  → Got user: {data['name']} ({data['email']})")

    # ── GET with query parameters (filtering) ──────────────────────────────
    print("\n  ── Example 1c: GET with query parameters (filter) ──")
    print_request("GET", "/posts?userId=1&_limit=2")
    status, data = api_call("GET", "/posts?userId=1&_limit=2")
    print_response(status, data)

    print(f"\n  → Filtered: only posts by userId=1 (got {len(data)} results)")

    # ── GET nested resources ───────────────────────────────────────────────
    print("\n  ── Example 1d: GET nested resources (comments on a post) ──")
    print_request("GET", "/posts/1/comments?_limit=2")
    status, data = api_call("GET", "/posts/1/comments?_limit=2")
    print_response(status, data)

    print(f"\n  → Got {len(data)} comments for post #1")

    print("""
  💡 GET Key Points:
     • Never changes data on the server (safe & idempotent)
     • Use query parameters (?key=value) for filtering, sorting, pagination
     • Returns 200 OK on success, 404 if resource doesn't exist
     • Response body contains the requested data as JSON
  """)


# ══════════════════════════════════════════════════════════════════════════════
#  2. POST — Create New Data
# ══════════════════════════════════════════════════════════════════════════════

def demo_post():
    print("\n" + "═" * 60)
    print("  📝 2. POST — Create New Data")
    print("═" * 60)
    print("""
  POST creates a NEW resource on the server. You send data in
  the request BODY, and the server returns the created resource
  (usually with a new ID assigned).

  Think: "Here's new data, please save it"
  """)

    # ── Create a new post ──────────────────────────────────────────────────
    print("  ── Example 2a: Create a new blog post ──")
    new_post = {
        "title": "My First API Post",
        "body": "I just learned how to use POST requests! REST APIs are awesome.",
        "userId": 1
    }
    print_request("POST", "/posts", new_post)
    status, data = api_call("POST", "/posts", new_post)
    print_response(status, data)

    print(f"\n  → Created! Server assigned id={data.get('id')}.")
    print(f"  → Status 201 = 'Created' (not 200)")

    # ── Create a new comment ───────────────────────────────────────────────
    print("\n  ── Example 2b: Create a comment on post #1 ──")
    new_comment = {
        "postId": 1,
        "name": "Great post!",
        "email": "learner@example.com",
        "body": "This tutorial helped me understand REST APIs."
    }
    print_request("POST", "/comments", new_comment)
    status, data = api_call("POST", "/comments", new_comment)
    print_response(status, data)

    # ── What the Claude API uses ───────────────────────────────────────────
    print("""
  💡 POST Key Points:
     • Sends data in the request BODY (as JSON)
     • Server returns 201 Created (or 200 OK)
     • Response usually contains the new resource with its assigned ID
     • NOT idempotent: calling POST twice creates TWO resources
     • The Claude API uses POST for /v1/messages — every message is a "create"

  💡 Claude API Connection:
     When you call client.messages.create(), it sends a POST request:

        POST https://api.anthropic.com/v1/messages
        Body: { "model": "...", "max_tokens": ..., "messages": [...] }
  """)


# ══════════════════════════════════════════════════════════════════════════════
#  3. PUT — Replace / Update Entire Resource
# ══════════════════════════════════════════════════════════════════════════════

def demo_put():
    print("\n" + "═" * 60)
    print("  🔄 3. PUT — Replace Entire Resource")
    print("═" * 60)
    print("""
  PUT REPLACES an entire resource with new data. You must send
  ALL fields — any field you omit will be removed/reset.

  Think: "Replace everything about this resource with this new version"
  """)

    # ── First, let's see the original ──────────────────────────────────────
    print("  ── Step 1: Get the original post #1 ──")
    print_request("GET", "/posts/1")
    status, original = api_call("GET", "/posts/1")
    print_response(status, original)

    # ── Now PUT (replace) it ───────────────────────────────────────────────
    print("\n  ── Step 2: PUT (replace) post #1 with completely new data ──")
    updated_post = {
        "id": 1,
        "title": "Updated: REST API Mastery",
        "body": "I now understand GET, POST, PUT, and DELETE!",
        "userId": 1
    }
    print_request("PUT", "/posts/1", updated_post)
    status, data = api_call("PUT", "/posts/1", updated_post)
    print_response(status, data)

    print(f"\n  → Post #1 fully replaced.")
    print(f"  → Old title: \"{original['title'][:40]}...\"")
    print(f"  → New title: \"{data['title']}\"")

    print("""
  💡 PUT Key Points:
     • Replaces the ENTIRE resource (all fields)
     • If you omit a field, it's treated as blank/null
     • Idempotent: calling PUT twice with same data = same result
     • Returns 200 OK on success
     • Use PUT when you have the complete updated version of a resource

  ⚠️  PUT vs POST:
     • POST = Create NEW resource (server assigns ID)
     • PUT  = Replace EXISTING resource (you specify the ID)
  """)


# ══════════════════════════════════════════════════════════════════════════════
#  4. PATCH — Partial Update
# ══════════════════════════════════════════════════════════════════════════════

def demo_patch():
    print("\n" + "═" * 60)
    print("  ✏️  4. PATCH — Partial Update")
    print("═" * 60)
    print("""
  PATCH updates ONLY the fields you specify. Everything else
  stays the same. It's like editing one cell in a spreadsheet.

  Think: "Change just these specific fields"
  """)

    # ── First, see the original ────────────────────────────────────────────
    print("  ── Step 1: Get original post #1 ──")
    print_request("GET", "/posts/1")
    status, original = api_call("GET", "/posts/1")
    print_response(status, original)

    # ── PATCH: update only the title ───────────────────────────────────────
    print("\n  ── Step 2: PATCH — only change the title ──")
    patch_data = {
        "title": "PATCHED: Just the Title Changed"
    }
    print_request("PATCH", "/posts/1", patch_data)
    status, data = api_call("PATCH", "/posts/1", patch_data)
    print_response(status, data)

    print(f"\n  → Only 'title' changed. 'body' and 'userId' are untouched.")
    print(f"  → Old title: \"{original['title'][:40]}...\"")
    print(f"  → New title: \"{data['title']}\"")
    print(f"  → Body still: \"{data['body'][:40]}...\"  (unchanged!)")

    print("""
  💡 PATCH Key Points:
     • Updates ONLY the fields you send
     • Other fields remain unchanged
     • More efficient than PUT for small changes
     • Returns 200 OK with the updated resource

  ⚠️  PATCH vs PUT:
     • PUT   = Send ALL fields → replaces everything
     • PATCH = Send SOME fields → changes only those
     • Use PATCH when you want to update one or two fields
     • Use PUT when you want to replace the whole resource
  """)


# ══════════════════════════════════════════════════════════════════════════════
#  5. DELETE — Remove a Resource
# ══════════════════════════════════════════════════════════════════════════════

def demo_delete():
    print("\n" + "═" * 60)
    print("  🗑️  5. DELETE — Remove a Resource")
    print("═" * 60)
    print("""
  DELETE removes a resource from the server. Usually returns
  an empty response (204 No Content) or confirmation (200 OK).

  Think: "Remove this resource permanently"
  """)

    # ── Verify the resource exists ─────────────────────────────────────────
    print("  ── Step 1: Verify post #1 exists ──")
    print_request("GET", "/posts/1")
    status, data = api_call("GET", "/posts/1")
    print_response(status, data)
    print(f"\n  → Post exists! (status {status})")

    # ── DELETE it ──────────────────────────────────────────────────────────
    print("\n  ── Step 2: DELETE post #1 ──")
    print_request("DELETE", "/posts/1")
    status, data = api_call("DELETE", "/posts/1")
    print_response(status, data)
    print(f"\n  → Deleted! (status {status})")

    # ── Try to GET the deleted resource ────────────────────────────────────
    print("\n  ── Step 3: Try to GET the deleted post ──")
    print("  (Note: JSONPlaceholder is a mock API, so it still returns data.)")
    print("  In a real API, this would return 404 Not Found.")

    print("""
  💡 DELETE Key Points:
     • Removes the resource at the specified URL
     • Usually returns 200 OK or 204 No Content
     • Idempotent: deleting something twice = same result
     • In real APIs, a GET after DELETE returns 404

  ⚠️  Caution:
     • DELETE is irreversible — always confirm before deleting
     • Some APIs use "soft delete" (mark as deleted, don't actually remove)
     • Always check permissions before allowing delete operations
  """)


# ══════════════════════════════════════════════════════════════════════════════
#  6. Headers, Status Codes & Real-World Patterns
# ══════════════════════════════════════════════════════════════════════════════

def demo_headers_and_patterns():
    print("\n" + "═" * 60)
    print("  📋 6. Headers, Status Codes & Real-World Patterns")
    print("═" * 60)
    print("""
  ── HTTP Headers ──────────────────────────────────────────

  Headers are key-value pairs sent with every request/response:

  ┌──────────────────────────┬──────────────────────────────┐
  │  Common Request Headers  │  What It Does                │
  ├──────────────────────────┼──────────────────────────────┤
  │  Content-Type            │  Format of your data         │
  │    application/json      │    → JSON body               │
  │  Authorization           │  Your credentials            │
  │    Bearer <token>        │    → OAuth token             │
  │  x-api-key              │  API key (Anthropic uses this)│
  │  Accept                  │  Desired response format     │
  └──────────────────────────┴──────────────────────────────┘

  ┌──────────────────────────┬──────────────────────────────┐
  │  Common Response Headers │  What It Tells You           │
  ├──────────────────────────┼──────────────────────────────┤
  │  Content-Type            │  Format of response data     │
  │  X-RateLimit-Remaining   │  How many requests left      │
  │  Retry-After             │  When to retry (seconds)     │
  └──────────────────────────┴──────────────────────────────┘

  ── Status Code Families ──────────────────────────────────

  • 1xx — Informational (rare)
  • 2xx — Success    ✅  (200 OK, 201 Created, 204 No Content)
  • 3xx — Redirect   ↗️  (301 Moved, 304 Not Modified)
  • 4xx — Client Error ❌ (400 Bad Request, 401, 403, 404, 429)
  • 5xx — Server Error 💥 (500, 502, 503, 529)

  Rule of thumb: if it starts with 4, YOUR code is wrong.
                 if it starts with 5, the SERVER has a problem.

  ── Real-World REST Patterns ──────────────────────────────

  1. Pagination:
     GET /posts?page=2&per_page=10
     GET /posts?offset=20&limit=10

  2. Sorting:
     GET /posts?sort=created_at&order=desc

  3. Filtering:
     GET /posts?status=published&author=alice

  4. Authentication:
     Header: Authorization: Bearer <your-token>
     Header: x-api-key: <your-key>      (Anthropic uses this)

  5. Versioning:
     URL:    https://api.example.com/v1/users
     Header: anthropic-version: 2023-06-01  (Anthropic uses this)
  """)


# ══════════════════════════════════════════════════════════════════════════════
#  7. Full CRUD Cycle (Create → Read → Update → Delete)
# ══════════════════════════════════════════════════════════════════════════════

def demo_full_crud():
    print("\n" + "═" * 60)
    print("  🔁 7. Full CRUD Cycle — Putting It All Together")
    print("═" * 60)
    print("""
  Let's walk through a complete lifecycle of a resource:
  CREATE (POST) → READ (GET) → UPDATE (PATCH) → DELETE
  """)

    # ── CREATE ─────────────────────────────────────────────────────────────
    print("  STEP 1: CREATE a new todo item (POST)")
    new_todo = {
        "title": "Learn REST APIs",
        "completed": False,
        "userId": 1
    }
    print_request("POST", "/todos", new_todo)
    status, created = api_call("POST", "/todos", new_todo)
    print_response(status, created)
    todo_id = created.get("id", 201)
    print(f"  → Created todo #{todo_id}\n")

    # ── READ ───────────────────────────────────────────────────────────────
    print(f"  STEP 2: READ the todo back (GET)")
    print_request("GET", f"/todos/{todo_id}")
    status, fetched = api_call("GET", f"/todos/{todo_id}")
    # JSONPlaceholder might not have this ID, so use our created data
    if status == 404:
        print(f"  📥 RESPONSE: ✅ Status 200 (simulated)")
        print(f"  {json.dumps(created, indent=2)}")
    else:
        print_response(status, fetched)
    print(f"  → Fetched: \"{created['title']}\" (completed: {created['completed']})\n")

    # ── UPDATE ─────────────────────────────────────────────────────────────
    print(f"  STEP 3: UPDATE — mark as completed (PATCH)")
    update = {"completed": True}
    print_request("PATCH", f"/todos/1", update)  # Use /1 since mock API
    status, updated = api_call("PATCH", "/todos/1", update)
    print_response(status, updated)
    print(f"  → Updated completed: False → True\n")

    # ── DELETE ─────────────────────────────────────────────────────────────
    print(f"  STEP 4: DELETE the todo (DELETE)")
    print_request("DELETE", f"/todos/1")
    status, deleted = api_call("DELETE", "/todos/1")
    print_response(status, deleted)
    print(f"  → Deleted!\n")

    print("""  ╔══════════════════════════════════════════════════════════════╗
  ║  CRUD SUMMARY                                               ║
  ║                                                              ║
  ║  Create → POST   /resource      → 201 Created               ║
  ║  Read   → GET    /resource/:id  → 200 OK                    ║
  ║  Update → PATCH  /resource/:id  → 200 OK                    ║
  ║  Replace→ PUT    /resource/:id  → 200 OK                    ║
  ║  Delete → DELETE /resource/:id  → 200 OK / 204 No Content   ║
  ╚══════════════════════════════════════════════════════════════╝
  """)


# ══════════════════════════════════════════════════════════════════════════════
#  8. Connecting to the Claude API
# ══════════════════════════════════════════════════════════════════════════════

def demo_claude_connection():
    print("\n" + "═" * 60)
    print("  🤖 8. How This Connects to the Claude API")
    print("═" * 60)
    print("""
  The Claude API is a REST API that primarily uses POST:

  ┌───────────────────────────────────────────────────────────┐
  │  Claude API Endpoints                                     │
  ├───────────────────────────────────────────────────────────┤
  │                                                           │
  │  POST /v1/messages          ← Send a message to Claude    │
  │  POST /v1/messages/batches  ← Create a batch of messages  │
  │  GET  /v1/messages/batches/:id  ← Check batch status      │
  │  POST /v1/messages/count_tokens ← Count tokens            │
  │  POST /v1/files             ← Upload a file               │
  │  GET  /v1/files             ← List your files             │
  │  GET  /v1/files/:id         ← Get file metadata           │
  │  DELETE /v1/files/:id       ← Delete a file               │
  │                                                           │
  └───────────────────────────────────────────────────────────┘

  Authentication:
    Header: x-api-key: sk-ant-...
    Header: anthropic-version: 2023-06-01

  When you write:

    client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}]
    )

  The SDK sends this HTTP request under the hood:

    POST https://api.anthropic.com/v1/messages
    Headers:
      Content-Type: application/json
      x-api-key: sk-ant-...
      anthropic-version: 2023-06-01
    Body:
      {
        "model": "claude-opus-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "Hello!"}]
      }

  Now that you understand REST, the Claude API lessons will
  make much more sense! Proceed to 01_basic_message.py →
  """)


# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n📡 LESSON 0: REST API Fundamentals")
    print("─" * 60)
    print("  Using: https://jsonplaceholder.typicode.com (free, no key needed)")
    print("  This lesson teaches ALL HTTP methods with live API calls.\n")

    explain_rest()

    input("  Press Enter to start the demos...\n")

    # Run all demos
    demo_get()
    demo_post()
    demo_put()
    demo_patch()
    demo_delete()
    demo_headers_and_patterns()
    demo_full_crud()
    demo_claude_connection()

    # Final summary
    print("═" * 60)
    print("  🎓 LESSON 0 COMPLETE!")
    print("═" * 60)
    print("""
  You now understand:
  ✅ GET    — Fetch data (read-only)
  ✅ POST   — Create new data (send body)
  ✅ PUT    — Replace entire resource (send all fields)
  ✅ PATCH  — Update specific fields (send only changes)
  ✅ DELETE — Remove a resource
  ✅ Status codes, headers, and authentication
  ✅ How the Claude API maps to REST concepts

  🎯 YOUR TURN — Exercises:
  1. Try fetching users:   GET /users
  2. Try fetching albums:  GET /albums?userId=1
  3. Create your own todo: POST /todos with your own title
  4. Update a user's name: PATCH /users/1 with {"name": "Your Name"}
  5. Install 'requests' library and rewrite one demo with it

  Ready for Claude? → python 01_basic_message.py
  """)


if __name__ == "__main__":
    main()
