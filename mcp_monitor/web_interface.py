
from flask import Flask, request, jsonify
from pathlib import Path

from . import MCPMonitor, RequestStatus


def create_web_interface(monitor: MCPMonitor, port=5000):

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates")
    )

    @app.route("/")
    def index():
        return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Walled AI | Security Dashboard</title>

<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #080c16;
    --panel: #111827;
    --panel-light: #172235;
    --border: rgba(255,255,255,.08);
    --text: #f1f5f9;
    --muted: #8995a9;
    --green: #22c55e;
    --red: #f43f5e;
    --blue: #60a5fa;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background:
        radial-gradient(ellipse at 75% 0%, rgba(37,99,235,.13), transparent 35%),
        var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
}

.layout {
    display: flex;
    min-height: 100vh;
}

.sidebar {
    width: 245px;
    background: rgba(12,18,31,.92);
    border-right: 1px solid var(--border);
    padding: 28px 18px;
    display: flex;
    flex-direction: column;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 8px;
    margin-bottom: 48px;
}

.brand-icon {
    width: 42px;
    height: 42px;
    display: grid;
    place-items: center;
    border-radius: 13px;
    background: linear-gradient(135deg,#2563eb,#7c3aed);
    font-size: 21px;
    box-shadow: 0 5px 25px rgba(37,99,235,.3);
}

.brand h2 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 19px;
    margin: 0;
}

.brand small {
    color: var(--muted);
    font-size: 11px;
}

.nav-label {
    font-size: 10px;
    color: #66738a;
    letter-spacing: 1.5px;
    font-weight: 700;
    padding: 0 12px;
    margin-bottom: 12px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 13px 14px;
    color: #9ba9bd;
    border-radius: 10px;
    margin-bottom: 6px;
    font-size: 13px;
}

.nav-item.active {
    color: white;
    background: linear-gradient(90deg,rgba(59,130,246,.2),rgba(59,130,246,.05));
    border: 1px solid rgba(59,130,246,.2);
}

.nav-icon {
    font-size: 17px;
}

.sidebar-bottom {
    margin-top: auto;
    padding: 15px;
    background: #111c2d;
    border: 1px solid var(--border);
    border-radius: 13px;
}

.sidebar-bottom small {
    color: var(--muted);
}

.connection {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
    font-size: 12px;
}

.dot {
    width: 8px;
    height: 8px;
    background: var(--green);
    border-radius: 50%;
    box-shadow: 0 0 12px var(--green);
}

.main {
    flex: 1;
    min-width: 0;
    padding: 36px 42px;
    max-width: 1600px;
    margin: 0 auto;
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    margin-bottom: 35px;
}

.eyebrow {
    color: var(--blue);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}

h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 31px;
    margin: 8px 0;
}

.subtitle {
    color: var(--muted);
    font-size: 13px;
}

.live-pill {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 10px 15px;
    border-radius: 30px;
    border: 1px solid rgba(34,197,94,.25);
    background: rgba(34,197,94,.08);
    color: #4ade80;
    font-size: 12px;
    font-weight: 600;
}

.stats {
    display: grid;
    grid-template-columns: repeat(3,minmax(0,1fr));
    gap: 17px;
    margin-bottom: 30px;
}

.stat-card {
    background: linear-gradient(145deg,#141f32,#101827);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 21px;
    position: relative;
    overflow: hidden;
}

.stat-card::after {
    content: "";
    position: absolute;
    width: 100px;
    height: 100px;
    right: -35px;
    top: -35px;
    background: rgba(59,130,246,.1);
    filter: blur(20px);
    border-radius: 50%;
}

.stat-top {
    display: flex;
    justify-content: space-between;
    color: var(--muted);
    font-size: 12px;
}

.stat-icon {
    font-size: 20px;
}

.stat-value {
    font-family: 'Space Grotesk',sans-serif;
    font-size: 32px;
    font-weight: 700;
    margin-top: 13px;
}

.stat-note {
    color: #7c8ba2;
    font-size: 11px;
    margin-top: 5px;
}

.content-grid {
    display: grid;
    grid-template-columns: minmax(0,1.65fr) minmax(280px,.85fr);
    gap: 20px;
    align-items: start;
}

.panel {
    background: rgba(17,24,39,.88);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
}

.panel-header {
    padding: 21px 23px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.panel-title {
    font-family: 'Space Grotesk',sans-serif;
    font-size: 16px;
    font-weight: 600;
}

.panel-subtitle {
    color: var(--muted);
    font-size: 11px;
    margin-top: 5px;
}

.count {
    background: rgba(59,130,246,.14);
    color: #93c5fd;
    border: 1px solid rgba(59,130,246,.2);
    border-radius: 30px;
    padding: 6px 11px;
    font-size: 12px;
    font-weight: 700;
}

.request-card {
    margin: 16px;
    padding: 19px;
    background: linear-gradient(145deg,#19253a,#131d2d);
    border: 1px solid rgba(96,165,250,.16);
    border-radius: 13px;
    transition: .2s ease;
}

.request-card:hover {
    border-color: rgba(96,165,250,.4);
    transform: translateY(-2px);
}

.request-heading {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: flex-start;
}

.tool-name {
    font-weight: 700;
    font-size: 14px;
}

.server-name {
    color: var(--muted);
    font-size: 11px;
    margin-top: 5px;
}

.pending-badge {
    color: #fbbf24;
    background: rgba(245,158,11,.1);
    border: 1px solid rgba(245,158,11,.2);
    border-radius: 30px;
    padding: 5px 9px;
    font-size: 10px;
    font-weight: 700;
    white-space: nowrap;
}

.request-meta {
    margin: 17px 0 9px;
    color: #91a0b6;
    font-size: 11px;
}

pre {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    max-height: 220px;
    overflow: auto;
    background: #0b1220;
    border: 1px solid var(--border);
    color: #b7c8df;
    padding: 14px;
    border-radius: 9px;
    font: 11px/1.7 monospace;
}

.actions {
    display: flex;
    gap: 10px;
    margin-top: 16px;
}

button {
    border: 0;
    border-radius: 9px;
    padding: 11px 18px;
    cursor: pointer;
    font-family: inherit;
    font-size: 12px;
    font-weight: 700;
    transition: .2s;
}

button:disabled {
    opacity: .5;
    cursor: wait;
}

.allow {
    color: white;
    background: linear-gradient(135deg,#16a34a,#15803d);
    box-shadow: 0 4px 14px rgba(22,163,74,.16);
}

.block {
    color: white;
    background: linear-gradient(135deg,#e11d48,#be123c);
    box-shadow: 0 4px 14px rgba(225,29,72,.13);
}

button:hover:not(:disabled) {
    transform: translateY(-2px);
    filter: brightness(1.1);
}

.empty {
    padding: 65px 20px;
    text-align: center;
}

.empty-icon {
    font-size: 35px;
    margin-bottom: 15px;
}

.empty h3 {
    font-size: 15px;
    margin: 0 0 8px;
}

.empty p {
    color: var(--muted);
    font-size: 12px;
}

.recent-item {
    padding: 17px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
}

.recent-item:last-child {
    border-bottom: 0;
}

.recent-name {
    font-size: 12px;
    font-weight: 600;
}

.recent-server {
    font-size: 10px;
    color: var(--muted);
    margin-top: 5px;
}

.status {
    font-size: 10px;
    font-weight: 700;
    padding: 5px 9px;
    border-radius: 30px;
    white-space: nowrap;
}

.status-allow {
    color: #4ade80;
    background: rgba(34,197,94,.1);
}

.status-block {
    color: #fb7185;
    background: rgba(244,63,94,.1);
}

.status-other {
    color: #94a3b8;
    background: rgba(148,163,184,.1);
}

.footer {
    text-align: center;
    color: #58677e;
    font-size: 11px;
    margin-top: 30px;
    padding: 20px;
}

@media(max-width:1000px) {
    .sidebar {
        width: 75px;
        padding: 25px 10px;
    }

    .brand {
        justify-content: center;
        padding: 0;
    }

    .brand-text, .nav-label, .nav-text,
    .sidebar-bottom {
        display: none;
    }

    .nav-item {
        justify-content: center;
        padding: 13px 5px;
    }

    .main {
        padding: 28px 22px;
    }
}

@media(max-width:750px) {
    .content-grid {
        grid-template-columns: 1fr;
    }

    .stats {
        grid-template-columns: 1fr;
    }

    .topbar {
        align-items: flex-start;
        flex-direction: column;
    }

    h1 {
        font-size: 25px;
    }
}

@media(max-width:480px) {
    .main {
        padding: 22px 12px;
    }

    .sidebar {
        width: 58px;
    }

    .panel-header {
        padding: 17px;
    }

    .request-card {
        margin: 10px;
        padding: 14px;
    }
}
</style>
</head>

<body>
<div class="layout">

    <aside class="sidebar">
        <div class="brand">
            <div class="brand-icon">◈</div>
            <div class="brand-text">
                <h2>Walled AI</h2>
                <small>SECURITY GATEWAY</small>
            </div>
        </div>

        <div class="nav-label">WORKSPACE</div>

        <div class="nav-item active">
            <span class="nav-icon">◫</span>
            <span class="nav-text">Dashboard</span>
        </div>

        <div class="nav-item">
            <span class="nav-icon">◉</span>
            <span class="nav-text">Authorization</span>
        </div>

        <div class="nav-item">
            <span class="nav-icon">◷</span>
            <span class="nav-text">Activity Logs</span>
        </div>

        <div class="sidebar-bottom">
            <small>GATEWAY STATUS</small>
            <div class="connection">
                <span class="dot"></span>
                <span>Monitoring active</span>
            </div>
        </div>
    </aside>

    <main class="main">

        <header class="topbar">
            <div>
                <div class="eyebrow">SECURITY CENTER / OVERVIEW</div>
                <h1>Authorization Dashboard</h1>
                <div class="subtitle">
                    Monitor and control incoming MCP tool requests.
                </div>
            </div>

            <div class="live-pill">
                <span class="dot"></span>
                LIVE MONITORING
            </div>
        </header>

        <section class="stats">

            <div class="stat-card">
                <div class="stat-top">
                    <span>Pending Requests</span>
                    <span class="stat-icon">◷</span>
                </div>
                <div class="stat-value" id="pendingStat">0</div>
                <div class="stat-note">Awaiting your approval</div>
            </div>

            <div class="stat-card">
                <div class="stat-top">
                    <span>Total Requests</span>
                    <span class="stat-icon">◫</span>
                </div>
                <div class="stat-value" id="totalStat">0</div>
                <div class="stat-note">All recorded requests</div>
            </div>

            <div class="stat-card">
                <div class="stat-top">
                    <span>Approved Requests</span>
                    <span class="stat-icon">✓</span>
                </div>
                <div class="stat-value" id="approvedStat">0</div>
                <div class="stat-note">Authorized tool executions</div>
            </div>

        </section>

        <section class="content-grid">

            <div class="panel">
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Authorization Queue</div>
                        <div class="panel-subtitle">
                            Review each request before execution
                        </div>
                    </div>
                    <span class="count" id="queueCount">0 REQUESTS</span>
                </div>

                <div id="pending">
                    <div class="empty">
                        <div class="empty-icon">◷</div>
                        <h3>Loading requests...</h3>
                        <p>Checking your authorization queue.</p>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Recent Activity</div>
                        <div class="panel-subtitle">
                            Latest authorization decisions
                        </div>
                    </div>
                    <span class="count">HISTORY</span>
                </div>

                <div id="recent">
                    <div class="empty">
                        <p>Loading activity...</p>
                    </div>
                </div>
            </div>

        </section>

        <div class="footer">
            Walled AI Security Gateway · MCP Authorization System
        </div>

    </main>
</div>

<script>
let refreshing = false;
let deciding = false;

function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
}

function showEmpty(container, icon, title, message) {
    const empty = createElement("div", "empty");
    empty.append(
        createElement("div", "empty-icon", icon),
        createElement("h3", "", title),
        createElement("p", "", message)
    );
    container.replaceChildren(empty);
}

async function decide(id, decision, buttons) {
    if (deciding) return;

    deciding = true;
    buttons.forEach(button => button.disabled = true);

    try {
        const response = await fetch("/decision", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                request_id: id,
                decision: decision
            })
        });

        const result = await response.json();

        if (!response.ok || result.status !== "success") {
            alert("Decision failed: " +
                (result.message || "Unknown error"));
        }

        await refresh();

    } catch (error) {
        alert("Unable to submit decision: " + error.message);
    } finally {
        deciding = false;
        buttons.forEach(button => button.disabled = false);
    }
}

function renderPending(requests) {
    const container = document.getElementById("pending");
    container.replaceChildren();

    if (!requests.length) {
        showEmpty(
            container,
            "✓",
            "All caught up!",
            "There are no pending authorization requests."
        );
        return;
    }

    requests.forEach(request => {
        const card = createElement("div", "request-card");

        const heading = createElement("div", "request-heading");
        const info = createElement("div");

        info.append(
            createElement("div", "tool-name", request.tool),
            createElement("div", "server-name",
                "SERVER / " + request.server)
        );

        heading.append(
            info,
            createElement("span", "pending-badge", "● PENDING")
        );

        const meta = createElement(
            "div",
            "request-meta",
            "REQUEST DETAILS"
        );

        const params = createElement("pre");
        params.textContent = JSON.stringify(
            request.parameters,
            null,
            2
        );

        const actions = createElement("div", "actions");

        const allow = createElement("button", "allow", "✓  Allow");
        const block = createElement("button", "block", "✕  Block");

        allow.onclick = () => decide(
            request.id, "allow", [allow, block]
        );

        block.onclick = () => decide(
            request.id, "block", [allow, block]
        );

        actions.append(allow, block);
        card.append(heading, meta, params, actions);
        container.appendChild(card);
    });
}

function renderRecent(requests) {
    const container = document.getElementById("recent");
    container.replaceChildren();

    const recent = requests
        .filter(request => request.status !== "pending")
        .slice(-10)
        .reverse();

    if (!recent.length) {
        showEmpty(
            container,
            "◷",
            "No activity yet",
            "Your authorization history will appear here."
        );
        return;
    }

    recent.forEach(request => {
        const item = createElement("div", "recent-item");

        const info = createElement("div");
        info.append(
            createElement("div", "recent-name", request.tool),
            createElement("div", "recent-server", request.server)
        );

        const normalized = String(
            request.user_decision || request.status || ""
        ).toLowerCase();

        let statusClass = "status-other";
        let statusText = normalized || "unknown";

        if (normalized === "allow" || normalized === "approved") {
            statusClass = "status-allow";
            statusText = "APPROVED";
        } else if (
            normalized === "block" ||
            normalized === "blocked" ||
            normalized === "denied"
        ) {
            statusClass = "status-block";
            statusText = "BLOCKED";
        }

        item.append(
            info,
            createElement("span", "status " + statusClass, statusText)
        );

        container.appendChild(item);
    });
}

async function refresh() {
    if (refreshing) return;
    refreshing = true;

    try {
        const response = await fetch("/api/requests", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error("Dashboard API returned " + response.status);
        }

        const data = await response.json();

        const pending = data.pending || [];
        const all = data.all || [];

        document.getElementById("pendingStat").textContent =
            pending.length;

        document.getElementById("totalStat").textContent =
            all.length;

        document.getElementById("approvedStat").textContent =
            all.filter(r =>
                ["allow", "approved"].includes(
                    String(r.user_decision || r.status).toLowerCase()
                )
            ).length;

        document.getElementById("queueCount").textContent =
            pending.length + " REQUESTS";

        renderPending(pending);
        renderRecent(all);

    } catch (error) {
        console.error("Dashboard refresh failed:", error);
    } finally {
        refreshing = false;
    }
}

refresh();
setInterval(refresh, 1000);
</script>

</body>
</html>
        """

    @app.route("/mcp/authorize", methods=["POST"])
    def authorize():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON"}), 400

        if not isinstance(data.get("arguments", {}), dict):
            return jsonify({"error": "Invalid arguments"}), 400

        decision = monitor.wait_for_decision(data, timeout=300)

        return jsonify({
            "decision": decision
        })

    @app.route("/decision", methods=["POST"])
    def decision():
        data = request.get_json(silent=True) or {}

        success = monitor.handle_decision(
            data.get("request_id"),
            data.get("decision")
        )

        if success:
            return jsonify({"status": "success"})

        return jsonify({
            "status": "error",
            "message": "Request not found or already decided"
        }), 404

    @app.route("/api/requests")
    def api_requests():

        def serialize(req):
            return {
                "id": req.id,
                "timestamp": req.timestamp,
                "server": req.server,
                "tool": req.tool,
                "parameters": req.parameters,
                "status": req.status.value,
                "user_decision": req.user_decision
            }

        requests = list(monitor.get_requests().values())

        return jsonify({
            "pending": [
                serialize(r) for r in requests
                if r.status == RequestStatus.PENDING
            ],
            "all": [serialize(r) for r in requests]
        })

    return app
