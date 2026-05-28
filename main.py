from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json, os, io, base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MaxNLocator

app = FastAPI(title="Smart Campus System")
app.mount("/static", StaticFiles(directory="static"), name="static")

DATA_FILE = "students.json"

# ── Matplotlib global dark theme ─────────────────────────────────────────────
DARK   = "#080808"
SURF   = "#111111"
SURF2  = "#1a1a1a"
BORDER = "#2a2a2a"
TEXT   = "#f0f0f0"
MUTED  = "#666666"
ACCENT = "#e8ff47"
GREEN  = "#4dff9b"
BLUE   = "#4d9fff"
ORANGE = "#ff9b4d"
RED    = "#ff4d4d"

GRADE_COLORS = {
    "A+": GREEN,
    "A":  "#a8ffd0",
    "B":  BLUE,
    "C":  ORANGE,
    "D":  "#cc7733",
    "F":  RED,
}

def set_dark_style():
    plt.rcParams.update({
        "figure.facecolor":  DARK,
        "axes.facecolor":    SURF,
        "axes.edgecolor":    BORDER,
        "axes.labelcolor":   MUTED,
        "axes.titlecolor":   TEXT,
        "xtick.color":       MUTED,
        "ytick.color":       MUTED,
        "text.color":        TEXT,
        "grid.color":        BORDER,
        "grid.linewidth":    0.6,
        "font.family":       "monospace",
        "figure.dpi":        130,
    })

def fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def calc_grade(marks: float) -> str:
    if marks >= 90: return "A+"
    if marks >= 80: return "A"
    if marks >= 70: return "B"
    if marks >= 60: return "C"
    if marks >= 50: return "D"
    return "F"

def to_df(db: dict) -> pd.DataFrame:
    if not db:
        return pd.DataFrame()
    rows = []
    for sid, s in db.items():
        rows.append({
            "sid":        sid,
            "name":       s["name"],
            "marks":      float(s["marks"]),
            "grade":      s["grade"],
            "courses":    s.get("courses", []),
            "hostel_fee": float(s.get("hostel_fee", 0)),
            "mess_fee":   float(s.get("mess_fee", 0)),
        })
    return pd.DataFrame(rows)

def default_student(sid, name, marks):
    return {"sid": sid, "name": name, "marks": marks,
            "grade": calc_grade(marks), "courses": [],
            "hostel_fee": 0, "mess_fee": 0}

# ── Pydantic models ───────────────────────────────────────────────────────────
class RegisterModel(BaseModel):
    sid: str; name: str; marks: float

class CourseModel(BaseModel):
    sid: str; course: str

class FeeModel(BaseModel):
    sid: str; hostel_fee: float; mess_fee: float

class UpdateMarksModel(BaseModel):
    sid: str; marks: float

# ── Chart generators ──────────────────────────────────────────────────────────

def make_bar_chart(df: pd.DataFrame) -> str:
    """Bar chart — marks per student (sorted descending)."""
    set_dark_style()
    df_s = df.sort_values("marks", ascending=False).reset_index(drop=True)
    colors = [GRADE_COLORS.get(g, MUTED) for g in df_s["grade"]]

    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(df_s["name"], df_s["marks"], color=colors,
                  width=0.6, zorder=2, edgecolor=SURF, linewidth=0.5)

    # value labels on top of bars
    for bar, val in zip(bars, df_s["marks"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{val:.0f}", ha="center", va="bottom",
                fontsize=8, color=TEXT)

    ax.set_ylim(0, 110)
    ax.set_ylabel("Marks", fontsize=9)
    ax.set_title("Student Marks — Bar Chart", fontsize=11, pad=14, color=TEXT)
    ax.axhline(50, color=RED, linewidth=0.8, linestyle="--", zorder=1, alpha=0.6)
    ax.axhline(float(df["marks"].mean()), color=ACCENT,
               linewidth=0.8, linestyle="--", zorder=1, alpha=0.7)
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    plt.xticks(rotation=30, ha="right", fontsize=8)

    legend = [
        mpatches.Patch(color=ACCENT, label=f"Avg ({df['marks'].mean():.1f})"),
        mpatches.Patch(color=RED,    label="Pass line (50)"),
    ]
    ax.legend(handles=legend, fontsize=8, facecolor=SURF2,
              edgecolor=BORDER, labelcolor=TEXT)
    fig.tight_layout()
    return fig_to_b64(fig)


def make_pie_chart(df: pd.DataFrame) -> str:
    """Pie chart — grade distribution."""
    set_dark_style()
    grade_order = ["A+", "A", "B", "C", "D", "F"]
    counts = df["grade"].value_counts()
    labels  = [g for g in grade_order if g in counts.index]
    sizes   = [counts[g] for g in labels]
    colors  = [GRADE_COLORS[g] for g in labels]

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors,
        autopct="%1.0f%%", startangle=140,
        pctdistance=0.78,
        wedgeprops={"linewidth": 1.2, "edgecolor": DARK},
    )
    for t in texts:
        t.set_color(TEXT); t.set_fontsize(10)
    for at in autotexts:
        at.set_color(DARK); at.set_fontsize(9); at.set_fontweight("bold")

    ax.set_title("Grade Distribution — Pie Chart", fontsize=11, pad=16, color=TEXT)
    fig.tight_layout()
    return fig_to_b64(fig)


def make_line_chart(df: pd.DataFrame) -> str:
    """Line chart — marks ranked from highest to lowest with trend line."""
    set_dark_style()
    df_s = df.sort_values("marks", ascending=False).reset_index(drop=True)
    x = np.arange(len(df_s))
    y = df_s["marks"].values

    # numpy polyfit trend line
    if len(x) >= 2:
        z  = np.polyfit(x, y, 1)
        p  = np.poly1d(z)
        trend = p(x)
    else:
        trend = y.copy()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(x, y, color=ACCENT, linewidth=2, zorder=3, label="Marks")
    ax.fill_between(x, y, alpha=0.08, color=ACCENT, zorder=2)
    ax.plot(x, trend, color=BLUE, linewidth=1.2,
            linestyle="--", zorder=4, label="Trend (polyfit)")

    # scatter dots colored by grade
    scatter_colors = [GRADE_COLORS.get(g, MUTED) for g in df_s["grade"]]
    ax.scatter(x, y, color=scatter_colors, s=50, zorder=5, edgecolors=DARK, linewidths=0.5)

    ax.axhline(50, color=RED, linewidth=0.8, linestyle=":", alpha=0.6, label="Pass line")
    ax.set_xticks(x)
    ax.set_xticklabels(df_s["name"], rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Marks", fontsize=9)
    ax.set_title("Performance Trend — Line Chart", fontsize=11, pad=14, color=TEXT)
    ax.set_ylim(0, 110)
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, facecolor=SURF2, edgecolor=BORDER, labelcolor=TEXT)
    fig.tight_layout()
    return fig_to_b64(fig)


def make_histogram(df: pd.DataFrame) -> str:
    """Histogram — marks distribution with numpy bins."""
    set_dark_style()
    marks = df["marks"].values

    # numpy histogram for custom bins
    bins  = np.arange(0, 111, 10)
    counts, edges = np.histogram(marks, bins=bins)

    # color each bin by grade zone
    bin_colors = []
    for edge in edges[:-1]:
        if edge >= 90:   bin_colors.append(GREEN)
        elif edge >= 80: bin_colors.append("#a8ffd0")
        elif edge >= 70: bin_colors.append(BLUE)
        elif edge >= 60: bin_colors.append(ORANGE)
        elif edge >= 50: bin_colors.append("#cc7733")
        else:            bin_colors.append(RED)

    fig, ax = plt.subplots(figsize=(9, 4))
    for i, (left, right, cnt, col) in enumerate(
            zip(edges[:-1], edges[1:], counts, bin_colors)):
        ax.bar(left, cnt, width=(right - left) * 0.9, align="edge",
               color=col, alpha=0.75, edgecolor=DARK, linewidth=0.5, zorder=2)
        if cnt > 0:
            ax.text(left + (right - left) / 2, cnt + 0.1,
                    str(cnt), ha="center", va="bottom",
                    fontsize=8, color=TEXT)

    ax.set_xlabel("Marks Range", fontsize=9)
    ax.set_ylabel("No. of Students", fontsize=9)
    ax.set_title("Marks Distribution — Histogram", fontsize=11, pad=14, color=TEXT)
    ax.set_xticks(bins)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)

    # zone legend
    legend_items = [
        mpatches.Patch(color=GREEN,    label="A+ (90–100)"),
        mpatches.Patch(color="#a8ffd0",label="A  (80–89)"),
        mpatches.Patch(color=BLUE,     label="B  (70–79)"),
        mpatches.Patch(color=ORANGE,   label="C  (60–69)"),
        mpatches.Patch(color="#cc7733",label="D  (50–59)"),
        mpatches.Patch(color=RED,      label="F  (0–49)"),
    ]
    ax.legend(handles=legend_items, fontsize=7.5, facecolor=SURF2,
              edgecolor=BORDER, labelcolor=TEXT, ncol=2)
    fig.tight_layout()
    return fig_to_b64(fig)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.post("/register")
def register_student(data: RegisterModel):
    db = load_data()
    if data.sid in db:
        raise HTTPException(400, "Student ID already exists.")
    db[data.sid] = default_student(data.sid, data.name, data.marks)
    save_data(db)
    return {"message": f"Student '{data.name}' registered successfully."}

@app.get("/records")
def get_records():
    return load_data()

@app.get("/student/{sid}")
def get_student(sid: str):
    db = load_data()
    if sid not in db:
        raise HTTPException(404, "Student not found.")
    return db[sid]

@app.delete("/student/{sid}")
def delete_student(sid: str):
    db = load_data()
    if sid not in db:
        raise HTTPException(404, "Student not found.")
    name = db[sid]["name"]
    del db[sid]
    save_data(db)
    return {"message": f"Student '{name}' deleted."}

@app.post("/course")
def enroll_course(data: CourseModel):
    db = load_data()
    if data.sid not in db:
        raise HTTPException(404, "Student not found.")
    if data.course in db[data.sid]["courses"]:
        raise HTTPException(400, "Already enrolled in this course.")
    db[data.sid]["courses"].append(data.course)
    save_data(db)
    return {"message": f"Enrolled in '{data.course}'."}

@app.post("/fee")
def save_fee(data: FeeModel):
    db = load_data()
    if data.sid not in db:
        raise HTTPException(404, "Student not found.")
    db[data.sid]["hostel_fee"] = data.hostel_fee
    db[data.sid]["mess_fee"]   = data.mess_fee
    save_data(db)
    return {"message": "Fee details saved."}

@app.patch("/marks")
def update_marks(data: UpdateMarksModel):
    db = load_data()
    if data.sid not in db:
        raise HTTPException(404, "Student not found.")
    db[data.sid]["marks"] = data.marks
    db[data.sid]["grade"] = calc_grade(data.marks)
    save_data(db)
    return {"message": "Marks updated.", "grade": db[data.sid]["grade"]}

@app.get("/sort")
def sort_students(by: str = "marks", order: str = "desc"):
    db = load_data()
    df = to_df(db)
    if df.empty:
        return []
    key = by if by in ("marks", "name", "sid") else "marks"
    asc = order != "desc"
    df = df.sort_values(key, ascending=asc)
    return df.to_dict(orient="records")

@app.get("/analysis")
def analysis():
    db = load_data()
    if not db:
        return {"message": "No students registered yet."}

    df = to_df(db)
    marks = df["marks"].values  # numpy array

    # ── Stats via NumPy + Pandas ──────────────────────────────────────────────
    stats = {
        "total":     int(len(marks)),
        "average":   round(float(np.mean(marks)), 2),
        "median":    round(float(np.median(marks)), 2),
        "std_dev":   round(float(np.std(marks)), 2),
        "highest":   float(np.max(marks)),
        "lowest":    float(np.min(marks)),
        "pass_rate": round(float(np.sum(marks >= 50) / len(marks) * 100), 1),
        "grade_distribution": df["grade"].value_counts().to_dict(),
        # percentile ranks via numpy
        "percentile_75": round(float(np.percentile(marks, 75)), 2),
        "percentile_25": round(float(np.percentile(marks, 25)), 2),
    }

    # ── Top / Bottom 3 via Pandas ─────────────────────────────────────────────
    stats["top_students"]    = df.nlargest(3, "marks")[["sid","name","marks","grade"]].to_dict(orient="records")
    stats["bottom_students"] = df.nsmallest(3, "marks")[["sid","name","marks","grade"]].to_dict(orient="records")

    # ── Charts via Matplotlib ─────────────────────────────────────────────────
    stats["chart_bar"]       = make_bar_chart(df)
    stats["chart_pie"]       = make_pie_chart(df)
    stats["chart_line"]      = make_line_chart(df)
    stats["chart_histogram"] = make_histogram(df)

    return stats

@app.post("/save")
def save_records():
    db = load_data()
    save_data(db)
    return {"message": f"Records saved ({len(db)} students)."}