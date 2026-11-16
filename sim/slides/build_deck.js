// NTN simülasyon kareleri → PPTX (kullanıcının "Diyagram_NTN_FINAL1" stilinde)
const path = require("path");
const fs = require("fs");
const PptxGenJS = require("pptxgenjs");
const { applyTheme } = require(process.argv[3]);

const DIR = __dirname;
const FR = path.join(DIR, "frames");
const frames = JSON.parse(fs.readFileSync(path.join(FR, "frames.json"), "utf8"));
const OUT = process.argv[2];

const THEME = {
  name: "NTN Paper",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "14140F", lt1: "FFFFFF", dk2: "6B6B66", lt2: "F4F3EF",
    accent1: "8A6A2F", accent2: "3D6B45", accent3: "A3372A",
    accent4: "2F6FB5", accent5: "7B55B0", accent6: "1F8A68",
    hlink: "2F6FB5", folHlink: "7B55B0",
  },
};
const HEX = { ink: "14140F", muted: "6B6B66", line: "DCDCD6", paper: "F4F3EF", white: "FFFFFF",
              gold: "8A6A2F", goldBg: "F3EAD7", green: "3D6B45", red: "A3372A" };
const UE_COL = ["1F8A68", "2F6FB5", "D0712B", "7B55B0"];   // simülasyondaki UE renkleri
const UE_ID = ["UAV", "A/C", "HST", "SHIP"];
const MONO = "Courier New";

const pres = new PptxGenJS();
pres.defineLayout({ name: "NTN_WIDE", width: 20, height: 11.25 });
pres.layout = "NTN_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "NTN Channel Detail — LEO and GEO access link";
pres.author = "Senanur Demirci";
const C = pres.SchemeColor;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "FRAME",
  background: { color: HEX.paper },
  objects: [
    { line: { x: 0.37, y: 1.22, w: 19.26, h: 0, line: { color: HEX.line, width: 0.75 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.37, y: 0.28, w: 11.8, h: 0.6,
        fontSize: 26, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.37, y: 0.82, w: 11.9, h: 0.36,
        fontSize: 14, fontFace: MONO, color: C.text2, align: "left", valign: "middle", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "TEXT",
  background: { color: HEX.paper },
  objects: [
    { line: { x: 0.37, y: 1.22, w: 19.26, h: 0, line: { color: HEX.line, width: 0.75 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.37, y: 0.28, w: 19.2, h: 0.6,
        fontSize: 26, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.37, y: 0.82, w: 19.2, h: 0.36,
        fontSize: 14, fontFace: MONO, color: C.text2, align: "left", valign: "middle", margin: 0 }, text: "" } },
  ],
});

// ------------------------------------------------------------------ helpers
const fmtT = (s) => { s = Math.round(s); return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`; };

function card(slide, x, y, w, h, title, name) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: HEX.white }, line: { color: HEX.line, width: 0.75 },
    objectName: name + " card" });
  slide.addText(title, { x: x + 0.18, y: y + 0.08, w: w - 0.36, h: 0.36, fontSize: 14, color: C.text2, charSpacing: 2,
    margin: 0, valign: "middle", isTextBox: true, objectName: name + " title" });
  slide.addShape(pres.shapes.LINE, { x, y: y + 0.5, w, h: 0, line: { color: HEX.line, width: 0.75 }, objectName: name + " rule" });
}

function statusBox(slide, f) {
  const k = f.kind;
  const style = {
    idle:     { fill: HEX.white,  line: HEX.line,  color: HEX.muted, bold: false },
    active:   { fill: HEX.white,  line: HEX.gold,  color: HEX.gold,  bold: false },
    imminent: { fill: HEX.white,  line: HEX.red,   color: HEX.red,   bold: true },
    executed: { fill: HEX.goldBg, line: HEX.gold,  color: HEX.gold,  bold: true },
  }[k];
  slide.addText(f.status, { x: 16.03, y: 0.38, w: 3.6, h: 0.62, fontSize: 13, fontFace: "Arial", bold: style.bold,
    color: style.color, fill: { color: style.fill }, line: { color: style.line, width: 1 }, align: "center",
    valign: "middle", margin: 0.05, isTextBox: true, objectName: "HO status" });
}

function header(slide, f, title, subtitle) {
  slide.addText(title, { placeholder: "title" });
  slide.addText(subtitle, { placeholder: "subtitle" });
  slide.addText(`t = ${f.t} s`, { x: 12.35, y: 0.33, w: 2.25, h: 0.72, fontSize: 28, fontFace: MONO, color: HEX.ink,
    align: "right", valign: "middle", margin: 0, isTextBox: true, objectName: "time" });
  slide.addText(f.layer === "LEO" ? `frame ${f.idx}/${f.n}` : "snapshot", { x: 14.7, y: 0.5, w: 1.28, h: 0.45,
    fontSize: 12, fontFace: MONO, color: HEX.muted, align: "left", valign: "bottom", margin: 0, isTextBox: true, objectName: "frame no" });
  statusBox(slide, f);
}

function ueTable(slide, f, x, y, w) {
  const keys = ["v", "h", "sat", "α", "d", "f_d", "df_d/dt", "PL", "RTT", "CNR DL", "SE DL", "link"];
  const labelW = 1.18, colW = (w - labelW) / 4;
  const cell = (text, opt = {}) => ({ text, options: Object.assign({ fontFace: MONO, fontSize: 12.5, color: HEX.ink,
    border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: HEX.line }, { type: "none" }], margin: [0, 0.06, 0, 0.06],
    valign: "middle" }, opt) });
  const rows = [[cell("UE", { color: HEX.muted, fontFace: "Arial" }),
                 ...UE_ID.map((id, i) => cell(id, { bold: true, color: UE_COL[i] }))]];
  for (const k of keys) {
    rows.push([cell(k, { color: HEX.muted }),
      ...f.rows[k].map((v) => cell(v, k === "link" ? { color: v === "LOS" ? HEX.green : HEX.red } : {}))]);
  }
  slide.addTable(rows, { x, y, w, colW: [labelW, colW, colW, colW, colW], rowH: 0.305, objectName: "per-UE link values" });
}

function constellationText(f) {
  const out = [];
  for (const [name, el, st] of f.cons) {
    const color = st === "serving" ? HEX.gold : st === "rising" ? HEX.green : st === "setting" ? HEX.red : HEX.muted;
    out.push({ text: `${name.padEnd(6, " ")} · α_ref = ${el.toFixed(1).padStart(5, " ")}° · ${st}`,
      options: { color, bold: st === "serving", breakLine: true } });
  }
  out[out.length - 1].options.breakLine = false;
  return out;
}

function frameSlide(f) {
  const isLeo = f.layer === "LEO";
  const slide = pres.addSlide({ masterName: "FRAME", sectionTitle: isLeo ? "LEO access link (frames)" : "GEO access link" });
  header(slide, f, isLeo ? "NTN Channel Detail — LEO access link" : "NTN Channel Detail — GEO access link",
    isLeo ? "3GPP TR 38.811/38.821 · f_c = 2 GHz · h = 600 km · v_sat = 7.56 km/s · 12 sats/plane · ε_min = 10°"
          : "3GPP TR 38.811/38.821 · f_c = 2 GHz · h = 35 786 km · Earth-fixed · GEO at +35° · ε_min = 10°");
  // simülasyon görüntüsü
  slide.addImage({ path: path.join(FR, f.image), x: 0.37, y: 1.37, w: 12.3, h: 8.45, objectName: "simulation view",
    altText: `${f.layer} simulation at t = ${f.t} s: side view, orbit view and Doppler history` });
  slide.addShape(pres.shapes.RECTANGLE, { x: 0.37, y: 1.37, w: 12.3, h: 8.45, fill: { type: "none" },
    line: { color: HEX.line, width: 0.75 }, objectName: "image frame" });
  const servTxt = isLeo ? `serving: ${f.serving.join(", ")}` : "GEO serving all UEs";
  slide.addText(`${servTxt} · PL ${f.rows.PL.join(" / ")} (UAV / A/C / HST / SHIP)`,
    { x: 0.37, y: 9.92, w: 7.3, h: 0.85, fontSize: 12, fontFace: MONO, color: HEX.muted, valign: "top", margin: 0,
      isTextBox: true, objectName: "caption left" });
  slide.addText("Altitude axis logarithmic · angles, ranges & Doppler from true geometry · ground strip = Doppler seen by a fixed ground terminal",
    { x: 7.9, y: 9.92, w: 4.77, h: 0.85, fontSize: 12, color: HEX.muted, valign: "top", margin: 0,
      isTextBox: true, objectName: "caption right" });
  // sağ panel
  const X = 12.95, W = 6.68;
  card(slide, X, 1.37, W, 4.7, "PER-UE LINK VALUES", "values");
  ueTable(slide, f, X + 0.1, 1.95, W - 0.2);
  card(slide, X, 6.2, W, 1.62, isLeo ? "CONSTELLATION" : "SATELLITE", "constellation");
  slide.addText(constellationText(f), { x: X + 0.18, y: 6.76, w: W - 0.36, h: 1.02, fontSize: 12, fontFace: MONO,
    valign: "top", margin: 0, paraSpaceAfter: 2, isTextBox: true, objectName: "constellation list" });
  card(slide, X, 7.95, W, 1.87, "LINK STATE", "state");
  const lines = f.state.map((s, i) => {
    const isUe = isLeo && i < 4;
    return { text: s, options: { color: isUe ? UE_COL[i] : HEX.muted, fontFace: isUe ? MONO : "Arial", breakLine: true } };
  });
  if (f.ho_detail) lines.push({ text: "HO: " + f.ho_detail, options: { color: HEX.gold, bold: true, breakLine: true } });
  lines[lines.length - 1].options.breakLine = false;
  slide.addText(lines, { x: X + 0.18, y: 8.53, w: W - 0.36, h: 1.25, fontSize: 12, valign: "top", margin: 0,
    paraSpaceAfter: 1, isTextBox: true, objectName: "link state" });
  // konuşmacı notu
  let note;
  if (isLeo) {
    note = `t = ${f.t} s (${fmtT(f.t)}) · frame ${f.idx}/${f.n} · ${f.status}` + (f.ho_detail ? ` (${f.ho_detail})` : "") +
      `\nServing: ${f.serving.join(", ")}. ` + f.state.slice(0, 4).join(" · ") +
      `\nDoppler per UE: ${f.rows.f_d.join(" / ")} (UAV / A/C / HST / SHIP). RTT: ${f.rows.RTT.join(" / ")}.` +
      "\nStatus box (illustrative): PREP ACTIVE = a UE's serving satellite drops below 10° within 60 s; IMMINENT = within 10 s; EXECUTED = a handover happened since the previous frame.";
  } else {
    note = "GEO snapshot at t = 120 s. One satellite serves all four UEs, no handover. Doppler only from UE motion " +
      `(${f.rows.f_d.join(" / ")}), Doppler rate ≈ 0. RTT ≈ 243–252 ms, path loss ≈ 190 dB, DL CNR ≈ 1 dB even with the 22 m 3GPP Set-1 antenna.`;
  }
  slide.addNotes(note);
}

// ------------------------------------------------------------------ slides
pres.addSection({ title: "LEO access link (frames)" });
frames.filter((f) => f.layer === "LEO").forEach(frameSlide);
pres.addSection({ title: "GEO access link" });
frames.filter((f) => f.layer === "GEO").forEach(frameSlide);

// --- karşılaştırma
pres.addSection({ title: "LEO vs GEO" });
{
  const s = pres.addSlide({ masterName: "TEXT", sectionTitle: "LEO vs GEO" });
  s.addText("LEO vs GEO — What the Simulation Shows", { placeholder: "title" });
  s.addText("Simulation (f_c = 2 GHz, handheld UE) + 3GPP TR 38.821 reference values", { placeholder: "subtitle" });
  const H = (t, o = {}) => ({ text: t, options: Object.assign({ bold: true, fontSize: 15, color: HEX.ink, fill: { color: "EDECE7" },
    border: [{ type: "none" }, { type: "none" }, { pt: 1, color: HEX.line }, { type: "none" }], valign: "middle", margin: [0, 0.1, 0, 0.1] }, o) });
  const R = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 13.5, fontFace: MONO, color: HEX.ink,
    border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: HEX.line }, { type: "none" }], valign: "middle", margin: [0, 0.1, 0, 0.1] }, o) });
  const L = (t) => R(t, { fontFace: "Arial", color: HEX.muted });
  const bad = { color: HEX.red, bold: true }, good = { color: HEX.green, bold: true };
  const rows = [
    [H(""), H("LEO-600", { color: HEX.gold }), H("GEO", { color: "2F6FB5" }), H("Source", { color: HEX.muted })],
    [L("Altitude"), R("600 km"), R("35 786 km"), L("TR 38.821 Tab. 4.2-2")],
    [L("Max UE–satellite distance (10°)"), R("1 932 km"), R("40 581 km"), L("TR 38.821 Tab. 4.2-2 = sim")],
    [L("RTT, service link (regenerative)"), R("4.0 – 12.9 ms", good), R("239 – 271 ms", bad), L("2d/c · sim = 3GPP")],
    [L("RTT, transparent (with feeder link)"), R("25.77 ms"), R("541.46 ms", bad), L("TR 38.821 Tab. 4.2-2")],
    [L("Max Doppler shift (2 GHz)"), R("±46 kHz (24 ppm)", bad), R("≤ 1.7 kHz (UE motion only)", good), L("sim · TR 38.821")],
    [L("Max Doppler rate (2 GHz)"), R("≈ 580 Hz/s", bad), R("≈ 0", good), L("sim (3GPP: 0.27 ppm/s)")],
    [L("Free-space path loss (2 GHz)"), R("154 – 164 dB"), R("≈ 190 dB", bad), L("TR 38.811 (6.6-2)")],
    [L("DL CNR, handheld (Set-1)"), R("6.6 dB (30°)"), R("0.0 dB (12.5°)"), L("TR 38.821 Tab. 6.1.3.3-1")],
    [L("UL CNR, handheld (Set-1)"), R("2.8 dB"), R("−10.9 dB", bad), L("TR 38.821 Tab. 6.1.3.3-1")],
    [L("Satellite change (handover)"), R("every ≈ 8 min (T/N)", bad), R("none", good), L("sim: 96.5 min / 12")],
    [L("Coverage of one satellite (10°)"), R("r = 1 761 km · 1.9 %"), R("r = 7 944 km · 34 %", good), L("λ = acos(R_E cos ε / r) − ε")],
    [L("Satellites for Istanbul, 24/7 (10°)"), R("≈ 38 (Walker 50°)", bad), R("1", good), L("own Walker search")],
  ];
  s.addTable(rows, { x: 0.37, y: 1.5, w: 13.4, colW: [4.3, 3.2, 3.2, 2.7], rowH: 0.56, objectName: "comparison table" });
  // çıkarımlar
  const tk = (y, title, color, items, name) => {
    s.addShape(pres.shapes.RECTANGLE, { x: 14.15, y, w: 5.48, h: 3.55, fill: { color: HEX.white }, line: { color: HEX.line, width: 0.75 }, objectName: name + " card" });
    s.addText(title, { x: 14.4, y: y + 0.18, w: 5.0, h: 0.5, fontSize: 20, bold: true, color, margin: 0, isTextBox: true, objectName: name + " title" });
    s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })),
      { x: 14.4, y: y + 0.8, w: 5.0, h: 2.6, fontSize: 15, color: HEX.ink, valign: "top", margin: 0, paraSpaceAfter: 8,
        isTextBox: true, objectName: name + " list" });
  };
  tk(1.5, "LEO: problems from motion", HEX.gold,
     ["Large, fast-changing Doppler → UE pre-compensation (GNSS + ephemeris)",
      "Delay changes ≈ 23 µs/s → continuous timing advance",
      "Handover every few minutes → conditional handover (T1, D1)"], "LEO takeaway");
  tk(5.2, "GEO: problems from distance", "2F6FB5",
     ["RTT ≈ 250–540 ms → more HARQ processes, K_offset",
      "≈ 190 dB path loss → weak handheld uplink (−10.9 dB)",
      "No Doppler, no handover, one satellite for a whole region"], "GEO takeaway");
  s.addText("LEO's problems come from motion, GEO's problems come from distance.",
    { x: 0.37, y: 9.25, w: 19.26, h: 0.6, fontSize: 20, italic: true, color: HEX.ink, align: "center", valign: "middle",
      margin: 0, isTextBox: true, objectName: "key message" });
  s.addText("Simulation: 2-D, single orbital plane, no Earth rotation, free-space loss only. Istanbul count: own Walker search (inclination 50–55°, ≤ 40 planes), coverage only (no capacity or handover margin).",
    { x: 0.37, y: 10.05, w: 19.26, h: 0.6, fontSize: 12, color: HEX.muted, valign: "top", margin: 0, isTextBox: true, objectName: "caveats" });
  s.addNotes("Key message: LEO's problems come from motion (Doppler, changing delay, frequent handover); GEO's come from distance (delay, path loss, weak uplink). Distance and RTT match TR 38.821 Table 4.2-2 exactly; Doppler within 4–8% (no Earth rotation in the model). The Istanbul satellite counts are coverage-only lower bounds from my own search.");
}

// --- formüller ve kaynaklar
pres.addSection({ title: "Formulas & References" });
{
  const s = pres.addSlide({ masterName: "TEXT", sectionTitle: "Formulas & References" });
  s.addText("NTN Channel Detail — Formulas & References", { placeholder: "title" });
  s.addText("Every value on the frame slides is computed with these equations", { placeholder: "subtitle" });
  const items = [
    ["Slant range  d  (→ d)", "d = √(R_E²·sin²α + h² + 2·h·R_E) − R_E·sin α", "TR 38.811 (6.6-3)"],
    ["Free-space path loss  (→ PL)", "FSPL = 32.45 + 20·log₁₀(f_c[GHz]) + 20·log₁₀(d[m])", "TR 38.811 (6.6-2)"],
    ["Round-trip time  (→ RTT)", "RTT = 2·d / c        (service link only)", "basic physics; TR 38.821 Tab. 4.2-2"],
    ["Doppler shift  (→ f_d)", "f_d = −f_c · ṙ / c,   ṙ = (Δp·Δv) / d", "relative velocity along line of sight"],
    ["Carrier-to-noise ratio  (→ CNR DL)", "CNR = EIRP + G/T − k − PL_FS − PL_A − PL_SM − PL_SL − 10·log₁₀(B)", "TR 38.821 (6.1.3.1-2)"],
    ["Receiver figure of merit", "G/T = G_a − NF − 10·log₁₀(T₀ + (T_a − T₀)·10^(−0.1·NF))", "TR 38.821 (6.1.3.1-3)"],
    ["Noise + interference  (→ SE DL)", "CNIR = 1 / (1/CNR + 1/CIR),   SE = log₂(1 + CNIR)", "TR 38.821 (6.1.3.1-1); Shannon"],
    ["Satellite coverage (footprint)", "λ = arccos(R_E·cos ε / r) − ε,   radius = R_E·λ", "geometry of (6.6-3)"],
    ["Orbital speed / handover period", "ω = √(μ / r³),   v = r·ω,   t_HO = T / N", "Kepler; sim"],
  ];
  const H = (t) => ({ text: t, options: { bold: true, fontSize: 14, color: HEX.gold, valign: "middle", margin: [0, 0.08, 0, 0.08],
    border: [{ type: "none" }, { type: "none" }, { pt: 1, color: HEX.line }, { type: "none" }] } });
  const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 15, color: HEX.ink, valign: "middle", margin: [0, 0.08, 0, 0.08],
    border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: HEX.line }, { type: "none" }] }, o) });
  const rows = [[H("QUANTITY  (→ COLUMN)"), H("FORMULA"), H("SOURCE")],
    ...items.map(([a, b, c]) => [cell(a, { bold: true }), cell(b, { fontFace: MONO, fontSize: 14.5 }), cell(c, { color: HEX.muted, fontSize: 14 })])];
  s.addTable(rows, { x: 0.37, y: 1.5, w: 13.6, colW: [3.6, 6.9, 3.1], rowH: 0.82, objectName: "formula table" });
  s.addShape(pres.shapes.RECTANGLE, { x: 14.35, y: 1.5, w: 5.28, h: 8.4, fill: { color: HEX.white }, line: { color: HEX.line, width: 0.75 }, objectName: "references card" });
  s.addText("REFERENCES", { x: 14.6, y: 1.65, w: 4.8, h: 0.45, fontSize: 14, color: HEX.gold, bold: true, charSpacing: 2, margin: 0, isTextBox: true, objectName: "references title" });
  const refs = [
    ["[1] 3GPP TR 38.811 V15.4.0", "Study on NR to support non-terrestrial networks. §6.6 path loss: Eq. 6.6-2, 6.6-3, 6.6-8; Tab. 6.6.1-1 LOS prob.; Tab. 6.6.2-1/2/3 SF & clutter; Tab. 6.6.6.2.1-1 scintillation"],
    ["[2] 3GPP TR 38.821 V16.2.0", "Solutions for NR to support NTN. Tab. 4.2-2 reference scenarios; Tab. 6.1.1.1-1/2/3 satellite & UE parameters; §6.1.3 link budget (Eq. 6.1.3.1-1/2/3); Tab. 6.1.3.3-1 results (60/60 CNR values reproduced within 0.06 dB)"],
    ["Simulation", "Python (numpy, matplotlib), Colab notebook leo_geo_doppler_colab. 2-D single orbital plane, circular orbits, Earth-fixed frame, free-space loss + 3GPP link-budget margins"],
  ];
  const t = [];
  refs.forEach(([a, b], i) => {
    t.push({ text: a, options: { bold: true, fontSize: 17, color: HEX.ink, breakLine: true } });
    t.push({ text: b, options: { fontSize: 15, color: HEX.muted, breakLine: i < refs.length - 1, paraSpaceAfter: 18 } });
  });
  s.addText(t, { x: 14.6, y: 2.25, w: 4.8, h: 7.4, valign: "top", margin: 0, isTextBox: true, objectName: "references list" });
  s.addNotes("All frame values come from these equations. Sources: 3GPP TR 38.811 V15.4.0 and TR 38.821 V16.2.0. The link budget code reproduces all 60 CNR values of TR 38.821 Table 6.1.3.3-1 within 0.06 dB. The Shannon formula (SE) is not in the TR documents; it is an upper bound.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
