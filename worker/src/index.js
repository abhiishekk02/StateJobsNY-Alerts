const ROLES = {
  "Software & IT": ["software", "developer", "programmer", "information technology", "computer", "systems", "network", "cyber", "cloud", "devops", "database"],
  "Data & Analytics": ["data", "analyst", "analytics", "research", "statistic", "business intelligence"],
  "Business & Operations": ["business", "operations", "project", "program", "administrative", "management"],
  Engineering: ["engineer", "engineering", "architect", "construction"],
  Finance: ["finance", "financial", "account", "audit", "budget", "tax"],
  Communications: ["communication", "public information", "media", "marketing", "writer", "editor"],
};
const LOCATIONS = ["Albany", "New York City", "Buffalo", "Rochester", "Syracuse", "Remote / statewide"];
const json = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), {status, headers: {"Content-Type": "application/json; charset=utf-8", ...headers}});
const page = (title, message, siteUrl) => new Response(`<!doctype html><meta name="viewport" content="width=device-width"><title>${title} · Northstar</title><style>body{margin:0;background:#f5f5f7;color:#111;font:16px system-ui;display:grid;place-items:center;min-height:100vh}.card{background:#fff;padding:50px;border-radius:28px;box-shadow:0 25px 70px #0002;max-width:520px;text-align:center}h1{font-size:42px;letter-spacing:-.05em;margin:0 0 16px}p{color:#6e6e73;line-height:1.6}a{display:inline-block;margin-top:18px;background:#111;color:#fff;padding:13px 20px;border-radius:99px;text-decoration:none}</style><main class="card"><h1>${title}</h1><p>${message}</p><a href="${siteUrl}">Back to Northstar</a></main>`, {headers: {"Content-Type": "text/html; charset=utf-8"}});

function cors(request, env) {
  const origin = request.headers.get("Origin");
  return origin === env.SITE_URL ? {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Allow-Methods": "POST, OPTIONS", Vary: "Origin"} : {};
}
const cleanEmail = (value) => String(value || "").trim().toLowerCase();
const validEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) && value.length <= 254;
const token = () => Array.from(crypto.getRandomValues(new Uint8Array(32)), b => b.toString(16).padStart(2, "0")).join("");
async function hash(value) { const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)); return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join(""); }

async function sendEmail(env, to, subject, html) {
  const response = await fetch("https://api.resend.com/emails", {method: "POST", headers: {Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json"}, body: JSON.stringify({from: env.FROM_EMAIL, to: [to], subject, html})});
  if (!response.ok) throw new Error(`Resend rejected email (${response.status})`);
}

async function subscribe(request, env) {
  let body; try { body = await request.json(); } catch { return json({error: "Invalid request."}, 400); }
  const name = String(body.name || "").trim().slice(0, 80), email = cleanEmail(body.email);
  const year = Number(body.graduationYear), roles = Array.isArray(body.roles) ? [...new Set(body.roles)] : [], locations = Array.isArray(body.locations) ? [...new Set(body.locations)] : [];
  if (!name || !validEmail(email) || !Number.isInteger(year) || year < 2000 || year > 2100 || !body.consent || !roles.length || !locations.length || roles.some(r => !ROLES[r]) || locations.some(l => !LOCATIONS.includes(l))) return json({error: "Please check the information you entered."}, 422);
  const verifyToken = token(), unsubscribeToken = token(), now = new Date().toISOString(), id = crypto.randomUUID();
  await env.DB.prepare(`INSERT INTO subscribers (id,email,name,graduation_year,roles,locations,status,verification_hash,unsubscribe_hash,consented_at,created_at,updated_at) VALUES (?,?,?,?,?,?,'pending',?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET name=excluded.name,graduation_year=excluded.graduation_year,roles=excluded.roles,locations=excluded.locations,status='pending',verification_hash=excluded.verification_hash,unsubscribe_hash=excluded.unsubscribe_hash,consented_at=excluded.consented_at,verified_at=NULL,unsubscribed_at=NULL,updated_at=excluded.updated_at`).bind(id,email,name,year,JSON.stringify(roles),JSON.stringify(locations),await hash(verifyToken),await hash(unsubscribeToken),now,now,now).run();
  const api = new URL(request.url).origin;
  try { await sendEmail(env, email, "Confirm your Northstar alerts", `<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;padding:40px"><p style="font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#777">Northstar</p><h1 style="font-size:36px;letter-spacing:-1.5px">One small step, ${escapeHtml(name)}.</h1><p style="color:#666;line-height:1.6">Confirm your email to begin receiving thoughtfully matched New York State opportunities.</p><a href="${api}/api/verify?token=${verifyToken}" style="display:inline-block;background:#111;color:#fff;text-decoration:none;padding:14px 20px;border-radius:99px;margin:12px 0">Confirm my alerts</a><p style="font-size:12px;color:#999">If you didn’t request this, you can ignore this email.</p></div>`); }
  catch { return json({error: "We saved your preferences but couldn’t send confirmation. Please try again."}, 502); }
  return json({ok: true}, 201);
}

async function verify(url, env) {
  const raw = url.searchParams.get("token"); if (!raw) return page("Invalid link", "This confirmation link is incomplete.", env.SITE_URL);
  const result = await env.DB.prepare("UPDATE subscribers SET status='active',verified_at=?,updated_at=? WHERE verification_hash=? AND status='pending'").bind(new Date().toISOString(),new Date().toISOString(),await hash(raw)).run();
  return result.meta.changes ? page("You’re in.", "Your alert is active. We’ll only write when a role genuinely matches.", env.SITE_URL) : page("Link expired", "This link has already been used or is no longer valid. You can subscribe again for a fresh one.", env.SITE_URL);
}

async function unsubscribe(url, env) {
  const raw = url.searchParams.get("token"); if (!raw) return page("Invalid link", "This unsubscribe link is incomplete.", env.SITE_URL);
  const now = new Date().toISOString(); const result = await env.DB.prepare("UPDATE subscribers SET status='unsubscribed',unsubscribed_at=?,updated_at=? WHERE unsubscribe_hash=? AND status='active'").bind(now,now,await hash(raw)).run();
  return result.meta.changes ? page("Unsubscribed.", "No more alerts will be sent. The door is always open if you change your mind.", env.SITE_URL) : page("Already handled", "This subscription is already inactive.", env.SITE_URL);
}

function matches(subscriber, job) {
  const roles = JSON.parse(subscriber.roles), locations = JSON.parse(subscriber.locations), haystack = `${job.title} ${job.agency}`.toLowerCase(), place = String(job.location || "").toLowerCase();
  const roleMatch = roles.some(role => ROLES[role].some(word => haystack.includes(word)));
  const locationMatch = locations.some(location => location === "Remote / statewide" || place.includes(location.toLowerCase()) || (location === "New York City" && /new york|manhattan|queens|bronx|brooklyn/.test(place)));
  return roleMatch && locationMatch;
}
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[c]); }

async function ingest(request, env) {
  if (!env.INGEST_API_KEY || request.headers.get("Authorization") !== `Bearer ${env.INGEST_API_KEY}`) return json({error: "Unauthorized"}, 401);
  let job; try { job = await request.json(); } catch { return json({error: "Invalid JSON"}, 400); }
  if (!job.job_id || !job.title || !job.url) return json({error: "Missing job fields"}, 422);
  const {results} = await env.DB.prepare("SELECT id,email,name,roles,locations,unsubscribe_hash FROM subscribers WHERE status='active'").all(); let sent = 0;
  for (const subscriber of results.filter(s => matches(s, job))) {
    const prior = await env.DB.prepare("SELECT 1 FROM deliveries WHERE subscriber_id=? AND job_id=?").bind(subscriber.id,String(job.job_id)).first(); if (prior) continue;
    const unsubToken = token(); const unsubHash = await hash(unsubToken); await env.DB.prepare("UPDATE subscribers SET unsubscribe_hash=? WHERE id=?").bind(unsubHash,subscriber.id).run();
    const unsubscribeUrl = `${new URL(request.url).origin}/api/unsubscribe?token=${unsubToken}`;
    const rows = [["Agency",job.agency],["Location",job.location],["Grade",job.grade],["Salary",job.salary],["Deadline",job.deadline]].map(([a,b])=>`<tr><td style="padding:8px;color:#888">${a}</td><td style="padding:8px"><b>${escapeHtml(b || "Not provided")}</b></td></tr>`).join("");
    await sendEmail(env, subscriber.email, `New match: ${job.title}`, `<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:35px"><p style="font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#777">A new match for ${escapeHtml(subscriber.name)}</p><h1 style="font-size:32px;letter-spacing:-1.3px">${escapeHtml(job.title)}</h1><table style="width:100%;border-collapse:collapse;background:#f6f6f7;border-radius:12px">${rows}</table><a href="${escapeHtml(job.url)}" style="display:inline-block;background:#111;color:#fff;text-decoration:none;padding:14px 20px;border-radius:99px;margin:24px 0">View official posting</a><p style="font-size:11px;color:#999">Northstar is independent and not affiliated with New York State. <a href="${unsubscribeUrl}" style="color:#777">Unsubscribe</a></p></div>`);
    await env.DB.prepare("INSERT INTO deliveries (subscriber_id,job_id,delivered_at) VALUES (?,?,?)").bind(subscriber.id,String(job.job_id),new Date().toISOString()).run(); sent++;
  }
  return json({ok: true, sent});
}

export default { async fetch(request, env) {
  const url = new URL(request.url), headers = cors(request, env);
  if (request.method === "OPTIONS") return new Response(null, {status: 204, headers});
  try {
    let response;
    if (request.method === "POST" && url.pathname === "/api/subscribe") response = await subscribe(request, env);
    else if (request.method === "GET" && url.pathname === "/api/verify") return verify(url, env);
    else if (request.method === "GET" && url.pathname === "/api/unsubscribe") return unsubscribe(url, env);
    else if (request.method === "POST" && url.pathname === "/api/jobs") response = await ingest(request, env);
    else if (url.pathname === "/api/health") response = json({ok: true});
    else response = json({error: "Not found"}, 404);
    Object.entries(headers).forEach(([key,value]) => response.headers.set(key,value)); return response;
  } catch (error) { console.error(error); const response = json({error: "Something went wrong."}, 500); Object.entries(headers).forEach(([k,v])=>response.headers.set(k,v)); return response; }
}};
