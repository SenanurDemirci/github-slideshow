"""Yeni stilde sunum için görseller (PNG) ve veriler (JSON).
Kullanım: python make_assets.py <leo_geo_doppler.py + ntn_3gpp.py klasörü> <çıktı klasörü>"""
import sys, json, os
CODE, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, CODE)
os.makedirs(OUT, exist_ok=True)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import leo_geo_doppler as m
import ntn_3gpp as n3

# ---------------------------------------------------------------- yeni renk paleti (simülasyon görüntüleri)
TEAL, GREEN, CORAL, IDLE = "#0FA3B1", "#3AAF85", "#E4572E", "#9AA5B1"
m.COL_SERVE, m.COL_RISE, m.COL_SET, m.COL_IDLE = TEAL, GREEN, CORAL, IDLE
m.COL_EARTH, m.COL_NOCOV = "#E3EAF1", "#CBD3DC"
m.SAT_PAL = ["#0FA3B1", "#3AAF85", "#E4572E", "#3A7BD5", "#7B5EA7", "#E08E0B"]
UE_COL = ["#7B5EA7", "#3A7BD5", "#E08E0B", "#C2185B"]          # UAV, A/C, HST, SHIP
for u, c in zip(m.UES, UE_COL):
    u["color"] = c
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": "#5B6B7F", "axes.labelcolor": "#0B1D33",
                     "xtick.color": "#0B1D33", "ytick.color": "#0B1D33"})

W, H, DPI = 12.35, 8.48, 150


def render(sim, path):
    app = m.App(sim, interactive=False)
    fig = app.fig
    fig.set_size_inches(W, H)
    for ax in (app.ax_info, app.ax_orbit, app.ax_dop):
        ax.remove()
    cur = sim.current()
    app.draw_local(cur)
    app.ax_local.set_position([0.07, 0.075, 0.915, 0.875])
    fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)
    return cur


def fmt_hz(f):
    s = "−" if f < 0 else "+"; a = abs(f)
    return f"{s}{a/1000:.1f} kHz" if a >= 1000 else f"{s}{a:.0f} Hz"


def values(sim, cur):
    geo = sim.layer == "GEO"
    keys = ["sat", "α", "d", "f_d", "df_d/dt", "RTT", "PL", "CNR DL"]
    rows = {k: [] for k in keys}
    for i, u in enumerate(m.UES):
        L = (cur[i]["geo"] if cur[i]["geo"]["el"] >= sim.el_min else None) if geo else cur[i]["leo"]
        rows["sat"].append(("GEO" if L else "—") if geo else m.sat_name(sim.srv[i]))
        if L is None:
            for k in keys[1:]:
                rows[k].append("—")
            continue
        s1 = sim.geo_state() if geo else sim.sat_state(sim.srv[i], sim.t + 1)
        rate = m.link(sim.ue_state(u, sim.t + 1), s1, sim.fc)["fd"] - L["fd"]
        orb = "GEO" if geo else "LEO-600"
        lb = n3.link_budget(orb, "S", "DL", max(L["el"], 1.0), h_km=None if geo else sim.h_leo)
        rows["α"].append(f"{L['el']:.1f}°"); rows["d"].append(f"{L['d']:.0f} km"); rows["f_d"].append(fmt_hz(L["fd"]))
        rows["df_d/dt"].append(f"{rate:+.0f} Hz/s".replace("-", "−")); rows["RTT"].append(f"{L['rtt']:.1f} ms")
        rows["PL"].append(f"{L['pl']:.1f} dB"); rows["CNR DL"].append(f"{lb['cnr']:.1f} dB")
    ref = sim.ground_state(0.0)
    cons = []
    if not geo:
        for k in sorted([k for k in range(sim.n_sat) if abs(sim.sat_theta(k, sim.t)) < m.VW * 1.6], key=lambda k: -sim.sat_theta(k, sim.t)):
            el = m.link(ref, sim.sat_state(k, sim.t), sim.fc)["el"]
            st = "serving" if k in sim.srv else ("rising" if sim.sat_theta(k, sim.t) < 0 else "setting")
            if el < 0:
                st = "below horizon"
            cons.append([m.sat_name(k), round(el, 1), st])
    cons.append(["GEO", round(m.link(ref, sim.geo_state(), sim.fc)["el"], 1), "serving" if geo else "standby"])
    ho = [] if geo else [sim.predict_ho(i) for i in range(len(m.UES))]
    rtt = float(np.mean([c["geo"]["rtt"] for c in cur])) if geo else float(np.mean([c["leo"]["rtt"] for c in cur if c["leo"]]))
    return dict(rows=rows, cons=cons, ho=ho, rtt=round(rtt, 1),
                serving=sorted({m.sat_name(k) for k in sim.srv if k >= 0}) if not geo else ["GEO"])


data = dict(ue=[dict(id=u["id"], name=u["name"], v=u["v"], color=c[1:]) for u, c in zip(m.UES, UE_COL)])

# ---------------------------------------------------------------- LEO kareleri (9 kare, 60 s)
frames, times = [], list(range(0, 481, 60))
sim = m.make_sim(layer="LEO", fc=2.0, h_leo=600, n_sat=12, el_min=10, geo_lon=35)
prev = None
for j, t in enumerate(times):
    sim.advance(t - sim.t)
    img = f"leo_{j+1:02d}.png"
    cur = render(sim, os.path.join(OUT, img))
    v = values(sim, cur)
    new = [e for e in sim.events if prev is not None and prev < e[0] <= t]
    hos = [s for s in v["ho"] if s is not None]
    if new:
        kind = "executed"; status = "HANDOVER → " + ", ".join(sorted({m.sat_name(e[3]) for e in new}))
    elif hos and min(hos) <= 60:
        kind = "pending"; status = f"HANDOVER IN {min(hos)} s"
    else:
        kind = "idle"; status = "NO HANDOVER PENDING"
    frames.append(dict(layer="LEO", t=t, idx=j + 1, n=len(times), image=img, kind=kind, status=status,
                       events=[[round(e[0]), e[1], m.sat_name(e[2]), m.sat_name(e[3])] for e in sorted(new)], **v))
    prev = t
data["events"] = [[round(e[0]), e[1], m.sat_name(e[2]), m.sat_name(e[3])] for e in sorted(sim.events) if 0 < e[0] <= 480]
leo_sim = sim

# ---------------------------------------------------------------- GEO karesi
g = m.make_sim(layer="GEO", fc=2.0, h_leo=600, n_sat=12, el_min=10, geo_lon=35)
g.advance(120)
cur = render(g, os.path.join(OUT, "geo_01.png"))
frames.append(dict(layer="GEO", t=120, idx=1, n=1, image="geo_01.png", kind="none", status="NO HANDOVER (GEO)", events=[], **values(g, cur)))
data["frames"] = frames

# ---------------------------------------------------------------- Doppler zaman grafiği
def series(s):
    tt = np.array([h[0] for h in s.hist]) - s.t
    return (tt / 60, np.array([[r[0] for r in h[1]] for h in s.hist]) / 1e3,
            np.array([[r[1] for r in h[1]] for h in s.hist]), np.array([[r[2] for r in h[1]] for h in s.hist]) / 1e3)

fig, (a, b) = plt.subplots(2, 1, figsize=(W, H), sharex=True, gridspec_kw=dict(height_ratios=[2.3, 1], hspace=0.28))
tm, fdL, srv, _ = series(leo_sim)
for i, u in enumerate(m.UES):
    y = fdL[:, i].copy(); y[1:][np.diff(srv[:, i]) != 0] = np.nan
    a.plot(tm, y, color=u["color"], lw=2.2, label=u["name"])
i = 0
br = np.where(np.diff(srv[:, i]) != 0)[0] + 1
segs = [(lo, hi) for lo, hi in zip(br[:-1], br[1:]) if tm[lo] > -27 and tm[hi - 1] < -3]
lo, hi = segs[len(segs) // 2]
seg = fdL[lo:hi, i]
k0, k1, kz = lo + int(np.argmax(seg)), lo + int(np.argmin(seg)), lo + int(np.argmin(np.abs(seg)))
akw = dict(fontsize=12, color="#0B1D33", arrowprops=dict(arrowstyle="->", color="#0B1D33", lw=1.2),
           bbox=dict(fc="white", ec="#9AA5B1", pad=3))
a.annotate("satellite rising (approaching)\nf_d ≈ +46 kHz", (tm[k0], fdL[k0, i]), (tm[k0] - 7.5, 33), **akw)
a.annotate("satellite overhead: f_d = 0\nchanges fastest (≈ −580 Hz/s)", (tm[kz], 0), (tm[kz] + 1.0, 22), **akw)
a.annotate("satellite setting (receding)\nf_d ≈ −46 kHz", (tm[k1], fdL[k1, i]), (tm[k1] - 9.5, -36), **akw)
a.plot([tm[hi - 1], tm[hi]], [fdL[hi - 1, i], fdL[hi, i]], ":", color=m.UES[i]["color"], lw=2.4)
a.annotate("handover: UAV jumps from the setting\nto the next (rising) satellite",
           (0.5 * (tm[hi - 1] + tm[hi]), 0.5 * (fdL[hi - 1, i] + fdL[hi, i])), (tm[hi] + 1.2, -24), **akw)
for ax in (a, b):
    ax.axhline(0, color="#5B6B7F", lw=0.8); ax.set_ylim(-55, 55); ax.set_ylabel("f_d [kHz]", fontsize=12)
    ax.grid(alpha=0.3); ax.tick_params(labelsize=11)
a.set_title("LEO-600 · 2 GHz · one S-curve per satellite pass (last 30 min)", loc="left", fontsize=13)
a.legend(fontsize=11, ncol=4, loc="upper right")
tg, _, _, fdG = series(g)
for i, u in enumerate(m.UES):
    b.plot(tg, fdG[:, i], color=u["color"], lw=2.2)
b.set_title("GEO · 2 GHz · same scale — Doppler only from UE motion, no handover", loc="left", fontsize=13)
b.set_xlabel("time relative to now [min]", fontsize=12); b.set_xlim(-30, 0)
fig.subplots_adjust(left=0.07, right=0.985, top=0.95, bottom=0.08)
fig.savefig(os.path.join(OUT, "doppler.png"), dpi=DPI, facecolor="white"); plt.close(fig)

# ---------------------------------------------------------------- kapsama geometrisi (coverage_figure'ın alt yarısı)
fig = m.coverage_figure(h_leo=600, el_min=10, n_sat=12, dpi=150)
fig.savefig(os.path.join(OUT, "_cov_full.png"), dpi=150, facecolor="white"); plt.close(fig)
im = Image.open(os.path.join(OUT, "_cov_full.png")); w, h = im.size
im.crop((0, int(h * 0.50), w, h)).save(os.path.join(OUT, "coverage_geometry.png"))
os.remove(os.path.join(OUT, "_cov_full.png"))

# ---------------------------------------------------------------- kapsama boşlukları (12 / 10 / 8 uydu)
fig = m.coverage_gap_figure(n_list=(12, 10, 8), h_leo=600, el_min=10, hours=2.0, dpi=150)
fig.savefig(os.path.join(OUT, "coverage_gaps.png"), dpi=150, facecolor="white"); plt.close(fig)
gaps = {}
for nsat in (12, 10, 8):
    t, el, cov, gp = m.coverage_timeline(nsat, 600, 10, 2.0)
    gaps[nsat] = dict(avail=round(100 * cov.mean(), 1), gap_s=round(float(np.mean([b - a for a, b in gp])) if gp else 0),
                      n_gaps=len(gp))
data["gaps"] = gaps

# ---------------------------------------------------------------- kapsama: yarıçap ve N_min – irtifa
hs = list(range(300, 2001, 100))
data["altitude"] = dict(h=hs, radius={e: [round(float(n3.footprint_rad(h, e) * n3.RE)) for h in hs] for e in (0, 10, 30)},
                        nmin={e: [int(np.floor(np.pi / n3.footprint_rad(h, e))) + 1 for h in hs] for e in (10, 30)},
                        geo_radius={e: round(float(n3.footprint_rad(35786, e) * n3.RE)) for e in (0, 10, 30)})

# ---------------------------------------------------------------- radyo kapsaması (TR 38.811 Monte Carlo)
rc = {}
for orb in ("LEO-600", "GEO"):
    el = n3.TARGET_EL[(n3.orbit_type(orb), "Set-1")]
    rc[orb] = dict(el=el, cov={s: round(100 * n3.coverage_mc(orb, "S", s, el_grid=[el], n=40000)["p_cnr"][0]) for s in n3.LOS_PROB},
                   los={s: round(100 * n3.los_probability(s, el)) for s in n3.LOS_PROB})
data["radio"] = rc

# ---------------------------------------------------------------- antenler ve beam'ler
RE = 6371.0
ant = []
for name, orb, band, D, gdoc, thdoc in [("LEO-600 S Set-2", "LEO-600", "S", 1, 24, 8.832), ("LEO-600 S Set-1", "LEO-600", "S", 2, 30, 4.4127),
                                        ("LEO-600 Ka Set-1", "LEO-600", "Ka", 0.5, 38.5, 1.7647), ("GEO S Set-2", "GEO", "S", 12, 45.5, 0.7353),
                                        ("GEO S Set-1", "GEO", "S", 22, 51, 0.4011), ("GEO Ka Set-1", "GEO", "Ka", 5, 58.5, 0.1765)]:
    lam = 3e8 / (2e9 if band == "S" else 20e9)
    th = 1.029 * lam / D
    ant.append(dict(name=name, D=D, th=round(np.degrees(th), 2), th_doc=thdoc, G=round(10 * np.log10(0.6 * (np.pi * D / lam) ** 2), 1),
                    G_doc=gdoc, N=int(round(np.pi / 4 * (2 * D / lam) ** 2)), beam_km=n3.SAT_PARAMS["Set-1" if "Set-1" in name else "Set-2"][orb][band]["beam_km"]))
data["antennas"] = ant
beams = []
for name, orb, band, d in [("LEO-600 · S-band · 50 km", "LEO-600", "S", 50), ("LEO-600 · Ka-band · 20 km", "LEO-600", "Ka", 20),
                           ("GEO · S-band · 250 km", "GEO", "S", 250), ("GEO · Ka-band · 110 km", "GEO", "Ka", 110)]:
    lam = n3.footprint_rad(n3.ORBITS[orb], 10); cap = 2 * np.pi * RE ** 2 * (1 - np.cos(lam)); ab = np.pi * (d / 2) ** 2
    beams.append(dict(name=name, istanbul=int(np.ceil(1.21 * 5461 / ab)), turkey=int(np.ceil(1.21 * 783562 / ab)),
                      visible=int(round(1.21 * cap / ab, -2)), visible_plain=int(round(cap / ab, -1))))
data["beams"] = beams
Db = 2 * np.sqrt(5461 / np.pi)
one = []
for orb, h in (("LEO-600", 600), ("GEO", 35786)):
    th = 2 * np.arctan(Db / 2 / h)
    one.append(dict(orbit=orb, th=round(np.degrees(th), 3), D_S=round(1.029 * 0.15 / th, 2), D_Ka=round(1.029 * 0.015 / th, 2),
                    N=int(round(np.pi / 4 * (2 * 1.029 / th) ** 2, -1))))
data["one_beam"] = dict(D_beam=round(Db), rows=one)

json.dump(data, open(os.path.join(OUT, "data.json"), "w"), ensure_ascii=False, indent=1)
for f in frames:
    print(f["layer"], f["t"], f["kind"], f["status"], f["events"])
print("events", data["events"]); print("gaps", gaps); print("beams", beams); print("one", data["one_beam"]); print("radio", rc)
