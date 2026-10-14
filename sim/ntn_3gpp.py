"""
3GPP NTN link budget, coverage and capacity
==========================================

Formüller ve tablolar şu iki belgeden alınmıştır:
  - 3GPP TR 38.811 V15.4.0  (NTN kanal modeli)
      (6.6-1) PL = PL_b + PL_g + PL_s + PL_e         toplam yol kaybı
      (6.6-2) FSPL = 32.45 + 20log10(f_c[GHz]) + 20log10(d[m])
      (6.6-3) d = sqrt(R_E² sin²α + h² + 2 h R_E) − R_E sin α      eğik mesafe
      (6.6-4) PL_b = FSPL + SF + CL                     SF ~ N(0, σ_SF²), CL sadece NLOS
      (6.6-8) PL_g = A_zenith(f_c) / sin α             atmosferik gaz kaybı
      Tablo 6.6.1-1      LOS olasılığı
      Tablo 6.6.2-1/2/3  gölgeleme (σ_SF) ve clutter kaybı (CL)
      Tablo 6.6.6.2.1-1  troposferik sintilasyon (Ka-band)
  - 3GPP TR 38.821 V16.2.0  (NTN çözümleri)
      (6.1.3.1-1) CNIR = 1 / (1/CNR + 1/CIR)            (doğrusal)
      (6.1.3.1-2) CNR = EIRP + G/T − k − PL_FS − PL_A − PL_SM − PL_SL − PL_AD − 10log10(B)
      (6.1.3.1-3) G/T = G_a − NF − 10log10(T_0 + (T_a − T_0)·10^(−0.1·NF))
      (6.1.3.1-5) EIRP = P_T − L_C + G_T
      Tablo 6.1.1.1-1/2  uydu parametreleri (Set-1 / Set-2)
      Tablo 6.1.1.1-3    UE parametreleri (VSAT, el cihazı)
      Tablo 6.1.3.2-1    link budget ayarları (bant genişliği, hedef elevasyon, kayıplar)
      Tablo 6.1.1.2-1    DL geometri SIR (CIR) kalibrasyon sonuçları
      Tablo 6.1.3.3-1    link budget sonuçları (doğrulama için)
      Tablo 6.1.1.3-1    SLS UE throughput sonuçları (kapasite karşılaştırması için)

Belgelerde OLMAYAN, burada eklenenler (açıkça işaretli):
  - Kapasite için Shannon sınırı  C = B·log2(1 + CNIR)   (bilgi kuramı üst sınırı)
  - Kapsama eşiği SNR_MIN_DB (varsayılan −6 dB ≈ NR'nin en düşük MCS'inin çalışma noktası)
  - (6.6-8)'deki zenit zayıflaması A_zenith: belgede ITU-R P.676 Şekil 6'ya atıf var, sayısal değer
    yok. Değerler TR 38.821 Tablo 6.1.3.3-1'deki atmosfer kayıplarından (6.6-8) ile geri hesaplandı.
"""
import numpy as np

RE = 6371.0                 # Dünya yarıçapı [km]
MU = 398600.4418            # Dünya kütleçekim parametresi [km^3/s^2]
K_BOLTZMANN_DBW = -228.6    # Boltzmann sabiti [dBW/K/Hz]          (TR 38.821 §6.1.3.1)
T0 = 290.0                  # ortam sıcaklığı [K]                  (TR 38.821 (6.1.3.1-3))
SNR_MIN_DB = -6.0           # kapsama eşiği [dB] — belgelerde tanımlı DEĞİL, değiştirilebilir

ORBITS = {"GEO": 35786.0, "LEO-1200": 1200.0, "LEO-600": 600.0}
REF_EL = np.arange(10, 91, 10)    # 38.811 tablolarının referans elevasyonları

# ---------------------------------------------------------------- TR 38.821 Tablo 6.1.1.1-1 / -2
# Işın başına: EIRP yoğunluğu [dBW/MHz] (DL), Tx kazancı [dBi], ışın çapı [km] (nadir), G/T [dB/K] (UL)
SAT_PARAMS = {
    "Set-1": {
        "GEO":      {"S":  dict(eirp_density=59.0, tx_gain=51.0, beam_km=250, gt=19.0),
                     "Ka": dict(eirp_density=40.0, tx_gain=58.5, beam_km=110, gt=28.0)},
        "LEO-1200": {"S":  dict(eirp_density=40.0, tx_gain=30.0, beam_km=90,  gt=1.1),
                     "Ka": dict(eirp_density=10.0, tx_gain=38.5, beam_km=40,  gt=13.0)},
        "LEO-600":  {"S":  dict(eirp_density=34.0, tx_gain=30.0, beam_km=50,  gt=1.1),
                     "Ka": dict(eirp_density=4.0,  tx_gain=38.5, beam_km=20,  gt=13.0)},
    },
    "Set-2": {
        "GEO":      {"S":  dict(eirp_density=53.5, tx_gain=45.5, beam_km=450, gt=14.0),
                     "Ka": dict(eirp_density=32.0, tx_gain=50.5, beam_km=280, gt=20.0)},
        "LEO-1200": {"S":  dict(eirp_density=34.0, tx_gain=24.0, beam_km=190, gt=-4.9),
                     "Ka": dict(eirp_density=2.0,  tx_gain=30.5, beam_km=90,  gt=5.0)},
        "LEO-600":  {"S":  dict(eirp_density=28.0, tx_gain=24.0, beam_km=90,  gt=-4.9),
                     "Ka": dict(eirp_density=-4.0, tx_gain=30.5, beam_km=50,  gt=5.0)},
    },
}

# ---------------------------------------------------------------- TR 38.821 Tablo 6.1.1.1-3
UE_PARAMS = {
    "VSAT":     dict(band="Ka", rx_gain=39.7, t_ant=150.0, nf=1.2, tx_power_dbm=33.0, tx_gain=43.2),
    "Handheld": dict(band="S",  rx_gain=0.0,  t_ant=290.0, nf=7.0, tx_power_dbm=23.0, tx_gain=0.0),
}

# ---------------------------------------------------------------- TR 38.821 Tablo 6.1.3.2-1
BANDS = {
    "S":  dict(f_dl=2.0,  f_ul=2.0,  sys_bw_mhz=30.0,  ul_bw_handheld_mhz=0.36),
    "Ka": dict(f_dl=20.0, f_ul=30.0, sys_bw_mhz=400.0, ul_bw_handheld_mhz=None),
}
TARGET_EL = {("LEO", "Set-1"): 30.0, ("LEO", "Set-2"): 30.0, ("GEO", "Set-1"): 12.5, ("GEO", "Set-2"): 20.0}
SHADOW_MARGIN = {"VSAT": 0.0, "Handheld": 3.0}          # "0 dB VSAT, 3 dB diğerleri"
IONO_SCINT_S_DB = 2.2                                   # "P3 eğrisi, zamanın %1'i" (Not 1)
REUSE_OPTION = {1: 1, 2: 3, 3: 2}                       # Option 1/2/3 → frekans yeniden kullanım faktörü

# ---------------------------------------------------------------- TR 38.821 Tablo 6.1.1.2-1 (DL geometri SIR, %50)
CIR_DL_MEDIAN = {1: -1.1, 2: 9.9, 3: 9.0}               # yeniden kullanım faktörü → CIR [dB]

# ---------------------------------------------------------------- TR 38.811 (6.6-8) zenit zayıflaması
# (geri hesaplandı: TR 38.821 Tablo 6.1.3.3-1'deki PL_A değerlerini ±0.05 dB içinde verir)
ZENITH_ATT_DB = {2.0: 0.04, 20.0: 0.26, 30.0: 0.24}

# ---------------------------------------------------------------- TR 38.811 Tablo 6.6.6.2.1-1 (Ka, %99)
TROPO_SCINT_KA_DB = [1.08, 0.48, 0.30, 0.22, 0.17, 0.13, 0.12, 0.12, 0.12]

# ---------------------------------------------------------------- TR 38.811 Tablo 6.6.1-1 (LOS olasılığı, %)
LOS_PROB = {
    "dense urban":    [28.2, 33.1, 39.8, 46.8, 53.7, 61.2, 73.8, 82.0, 98.1],
    "urban":          [24.6, 38.6, 49.3, 61.3, 72.6, 80.5, 91.9, 96.8, 99.2],
    "suburban/rural": [78.2, 86.9, 91.9, 92.9, 93.5, 94.0, 94.9, 95.2, 99.8],
}

# ---------------------------------------------------------------- TR 38.811 Tablo 6.6.2-1/2/3
# her elevasyon için (σ_SF LOS, σ_SF NLOS, CL NLOS) [dB]
SF_CL = {
    "dense urban": {
        "S":  [(3.5, 15.5, 34.3), (3.4, 13.9, 30.9), (2.9, 12.4, 29.0), (3.0, 11.7, 27.7), (3.1, 10.6, 26.8),
               (2.7, 10.5, 26.2), (2.5, 10.1, 25.8), (2.3, 9.2, 25.5), (1.2, 9.2, 25.5)],
        "Ka": [(2.9, 17.1, 44.3), (2.4, 17.1, 39.9), (2.7, 15.6, 37.5), (2.4, 14.6, 35.8), (2.4, 14.2, 34.6),
               (2.7, 12.6, 33.8), (2.6, 12.1, 33.3), (2.8, 12.3, 33.0), (0.6, 12.3, 32.9)],
    },
    "urban": {
        "S":  [(4, 6, cl) for cl in (34.3, 30.9, 29.0, 27.7, 26.8, 26.2, 25.8, 25.5, 25.5)],
        "Ka": [(4, 6, cl) for cl in (44.3, 39.9, 37.5, 35.8, 34.6, 33.8, 33.3, 33.0, 32.9)],
    },
    "suburban/rural": {
        "S":  [(1.79, 8.93, 19.52), (1.14, 9.08, 18.17), (1.14, 8.78, 18.42), (0.92, 10.25, 18.28),
               (1.42, 10.56, 18.63), (1.56, 10.74, 17.68), (0.85, 10.17, 16.50), (0.72, 11.52, 16.30),
               (0.72, 11.52, 16.30)],
        "Ka": [(1.9, 10.7, 29.5), (1.6, 10.0, 24.6), (1.9, 11.2, 21.9), (2.3, 11.6, 20.0), (2.7, 11.8, 18.7),
               (3.1, 10.8, 17.8), (3.0, 10.8, 17.2), (3.6, 10.8, 16.9), (0.4, 10.8, 16.8)],
    },
}

# ---------------------------------------------------------------- TR 38.821 Tablo 6.1.3.3-1 (doğrulama)
CNR_38821 = {  # vaka: (DL CNR, UL CNR) [dB]
    1: (11.6, 0.5), 2: (11.6, 5.2), 3: (11.6, 3.5), 4: (0.0, -10.9), 5: (0.0, -10.9),
    6: (8.5, 18.4), 7: (8.5, 23.1), 8: (8.5, 21.4), 9: (6.6, 2.8), 10: (6.6, 2.8),
    11: (9.1, 13.0), 12: (9.1, 17.8), 13: (9.1, 16.0), 14: (7.2, -2.6), 15: (7.2, -2.6),
    16: (4.8, -6.3), 17: (4.8, -1.6), 18: (4.8, -3.3), 19: (-5.2, -15.7), 20: (-5.2, -15.7),
    21: (0.5, 10.4), 22: (0.5, 15.1), 23: (0.5, 13.4), 24: (0.6, -3.2), 25: (0.6, -3.2),
    26: (1.1, 5.0), 27: (1.1, 9.8), 28: (1.1, 8.0), 29: (1.2, -8.6), 30: (1.2, -8.6),
}

# ---------------------------------------------------------------- TR 38.821 Tablo 6.1.1.3-1 (SLS, DL UE throughput, Mbit/s)
# 10 UE/hücre, proportional fair, kırsal, TR 38.811 LOS olasılığı; (5%, 50%, 95%)
SLS_THROUGHPUT = {
    # vaka: (yörünge, bant, yeniden kullanım, {RU: (5%, 50%, 95%)})
    1:  ("GEO", "Ka", 1, {"20%": (0.96, 2.70, 4.93), "~50%": (5.34, 8.53, 11.99)}),
    2:  ("GEO", "Ka", 3, {"20%": (0.48, 2.05, 3.90), "~50%": (4.03, 6.61, 9.99)}),
    6:  ("LEO-600", "Ka", 1, {"20%": (2.04, 4.08, 6.43), "~50%": (6.91, 10.03, 13.70)}),
    7:  ("LEO-600", "Ka", 3, {"20%": (1.02, 2.78, 4.70), "~50%": (4.76, 7.75, 11.22)}),
    9:  ("LEO-600", "S", 1, {"20%": (0.11, 0.31, 0.52), "~50%": (0.44, 0.74, 1.09)}),
    10: ("LEO-600", "S", 3, {"20%": (0.03, 0.15, 0.34), "~50%": (0.30, 0.58, 0.88)}),
    14: ("LEO-1200", "S", 1, {"20%": (0.11, 0.30, 0.52), "~50%": (0.40, 0.78, 1.09)}),
    15: ("LEO-1200", "S", 3, {"20%": (0.05, 0.19, 0.41), "~50%": (0.31, 0.60, 0.90)}),
}


# ================================================================ temel formüller
def ref_index(el_deg):
    """38.811: en yakın referans elevasyonun (10°, 20°, …, 90°) indeksi."""
    return int(np.clip(np.round(np.asarray(el_deg) / 10.0), 1, 9)) - 1


def slant_range_km(h_km, el_deg):
    """TR 38.811 (6.6-3): eğik mesafe d [km]."""
    a = np.radians(el_deg)
    return np.sqrt((RE * np.sin(a)) ** 2 + h_km ** 2 + 2 * h_km * RE) - RE * np.sin(a)


def fspl_db(d_km, f_ghz):
    """TR 38.811 (6.6-2): FSPL = 32.45 + 20log10(f_c[GHz]) + 20log10(d[m])."""
    return 32.45 + 20 * np.log10(f_ghz) + 20 * np.log10(np.asarray(d_km) * 1e3)


def atm_loss_db(f_ghz, el_deg):
    """TR 38.811 (6.6-8): PL_g = A_zenith(f) / sin α."""
    az = ZENITH_ATT_DB.get(float(f_ghz), np.interp(f_ghz, [2, 20, 30], [0.04, 0.26, 0.24]))
    return az / np.sin(np.radians(el_deg))


def scint_loss_db(band, el_deg, low_latitude=True):
    """Sintilasyon: S-band iyonosferik (TR 38.821 Tablo 6.1.3.2-1, ±20° enlem; 20–60° enlemde 0 dB),
    Ka-band troposferik (TR 38.811 Tablo 6.6.6.2.1-1)."""
    if band == "S":
        return IONO_SCINT_S_DB if low_latitude else 0.0
    return TROPO_SCINT_KA_DB[ref_index(el_deg)]


def ue_gt_db(terminal):
    """TR 38.821 (6.1.3.1-3): G/T = G_a − NF − 10log10(T0 + (T_a − T0)·10^(−0.1 NF))."""
    p = UE_PARAMS[terminal]
    return p["rx_gain"] - p["nf"] - 10 * np.log10(T0 + (p["t_ant"] - T0) * 10 ** (-0.1 * p["nf"]))


def los_probability(scenario, el_deg):
    """TR 38.811 Tablo 6.6.1-1 (en yakın referans açı)."""
    return LOS_PROB[scenario][ref_index(el_deg)] / 100.0


def sf_cl(scenario, band, el_deg):
    """TR 38.811 Tablo 6.6.2-x: (σ_SF LOS, σ_SF NLOS, CL NLOS) [dB]."""
    return SF_CL[scenario][band][ref_index(el_deg)]


def db2lin(x):
    return 10 ** (np.asarray(x) / 10.0)


def lin2db(x):
    return 10 * np.log10(x)


def shannon_bps(bw_hz, snr_db):
    """Shannon sınırı C = B·log2(1 + SNR)  — 3GPP belgelerinde formül olarak YOK, üst sınır."""
    return bw_hz * np.log2(1 + db2lin(snr_db))


def orbit_type(orbit):
    return "GEO" if orbit == "GEO" else "LEO"


# ================================================================ link budget (TR 38.821 §6.1.3)
def link_budget(orbit="LEO-600", band="S", direction="DL", el_deg=None, set_name="Set-1", reuse=1,
                terminal=None, low_latitude=True, shadow_margin_db=None, h_km=None):
    """TR 38.821 (6.1.3.1-1/-2) link budget. Tüm terimleri ve CNR, CIR, CNIR, Shannon kapasitesini döndürür.
    el_deg verilmezse Tablo 6.1.3.2-1'deki hedef elevasyon kullanılır.
    h_km verilirse yörünge irtifası bu değerle değiştirilir (EIRP yoğunluğu aynı kalır)."""
    terminal = terminal or ("Handheld" if band == "S" else "VSAT")
    if el_deg is None:
        el_deg = TARGET_EL[(orbit_type(orbit), set_name)]
    h = ORBITS[orbit] if h_km is None else h_km
    sat = SAT_PARAMS[set_name][orbit][band]
    ue = UE_PARAMS[terminal]
    b = BANDS[band]
    f = b["f_dl"] if direction == "DL" else b["f_ul"]
    if direction == "DL":
        bw_mhz = b["sys_bw_mhz"] / reuse
        eirp_dbw = sat["eirp_density"] + 10 * np.log10(bw_mhz)           # yoğunluk × bant genişliği
        gt = ue_gt_db(terminal)
    else:
        bw_mhz = b["ul_bw_handheld_mhz"] if terminal == "Handheld" else b["sys_bw_mhz"] / reuse
        eirp_dbw = ue["tx_power_dbm"] - 30 + ue["tx_gain"]               # (6.1.3.1-5), L_C = 0
        gt = sat["gt"]
    d = slant_range_km(h, el_deg)
    pl_fs = fspl_db(d, f)
    pl_a = atm_loss_db(f, el_deg)
    pl_sm = SHADOW_MARGIN[terminal] if shadow_margin_db is None else shadow_margin_db
    pl_sl = scint_loss_db(band, el_deg, low_latitude)
    pl_ad = 0.0
    bw_hz = bw_mhz * 1e6
    cnr = eirp_dbw + gt - K_BOLTZMANN_DBW - pl_fs - pl_a - pl_sm - pl_sl - pl_ad - 10 * np.log10(bw_hz)  # (6.1.3.1-2)
    cir = CIR_DL_MEDIAN[reuse] if direction == "DL" else np.inf
    cnir = cnr if np.isinf(cir) else lin2db(1 / (1 / db2lin(cnr) + 1 / db2lin(cir)))                   # (6.1.3.1-1)
    return dict(orbit=orbit, band=band, direction=direction, terminal=terminal, set=set_name, reuse=reuse,
                el=el_deg, h_km=h, f_ghz=f, d_km=d, eirp_dbw=eirp_dbw, eirp_dbm=eirp_dbw + 30, gt=gt,
                bw_mhz=bw_mhz, pl_fs=pl_fs, pl_a=pl_a, pl_sm=pl_sm, pl_sl=pl_sl, pl_ad=pl_ad,
                cnr=cnr, cir=cir, cnir=cnir,
                se=np.log2(1 + db2lin(cnir)), capacity_bps=shannon_bps(bw_hz, cnir))


def study_case(n):
    """TR 38.821 Tablo 6.1.1.1-9: vaka numarası → (yörünge, set, bant, yeniden kullanım)."""
    set_name = "Set-1" if n <= 15 else "Set-2"
    m = (n - 1) % 15 + 1
    table = [("GEO", "Ka", 1), ("GEO", "Ka", 2), ("GEO", "Ka", 3), ("GEO", "S", 1), ("GEO", "S", 2),
             ("LEO-600", "Ka", 1), ("LEO-600", "Ka", 2), ("LEO-600", "Ka", 3), ("LEO-600", "S", 1), ("LEO-600", "S", 2),
             ("LEO-1200", "Ka", 1), ("LEO-1200", "Ka", 2), ("LEO-1200", "Ka", 3), ("LEO-1200", "S", 1), ("LEO-1200", "S", 2)]
    orbit, band, opt = table[m - 1]
    return orbit, set_name, band, REUSE_OPTION[opt]


def validate_38821(verbose=True):
    """TR 38.821 Tablo 6.1.3.3-1'deki 30 vakanın CNR değerlerini yeniden üretir."""
    rows = []
    for n in range(1, 31):
        orbit, set_name, band, reuse = study_case(n)
        for j, direction in enumerate(("DL", "UL")):
            lb = link_budget(orbit, band, direction, set_name=set_name, reuse=reuse)
            rows.append((n, direction, orbit, set_name, band, reuse, lb["el"], CNR_38821[n][j], lb["cnr"]))
    if verbose:
        print(f"{'SC':>3} {'dir':3} {'orbit':8} {'set':5} {'band':4} {'reuse':>5} {'el':>5} "
              f"{'3GPP CNR':>9} {'bizim':>7} {'fark':>6}")
        for n, dr, o, st, b, r, el, ref, ours in rows:
            print(f"{n:>3} {dr:3} {o:8} {st:5} {b:4} {r:>5} {el:>5.1f} {ref:>9.1f} {ours:>7.2f} {ours - ref:>+6.2f}")
        err = np.array([r[-1] - r[-2] for r in rows])
        print(f"\n60 değer: en büyük |fark| = {np.abs(err).max():.2f} dB, ortalama |fark| = {np.abs(err).mean():.2f} dB")
    return rows


def print_link_budget(lb):
    """Bir link budget'ı TR 38.821 Tablo 6.1.3.3-1 düzeninde yazdırır."""
    print(f"{lb['orbit']} {lb['set']} {lb['band']}-band {lb['direction']}, {lb['terminal']}, "
          f"yeniden kullanım {lb['reuse']}, α = {lb['el']:.1f}°")
    items = [("Frekans [GHz]", lb["f_ghz"]), ("Eğik mesafe d [km]  (6.6-3)", lb["d_km"]),
             ("TX: EIRP [dBm]", lb["eirp_dbm"]), ("RX: G/T [dB/K]  (6.1.3.1-3)", lb["gt"]),
             ("Bant genişliği [MHz]", lb["bw_mhz"]), ("FSPL [dB]  (6.6-2)", lb["pl_fs"]),
             ("Atmosfer kaybı [dB]  (6.6-8)", lb["pl_a"]), ("Gölgeleme payı [dB]", lb["pl_sm"]),
             ("Sintilasyon kaybı [dB]", lb["pl_sl"]), ("Ek kayıp [dB]", lb["pl_ad"]),
             ("CNR [dB]  (6.1.3.1-2)", lb["cnr"]), ("CIR [dB]  (Tablo 6.1.1.2-1)", lb["cir"]),
             ("CNIR [dB]  (6.1.3.1-1)", lb["cnir"]),
             ("Spektral verim [b/s/Hz]  (Shannon)", lb["se"]),
             ("Işın kapasitesi [Mbit/s]  (Shannon)", lb["capacity_bps"] / 1e6)]
    for k, v in items:
        print(f"  {k:<38} {v:>10.2f}" if np.isfinite(v) else f"  {k:<38} {'—':>10}")


# ================================================================ kapsama ve kapasite
def coverage_mc(orbit="LEO-600", band="S", scenario="suburban/rural", el_grid=None, n=20000,
                snr_min_db=SNR_MIN_DB, set_name="Set-1", reuse=1, seed=1, direction="DL"):
    """TR 38.811 büyük ölçekli modeli ile Monte Carlo kapsama olasılığı.
    Her elevasyonda: LOS ~ Bernoulli(P_LOS) [Tablo 6.6.1-1], SF ~ N(0, σ²) ve NLOS ise CL [Tablo 6.6.2-x]
    (6.6-4) PL_b = FSPL + SF + CL. 38.821'deki sabit 3 dB gölgeleme payının yerine rastgele SF+CL kullanılır.
    Dönüş: el, P(CNR ≥ eşik), P(CNIR ≥ eşik), ortalama spektral verim (Shannon), LOS olasılığı."""
    rng = np.random.default_rng(seed)
    el_grid = np.arange(10, 91, 2.5) if el_grid is None else np.asarray(el_grid)
    p_cnr, p_cnir, se_mean, plos = [], [], [], []
    for el in el_grid:
        lb = link_budget(orbit, band, direction, el, set_name, reuse, shadow_margin_db=0.0)
        pl = los_probability(scenario, el)
        s_los, s_nlos, cl = sf_cl(scenario, band, el)
        los = rng.random(n) < pl
        sf = np.where(los, rng.normal(0, s_los, n), rng.normal(0, s_nlos, n))
        cnr = lb["cnr"] - sf - np.where(los, 0.0, cl)
        cnir = cnr if not np.isfinite(lb["cir"]) else lin2db(1 / (1 / db2lin(cnr) + 1 / db2lin(lb["cir"])))
        p_cnr.append(np.mean(cnr >= snr_min_db))
        p_cnir.append(np.mean(cnir >= snr_min_db))
        se_mean.append(np.mean(np.log2(1 + db2lin(cnir))))
        plos.append(pl)
    return dict(el=el_grid, p_cnr=np.array(p_cnr), p_cnir=np.array(p_cnir), se=np.array(se_mean), p_los=np.array(plos))


def pass_elevation(h_km, t_s):
    """Tepe geçişi (UE yörünge düzleminde): t = 0 anında uydu tam tepede. Dönüş: elevasyon [derece]."""
    r = RE + h_km
    beta = np.sqrt(MU / r ** 3) * np.asarray(t_s)
    return np.degrees(np.arctan2(np.cos(beta) - RE / r, np.abs(np.sin(beta)) + 1e-12))


def footprint_rad(h_km, el_min_deg):
    """Geometrik kapsama açısı λ = arccos(R_E cos ε / r) − ε  (TR 38.811 (6.6-3) geometrisi)."""
    e = np.radians(el_min_deg)
    return np.arccos(RE * np.cos(e) / (RE + h_km)) - e


def beams_per_footprint(orbit, band, set_name="Set-1", el_min_deg=10.0):
    """Görünürlük alanını nadir ışın çapıyla kaplamak için yaklaşık ışın sayısı (alan oranı).
    Işınlar nadirden uzakta büyüdüğü için bu bir üst kestirimdir."""
    lam = footprint_rad(ORBITS[orbit], el_min_deg)
    cap_area = 2 * np.pi * RE ** 2 * (1 - np.cos(lam))
    beam = SAT_PARAMS[set_name][orbit][band]["beam_km"]
    return cap_area / (np.pi * (beam / 2) ** 2)


# ================================================================ figürler
_COL = {"GEO": "#2f6fb5", "LEO-1200": "#7b55b0", "LEO-600": "#a8761d"}
_SCN = {"dense urban": "#c0504d", "urban": "#d0712b", "suburban/rural": "#4f9a5a"}


def plot_coverage(band="S", set_name="Set-1", reuse=1, snr_min_db=SNR_MIN_DB, el_min=10.0, h_leo=600, dpi=80):
    """Radyo kapsaması (TR 38.821 link budget + TR 38.811 kanal modeli), 2×2 figür."""
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 2, figsize=(15, 10), dpi=dpi)
    (a, b), (c, d) = axs
    els = np.arange(10, 90.1, 1)

    # (a) CNR – elevasyon (deterministik 38.821 link budget)
    for orbit in ORBITS:
        dl = [link_budget(orbit, band, "DL", e, set_name, reuse)["cnr"] for e in els]
        ul = [link_budget(orbit, band, "UL", e, set_name, reuse)["cnr"] for e in els]
        a.plot(els, dl, color=_COL[orbit], lw=2, label=f"{orbit} DL")
        a.plot(els, ul, "--", color=_COL[orbit], lw=1.3, label=f"{orbit} UL")
    a.axhline(snr_min_db, color="k", ls=":", lw=1)
    a.text(89, snr_min_db + 0.4, f"threshold {snr_min_db:g} dB", ha="right", fontsize=8)
    a.set_xlabel("elevation α [°]")
    a.set_ylabel("CNR [dB]")
    a.set_title(f"(a) CNR vs elevation — TR 38.821 (6.1.3.1-2), {set_name}, {band}-band, LOS", loc="left", fontsize=10)
    a.grid(alpha=0.3)
    a.legend(fontsize=7, ncol=3)

    # (b) kapsama olasılığı – elevasyon, 3 senaryo (38.811 Monte Carlo)
    for scn in LOS_PROB:
        mc = coverage_mc("LEO-600", band, scn, snr_min_db=snr_min_db, set_name=set_name, reuse=reuse)
        b.plot(mc["el"], 100 * mc["p_cnr"], color=_SCN[scn], lw=2, label=f"{scn}  (CNR)")
        b.plot(mc["el"], 100 * mc["p_los"], ":", color=_SCN[scn], lw=1, label=f"{scn}  P_LOS")
    b.set_ylim(0, 102)
    b.set_xlabel("elevation α [°]")
    b.set_ylabel("coverage probability  P(CNR ≥ threshold) [%]")
    b.set_title("(b) LEO-600 DL coverage — TR 38.811 LOS prob. + SF + clutter (Monte Carlo)", loc="left", fontsize=10)
    b.grid(alpha=0.3)
    b.legend(fontsize=7)

    # (c) bir LEO geçişi boyunca kapsama – zaman (yerde sabit UE, tepe geçişi)
    h = float(h_leo)
    orbit = "LEO-600" if h < 900 else "LEO-1200"
    lam = footprint_rad(h, el_min)
    t_half = lam / np.sqrt(MU / (RE + h) ** 3)
    ts = np.linspace(-t_half, t_half, 121)
    el_t = pass_elevation(h, ts)
    for scn in LOS_PROB:
        mc = coverage_mc(orbit, band, scn, el_grid=el_t, n=20000, snr_min_db=snr_min_db, set_name=set_name, reuse=reuse)
        c.plot(ts / 60, 100 * mc["p_cnr"], color=_SCN[scn], lw=2, label=scn)
    for scn in LOS_PROB:
        g = coverage_mc("GEO", band, scn, el_grid=[45.0], n=20000, snr_min_db=snr_min_db, set_name=set_name, reuse=reuse)
        c.axhline(100 * g["p_cnr"][0], color=_SCN[scn], ls="--", lw=1)
    c2 = c.twinx()
    c2.plot(ts / 60, el_t, color="0.5", lw=1)
    c2.set_ylabel("elevation [°] (grey)", color="0.4")
    c.set_ylim(0, 102)
    c.set_xlabel(f"time from zenith [min]   ({orbit.split('-')[0]} {h:.0f} km, ε_min = {el_min:g}°)")
    c.set_ylabel("coverage probability [%]")
    c.set_title("(c) Coverage during one LEO pass (solid) vs GEO at 45° (dashed)", loc="left", fontsize=10)
    c.grid(alpha=0.3)
    c.legend(fontsize=7, loc="lower center")

    # (d) kapsama tablosu: hedef elevasyonda her yörünge × senaryo
    d.axis("off")
    rows, cells = [], []
    for orbit in ORBITS:
        el = TARGET_EL[(orbit_type(orbit), set_name)]
        lb = link_budget(orbit, band, "DL", None, set_name, reuse)
        row = [f"{el:g}°", f"{lb['cnr']:.1f}", f"{lb['cnir']:.1f}"]
        for scn in LOS_PROB:
            mc = coverage_mc(orbit, band, scn, el_grid=[el], snr_min_db=snr_min_db, set_name=set_name, reuse=reuse)
            row.append(f"{100 * mc['p_cnr'][0]:.0f}%")
        row.append(f"{beams_per_footprint(orbit, band, set_name, el_min):,.0f}")
        rows.append(orbit)
        cells.append(row)
    tb = d.table(cellText=cells, rowLabels=rows,
                 colLabels=["target α", "CNR\n[dB]", "CNIR\n[dB]", "dense\nurban", "urban", "suburban\n/rural",
                            "beams per\nfootprint"],
                 bbox=[0.12, 0.45, 0.88, 0.45], cellLoc="center")
    tb.auto_set_font_size(False)
    tb.set_fontsize(9)
    d.text(0, 0.98, f"(d) DL coverage at TR 38.821 target elevation ({set_name}, {band}-band, reuse {reuse})",
           fontsize=10, va="top", transform=d.transAxes)
    d.text(0, 0.36,
           f"• CNR, CNIR: TR 38.821 link budget (3 dB shadow margin for handheld, LOS)\n"
           f"• coverage %: TR 38.811 Monte Carlo, P(CNR ≥ {snr_min_db:g} dB)\n"
           f"• beams per footprint: visibility area (ε ≥ {el_min:g}°) / nadir beam area\n"
           f"  (beam diameter from TR 38.821 Table 6.1.1.1-1/2)\n"
           f"• threshold {snr_min_db:g} dB is NOT from the TR documents (≈ lowest NR MCS)",
           fontsize=8.5, va="top", transform=d.transAxes, color="0.3")
    fig.suptitle("Radio coverage:  CNR = EIRP + G/T − k − PL_FS − PL_A − PL_SM − PL_SL − 10log10(B)     "
                 "PL_b = FSPL + SF + CL", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def plot_capacity(band="S", set_name="Set-1", n_ue=10, el_min=10.0, h_leo=600, dpi=80):
    """Kapasite (Shannon sınırı, TR 38.821 CNIR ile), 2×2 figür + 38.821 SLS sonuçlarıyla karşılaştırma."""
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 2, figsize=(15, 10), dpi=dpi)
    (a, b), (c, d) = axs
    els = np.arange(10, 90.1, 1)

    # (a) spektral verim – elevasyon, yeniden kullanım 1 ve 3
    for orbit in ORBITS:
        for reuse, ls in ((1, "-"), (3, "--")):
            se = [link_budget(orbit, band, "DL", e, set_name, reuse)["se"] for e in els]
            a.plot(els, se, ls, color=_COL[orbit], lw=2 if reuse == 1 else 1.3, label=f"{orbit}, reuse {reuse}")
    a.set_xlabel("elevation α [°]")
    a.set_ylabel("spectral efficiency log2(1 + CNIR) [b/s/Hz]")
    a.set_title(f"(a) DL spectral efficiency — CNIR from TR 38.821 (6.1.3.1-1), {band}-band", loc="left", fontsize=10)
    a.grid(alpha=0.3)
    a.legend(fontsize=7, ncol=2)

    # (b) ışın kapasitesi ve UE başına kapasite – elevasyon
    for orbit in ORBITS:
        for reuse, ls in ((1, "-"), (3, "--")):
            cap = np.array([link_budget(orbit, band, "DL", e, set_name, reuse)["capacity_bps"] for e in els]) / 1e6
            b.plot(els, cap, ls, color=_COL[orbit], lw=2 if reuse == 1 else 1.3, label=f"{orbit}, reuse {reuse}")
    b.set_xlabel("elevation α [°]")
    b.set_ylabel("beam capacity (Shannon) [Mbit/s]")
    b2 = b.secondary_yaxis("right", functions=(lambda x: x / n_ue, lambda x: x * n_ue))
    b2.set_ylabel(f"per UE with {n_ue} UEs/beam [Mbit/s]")
    b.set_title(f"(b) DL beam capacity  C = B·log2(1+CNIR),  B = {BANDS[band]['sys_bw_mhz']:g} MHz / reuse",
                loc="left", fontsize=10)
    b.grid(alpha=0.3)
    b.legend(fontsize=7, ncol=2)

    # (c) bir geçiş boyunca throughput – zaman (yerde sabit UE)
    h = float(h_leo)
    orbit = "LEO-600" if h < 900 else "LEO-1200"
    lam = footprint_rad(h, el_min)
    t_half = lam / np.sqrt(MU / (RE + h) ** 3)
    ts = np.linspace(-t_half, t_half, 201)
    el_t = pass_elevation(h, ts)
    for reuse, ls in ((1, "-"), (3, "--")):
        cap = np.array([link_budget(orbit, band, "DL", e, set_name, reuse, h_km=h)["capacity_bps"] for e in el_t]) / 1e6
        c.plot(ts / 60, cap / n_ue, ls, color=_COL[orbit], lw=2, label=f"{orbit} ({h:.0f} km), reuse {reuse}")
        cg = link_budget("GEO", band, "DL", 45.0, set_name, reuse)["capacity_bps"] / 1e6
        c.axhline(cg / n_ue, color=_COL["GEO"], ls=ls, lw=1.3, label=f"GEO at 45°, reuse {reuse}")
        c.text(ts[0] / 60, cg / n_ue, f" avg LEO pass: {np.mean(cap) / n_ue:.2f}", fontsize=7, va="bottom",
               color=_COL[orbit]) if reuse == 1 else None
    c.set_xlabel("time from zenith [min]")
    c.set_ylabel(f"per-UE DL throughput (Shannon, {n_ue} UEs/beam) [Mbit/s]")
    c.set_title("(c) Per-UE capacity during one LEO pass vs GEO", loc="left", fontsize=10)
    c.grid(alpha=0.3)
    c.legend(fontsize=7)

    # (d) 38.821 SLS sonuçlarıyla karşılaştırma (aynı vaka, hedef elevasyon)
    d.axis("off")
    cells, rows = [], []
    for case, (orbit, bnd, reuse, ru) in SLS_THROUGHPUT.items():
        lb = link_budget(orbit, bnd, "DL", None, "Set-1", reuse)
        per_ue = lb["capacity_bps"] / 1e6 / 10
        rows.append(f"SC{case}")
        cells.append([f"{orbit} {bnd}", f"{reuse}", f"{lb['cnir']:.1f}", f"{lb['se']:.2f}",
                      f"{lb['capacity_bps'] / 1e6:.1f}", f"{per_ue:.2f}", f"{ru['~50%'][1]:.2f}",
                      f"{per_ue / ru['~50%'][1]:.1f}×"])
    tb = d.table(cellText=cells, rowLabels=rows,
                 colLabels=["orbit / band", "reuse", "CNIR\n[dB]", "SE\n[b/s/Hz]", "beam C\n[Mbit/s]",
                            "C per UE\n(10 UEs)", "3GPP SLS\nmedian", "Shannon /\nSLS"],
                 bbox=[0.08, 0.38, 0.92, 0.55], cellLoc="center")
    tb.auto_set_font_size(False)
    tb.set_fontsize(8.5)
    d.text(0, 0.99, "(d) Shannon bound vs TR 38.821 Table 6.1.1.3-1 SLS (Set-1, DL, 10 UEs/cell, RU ~50%)",
           fontsize=10, va="top", transform=d.transAxes)
    ratios = [float(r[-1][:-1]) for r in cells]
    d.text(0, 0.30,
           "• Shannon is an upper bound: no protocol overhead (RS, CP, control), no fast fading,\n"
           "  ideal link adaptation, all 10 UEs share the beam equally.\n"
           "• SLS adds fading, LOS/NLOS (rural), scheduling (PF), HARQ, finite MCS table.\n"
           f"• Shannon / SLS = {min(ratios):.1f}–{max(ratios):.1f}×: same order of magnitude and same ranking\n"
           "  (Ka ≫ S, reuse 3 ≈ reuse 1 per UE) → link budget is consistent with the 3GPP SLS.\n"
           "• The Shannon formula itself is NOT in TR 38.811 / 38.821.",
           fontsize=8.5, va="top", transform=d.transAxes, color="0.3")
    fig.suptitle("Capacity:  CNIR = 1 / (1/CNR + 1/CIR)   (TR 38.821)      C = B·log2(1 + CNIR)   (Shannon)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


if __name__ == "__main__":
    validate_38821()
    print()
    print_link_budget(link_budget("LEO-600", "S", "DL"))
