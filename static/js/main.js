const API = '';

// ── NAV ──────────────────────────────────────────
function switchPage(id, btn) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('page-' + id).classList.add('active');
  btn.classList.add('active');
  if (id === 'dashboard') loadDashboard();
  if (id === 'records')   loadRecords();
}

// ── TOAST ────────────────────────────────────────
function toast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + type;
  clearTimeout(t._to);
  t._to = setTimeout(() => t.className = '', 3200);
}

// ── HELPERS ───────────────────────────────────────
function gradeBadge(g) {
  const map = {'A+':'g-ap','A':'g-a','B':'g-b','C':'g-c','D':'g-d','F':'g-f'};
  return `<span class="grade ${map[g]||'g-f'}">${g}</span>`;
}
function coursePills(courses) {
  if (!courses || !courses.length) return '<span style="color:var(--muted2);font-size:11px">—</span>';
  return courses.map(c => `<span class="pill">${c}</span>`).join('');
}

// ── REGISTER ──────────────────────────────────────
async function registerStudent() {
  const sid = document.getElementById('reg-sid').value.trim();
  const name = document.getElementById('reg-name').value.trim();
  const marks = parseFloat(document.getElementById('reg-marks').value);
  if (!sid || !name || isNaN(marks)) { toast('Fill all fields.', 'error'); return; }
  if (marks < 0 || marks > 100) { toast('Marks must be 0–100.', 'error'); return; }
  try {
    const r = await fetch(`${API}/register`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sid,name,marks})});
    const d = await r.json();
    if (!r.ok) { toast(d.detail,'error'); return; }
    toast(d.message); clearReg();
  } catch { toast('Server error.','error'); }
}
function clearReg() {
  ['reg-sid','reg-name','reg-marks'].forEach(id => document.getElementById(id).value='');
}
async function updateMarks() {
  const sid = document.getElementById('upd-sid').value.trim();
  const marks = parseFloat(document.getElementById('upd-marks').value);
  if (!sid || isNaN(marks)) { toast('Fill all fields.','error'); return; }
  try {
    const r = await fetch(`${API}/marks`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({sid,marks})});
    const d = await r.json();
    if (!r.ok) { toast(d.detail,'error'); return; }
    toast(`Updated — new grade: ${d.grade}`);
    document.getElementById('upd-sid').value='';
    document.getElementById('upd-marks').value='';
  } catch { toast('Server error.','error'); }
}

// ── COURSE ────────────────────────────────────────
async function enrollCourse() {
  const sid = document.getElementById('c-sid').value.trim();
  const course = document.getElementById('c-course').value.trim();
  if (!sid || !course) { toast('Fill all fields.','error'); return; }
  try {
    const r = await fetch(`${API}/course`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sid,course})});
    const d = await r.json();
    if (!r.ok) { toast(d.detail,'error'); return; }
    toast(d.message);
    document.getElementById('c-sid').value='';
    document.getElementById('c-course').value='';
  } catch { toast('Server error.','error'); }
}

// ── FEES ──────────────────────────────────────────
async function saveFee() {
  const sid = document.getElementById('f-sid').value.trim();
  const hostel_fee = parseFloat(document.getElementById('f-hostel').value);
  const mess_fee = parseFloat(document.getElementById('f-mess').value);
  if (!sid || isNaN(hostel_fee) || isNaN(mess_fee)) { toast('Fill all fields.','error'); return; }
  try {
    const r = await fetch(`${API}/fee`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sid,hostel_fee,mess_fee})});
    const d = await r.json();
    if (!r.ok) { toast(d.detail,'error'); return; }
    toast(d.message);
    ['f-sid','f-hostel','f-mess'].forEach(id => document.getElementById(id).value='');
  } catch { toast('Server error.','error'); }
}

// ── SEARCH ────────────────────────────────────────
async function searchStudent() {
  const sid = document.getElementById('s-sid').value.trim();
  if (!sid) { toast('Enter a Student ID.','error'); return; }
  const box = document.getElementById('search-result');
  try {
    const r = await fetch(`${API}/student/${sid}`);
    const d = await r.json();
    if (!r.ok) { box.innerHTML=`<div class="card"><p style="color:var(--red);font-family:'DM Mono',monospace;font-size:13px">${d.detail}</p></div>`; return; }
    box.innerHTML=`
      <div class="card"><h3>Result</h3>
        <div class="student-card">
          <div class="field-item"><div class="fi-label">ID</div><div class="fi-val">${d.sid}</div></div>
          <div class="field-item"><div class="fi-label">Name</div><div class="fi-val">${d.name}</div></div>
          <div class="field-item"><div class="fi-label">Marks</div><div class="fi-val">${d.marks}</div></div>
          <div class="field-item"><div class="fi-label">Grade</div><div class="fi-val">${gradeBadge(d.grade)}</div></div>
          <div class="field-item"><div class="fi-label">Hostel Fee</div><div class="fi-val">₹${d.hostel_fee.toLocaleString()}</div></div>
          <div class="field-item"><div class="fi-label">Mess Fee</div><div class="fi-val">₹${d.mess_fee.toLocaleString()}</div></div>
          <div class="field-item full"><div class="fi-label">Courses</div><div class="fi-val" style="margin-top:6px">${coursePills(d.courses)}</div></div>
        </div>
        <div class="btn-row" style="margin-top:16px">
          <button class="btn btn-danger btn-sm" onclick="deleteStudent('${d.sid}')">Delete Student</button>
        </div>
      </div>`;
  } catch { toast('Server error.','error'); }
}
function clearSearch() {
  document.getElementById('s-sid').value='';
  document.getElementById('search-result').innerHTML='';
}
async function deleteStudent(sid) {
  if (!confirm(`Delete student ${sid}? This cannot be undone.`)) return;
  try {
    const r = await fetch(`${API}/student/${sid}`,{method:'DELETE'});
    const d = await r.json();
    if (!r.ok) { toast(d.detail,'error'); return; }
    toast(d.message);
    document.getElementById('search-result').innerHTML='';
    document.getElementById('s-sid').value='';
  } catch { toast('Server error.','error'); }
}

// ── RECORDS ───────────────────────────────────────
async function loadRecords() {
  const by = document.getElementById('sort-by')?.value||'marks';
  const order = document.getElementById('sort-order')?.value||'desc';
  try {
    const r = await fetch(`${API}/sort?by=${by}&order=${order}`);
    const data = await r.json();
    const tbody = document.getElementById('records-table');
    if (!data.length) { tbody.innerHTML='<tr><td colspan="8"><div class="empty"><span>⬡</span>No records</div></td></tr>'; return; }
    tbody.innerHTML=data.map(s=>`
      <tr>
        <td>${s.sid}</td><td>${s.name}</td><td>${s.marks}</td>
        <td>${gradeBadge(s.grade)}</td><td>${coursePills(s.courses)}</td>
        <td>₹${s.hostel_fee.toLocaleString()}</td><td>₹${s.mess_fee.toLocaleString()}</td>
        <td><button class="btn btn-danger btn-sm" onclick="deleteStudent('${s.sid}')">✕</button></td>
      </tr>`).join('');
  } catch { toast('Failed to load records.','error'); }
}
document.getElementById('sort-by')?.addEventListener('change', loadRecords);
document.getElementById('sort-order')?.addEventListener('change', loadRecords);

// ── DASHBOARD ─────────────────────────────────────
async function loadDashboard() {
  try {
    const [recR, anaR] = await Promise.all([
      fetch(`${API}/sort?by=marks&order=desc`),
      fetch(`${API}/analysis`)
    ]);
    const students = await recR.json();
    const ana = await anaR.json();
    if (!ana.message) {
      document.getElementById('d-total').textContent = ana.total;
      document.getElementById('d-avg').textContent   = ana.average;
      document.getElementById('d-pass').textContent  = ana.pass_rate + '%';
      document.getElementById('d-high').textContent  = ana.highest;
    }
    const tbody = document.getElementById('dash-table');
    if (!students.length) { tbody.innerHTML='<tr><td colspan="5"><div class="empty"><span>⬡</span>No students yet</div></td></tr>'; return; }
    tbody.innerHTML=students.slice(0,8).map(s=>`
      <tr>
        <td>${s.sid}</td><td>${s.name}</td><td>${s.marks}</td>
        <td>${gradeBadge(s.grade)}</td><td>${coursePills(s.courses)}</td>
      </tr>`).join('');
  } catch {}
}

// ── ANALYTICS (Matplotlib charts from backend) ────
async function loadAnalysis() {
  const area = document.getElementById('charts-area');
  area.innerHTML = '<div class="chart-loading"><div class="spinner"></div>Generating charts with Matplotlib…</div>';
  try {
    const r = await fetch(`${API}/analysis`);
    const d = await r.json();
    if (d.message) {
      area.innerHTML = `<div class="chart-loading">${d.message}</div>`;
      return;
    }

    // Stats
    document.getElementById('a-total').textContent = d.total;
    document.getElementById('a-avg').textContent   = d.average;
    document.getElementById('a-med').textContent   = d.median;
    document.getElementById('a-std').textContent   = d.std_dev;
    document.getElementById('a-pass').textContent  = d.pass_rate + '%';
    document.getElementById('a-p75').textContent   = d.percentile_75;
    document.getElementById('a-high').textContent  = d.highest;
    document.getElementById('a-low').textContent   = d.lowest;

    // Top / Bottom
    const pg = document.getElementById('perf-grid');
    pg.style.display = 'grid';
    document.getElementById('top-students').innerHTML =
      d.top_students.map(s=>`
        <div class="perf-row">
          <span class="perf-name">${s.name}</span>
          <span style="display:flex;gap:8px;align-items:center">
            ${gradeBadge(s.grade)}
            <span class="perf-marks">${s.marks}</span>
          </span>
        </div>`).join('');
    document.getElementById('bottom-students').innerHTML =
      d.bottom_students.map(s=>`
        <div class="perf-row">
          <span class="perf-name">${s.name}</span>
          <span style="display:flex;gap:8px;align-items:center">
            ${gradeBadge(s.grade)}
            <span class="perf-marks">${s.marks}</span>
          </span>
        </div>`).join('');

    // Charts — 4 Matplotlib images from backend
    area.innerHTML = `
      <div class="chart-grid">
        <div class="chart-card wide">
          <div class="chart-title">Bar Chart — Marks per Student</div>
          <img src="${d.chart_bar}" alt="Bar chart">
        </div>
        <div class="chart-card wide">
          <div class="chart-title">Line Chart — Performance Trend + NumPy Trend Line</div>
          <img src="${d.chart_line}" alt="Line chart">
        </div>
        <div class="chart-card">
          <div class="chart-title">Pie Chart — Grade Distribution</div>
          <img src="${d.chart_pie}" alt="Pie chart">
        </div>
        <div class="chart-card">
          <div class="chart-title">Histogram — Marks Distribution (NumPy bins)</div>
          <img src="${d.chart_histogram}" alt="Histogram">
        </div>
      </div>`;
  } catch(e) {
    area.innerHTML = `<div class="chart-loading" style="color:var(--red)">Failed to load analytics. Is the server running?</div>`;
  }
}

// ── INIT ──────────────────────────────────────────
loadDashboard();