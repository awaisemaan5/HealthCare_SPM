from flask import Flask, request, redirect, url_for, render_template_string, flash, session
import hmac
import sqlite3, os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "healthcare-spm-demo")
LOGIN_USERNAME = os.environ.get("SPM_USERNAME") or "chawais"
LOGIN_PASSWORD = os.environ.get("SPM_PASSWORD") or "pakistan"
DB = os.path.join(os.path.dirname(__file__), "spm.db")


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS project(id INTEGER PRIMARY KEY, name TEXT, budget REAL, weeks INTEGER, status TEXT);
        CREATE TABLE IF NOT EXISTS requirements(id INTEGER PRIMARY KEY, title TEXT, priority TEXT, status TEXT);
        CREATE TABLE IF NOT EXISTS changes(id INTEGER PRIMARY KEY, title TEXT, reason TEXT, cost REAL, weeks INTEGER, status TEXT);
        CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, title TEXT, assignee TEXT, duration INTEGER, start_week INTEGER, dependency TEXT, cost REAL, progress REAL, status TEXT);
        CREATE TABLE IF NOT EXISTS defects(id INTEGER PRIMARY KEY, title TEXT, severity TEXT, assignee TEXT, status TEXT);
        CREATE TABLE IF NOT EXISTS risks(id INTEGER PRIMARY KEY, title TEXT, likelihood INTEGER, impact INTEGER, response TEXT, status TEXT);
        CREATE TABLE IF NOT EXISTS quality(id INTEGER PRIMARY KEY, item TEXT, result TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY, description TEXT, amount REAL);
        """)
        if not c.execute("SELECT id FROM project").fetchone():
            c.execute("INSERT INTO project VALUES(1,?,?,?,?)", ("Smart Healthcare Project Management System", 5000000, 16, "In Progress"))
            c.executemany("INSERT INTO requirements(title,priority,status) VALUES(?,?,?)", [
                ("Patient appointment scheduling", "High", "Approved"), ("Laboratory reports", "High", "Approved"),
                ("Doctor schedules", "Medium", "Approved"), ("Online consultations", "High", "Approved"),
                ("Hospital billing", "High", "Approved"), ("AI preliminary diagnosis", "High", "Pending"),
                ("Mobile application", "High", "Pending")])
            c.executemany("INSERT INTO tasks(title,assignee,duration,start_week,dependency,cost,progress,status) VALUES(?,?,?,?,?,?,?,?)", [
                ("Requirements analysis", "Project Manager", 2, 1, "None", 350000, 100, "Completed"),
                ("Database design", "Database Developer", 2, 3, "Requirements analysis", 450000, 100, "Completed"),
                ("Backend development", "Backend Developer 1", 5, 5, "Database design", 1200000, 55, "In Progress"),
                ("Frontend development", "Frontend Developer 1", 5, 5, "Requirements analysis", 950000, 45, "In Progress"),
                ("Integration and testing", "QA Engineer", 2, 10, "Backend and frontend", 700000, 0, "Not Started"),
                ("Deployment", "Project Manager", 1, 12, "Integration and testing", 300000, 0, "Not Started")])
            c.executemany("INSERT INTO defects(title,severity,assignee,status) VALUES(?,?,?,?)", [
                ("Appointment scheduling produces incorrect slots", "Critical", "Backend Developer 1", "Open"),
                ("Duplicate patient records", "Critical", "Database Developer", "Open")])
            c.executemany("INSERT INTO risks(title,likelihood,impact,response,status) VALUES(?,?,?,?,?)", [
                ("Schedule delay", 4, 5, "Prioritize critical path; weekly review", "Open"),
                ("Budget overrun", 4, 5, "Require change approval and cost review", "Open")])


init()

LOGIN_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign in · Healthcare SPM</title><style>
:root{--navy:#0f1f3d;--blue:#2563eb;--teal:#0d9488;--bg:#f4f6fb;--text:#18233b;--muted:#6b7a95;--line:#e4e9f2}
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:'Segoe UI',system-ui,-apple-system,Arial,sans-serif;background:var(--bg);color:var(--text);display:grid;place-items:center;padding:24px}
.login{display:grid;grid-template-columns:1fr 1fr;width:min(900px,100%);min-height:540px;background:#fff;border:1px solid var(--line);border-radius:20px;overflow:hidden;box-shadow:0 20px 60px #10182818}
.intro{background:linear-gradient(145deg,var(--navy),#1b2f57);color:#fff;padding:56px 44px;display:flex;flex-direction:column;justify-content:space-between}
.brand{display:flex;align-items:center;gap:12px}.logo{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--teal),var(--blue));display:grid;place-items:center;font-size:23px;font-weight:800}
.brand b{display:block;font-size:17px}.brand span{font-size:12px;color:#cfd9ee}
.intro h1{font-size:34px;line-height:1.2;margin:0 0 14px}.intro p{line-height:1.7;color:#d4def0;margin:0}
.form-panel{padding:60px 48px;display:flex;flex-direction:column;justify-content:center}.form-panel h2{font-size:26px;margin:0 0 8px}.sub{color:var(--muted);margin:0 0 28px}
label{display:block;font-size:13px;font-weight:600;margin:18px 0 7px}input{width:100%;padding:12px 13px;border:1px solid #ccd5e4;border-radius:9px;font:inherit}
input:focus{outline:2px solid #bcd1fb;border-color:var(--blue)}button{width:100%;margin-top:24px;background:var(--blue);color:#fff;padding:12px;border:0;border-radius:9px;font:inherit;font-weight:700;cursor:pointer}
button:hover{filter:brightness(1.08)}.flash{background:#fff7e0;border:1px solid #f3dc9b;padding:12px;border-radius:9px;margin:0 0 14px;font-size:13px}
.foot{font-size:12px;color:var(--muted);margin-top:22px}
@media(max-width:680px){.login{grid-template-columns:1fr}.intro{padding:28px;gap:34px}.intro h1{font-size:28px}.form-panel{padding:34px 28px}}
</style></head><body><div class="login">
<section class="intro"><div class="brand"><div class="logo">+</div><div><b>HealthPM</b><span>Project Control Center</span></div></div>
<div><h1>Manage healthcare projects with clarity.</h1><p>Sign in to review project progress, requirements, schedules, risks, and reports.</p></div>
<p>Educational demo · Sample data only</p></section>
<main class="form-panel"><h2>Welcome back</h2><p class="sub">Sign in to continue to your workspace.</p>
{% with messages=get_flashed_messages() %}{% for message in messages %}<div class="flash" role="alert">{{message}}</div>{% endfor %}{% endwith %}
<form method="post"><label for="username">Username</label><input id="username" name="username" autocomplete="username" required autofocus>
<label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" required>
<button type="submit">Sign in</button></form><div class="foot">Do not enter real patient information.</div></main></div></body></html>"""


@app.before_request
def require_login():
    if request.endpoint in ("login", "static"):
        return None
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        valid_username = hmac.compare_digest(username.encode("utf-8"), LOGIN_USERNAME.encode("utf-8"))
        valid_password = hmac.compare_digest(password.encode("utf-8"), LOGIN_PASSWORD.encode("utf-8"))
        if valid_username and valid_password:
            session.clear()
            session["authenticated"] = True
            return redirect(url_for("home"))
        flash("The username or password is incorrect.")
    return render_template_string(LOGIN_PAGE)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been signed out.")
    return redirect(url_for("login"))


STYLE = """<style>
:root{--navy:#0f1f3d;--navy2:#1b2f57;--blue:#2563eb;--teal:#0d9488;--bg:#f4f6fb;--card:#fff;--line:#e4e9f2;--text:#18233b;--muted:#6b7a95;--red:#dc2626;--amber:#d97706;--green:#16a34a}
*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,Arial,sans-serif;background:var(--bg);color:var(--text);font-size:14px}
.layout{display:flex;min-height:100vh}
.side{width:240px;background:linear-gradient(180deg,var(--navy),var(--navy2));color:#cfd9ee;padding:22px 14px;position:sticky;top:0;height:100vh;flex-shrink:0}
.brand{display:flex;align-items:center;gap:10px;padding:0 8px 22px;border-bottom:1px solid #ffffff1f;margin-bottom:16px}
.logo{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,var(--teal),var(--blue));display:grid;place-items:center;color:#fff;font-weight:800;font-size:20px}
.brand b{color:#fff;font-size:15px;display:block}.brand span{font-size:11px;opacity:.7}
.side a{display:flex;gap:10px;align-items:center;padding:11px 12px;border-radius:9px;color:#cfd9ee;text-decoration:none;margin-bottom:3px;transition:.15s}
.side a:hover{background:#ffffff14;color:#fff}.side a.on{background:var(--blue);color:#fff;box-shadow:0 4px 12px #2563eb55}
.content{flex:1;min-width:0}
.top{background:#fff;border-bottom:1px solid var(--line);padding:16px 30px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
.top h1{margin:0;font-size:20px}.top small{color:var(--muted)}
.pill{background:#e0ecff;color:var(--blue);padding:6px 12px;border-radius:20px;font-weight:600;font-size:12px}
main{padding:26px 30px;max-width:1250px}
h2{margin:0 0 16px;font-size:18px}h3{margin:0 0 12px;font-size:15px}
.grid{display:grid;gap:16px}.kpis{grid-template-columns:repeat(auto-fit,minmax(200px,1fr));margin-bottom:18px}
.two{grid-template-columns:repeat(auto-fit,minmax(380px,1fr));margin-bottom:18px}
.card,section{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 1px 3px #1018280a;margin-bottom:18px}
.grid .card,.grid section{margin-bottom:0}
.kpi{display:flex;gap:14px;align-items:center}.ico{width:46px;height:46px;border-radius:12px;display:grid;place-items:center;font-size:21px;flex-shrink:0}
.kpi .l{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.4px}.kpi .v{font-size:22px;font-weight:700;margin-top:2px}
.b1{background:#e0ecff}.b2{background:#d5f5ef}.b3{background:#fff1d6}.b4{background:#ffe1e1}.b5{background:#ece4ff}
.warn{color:var(--red);font-weight:700}
.donut{width:130px;height:130px;border-radius:50%;display:grid;place-items:center;margin:auto}
.donut div{width:92px;height:92px;border-radius:50%;background:#fff;display:grid;place-items:center;font-size:24px;font-weight:800}
.bar{background:#e6ebf4;border-radius:8px;height:10px;overflow:hidden}.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--blue),var(--teal));border-radius:8px}
table{width:100%;border-collapse:collapse}th{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);background:#f7f9fd;text-align:left;padding:11px 12px}
td{padding:12px;border-bottom:1px solid var(--line);vertical-align:middle}tr:hover td{background:#fafcff}
.tw{overflow-x:auto}
.badge{display:inline-block;padding:4px 10px;border-radius:20px;font-size:11.5px;font-weight:600;background:#eef1f7;color:#4b5a75}
.approved,.completed,.resolved,.low{background:#dcf5e5;color:#12803a}.pending,.not-started,.medium{background:#fff1d6;color:#a35a00}
.in-progress,.open{background:#dfeaff;color:#1d4fc4}.rejected,.critical,.high,.delayed{background:#ffe1e1;color:#b42318}
form{margin:0}.f{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input,select{padding:10px 12px;border:1px solid #ccd5e4;border-radius:8px;background:#fff;font:inherit;max-width:100%}
input:focus,select:focus{outline:2px solid #bcd1fb;border-color:var(--blue)}
button,.btn{background:var(--blue);color:#fff;padding:9px 15px;border:0;border-radius:8px;cursor:pointer;font:inherit;font-weight:600;text-decoration:none;display:inline-block}
button:hover{filter:brightness(1.1)}.ok{background:var(--green)}.no{background:var(--red)}.sm{padding:6px 11px;font-size:12px}
.flash{background:#fff7e0;border:1px solid #f3dc9b;padding:12px 16px;border-radius:10px;margin-bottom:16px}
.gantt{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;align-items:center;font-size:12.5px}
.track{position:relative;height:20px;background:#eef2f9;border-radius:6px}.seg{position:absolute;top:0;height:20px;border-radius:6px;background:#b9cdf7;overflow:hidden}.seg i{display:block;height:100%;background:var(--blue)}
.li{padding:10px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:10px}.li:last-child{border:0}
.note{color:var(--muted);font-size:12.5px;margin-top:12px}
.foot{color:var(--muted);font-size:12px;padding:10px 30px 24px}
@media(max-width:860px){.layout{flex-direction:column}.side{width:100%;height:auto;position:static;display:flex;flex-wrap:wrap;gap:4px;padding:12px}.brand{border:0;padding:0 8px;margin:0;width:100%}main,.top{padding:16px}.two{grid-template-columns:1fr}}
@media print{.side,.top .pill,button{display:none!important}main{padding:0}}
</style>"""

PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{title}} · Healthcare SPM</title>""" + STYLE + """</head><body><div class="layout">
<aside class="side"><div class="brand"><div class="logo">+</div><div><b>HealthPM</b><span>Project Control Center</span></div></div>
{% for href,icon,label in nav %}<a href="{{href}}" class="{{'on' if href==active else ''}}"><span>{{icon}}</span>{{label}}</a>{% endfor %}</aside>
<div class="content"><div class="top"><div><h1>{{title}}</h1><small>Smart Healthcare Project Management System</small></div><div style="display:flex;align-items:center;gap:12px"><span class="pill">● Live project</span><form method="post" action="{{url_for('logout')}}"><button class="sm" type="submit">Sign out</button></form></div></div>
<main>{% with messages=get_flashed_messages() %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endwith %}{{body|safe}}</main>
<div class="foot">Educational demo • Sample data only • No real patient information</div></div></div></body></html>"""

NAV = [("/", "📊", "Dashboard"), ("/requirements", "🧩", "Requirements & WBS"), ("/changes", "🔄", "Change Requests"),
       ("/schedule", "🗓️", "Schedule & Resources"), ("/cost", "💰", "Cost & EVM"), ("/quality", "🧪", "Quality & Defects"),
       ("/risks", "⚠️", "Risk Control"), ("/report", "📄", "Report")]


@app.template_filter("slug")
def slug(s):
    return str(s).lower().replace(" ", "-")


def page(title, active, body, **kw):
    return render_template_string(PAGE, title=title, active=active, nav=NAV, body=render_template_string(body, **kw))


def rows(sql, args=()):
    with db() as c:
        return c.execute(sql, args).fetchall()


def val(sql, args=(), default=0):
    r = rows(sql, args)
    return r[0][0] if r and r[0][0] is not None else default


@app.route("/")
def home():
    p = rows("SELECT * FROM project")[0]
    req = rows("SELECT * FROM requirements"); tasks = rows("SELECT * FROM tasks")
    defects = rows("SELECT * FROM defects"); changes = rows("SELECT * FROM changes")
    risks = rows("SELECT * FROM risks ORDER BY likelihood*impact DESC LIMIT 4")
    spent = val("SELECT SUM(amount) FROM expenses") + val("SELECT SUM(cost*progress/100) FROM tasks")
    progress = sum(t["progress"] for t in tasks) / max(len(tasks), 1)
    pending = sum(x["status"] == "Pending" for x in req) + sum(x["status"] == "Pending" for x in changes)
    critical = sum(x["severity"] == "Critical" and x["status"] != "Resolved" for x in defects)
    total_weeks = max([p["weeks"]] + [t["start_week"] + t["duration"] - 1 for t in tasks])
    used = min(spent / p["budget"] * 100, 100) if p["budget"] else 0
    body = """
<div class="grid kpis">
 <div class="card kpi"><div class="ico b1">💼</div><div><div class="l">Approved budget</div><div class="v">PKR {{'{:,.0f}'.format(p['budget'])}}</div></div></div>
 <div class="card kpi"><div class="ico b2">⏱️</div><div><div class="l">Duration</div><div class="v">{{p['weeks']}} weeks</div></div></div>
 <div class="card kpi"><div class="ico b5">💸</div><div><div class="l">Estimated spent</div><div class="v">PKR {{'{:,.0f}'.format(spent)}}</div></div></div>
 <div class="card kpi"><div class="ico b3">📝</div><div><div class="l">Pending requests</div><div class="v">{{pending}}</div></div></div>
 <div class="card kpi"><div class="ico b4">🐞</div><div><div class="l">Critical open defects</div><div class="v {{'warn' if critical else ''}}">{{critical}}</div></div></div>
</div>
<div class="grid two">
 <section><h3>Overall progress</h3>
  <div class="donut" style="background:conic-gradient(var(--blue) {{progress*3.6}}deg,#e6ebf4 0)"><div>{{'{:.0f}'.format(progress)}}%</div></div>
  <p class="note" style="text-align:center">Average of all activity progress</p>
  <div style="margin-top:14px"><div style="display:flex;justify-content:space-between"><b>Budget utilization</b><span>{{'{:.0f}'.format(used)}}%</span></div><div class="bar" style="margin-top:6px"><span style="width:{{used}}%"></span></div></div>
 </section>
 <section><h3>Timeline (weeks 1–{{total_weeks}})</h3><div class="gantt">
  {% for t in tasks %}<div>{{t.title}}</div><div class="track"><div class="seg" style="left:{{(t.start_week-1)/total_weeks*100}}%;width:{{t.duration/total_weeks*100}}%"><i style="width:{{t.progress}}%"></i></div></div>{% endfor %}
 </div></section>
</div>
<div class="grid two">
 <section><h3>Immediate attention</h3>
  <div class="li"><span>Fix appointment scheduling and duplicate patient records before release.</span><span class="badge critical">Critical</span></div>
  <div class="li"><span>AI diagnosis and mobile application are outside approved scope until approved.</span><span class="badge pending">Scope</span></div>
  <div class="li"><span>Review budget and schedule before authorizing new work.</span><span class="badge medium">Review</span></div>
 </section>
 <section><h3>Top risks</h3>
  {% for r in risks %}<div class="li"><span>{{r.title}}</span><span class="badge {{'high' if r.likelihood*r.impact>=15 else 'medium'}}">{{r.likelihood*r.impact}}/25</span></div>{% endfor %}
 </section>
</div>
<section><h3>Project charter</h3><p><b>Objective:</b> Manage appointments, laboratory reports, doctor schedules, online consultations and billing for five hospitals.</p>
<p><b>Deadline:</b> Original 16 weeks. <b>Status:</b> <span class="badge {{p['status']|slug}}">{{p['status']}}</span></p></section>"""
    return page("Dashboard", "/", body, p=p, progress=progress, spent=spent, pending=pending, critical=critical,
                tasks=tasks, total_weeks=total_weeks, used=used, risks=risks)


@app.route("/requirements", methods=["GET", "POST"])
def requirements():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Requirement title is required.")
        else:
            with db() as c:
                c.execute("INSERT INTO requirements(title,priority,status) VALUES(?,?,?)", (title, request.form.get("priority", "Medium"), "Pending"))
            flash("Requirement saved as Pending. Only approved requirements enter scope.")
        return redirect(url_for("requirements"))
    items = rows("SELECT * FROM requirements")
    body = """<section><h3>Add requirement</h3><form method="post" class="f"><input name="title" placeholder="Requirement / deliverable" required style="min-width:280px"><select name="priority"><option>High</option><option>Medium</option><option>Low</option></select><button>Add pending requirement</button></form></section>
<section><h3>WBS / requirements register</h3><div class="tw"><table><tr><th>ID</th><th>Deliverable</th><th>Priority</th><th>Status</th><th>Action</th></tr>
{% for r in items %}<tr><td>{{r.id}}</td><td>{{r.title}}</td><td><span class="badge {{r.priority|slug}}">{{r.priority}}</span></td><td><span class="badge {{r.status|slug}}">{{r.status}}</span></td>
<td>{% if r.status=='Pending' %}<form method="post" action="/approve_req/{{r.id}}"><button class="sm ok">Approve</button></form>{% endif %}</td></tr>{% endfor %}</table></div>
<p class="note">WBS level 1: Healthcare System → requirements, database, backend, frontend, integration/testing, deployment.</p></section>"""
    return page("Requirements & WBS", "/requirements", body, items=items)


@app.route("/approve_req/<int:i>", methods=["POST"])
def approve_req(i):
    with db() as c:
        c.execute("UPDATE requirements SET status='Approved' WHERE id=?", (i,))
    flash("Requirement approved and added to scope.")
    return redirect(url_for("requirements"))


@app.route("/changes", methods=["GET", "POST"])
def changes():
    if request.method == "POST":
        try:
            cost = float(request.form["cost"]); weeks = int(request.form["weeks"]); title = request.form["title"].strip()
            if not title or cost < 0 or weeks < 0:
                raise ValueError()
            with db() as c:
                c.execute("INSERT INTO changes(title,reason,cost,weeks,status) VALUES(?,?,?,?,?)", (title, request.form["reason"], cost, weeks, "Pending"))
            flash("Change request recorded as Pending.")
        except (ValueError, KeyError):
            flash("Enter a title, valid non-negative cost and duration.")
        return redirect(url_for("changes"))
    items = rows("SELECT * FROM changes")
    body = """<section><h3>Submit change request</h3><form method="post" class="f"><input name="title" placeholder="Change (e.g. AI diagnosis + mobile app)" required style="min-width:260px"><input name="reason" placeholder="Business justification" required><input name="cost" type="number" min="0" step="1000" placeholder="Cost impact PKR" required><input name="weeks" type="number" min="0" placeholder="Extra weeks" required><button>Submit request</button></form></section>
<section><h3>Change log</h3><div class="tw"><table><tr><th>Change</th><th>Justification</th><th>Cost (PKR)</th><th>Weeks</th><th>Status</th><th>Decision</th></tr>
{% for x in items %}<tr><td>{{x.title}}</td><td>{{x.reason}}</td><td>{{'{:,.0f}'.format(x.cost)}}</td><td>{{x.weeks}}</td><td><span class="badge {{x.status|slug}}">{{x.status}}</span></td>
<td>{% if x.status=='Pending' %}<div class="f"><form method="post" action="/decide/{{x.id}}/Approved"><button class="sm ok">Approve</button></form><form method="post" action="/decide/{{x.id}}/Rejected"><button class="sm no">Reject</button></form></div>{% endif %}</td></tr>{% endfor %}</table></div></section>"""
    return page("Change Requests", "/changes", body, items=items)


@app.route("/decide/<int:i>/<status>", methods=["POST"])
def decide(i, status):
    if status not in ("Approved", "Rejected"):
        return "Invalid", 400
    with db() as c:
        x = c.execute("SELECT * FROM changes WHERE id=?", (i,)).fetchone()
        if x and x["status"] == "Pending":
            c.execute("UPDATE changes SET status=? WHERE id=?", (status, i))
            if status == "Approved":
                c.execute("UPDATE project SET budget=budget+?,weeks=weeks+? WHERE id=1", (x["cost"], x["weeks"]))
                c.execute("INSERT INTO requirements(title,priority,status) VALUES(?,?,?)", (x["title"], "High", "Approved"))
    flash("Decision recorded. Approved changes update budget, duration and scope." if status == "Approved" else "Change rejected; baseline unchanged.")
    return redirect(url_for("changes"))


@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    if request.method == "POST":
        try:
            title = request.form["title"].strip(); duration = int(request.form["duration"]); start = int(request.form["start"]); cost = float(request.form["cost"])
            if not title or duration < 1 or start < 1 or cost < 0:
                raise ValueError()
            with db() as c:
                c.execute("INSERT INTO tasks(title,assignee,duration,start_week,dependency,cost,progress,status) VALUES(?,?,?,?,?,?,0,'Not Started')",
                          (title, request.form["assignee"], duration, start, request.form["dependency"], cost))
            flash("Activity added.")
        except (ValueError, KeyError):
            flash("Enter valid activity details.")
        return redirect(url_for("schedule"))
    items = rows("SELECT * FROM tasks ORDER BY start_week")
    body = """<section><h3>Add activity</h3><form method="post" class="f"><input name="title" placeholder="Activity" required><input name="assignee" placeholder="Responsible person" required><input name="duration" type="number" min="1" placeholder="Duration (weeks)" required><input name="start" type="number" min="1" placeholder="Start week" required><input name="dependency" placeholder="Dependency" required><input name="cost" type="number" min="0" placeholder="Cost PKR" required><button>Add activity</button></form></section>
<section><h3>Activity plan</h3><div class="tw"><table><tr><th>Activity</th><th>Owner</th><th>Start</th><th>End</th><th>Dependency</th><th>Cost PKR</th><th style="min-width:120px">Progress</th><th>Status</th><th>Update</th></tr>
{% for t in items %}<tr><td><b>{{t.title}}</b></td><td>{{t.assignee}}</td><td>W{{t.start_week}}</td><td>W{{t.start_week+t.duration-1}}</td><td>{{t.dependency}}</td><td>{{'{:,.0f}'.format(t.cost)}}</td>
<td>{{'%.0f'|format(t.progress)}}%<div class="bar" style="margin-top:5px"><span style="width:{{t.progress}}%"></span></div></td><td><span class="badge {{t.status|slug}}">{{t.status}}</span></td>
<td><form method="post" action="/progress/{{t.id}}" class="f"><input type="number" name="progress" min="0" max="100" value="{{'%.0f'|format(t.progress)}}" style="width:70px"><button class="sm">Save</button></form></td></tr>{% endfor %}</table></div>
<p class="note">End week = start week + duration − 1. This simple timeline displays dependencies; review the critical path manually.</p></section>"""
    return page("Schedule & Resources", "/schedule", body, items=items)


@app.route("/progress/<int:i>", methods=["POST"])
def progress(i):
    try:
        n = float(request.form["progress"])
        if not 0 <= n <= 100:
            raise ValueError()
        status = "Completed" if n == 100 else ("In Progress" if n > 0 else "Not Started")
        with db() as c:
            c.execute("UPDATE tasks SET progress=?,status=? WHERE id=?", (n, status, i))
    except ValueError:
        flash("Progress must be between 0 and 100.")
    return redirect(url_for("schedule"))


@app.route("/cost", methods=["GET", "POST"])
def cost():
    if request.method == "POST":
        try:
            amount = float(request.form["amount"]); desc = request.form["description"].strip()
            if amount < 0 or not desc:
                raise ValueError()
            with db() as c:
                c.execute("INSERT INTO expenses(description,amount) VALUES(?,?)", (desc, amount))
        except ValueError:
            flash("Enter a description and non-negative amount.")
        return redirect(url_for("cost"))
    p = rows("SELECT * FROM project")[0]; tasks = rows("SELECT * FROM tasks")
    pv = sum(t["cost"] for t in tasks) * 0.65
    ev = sum(t["cost"] * t["progress"] / 100 for t in tasks)
    ac = val("SELECT SUM(amount) FROM expenses") + ev
    cpi = ev / ac if ac else 0
    spi = ev / pv if pv else 0
    planned = sum(t["cost"] for t in tasks)
    items = rows("SELECT * FROM expenses")
    body = """<div class="grid kpis">
 <div class="card kpi"><div class="ico b1">🏦</div><div><div class="l">Budget baseline</div><div class="v">PKR {{'{:,.0f}'.format(p.budget)}}</div></div></div>
 <div class="card kpi"><div class="ico b5">📋</div><div><div class="l">Planned activity cost</div><div class="v">PKR {{'{:,.0f}'.format(planned)}}</div></div></div>
 <div class="card kpi"><div class="ico b2">🎯</div><div><div class="l">PV (assumed 65%)</div><div class="v">PKR {{'{:,.0f}'.format(pv)}}</div></div></div>
 <div class="card kpi"><div class="ico b2">✅</div><div><div class="l">EV</div><div class="v">PKR {{'{:,.0f}'.format(ev)}}</div></div></div>
 <div class="card kpi"><div class="ico b3">💳</div><div><div class="l">AC</div><div class="v">PKR {{'{:,.0f}'.format(ac)}}</div></div></div>
 <div class="card kpi"><div class="ico b4">📉</div><div><div class="l">CPI</div><div class="v {{'warn' if cpi<1 else ''}}">{{'%.2f'|format(cpi)}}</div></div></div>
 <div class="card kpi"><div class="ico b4">📆</div><div><div class="l">SPI</div><div class="v {{'warn' if spi<1 else ''}}">{{'%.2f'|format(spi)}}</div></div></div></div>
<section><h3>Record expense</h3><form method="post" class="f"><input name="description" placeholder="Expense description" required style="min-width:260px"><input name="amount" type="number" min="0" step="100" placeholder="Actual cost PKR" required><button>Record expense</button></form>
<p class="note"><b>Interpretation:</b> CPI = EV / AC; SPI = EV / PV. Values below 1 indicate cost inefficiency or schedule lag. PV is a demonstration estimate (65% of activity budget), not a date-driven baseline.</p></section>
<section><h3>Expense log</h3><div class="tw"><table><tr><th>Description</th><th>Amount PKR</th></tr>{% for x in items %}<tr><td>{{x.description}}</td><td>{{'{:,.0f}'.format(x.amount)}}</td></tr>{% endfor %}</table></div>
{% if ac>p.budget %}<p class="warn">WARNING: actual cost exceeds the approved budget.</p>{% endif %}{% if cpi<0.9 %}<p class="warn">WARNING: CPI below 0.90 threshold.</p>{% endif %}{% if spi<0.9 %}<p class="warn">WARNING: SPI below 0.90 threshold.</p>{% endif %}</section>"""
    return page("Cost & EVM", "/cost", body, p=p, planned=planned, pv=pv, ev=ev, ac=ac, cpi=cpi, spi=spi, items=items)


@app.route("/quality", methods=["GET", "POST"])
def quality():
    if request.method == "POST":
        with db() as c:
            c.execute("INSERT INTO defects(title,severity,assignee,status) VALUES(?,?,?,?)",
                      (request.form["title"], request.form["severity"], request.form["assignee"], "Open"))
        return redirect(url_for("quality"))
    items = rows("SELECT * FROM defects")
    body = """<section><h3>Report defect</h3><form method="post" class="f"><input name="title" placeholder="Defect description" required style="min-width:260px"><select name="severity"><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></select><input name="assignee" placeholder="Assigned team member" required><button>Save defect</button></form></section>
<section><h3>Defect register</h3><div class="tw"><table><tr><th>Defect</th><th>Severity</th><th>Assigned</th><th>Status</th><th>Action</th></tr>
{% for d in items %}<tr><td>{{d.title}}</td><td><span class="badge {{d.severity|slug}}">{{d.severity}}</span></td><td>{{d.assignee}}</td><td><span class="badge {{d.status|slug}}">{{d.status}}</span></td>
<td>{% if d.status!='Resolved' %}<form method="post" action="/resolve/{{d.id}}"><button class="sm ok">Mark resolved</button></form>{% endif %}</td></tr>{% endfor %}</table></div></section>
<section><h3>Quality checklist</h3><div class="li"><span>Appointment slot conflicts tested</span></div><div class="li"><span>Duplicate patient records prevented</span></div><div class="li"><span>Billing calculations verified</span></div><div class="li"><span>Role-based access and privacy checked</span></div><div class="li"><span>Load and response-time tests completed</span></div><div class="li"><span>Backup and recovery verified</span></div>
<p class="warn" style="margin-top:12px">Do not deploy while critical defects remain unresolved.</p></section>"""
    return page("Quality & Defects", "/quality", body, items=items)


@app.route("/resolve/<int:i>", methods=["POST"])
def resolve(i):
    with db() as c:
        c.execute("UPDATE defects SET status='Resolved' WHERE id=?", (i,))
    return redirect(url_for("quality"))


@app.route("/risks", methods=["GET", "POST"])
def risks():
    if request.method == "POST":
        try:
            l = int(request.form["likelihood"]); i = int(request.form["impact"])
            if not 1 <= l <= 5 or not 1 <= i <= 5:
                raise ValueError()
            with db() as c:
                c.execute("INSERT INTO risks(title,likelihood,impact,response,status) VALUES(?,?,?,?,?)", (request.form["title"], l, i, request.form["response"], "Open"))
        except ValueError:
            flash("Likelihood and impact must be between 1 and 5.")
        return redirect(url_for("risks"))
    items = rows("SELECT * FROM risks ORDER BY likelihood*impact DESC")
    body = """<section><h3>Add risk</h3><form method="post" class="f"><input name="title" placeholder="Risk or issue" required style="min-width:240px"><input name="likelihood" type="number" min="1" max="5" placeholder="Likelihood 1-5" required><input name="impact" type="number" min="1" max="5" placeholder="Impact 1-5" required><input name="response" placeholder="Preventive/corrective action" required><button>Add risk</button></form></section>
<section><h3>Risk register (prioritized)</h3><div class="tw"><table><tr><th>Risk</th><th>Likelihood</th><th>Impact</th><th>Score</th><th>Priority</th><th>Response / PDPC action</th><th>Status</th></tr>
{% for r in items %}{% set s=r.likelihood*r.impact %}<tr><td><b>{{r.title}}</b></td><td>{{r.likelihood}}</td><td>{{r.impact}}</td><td>{{s}}/25</td><td><span class="badge {{'high' if s>=15 else ('medium' if s>=8 else 'low')}}">{{'High' if s>=15 else ('Medium' if s>=8 else 'Low')}}</span></td><td>{{r.response}}</td><td><span class="badge {{r.status|slug}}">{{r.status}}</span></td></tr>{% endfor %}</table></div>
<p class="note">PDPC example: incorrect appointments → add validation + automated tests → QA retest → block release if defect persists.</p></section>"""
    return page("Risk Control", "/risks", body, items=items)


@app.route("/report")
def report():
    p = rows("SELECT * FROM project")[0]; tasks = rows("SELECT * FROM tasks")
    defects = rows("SELECT * FROM defects"); changes = rows("SELECT * FROM changes")
    pending = sum(x["status"] == "Pending" for x in changes)
    critical = sum(x["severity"] == "Critical" and x["status"] != "Resolved" for x in defects)
    delayed = sum(x["status"] == "Delayed" for x in tasks)
    progress = sum(t["progress"] for t in tasks) / max(1, len(tasks))
    body = """<section><h3>{{p.name}}</h3>
<div class="grid kpis" style="margin-top:14px">
 <div class="card"><div class="l" style="color:var(--muted)">Approved budget</div><div class="v" style="font-size:20px;font-weight:700">PKR {{'{:,.0f}'.format(p.budget)}}</div></div>
 <div class="card"><div class="l" style="color:var(--muted)">Approved duration</div><div class="v" style="font-size:20px;font-weight:700">{{p.weeks}} weeks</div></div>
 <div class="card"><div class="l" style="color:var(--muted)">Average progress</div><div class="v" style="font-size:20px;font-weight:700">{{'%.1f'|format(progress)}}%</div></div>
 <div class="card"><div class="l" style="color:var(--muted)">Pending changes</div><div class="v" style="font-size:20px;font-weight:700">{{pending}}</div></div>
 <div class="card"><div class="l" style="color:var(--muted)">Delayed tasks</div><div class="v" style="font-size:20px;font-weight:700">{{delayed}}</div></div>
 <div class="card"><div class="l" style="color:var(--muted)">Critical defects</div><div class="v {{'warn' if critical else ''}}" style="font-size:20px;font-weight:700">{{critical}}</div></div></div>
<h3>Recommendations</h3><ol><li>Resolve appointment scheduling and duplicate-record defects.</li><li>Approve or reject each change request before work starts.</li><li>Review EVM indicators and actual expenses weekly.</li><li>Validate dependency dates and agree a revised baseline after change approval.</li></ol>
<button onclick="window.print()">Print / Save as PDF</button></section>"""
    return page("Project Status Report", "/report", body, p=p, progress=progress, pending=pending, critical=critical, delayed=delayed)


if __name__ == "__main__":
    app.run(debug=True)