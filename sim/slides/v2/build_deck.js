// LEO & GEO NTN — simulation study deck (new "deep space" style)
// node build_deck.js <out.pptx> <apply_theme.js>
const path = require("path");
const fs = require("fs");
const PptxGenJS = require("pptxgenjs");
const { applyTheme } = require(process.argv[3]);

const A = path.join(__dirname, "assets");
const D = JSON.parse(fs.readFileSync(path.join(A, "data.json"), "utf8"));
const OUT = process.argv[2];

const THEME = {
  name: "NTN Deep Space",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B1D33", lt1: "FFFFFF", dk2: "5B6B7F", lt2: "C8D3DF",
    accent1: "0FA3B1", accent2: "F2A541", accent3: "E4572E",
    accent4: "3A7BD5", accent5: "7B5EA7", accent6: "3AAF85",
    hlink: "3A7BD5", folHlink: "7B5EA7",
  },
};
const X = { navy: "0B1D33", navy2: "15304F", navy3: "1E3A5F", white: "FFFFFF", mist: "C8D3DF", slate: "5B6B7F",
            line: "D5DDE6", soft: "F2F5F9", teal: "0FA3B1", amber: "F2A541", coral: "E4572E", green: "3AAF85",
            blue: "3A7BD5", violet: "7B5EA7" };
const UEC = D.ue.map((u) => u.color);

const pres = new PptxGenJS();
pres.defineLayout({ name: "WIDE20", width: 20, height: 11.25 });
pres.layout = "WIDE20";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "LEO and GEO Non-Terrestrial Networks — Simulation Study";
pres.author = "Senanur Demirci";
const C = pres.SchemeColor;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "COVER", background: { color: X.navy },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 1.2, y: 2.6, w: 17, h: 0.6, fontSize: 18, bold: true,
        color: C.accent1, charSpacing: 4, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 1.2, y: 3.3, w: 11.5, h: 2.6, fontSize: 56, color: C.background1,
        valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 1.2, y: 6.2, w: 11.5, h: 1.6, fontSize: 22, align: "left", color: C.background2,
        valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: X.navy },
  objects: [
    { placeholder: { options: { name: "num", type: "body", x: 1.2, y: 2.4, w: 5, h: 2.2, fontSize: 130, bold: true,
        color: C.accent1, margin: 0, valign: "bottom", fontFace: "Cambria" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 1.2, y: 4.85, w: 17, h: 1.2, fontSize: 48, color: C.background1,
        margin: 0, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 1.2, y: 6.25, w: 15.5, h: 2.0, fontSize: 22, color: C.background2,
        margin: 0, valign: "top", align: "left" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: X.navy },
  slideNumber: { x: 19.0, y: 10.7, w: 0.6, h: 0.35, fontSize: 11, color: X.mist, align: "right" },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.5, y: 0.32, w: 14, h: 0.36, fontSize: 13, bold: true,
        color: C.accent1, charSpacing: 3, margin: 0, valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.68, w: 14.6, h: 0.75, fontSize: 32,
        color: C.background1, margin: 0, valign: "middle", align: "left" }, text: "" } },
  ],
});

// ------------------------------------------------------------------ helpers
function card(s, x, y, w, h, title, name, fill = X.white) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { type: "none" },
    objectName: name + " card" });
  if (title) {
    s.addText(title, { x: x + 0.3, y: y + 0.2, w: w - 0.6, h: 0.42, fontSize: 15, bold: true, color: C.text1, margin: 0,
      valign: "middle", isTextBox: true, objectName: name + " title" });
  }
}
function img(s, file, x, y, w, name, alt) {
  const p = path.join(A, file);
  const sz = require("child_process").execSync(`python3 -c "from PIL import Image;im=Image.open('${p}');print(im.size[0],im.size[1])"`).toString().trim().split(" ").map(Number);
  const h = w * sz[1] / sz[0];
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x - 0.08, y: y - 0.08, w: w + 0.16, h: h + 0.16, rectRadius: 0.08,
    fill: { color: X.white }, line: { type: "none" }, objectName: name + " frame" });
  s.addImage({ path: p, x, y, w, h, objectName: name, altText: alt });
  return h;
}
function content(kicker, title, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(kicker, { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  return s;
}
const T = (t, o = {}) => ({ text: String(t), options: Object.assign({ fontSize: 13, color: X.navy, valign: "middle",
  margin: [0, 0.08, 0, 0.08], border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: X.line }, { type: "none" }] }, o) });
const TH = (t, o = {}) => T(t, Object.assign({ bold: true, fill: { color: X.soft } }, o));
function stat(s, x, y, w, h, big, label, color, name, bigSize = 40) {
  card(s, x, y, w, h, null, name);
  s.addText(big, { x: x + 0.3, y: y + 0.2, w: w - 0.6, h: h * 0.48, fontSize: bigSize, bold: true, color, margin: 0,
    valign: "middle", fontFace: "Cambria", isTextBox: true, objectName: name + " value" });
  s.addText(label, { x: x + 0.3, y: y + 0.2 + h * 0.48, w: w - 0.6, h: h * 0.52 - 0.35, fontSize: 14, color: X.navy, margin: 0,
    valign: "top", isTextBox: true, objectName: name + " label" });
}
function bullets(s, items, x, y, w, h, name, size = 16, color = X.navy) {
  s.addText(items.map((t, i) => (typeof t === "string" ? { text: t, options: { bullet: true, breakLine: i < items.length - 1 } }
    : { text: t.text, options: Object.assign({ bullet: true, breakLine: i < items.length - 1 }, t.options) })),
    { x, y, w, h, fontSize: size, color, valign: "top", margin: 0, paraSpaceAfter: 9, isTextBox: true, objectName: name });
}
const fmtT = (s) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.round(s % 60)).padStart(2, "0")}`;

// ------------------------------------------------------------------ 0. cover
{
  const s = pres.addSlide({ masterName: "COVER" });
  s.addText("NON-TERRESTRIAL NETWORKS · SIMULATION STUDY", { placeholder: "kicker" });
  s.addText("LEO and GEO Access Links: Doppler, Coverage and Antennas", { placeholder: "title" });
  s.addText("Python simulation built on 3GPP TR 38.811 and TR 38.821 · Senanur Demirci", { placeholder: "body" });
  // orbit motif: earth + LEO + GEO rings (to scale ratio LEO/GEO radius)
  const cx = 15.6, cy = 5.8;
  s.addShape(pres.shapes.OVAL, { x: cx - 3.6, y: cy - 3.6, w: 7.2, h: 7.2, fill: { type: "none" }, line: { color: X.navy3, width: 1.5, dashType: "dash" }, objectName: "GEO ring" });
  s.addShape(pres.shapes.OVAL, { x: cx - 0.65, y: cy - 0.65, w: 1.3, h: 1.3, fill: { color: X.navy3 }, line: { color: X.teal, width: 2 }, objectName: "LEO ring" });
  s.addShape(pres.shapes.OVAL, { x: cx - 0.54, y: cy - 0.54, w: 1.08, h: 1.08, fill: { color: X.blue }, line: { type: "none" }, objectName: "Earth" });
  s.addShape(pres.shapes.OVAL, { x: cx - 0.12, y: cy - 0.77, w: 0.24, h: 0.24, fill: { color: X.teal }, line: { type: "none" }, objectName: "LEO satellite" });
  s.addShape(pres.shapes.OVAL, { x: cx + 2.4, y: cy - 2.82, w: 0.3, h: 0.3, fill: { color: X.amber }, line: { type: "none" }, objectName: "GEO satellite" });
  s.addText("LEO 600 km", { x: cx + 0.5, y: cy - 1.25, w: 2.0, h: 0.4, fontSize: 14, color: X.teal, margin: 0, isTextBox: true, objectName: "LEO label" });
  s.addText("GEO 35 786 km", { x: cx + 2.8, y: cy - 3.25, w: 3.2, h: 0.4, fontSize: 14, color: X.amber, margin: 0, isTextBox: true, objectName: "GEO label" });
  s.addNotes("This talk uses my Python simulation (built on 3GPP TR 38.811 and TR 38.821) to show how LEO and GEO access links behave: link dynamics and Doppler, coverage, and how many antennas and beams a satellite needs to cover a region. Orbit sketch: the ring radii are to scale.");
}

// ------------------------------------------------------------------ 1. link dynamics
function section(num, title, body, secTitle) {
  pres.addSection({ title: secTitle });
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: secTitle });
  s.addText(num, { placeholder: "num" });
  s.addText(title, { placeholder: "title" });
  s.addText(body, { placeholder: "body" });
  return s;
}
section("01", "Link Dynamics", "Four moving users (UAV, aircraft, high-speed train, ship) served by a LEO plane at 600 km and by a GEO satellite. What changes from second to second?", "1 · Link dynamics")
  .addNotes("Section 1: what the radio link looks like over time for LEO and GEO. The frames step 60 s; the LEO part covers 8 minutes and contains four handovers.");

function timeline(s, f) {
  const x0 = 1.3, x1 = 18.7, y = 10.55, tmax = 480;
  const xp = (t) => x0 + (x1 - x0) * t / tmax;
  s.addText("t [s]", { x: 0.5, y: y - 0.2, w: 0.7, h: 0.4, fontSize: 12, color: X.mist, margin: 0, isTextBox: true, objectName: "timeline label" });
  s.addShape(pres.shapes.LINE, { x: x0, y, w: x1 - x0, h: 0, line: { color: X.navy3, width: 2.5 }, objectName: "timeline axis" });
  s.addShape(pres.shapes.LINE, { x: x0, y, w: xp(f.t) - x0, h: 0, line: { color: X.teal, width: 2.5 }, objectName: "timeline progress" });
  for (const ev of D.events) {
    s.addShape(pres.shapes.DIAMOND, { x: xp(ev[0]) - 0.11, y: y - 0.11, w: 0.22, h: 0.22, fill: { color: ev[0] <= f.t ? X.amber : X.navy3 },
      line: { color: X.amber, width: 1 }, objectName: "handover marker" });
    s.addText(`${ev[1]} → ${ev[3]}`, { x: xp(ev[0]) - 0.9, y: y - 0.52, w: 1.8, h: 0.3, fontSize: 11, color: ev[0] <= f.t ? X.amber : X.slate,
      align: "center", margin: 0, isTextBox: true, objectName: "handover label" });
  }
  for (let t = 0; t <= tmax; t += 60) {
    const cur = t === f.t, past = t < f.t;
    const r = cur ? 0.13 : 0.07;
    s.addShape(pres.shapes.OVAL, { x: xp(t) - r, y: y - r, w: 2 * r, h: 2 * r, fill: { color: cur ? X.white : past ? X.teal : X.navy },
      line: { color: cur ? X.teal : past ? X.teal : X.slate, width: cur ? 2.5 : 1 }, objectName: "frame dot" });
    s.addText(String(t), { x: xp(t) - 0.4, y: y + 0.14, w: 0.8, h: 0.28, fontSize: 11, color: cur ? X.white : X.mist, bold: cur,
      align: "center", margin: 0, isTextBox: true, objectName: "frame time" });
  }
}

function frameSlide(f) {
  const leo = f.layer === "LEO";
  const s = content(leo ? `01 · LINK DYNAMICS — LEO-600 · FRAME ${f.idx} OF ${f.n}` : "01 · LINK DYNAMICS — GEO",
    leo ? `LEO Access Link at t = ${f.t} s` : `GEO Access Link at t = ${f.t} s`, "1 · Link dynamics");
  // status pill
  const st = { idle: [X.navy3, X.mist], pending: [X.amber, X.navy], executed: [X.teal, X.white], none: [X.navy3, X.mist] }[f.kind];
  s.addText(f.status, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.3, x: 15.3, y: 0.55, w: 4.2, h: 0.68, fill: { color: st[0] },
    line: { type: "none" }, fontSize: 15, bold: true, color: st[1], align: "center", valign: "middle", margin: 0, objectName: "handover status" });
  // left: values
  card(s, 0.5, 1.7, 6.35, 5.05, "Per-UE link values", "values");
  const head = [T("", { fill: { color: X.soft } }), ...D.ue.map((u, i) => TH(`${u.id}\n${Math.abs(u.v)} km/h ${u.v < 0 ? "←" : "→"}`,
    { color: UEC[i], align: "center", fontSize: 12.5 }))];
  const rows = [head];
  for (const k of ["sat", "α", "d", "f_d", "df_d/dt", "RTT", "PL", "CNR DL"]) {
    rows.push([T(k, { color: X.slate, fontSize: 12.5 }), ...f.rows[k].map((v) => T(v, { align: "center", fontSize: 12.5,
      bold: k === "f_d", color: k === "sat" && v === "—" ? X.coral : X.navy }))]);
  }
  s.addTable(rows, { x: 0.65, y: 2.3, w: 6.05, colW: [1.13, 1.23, 1.23, 1.23, 1.23], rowH: [0.6, 0.43, 0.43, 0.43, 0.43, 0.43, 0.43, 0.43, 0.43],
    objectName: "per-UE values" });
  card(s, 0.5, 6.9, 6.35, 3.05, leo ? "Satellites & next handover" : "Satellite & link state", "state");
  const lines = [];
  for (const [name, el, stt] of f.cons) {
    const col = stt === "serving" ? X.teal : stt === "rising" ? X.green : stt === "setting" ? X.coral : X.slate;
    lines.push({ text: `${name}  ${el.toFixed(1)}°  ${stt}`, options: { color: col, bold: stt === "serving", breakLine: true } });
  }
  if (leo) {
    D.ue.forEach((u, i) => lines.push({ text: `${u.id}: ${f.rows.sat[i]} → HO in ${f.ho[i] ? fmtT(f.ho[i]) : ">30:00"}`,
      options: { color: UEC[i], breakLine: true } }));
  } else {
    lines.push({ text: "One satellite for all four UEs · no handover", options: { color: X.navy, breakLine: true } });
  }
  lines.push({ text: `Mean access RTT ${f.rtt} ms`, options: { color: X.slate, breakLine: false } });
  s.addText(lines, { x: 0.8, y: 7.42, w: 5.8, h: 2.45, fontSize: 13, valign: "top", margin: 0, paraSpaceAfter: 1, isTextBox: true,
    objectName: "link state" });
  // right: image
  img(s, f.image, 7.2, 1.7, 12.3, "simulation view", `${f.layer} simulation at t = ${f.t} s, side view`);
  if (leo) timeline(s, f);
  else s.addText("GEO is fixed in the sky: no Doppler from the satellite, no handover — but every link is ~37 000 km long.",
    { x: 0.5, y: 10.3, w: 18, h: 0.5, fontSize: 15, italic: true, color: X.mist, margin: 0, isTextBox: true, objectName: "GEO message" });
  const ev = f.events.length ? ` Handover since previous frame: ${f.events.map((e) => `${e[1]} ${e[2]}→${e[3]} at ${fmtT(e[0])}`).join("; ")}.` : "";
  s.addNotes(leo
    ? `t = ${f.t} s (${fmtT(f.t)}). ${f.status}.${ev} Serving: ${f.serving.join(", ")}. Doppler UAV/A-C/HST/SHIP: ${f.rows.f_d.join(" / ")}. RTT: ${f.rows.RTT.join(" / ")}. Next handover per UE: ${D.ue.map((u, i) => u.id + " " + (f.ho[i] ? fmtT(f.ho[i]) : ">30:00")).join(", ")}.`
    : `GEO at t = 120 s: one satellite serves all four UEs, no handover. Doppler only from UE motion (${f.rows.f_d.join(" / ")}). RTT about 243-252 ms, path loss about 190 dB, DL CNR about 1 dB even with the 22 m Set-1 antenna.`);
}
D.frames.forEach(frameSlide);

// Doppler over time
{
  const s = content("01 · LINK DYNAMICS — DOPPLER", "Doppler over Time: LEO versus GEO", "1 · Link dynamics");
  img(s, "doppler.png", 0.6, 1.75, 12.4, "doppler chart", "Doppler over 30 minutes: LEO S-curves between +46 and -46 kHz with handover jumps; GEO almost flat");
  stat(s, 13.45, 1.7, 6.05, 1.95, "±46 kHz", "LEO max Doppler (3GPP: 24 ppm) — 1.5–3× the NR subcarrier spacing", X.coral, "LEO doppler");
  stat(s, 13.45, 3.8, 6.05, 1.95, "≈ 580 Hz/s", "Doppler rate when the satellite is overhead", X.coral, "LEO rate");
  stat(s, 13.45, 5.9, 6.05, 1.95, "≈ 8 min", "one S-curve per pass; each jump is a handover", X.amber, "LEO pass");
  stat(s, 13.45, 8.0, 6.05, 1.95, "≤ 1.7 kHz", "GEO: only the UE's own motion, no handover", X.green, "GEO doppler");
  s.addText("The UE pre-compensates this Doppler with its GNSS position and the satellite ephemeris (3GPP Rel-17).",
    { x: 0.6, y: 10.4, w: 12.4, h: 0.5, fontSize: 15, italic: true, color: X.mist, margin: 0, isTextBox: true, objectName: "key message" });
  s.addNotes("Each LEO pass draws an S-curve: +46 kHz while the satellite rises, 0 overhead (where it changes fastest, about 580 Hz/s), -46 kHz while it sets. The dotted jump is a handover, about every 8 minutes per UE. On the same scale GEO is flat: only UE motion, at most 1.7 kHz.");
}

// ------------------------------------------------------------------ 2. coverage
section("02", "Coverage", "How much of the Earth can one satellite see, how many satellites keep a city covered, and what happens in a city full of buildings?", "2 · Coverage")
  .addNotes("Section 2: coverage. Geometric coverage first (what one satellite can see), then constellation size, coverage gaps and finally radio coverage in different environments.");
{
  const s = content("02 · COVERAGE — GEOMETRY", "How Much Can One Satellite See?", "2 · Coverage");
  img(s, "cov_triangle.png", 0.6, 1.8, 11.2, "coverage geometry", "Triangle Earth centre - UE at coverage edge - satellite, with angles epsilon, eta and lambda");
  img(s, "cov_scale.png", 13.35, 1.8, 5.1, "coverage to scale", "LEO and GEO coverage drawn to scale");
  card(s, 0.5, 6.65, 11.4, 3.4, "Coverage angle from the minimum elevation ε", "formula");
  s.addText([
    { text: "λ = arccos( R_E · cos ε / r ) − ε", options: { fontSize: 26, fontFace: "Cambria", bold: true, color: X.navy, breakLine: true } },
    { text: "radius on ground = R_E · λ      share of Earth = (1 − cos λ) / 2", options: { fontSize: 18, fontFace: "Cambria", color: X.navy, breakLine: true } },
    { text: "r = R_E + h · ε = minimum elevation (10° in TR 38.821 Tab. 4.2-2) · η = nadir angle", options: { fontSize: 14, color: X.slate } },
  ], { x: 0.8, y: 7.25, w: 10.8, h: 2.6, valign: "top", margin: 0, paraSpaceAfter: 10, isTextBox: true, objectName: "formula text" });
  stat(s, 12.3, 6.65, 3.5, 3.4, "1.9 %", "one LEO-600 sat\nradius 1 761 km\n(λ = 15.8°)", X.teal, "LEO share", 44);
  stat(s, 16.0, 6.65, 3.5, 3.4, "34 %", "one GEO sat\nradius 7 944 km\n(λ = 71.4°)", X.amber, "GEO share", 44);
  s.addNotes("The coverage angle follows from the triangle Earth centre - UE - satellite. At 10 degrees minimum elevation a LEO satellite at 600 km sees a circle of 1761 km radius, 1.9% of the Earth; a GEO satellite sees 34%, about 18 times more.");
}
{
  const s = content("02 · COVERAGE — ALTITUDE AND ELEVATION", "Higher Orbit, Bigger Footprint — Higher ε, Many More Satellites", "2 · Coverage");
  const al = D.altitude, labels = al.h.map(String);
  card(s, 0.5, 1.7, 9.35, 7.0, null, "radius chart");
  s.addChart(pres.charts.LINE, [
    { name: "ε = 0°", labels, values: al.radius["0"] }, { name: "ε = 10°", labels, values: al.radius["10"] }, { name: "ε = 30°", labels, values: al.radius["30"] }],
    { x: 0.7, y: 1.85, w: 8.95, h: 6.7, showTitle: true, title: "Footprint radius [km] vs LEO altitude [km]", titleFontSize: 16, titleColor: X.navy, titleFontFace: "+mn-lt",
      chartColors: [X.blue, X.teal, X.coral], lineSize: 3, lineDataSymbol: "none", showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: "+mn-lt",
      catAxisLabelColor: X.slate, valAxisLabelColor: X.slate, catAxisLabelFontSize: 12, valAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
      valGridLine: { color: "E3E8EE", size: 0.75 }, catGridLine: { style: "none" }, catAxisLabelFrequency: 2, objectName: "radius vs altitude" });
  card(s, 10.15, 1.7, 9.35, 7.0, null, "nmin chart");
  s.addChart(pres.charts.LINE, [{ name: "ε = 10°", labels, values: al.nmin["10"] }, { name: "ε = 30°", labels, values: al.nmin["30"] }],
    { x: 10.35, y: 1.85, w: 8.95, h: 6.7, showTitle: true, title: "Satellites per plane for continuous coverage  N > π / λ", titleFontSize: 16, titleColor: X.navy, titleFontFace: "+mn-lt",
      chartColors: [X.teal, X.coral], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 6, showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: "+mn-lt",
      catAxisLabelColor: X.slate, valAxisLabelColor: X.slate, catAxisLabelFontSize: 12, valAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
      valGridLine: { color: "E3E8EE", size: 0.75 }, catGridLine: { style: "none" }, catAxisLabelFrequency: 2, objectName: "Nmin vs altitude" });
  bullets(s, [
    { text: "At 600 km: raising ε from 10° to 30° (e.g. buildings in a city) shrinks the radius 1 761 → 853 km and doubles the satellites per plane 12 → 24", options: { color: X.white } },
    { text: `GEO radius for comparison: ${D.altitude.geo_radius["0"]} / ${D.altitude.geo_radius["10"]} / ${D.altitude.geo_radius["30"]} km at ε = 0° / 10° / 30°`, options: { color: X.mist } },
  ], 0.6, 8.95, 18.8, 1.5, "takeaways", 16);
  s.addNotes("Left: footprint radius grows with altitude and shrinks with minimum elevation. Right: satellites needed in one orbital plane for continuous coverage, N > pi / lambda. At 600 km, going from 10 to 30 degrees minimum elevation doubles the number from 12 to 24.");
}
{
  const s = content("02 · COVERAGE — CONSTELLATION SIZE", "How Many Satellites Keep Istanbul Covered 24/7?", "2 · Coverage");
  card(s, 0.5, 1.7, 9.6, 6.15, null, "istanbul chart");
  const cats = ["GEO", "MEO 8 062 km", "LEO 1 200 km", "LEO 600 km"];
  s.addChart(pres.charts.BAR, [{ name: "ε = 10°", labels: cats, values: [1, 5, 20, 38] }, { name: "ε = 30°", labels: cats, values: [1, 12, 51, 170] }],
    { x: 0.7, y: 1.85, w: 9.2, h: 5.85, barDir: "col", barGrouping: "clustered", showTitle: true, title: "Minimum satellites (Istanbul, 41.0° N, 24 h)",
      titleFontSize: 16, titleColor: X.navy, titleFontFace: "+mn-lt", chartColors: [X.teal, X.coral], showValue: true, dataLabelPosition: "outEnd",
      dataLabelFontSize: 14, dataLabelColor: X.navy, dataLabelFontFace: "+mn-lt", showLegend: true, legendPos: "b", legendFontSize: 13, legendFontFace: "+mn-lt",
      catAxisLabelColor: X.slate, valAxisLabelColor: X.slate, catAxisLabelFontSize: 13, valAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
      valGridLine: { color: "E3E8EE", size: 0.75 }, catGridLine: { style: "none" }, valAxisMaxVal: 190, objectName: "istanbul constellation chart" });
  card(s, 10.4, 1.7, 9.1, 6.15, "What the numbers say", "istanbul notes");
  bullets(s, [
    "Lower orbit → smaller footprint → more satellites: 1 GEO, 5 MEO, 20–38 LEO (ε = 10°)",
    "Minimum elevation dominates: LEO-600 needs 38 satellites at 10° but 170 at 30°",
    "A LEO constellation that covers Istanbul also covers every city at 41° latitude (Madrid, New York, Beijing): you cannot buy LEO coverage for one city",
    "For one country, GEO is the natural choice (one satellite) — at the price of ~250 ms RTT",
  ], 10.7, 2.5, 8.5, 5.3, "istanbul bullets", 18);
  s.addText("Method: Walker constellations searched against Istanbul (41.0° N, 29.0° E) with Earth rotation, 24 h at 90 s steps, verified over 3 days at 10 s. Inclinations 50°/53°/55°, ≤ 40 planes. Coverage only (≥ 1 satellite above ε) — no capacity or handover margin; circular orbits, no J2.",
    { x: 0.5, y: 8.05, w: 19, h: 0.9, fontSize: 13, color: X.mist, margin: 0, valign: "top", isTextBox: true, objectName: "method" });
  s.addNotes("I searched for the smallest Walker constellation that keeps at least one satellite above the minimum elevation over Istanbul for 24 hours, including Earth rotation. One GEO is enough; MEO needs 5 (12 at 30 degrees); LEO at 1200 km needs 20 (51), at 600 km 38 (170). These are coverage-only lower bounds within the searched space. Key insight: LEO cannot serve one city alone - the same constellation covers the whole latitude band.");
}
{
  const s = content("02 · COVERAGE — INCOMPLETE CONSTELLATION", "Too Few Satellites → Predictable Coverage Gaps", "2 · Coverage");
  img(s, "gaps_plot.png", 0.6, 1.75, 11.6, "coverage gap timelines", "Best elevation seen by a ground UE over 2 hours for 12, 10 and 8 satellites per plane; red bands are coverage gaps");
  const g = D.gaps;
  stat(s, 12.75, 1.7, 6.75, 1.85, `${g["12"].avail.toFixed(0)} %`, "N = 12 per plane: continuous (N ≥ N_min = 12)", X.green, "gap12", 36);
  stat(s, 12.75, 3.7, 6.75, 1.85, `${g["10"].avail.toFixed(0)} %`, `N = 10: gaps of ≈ ${g["10"].gap_s} s every ≈ 9.7 min`, X.amber, "gap10", 36);
  stat(s, 12.75, 5.7, 6.75, 1.85, `${g["8"].avail.toFixed(0)} %`, `N = 8: gaps of ≈ ${Math.round(g["8"].gap_s / 6) / 10} min every ≈ 12 min`, X.coral, "gap8", 36);
  card(s, 12.75, 7.7, 6.75, 2.6, "3GPP response (Rel-17/18)", "3gpp gaps");
  bullets(s, ["Network broadcasts the next satellite's ephemeris", "UE predicts the gap, skips cell search (saves battery)",
    "UE reports unavailability → core does not page it"], 13.05, 8.3, 6.2, 1.95, "3gpp gap bullets", 14);
  s.addNotes("With fewer satellites than N_min the ground user sees periodic gaps. Availability = N 2 lambda / 2 pi; gap length = (2 pi / N - 2 lambda) / omega; theory and simulation agree within a few seconds. Because orbits are known, gaps are predictable - this is exactly what the 3GPP discontinuous-coverage features use. Single-plane model: neighbouring planes could fill some gaps.");
}
{
  const s = content("02 · COVERAGE — RADIO COVERAGE", "Visible Is Not Enough: Coverage in Cities", "2 · Coverage");
  const envs = ["dense urban", "urban", "suburban/rural"], labs = ["Dense urban", "Urban", "Suburban / rural"];
  card(s, 0.5, 1.7, 11.3, 7.6, null, "radio chart");
  s.addChart(pres.charts.BAR, [
    { name: "LEO-600 (α = 30°)", labels: labs, values: envs.map((e) => D.radio["LEO-600"].cov[e]) },
    { name: "GEO (α = 12.5°)", labels: labs, values: envs.map((e) => D.radio.GEO.cov[e]) }],
    { x: 0.7, y: 1.85, w: 10.9, h: 7.3, barDir: "col", barGrouping: "clustered", showTitle: true, title: "Coverage probability P(CNR ≥ −6 dB) [%] — handheld, 2 GHz",
      titleFontSize: 16, titleColor: X.navy, titleFontFace: "+mn-lt", chartColors: [X.teal, X.amber], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 15,
      dataLabelColor: X.navy, dataLabelFontFace: "+mn-lt", showLegend: true, legendPos: "b", legendFontSize: 14, legendFontFace: "+mn-lt", valAxisMaxVal: 100, valAxisMinVal: 0,
      catAxisLabelColor: X.slate, valAxisLabelColor: X.slate, catAxisLabelFontSize: 14, valAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
      valGridLine: { color: "E3E8EE", size: 0.75 }, catGridLine: { style: "none" }, objectName: "radio coverage chart" });
  card(s, 12.1, 1.7, 7.4, 7.6, "Why cities are hard", "radio notes");
  bullets(s, [
    "TR 38.811 channel: line-of-sight probability, shadow fading and clutter loss per environment",
    "Behind a building the clutter loss is 18–34 dB → the link is lost",
    "So coverage ≈ probability of seeing the satellite (LOS): LEO 40 / 49 / 92 %, GEO 28 / 25 / 78 %",
    "Higher elevation = fewer buildings in the way → LEO overhead passes help in cities",
  ], 12.4, 2.5, 6.85, 6.7, "radio bullets", 19);
  s.addText("Monte Carlo with TR 38.811 Tab. 6.6.1-1 (LOS probability) and Tab. 6.6.2-1/2/3 (shadow fading, clutter loss); link budget TR 38.821 Set-1. Threshold −6 dB is my choice (≈ lowest NR MCS), not from the TRs.",
    { x: 0.5, y: 9.55, w: 19, h: 0.8, fontSize: 13, color: X.mist, margin: 0, valign: "top", isTextBox: true, objectName: "method" });
  s.addNotes("Geometric coverage says the satellite is above the horizon; radio coverage asks whether the signal is strong enough. With the 3GPP TR 38.811 channel model, a user behind a building loses 18 to 34 dB, so coverage is almost the line-of-sight probability: about 50% in cities for LEO at 30 degrees, 95% in rural areas; GEO at 12.5 degrees is worse in cities.");
}

// ------------------------------------------------------------------ 3. antennas & beams
section("03", "Antennas and Beams", "Why does a satellite carry hundreds or thousands of antenna elements, and how many beams does it need to cover a region?", "3 · Antennas & beams")
  .addNotes("Section 3: antennas and beams. First why satellites use many antennas, then the link between antenna size, beam size and element count, and finally how many beams are needed to cover Istanbul, Turkey or a satellite's whole footprint.");
{
  const s = content("03 · ANTENNAS — WHY SO MANY?", "Many Antennas, One Layer: Satellite MIMO = Beamforming", "3 · Antennas & beams");
  card(s, 0.5, 1.7, 11.0, 5.0, "The three functions of MIMO", "mimo table card");
  const ok = { color: X.green, bold: true, align: "center" }, no = { color: X.coral, bold: true, align: "center" };
  s.addTable([
    [TH("Function", { fontSize: 15 }), TH("What it does", { fontSize: 15 }), TH("Terrestrial 5G", { fontSize: 15, align: "center" }), TH("Single satellite", { fontSize: 15, align: "center" })],
    [T("Beamforming", { bold: true, fontSize: 15 }), T("Focuses energy in one direction → gain", { fontSize: 15 }), T("✓", Object.assign({ fontSize: 18 }, ok)), T("✓ main use", Object.assign({ fontSize: 15 }, ok))],
    [T("Spatial multiplexing (SU-MIMO)", { bold: true, fontSize: 15 }), T("Several data layers to one user", { fontSize: 15 }), T("✓", Object.assign({ fontSize: 18 }, ok)), T("✗ rank 1", Object.assign({ fontSize: 15 }, no))],
    [T("MU-MIMO", { bold: true, fontSize: 15 }), T("Different users at the same time and frequency", { fontSize: 15 }), T("✓", Object.assign({ fontSize: 18 }, ok)), T("✓ via multibeam", Object.assign({ fontSize: 15 }, ok))],
  ], { x: 0.8, y: 2.4, w: 10.4, colW: [3.1, 3.7, 1.6, 2.0], rowH: [0.6, 0.95, 0.95, 0.95], objectName: "mimo table" });
  card(s, 11.8, 1.7, 7.7, 5.0, "Why rank 1?", "rank card");
  bullets(s, ["Satellite 600–36 000 km away → one line-of-sight path", "Scattering happens only near the user → all paths reach the satellite from the same angle",
    "Channel H ≈ √β · a_r · a_tᴴ → rank 1 (\"keyhole channel\")", "3GPP: satellite = one circular aperture (TR 38.811 §6.4.1), 1 Tx in link-level studies (TR 38.821 Tab. 6.1.2-1)"],
    12.1, 2.4, 7.1, 4.2, "rank bullets", 17);
  card(s, 0.5, 6.95, 19.0, 3.3, "So the antenna elements are used for …", "uses card");
  const uses = [["Gain", "narrow, strong beams to overcome ~154–190 dB path loss"], ["Multibeam", "hundreds of beams at once, frequency reused across beams → capacity"],
    ["Steering (LEO)", "keep beams on the ground while the satellite moves at 7.6 km/s"], ["Receive gain", "better G/T for the weak handheld uplink"]];
  uses.forEach(([a, b], i) => {
    const x = 0.8 + i * 4.7;
    s.addShape(pres.shapes.OVAL, { x, y: 7.65, w: 0.6, h: 0.6, fill: { color: [X.teal, X.blue, X.amber, X.violet][i] }, line: { type: "none" }, objectName: "use icon" });
    s.addText(String(i + 1), { x, y: 7.65, w: 0.6, h: 0.6, fontSize: 18, bold: true, color: X.white, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "use number" });
    s.addText([{ text: a, options: { bold: true, fontSize: 20, breakLine: true } }, { text: b, options: { fontSize: 17, color: X.slate } }],
      { x: x + 0.8, y: 7.55, w: 3.7, h: 2.5, color: X.navy, valign: "top", margin: 0, isTextBox: true, objectName: "use text" });
  });
  s.addNotes("Terrestrial MIMO relies on rich scattering. A satellite link is line-of-sight dominated; even with scattering near the user, all paths arrive at the satellite from almost the same angle, so the channel is rank 1. That is how 3GPP models it too. The hundreds to thousands of antenna elements are used for beamforming gain, multibeam with frequency reuse, beam steering on LEO, and receive gain for the uplink.");
}
{
  const s = content("03 · ANTENNAS — SIZE, BEAM, ELEMENTS", "From Antenna Size to Beam Size to Element Count", "3 · Antennas & beams");
  const f = [["Beam width", "θ₃dB = 1.029 · λ / D"], ["Gain", "G = η · (π D / λ)²   (η ≈ 0.6)"], ["Elements (λ/2 grid)", "N = (π/4) · (2D / λ)²"], ["Link", "G ≈ η · π · N"]];
  f.forEach(([a, b], i) => {
    const x = 0.5 + i * 4.8;
    card(s, x, 1.7, 4.55, 1.75, null, "formula " + i);
    s.addText([{ text: a, options: { fontSize: 14, color: X.slate, breakLine: true } }, { text: b, options: { fontSize: 20, bold: true, fontFace: "Cambria", color: X.navy } }],
      { x: x + 0.25, y: 1.85, w: 4.1, h: 1.45, valign: "middle", margin: 0, isTextBox: true, objectName: "formula text " + i });
  });
  card(s, 0.5, 3.7, 19.0, 5.25, "3GPP satellite antennas (TR 38.821 Tab. 6.1.1.1-1/2) — and what a phased array would need", "antenna table card");
  const rows = [[TH("Satellite"), TH("Aperture D", { align: "center" }), TH("Beam width calc / 3GPP", { align: "center" }), TH("Gain calc / 3GPP", { align: "center" }),
    TH("Beam on ground (nadir)", { align: "center" }), TH("Elements (λ/2)", { align: "center" })]];
  for (const a of D.antennas) {
    const big = a.N > 10000;
    rows.push([T(a.name, { bold: true, fontSize: 15 }), T(`${a.D} m`, { align: "center", fontSize: 15 }), T(`${a.th}° / ${a.th_doc}°`, { align: "center", fontSize: 15 }),
      T(`${a.G} / ${a.G_doc} dBi`, { align: "center", fontSize: 15 }), T(`${a.beam_km} km`, { align: "center", fontSize: 15 }),
      T(`≈ ${a.N.toLocaleString("en-US")}`, { align: "center", fontSize: 15, bold: true, color: big ? X.coral : X.teal })]);
  }
  s.addTable(rows, { x: 0.8, y: 4.35, w: 18.4, colW: [3.6, 2.4, 3.4, 3.2, 3.0, 2.8], rowH: 0.62, objectName: "antenna table" });
  bullets(s, [
    { text: "My formulas reproduce 3GPP's beam widths and gains → the element counts are consistent (element counts themselves are my calculation)", options: { color: X.white } },
    { text: "LEO: hundreds to thousands of elements → phased array is practical. GEO: tens of thousands → large deployable reflector + feed array", options: { color: X.mist } },
  ], 0.6, 9.2, 18.8, 1.3, "antenna takeaways", 16);
  s.addNotes("Beam width is about 1.029 lambda over D, gain is eta (pi D / lambda) squared, and a lambda/2 phased array needs N = (pi/4)(2D/lambda)^2 elements, so gain is about eta pi N. These formulas reproduce the beam widths and gains in TR 38.821. LEO satellites need hundreds to thousands of elements; GEO would need tens of thousands, so GEO uses big reflectors with feed arrays instead.");
}
{
  const s = content("03 · BEAMS — COVERING A REGION", "How Many Beams to Cover a Region?", "3 · Antennas & beams");
  card(s, 0.5, 1.7, 19.0, 1.55, null, "beam formula");
  s.addText([{ text: "N_beams ≈ 1.21 · A_region / (π · (D_beam / 2)²)", options: { fontSize: 26, bold: true, fontFace: "Cambria", color: X.navy } },
    { text: "      1.21 = hexagonal overlap · D_beam from TR 38.821 Tab. 6.1.1.1-1 (nadir)", options: { fontSize: 15, color: X.slate } }],
    { x: 0.8, y: 1.85, w: 18.4, h: 1.25, valign: "middle", margin: 0, isTextBox: true, objectName: "beam formula text" });
  card(s, 0.5, 3.5, 11.6, 5.6, null, "beam table card");
  const rows = [[TH("Beam type", { fontSize: 15 }), TH("Istanbul\n5 461 km²", { align: "center", fontSize: 15 }), TH("Turkey\n783 562 km²", { align: "center", fontSize: 15 }),
    TH("Whole visible area\n(ε ≥ 10°)", { align: "center", fontSize: 15 })]];
  for (const b of D.beams) {
    rows.push([T(b.name, { bold: true, fontSize: 16 }), T(String(b.istanbul), { align: "center", fontSize: 20, bold: true, color: X.teal }),
      T(b.turkey.toLocaleString("en-US"), { align: "center", fontSize: 20, bold: true, color: X.blue }),
      T(`≈ ${b.visible.toLocaleString("en-US")}`, { align: "center", fontSize: 18, color: X.navy })]);
  }
  s.addTable(rows, { x: 0.8, y: 3.75, w: 11.0, colW: [3.9, 2.0, 2.3, 2.8], rowH: [0.85, 1.0, 1.0, 1.0, 1.0], objectName: "beam table" });
  s.addText("Visible-area values are upper bounds: beams grow away from nadir.", { x: 0.8, y: 8.6, w: 11, h: 0.4, fontSize: 13, color: X.slate, margin: 0, isTextBox: true, objectName: "beam note" });
  card(s, 12.4, 3.5, 7.1, 5.6, "Antennas vs beams", "antennas vs beams");
  bullets(s, ["The antenna (D, elements) sets how SMALL each beam is", "The number of beams sets how much AREA is covered",
    "One phased array forms many beams at once (digital beamforming) — limited by power and RF chains, not by elements",
    "Turkey: ~480 LEO S-band beams vs ~20 GEO S-band beams"], 12.7, 4.2, 6.55, 4.8, "beam bullets", 18);
  s.addNotes("Number of beams = region area over beam area, with 1.21 for hexagonal overlap. With 3GPP Set-1 beams: Istanbul needs 4 LEO S-band beams or 1 GEO beam; Turkey about 480 LEO or 20 GEO S-band beams. Filling a LEO satellite's whole visible area would need about 4,900 beams by area ratio, about 6,000 with overlap - no satellite does that; it only illuminates where users are. The antenna sets the beam size; the beam count sets the covered area.");
}
{
  const s = content("03 · BEAMS — WORKED EXAMPLE", "One Beam the Size of Istanbul: How Big an Antenna?", "3 · Antennas & beams");
  const ob = D.one_beam;
  s.addText(`Istanbul ≈ 5 461 km² → one circular beam of ≈ ${ob.D_beam} km diameter`, { x: 0.5, y: 1.65, w: 19, h: 0.55, fontSize: 20, color: X.mist,
    margin: 0, isTextBox: true, objectName: "example intro" });
  const leo = ob.rows[0], geo = ob.rows[1];
  const col = (x, title, color, r, name) => {
    card(s, x, 2.4, 9.3, 5.4, null, name);
    s.addText(title, { x: x + 0.35, y: 2.6, w: 8.6, h: 0.6, fontSize: 24, bold: true, fontFace: "Cambria", color, margin: 0, isTextBox: true, objectName: name + " title" });
    s.addText(`beam width needed: θ = ${r.th}°`, { x: x + 0.35, y: 3.25, w: 8.6, h: 0.45, fontSize: 16, color: X.slate, margin: 0, isTextBox: true, objectName: name + " theta" });
    const big = (y, v, l) => s.addText([{ text: v, options: { fontSize: 46, bold: true, fontFace: "Cambria", color, breakLine: true } },
      { text: l, options: { fontSize: 15, color: X.navy } }], { x: x + 0.35, y, w: 4.3, h: 1.9, valign: "top", margin: 0, isTextBox: true, objectName: name + " stat" });
    big(4.0, `${r.D_S} m`, "antenna diameter at 2 GHz (S-band)");
    s.addText([{ text: `${r.D_Ka} m`, options: { fontSize: 46, bold: true, fontFace: "Cambria", color, breakLine: true } },
      { text: "at 20 GHz (Ka-band)", options: { fontSize: 15, color: X.navy } }], { x: x + 4.75, y: 4.0, w: 4.3, h: 1.9, valign: "top", margin: 0, isTextBox: true, objectName: name + " ka" });
    s.addText([{ text: `≈ ${r.N.toLocaleString("en-US")}`, options: { fontSize: 34, bold: true, fontFace: "Cambria", color: X.navy } },
      { text: "  phased-array elements (any frequency)", options: { fontSize: 15, color: X.slate } }],
      { x: x + 0.35, y: 6.3, w: 8.6, h: 1.2, valign: "middle", margin: 0, isTextBox: true, objectName: name + " elements" });
  };
  col(0.5, "From LEO-600", X.teal, leo, "LEO");
  col(10.2, "From GEO", X.amber, geo, "GEO");
  card(s, 0.5, 8.05, 19.0, 2.25, null, "insight");
  s.addText([{ text: "Element count depends only on the beam angle:  N ≈ (π/4) · (2.06 / θ₃dB)²", options: { fontSize: 22, bold: true, fontFace: "Cambria", color: X.navy, breakLine: true } },
    { text: "GEO is 60× farther → needs a 60× narrower beam → 60× bigger antenna and 3 600× more elements. That is why GEO beams are 250 km or larger and LEO uses compact phased arrays.",
      options: { fontSize: 16, color: X.slate } }], { x: 0.8, y: 8.2, w: 18.4, h: 1.95, valign: "middle", margin: 0, isTextBox: true, objectName: "insight text" });
  s.addNotes(`To cover Istanbul with one beam we need about an ${ob.D_beam} km beam. From 600 km that is ${leo.th} degrees: a ${leo.D_S} m antenna at 2 GHz, ${leo.D_Ka} m at 20 GHz, about ${leo.N} elements. From GEO it is ${geo.th} degrees: a ${geo.D_S} m antenna at 2 GHz (${geo.D_Ka} m at Ka-band), about ${geo.N.toLocaleString("en-US")} elements. The element count depends only on the beam angle, not on frequency; frequency only changes the physical size.`);
}
{
  const s = content("03 · RESEARCH DIRECTION", "Beyond One Satellite: Distributed Massive MIMO", "3 · Antennas & beams");
  card(s, 0.5, 1.7, 9.3, 8.4, "Idea [Abdelsadek, Karabulut Kurt, Yanikomeroglu, 2022]", "dmimo idea");
  bullets(s, ["Mega-constellations: several LEO satellites visible at once", "A user is served jointly by a cluster of satellites (cell-free massive MIMO)",
    "Antennas hundreds of km apart → breaks the rank-1 / keyhole limit", "Precoding allows full frequency reuse instead of colour reuse",
    "Cluster handover → longer service time, fewer handovers", "Reported: ~4× spectral efficiency vs single-satellite (8 satellites, 30 GHz)"],
    0.8, 2.5, 8.7, 7.4, "dmimo bullets", 20);
  card(s, 10.1, 1.7, 9.4, 4.5, "LoS-MIMO rule: why it needs many satellites", "losmimo");
  s.addText([{ text: "d_t · d_r ≈ λ · R / N", options: { fontSize: 26, bold: true, fontFace: "Cambria", color: X.navy, breakLine: true } },
    { text: "rank 2 at R = 600 km with a phone (d_r = λ/2) needs satellite antennas ≈ 600 km apart; a 1 m VSAT at Ka-band still needs ≈ 4.5 km → only possible across different satellites",
      options: { fontSize: 18, color: X.slate } }], { x: 10.4, y: 2.45, w: 8.8, h: 3.7, valign: "top", margin: 0, isTextBox: true, objectName: "losmimo text" });
  card(s, 10.1, 6.4, 9.4, 3.7, "Challenges — visible in our simulation", "dmimo challenges");
  bullets(s, ["Two serving satellites can differ by ≈ 86 kHz in Doppler (rising +41, setting −45 kHz)", "… and by ≈ 4.4 ms in delay (600 vs 1 932 km)",
    "→ per-satellite pre-compensation + phase sync before coherent combining", "Not in TR 38.811 / 38.821 — research topic"], 10.4, 7.05, 8.8, 3.0, "challenge bullets", 17);
  s.addNotes("Research direction: instead of one satellite per user, a cluster of satellites serves the user jointly. Because the antennas are on different satellites, hundreds of km apart, the channel is no longer rank 1. The paper by Abdelsadek, Karabulut Kurt and Yanikomeroglu (IEEE OJ-COMS 2022) reports about 4 times the spectral efficiency and fewer handovers. Our simulation shows the hard part: two serving satellites differ by tens of kHz in Doppler and milliseconds in delay, so each must be compensated separately.");
}

// ------------------------------------------------------------------ 4. summary
section("04", "Summary", "What the simulation shows about LEO and GEO — and where the numbers come from.", "4 · Summary")
  .addNotes("Section 4: summary and references.");
{
  const s = content("04 · SUMMARY", "LEO versus GEO", "4 · Summary");
  card(s, 0.5, 1.7, 12.6, 8.55, null, "compare card");
  const bad = { color: X.coral, bold: true }, good = { color: X.green, bold: true };
  const R = (t, o = {}) => T(t, Object.assign({ fontSize: 14.5 }, o));
  const rows = [[TH("", { fontSize: 15 }), TH("LEO-600", { fontSize: 15, color: X.teal }), TH("GEO", { fontSize: 15, color: "C77C0E" })],
    [R("RTT, service link", { color: X.slate }), R("4 – 13 ms", good), R("239 – 271 ms", bad)],
    [R("Max Doppler (2 GHz)", { color: X.slate }), R("±46 kHz, ≈ 580 Hz/s", bad), R("≤ 1.7 kHz (UE motion)", good)],
    [R("Path loss (2 GHz)", { color: X.slate }), R("154 – 164 dB"), R("≈ 190 dB", bad)],
    [R("Handheld UL CNR (3GPP Set-1)", { color: X.slate }), R("+2.8 dB"), R("−10.9 dB", bad)],
    [R("Handover", { color: X.slate }), R("every ≈ 8 min", bad), R("none", good)],
    [R("One satellite covers", { color: X.slate }), R("1.9 % of Earth"), R("34 % of Earth", good)],
    [R("Satellites for Istanbul 24/7 (ε = 10°)", { color: X.slate }), R("≈ 38", bad), R("1", good)],
    [R("Beams to cover Turkey (S-band)", { color: X.slate }), R("≈ 480 × 50 km"), R("≈ 20 × 250 km")],
    [R("Antenna for an Istanbul-size beam (2 GHz)", { color: X.slate }), R("1.1 m, ≈ 170 elements", good), R("66 m, ≈ 610 000 elements", bad)],
  ];
  s.addTable(rows, { x: 0.8, y: 1.95, w: 12.0, colW: [5.0, 3.5, 3.5], rowH: 0.8, objectName: "comparison table" });
  const tk = (y, title, color, items, name) => {
    card(s, 13.4, y, 6.1, 4.15, null, name);
    s.addText(title, { x: 13.7, y: y + 0.25, w: 5.6, h: 0.55, fontSize: 21, bold: true, fontFace: "Cambria", color, margin: 0, isTextBox: true, objectName: name + " title" });
    bullets(s, items, 13.7, y + 0.95, 5.6, 3.0, name + " list", 17);
  };
  tk(1.7, "LEO: problems from motion", X.teal, ["Doppler → UE pre-compensation", "Changing delay → continuous timing advance", "Frequent handover → conditional HO (T1, D1)", "Many satellites and beams for coverage"], "LEO takeaway");
  tk(6.1, "GEO: problems from distance", "C77C0E", ["~250–540 ms RTT → more HARQ, K_offset", "~190 dB path loss → weak phone uplink", "Huge antennas for small beams", "But: 1 satellite, no Doppler, no handover"], "GEO takeaway");
  s.addNotes("Summary: LEO's problems come from motion - Doppler, changing delay, frequent handover, and the need for many satellites and beams. GEO's problems come from distance - delay, path loss, weak uplink and the huge antennas needed for small beams. Distances and RTT match TR 38.821 Table 4.2-2; Doppler within 4-8 percent; link budget reproduces all 60 CNR values of TR 38.821 Table 6.1.3.3-1.");
}
{
  const s = content("04 · FORMULAS & REFERENCES", "Formulas and Sources", "4 · Summary");
  card(s, 0.5, 1.7, 12.8, 8.55, null, "formula card");
  const items = [
    ["Slant range", "d = √(R_E² sin²α + h² + 2hR_E) − R_E sin α", "TR 38.811 (6.6-3)"],
    ["Path loss", "FSPL = 32.45 + 20 log₁₀ f_c[GHz] + 20 log₁₀ d[m]", "TR 38.811 (6.6-2)"],
    ["Delay", "RTT = 2d / c", "TR 38.821 Tab. 4.2-2"],
    ["Doppler", "f_d = −f_c · ṙ / c", "geometry"],
    ["Link budget", "CNR = EIRP + G/T − k − PL − 10 log₁₀ B", "TR 38.821 (6.1.3.1-2)"],
    ["Coverage angle", "λ = arccos(R_E cos ε / r) − ε", "geometry of (6.6-3)"],
    ["Sats per plane", "N > π / λ,   t_HO = T / N", "own derivation"],
    ["Beam width / gain", "θ₃dB = 1.029 λ / D,   G = η(πD/λ)²", "TR 38.811 §6.4.1 pattern"],
    ["Elements / beams", "N = (π/4)(2D/λ)²,   N_b = 1.21 A / (π(D_b/2)²)", "own calculation"],
  ];
  s.addTable([[TH("Quantity", { fontSize: 14 }), TH("Formula", { fontSize: 14 }), TH("Source", { fontSize: 14 })],
    ...items.map(([a, b, c]) => [T(a, { bold: true, fontSize: 14 }), T(b, { fontSize: 14.5, fontFace: "Cambria" }), T(c, { fontSize: 13, color: X.slate })])],
    { x: 0.8, y: 1.95, w: 12.2, colW: [2.6, 6.6, 3.0], rowH: 0.8, objectName: "formula table" });
  card(s, 13.6, 1.7, 5.9, 8.55, "References", "refs");
  const refs = [["[1] 3GPP TR 38.811 V15.4.0", "NR to support non-terrestrial networks: channel model, path loss, LOS probability, antenna pattern"],
    ["[2] 3GPP TR 38.821 V16.2.0", "Solutions for NR to support NTN: reference scenarios, satellite & UE parameters, link budget (60/60 CNR values reproduced within 0.06 dB)"],
    ["[3] M. Y. Abdelsadek, G. Karabulut Kurt, H. Yanikomeroglu", "\"Distributed Massive MIMO for LEO Satellite Networks,\" IEEE OJ-COMS, vol. 3, pp. 2162–2177, 2022"],
    ["Simulation", "Own Python code (numpy, matplotlib), Google Colab notebook. 2-D single plane, circular orbits, Earth-fixed frame"]];
  const t = [];
  refs.forEach(([a, b], i) => { t.push({ text: a, options: { bold: true, fontSize: 15, color: X.navy, breakLine: true } });
    t.push({ text: b, options: { fontSize: 13.5, color: X.slate, breakLine: i < refs.length - 1, paraSpaceAfter: 14 } }); });
  s.addText(t, { x: 13.9, y: 2.35, w: 5.35, h: 7.7, valign: "top", margin: 0, isTextBox: true, objectName: "reference list" });
  s.addNotes("All numbers in this talk come from these formulas. 3GPP sources: TR 38.811 V15.4.0 and TR 38.821 V16.2.0. Formulas marked own derivation or own calculation are not in the TRs but are checked against 3GPP values where possible.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
