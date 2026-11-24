"""Charts for the article: performance and memory comparison.

Outputs (300 dpi PNG, Noto fonts, Morandi-ish restrained palette):
  fig1: throughput (rows/s) by scale, 3 methods
  fig2: dictionary memory footprint vs number of distinct values (log-log)
"""
import json, os
import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11

BASE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(BASE, "bench_results.json")))

# palette: restrained, print-friendly
C_DRIM = "#2F5D8C"   # muted blue
C_DICT = "#B0713F"   # muted amber
C_RAND = "#7A7A7A"   # grey
GRID = dict(axis="y", color="#DDDDDD", linewidth=0.8, zorder=0)

# ---------------- fig 1: throughput by scale ----------------
scale = [r for r in data["scale"]]
ns = sorted(set(r["n_users"] for r in scale))
series = {"DRIM": [], "DICT": [], "RANDOM": []}
for meth in series:
    for n in ns:
        rec = next(r for r in scale if r["n_users"] == n and r["method"] == meth)
        series[meth].append(rec["rows_per_s"])

fig, ax = plt.subplots(figsize=(7.0, 4.0), constrained_layout=True)
x = range(len(ns))
w = 0.26
ax.bar([i - w for i in x], series["DRIM"], width=w, color=C_DRIM, label="DRIM", zorder=3)
ax.bar(list(x), series["DICT"], width=w, color=C_DICT, label="Словарный подход", zorder=3)
ax.bar([i + w for i in x], series["RANDOM"], width=w, color=C_RAND, label="Случайная замена", zorder=3)
ax.set_xticks(list(x))
ax.set_xticklabels([f"{n//1000} тыс." for n in ns])
ax.set_xlabel("Число строк users (n), всего обрабатывается 4n строк")
ax.set_ylabel("Пропускная способность, строк/с")
ax.set_title("Пропускная способность маскирования по масштабу данных")
ax.grid(**GRID)
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False)
ax.set_axisbelow(True)
fig.savefig(os.path.join(BASE, "fig1_throughput.png"), dpi=300)
plt.close(fig)

# ---------------- fig 2: dictionary memory vs distinct values ----------------
mem = data["memory"]
ks = [m["k"] for m in mem]
dm = [m["dict_mb"] for m in mem]

fig, ax = plt.subplots(figsize=(7.0, 4.0), constrained_layout=True)
ax.plot(ks, dm, "o-", color=C_DICT, label="Словарь соответствий", linewidth=2, markersize=6, zorder=3)
ax.axhline(y=32/1048576, color=C_DRIM, linestyle="--", linewidth=2,
           label="DRIM (32 байта, константа)", zorder=3)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Число уникальных обезличиваемых значений k")
ax.set_ylabel("Память состояния, МБ")
ax.set_title("Память состояния метода при росте числа уникальных значений")
ax.set_xticks(ks)
ax.set_xticklabels([f"{k:,}".replace(",", " ") for k in ks])
ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
ax.grid(axis="both", which="major", color="#DDDDDD", linewidth=0.8, zorder=0)
ax.grid(axis="both", which="minor", color="#EEEEEE", linewidth=0.5, zorder=0)
ax.legend(loc="upper left", frameon=False)
ax.set_axisbelow(True)
fig.savefig(os.path.join(BASE, "fig2_memory.png"), dpi=300)
plt.close(fig)

for f in ("fig1_throughput.png", "fig2_memory.png"):
    p = os.path.join(BASE, f)
    print(p, os.path.getsize(p), "bytes")
