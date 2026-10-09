"""
LEO / GEO NTN bağlantı simülatörü — yörüngeler, Doppler ve kapsama
=================================================================

Hareketli kullanıcılar (UE: İHA, uçak, hızlı tren, gemi) bir LEO uydu
düzlemi veya bir GEO uydusu tarafından servis edilir. Her UE için anlık
elevasyon açısı (α), eğik mesafe (d), Doppler kayması (f_d), Doppler
değişim hızı (df_d/dt), serbest uzay yol kaybı (PL), gecikme / RTT ve
LEO handover'ları hesaplanır.

Ekran düzeni
  - Sol üst : yerel bağlantı görünümü (yandan; irtifa ekseni logaritmik)
              zemindeki renkli şerit = yerde sabit bir terminalin gördüğü
              Doppler (mavi negatif, kırmızı pozitif, gri kapsama yok)
  - Sol alt : yörünge görünümü (gerçek ölçek, Dünya'ya sabit çerçeve)
  - Orta alt: son 30 dk Doppler f_d(t) + hangi uydunun servis ettiği
  - Sağ     : UE başına bağlantı değerleri, takımyıldız, handover kaydı
  - En alt  : kaydırıcılar ve butonlar

Model / sadeleştirmeler
  - Her şey tek bir yörünge düzleminde, 2B ve Dünya'ya sabit çerçevede.
    Dünya dönüşünün LEO Doppler'ine katkısı ihmal edilir.
  - GEO, Dünya'ya göre sabit → GEO Doppler'i sadece UE hareketinden gelir.
  - f_d = -f_c * (dr/dt) / c ,  PL = FSPL = 20log10(d_km) + 20log10(f_GHz) + 92.45

Kullanım
  python leo_geo_doppler.py                    # etkileşimli pencere
  python leo_geo_doppler.py --save sim.gif     # animasyonu dosyaya kaydet
  python leo_geo_doppler.py --png ekran.png --t 600   # tek kare (t = 600 s)

Gerekenler: pip install numpy matplotlib pillow
"""
import argparse
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb
from matplotlib.widgets import Button, RadioButtons, Slider

# ----------------------------------------------------------------- sabitler
C = 299792.458        # ışık hızı [km/s]
MU = 398600.4418      # Dünya kütleçekim parametresi [km^3/s^2]
RE = 6371.0           # Dünya yarıçapı [km]
RGEO = 42164.17       # GEO yörünge yarıçapı [km]
D = np.pi / 180       # derece → radyan

VW = 20 * D           # yerel görünümün yarı genişliği (merkez açı) ≈ ±2220 km
HYST = 8.0            # handover histerezisi [derece]
SAMPLE = 2.0          # geçmiş kayıt adımı [s]
WINDOW = 1800.0       # grafik penceresi [s] (30 dk)
TH0 = -6 * D          # SAT-1'in başlangıç fazı

# Kullanıcılar: h [km], v [km/h] (+ sağa, - sola), phi0 = başlangıç konumu
UES = [
    dict(id="UAV",  name="UAV",       h=0.3, v=-200, phi0=4.5 * D,  color="#1f8a68"),
    dict(id="A/C",  name="Aircraft",  h=11,  v=900,  phi0=-2.0 * D, color="#2f6fb5"),
    dict(id="HST",  name="HST train", h=0,   v=400,  phi0=-9.0 * D, color="#d0712b"),
    dict(id="SHIP", name="Ship",      h=0,   v=40,   phi0=12.0 * D, color="#7b55b0"),
]
SAT_PAL = ["#c9952c", "#4f9a5a", "#c0504d", "#2f6fb5", "#7b55b0", "#1f8a8a"]
COL_SERVE, COL_RISE, COL_SET, COL_IDLE = "#a8761d", "#4f9a5a", "#c0504d", "#8e8a82"
COL_NOCOV, COL_EARTH = "#d3cec4", "#efe9dc"
CARRIERS = {"L 1.6 GHz": 1.6, "S 2 GHz": 2.0, "Ku 12 GHz": 12.0, "Ka 20 GHz": 20.0, "Ka 30 GHz": 30.0}


# ----------------------------------------------------------------- fizik
def wrap_view(a):
    """UE yerel görünümün dışına çıkınca diğer kenardan geri girsin."""
    w = 2 * VW
    return (a + VW) % w - VW


def link(ue, sat, fc):
    """UE ile uydu arasındaki bağlantı. ue/sat: dict(p=[x,y], v=[vx,vy]) km, km/s."""
    dp = sat["p"] - ue["p"]
    d = np.hypot(*dp)
    up = ue["p"] / np.hypot(*ue["p"])                  # yerel zenit yönü
    el = np.degrees(np.arcsin(np.clip(dp @ up / d, -1, 1)))
    rr = dp @ (sat["v"] - ue["v"]) / d                 # mesafe değişim hızı [km/s]
    fd = -fc * 1e9 * rr / C                            # Doppler [Hz]
    pl = 20 * np.log10(d) + 20 * np.log10(fc) + 92.45  # FSPL [dB]
    ow = d / C * 1000                                  # tek yön gecikme [ms]
    return dict(d=d, el=el, rr=rr, fd=fd, pl=pl, ow=ow, rtt=2 * ow)


def footprint(r, el_deg):
    """Minimum elevasyonda kapsama kenarının Dünya merkez açısı [rad]."""
    el = el_deg * D
    return np.arccos(RE * np.cos(el) / r) - el


def fmt_hz(f):
    s = "-" if f < 0 else "+"
    a = abs(f)
    return f"{s}{a / 1000:.1f} kHz" if a >= 1000 else f"{s}{a:.0f} Hz"


def fmt_t(s):
    neg, s = s < 0, int(round(abs(s)))
    return ("-" if neg else "") + f"{s // 60:02d}:{s % 60:02d}"


def sat_name(k):
    return "—" if k < 0 else f"SAT-{k + 1}"


# ----------------------------------------------------------------- simülasyon
class Sim:
    def __init__(self):
        self.fc = 2.0          # taşıyıcı frekans [GHz]
        self.h_leo = 600.0     # LEO irtifası [km]
        self.n_sat = 12        # düzlemdeki uydu sayısı
        self.el_min = 10.0     # minimum elevasyon [derece]
        self.geo_lon = 35.0    # GEO'nun merkeze göre açısı [derece]
        self.layer = "LEO"     # servis katmanı: "LEO" veya "GEO"
        self.speed = 30.0      # simülasyon saniyesi / gerçek saniye
        self.playing = True
        self.rebuild(keep_t=False)

    # --- geometri
    @property
    def r_leo(self):
        return RE + self.h_leo

    @property
    def omega(self):
        return np.sqrt(MU / self.r_leo ** 3)

    def ue_state(self, u, t):
        phi = wrap_view(u["phi0"] + (u["v"] / 3600) / (RE + u["h"]) * t)
        r, vs = RE + u["h"], u["v"] / 3600
        return dict(phi=phi, p=np.array([r * np.sin(phi), r * np.cos(phi)]),
                    v=np.array([vs * np.cos(phi), -vs * np.sin(phi)]))

    def sat_theta(self, k, t):
        a = TH0 + 2 * np.pi * k / self.n_sat + self.omega * t
        return np.arctan2(np.sin(a), np.cos(a))

    def sat_state(self, k, t):
        th, r, w = self.sat_theta(k, t), self.r_leo, self.omega
        return dict(th=th, p=np.array([r * np.sin(th), r * np.cos(th)]),
                    v=np.array([r * w * np.cos(th), -r * w * np.sin(th)]))

    def geo_state(self):
        th = self.geo_lon * D
        return dict(th=th, p=np.array([RGEO * np.sin(th), RGEO * np.cos(th)]), v=np.zeros(2))

    @staticmethod
    def ground_state(phi):
        return dict(phi=phi, p=np.array([RE * np.sin(phi), RE * np.cos(phi)]), v=np.zeros(2))

    # --- servis eden uydu seçimi (en yüksek elevasyon + histerezis)
    def eval_serving(self, i, t, log):
        u, us = UES[i], self.ue_state(UES[i], t)
        links = [link(us, self.sat_state(k, t), self.fc) for k in range(self.n_sat)]
        vis = [k for k in range(self.n_sat) if links[k]["el"] >= self.el_min]
        best = max(vis, key=lambda k: links[k]["el"]) if vis else -1
        cur = self.srv[i]
        if 0 <= cur < self.n_sat and links[cur]["el"] >= self.el_min:
            # mevcut uydu batıyorsa ve yeni uydu belirgin şekilde daha yüksekse geç
            if best != cur and links[best]["el"] - links[cur]["el"] > HYST and links[cur]["rr"] > 0:
                cur = best
        else:
            cur = best
        if cur != self.srv[i]:
            if log and self.srv_init[i]:
                self.events.insert(0, (t, u["id"], self.srv[i], cur))
                del self.events[40:]
            self.srv[i] = cur
        self.srv_init[i] = True
        return us, links

    def sample(self, t, log):
        g = self.geo_state()
        row = []
        for i in range(len(UES)):
            us, links = self.eval_serving(i, t, log)
            leo = links[self.srv[i]] if self.srv[i] >= 0 else None
            geo = link(us, g, self.fc)
            row.append((leo["fd"] if leo else np.nan, self.srv[i],
                        geo["fd"] if geo["el"] >= self.el_min else np.nan))
        self.hist.append((t, row))

    def advance(self, dt):
        target = self.t + dt
        while self.next_sample <= target:
            self.sample(self.next_sample, log=True)
            self.next_sample += SAMPLE
        self.t = target
        while self.hist and self.hist[0][0] < self.t - WINDOW:
            self.hist.pop(0)

    def rebuild(self, keep_t=True):
        """Parametre değişince geçmişi yeniden hesapla (son 30 dk önceden doldurulur)."""
        t0 = self.t if keep_t else 0.0
        self.hist, self.events = [], []
        self.srv = [-1] * len(UES)
        self.srv_init = [False] * len(UES)
        self.t = t0 - WINDOW
        self.next_sample = self.t
        self.advance(WINDOW)

    def current(self):
        """Şu anki her UE için LEO ve GEO bağlantıları."""
        g = self.geo_state()
        out = []
        for i, u in enumerate(UES):
            us = self.ue_state(u, self.t)
            leo = link(us, self.sat_state(self.srv[i], self.t), self.fc) if self.srv[i] >= 0 else None
            out.append(dict(us=us, leo=leo, geo=link(us, g, self.fc)))
        return out

    def coverage(self):
        """Kapsama analizi: λ = arccos(R_E·cos ε / r) − ε  (ε = minimum elevasyon)."""
        lam_leo = footprint(self.r_leo, self.el_min)
        lam_geo = footprint(RGEO, self.el_min)
        ratio = np.pi / lam_leo                       # kesintisiz kapsama: 2π/N < 2λ  →  N > π/λ
        n_min = int(np.floor(ratio)) + 1
        return dict(
            lam_leo=lam_leo, r_leo_km=lam_leo * RE, lam_geo=lam_geo, r_geo_km=lam_geo * RE,
            cap_leo=(1 - np.cos(lam_leo)) / 2,          # Dünya yüzeyinin kapsanan oranı (küresel başlık)
            cap_geo=(1 - np.cos(lam_geo)) / 2,
            pass_min=2 * lam_leo / self.omega / 60,     # bir uydunun görünme süresi [dk]
            ho_min=2 * np.pi / self.omega / 60 / self.n_sat,   # handover aralığı T/N [dk]
            n_ratio=ratio, n_min=n_min, continuous=self.n_sat >= n_min,
        )

    def predict_ho(self, i):
        """Servis eden uydu el_min'in altına inene kadar kalan süre [s]."""
        k = self.srv[i]
        if k < 0:
            return None
        for s in range(5, 1801, 5):
            if link(self.ue_state(UES[i], self.t + s), self.sat_state(k, self.t + s), self.fc)["el"] < self.el_min:
                return s
        return None


# ----------------------------------------------------------------- çizim
class App:
    def __init__(self, sim, interactive=True):
        self.sim = sim
        self.fig = plt.figure(figsize=(17, 10.5) if interactive else (17, 9.2))
        if interactive:
            self.fig.canvas.manager.set_window_title("LEO / GEO NTN Doppler Simulator")
        gs = self.fig.add_gridspec(3, 3, left=0.04, right=0.99, top=0.95, bottom=0.17 if interactive else 0.06,
                                   width_ratios=[1, 1.25, 1.05], height_ratios=[1.35, 0.85, 0.25],
                                   hspace=0.28, wspace=0.18)
        self.ax_local = self.fig.add_subplot(gs[0, :2])
        self.ax_orbit = self.fig.add_subplot(gs[1:, 0])
        self.ax_dop = self.fig.add_subplot(gs[1, 1])
        self.ax_cov = self.fig.add_subplot(gs[2, 1], sharex=self.ax_dop)
        self.ax_info = self.fig.add_subplot(gs[:, 2])
        self.cmap = plt.get_cmap("coolwarm")
        if interactive:
            self._widgets()

    # --- kontroller
    def _widgets(self):
        s, f = self.sim, self.fig
        def slider(rect, label, vmin, vmax, val, step, attr):
            sl = Slider(f.add_axes(rect), label, vmin, vmax, valinit=val, valstep=step)
            def on(v):
                setattr(s, attr, int(v) if attr == "n_sat" else float(v))
                s.rebuild()
            sl.on_changed(on)
            return sl
        self.sliders = [
            slider([0.07, 0.11, 0.22, 0.02], "LEO alt [km]", 400, 1500, s.h_leo, 10, "h_leo"),
            slider([0.07, 0.08, 0.22, 0.02], "Sats/plane", 6, 24, s.n_sat, 1, "n_sat"),
            slider([0.07, 0.05, 0.22, 0.02], "Min elev [°]", 0, 40, s.el_min, 1, "el_min"),
            slider([0.07, 0.02, 0.22, 0.02], "GEO offset [°]", -70, 70, s.geo_lon, 1, "geo_lon"),
            Slider(f.add_axes([0.40, 0.11, 0.18, 0.02]), "Speed [×]", 1, 120, valinit=s.speed, valstep=1),
        ]
        self.sliders[-1].on_changed(lambda v: setattr(s, "speed", float(v)))

        self.rb_layer = RadioButtons(f.add_axes([0.36, 0.01, 0.07, 0.08]), ["LEO", "GEO"])
        self.rb_layer.on_clicked(lambda l: setattr(s, "layer", l))
        self.rb_fc = RadioButtons(f.add_axes([0.45, 0.01, 0.09, 0.09]), list(CARRIERS), active=1)
        self.rb_fc.on_clicked(lambda l: (setattr(s, "fc", CARRIERS[l]), s.rebuild()))

        self.bt_play = Button(f.add_axes([0.58, 0.05, 0.06, 0.04]), "Pause")
        def toggle(_):
            s.playing = not s.playing
            self.bt_play.label.set_text("Pause" if s.playing else "Play")
        self.bt_play.on_clicked(toggle)
        self.bt_reset = Button(f.add_axes([0.65, 0.05, 0.06, 0.04]), "Reset")
        self.bt_reset.on_clicked(lambda _: s.rebuild(keep_t=False))

    def sat_status(self, k, serving):
        if k in serving:
            return "serve", COL_SERVE
        return ("rise", COL_RISE) if self.sim.sat_theta(k, self.sim.t) < 0 else ("set", COL_SET)

    # --- yerel bağlantı görünümü (yandan)
    def draw_local(self, cur):
        s, ax = self.sim, self.ax_local
        ax.clear()
        t = s.t
        X = lambda phi: phi * RE                                   # yer izi [km]
        Y = lambda phi, h: np.log10(1 + np.maximum(h, 0)) - 0.35 * (phi / VW) ** 2   # log irtifa + eğrilik
        phis = np.linspace(-VW, VW, 200)
        serving = {k for k in s.srv if k >= 0}

        # atmosfer katmanları
        for h0, h1, name in [(0, 15, "troposphere · O₂/H₂O"), (60, 1000, "ionosphere")]:
            ax.fill_between(X(phis), Y(phis, h0), Y(phis, h1), color="#7d8cb0", alpha=0.07, lw=0)
            ax.text(X(-VW) + 40, Y(-VW, (h0 + h1) / 12), name, fontsize=8, color="0.45")
        # Dünya yüzeyi
        ax.fill_between(X(phis), Y(phis, 0), -1, color=COL_EARTH, lw=0)
        ax.plot(X(phis), Y(phis, 0), color="0.25", lw=1.2)
        ax.text(X(-VW) + 40, -0.62, f"Earth surface · R_E = {RE:.0f} km", fontsize=8, color="0.45")
        geo_only = s.layer == "GEO"   # GEO seçilince LEO hiç çizilmez
        ref = s.ground_state(0.0)
        # LEO yörüngesi
        if not geo_only:
            ax.plot(X(phis), Y(phis, s.h_leo), "--", color="0.6", lw=0.9)
            ax.text(X(-VW) + 40, Y(-VW, s.h_leo) - 0.17,
                    f"LEO orbit · h = {s.h_leo:.0f} km · v = {s.r_leo * s.omega:.2f} km/s →", fontsize=8, color="0.45")

        # zemin Doppler şeridi (yerde sabit terminal, en iyi LEO uydusu)
        fref = s.fc * 1e9 * s.omega * RE / C
        seg_phi = np.linspace(-VW, VW, 161)
        segs, cols = [], []
        g = s.geo_state()
        for a, b in zip(seg_phi[:-1], seg_phi[1:]):
            gt = s.ground_state((a + b) / 2)
            col = COL_NOCOV
            if s.layer == "LEO":
                ls = [link(gt, s.sat_state(k, t), s.fc) for k in range(s.n_sat)]
                vis = [l for l in ls if l["el"] >= s.el_min]
                if vis:
                    col = self.cmap(0.5 + 0.5 * np.clip(max(vis, key=lambda l: l["el"])["fd"] / fref, -1, 1))
            elif link(gt, g, s.fc)["el"] >= s.el_min:
                col = self.cmap(0.5)
            segs.append([(X(a), Y(a, 0) - 0.09), (X(b), Y(b, 0) - 0.09)])
            cols.append(col)
        ax.add_collection(LineCollection(segs, colors=cols, linewidths=7))

        # LEO uyduları: kapsama alanı, yörünge izi, ISL, etiket
        lam = footprint(s.r_leo, s.el_min)
        vis = [] if geo_only else sorted([k for k in range(s.n_sat) if abs(s.sat_theta(k, t)) < VW * 1.1], key=lambda k: s.sat_theta(k, t))
        for a, b in zip(vis[:-1], vis[1:]):
            ta, tb = s.sat_theta(a, t), s.sat_theta(b, t)
            if tb - ta < 4 * np.pi / s.n_sat:
                ax.plot([X(ta), X(tb)], [Y(ta, s.h_leo), Y(tb, s.h_leo)], color=COL_IDLE, lw=0.8)
                ax.text((X(ta) + X(tb)) / 2, (Y(ta, s.h_leo) + Y(tb, s.h_leo)) / 2 + 0.05,
                        f"ISL {2 * s.r_leo * np.sin(np.pi / s.n_sat):.0f} km", fontsize=7, color="0.45", ha="center")
        for k in vis:
            th = s.sat_theta(k, t)
            st, col = self.sat_status(k, serving)
            # kapsama alanı (footprint) zeminde
            fp = np.linspace(max(-VW, th - lam), min(VW, th + lam), 40)
            if s.layer == "LEO" or st != "serve":
                ax.plot(X(fp), Y(fp, 0) + 0.03, color=col, lw=3 if st == "serve" else 2, alpha=0.9 if st == "serve" else 0.45)
            if st == "serve" and s.layer == "LEO":
                for e in (th - lam, th + lam):
                    ax.plot([X(th), X(e)], [Y(th, s.h_leo), Y(e, 0)], ":", color=col, lw=1)
            # geçmiş 4 dk yörünge izi
            tr = th - s.omega * np.linspace(240, 0, 25)
            ax.plot(X(tr), Y(tr, s.h_leo), color=col, lw=2, alpha=0.8)
            ax.plot(X(th), Y(th, s.h_leo), "s", ms=9 if st == "serve" else 7, color=col, mec="k", mew=0.6)
            lab = {"serve": "serving", "rise": "rising", "set": "setting"}[st]
            ax.text(X(th), Y(th, s.h_leo) + 0.12,
                    f"{sat_name(k)} · α_ref {link(ref, s.sat_state(k, t), s.fc)['el']:.1f}° · {lab}",
                    fontsize=8, color=col, ha="center", fontweight="bold" if st == "serve" else "normal")

        # GEO (ölçek dışı, üstte)
        gx = X(np.clip(g["th"], -VW * 0.9, VW * 0.9))
        gy = 3.55
        gcol = COL_SERVE if s.layer == "GEO" else COL_IDLE
        ax.plot(gx, gy, "s", ms=9, color=gcol, mec="k", mew=0.6)
        ax.text(gx + (-60 if gx > 0 else 60), gy, f"GEO · 35 786 km (off-scale) · α_ref {link(ref, g, s.fc)['el']:.1f}°",
                fontsize=8, color=gcol, ha="right" if gx > 0 else "left", va="center")

        # UE'ler: iz, yön oku, bağlantı çizgileri, etiketler
        for i, (u, cu) in enumerate(zip(UES, cur)):
            phi, c = cu["us"]["phi"], u["color"]
            ux, uy = X(phi), Y(phi, u["h"])
            # geçmiş 30 dk iz (görünümden çıkıp girince kopar)
            past = wrap_view(u["phi0"] + (u["v"] / 3600) / (RE + u["h"]) * (t - np.arange(1800, -1, -20)))
            jumps = np.where(np.abs(np.diff(past)) > VW)[0] + 1
            for seg in np.split(past, jumps):
                ax.plot(X(seg), Y(seg, u["h"]), ":", color=c, lw=1.4, alpha=0.7)
            # gelecek 10 dk yön oku
            pf = phi + (u["v"] / 3600) / (RE + u["h"]) * 600
            ax.annotate("", (X(pf), Y(pf, u["h"])), (ux, uy),
                        arrowprops=dict(arrowstyle="->", color=c, ls="--", lw=1.2))
            # bağlantılar
            if s.srv[i] >= 0 and not geo_only:
                th = s.sat_theta(s.srv[i], t)
                prim = s.layer == "LEO"
                ax.plot([ux, X(th)], [uy, Y(th, s.h_leo)], "-" if prim else "--", color=c,
                        lw=1.6 if prim else 0.8, alpha=1 if prim else 0.3)
                if prim:
                    ax.text(ux + (X(th) - ux) * 0.6, uy + (Y(th, s.h_leo) - uy) * 0.6, f" d={cu['leo']['d']:.0f} km",
                            fontsize=7, color=c)
            if cu["geo"]["el"] >= s.el_min:
                prim = s.layer == "GEO"
                ax.plot([ux, gx], [uy, gy], "-" if prim else "--", color=c, lw=1.4 if prim else 0.8, alpha=1 if prim else 0.3)
                if prim:
                    ax.text(ux + (gx - ux) * 0.35, uy + (gy - uy) * 0.35, f" d={cu['geo']['d']:.0f} km", fontsize=7, color=c)
            if u["h"] > 0.1:
                ax.plot([ux, ux], [uy, Y(phi, 0)], color=c, lw=0.8, alpha=0.4)
            ax.plot(ux, uy, marker=">" if u["v"] >= 0 else "<", ms=10, color=c, mec="k", mew=0.6)
            L = cu["leo"] if s.layer == "LEO" else (cu["geo"] if cu["geo"]["el"] >= s.el_min else None)
            txt = f"{u['name']} · {abs(u['v'])} km/h {'→' if u['v'] >= 0 else '←'}\n"
            txt += (f"α {L['el']:.1f}° · f_d {fmt_hz(L['fd'])}\nd {L['d']:.0f} km · RTT {L['rtt']:.1f} ms") if L else "no coverage"
            ax.text(ux, uy + 0.22 + 0.12 * (i % 2), txt, fontsize=7.5, color=c, ha="center", va="bottom",
                    family="monospace", bbox=dict(fc="white", ec="none", alpha=0.7, pad=1))

        ax.set_xlim(X(-VW), X(VW))
        ax.set_ylim(-0.75, 3.75)
        ax.set_yticks([np.log10(1 + h) for h in (0, 1, 10, 100, 1000)])
        ax.set_yticklabels(["0", "1 km", "10 km", "100 km", "1000 km"], fontsize=8)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_xlabel("ground track [km]  (altitude axis is logarithmic; angles, ranges & Doppler are true geometry)", fontsize=8)
        srvs = ", ".join(sat_name(k) for k in sorted(serving)) or "none"
        ax.set_title(f"LOCAL LINK VIEW  ·  t = {fmt_t(t)}  ·  {s.speed:.0f}×  ·  layer {s.layer}  ·  "
                     f"{'serving: ' + srvs if s.layer == 'LEO' else 'GEO @ %+.0f°' % s.geo_lon}  ·  "
                     f"f_c {s.fc:g} GHz" + ("" if geo_only else f"  ·  HO events: {len(s.events)}"),
                     fontsize=10, loc="left")

    # --- yörünge görünümü (gerçek ölçek)
    def draw_orbit(self, cur):
        s, ax = self.sim, self.ax_orbit
        ax.clear()
        t = s.t
        pol = lambda th, r: (r * np.sin(th), r * np.cos(th))
        arc = lambda a, b, r, n=60: pol(np.linspace(a, b, n), r)
        serving = {k for k in s.srv if k >= 0}
        full = np.linspace(0, 2 * np.pi, 361)
        ax.fill(*pol(full, RE), color=COL_EARTH, ec="0.25", lw=1)
        ax.plot(*arc(-VW, VW, RE), color="k", lw=4)                 # yerel görünüm penceresi
        geo_only = s.layer == "GEO"
        if not geo_only:
            ax.plot(*pol(full, s.r_leo), "--", color="0.6", lw=0.8)
        ax.plot(*pol(full, RGEO), "--", color="0.6", lw=0.8)
        # GEO kapsama konisi
        g = s.geo_state()
        lg = footprint(RGEO, s.el_min)
        gcol = COL_SERVE if s.layer == "GEO" else COL_IDLE
        ex, ey = arc(g["th"] - lg, g["th"] + lg, RE)
        ax.fill(np.r_[g["p"][0], ex], np.r_[g["p"][1], ey], color=gcol, alpha=0.08, lw=0)
        ax.plot(*arc(g["th"] - lg, g["th"] + lg, RE * 1.01), color=gcol, lw=3)
        ax.plot(*g["p"], "s", color=gcol, mec="k", ms=8)
        ax.text(*pol(g["th"], RGEO * 1.07), "GEO", color=gcol, fontsize=8, ha="center", clip_on=True)
        # LEO uyduları
        lam = footprint(s.r_leo, s.el_min)
        for k in ([] if geo_only else range(s.n_sat)):
            th = s.sat_theta(k, t)
            st, _ = self.sat_status(k, serving)
            c = COL_SERVE if st == "serve" else SAT_PAL[k % len(SAT_PAL)]
            ax.plot(*arc(th - s.omega * 480, th, s.r_leo, 30), color=c, lw=2, alpha=0.7)
            if st == "serve" and s.layer == "LEO":
                ex, ey = arc(th - lam, th + lam, RE)
                ax.fill(np.r_[pol(th, s.r_leo)[0], ex], np.r_[pol(th, s.r_leo)[1], ey], color=c, alpha=0.15, lw=0)
                ax.plot(*arc(th - lam, th + lam, RE * 1.005), color=c, lw=3)
            ax.plot(*pol(th, s.r_leo), "o", color=c, ms=6 if st == "serve" else 4)
            ax.text(*pol(th, s.r_leo * 1.06), sat_name(k), fontsize=6.5, color=c, ha="center", va="center", clip_on=True)
        # UE'ler ve bağlantılar
        for i, (u, cu) in enumerate(zip(UES, cur)):
            p = cu["us"]["p"]
            if s.layer == "LEO" and s.srv[i] >= 0:
                q = pol(s.sat_theta(s.srv[i], t), s.r_leo)
                ax.plot([p[0], q[0]], [p[1], q[1]], color=u["color"], lw=0.8)
            if s.layer == "GEO" and cu["geo"]["el"] >= s.el_min:
                ax.plot([p[0], g["p"][0]], [p[1], g["p"][1]], color=u["color"], lw=0.6, alpha=0.6)
            ax.plot(*p, "o", color=u["color"], ms=3)
        if geo_only:
            R = RGEO * 1.12
            ax.set_xlim(-R, R)
            ax.set_ylim(-R * 0.75, R * 1.08)
            title = (f"ORBIT VIEW · to scale (GEO)\nGEO h = 35 786 km · footprint @ {s.el_min:.0f}°: "
                     f"±{lg / D:.1f}° ({lg * RE:.0f} km)")
        else:
            R = s.r_leo * 1.25
            ax.set_xlim(-R, R)
            ax.set_ylim(-R * 0.55, R * 1.05)
            title = (f"ORBIT VIEW · to scale (LEO zoom)\nfootprint @ {s.el_min:.0f}°: LEO ±{lam / D:.1f}° "
                     f"({lam * RE:.0f} km) · GEO ±{lg / D:.1f}°")
        ax.set_aspect("equal")
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_title(title, fontsize=9, loc="left")

    # --- Doppler grafiği ve kapsama zaman çizelgesi
    def draw_doppler(self):
        s, ax, axc = self.sim, self.ax_dop, self.ax_cov
        ax.clear(), axc.clear()
        if not s.hist:
            return
        tt = np.array([h[0] for h in s.hist]) - s.t                 # 0 = şimdi
        fdL = np.array([[r[0] for r in h[1]] for h in s.hist])
        srv = np.array([[r[1] for r in h[1]] for h in s.hist])
        fdG = np.array([[r[2] for r in h[1]] for h in s.hist])
        for i, u in enumerate(UES):
            prim_geo = s.layer == "GEO"
            ax.plot(tt / 60, fdG[:, i] / 1e3, "-" if prim_geo else "--", color=u["color"], lw=1.6 if prim_geo else 1, alpha=1 if prim_geo else 0.35)
            if s.layer == "LEO":
                y = fdL[:, i].copy()
                y[1:][np.diff(srv[:, i]) != 0] = np.nan                # handover anında çizgiyi kopar
                ax.plot(tt / 60, y / 1e3, color=u["color"], lw=1.6, label=u["id"])
            else:
                ax.plot([], [], color=u["color"], label=u["id"])
        ax.axhline(0, color="0.5", lw=0.8)
        ax.set_xlim(-WINDOW / 60, 0)
        ax.set_ylabel("f_d [kHz]", fontsize=8)
        ax.tick_params(labelsize=8, labelbottom=False)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, ncol=4, loc="upper left", title="— GEO (UE motion only)" if s.layer == "GEO" else "— LEO serving   - - GEO", title_fontsize=7)
        ax.set_title("DOPPLER f_d(t) · last 30 min", fontsize=9, loc="left")
        # kapsama zaman çizelgesi: renk = servis eden uydu, siyah çizgi = handover
        rgb = np.zeros((len(UES), len(tt), 3))
        for i in range(len(UES)):
            for j in range(len(tt)):
                if s.layer == "LEO":
                    c = SAT_PAL[srv[j, i] % len(SAT_PAL)] if srv[j, i] >= 0 else COL_NOCOV
                else:
                    c = COL_SERVE if not np.isnan(fdG[j, i]) else COL_NOCOV
                rgb[i, j] = to_rgb(c)
        axc.imshow(rgb, aspect="auto", interpolation="nearest",
                   extent=(tt[0] / 60, (tt[-1] + SAMPLE) / 60, len(UES) - 0.5, -0.5))
        if s.layer == "LEO":
            for i in range(len(UES)):
                ho = tt[np.where(np.diff(srv[:, i]) != 0)[0] + 1] / 60
                axc.vlines(ho, i - 0.5, i + 0.5, color="k", lw=1.2)
        axc.set_yticks(range(len(UES)))
        axc.set_yticklabels([u["id"] for u in UES], fontsize=7)
        axc.tick_params(labelsize=8)
        axc.set_xlim(-WINDOW / 60, 0)
        axc.set_xlabel("time relative to now [min]   (coverage: colour = serving SAT, | = handover)", fontsize=8)

    # --- sağ panel: tablolar
    def draw_info(self, cur):
        s, ax = self.sim, self.ax_info
        ax.clear()
        ax.axis("off")
        L = [c["leo"] if s.layer == "LEO" else (c["geo"] if c["geo"]["el"] >= s.el_min else None) for c in cur]
        rate = []
        for i, u in enumerate(UES):
            if L[i] is None:
                rate.append(None)
                continue
            sat1 = s.sat_state(s.srv[i], s.t + 1) if s.layer == "LEO" else s.geo_state()
            rate.append(link(s.ue_state(u, s.t + 1), sat1, s.fc)["fd"] - L[i]["fd"])
        na = "—"
        rows = [
            ("v", [f"{u['v']:+d} km/h" for u in UES]),
            ("h", [f"{u['h']:g} km" if u["h"] >= 1 else (f"{u['h'] * 1000:.0f} m" if u["h"] > 0 else "ground") for u in UES]),
            ("sat", [(sat_name(s.srv[i]) if s.layer == "LEO" else ("GEO" if L[i] else na)) for i in range(len(UES))]),
            ("α", [f"{l['el']:.1f}°" if l else na for l in L]),
            ("d", [f"{l['d']:.0f} km" if l else na for l in L]),
            ("f_d", [fmt_hz(l["fd"]) if l else na for l in L]),
            ("df_d/dt", [f"{r:+.1f} Hz/s" if r is not None else na for r in rate]),
            ("PL", [f"{l['pl']:.1f} dB" if l else na for l in L]),
            ("delay", [f"{l['ow']:.2f} ms" if l else na for l in L]),
            ("RTT", [f"{l['rtt']:.1f} ms" if l else na for l in L]),
            ("link", ["LOS" if l else "no cov." for l in L]),
        ]
        ax.text(0, 1.0, f"PER-UE LINK VALUES  ({s.layer})", fontsize=10, fontweight="bold", va="top", transform=ax.transAxes)
        tb = ax.table(cellText=[r[1] for r in rows], rowLabels=[r[0] for r in rows], colLabels=[u["id"] for u in UES],
                      bbox=[0.16, 0.55, 0.84, 0.42], cellLoc="center")
        tb.auto_set_font_size(False)
        tb.set_fontsize(8)
        for j, u in enumerate(UES):
            tb[0, j].get_text().set_color(u["color"])
            tb[0, j].get_text().set_fontweight("bold")
        for cell in tb.get_celld().values():
            cell.set_edgecolor("#d9d5cc")

        # takımyıldız
        serving = {k for k in s.srv if k >= 0}
        ref = s.ground_state(0.0)
        geo_only = s.layer == "GEO"
        ks = [] if geo_only else sorted([k for k in range(s.n_sat) if abs(s.sat_theta(k, s.t)) < VW * 1.6],
                                        key=lambda k: -s.sat_theta(k, s.t))
        y = 0.50
        ax.text(0, y, "SATELLITE" if geo_only else "CONSTELLATION", fontsize=10, fontweight="bold", transform=ax.transAxes)
        y -= 0.03
        for k in ks:
            st, c = self.sat_status(k, serving)
            el = link(ref, s.sat_state(k, s.t), s.fc)["el"]
            lab = "below horizon" if el < 0 else {"serve": "serving", "rise": "rising", "set": "setting"}[st]
            ax.text(0, y, f"{sat_name(k):<6} · α_ref = {el:6.1f}° · {lab}", fontsize=8, family="monospace", color=c,
                    transform=ax.transAxes)
            y -= 0.022
        gc = COL_SERVE if s.layer == "GEO" else "0.45"
        ax.text(0, y, f"{'GEO':<6} · α_ref = {link(ref, s.geo_state(), s.fc)['el']:6.1f}° · "
                      f"{'serving' if s.layer == 'GEO' else 'standby'}", fontsize=8, family="monospace", color=gc,
                transform=ax.transAxes)
        y -= 0.03
        if geo_only:
            info = (f"GEO h=35 786 km · fixed relative to Earth (T = 23 h 56 min)\n"
                    f"f_c={s.fc:g} GHz · sub-satellite offset {s.geo_lon:+.0f}°")
        else:
            info = (f"LEO h={s.h_leo:.0f} km · v={s.r_leo * s.omega:.2f} km/s · T={2 * np.pi / s.omega / 60:.1f} min · "
                    f"{s.n_sat}/plane\nf_c={s.fc:g} GHz · max |f_d| ≈ {fmt_hz(s.fc * 1e9 * s.omega * RE / C)[1:]}")
        ax.text(0, y, info, fontsize=8, color="0.4", transform=ax.transAxes, va="top")

        # kapsama (footprint) analizi
        cv = s.coverage()
        y -= 0.065
        ax.text(0, y, "COVERAGE", fontsize=10, fontweight="bold", transform=ax.transAxes)
        ax.text(0.30, y, "λ = arccos(R_E·cos ε / r) − ε", fontsize=8, color="0.4", transform=ax.transAxes)
        y -= 0.026
        lines = [
            (f"ε_min = {s.el_min:.0f}°", "0.2"),
            (f"LEO {s.h_leo:.0f} km: λ = {cv['lam_leo'] / D:.1f}° → radius {cv['r_leo_km']:.0f} km "
             f"({100 * cv['cap_leo']:.1f}% of Earth) · visible {cv['pass_min']:.1f} min", "0.2"),
            (f"GEO: λ = {cv['lam_geo'] / D:.1f}° → radius {cv['r_geo_km']:.0f} km ({100 * cv['cap_geo']:.0f}% of Earth)", "0.2"),
        ]
        if not geo_only:
            ok = cv["continuous"]
            lines.append((f"Sats/plane needed: N > π/λ = {cv['n_ratio']:.1f} → N_min = {cv['n_min']} · "
                          f"now {s.n_sat} → {'continuous ✓' if ok else 'COVERAGE GAPS ✗'}",
                          COL_RISE if ok else COL_SET))
        for txt, c in lines:
            ax.text(0, y, txt, fontsize=7.8, color=c, transform=ax.transAxes)
            y -= 0.021

        # bağlantı durumu + handover kaydı
        y -= 0.03
        ax.text(0, y, "LINK STATE", fontsize=10, fontweight="bold", transform=ax.transAxes)
        y -= 0.03
        if s.layer == "LEO":
            for i, u in enumerate(UES):
                ho = s.predict_ho(i)
                msg = (f"{sat_name(s.srv[i])} → HO in {fmt_t(ho) if ho else '>30:00'}" if s.srv[i] >= 0
                       else "no LEO coverage")
                ax.text(0, y, f"{u['id']:<5} {msg}", fontsize=8, family="monospace", color=u["color"], transform=ax.transAxes)
                y -= 0.022
        else:
            mx = max(abs(c["geo"]["fd"]) for c in cur)
            ax.text(0, y, f"GEO serving UEs in footprint · no handovers\nDoppler only from UE motion (max {fmt_hz(mx)})",
                    fontsize=8, transform=ax.transAxes, va="top")
            y -= 0.044
        rl = [c["leo"]["rtt"] for c in cur if c["leo"]]
        rg = np.mean([c["geo"]["rtt"] for c in cur])
        ax.text(0, y, f"Mean access RTT: GEO {rg:.1f} ms" if geo_only else
                f"Mean access RTT: LEO {np.mean(rl) if rl else 0:.1f} ms · GEO {rg:.1f} ms",
                fontsize=8, color="0.4", transform=ax.transAxes)
        y -= 0.03
        if geo_only:
            return
        ev = s.events[:6]
        ax.text(0, y, "\n".join(f"{fmt_t(e[0])} · {e[1]:<4} {sat_name(e[2])} → {sat_name(e[3])}" for e in ev)
                or "no handover events yet", fontsize=8, family="monospace", va="top", transform=ax.transAxes)

    def draw(self):
        cur = self.sim.current()
        self.draw_local(cur)
        self.draw_orbit(cur)
        self.draw_doppler()
        self.draw_info(cur)

    def step(self, _frame, dt=None):
        # Gerçek geçen süre kadar ilerle (matplotlib yavaş çizse de "Speed ×" doğru kalır)
        now = time.perf_counter()
        if dt is None:
            dt = min(1.0, now - getattr(self, "_last", now))
        self._last = now
        if self.sim.playing:
            self.sim.advance(dt * self.sim.speed)
        self.draw()


# ----------------------------------------------------------------- Colab / Jupyter yardımcıları
def make_sim(layer="LEO", fc=2.0, h_leo=600, n_sat=12, el_min=10, geo_lon=35, speed=30):
    """Verilen parametrelerle simülasyon nesnesi oluşturur."""
    sim = Sim()
    sim.layer, sim.fc, sim.h_leo, sim.n_sat = layer, float(fc), float(h_leo), int(n_sat)
    sim.el_min, sim.geo_lon, sim.speed = float(el_min), float(geo_lon), float(speed)
    sim.rebuild(keep_t=False)
    return sim


def coverage_figure(h_leo=600, el_min=10, n_sat=12, dpi=80, **_ignored):
    """Kapsama analizi figürü: λ = arccos(R_E·cos ε / r) − ε
    (a) kapsama yarıçapı – irtifa, (b) gereken uydu sayısı – irtifa,
    (c) kapsama üçgeni (seçilen LEO), (d) LEO ve GEO kapsaması gerçek ölçekte."""
    fig, axs = plt.subplots(2, 2, figsize=(15, 10), dpi=dpi)
    (a, b), (c, d) = axs
    hs = np.linspace(300, 2000, 300)
    eps_list = sorted({0, 10, 30, int(el_min)})
    colors = plt.get_cmap("viridis")(np.linspace(0, 0.85, len(eps_list)))

    # (a) kapsama yarıçapı
    for e, col in zip(eps_list, colors):
        lam = footprint(RE + hs, e)
        a.plot(hs, lam * RE, color=col, lw=2.2 if e == el_min else 1.3,
               label=f"ε = {e}°   (GEO: {footprint(RGEO, e) * RE:.0f} km)")
    lam0 = footprint(RE + h_leo, el_min)
    a.plot(h_leo, lam0 * RE, "o", color="k")
    a.annotate(f"{h_leo:.0f} km, ε={el_min:.0f}°\nλ={lam0 / D:.1f}° → {lam0 * RE:.0f} km", (h_leo, lam0 * RE),
               (h_leo + 120, lam0 * RE + 700), arrowprops=dict(arrowstyle="->"), fontsize=9)
    a.set_xlabel("LEO altitude h [km]")
    a.set_ylabel("footprint radius on ground  R_E·λ  [km]")
    a.set_title("(a) Coverage radius vs altitude and min elevation", loc="left", fontsize=10)
    a.grid(alpha=0.3)
    a.legend(fontsize=8)

    # (b) kesintisiz kapsama için düzlem başına gereken uydu sayısı
    for e, col in zip(eps_list, colors):
        nmin = np.floor(np.pi / footprint(RE + hs, e)) + 1
        b.step(hs, nmin, where="mid", color=col, lw=2.2 if e == el_min else 1.3, label=f"ε = {e}°")
    n0 = int(np.floor(np.pi / lam0)) + 1
    b.plot(h_leo, n0, "o", color="k")
    b.axhline(n_sat, color="0.4", ls="--", lw=1)
    b.text(hs[-1], n_sat + 0.4, f"simulation: N = {n_sat}", ha="right", fontsize=8, color="0.3")
    b.annotate(f"N_min = {n0}", (h_leo, n0), (h_leo + 150, n0 + 6), arrowprops=dict(arrowstyle="->"), fontsize=9)
    b.set_xlabel("LEO altitude h [km]")
    b.set_ylabel("satellites per plane  N_min = ⌊π/λ⌋ + 1")
    b.set_title("(b) Satellites needed for continuous coverage (one plane)", loc="left", fontsize=10)
    b.set_ylim(0, 40)
    b.grid(alpha=0.3)
    b.legend(fontsize=8)

    # (c) kapsama üçgeni: Dünya merkezi O, sınırdaki UE U, uydu S
    r = RE + h_leo
    eta = np.arcsin(RE * np.cos(el_min * D) / r)
    pol = lambda th, rr: (rr * np.sin(th), rr * np.cos(th))
    th = np.linspace(-0.45, 0.45, 300)
    c.fill_between(*pol(th, RE), RE * 0.75, color=COL_EARTH)
    c.plot(*pol(th, RE), color="0.25", lw=1.2)
    c.plot(*pol(th, r), "--", color="0.6", lw=1)
    S, U = np.array(pol(0, r)), np.array(pol(lam0, RE))
    c.plot(*zip(S, U), color=COL_SERVE, lw=2)
    c.plot(*zip(S, pol(-lam0, RE)), color=COL_SERVE, lw=2)
    c.plot(*pol(np.linspace(-lam0, lam0, 80), RE * 1.002), color=COL_SERVE, lw=5, alpha=0.6)
    c.plot([0, 0], [RE * 0.75, r], ":", color="0.4")
    c.plot([0, U[0] * 0.93], [RE * 0.75, RE * 0.75 + (U[1] - RE * 0.75) * 0.93], ":", color="0.4")
    hor = np.array([np.cos(lam0), -np.sin(lam0)])       # UE'nin yerel ufku
    c.plot(*zip(U - hor * 900, U + hor * 300), color="0.5", lw=1)
    c.plot(*S, "s", ms=10, color=COL_SERVE, mec="k")
    c.plot(*U, "o", ms=7, color=UES[2]["color"], mec="k")
    c.text(S[0] + 60, S[1] + 40, f"satellite  (h = {h_leo:.0f} km)", fontsize=9)
    c.text(S[0] + 110, S[1] - 420, f"η = {eta / D:.1f}°\n(nadir angle)", fontsize=9, color=COL_SERVE)
    c.text(U[0] + 60, U[1] + 70, f"ε = {el_min:.0f}°", fontsize=10, color=UES[2]["color"], fontweight="bold")
    c.text(U[0] - 40, U[1] - 260, "UE at coverage edge", fontsize=8, ha="center")
    c.text(lam0 * RE * 0.25, RE * 0.8, f"λ = {lam0 / D:.1f}°  (Earth-centre angle)", fontsize=9)
    c.text(0, RE + 40, f"radius = R_E·λ = {lam0 * RE:.0f} km", fontsize=9, ha="center", color=COL_SERVE, fontweight="bold")
    c.set_aspect("equal")
    c.set_xlim(-0.5 * r, 0.5 * r)
    c.set_ylim(RE * 0.78, r * 1.06)
    c.set_xticks([]), c.set_yticks([])
    c.set_title("(c) Geometry:  sin η = R_E·cos ε / r ,  λ = 90° − ε − η", loc="left", fontsize=10)

    # (d) LEO ve GEO kapsaması gerçek ölçekte
    full = np.linspace(0, 2 * np.pi, 361)
    d.fill(*pol(full, RE), color=COL_EARTH, ec="0.25")
    d.plot(*pol(full, r), "--", color="0.6", lw=0.8)
    d.plot(*pol(full, RGEO), "--", color="0.6", lw=0.8)
    lg = footprint(RGEO, el_min)
    for th0, rr, lam, col, name in [(0.0, r, lam0, COL_SERVE, "LEO"), (np.pi / 2, RGEO, lg, "#2f6fb5", "GEO")]:
        ex, ey = pol(np.linspace(th0 - lam, th0 + lam, 100), RE)
        sx, sy = pol(th0, rr)
        d.fill(np.r_[sx, ex], np.r_[sy, ey], color=col, alpha=0.18, lw=0)
        d.plot(*pol(np.linspace(th0 - lam, th0 + lam, 100), RE * 1.01), color=col, lw=4)
        d.plot(sx, sy, "s", color=col, mec="k", ms=8)
    d.text(*pol(0, r + 2500), f"LEO: ±{lam0 / D:.1f}°", ha="center", color=COL_SERVE, fontsize=9, fontweight="bold")
    d.text(*pol(np.pi / 2, RGEO + 1500), f"GEO: ±{lg / D:.1f}°", ha="left", va="center", color="#2f6fb5", fontsize=9,
           fontweight="bold")
    cap_l, cap_g = (1 - np.cos(lam0)) / 2, (1 - np.cos(lg)) / 2
    d.text(-RGEO * 1.05, -RGEO * 1.0,
           f"Covered share of Earth surface:\n  one LEO sat: {100 * cap_l:.1f}%\n  one GEO sat: {100 * cap_g:.0f}%  "
           f"(≈ {cap_g / cap_l:.0f}× LEO)", fontsize=9, va="bottom")
    d.set_aspect("equal")
    d.set_xlim(-RGEO * 1.1, RGEO * 1.25)
    d.set_ylim(-RGEO * 1.1, RGEO * 1.1)
    d.set_xticks([]), d.set_yticks([])
    d.set_title(f"(d) LEO vs GEO coverage to scale (ε = {el_min:.0f}°)", loc="left", fontsize=10)
    fig.suptitle("Footprint:  λ = arccos(R_E·cos ε / r) − ε     radius = R_E·λ     "
                 "continuous coverage in one plane needs  N > π/λ", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def snapshot(t=0.0, dpi=80, **params):
    """t [s] anındaki tek kareyi çizer ve figürü döndürür (notebook'ta gösterilir)."""
    sim = make_sim(**params)
    app = App(sim, interactive=False)
    sim.advance(t)
    app.draw()
    app.fig.set_dpi(dpi)
    return app.fig


def animate(frames=60, step_s=30.0, dpi=60, **params):
    """Her karede step_s simülasyon saniyesi ilerleyen animasyon döndürür.
    Notebook'ta: HTML(animate(...).to_jshtml())"""
    sim = make_sim(**params)
    app = App(sim, interactive=False)
    app.fig.set_dpi(dpi)
    def update(_f):
        sim.advance(step_s)
        app.draw()
    app.draw()
    anim = FuncAnimation(app.fig, update, frames=frames, interval=200)
    plt.close(app.fig)   # notebook'ta fazladan statik figür görünmesin
    return anim


# ----------------------------------------------------------------- ana program
def main():
    ap = argparse.ArgumentParser(description="LEO/GEO NTN Doppler & coverage simulator")
    ap.add_argument("--save", help="animasyonu kaydet (.gif veya .mp4)")
    ap.add_argument("--frames", type=int, default=200, help="--save için kare sayısı")
    ap.add_argument("--png", help="tek kareyi PNG olarak kaydet")
    ap.add_argument("--coverage", help="kapsama analizi figürünü PNG olarak kaydet")
    ap.add_argument("--t", type=float, default=0.0, help="--png için simülasyon zamanı [s]")
    ap.add_argument("--layer", choices=["LEO", "GEO"], default="LEO")
    ap.add_argument("--fc", type=float, default=2.0, help="taşıyıcı frekans [GHz]")
    ap.add_argument("--speed", type=float, default=30.0, help="simülasyon hızı [×]")
    a = ap.parse_args()

    sim = Sim()
    sim.layer, sim.fc, sim.speed = a.layer, a.fc, a.speed
    sim.rebuild(keep_t=False)

    if a.coverage:
        coverage_figure(h_leo=sim.h_leo, el_min=sim.el_min, n_sat=sim.n_sat).savefig(a.coverage, dpi=110)
        print("saved", a.coverage)
    elif a.png:
        app = App(sim, interactive=False)
        sim.advance(a.t)
        app.draw()
        app.fig.savefig(a.png, dpi=110)
        print("saved", a.png)
    elif a.save:
        app = App(sim, interactive=False)
        # kayıtta her kare sabit 0.5 s gerçek zamana karşılık gelir
        anim = FuncAnimation(app.fig, lambda f: app.step(f, dt=0.5), frames=a.frames, interval=150)
        anim.save(a.save, fps=8, dpi=80)
        print("saved", a.save)
    else:
        app = App(sim, interactive=True)
        app.anim = FuncAnimation(app.fig, app.step, interval=150, cache_frame_data=False)
        plt.show()


if __name__ == "__main__":
    main()
