/**
 * ╔══════════════════════════════════════════════════════════╗
 * ║   LESSON 8: Autodesk ACC Build — Two-Legged OAuth        ║
 * ║                                                          ║
 * ║   Learn:                                                 ║
 * ║   • Two-legged OAuth 2.0 authentication flow             ║
 * ║   • Getting an access token with client credentials      ║
 * ║   • Listing ACC Build projects                           ║
 * ║   • Working with Issues (list + create)                  ║
 * ║   • Working with RFIs                                    ║
 * ║                                                          ║
 * ║   Uses Node.js 18+ built-in fetch (no extra deps).       ║
 * ║   Set APS_CLIENT_ID and APS_CLIENT_SECRET in .env        ║
 * ╚══════════════════════════════════════════════════════════╝
 *
 * Run: node 08_autodesk_acc.js
 */

import { config } from 'dotenv';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: join(__dirname, '..', '.env') });

// ══════════════════════════════════════════════════════════════════════════════
//  Configuration
// ══════════════════════════════════════════════════════════════════════════════

const APS_AUTH_URL = 'https://developer.api.autodesk.com/authentication/v2/token';
const APS_BASE_URL = 'https://developer.api.autodesk.com';
const CLIENT_ID = process.env.APS_CLIENT_ID || '';
const CLIENT_SECRET = process.env.APS_CLIENT_SECRET || '';

async function apsRequest(method, url, headers = {}, body = null) {
  const options = { method, headers };
  if (body !== null) {
    if (typeof body === 'string') {
      options.body = body;
    } else {
      options.body = JSON.stringify(body);
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }
  }
  const resp = await fetch(url, options);
  const text = await resp.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  return { status: resp.status, data };
}

// ══════════════════════════════════════════════════════════════════════════════
//  STEP 1: Two-Legged OAuth — Get Access Token
// ══════════════════════════════════════════════════════════════════════════════

async function demoTwoLeggedAuth() {
  console.log('\n📋 Demo 1: Two-Legged OAuth 2.0 Authentication\n');

  console.log('  Two-legged OAuth is for server-to-server communication.');
  console.log('  No user login is needed — your app authenticates with its own credentials.\n');

  console.log('  ┌─────────────────────────────────────────────────────────────────┐');
  console.log('  │  TWO-LEGGED OAUTH FLOW                                         │');
  console.log('  ├─────────────────────────────────────────────────────────────────┤');
  console.log('  │                                                                 │');
  console.log('  │  Your Server                  Autodesk Auth Server              │');
  console.log('  │      │                              │                           │');
  console.log('  │      │  POST /authentication/v2/token                           │');
  console.log('  │      │  Authorization: Basic base64(id:secret)                  │');
  console.log('  │      │  Body: grant_type=client_credentials&scope=...           │');
  console.log('  │      │─────────────────────────────►│                           │');
  console.log('  │      │                              │                           │');
  console.log('  │      │  { access_token, expires_in, token_type }                │');
  console.log('  │      │◄─────────────────────────────│                           │');
  console.log('  │      │                              │                           │');
  console.log('  │  Use access_token as Bearer token for all ACC API calls         │');
  console.log('  │                                                                 │');
  console.log('  └─────────────────────────────────────────────────────────────────┘\n');

  if (!CLIENT_ID || !CLIENT_SECRET) {
    console.log('  ⚠  APS_CLIENT_ID and APS_CLIENT_SECRET not set.');
    console.log('     Set them in your .env file or environment variables.');
    console.log('     Get credentials at: https://aps.autodesk.com/myapps\n');
    console.log('  Here\'s what the request would look like:\n');
    console.log('    POST https://developer.api.autodesk.com/authentication/v2/token');
    console.log('    Authorization: Basic <base64(client_id:client_secret)>');
    console.log('    Content-Type: application/x-www-form-urlencoded');
    console.log('    Body: grant_type=client_credentials&scope=data:read data:write\n');
    console.log('    Expected response:');
    console.log('    { "access_token": "eyJ...", "expires_in": 3600, "token_type": "Bearer" }\n');
    return null;
  }

  const b64 = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64');
  const scopes = 'data:read data:write data:create account:read';
  const body = `grant_type=client_credentials&scope=${encodeURIComponent(scopes)}`;

  console.log('  Requesting access token...');
  console.log(`    POST ${APS_AUTH_URL}`);
  console.log('    Authorization: Basic <base64(client_id:client_secret)>');
  console.log(`    Scopes: ${scopes}\n`);

  const { status, data } = await apsRequest('POST', APS_AUTH_URL, {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': `Basic ${b64}`
  }, body);

  if (status === 200 && data.access_token) {
    console.log('  ✅ Token received!');
    console.log(`    Token (first 40 chars): ${data.access_token.substring(0, 40)}...`);
    console.log(`    Expires in: ${data.expires_in} seconds (${Math.floor(data.expires_in / 60)} minutes)`);
    console.log(`    Token type: ${data.token_type || 'Bearer'}`);
    return data.access_token;
  } else {
    console.log(`  ✗ Authentication failed! Status: ${status}`);
    console.log(`    Response: ${JSON.stringify(data, null, 2).substring(0, 300)}`);
    return null;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  STEP 2: List ACC Build Projects
// ══════════════════════════════════════════════════════════════════════════════

async function demoListProjects(token) {
  console.log('\n\n📋 Demo 2: List ACC Build Projects\n');

  if (!token) {
    console.log('  ⚠  No token available. Showing expected request format.\n');
    console.log('    GET https://developer.api.autodesk.com/construction/admin/v1/projects');
    console.log('    Authorization: Bearer <access_token>\n');
    console.log('    Expected response:');
    console.log('    {');
    console.log('      "pagination": { "limit": 20, "offset": 0, "totalResults": 5 },');
    console.log('      "results": [');
    console.log('        { "id": "abc-123", "name": "Project Alpha", "status": "active" }');
    console.log('      ]');
    console.log('    }\n');
    return null;
  }

  const url = `${APS_BASE_URL}/construction/admin/v1/projects`;
  console.log(`  GET ${url}`);
  console.log('  Authorization: Bearer <token>\n');

  const { status, data } = await apsRequest('GET', url, {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  });

  if (status === 200) {
    const results = data.results || [];
    const total = data.pagination?.totalResults ?? results.length;
    console.log(`  ✅ Found ${total} project(s)\n`);

    for (let i = 0; i < Math.min(results.length, 5); i++) {
      const proj = results[i];
      console.log(`    ${i + 1}. ${proj.name || 'Unnamed'}`);
      console.log(`       ID:     ${proj.id || 'N/A'}`);
      console.log(`       Status: ${proj.status || 'N/A'}`);
      console.log(`       Type:   ${proj.type || 'N/A'}\n`);
    }
    if (total > 5) console.log(`    ... and ${total - 5} more project(s)`);
    return results[0]?.id || null;
  } else {
    console.log(`  ✗ Failed! Status: ${status}`);
    console.log(`    Response: ${JSON.stringify(data, null, 2).substring(0, 300)}`);
    return null;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  STEP 3: List Issues
// ══════════════════════════════════════════════════════════════════════════════

async function demoListIssues(token, projectId) {
  console.log('\n\n📋 Demo 3: List Project Issues\n');

  if (!token || !projectId) {
    console.log('  ⚠  No token or project ID. Showing expected request format.\n');
    console.log('    GET https://developer.api.autodesk.com/construction/issues/v1/projects/{projectId}/issues');
    console.log('    Authorization: Bearer <access_token>\n');
    console.log('    Expected response:');
    console.log('    {');
    console.log('      "results": [');
    console.log('        { "id": "issue-001", "title": "Concrete crack", "status": "open" }');
    console.log('      ]');
    console.log('    }\n');
    return;
  }

  const url = `${APS_BASE_URL}/construction/issues/v1/projects/${projectId}/issues`;
  console.log(`  GET ${url}`);
  console.log('  Authorization: Bearer <token>\n');

  const { status, data } = await apsRequest('GET', url, {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  });

  if (status === 200) {
    const results = data.results || [];
    const total = data.pagination?.totalResults ?? results.length;
    console.log(`  ✅ Found ${total} issue(s)\n`);

    for (let i = 0; i < Math.min(results.length, 5); i++) {
      const issue = results[i];
      console.log(`    ${i + 1}. ${issue.title || 'Untitled'}`);
      console.log(`       ID:     ${issue.id || 'N/A'}`);
      console.log(`       Status: ${issue.status || 'N/A'}`);
      console.log(`       Type:   ${issue.issueType || 'N/A'}\n`);
    }
  } else {
    console.log(`  ✗ Failed! Status: ${status}`);
    console.log(`    Response: ${JSON.stringify(data, null, 2).substring(0, 300)}`);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  STEP 4: Create an Issue
// ══════════════════════════════════════════════════════════════════════════════

async function demoCreateIssue(token, projectId) {
  console.log('\n\n📋 Demo 4: Create a New Issue\n');

  if (!token || !projectId) {
    console.log('  ⚠  No token or project ID. Showing expected request format.\n');
    console.log('    POST https://developer.api.autodesk.com/construction/issues/v1/projects/{projectId}/issues');
    console.log('    Authorization: Bearer <access_token>');
    console.log('    Content-Type: application/json\n');
    console.log('    Body: { "title": "Safety railing missing", "status": "open" }\n');
    console.log('    Expected response (201 Created):');
    console.log('    { "id": "new-issue-789", "title": "Safety railing missing", "status": "open" }\n');
    return;
  }

  const url = `${APS_BASE_URL}/construction/issues/v1/projects/${projectId}/issues`;
  const issueData = {
    title: 'Tutorial Test Issue — Safe to Delete',
    description: 'This issue was created by the API tutorial script. You can safely delete it.',
    status: 'open'
  };

  console.log(`  POST ${url}`);
  console.log(`  Body: ${JSON.stringify(issueData, null, 2)}\n`);

  const { status, data } = await apsRequest('POST', url, {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }, issueData);

  if (status === 200 || status === 201) {
    console.log('  ✅ Issue created!');
    console.log(`    ID:      ${data.id || 'N/A'}`);
    console.log(`    Title:   ${data.title || 'N/A'}`);
    console.log(`    Status:  ${data.status || 'N/A'}`);
  } else {
    console.log(`  ✗ Failed! Status: ${status}`);
    console.log(`    Response: ${JSON.stringify(data, null, 2).substring(0, 300)}`);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  STEP 5: List RFIs
// ══════════════════════════════════════════════════════════════════════════════

async function demoListRfis(token, projectId) {
  console.log('\n\n📋 Demo 5: List RFIs (Requests for Information)\n');

  if (!token || !projectId) {
    console.log('  ⚠  No token or project ID. Showing expected request format.\n');
    console.log('    GET https://developer.api.autodesk.com/construction/rfis/v2/projects/{projectId}/rfis');
    console.log('    Authorization: Bearer <access_token>\n');
    console.log('    Expected response:');
    console.log('    {');
    console.log('      "results": [');
    console.log('        { "id": "rfi-001", "title": "Beam specs clarification", "status": "open" }');
    console.log('      ]');
    console.log('    }\n');
    return;
  }

  const url = `${APS_BASE_URL}/construction/rfis/v2/projects/${projectId}/rfis`;
  console.log(`  GET ${url}`);
  console.log('  Authorization: Bearer <token>\n');

  const { status, data } = await apsRequest('GET', url, {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  });

  if (status === 200) {
    const results = data.results || [];
    const total = data.pagination?.totalResults ?? results.length;
    console.log(`  ✅ Found ${total} RFI(s)\n`);

    for (let i = 0; i < Math.min(results.length, 5); i++) {
      const rfi = results[i];
      console.log(`    ${i + 1}. ${rfi.title || 'Untitled'}`);
      console.log(`       ID:       ${rfi.id || 'N/A'}`);
      console.log(`       Status:   ${rfi.status || 'N/A'}`);
      console.log(`       Priority: ${rfi.priority || 'N/A'}\n`);
    }
  } else {
    console.log(`  ✗ Failed! Status: ${status}`);
    console.log(`    Response: ${JSON.stringify(data, null, 2).substring(0, 300)}`);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  STEP 6: Submittals — Full Workflow
// ══════════════════════════════════════════════════════════════════════════════

async function demoSubmittals(token, projectId) {
  console.log('\n\n📋 Demo 6: Submittals — Full Workflow\n');
  console.log('  Submittals are formal document submissions for review/approval.');
  console.log('  Workflow: draft → submitted → reviewed → approved/rejected\n');

  const baseUrl = projectId ? `${APS_BASE_URL}/construction/submittals/v2/projects/${projectId}` : null;

  // 6a: List submittals
  console.log('  ─── 6a: List Submittals ───\n');
  if (!token || !projectId) {
    console.log('  ⚠  No token/project. Expected format:');
    console.log('    GET .../submittals/v2/projects/{projectId}/items');
    console.log('    Response: { results: [{ id, title, status }] }\n');
  } else {
    const { status, data } = await apsRequest('GET', `${baseUrl}/items`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    });
    if (status === 200) {
      const results = data.results || [];
      console.log(`  ✅ Found ${data.pagination?.totalResults ?? results.length} submittal(s)\n`);
      results.slice(0, 5).forEach((s, i) => {
        console.log(`    ${i+1}. ${s.title || 'Untitled'} — Status: ${s.status}`);
      });
    } else {
      console.log(`  ✗ Failed! Status: ${status}`);
    }
  }

  // 6b: Create submittal
  console.log('\n  ─── 6b: Create Submittal (draft) ───\n');
  let submittalId = null;
  if (!token || !projectId) {
    console.log('    POST .../items');
    console.log('    Body: { "title": "Shop Drawings — HVAC", "status": "draft" }\n');
  } else {
    const body = { title: 'Tutorial Test Submittal — Safe to Delete', description: 'Created by tutorial.', status: 'draft' };
    const { status, data } = await apsRequest('POST', `${baseUrl}/items`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    }, body);
    if (status === 200 || status === 201) {
      submittalId = data.id;
      console.log(`  ✅ Created! ID: ${data.id}, Status: ${data.status}`);
    } else {
      console.log(`  ✗ Failed! Status: ${status}`);
    }
  }

  // 6c: Submit for review
  console.log('\n  ─── 6c: Submit for Review ───\n');
  if (!token || !submittalId) {
    console.log('    POST .../items/{itemId}:transition');
    console.log('    Body: { "toState": "submitted" }\n');
  } else {
    const { status, data } = await apsRequest('POST', `${baseUrl}/items/${submittalId}:transition`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    }, { toState: 'submitted' });
    if (status === 200 || status === 201) {
      console.log(`  ✅ Submitted! New status: ${data.status || 'submitted'}`);
    } else {
      console.log(`  ✗ Transition failed: ${status}`);
    }
  }

  // 6d: Check status
  console.log('\n  ─── 6d: Check Approval Status ───\n');
  if (!token || !submittalId) {
    console.log('    GET .../items/{itemId}');
    console.log('    Returns: id, title, status, reviewers, responses\n');
  } else {
    const { status, data } = await apsRequest('GET', `${baseUrl}/items/${submittalId}`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    });
    if (status === 200) {
      console.log(`  ✅ Status: ${data.status}, Title: ${data.title}`);
    } else {
      console.log(`  ✗ Failed! Status: ${status}`);
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  STEP 7: Assets — Full CRUD
// ══════════════════════════════════════════════════════════════════════════════

async function demoAssets(token, projectId) {
  console.log('\n\n📋 Demo 7: Assets — Full CRUD\n');
  console.log('  Assets track physical equipment, materials, and components.\n');

  const assetsBase = projectId ? `${APS_BASE_URL}/construction/assets/v2/projects/${projectId}` : null;

  // 7a: List categories
  console.log('  ─── 7a: List Asset Categories ───\n');
  let categoryId = null;
  if (!token || !projectId) {
    console.log('    GET .../assets/v2/projects/{projectId}/categories');
    console.log('    Response: [{ id, name, parentId }]\n');
  } else {
    const { status, data } = await apsRequest('GET', `${assetsBase}/categories`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    });
    if (status === 200) {
      const cats = Array.isArray(data) ? data : (data.results || []);
      console.log(`  ✅ Found ${cats.length} categor(ies)\n`);
      cats.slice(0, 5).forEach((c, i) => console.log(`    ${i+1}. ${c.name || 'Unnamed'} (ID: ${c.id})`));
      categoryId = cats[0]?.id || null;
    } else {
      console.log(`  ✗ Failed! Status: ${status}`);
    }
  }

  // 7b: List assets
  console.log('\n  ─── 7b: List Assets ───\n');
  if (!token || !projectId) {
    console.log('    POST .../assets:search');
    console.log('    Body: {}');
    console.log('    Response: { results: [{ id, displayName, categoryId }] }\n');
  } else {
    const { status, data } = await apsRequest('POST', `${assetsBase}/assets:search`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    }, {});
    if (status === 200) {
      const results = data.results || [];
      console.log(`  ✅ Found ${results.length} asset(s)\n`);
      results.slice(0, 5).forEach((a, i) => console.log(`    ${i+1}. ${a.displayName || 'Unnamed'} (ID: ${a.id})`));
    } else {
      console.log(`  ✗ Failed! Status: ${status}`);
    }
  }

  // 7c: Create asset
  console.log('\n  ─── 7c: Create Asset ───\n');
  let createdAssetId = null;
  if (!token || !projectId) {
    console.log('    POST .../assets:batch-create');
    console.log('    Body: { items: [{ displayName: "HVAC Unit", categoryId: "..." }] }\n');
  } else {
    const item = { displayName: 'Tutorial Test Asset — Safe to Delete', description: 'Created by tutorial.' };
    if (categoryId) item.categoryId = categoryId;
    const { status, data } = await apsRequest('POST', `${assetsBase}/assets:batch-create`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    }, { items: [item] });
    if (status === 200 || status === 201) {
      const results = data.results || (data.id ? [data] : []);
      createdAssetId = results[0]?.id;
      console.log(`  ✅ Created! ID: ${createdAssetId}, Name: ${results[0]?.displayName || 'N/A'}`);
    } else {
      console.log(`  ✗ Failed! Status: ${status}`);
    }
  }

  // 7d: Update asset
  console.log('\n  ─── 7d: Update Asset ───\n');
  if (!token || !createdAssetId) {
    console.log('    PATCH .../assets:batch-patch');
    console.log('    Body: { items: [{ id: "...", displayName: "Updated Name" }] }\n');
  } else {
    const { status } = await apsRequest('PATCH', `${assetsBase}/assets:batch-patch`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    }, { items: [{ id: createdAssetId, displayName: 'Tutorial Asset (Updated)' }] });
    console.log(status === 200 ? '  ✅ Asset updated!' : `  ✗ Failed! Status: ${status}`);
  }

  // 7e: Delete asset
  console.log('\n  ─── 7e: Delete Asset ───\n');
  if (!token || !createdAssetId) {
    console.log('    POST .../assets:batch-delete');
    console.log('    Body: { ids: ["asset-id"] }\n');
  } else {
    const { status } = await apsRequest('POST', `${assetsBase}/assets:batch-delete`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    }, { ids: [createdAssetId] });
    console.log(status === 200 || status === 204 ? '  ✅ Asset deleted!' : `  ✗ Failed! Status: ${status}`);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
//  STEP 8: Assets with Revit — Extract & Link
// ══════════════════════════════════════════════════════════════════════════════

async function demoRevitAssets(token, projectId) {
  console.log('\n\n📋 Demo 8: Assets with Revit — Extract & Link\n');
  console.log('  Extract element data from Revit (.rvt) files using Model Derivative API,');
  console.log('  then link elements to ACC assets via custom attributes.\n');

  console.log('  ┌──────────────────────────────────────────────────────────────────┐');
  console.log('  │  REVIT → ACC ASSET WORKFLOW                                      │');
  console.log('  ├──────────────────────────────────────────────────────────────────┤');
  console.log('  │  1. Upload .rvt file → get URN                                  │');
  console.log('  │  2. POST /modelderivative/v2/designdata/job → translate         │');
  console.log('  │  3. GET  .../designdata/{urn}/manifest → poll until success     │');
  console.log('  │  4. GET  .../designdata/{urn}/metadata → get GUIDs             │');
  console.log('  │  5. GET  .../metadata/{guid}/properties → element data         │');
  console.log('  │  6. Create ACC assets with revitElementId custom attribute      │');
  console.log('  └──────────────────────────────────────────────────────────────────┘\n');

  // 8a: Translation job
  console.log('  ─── 8a: Submit Translation Job ───\n');
  console.log('    POST https://developer.api.autodesk.com/modelderivative/v2/designdata/job');
  console.log('    Body:');
  console.log('    {');
  console.log('      "input": { "urn": "<base64-urn>", "rootFilename": "model.rvt" },');
  console.log('      "output": { "formats": [{ "type": "svf2", "views": ["2d","3d"] }] }');
  console.log('    }');
  console.log('    Response: { result: "created", urn: "..." }\n');

  // 8b: Check status
  console.log('  ─── 8b: Check Translation Status ───\n');
  console.log('    GET .../designdata/{urn}/manifest');
  console.log('    Response: { status: "success", progress: "complete" }');
  console.log('    Status values: pending → inprogress → success | failed\n');

  // 8c: Extract properties
  console.log('  ─── 8c: Extract Revit Element Properties ───\n');
  console.log('    GET .../designdata/{urn}/metadata → { data: { metadata: [{ guid }] } }');
  console.log('    GET .../designdata/{urn}/metadata/{guid}/properties');
  console.log('    Response element:');
  console.log('    {');
  console.log('      "objectid": 12345,');
  console.log('      "name": "HVAC Supply Duct [654321]",');
  console.log('      "externalId": "a1b2c3d4-e5f6-...",');
  console.log('      "properties": {');
  console.log('        "Dimensions": { "Width": "600 mm", "Height": "400 mm" },');
  console.log('        "Identity Data": { "Type Name": "Rectangular Duct" }');
  console.log('      }');
  console.log('    }\n');

  // 8d: Link to ACC assets
  console.log('  ─── 8d: Link Revit Elements to ACC Assets ───\n');
  if (!token || !projectId) {
    console.log('    POST .../assets:batch-create');
    console.log('    Body: {');
    console.log('      items: [{');
    console.log('        displayName: "HVAC Supply Duct - Floor 3",');
    console.log('        clientAssetId: "a1b2c3d4-e5f6-...",  // Revit externalId');
    console.log('        customAttributes: [');
    console.log('          { attributeDefinitionId: "revit-elem-attr", value: "a1b2c3d4-..." },');
    console.log('          { attributeDefinitionId: "revit-type-attr", value: "Rectangular Duct" }');
    console.log('        ]');
    console.log('      }]');
    console.log('    }\n');
  } else {
    const assetsBase = `${APS_BASE_URL}/construction/assets/v2/projects/${projectId}`;
    const body = {
      items: [{
        displayName: 'Revit-Linked Asset (Tutorial Demo)',
        description: 'Linked to Revit externalId: a1b2c3d4-e5f6-7890',
        clientAssetId: 'tutorial-revit-demo-001'
      }]
    };
    console.log(`  POST ${assetsBase}/assets:batch-create`);
    console.log(`  Body: ${JSON.stringify(body, null, 2)}\n`);
    const { status, data } = await apsRequest('POST', `${assetsBase}/assets:batch-create`, {
      'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json'
    }, body);
    if (status === 200 || status === 201) {
      const results = data.results || (data.id ? [data] : []);
      console.log(`  ✅ Revit-linked asset created! ID: ${results[0]?.id || 'N/A'}`);
    } else {
      console.log(`  ✗ Failed! Status: ${status}`);
    }
  }

  console.log('\n  Complete workflow: Upload RVT → Translate → Extract → Create linked assets');
}

// ══════════════════════════════════════════════════════════════════════════════
//  Main
// ══════════════════════════════════════════════════════════════════════════════

async function main() {
  console.log('\n🏗️  LESSON 8: Autodesk ACC Build — Two-Legged OAuth\n' + '─'.repeat(50));

  console.log('\n  This lesson teaches you to authenticate with Autodesk\'s API');
  console.log('  and interact with ACC Build (projects, issues, RFIs,');
  console.log('  submittals, assets, and Revit model integration).\n');
  console.log('  ┌──────────────────────────────────────────────────────────┐');
  console.log('  │  Prerequisites:                                          │');
  console.log('  │  1. An Autodesk Platform Services (APS) app              │');
  console.log('  │     → Create at: https://aps.autodesk.com/myapps         │');
  console.log('  │  2. Set environment variables:                           │');
  console.log('  │     APS_CLIENT_ID=your_client_id                        │');
  console.log('  │     APS_CLIENT_SECRET=your_client_secret                │');
  console.log('  │  3. App must have ACC Build API access enabled           │');
  console.log('  └──────────────────────────────────────────────────────────┘');

  const token = await demoTwoLeggedAuth();
  const projectId = await demoListProjects(token);
  await demoListIssues(token, projectId);
  await demoCreateIssue(token, projectId);
  await demoListRfis(token, projectId);
  await demoSubmittals(token, projectId);
  await demoAssets(token, projectId);
  await demoRevitAssets(token, projectId);

  console.log('\n\n💡 Key Concepts:');
  console.log('  • Two-legged OAuth: server-to-server, no user login needed');
  console.log('  • Submittals: draft → submitted → reviewed → approved/rejected');
  console.log('  • Assets use batch operations: batch-create, batch-patch, batch-delete');
  console.log('  • Revit integration: Model Derivative API → extract → link to assets');
  console.log('  • Token expires in 3600s (1 hour) — cache and refresh before expiry');

  console.log('\n' + '─'.repeat(50));
  console.log('🎯 YOUR TURN — Exercises:');
  console.log('  1. Build a full Revit→Asset pipeline with a real .rvt file');
  console.log('  2. Add custom attributes to assets and search by them');
  console.log('  3. Create submittal templates and reuse them');
  console.log('  4. Add pagination support — fetch all pages of results\n');
}

main().catch(console.error);
