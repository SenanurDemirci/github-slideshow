"""Kareleri (PNG) ve her karenin değerlerini (JSON) üretir. Kod: kullanıcının notebook'undaki leo_geo_doppler.py / ntn_3gpp.py"""
import sys, json, os
CODE, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, CODE)
import matplotlib; matplotlib.use("Agg")
import numpy as np
import leo_geo_doppler as m
import ntn_3gpp as n3

W, H, DPI = 12.3, 8.45, 150

def render(sim, path):
    app = m.App(sim, interactive=False)
    fig = app.fig
    fig.set_size_inches(W, H)
    app.ax_info.remove()
    cur = sim.current()
    app.draw_local(cur); app.draw_orbit(cur); app.draw_doppler()
    app.ax_local.set_position([0.065, 0.475, 0.925, 0.475])
    app.ax_orbit.set_position([0.02, 0.05, 0.37, 0.33])
    app.ax_dop.set_position([0.465, 0.075, 0.525, 0.30])
    fig.savefig(path, dpi=DPI, facecolor="white")
    matplotlib.pyplot.close(fig)
    return cur

def fmt_hz(f):
    s = "−" if f < 0 else "+"; a = abs(f)
    return f"{s}{a/1000:.1f} kHz" if a >= 1000 else f"{s}{a:.0f} Hz"

def values(sim, cur):
    geo = sim.layer == "GEO"
    band = "S" if abs(sim.fc - 2.0) < 1e-9 else None
    rows = {k: [] for k in ["v", "h", "sat", "α", "d", "f_d", "df_d/dt", "PL", "RTT", "CNR DL", "SE DL", "link"]}
    for i, u in enumerate(m.UES):
        L = (cur[i]["geo"] if cur[i]["geo"]["el"] >= sim.el_min else None) if geo else cur[i]["leo"]
        rows["v"].append(("← " if u["v"] < 0 else "") + f"{abs(u['v'])} km/h" + (" →" if u["v"] >= 0 else ""))
        rows["h"].append(f"{u['h']:g} km" if u["h"] >= 1 else (f"{u['h']*1000:.0f} m" if u["h"] > 0 else "ground"))
        rows["sat"].append(("GEO" if L else "—") if geo else m.sat_name(sim.srv[i]))
        if L is None:
            for k in ["α", "d", "f_d", "df_d/dt", "PL", "RTT", "CNR DL", "SE DL"]: rows[k].append("—")
            rows["link"].append("no cov."); continue
        s1 = sim.geo_state() if geo else sim.sat_state(sim.srv[i], sim.t + 1)
        rate = m.link(sim.ue_state(u, sim.t + 1), s1, sim.fc)["fd"] - L["fd"]
        rows["α"].append(f"{L['el']:.1f}°"); rows["d"].append(f"{L['d']:.0f} km"); rows["f_d"].append(fmt_hz(L["fd"]))
        rows["df_d/dt"].append(f"{rate:+.1f} Hz/s".replace("-", "−")); rows["PL"].append(f"{L['pl']:.1f} dB")
        rows["RTT"].append(f"{L['rtt']:.1f} ms")
        if band:
            orb = "GEO" if geo else ("LEO-600" if sim.h_leo < 900 else "LEO-1200")
            lb = n3.link_budget(orb, band, "DL", max(L["el"], 1.0), h_km=None if geo else sim.h_leo)
            rows["CNR DL"].append(f"{lb['cnr']:.1f} dB"); rows["SE DL"].append(f"{lb['se']:.2f} b/s/Hz")
        else:
            rows["CNR DL"].append("n/a"); rows["SE DL"].append("n/a")
        rows["link"].append("LOS")
    # takımyıldız
    ref = sim.ground_state(0.0)
    cons = []
    if not geo:
        ks = sorted([k for k in range(sim.n_sat) if abs(sim.sat_theta(k, sim.t)) < m.VW * 1.6], key=lambda k: -sim.sat_theta(k, sim.t))
        for k in ks:
            el = m.link(ref, sim.sat_state(k, sim.t), sim.fc)["el"]
            st = "serving" if k in sim.srv else ("rising" if sim.sat_theta(k, sim.t) < 0 else "setting")
            if el < 0: st = "below horizon"
            cons.append((m.sat_name(k), round(el, 1), st))
    gel = m.link(ref, sim.geo_state(), sim.fc)["el"]
    cons.append(("GEO", round(gel, 1), "serving" if geo else "standby"))
    # bağlantı durumu
    state, ho = [], []
    if geo:
        mx = max(abs(c["geo"]["fd"]) for c in cur)
        state = ["GEO serving all 4 UEs · no handovers", f"Doppler only from UE motion (max {fmt_hz(mx)})",
                 f"Mean access RTT {np.mean([c['geo']['rtt'] for c in cur]):.1f} ms"]
    else:
        for i, u in enumerate(m.UES):
            s = sim.predict_ho(i); ho.append(s)
            state.append(f"{u['id']}: {m.sat_name(sim.srv[i])} → HO in {m.fmt_t(s) if s else '>30:00'}"
                         if sim.srv[i] >= 0 else f"{u['id']}: no LEO coverage")
        rl = [c["leo"]["rtt"] for c in cur if c["leo"]]
        state.append(f"Mean access RTT {np.mean(rl):.1f} ms (LEO) · {np.mean([c['geo']['rtt'] for c in cur]):.1f} ms (GEO)")
    return dict(rows=rows, cons=cons, state=state, ho=[x if x is not None else None for x in ho],
                serving=sorted({m.sat_name(k) for k in sim.srv if k >= 0}))

frames = []
sim = m.make_sim(layer="LEO", fc=2.0, h_leo=600, n_sat=12, el_min=10, geo_lon=35)
prev_t, times = None, list(range(0, 481, 30))
for j, t in enumerate(times):
    sim.advance(t - sim.t)
    path = os.path.join(OUT, f"leo_{j+1:02d}.png")
    cur = render(sim, path)
    v = values(sim, cur)
    new_ev = [e for e in sim.events if prev_t is not None and prev_t < e[0] <= t]
    hos = [s for s in v["ho"] if s is not None]
    if new_ev:
        to = sorted({m.sat_name(e[3]) for e in new_ev})
        status, kind = "HANDOVER EXECUTED → " + ", ".join(to), "executed"
        detail = "; ".join(f"{e[1]} {m.sat_name(e[2])}→{m.sat_name(e[3])} at {m.fmt_t(e[0])}" for e in sorted(new_ev))
    elif hos and min(hos) <= 10:
        status, kind, detail = "HO EXECUTION IMMINENT", "imminent", ""
    elif hos and min(hos) <= 60:
        status, kind, detail = "HO PREP ACTIVE", "active", ""
    else:
        status, kind, detail = "HO PREP NOT STARTED", "idle", ""
    frames.append(dict(layer="LEO", t=t, idx=j + 1, n=len(times), image=os.path.basename(path), status=status,
                       kind=kind, ho_detail=detail, **v))
    prev_t = t
# GEO karesi
g = m.make_sim(layer="GEO", fc=2.0, h_leo=600, n_sat=12, el_min=10, geo_lon=35)
g.advance(120)
cur = render(g, os.path.join(OUT, "geo_01.png"))
frames.append(dict(layer="GEO", t=120, idx=1, n=1, image="geo_01.png", status="NO HANDOVER (GEO)", kind="idle",
                   ho_detail="", **values(g, cur)))
json.dump(frames, open(os.path.join(OUT, "frames.json"), "w"), ensure_ascii=False, indent=1)
for f in frames:
    print(f["layer"], f["t"], f["status"], f["ho_detail"], "| serving", f["serving"], "| ho", f["ho"])
