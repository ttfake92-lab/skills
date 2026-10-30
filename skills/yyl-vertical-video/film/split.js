// yyl-vertical-video · film module for the lighttrail renderer (1080×1920).
// Layout measured on the two reference reels (references/reference-analysis.md):
//   · top ≈ 62 %: near-black canvas with a faint grid — a two-line header (heavy sans + italic serif with a red underline)
//     and one motion-graphics component at a time, each built in sync with the words that name it;
//   · bottom: a rounded "person card" bleeding off the bottom edge. The speaker inside it is cut out (Vision mask) and drawn
//     ~14 % larger than the room behind, anchored at the card's bottom, so the head and hands break out over the card's top
//     edge while the background stays cropped below it — the depth trick of the reference;
//   · fullscreen person segments (judgement, jokes, CTA) morph out of the card and back.
// Reads project/film/beats.json (layout / titles / scenes / theme), project/words.json + captions.json (align.py),
// project/film/peaks.json and media/build/data/{source,media,faces}.json (prep.py). Schema: ../references/beats.md
import { setSize, E, seg, clamp, lerp, rrect, TAU, hash, F } from '/engine/core.js';
import { loadJSON, loadImage } from '/engine/media.js';
import { QA, reg } from '/engine/devices.js';

const W = 1080, H = 1920;
const LATI = F.serif, ZHSERIF = '"Songti SC"';
const RED = [226, 28, 52], GREEN = [52, 199, 112];
const THEMES = {
  dark: { bg: [9, 9, 11], fg: [244, 243, 240], dim: [150, 150, 156], card: [24, 24, 28], line: [255, 255, 255], grid: 0.035 },
  light: { bg: [231, 231, 228], fg: [17, 17, 19], dim: [110, 110, 116], card: [250, 250, 248], line: [0, 0, 0], grid: 0.05 },
};
// the person card (design = output pixels)
const CARD = { x: 72, y: 1410, w: 936, h: 560, r: 34 };
const POP = 1.16;              // cut-out scale over the background inside the card
const CAP_Y = { split: 1262, full: 1300 };
const STAGE = { top: 330, bot: 1190 };   // components live here

// default sound per component event: [libraryId, gain, dt]
export const SFX = {
  layout: [['swish-soft', 0.5, -0.1]], title: [['ui-pop-deep', 0.45]], item: [['ui-blip', 0.45]], hot: [['ui-select', 0.5]],
  snap: [['mouse-click', 0.4]], stamp: [['stamp-thud', 0.7]], glitch: [['glitch', 0.45]], type: [['keyboard-type', 0.35]],
  send: [['airy-short-whoosh', 0.55]], node: [['tiny-bubble-pop', 0.5]], card: [['simple-whoosh', 0.45]], phone: [['ui-pop-deep', 0.4]],
  shimmer: [['magic-shimmer', 0.5]], error: [['wrong-buzz', 0.35]], check: [['right-ding', 0.45]], scan: [['scan-sweep', 0.45]],
  lock: [['lock-clack', 0.6]], notify: [['notify-chime', 0.5]], riser: [['sharp-bass-riser', 0.4, -0.5]], impact: [['vine-boom-impact', 0.35]],
  ding: [['clean-ding', 0.5]], whoosh: [['deep-short-whoosh', 0.45]],
};

const mixc = (a, b, k) => a.map((v, i) => Math.round(v + (b[i] - v) * k));
const css = (c, a = 1) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
// all type is serif (Songti SC has Light / Regular / Bold / Black; its Latin glyphs are serif too)
const serif = (s, w = 800) => `${w >= 850 ? 900 : w >= 600 ? 700 : 400} ${s}px ${ZHSERIF}`;
const isLatin = (ch) => /[A-Za-z0-9+\-.·&#@%:/]/.test(ch);

export async function createFilm({ media, query, log }) {
  setSize(W, H);
  const SHOW_CAPTIONS = !query || query.get('captions') !== '0';
  const beats = await loadJSON('/project/film/beats.json');
  const src = await loadJSON('/media/data/source.json');
  const lib = await loadJSON('/media/data/media.json');
  const words = await loadJSON('/project/words.json');
  const caps = (await loadJSON('/project/captions.json')).cards;
  const peaks = await loadJSON('/project/film/peaks.json');
  const faces = (await loadJSON('/media/data/faces.json')).faces;
  const FPS = src.fps, NF = Math.round((beats.duration || src.frames / FPS) * FPS);
  await Promise.all(['900 60px "Songti SC"', '700 40px "Songti SC"', '400 40px "Songti SC"', 'italic 400 60px LTSerif', serif(30, 700)].map((f) => document.fonts.load(f, '永AI剪辑ab')));

  media.register('cam', { url: '/media/frames/cam', count: src.frames });
  media.register('mask', { url: '/media/frames/mask', count: src.frames, ext: 'png' });
  for (const [k, n] of Object.entries(lib.seq)) if (k !== 'cam' && k !== 'mask') media.register(k, { url: `/media/frames/${k}`, count: n });
  const IMG = {};
  for (const [k, p] of Object.entries(lib.images || {})) IMG[k] = await loadImage(`/media/${p}`);

  // ───────── anchors: "at:词#2+0.1", "end:词", number ─────────
  const text = words.text, chars = words.chars;
  const norm = (s) => s.replace(/[\s，。、？！：；“”‘’「」,.?!:;"'()（）…—-]/g, '').toLowerCase();
  function T(v) {
    if (typeof v === 'number') return v;
    const m = /^(at|end):(.+?)(?:#(\d+))?([+-][\d.]+)?$/.exec(v);
    if (!m) throw new Error(`bad anchor ${v}`);
    const w = norm(m[2]); let i = -1;
    for (let n = 0; n < Number(m[3] || 1); n++) { i = text.indexOf(w, i + 1); if (i < 0) throw new Error(`anchor not in script: ${v}`); }
    return (m[1] === 'at' ? chars[i].t0 : chars[i + w.length - 1].t1) + Number(m[4] || 0);
  }
  const deep = (o) => (Array.isArray(o) ? o.map(deep) : o && typeof o === 'object'
    ? Object.fromEntries(Object.entries(o).map(([k, v]) => [k, deep(v)]))
    : typeof o === 'string' && /^(at|end):/.test(o) ? T(o) : o);
  const LAY = deep(beats.layout), TITLES = deep(beats.titles), SCENES = deep(beats.scenes), THEME = deep(beats.theme || []);
  const CTA = deep(beats.cta || []);

  // ───────── face framing: one median box (a digital human barely moves; per-frame follow would jitter) ─────────
  const fk = Object.values(faces);
  const med = (i) => { const a = fk.map((b) => b[i]).sort((x, y) => x - y); return a[a.length >> 1]; };
  const FACE = { x: med(0), y: med(1), w: med(2), h: med(3) };
  const SW = src.width, SH = src.height;
  // split: background scaled to the card, hair top just above the card's top edge (the room is cropped below it)
  const hairTop = (FACE.y - FACE.h * 0.42) * SH;
  // …and big enough that the room still runs past the frame's bottom edge (a short source would leave a black strip)
  const sB = Math.max(CARD.w * 1.06 / SW, 0.5, (H + 8 - CARD.y - 34) / (SH - hairTop));
  const TB = { s: sB, x: clamp(540 - (FACE.x + FACE.w / 2) * SW * sB, CARD.x + CARD.w - SW * sB, CARD.x), y: CARD.y + 34 - hairTop * sB };
  // full: cover 1080×1920, face centred horizontally, eyes near 30 % height
  const sF = Math.max(H / SH, W / SW) * 1.02;
  const TF = { s: sF, x: clamp(540 - (FACE.x + FACE.w / 2) * SW * sF, W - SW * sF, 0), y: clamp(H * 0.24 - FACE.y * SH * sF, H - SH * sF, 0) };

  // layout value u: 0 split, 1 full, eased through a 0.34 s morph that starts 0.12 s before the switch word
  const MORPH = 0.34;
  function layoutU(t) {
    let u = LAY[0].mode === 'full' ? 1 : 0;
    for (let i = 1; i < LAY.length; i++) {
      const L = LAY[i], to = L.mode === 'full' ? 1 : 0;
      const p = E.inOutCubic(seg(t, L.t - 0.12, L.t - 0.12 + MORPH));
      u = lerp(u, to, p);
    }
    return u;
  }
  const fullSince = (t) => { let s = 0; for (const L of LAY) if (L.t <= t && L.mode === 'full') s = L.t; else if (L.t <= t) s = -1; return s; };
  function themeK(t) {
    let k = 0;
    for (const th of THEME) k = lerp(k, th.theme === 'light' ? 1 : 0, E.inOutCubic(seg(t, th.t - 0.15, th.t + 0.2)));
    return k;
  }

  const off = (w = W, h = H) => { const cv = document.createElement('canvas'); cv.width = w; cv.height = h; return cv; };
  const cut = off(), cutc = cut.getContext('2d');
  const tmp = off(), tmpc = tmp.getContext('2d');
  const camIdx = (tf) => Math.min(src.frames - 1, Math.max(0, Math.floor(tf * FPS + 1e-4)));   // sub-frame times map to the frame being rendered
  const seqIdx = (n, t, t0) => (((Math.floor(t * FPS + 1e-4) - Math.round(t0 * FPS)) % n) + n) % n;
  const seqFrame = (k, t, t0) => { const n = lib.seq[k]; if (!n) return null; return media.frame(k, seqIdx(n, t, t0)); };

  // ───────── theme helpers ─────────
  let TH = THEMES.dark;
  const col = (k, a = 1) => css(TH[k], a);

  // ───────── text ─────────
  function runs(str, latinFont, cjkFont) {
    const out = []; for (const ch of str) { const f = isLatin(ch) ? latinFont : cjkFont; if (out.length && out[out.length - 1].f === f) out[out.length - 1].s += ch; else out.push({ s: ch, f }); }
    return out;
  }
  function textW(c, str, latinFont, cjkFont) { let w = 0; for (const r of runs(str, latinFont, cjkFont)) { c.font = r.f; w += c.measureText(r.s).width; } return w; }
  // per-glyph blur reveal (the reference's headline entrance); skew for the synthetic italic of the CJK serif
  function reveal(c, str, x, y, o) {
    const { lf, cf, color, t, t0, stagger = 0.035, dur = 0.32, align = 'center', skew = 0, out = 1e9, sy = 1 } = o;   // sy: vertical stretch about the baseline
    const w = textW(c, str, lf, cf);
    let cx = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
    const pOut = seg(t, out - 0.22, out);
    let i = 0;
    for (const r of runs(str, lf, cf)) {
      c.font = r.f;
      for (const ch of r.s) {
        const cw = c.measureText(ch).width;
        const p = E.outCubic(seg(t, t0 + i * stagger, t0 + i * stagger + dur)) * (1 - pOut);
        if (p > 0.003) {
          c.save(); c.globalAlpha *= p; const b = (1 - p) * 12; if (b > 0.4) c.filter = `blur(${b.toFixed(1)}px)`;
          c.translate(cx, y + (1 - p) * 14); if (sy !== 1) c.scale(1, sy);
          if (skew && !isLatin(ch)) c.transform(1, 0, -skew, 1, 0, 0);
          c.fillStyle = color; c.fillText(ch, 0, 0); c.restore();
        }
        cx += cw; i++;
      }
    }
    return w;
  }

  // ───────── background ─────────
  function drawBg(c, t) {
    c.fillStyle = col('bg'); c.fillRect(0, 0, W, H);
    c.strokeStyle = col('line', TH.grid); c.lineWidth = 1; c.beginPath();
    for (let x = 6; x < W; x += 54) { c.moveTo(x + 0.5, 0); c.lineTo(x + 0.5, H); }
    for (let y = 0; y < H; y += 54) { c.moveTo(0, y + 0.5); c.lineTo(W, y + 0.5); }
    c.stroke();
    // two slow, faint colour fields behind the stage, so the glass panels have something to refract
    for (const [gx, gy, gr, cc, ga] of [[320 + 90 * Math.sin(t * 0.23), 640 + 60 * Math.cos(t * 0.31), 560, RED, 0.13],
      [800 + 70 * Math.cos(t * 0.19), 1040 + 80 * Math.sin(t * 0.27), 520, [120, 140, 255], 0.07]]) {
      const rg = c.createRadialGradient(gx, gy, 0, gx, gy, gr); rg.addColorStop(0, css(cc, ga)); rg.addColorStop(1, css(cc, 0));
      c.fillStyle = rg; c.fillRect(0, 0, W, H);
    }
    const g = c.createRadialGradient(540, 760, 120, 540, 760, 1100);
    g.addColorStop(0, col('bg', 0)); g.addColorStop(1, col('bg', 0.85));
    c.fillStyle = g; c.fillRect(0, 0, W, H);
  }

  // ───────── header ─────────
  function drawTitle(c, t) {
    for (const ti of TITLES) {
      if (t < ti.from - 0.05 || t > ti.to + 0.05) continue;
      c.save(); c.textBaseline = 'alphabetic';
      // headline type is stretched ~22 % taller (the reference's condensed display look)
      reveal(c, ti.a, 540, 172, { lf: serif(62, 900), cf: serif(62, 900), color: col('fg'), t, t0: ti.from, out: ti.to, sy: 1.22 });
      const w = reveal(c, ti.b, 540, 282, { lf: `italic 400 92px ${LATI}`, cf: `900 78px ${ZHSERIF}`, color: col('fg'), t, t0: ti.from + 0.16, out: ti.to, skew: 0.2, stagger: 0.04, sy: 1.22 });
      const p = E.inOutCubic(seg(t, ti.from + 0.45, ti.from + 0.85)) * (1 - seg(t, ti.to - 0.22, ti.to));
      if (p > 0) { c.fillStyle = css(RED, 0.95); c.fillRect(540 - w / 2 - 6, 302, (w + 12) * p, 5); }
      c.restore();
    }
  }

  // ───────── person ─────────
  function personTransform(u) {
    return { s: lerp(TB.s, TF.s, u), x: lerp(TB.x, TF.x, u), y: lerp(TB.y, TF.y, u) };
  }
  function drawPerson(c, t, tf, u) {
    const img = media.frame('cam', camIdx(tf)); if (!img) return;
    const R = { x: lerp(CARD.x, 0, u), y: lerp(CARD.y, 0, u), w: lerp(CARD.w, W, u), h: lerp(CARD.h, H, u), r: lerp(CARD.r, 0, u) };
    let tr = personTransform(u);
    // fullscreen: slow push-in from the moment it went full
    const fs = fullSince(t);
    if (u > 0.5 && fs >= 0) {
      const z = 1 + 0.045 * E.outCubic(seg(t, fs, fs + 4)) + 0.03 * E.outBack(seg(t, fs - 0.1, fs + 0.35)) * (1 - seg(t, fs + 0.35, fs + 1.2));
      const ax = 540, ay = H * 0.3;
      tr = { s: tr.s * z, x: ax + (tr.x - ax) * z, y: ay + (tr.y - ay) * z };
    }
    const dw = SW * tr.s, dh = SH * tr.s;
    // card shadow + room
    c.save();
    c.shadowColor = 'rgba(0,0,0,0.55)'; c.shadowBlur = 50 * (1 - u); c.shadowOffsetY = 12 * (1 - u);
    rrect(c, R.x, R.y, R.w, R.h, R.r); c.fillStyle = '#000'; c.fill();
    c.restore();
    c.save(); rrect(c, R.x, R.y, R.w, R.h, R.r); c.clip();
    if (u < 0.98) c.filter = `blur(${(1.6 * (1 - u)).toFixed(2)}px) brightness(${lerp(0.8, 1, u).toFixed(3)})`;
    c.drawImage(img, tr.x, tr.y, dw, dh); c.filter = 'none';
    c.restore();
    if (u < 0.98) {     // the larger cut-out, anchored at the card's bottom centre
      const m = media.frame('mask', camIdx(tf)); if (!m) return;
      const k = lerp(POP, 1, u), ax = 540, ay = lerp(H, H, u);
      const px = ax + (tr.x - ax) * k, py = ay + (tr.y - ay) * k;
      cutc.setTransform(1, 0, 0, 1, 0, 0); cutc.globalCompositeOperation = 'source-over'; cutc.clearRect(0, 0, W, H);
      cutc.drawImage(img, px, py, dw * k, dh * k);
      cutc.globalCompositeOperation = 'destination-in'; cutc.drawImage(m, px, py, dw * k, dh * k);
      cutc.globalCompositeOperation = 'source-over';
      c.save(); c.globalAlpha = 1 - seg(u, 0.6, 0.98);
      c.shadowColor = 'rgba(0,0,0,0.6)'; c.shadowBlur = 34; c.shadowOffsetY = 14;
      c.drawImage(cut, 0, 0); c.restore();
      // thin rim of the card over the room but under the person, so the break-out reads
      c.save(); c.globalAlpha = 1 - u; rrect(c, R.x + 0.5, R.y + 0.5, R.w - 1, R.h, R.r);
      c.strokeStyle = 'rgba(255,255,255,0.10)'; c.lineWidth = 1.5; c.stroke(); c.restore();
    }
  }
  function faceBox(u) { const tr = personTransform(u); const k = u < 0.5 ? POP : 1;
    const ax = 540, ay = H, px = ax + (tr.x - ax) * k, py = ay + (tr.y - ay) * k, s = tr.s * k;
    return [px + FACE.x * SW * s, py + FACE.y * SH * s, FACE.w * SW * s, FACE.h * SH * s]; }

  // ───────── captions ─────────
  function capAt(t) { for (const k of caps) if (t >= k.t0 && t < k.t1) return k; return null; }
  function drawCaption(c, t, u) {
    if (CTA.some((x) => t >= x.from && t < x.to)) return;
    const k = capAt(t); if (!k) return;
    const y = lerp(CAP_Y.split, CAP_Y.full, u);
    let size = 62; c.font = serif(size, 900);
    let w = textW(c, k.text, serif(size, 900), serif(size, 900)); if (w > 940) { size = Math.floor(size * 940 / w); w = 940; }
    const p = E.outBack(seg(t, k.t0, k.t0 + 0.14), 2.2), a = seg(t, k.t0, k.t0 + 0.06);
    c.save(); c.globalAlpha = a; c.translate(540, y); c.scale(lerp(0.86, 1, p), lerp(0.86, 1, p));
    c.font = serif(size, 900); c.textAlign = 'center'; c.textBaseline = 'middle';
    c.shadowColor = 'rgba(0,0,0,0.75)'; c.shadowBlur = 18; c.shadowOffsetY = 3;
    c.fillStyle = '#fff'; c.fillText(k.text, 0, 0); c.restore();
    reg(540 - w / 2, y - size * 0.6, w, size * 1.2, 'caption');
  }
  function drawCTA(c, t) {
    for (const x of CTA) {
      if (t < x.from || t > x.to) continue;
      const p = E.outCubic(seg(t, x.from, x.from + 0.4)), q = seg(t, x.to - 0.2, x.to);
      c.save(); c.globalAlpha = 1 - q; c.textBaseline = 'middle';
      c.shadowColor = 'rgba(0,0,0,0.8)'; c.shadowBlur = 24;
      reveal(c, x.a, 540, 1330, { lf: serif(66, 900), cf: serif(66, 900), color: '#fff', t, t0: x.from });
      reveal(c, x.b, 540, 1446, { lf: `italic 400 132px ${LATI}`, cf: `900 112px ${ZHSERIF}`, color: css(RED), t, t0: x.at, skew: 0.2, stagger: 0.05, sy: 1.16 });
      if (x.c) reveal(c, x.c, 540, 1560, { lf: serif(54, 800), cf: serif(54, 800), color: '#fff', t, t0: x.at + 0.5 });
      c.restore(); reg(140, 1280, 800, 330, 'caption');
      void p;
    }
  }

  // ───────── card primitive: liquid glass ─────────
  // A frosted, slightly lensing panel: what is already on the canvas behind it is blurred, brightened, saturated and
  // magnified a touch, then a smoked tint keeps text legible; a top sheen, an inner rim glow and a bright specular edge
  // (top-left strong, bottom-right weaker) give the glass thickness; a light band sweeps across as the panel arrives.
  const back = document.createElement('canvas'), backc = back.getContext('2d');
  const GL = { t: 0, t0: -9 };                       // scene clock for the entrance sweep (set by env)
  const withFilter = (f0, f) => (f0 && f0 !== 'none' ? `${f0} ${f}` : f);
  function glass(c, x, y, w, h, r = 26, o = {}) {
    const cv = c.canvas, m = c.getTransform();
    const pts = [[x, y], [x + w, y], [x, y + h], [x + w, y + h]].map(([px, py]) => m.transformPoint(new DOMPoint(px, py)));
    const pad = 70, bx = Math.max(0, Math.min(...pts.map((q) => q.x)) - pad), by = Math.max(0, Math.min(...pts.map((q) => q.y)) - pad);
    const bw = Math.min(cv.width, Math.max(...pts.map((q) => q.x)) + pad) - bx, bh = Math.min(cv.height, Math.max(...pts.map((q) => q.y)) + pad) - by;
    if (bw <= 0 || bh <= 0) return;
    if (back.width < bw || back.height < bh) { back.width = Math.ceil(bw); back.height = Math.ceil(bh); }
    backc.setTransform(1, 0, 0, 1, 0, 0); backc.clearRect(0, 0, back.width, back.height); backc.drawImage(cv, bx, by, bw, bh, 0, 0, bw, bh);
    const f0 = c.filter;
    c.save();
    c.shadowColor = `rgba(0,0,0,${o.shadow ?? 0.5})`; c.shadowBlur = 56; c.shadowOffsetY = 24;
    rrect(c, x, y, w, h, r); c.fillStyle = 'rgba(0,0,0,0.5)'; c.fill(); c.shadowColor = 'transparent';
    rrect(c, x, y, w, h, r); c.clip();
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
    const cx = (pts[0].x + pts[3].x) / 2, cy = (pts[0].y + pts[3].y) / 2, k = 1.07;
    c.filter = withFilter(f0, 'blur(20px) saturate(180%) brightness(1.3)');
    c.drawImage(back, 0, 0, bw, bh, cx + (bx - cx) * k, cy + (by - cy) * k, bw * k, bh * k);
    c.restore();
    const base = o.fill || TH.card;
    const g = c.createLinearGradient(0, y, 0, y + h);
    g.addColorStop(0, css(mixc(base, [255, 255, 255], 0.1), o.a ?? 0.58)); g.addColorStop(1, css(base, o.a ?? 0.72));
    c.fillStyle = g; c.fillRect(x, y, w, h);
    const sh = c.createRadialGradient(x + w * 0.25, y - h * 0.2, 0, x + w * 0.25, y - h * 0.2, Math.max(w, h) * 0.8);
    sh.addColorStop(0, 'rgba(255,255,255,0.14)'); sh.addColorStop(1, 'rgba(255,255,255,0)');
    c.fillStyle = sh; c.fillRect(x, y, w, h);
    c.save(); c.filter = withFilter(f0, 'blur(6px)'); rrect(c, x, y, w, h, r); c.lineWidth = 14; c.strokeStyle = 'rgba(255,255,255,0.07)'; c.stroke(); c.restore();
    const at = o.at ?? GL.t0, sp = seg(GL.t, at + 0.12, at + 0.95);
    if (sp > 0 && sp < 1) {
      const sx = x - w * 0.3 + w * 1.6 * E.inOutCubic(sp), lg = c.createLinearGradient(sx - 140, y, sx + 140, y + h * 0.35);
      lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, `rgba(255,255,255,${0.16 * Math.sin(Math.PI * sp)})`); lg.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = lg; c.fillRect(x, y, w, h);
    }
    c.restore();
    c.save(); rrect(c, x, y, w, h, r);
    const eg = c.createLinearGradient(x, y, x + w * 0.55, y + h);
    eg.addColorStop(0, 'rgba(255,255,255,0.6)'); eg.addColorStop(0.32, 'rgba(255,255,255,0.12)'); eg.addColorStop(0.7, 'rgba(255,255,255,0.06)'); eg.addColorStop(1, 'rgba(255,255,255,0.32)');
    c.strokeStyle = o.stroke || eg; c.lineWidth = o.lw || 1.6; c.stroke();
    c.restore();
  }
  // scene envelope: blur + scale in, blur + lift out
  function env(c, t, sc, cx = 540, cy = 760, fn) {
    const pin = E.outCubic(seg(t, sc.t0, sc.t0 + 0.42)), pout = E.inCubic(seg(t, sc.t1 - 0.26, sc.t1));
    const a = pin * (1 - pout); if (a <= 0.002) return;
    GL.t = t; GL.t0 = sc.t0;
    c.save(); c.globalAlpha = a;
    const b = (1 - pin) * 14 + pout * 10; if (b > 0.4) c.filter = `blur(${b.toFixed(1)}px)`;
    // liquid entrance: spring past full size, with a brief squash (wider, shorter) that settles
    const q = seg(t, sc.t0, sc.t0 + 0.55), s = lerp(0.9, 1, E.outBack(q, 1.3)) * lerp(1, 0.96, pout), wob = 0.035 * Math.sin(Math.PI * q) * (1 - q);
    c.translate(cx, cy - pout * 30); c.scale(s * (1 + wob), s * (1 - wob)); c.translate(-cx, -cy);
    fn(); c.restore();
  }
  const local = (t, at, d = 0.35) => E.outCubic(seg(t, at, at + d));
  function blurIn(c, p, fn) { if (p <= 0.002) return; c.save(); c.globalAlpha *= p; const b = (1 - p) * 12; if (b > 0.4) c.filter = `blur(${b.toFixed(1)}px)`; c.translate(0, (1 - p) * 16); fn(); c.restore(); }

  // ───────── icons (line icons drawn at 0..1 box) ─────────
  function icon(c, name, x, y, s, color) {
    c.save(); c.translate(x, y); c.scale(s, s); c.strokeStyle = color; c.fillStyle = color; c.lineWidth = 2.4 / s * (s / 1) ; c.lineWidth = 0.075; c.lineCap = 'round'; c.lineJoin = 'round';
    const P = new Path2D();
    switch (name) {
      case 'cut': c.beginPath(); c.arc(0.25, 0.75, 0.14, 0, TAU); c.arc(0.75, 0.75, 0.14, 0, TAU); c.moveTo(0.33, 0.64); c.lineTo(0.78, 0.1); c.moveTo(0.67, 0.64); c.lineTo(0.22, 0.1); c.stroke(); break;
      case 'cc': rrect(c, 0.05, 0.2, 0.9, 0.6, 0.12); c.stroke(); c.beginPath(); c.moveTo(0.22, 0.45); c.lineTo(0.5, 0.45); c.moveTo(0.58, 0.45); c.lineTo(0.78, 0.45); c.moveTo(0.22, 0.6); c.lineTo(0.42, 0.6); c.moveTo(0.5, 0.6); c.lineTo(0.78, 0.6); c.stroke(); break;
      case 'film': rrect(c, 0.08, 0.15, 0.84, 0.7, 0.1); c.stroke(); for (let i = 0; i < 4; i++) { c.fillRect(0.14 + i * 0.2, 0.2, 0.08, 0.08); c.fillRect(0.14 + i * 0.2, 0.72, 0.08, 0.08); } c.beginPath(); c.moveTo(0.42, 0.38); c.lineTo(0.62, 0.5); c.lineTo(0.42, 0.62); c.closePath(); c.fill(); break;
      case 'spark': c.beginPath(); for (let i = 0; i < 8; i++) { const a = i * TAU / 8, r = i % 2 ? 0.16 : 0.44; c.lineTo(0.5 + Math.cos(a) * r, 0.5 + Math.sin(a) * r); } c.closePath(); c.stroke(); break;
      case 'sound': c.beginPath(); c.moveTo(0.1, 0.38); c.lineTo(0.28, 0.38); c.lineTo(0.5, 0.18); c.lineTo(0.5, 0.82); c.lineTo(0.28, 0.62); c.lineTo(0.1, 0.62); c.closePath(); c.stroke(); c.beginPath(); c.arc(0.5, 0.5, 0.2, -0.8, 0.8); c.stroke(); c.beginPath(); c.arc(0.5, 0.5, 0.36, -0.8, 0.8); c.stroke(); break;
      case 'doc': c.beginPath(); c.moveTo(0.2, 0.08); c.lineTo(0.62, 0.08); c.lineTo(0.82, 0.28); c.lineTo(0.82, 0.92); c.lineTo(0.2, 0.92); c.closePath(); c.stroke(); c.beginPath(); for (let i = 0; i < 3; i++) { c.moveTo(0.32, 0.42 + i * 0.15); c.lineTo(0.7, 0.42 + i * 0.15); } c.stroke(); break;
      case 'wave': c.beginPath(); [0.3, 0.6, 0.9, 0.5, 0.75, 0.35, 0.6].forEach((h, i) => { const x = 0.12 + i * 0.126; c.moveTo(x, 0.5 - h * 0.4); c.lineTo(x, 0.5 + h * 0.4); }); c.stroke(); break;
      case 'user': c.beginPath(); c.arc(0.5, 0.34, 0.18, 0, TAU); c.stroke(); c.beginPath(); c.arc(0.5, 1.0, 0.38, Math.PI * 1.1, Math.PI * 1.9); c.stroke(); break;
      case 'check': c.beginPath(); c.moveTo(0.2, 0.52); c.lineTo(0.42, 0.72); c.lineTo(0.82, 0.28); c.stroke(); break;
      case 'face': c.beginPath(); c.arc(0.5, 0.5, 0.4, 0, TAU); c.stroke(); c.fillRect(0.34, 0.38, 0.07, 0.1); c.fillRect(0.59, 0.38, 0.07, 0.1); c.beginPath(); c.arc(0.5, 0.56, 0.16, 0.3, Math.PI - 0.3); c.stroke(); break;
      case 'sync': c.beginPath(); c.arc(0.5, 0.5, 0.34, -2.6, 0.6); c.stroke(); c.beginPath(); c.moveTo(0.78, 0.55); c.lineTo(0.8, 0.72); c.lineTo(0.64, 0.68); c.stroke(); c.beginPath(); c.arc(0.5, 0.5, 0.34, 0.6 + 0.0, 2.6 - 0.0 + Math.PI * 0); c.stroke(); break;
      case 'vol': c.beginPath(); c.moveTo(0.1, 0.38); c.lineTo(0.28, 0.38); c.lineTo(0.5, 0.18); c.lineTo(0.5, 0.82); c.lineTo(0.28, 0.62); c.lineTo(0.1, 0.62); c.closePath(); c.stroke(); c.beginPath(); c.moveTo(0.64, 0.36); c.lineTo(0.9, 0.36); c.moveTo(0.64, 0.5); c.lineTo(0.9, 0.5); c.moveTo(0.64, 0.64); c.lineTo(0.9, 0.64); c.stroke(); break;
      case 'search': c.beginPath(); c.arc(0.42, 0.42, 0.26, 0, TAU); c.stroke(); c.beginPath(); c.moveTo(0.62, 0.62); c.lineTo(0.88, 0.88); c.stroke(); break;
      case 'music': c.beginPath(); c.moveTo(0.38, 0.75); c.lineTo(0.38, 0.18); c.lineTo(0.85, 0.1); c.lineTo(0.85, 0.66); c.stroke(); c.beginPath(); c.ellipse(0.28, 0.76, 0.12, 0.09, -0.3, 0, TAU); c.fill(); c.beginPath(); c.ellipse(0.75, 0.68, 0.12, 0.09, -0.3, 0, TAU); c.fill(); break;
      case 'lock': rrect(c, 0.18, 0.44, 0.64, 0.48, 0.08); c.stroke(); c.beginPath(); c.arc(0.5, 0.44, 0.2, Math.PI, 0); c.stroke(); break;
      case 'chat': rrect(c, 0.06, 0.12, 0.88, 0.62, 0.16); c.stroke(); c.beginPath(); c.moveTo(0.26, 0.74); c.lineTo(0.2, 0.92); c.lineTo(0.44, 0.74); c.stroke(); break;
      case 'code': c.beginPath(); c.moveTo(0.32, 0.25); c.lineTo(0.1, 0.5); c.lineTo(0.32, 0.75); c.moveTo(0.68, 0.25); c.lineTo(0.9, 0.5); c.lineTo(0.68, 0.75); c.moveTo(0.58, 0.18); c.lineTo(0.42, 0.82); c.stroke(); break;
      case 'rec': c.beginPath(); c.arc(0.5, 0.5, 0.38, 0, TAU); c.fill(); break;
      case 'cam': rrect(c, 0.06, 0.26, 0.6, 0.48, 0.08); c.stroke(); c.beginPath(); c.moveTo(0.7, 0.42); c.lineTo(0.94, 0.3); c.lineTo(0.94, 0.7); c.lineTo(0.7, 0.58); c.closePath(); c.stroke(); break;
      default: break;
    }
    void P; c.restore();
  }

  // ───────── components ─────────
  const C = {};
  const cues = [];
  const cue = (t, kind, gain = 1) => { for (const [id, g, dt = 0] of SFX[kind] || []) cues.push({ t: t + dt, id, gain: g * gain }); };

  // NLE timeline: tracks fill with clips that snap in, playhead sweeps
  C.nle = { cues: (sc) => { cue(sc.t0, 'card'); for (let i = 0; i < 7; i++) cue(sc.t0 + 0.35 + i * 0.12, 'snap', 0.8); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const x0 = 90, y0 = 470, w = 900, h = 560; glass(c, x0, y0, w, h, 28);
        // preview monitor
        const pv = { x: x0 + 30, y: y0 + 28, w: w - 60, h: 250 };
        c.save(); rrect(c, pv.x, pv.y, pv.w, pv.h, 14); c.clip(); c.fillStyle = '#000'; c.fillRect(pv.x, pv.y, pv.w, pv.h);
        const im = IMG[`t${Math.floor((t - sc.t0) * 2.5) % 12}`]; if (im) { const s = Math.max(pv.w / im.width, pv.h / im.height); c.drawImage(im, pv.x + (pv.w - im.width * s) / 2, pv.y + (pv.h - im.height * s) / 2, im.width * s, im.height * s); }
        c.restore();
        c.font = serif(20, 700); c.fillStyle = col('dim'); c.textAlign = 'left';
        const tc = (t - sc.t0) * 1; c.fillText(`00:00:${String(Math.floor(tc)).padStart(2, '0')}:${String(Math.floor((tc % 1) * 30)).padStart(2, '0')}`, pv.x, pv.y + pv.h + 34);
        // tracks
        const tracks = [{ n: 'V2', col: [120, 92, 255] }, { n: 'V1', col: [64, 132, 255] }, { n: 'T1', col: RED }, { n: 'A1', col: GREEN }];
        const ty = pv.y + pv.h + 56;
        tracks.forEach((tk, j) => {
          const yy = ty + j * 48; c.fillStyle = col('fg', 0.06); c.fillRect(x0 + 70, yy, w - 100, 38);
          c.font = serif(18, 700); c.fillStyle = col('dim'); c.fillText(tk.n, x0 + 28, yy + 26);
          const segs = [[0, 0.22], [0.25, 0.5], [0.53, 0.7], [0.74, 1]];
          segs.forEach(([a, b], i) => {
            const at = sc.t0 + 0.35 + (j * 2 + i) * 0.09; const p = E.outBack(seg(t, at, at + 0.3), 1.4);
            if (p <= 0) return; const sx = x0 + 70 + a * (w - 100), sw = (b - a) * (w - 100) - 6;
            c.save(); c.globalAlpha *= clamp(p); c.translate(0, (1 - p) * -40);
            rrect(c, sx, yy + 3, sw, 32, 6); c.fillStyle = css(tk.col, j === 3 ? 0.35 : 0.8); c.fill();
            if (j === 3) { c.strokeStyle = css(tk.col); c.lineWidth = 2; c.beginPath(); for (let q = 0; q < sw; q += 4) { const v = peaks.peaks[Math.floor((q + a * 900) * 1.3) % peaks.peaks.length] * 13; c.moveTo(sx + q, yy + 19 - v); c.lineTo(sx + q, yy + 19 + v); } c.stroke(); }
            c.restore();
          });
        });
        const ph = x0 + 70 + (w - 100) * clamp((t - sc.t0 - 0.2) / (sc.t1 - sc.t0 + 0.5));
        c.fillStyle = css(RED); c.fillRect(ph - 1.5, ty - 12, 3, 48 * 4 + 6); c.beginPath(); c.moveTo(ph - 9, ty - 16); c.lineTo(ph + 9, ty - 16); c.lineTo(ph, ty - 4); c.fill();
      });
    } };

  // stacked list of chips (icon + label), each revealed on its word; the newest is red
  C.chips = { cues: (sc) => { cue(sc.t0, 'card'); sc.items.forEach((it) => cue(it.at, it.hot ? 'hot' : 'item')); },
    draw(c, t, sc) {
      const n = sc.items.length, rowH = 112, w = 700, h = n * rowH + 50, x0 = 540 - w / 2, y0 = 760 - h / 2 + 10;
      env(c, t, sc, 540, 760, () => {
        glass(c, x0, y0, w, h, 30);
        let last = -1; sc.items.forEach((it, i) => { if (t >= it.at) last = i; });
        sc.items.forEach((it, i) => {
          const p = local(t, it.at, 0.4); const yy = y0 + 25 + i * rowH + rowH / 2;
          blurIn(c, p, () => {
            const hot = i === last || it.hot && t >= it.at;
            const color = hot ? css(RED) : col('fg', 0.92);
            if (hot) { c.save(); rrect(c, x0 + 18, yy - rowH / 2 + 10, w - 36, rowH - 20, 18); c.fillStyle = css(RED, 0.12); c.fill(); c.restore(); }
            icon(c, it.icon, x0 + 60, yy - 26, 52, color);
            c.font = serif(56, 800); c.fillStyle = color; c.textBaseline = 'middle'; c.textAlign = 'left';
            c.fillText(it.text, x0 + 150, yy + 2);
            if (it.icon === 'sound' && hot) {     // live waveform beside the last chip
              c.strokeStyle = css(RED); c.lineWidth = 4; c.lineCap = 'round'; c.beginPath();
              for (let q = 0; q < 14; q++) { const v = 6 + 26 * Math.abs(Math.sin(t * 9 + q * 0.9)) * (0.4 + 0.6 * hash(q)); const xx = x0 + w - 230 + q * 14; c.moveTo(xx, yy - v); c.lineTo(xx, yy + v); }
              c.stroke();
            }
          });
        });
      });
    } };

  // a REC button that gets struck out ("口播也不用录制")
  C.rec = { cues: (sc) => { cue(sc.t0, 'glitch'); cue(sc.strike, 'stamp'); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const x0 = 190, y0 = 520, w = 700, h = 460; glass(c, x0, y0, w, h, 34);
        const blink = Math.sin(t * 9) > -0.2 || t > sc.strike ? 1 : 0.35;
        const dead = local(t, sc.strike, 0.3);
        c.save(); c.globalAlpha *= lerp(1, 0.35, dead);
        icon(c, 'rec', 260, 600, 90, css(RED, blink)); c.font = serif(64, 900); c.fillStyle = col('fg'); c.textBaseline = 'middle'; c.fillText('REC', 380, 646);
        icon(c, 'cam', 640, 585, 130, col('fg', 0.8));
        c.font = serif(50, 800); c.fillStyle = col('fg', 0.85); c.textAlign = 'center'; c.fillText('录制口播', 540, 860); c.restore();
        if (dead > 0) {
          c.save(); c.strokeStyle = css(RED); c.lineWidth = 14; c.lineCap = 'round';
          c.beginPath(); c.moveTo(250, 920); c.lineTo(250 + (830 - 250) * dead, 920 - (920 - 560) * dead); c.stroke();
          const ps = E.outBack(seg(t, sc.strike + 0.1, sc.strike + 0.4), 2.5);
          if (ps > 0) { c.translate(760, 950); c.rotate(-0.12); c.scale(ps, ps); rrect(c, -120, -46, 240, 92, 16); c.fillStyle = css(RED); c.fill(); c.font = serif(52, 900); c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('不用录', 0, 3); }
          c.restore();
        }
      });
    } };

  // a script document typing itself, then sent into a red AI node
  C.doc = { cues: (sc) => { cue(sc.t0, 'card'); cue(sc.t0 + 0.3, 'type'); cue(sc.send, 'send'); cue(sc.send + 0.45, 'node'); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const fly = E.inOutCubic(seg(t, sc.send, sc.send + 0.5));
        const lines = sc.lines;
        c.save();
        const cx = lerp(470, 820, fly), cy = lerp(760, 640, fly), s = lerp(1, 0.18, fly);
        c.translate(cx, cy); c.scale(s, s); c.rotate(fly * 0.3); c.globalAlpha *= 1 - seg(fly, 0.8, 1);
        const w = 620, h = 640; glass(c, -w / 2, -h / 2, w, h, 26);
        icon(c, 'doc', -w / 2 + 34, -h / 2 + 30, 44, css(RED)); c.font = serif(26, 700); c.fillStyle = col('dim'); c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText('脚本.md', -w / 2 + 92, -h / 2 + 54);
        const total = lines.join('').length; const shown = Math.floor(clamp((t - sc.t0 - 0.25) / Math.max(0.6, sc.send - sc.t0 - 0.4)) * total);
        let k = 0; c.font = serif(34, 600);
        lines.forEach((ln, i) => {
          const yy = -h / 2 + 140 + i * 66; const n = clamp(shown - k, 0, ln.length); k += ln.length;
          c.fillStyle = col('fg', 0.12); rrect(c, -w / 2 + 40, yy - 4, (w - 80) * (0.55 + 0.4 * hash(i)), 10, 5); if (n === 0) c.fill();
          c.fillStyle = col('fg', 0.92); c.fillText(ln.slice(0, n), -w / 2 + 40, yy);
          if (n > 0 && n < ln.length && Math.floor(t * 3) % 2 === 0) { const mw = c.measureText(ln.slice(0, n)).width; c.fillStyle = css(RED); c.fillRect(-w / 2 + 44 + mw, yy - 20, 4, 40); }
        });
        c.restore();
        // AI node
        const pn = local(t, sc.send - 0.25, 0.4); if (pn > 0) {
          const pulse = Math.exp(-Math.max(0, t - sc.send - 0.45) * 3) * seg(t, sc.send + 0.4, sc.send + 0.5);
          c.save(); c.globalAlpha *= pn; c.translate(820, 640); c.scale(lerp(0.6, 1, pn) * (1 + pulse * 0.12), lerp(0.6, 1, pn) * (1 + pulse * 0.12));
          c.shadowColor = css(RED, 0.8); c.shadowBlur = 60; const g = c.createRadialGradient(-30, -30, 10, 0, 0, 120); g.addColorStop(0, 'rgb(255,80,96)'); g.addColorStop(1, 'rgb(150,8,28)');
          c.beginPath(); c.arc(0, 0, 112, 0, TAU); c.fillStyle = g; c.fill(); c.shadowBlur = 0;
          c.font = `italic 400 110px ${LATI}`; c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('AI', 0, 8);
          c.restore();
        }
      });
    } };

  // three-step pipeline: step pills on top, one big card whose content changes per step
  C.pipe = { cues: (sc) => { cue(sc.t0, 'card'); sc.steps.forEach((s) => cue(s.at, 'node')); cue(sc.steps[2].at, 'whoosh'); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const steps = sc.steps; let cur = 0; steps.forEach((s, i) => { if (t >= s.at) cur = i; });
        // pills
        const px = [200, 540, 880];
        c.save(); c.strokeStyle = col('line', 0.15); c.lineWidth = 3; c.beginPath(); c.moveTo(px[0], 410); c.lineTo(px[2], 410); c.stroke();
        const prog = steps.reduce((a, s, i) => (i ? a + local(t, s.at, 0.5) : a), 0) / 2;
        c.strokeStyle = css(RED); c.beginPath(); c.moveTo(px[0], 410); c.lineTo(px[0] + (px[2] - px[0]) * prog, 410); c.stroke(); c.restore();
        steps.forEach((s, i) => {
          const on = t >= s.at, p = local(t, s.at, 0.35);
          c.save(); c.translate(px[i], 410); const r = 44 * (1 + 0.15 * Math.exp(-Math.max(0, t - s.at) * 6) * (on ? 1 : 0));
          c.beginPath(); c.arc(0, 0, r, 0, TAU); c.fillStyle = on ? css(RED) : css(TH.card); c.fill(); c.strokeStyle = on ? css(RED) : col('line', 0.2); c.lineWidth = 2; c.stroke();
          icon(c, s.icon, -24, -24, 48, on ? '#fff' : col('dim'));
          c.font = serif(32, 800); c.fillStyle = on ? col('fg') : col('dim'); c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(s.label, 0, 84);
          c.font = serif(22, 600); c.fillStyle = col('dim', on ? 0.9 : 0.5); c.fillText(s.tool, 0, 120);
          c.restore(); void p;
        });
        // big card
        const x0 = 110, y0 = 580, w = 860, h = 520; glass(c, x0, y0, w, h, 28);
        c.save(); rrect(c, x0 + 1, y0 + 1, w - 2, h - 2, 27); c.clip();
        steps.forEach((s, i) => {
          const a = local(t, s.at, 0.3) * (i < steps.length - 1 ? 1 - local(t, steps[i + 1].at - 0.1, 0.25) : 1);
          if (a <= 0) return; c.save(); c.globalAlpha *= a;
          if (s.show === 'doc') {
            c.font = serif(40, 700); c.fillStyle = col('fg', 0.9); c.textAlign = 'left'; c.textBaseline = 'middle';
            ['这条视频是AI帮我剪的。', '镜头切换、加字幕、', 'B-roll素材、动效设计……'].forEach((l, j) => c.fillText(l, x0 + 60, y0 + 120 + j * 90));
            for (let j = 0; j < 3; j++) { c.fillStyle = col('fg', 0.1); rrect(c, x0 + 60, y0 + 380 + j * 30 - 30, 500 + 200 * hash(j), 12, 6); c.fill(); }
          } else if (s.show === 'wave') {
            const mid = y0 + h / 2, rate = peaks.rate, t0 = Math.max(0, t - 3);
            c.strokeStyle = css(RED); c.lineWidth = 6; c.lineCap = 'round'; c.beginPath();
            for (let q = 0; q < 70; q++) { const tt = t0 + q * (3 / 70), v = (peaks.peaks[Math.floor(tt * rate)] || 0) * 170 + 4; const xx = x0 + 50 + q * ((w - 100) / 69); c.moveTo(xx, mid - v); c.lineTo(xx, mid + v); }
            c.stroke(); c.font = serif(26, 700); c.fillStyle = col('dim'); c.textAlign = 'left'; c.fillText('voice-final.wav · 48 kHz', x0 + 50, y0 + h - 40);
          } else if (s.show === 'avatar') {
            const img = media.frame('cam', camIdx(t)); if (img) { const sc2 = Math.max(w / img.width, h / img.height); c.drawImage(img, x0 + (w - img.width * sc2) / 2, y0 + (h - img.height * sc2) / 2, img.width * sc2, img.height * sc2); }
            const pb = local(t, s.at + 0.25, 0.3); c.globalAlpha *= pb; rrect(c, x0 + 30, y0 + 30, 250, 60, 30); c.fillStyle = 'rgba(0,0,0,0.6)'; c.fill();
            icon(c, 'check', x0 + 44, y0 + 40, 40, css(GREEN)); c.font = serif(28, 800); c.fillStyle = '#fff'; c.textBaseline = 'middle'; c.textAlign = 'left'; c.fillText('数字人已生成', x0 + 92, y0 + 61);
          }
          c.restore();
        });
        c.restore();
      });
    } };

  // narrative logic: a red node wired to script rows; each row gets its matched footage
  C.logic = { cues: (sc) => { cue(sc.t0, 'node'); sc.rows.forEach((r, i) => cue(sc.t0 + 0.4 + i * 0.12, 'item', 0.6)); sc.rows.forEach((r, i) => cue(sc.match + i * 0.14, 'snap')); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const nx = 190, ny = 760; const rows = sc.rows;
        rows.forEach((r, i) => {
          const yy = 470 + i * 150, p = local(t, sc.t0 + 0.4 + i * 0.12, 0.45);
          // wire
          c.save(); c.strokeStyle = col('line', 0.25); c.lineWidth = 3; c.beginPath(); c.moveTo(nx + 100, ny);
          const ex = 400; c.bezierCurveTo(nx + 180, ny, ex - 90, yy + 52, lerp(nx + 100, ex, p), lerp(ny, yy + 52, p)); c.stroke(); c.restore();
          blurIn(c, p, () => {
            glass(c, 400, yy, 560, 104, 20);
            c.font = serif(34, 700); c.fillStyle = col('fg', 0.92); c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText(r.text, 430, yy + 52);
            const pm = E.outBack(seg(t, sc.match + i * 0.14, sc.match + i * 0.14 + 0.35), 1.6);
            if (pm > 0) { const im = IMG[r.img]; c.save(); c.globalAlpha *= clamp(pm); c.translate(870, yy + 52); c.scale(pm, pm); rrect(c, -70, -42, 140, 84, 12); c.clip(); if (im) { const s = Math.max(140 / im.width, 84 / im.height); c.drawImage(im, -im.width * s / 2, -im.height * s / 2, im.width * s, im.height * s); } c.restore(); }
          });
        });
        const pn = local(t, sc.t0, 0.4);
        c.save(); c.globalAlpha *= pn; c.translate(nx, ny); c.shadowColor = css(RED, 0.7); c.shadowBlur = 50;
        const g = c.createRadialGradient(-25, -25, 10, 0, 0, 110); g.addColorStop(0, 'rgb(240,60,80)'); g.addColorStop(1, 'rgb(130,6,24)');
        c.beginPath(); c.arc(0, 0, 100, 0, TAU); c.fillStyle = g; c.fill(); c.shadowBlur = 0;
        c.font = serif(34, 900); c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('叙事', 0, -20); c.fillText('逻辑', 0, 22); c.restore();
      });
    } };

  function phone(c, x, y, w, k, t, t0, dot) {
    const h = w * 2.05, r = w * 0.16;
    c.save(); c.shadowColor = 'rgba(0,0,0,0.6)'; c.shadowBlur = 30; c.shadowOffsetY = 12;
    rrect(c, x - w / 2, y - h / 2, w, h, r); c.fillStyle = '#0d0d0f'; c.fill(); c.shadowColor = 'transparent';
    c.strokeStyle = 'rgba(255,255,255,0.22)'; c.lineWidth = 3; c.stroke();
    rrect(c, x - w / 2 + 9, y - h / 2 + 9, w - 18, h - 18, r - 8); c.clip();
    const f = seqFrame(k, t, t0); if (f) { const s = Math.max((w - 18) / f.width, (h - 18) / f.height); c.drawImage(f, x - f.width * s / 2, y - f.height * s / 2, f.width * s, f.height * s); }
    c.restore();
    c.save(); rrect(c, x - w * 0.16, y - h / 2 + 18, w * 0.32, 18, 9); c.fillStyle = '#000'; c.fill(); c.restore();
    if (dot) { c.beginPath(); c.arc(x + w / 2 - 6, y + h / 2 - 6, 14, 0, TAU); c.fillStyle = css(GREEN); c.fill(); c.strokeStyle = col('bg'); c.lineWidth = 4; c.stroke(); }
  }
  C.phones = { cues: (sc) => sc.seqs.forEach((s, i) => cue(sc.t0 + i * 0.14, 'phone')),
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const pos = [[330, 560], [750, 560], [330, 980], [750, 980]];
        sc.seqs.forEach((k, i) => { const p = local(t, sc.t0 + i * 0.14, 0.45); blurIn(c, p, () => phone(c, pos[i][0], pos[i][1] + (i % 2 ? 30 : -10), 190, k, t, sc.t0, true)); });
        const pt = local(t, sc.t0 + 0.5, 0.4); blurIn(c, pt, () => { rrect(c, 380, 740, 320, 76, 38); c.fillStyle = css(RED); c.fill(); c.font = serif(38, 900); c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('社交媒体素材', 540, 780); });
      });
    } };

  // macOS-style window playing a screen recording
  C.window = { cues: (sc) => cue(sc.t0, 'card'),
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const x0 = 70, y0 = 520, w = 940, h = 600; glass(c, x0, y0, w, h, 22, { fill: [30, 30, 34] });
        ['#ff5f57', '#febc2e', '#28c840'].forEach((cc, i) => { c.beginPath(); c.arc(x0 + 34 + i * 30, y0 + 30, 9, 0, TAU); c.fillStyle = cc; c.fill(); });
        c.font = serif(22, 600); c.fillStyle = 'rgba(255,255,255,0.55)'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(sc.label || '我的录屏.mov', 540, y0 + 30);
        const f = seqFrame(sc.seq, t, sc.t0); c.save(); rrect(c, x0 + 12, y0 + 58, w - 24, h - 70, 12); c.clip();
        if (f) { const s = Math.max((w - 24) / f.width, (h - 70) / f.height); const z = 1 + 0.06 * seg(t, sc.t0, sc.t1); c.drawImage(f, x0 + 12 + (w - 24 - f.width * s * z) / 2, y0 + 58 + (h - 70 - f.height * s * z) / 2, f.width * s * z, f.height * s * z); }
        c.restore();
        // cursor
        const cx = lerp(620, 420, E.inOutCubic(seg(t, sc.t0 + 0.4, sc.t0 + 1.4))), cy = lerp(1000, 760, E.inOutCubic(seg(t, sc.t0 + 0.4, sc.t0 + 1.4)));
        c.save(); c.translate(cx, cy); c.beginPath(); c.moveTo(0, 0); c.lineTo(0, 40); c.lineTo(11, 30); c.lineTo(20, 48); c.lineTo(28, 44); c.lineTo(19, 27); c.lineTo(33, 27); c.closePath(); c.fillStyle = '#fff'; c.fill(); c.strokeStyle = '#000'; c.lineWidth = 2; c.stroke(); c.restore();
        rrect(c, 760, y0 + h - 30, 220, 64, 32); c.fillStyle = css(RED); c.fill(); c.font = serif(32, 900); c.fillStyle = '#fff'; c.textAlign = 'center'; c.fillText('我的录屏', 870, y0 + h + 3);
      });
    } };

  // search bar typing → "no results" shake, then an AI generation card that resolves into the clip
  C.search = { cues: (sc) => { cue(sc.t0, 'card'); cue(sc.t0 + 0.15, 'type'); cue(sc.fail, 'error'); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 700, () => {
        const sh = Math.sin((t - sc.fail) * 60) * 14 * Math.exp(-Math.max(0, t - sc.fail) * 7) * (t > sc.fail ? 1 : 0);
        c.save(); c.translate(sh, 0);
        glass(c, 120, 520, 840, 120, 60); icon(c, 'search', 160, 550, 60, col('dim'));
        const q = sc.query, n = Math.floor(clamp((t - sc.t0 - 0.15) / 0.7) * q.length);
        c.font = serif(42, 700); c.fillStyle = col('fg'); c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText(q.slice(0, n), 250, 582);
        c.restore();
        for (let i = 0; i < 6; i++) { const p = local(t, sc.t0 + 0.6 + i * 0.05, 0.3); const x = 120 + (i % 3) * 287, y = 690 + Math.floor(i / 3) * 190;
          blurIn(c, p, () => { rrect(c, x, y, 266, 170, 16); c.fillStyle = col('fg', 0.06); c.fill(); c.strokeStyle = col('line', 0.1); c.lineWidth = 2; c.setLineDash([10, 8]); c.stroke(); c.setLineDash([]); }); }
        const pf = local(t, sc.fail, 0.3); blurIn(c, pf, () => { c.font = serif(44, 900); c.fillStyle = css(RED); c.textAlign = 'center'; c.fillText('未找到合适素材', 540, 875); });
      });
    } };
  C.aigen = { cues: (sc) => { cue(sc.t0, 'shimmer'); cue(sc.reveal, 'ding'); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const x0 = 90, y0 = 500, w = 900, h = 520; glass(c, x0, y0, w, h, 28);
        c.save(); rrect(c, x0 + 14, y0 + 14, w - 28, h - 28, 18); c.clip();
        const f = seqFrame(sc.seq, t, sc.reveal); const r = E.inOutCubic(seg(t, sc.reveal, sc.reveal + 0.6));
        if (f) { const s = Math.max((w - 28) / f.width, (h - 28) / f.height); c.filter = `blur(${((1 - r) * 30).toFixed(1)}px) saturate(${lerp(0.2, 1, r).toFixed(2)})`; c.drawImage(f, x0 + 14 + (w - 28 - f.width * s) / 2, y0 + 14 + (h - 28 - f.height * s) / 2, f.width * s, f.height * s); c.filter = 'none'; }
        // shimmer sweep while generating
        const k = (t - sc.t0) * 1.4 % 1.4; const g = c.createLinearGradient(x0 + (k - 0.4) * w * 1.4, 0, x0 + (k) * w * 1.4, 0);
        g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.5, `rgba(255,255,255,${0.22 * (1 - r)})`); g.addColorStop(1, 'rgba(255,255,255,0)');
        c.fillStyle = `rgba(20,20,24,${0.75 * (1 - r)})`; c.fillRect(x0, y0, w, h); c.fillStyle = g; c.fillRect(x0, y0, w, h);
        if (r < 1) { c.font = serif(30, 700); c.fillStyle = `rgba(255,255,255,${1 - r})`; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(`生成中 ${Math.min(99, Math.floor(seg(t, sc.t0, sc.reveal) * 99))}%`, 540, y0 + h / 2); }
        c.restore();
        const pb = local(t, sc.t0 + 0.2, 0.35); blurIn(c, pb, () => { rrect(c, x0 + 30, y0 - 34, 380, 68, 34); c.fillStyle = css(RED); c.fill(); c.font = serif(32, 900); c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(sc.badge, x0 + 220, y0); });
      });
    } };

  // code editor typing the beat definitions
  C.code = { cues: (sc) => { cue(sc.t0, 'card'); cue(sc.t0 + 0.2, 'type'); cue(sc.t0 + 1.2, 'type', 0.8); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const x0 = 90, y0 = 470, w = 900, h = 640; glass(c, x0, y0, w, h, 24, { fill: [18, 18, 22] });
        ['#ff5f57', '#febc2e', '#28c840'].forEach((cc, i) => { c.beginPath(); c.arc(x0 + 32 + i * 28, y0 + 30, 8, 0, TAU); c.fillStyle = cc; c.fill(); });
        c.font = '600 22px LTMono'; c.fillStyle = 'rgba(255,255,255,0.45)'; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText('beats.json', x0 + 130, y0 + 30);
        const L = sc.lines; const total = L.reduce((a, l) => a + l.length, 0);
        const shown = Math.floor(clamp((t - sc.t0 - 0.2) / (sc.t1 - sc.t0 - 0.6)) * total); let k = 0;
        c.font = '600 30px LTMono';
        L.forEach((ln, i) => {
          const n = clamp(shown - k, 0, ln.length); k += ln.length; const yy = y0 + 100 + i * 50;
          c.fillStyle = 'rgba(255,255,255,0.25)'; c.fillText(String(i + 1).padStart(2, ' '), x0 + 26, yy);
          let xx = x0 + 90; const part = ln.slice(0, n);
          for (const tok of part.split(/("[^"]*"?|[{}\[\],:])/).filter(Boolean)) {
            c.fillStyle = tok.startsWith('"') ? (tok.includes('at:') ? 'rgb(255,120,130)' : 'rgb(152,214,160)') : /[{}\[\],:]/.test(tok) ? 'rgba(255,255,255,0.5)' : 'rgb(130,180,255)';
            c.fillText(tok, xx, yy); xx += c.measureText(tok).width;
          }
          if (n > 0 && n < ln.length) { c.fillStyle = css(RED); c.fillRect(xx + 2, yy - 18, 3, 36); }
        });
      });
    } };

  // words on one lane, animation blocks on another, connectors between: "每一段动画都去匹配口播文字"
  C.sync = { cues: (sc) => { cue(sc.t0, 'card'); sc.pairs.forEach((p, i) => cue(sc.t0 + 0.5 + i * 0.32, 'snap')); cue(sc.t1 - 0.6, 'ding', 0.7); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const x0 = 80, y0 = 480, w = 920, h = 600; glass(c, x0, y0, w, h, 28);
        c.font = serif(22, 700); c.fillStyle = col('dim'); c.textAlign = 'left'; c.textBaseline = 'middle';
        c.fillText('口播 · 字', x0 + 36, y0 + 60); c.fillText('动效 · 帧', x0 + 36, y0 + 380);
        sc.pairs.forEach((pr, i) => {
          const at = sc.t0 + 0.5 + i * 0.32, p = local(t, at - 0.2, 0.35), q = local(t, at, 0.35);
          const bx = x0 + 50 + i * 215, bw = 190;
          blurIn(c, p, () => { rrect(c, bx, y0 + 100, bw, 90, 18); c.fillStyle = col('fg', 0.08); c.fill(); c.font = serif(38, 800); c.fillStyle = col('fg'); c.textAlign = 'center'; c.fillText(pr.word, bx + bw / 2, y0 + 147); });
          c.save(); c.strokeStyle = css(RED, q); c.lineWidth = 3; c.setLineDash([8, 8]); c.beginPath(); c.moveTo(bx + bw / 2, y0 + 192); c.lineTo(bx + bw / 2, y0 + 192 + 220 * q); c.stroke(); c.restore();
          blurIn(c, q, () => { rrect(c, bx, y0 + 420, bw, 120, 18); c.fillStyle = css(RED, 0.9); c.fill(); icon(c, pr.icon, bx + bw / 2 - 30, y0 + 432, 60, '#fff'); c.font = serif(26, 800); c.fillStyle = '#fff'; c.textAlign = 'center'; c.fillText(pr.fx, bx + bw / 2, y0 + 518); });
          c.save(); c.globalAlpha *= q; c.translate(bx + bw / 2, y0 + 420); c.rotate(Math.PI / 4); c.fillStyle = '#fff'; c.fillRect(-9, -9, 18, 18); c.restore();
        });
      });
    } };

  // sound lane: effect blocks with their waveforms, each one heard as it lands
  C.sfxlane = { cues: (sc) => { cue(sc.t0, 'card', 0.6); sc.fx.forEach((f) => cues.push({ t: f.at, id: f.id, gain: f.gain ?? 0.6 })); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const x0 = 80, y0 = 500, w = 920, h = 560; glass(c, x0, y0, w, h, 28);
        c.font = serif(22, 700); c.fillStyle = col('dim'); c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText('V · 动效', x0 + 36, y0 + 52); c.fillText('A · 音效', x0 + 36, y0 + 300);
        sc.fx.forEach((f, i) => {
          const bx = x0 + 50 + i * 215, bw = 190, p = local(t, f.at - 0.15, 0.3), q = local(t, f.at, 0.2);
          blurIn(c, p, () => { rrect(c, bx, y0 + 90, bw, 130, 18); c.fillStyle = col('fg', 0.08); c.fill(); c.font = serif(34, 800); c.fillStyle = col('fg'); c.textAlign = 'center'; c.fillText(f.fx, bx + bw / 2, y0 + 155); });
          const flash = Math.exp(-Math.max(0, t - f.at) * 4) * (t >= f.at ? 1 : 0);
          blurIn(c, q, () => {
            rrect(c, bx, y0 + 340, bw, 150, 18); c.fillStyle = css(mixc(GREEN, [255, 255, 255], flash * 0.5), 0.25 + 0.5 * flash); c.fill();
            c.strokeStyle = css(GREEN); c.lineWidth = 4; c.lineCap = 'round'; c.beginPath();
            for (let qq = 0; qq < 16; qq++) { const env2 = Math.exp(-qq * f.decay), v = 6 + 50 * env2 * (0.4 + 0.6 * hash(qq, i)); const xx = bx + 18 + qq * 10.5; c.moveTo(xx, y0 + 415 - v); c.lineTo(xx, y0 + 415 + v); }
            c.stroke(); c.font = serif(22, 700); c.fillStyle = col('fg', 0.8); c.textAlign = 'center'; c.fillText(f.label, bx + bw / 2, y0 + 520);
          });
        });
      });
    } };

  // music library: rows, one gets picked, equaliser plays
  C.music = { cues: (sc) => { cue(sc.t0, 'card'); sc.tracks.forEach((r, i) => cue(sc.t0 + 0.3 + i * 0.1, 'item', 0.4)); cue(sc.pick, 'hot'); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const x0 = 110, y0 = 450, w = 860, h = 690; glass(c, x0, y0, w, h, 28);
        icon(c, 'music', x0 + 40, y0 + 36, 46, css(RED)); c.font = serif(36, 900); c.fillStyle = col('fg'); c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText('Epidemic Sound', x0 + 104, y0 + 60);
        const pick = t >= sc.pick;
        sc.tracks.forEach((r, i) => {
          const yy = y0 + 130 + i * 108, p = local(t, sc.t0 + 0.3 + i * 0.1, 0.35), on = pick && i === sc.chosen;
          blurIn(c, p, () => {
            if (on) { rrect(c, x0 + 20, yy, w - 40, 92, 18); c.fillStyle = css(RED, 0.16); c.fill(); c.strokeStyle = css(RED); c.lineWidth = 2; c.stroke(); }
            c.fillStyle = on ? css(RED) : col('fg', 0.1); rrect(c, x0 + 40, yy + 14, 64, 64, 12); c.fill();
            if (on) { c.fillStyle = '#fff'; for (let b = 0; b < 4; b++) { const v = 10 + 22 * Math.abs(Math.sin(t * 8 + b * 1.7)); c.fillRect(x0 + 52 + b * 11, yy + 62 - v, 7, v); } }
            c.font = serif(36, 800); c.fillStyle = on ? css(RED) : col('fg'); c.fillText(r.title, x0 + 130, yy + 34);
            c.font = serif(22, 600); c.fillStyle = col('dim'); c.fillText(r.meta, x0 + 130, yy + 70);
            if (!on && pick) { c.fillStyle = col('bg', 0.5); c.fillRect(x0 + 20, yy, w - 40, 92); }
          });
        });
      });
    } };

  // QA gate (light theme): a film strip being scanned, then three checks and a loudness meter
  C.gate = { cues: (sc) => { cue(sc.scan, 'scan'); sc.checks.forEach((k) => cue(k.at, 'check')); cue(sc.meter, 'ding', 0.6); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        // strip
        const p0 = local(t, sc.t0, 0.4); blurIn(c, p0, () => {
          for (let i = 0; i < 6; i++) { const im = IMG[`t${i + 2}`]; const x = 90 + i * 152; rrect(c, x, 360, 140, 200, 12); c.save(); c.clip(); if (im) { const s = Math.max(140 / im.width, 200 / im.height); c.drawImage(im, x + 70 - im.width * s / 2, 460 - im.height * s / 2, im.width * s, im.height * s); } c.restore(); }
          const sx = 90 + 912 * clamp((t - sc.scan) / 1.3); if (t >= sc.scan) { c.fillStyle = css(RED); c.fillRect(sx - 2, 345, 4, 230); const g = c.createLinearGradient(sx - 120, 0, sx, 0); g.addColorStop(0, css(RED, 0)); g.addColorStop(1, css(RED, 0.25)); c.fillStyle = g; c.fillRect(sx - 120, 360, 120, 200); }
        });
        sc.checks.forEach((k, i) => {
          const yy = 610 + i * 130, p = local(t, k.at - 0.1, 0.35), q = E.outBack(seg(t, k.at, k.at + 0.3), 2);
          blurIn(c, p, () => {
            glass(c, 140, yy, 800, 108, 24, { shadow: 0.12 });
            icon(c, k.icon, 180, yy + 26, 56, col('fg', 0.8)); c.font = serif(40, 800); c.fillStyle = col('fg'); c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText(k.text, 270, yy + 56);
            if (q > 0) { c.save(); c.translate(870, yy + 54); c.scale(q, q); c.beginPath(); c.arc(0, 0, 32, 0, TAU); c.fillStyle = css(GREEN); c.fill(); icon(c, 'check', -22, -22, 44, '#fff'); c.restore(); }
          });
        });
        const pm = local(t, sc.meter - 0.2, 0.4); blurIn(c, pm, () => {
          const y = 1010, x0 = 140, w = 800; c.font = serif(24, 700); c.fillStyle = col('dim'); c.textAlign = 'left'; c.fillText('LOUDNESS', x0, y - 26);
          const zones = [[-30, -20, [180, 180, 186]], [-20, -14, GREEN], [-14, -6, [240, 170, 40]], [-6, 0, RED]];
          const X = (db) => x0 + (db + 30) / 30 * w; zones.forEach(([a, b, cc]) => { c.fillStyle = css(cc, 0.85); c.fillRect(X(a), y, X(b) - X(a) - 3, 26); });
          const v = lerp(-29, -16, E.outCubic(seg(t, sc.meter, sc.meter + 0.8))) + Math.sin(t * 13) * 0.4 * seg(t, sc.meter + 0.8, sc.meter + 1);
          c.fillStyle = col('fg'); c.beginPath(); c.moveTo(X(v), y - 4); c.lineTo(X(v) - 12, y - 22); c.lineTo(X(v) + 12, y - 22); c.fill(); c.fillRect(X(v) - 2, y - 4, 4, 34);
          c.font = serif(30, 800); c.textAlign = 'right'; c.fillStyle = css(GREEN); c.fillText(`${v.toFixed(1)} LUFS`, x0 + w, y - 26);
        });
      });
    } };

  // thumbnails orbit, then pour into a silhouette of the speaker; a lock closes; a red stamp lands
  C.orbit = { cues: (sc) => { cue(sc.t0, 'riser', 0.7); cue(sc.feed, 'whoosh'); for (let i = 0; i < 12; i++) cue(sc.feed + 0.1 + i * 0.07, 'snap', 0.35); cue(sc.lock, 'lock'); cue(sc.stamp, 'stamp'); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const cx = 540, cy = 760, R0 = 330;   // ring kept below the header (top ≈ y 316) and above the caption
        // disc + silhouette
        const pd = local(t, sc.t0, 0.5);
        c.save(); c.globalAlpha *= pd; c.shadowColor = 'rgba(255,255,255,0.55)'; c.shadowBlur = 80; c.beginPath(); c.arc(cx, cy, 175, 0, TAU); c.fillStyle = '#f4f3ef'; c.fill(); c.restore();
        const img = media.frame('cam', camIdx(t)), m = media.frame('mask', camIdx(t));
        if (img && m && pd > 0) {
          const s = 380 / (FACE.h * SH) * 0.55, dw = SW * s, dh = SH * s, fx = cx - (FACE.x + FACE.w / 2) * SW * s, fy = cy - 60 - (FACE.y + FACE.h * 0.5) * SH * s;
          tmpc.setTransform(1, 0, 0, 1, 0, 0); tmpc.globalCompositeOperation = 'source-over'; tmpc.clearRect(0, 0, W, H);
          tmpc.fillStyle = '#0b0b0d'; tmpc.fillRect(0, 0, W, H); tmpc.globalCompositeOperation = 'destination-in'; tmpc.drawImage(m, fx, fy, dw, dh);
          tmpc.globalCompositeOperation = 'destination-in'; tmpc.beginPath(); tmpc.rect(0, 0, W, cy + 240); tmpc.fill(); tmpc.globalCompositeOperation = 'source-over';
          c.save(); c.globalAlpha *= pd; c.drawImage(tmp, 0, 0);
          // red glow "brain" — the style being learnt
          const fed = seg(t, sc.feed, sc.lock); const g = c.createRadialGradient(cx, cy - 70, 4, cx, cy - 70, 90); g.addColorStop(0, css(RED, 0.9 * fed)); g.addColorStop(1, css(RED, 0));
          c.globalCompositeOperation = 'lighter'; c.fillStyle = g; c.beginPath(); c.arc(cx, cy - 70, 90, 0, TAU); c.fill(); c.restore();
        }
        for (let i = 0; i < 12; i++) {
          const im = IMG[`t${i}`]; if (!im) continue;
          const a0 = i / 12 * TAU + (t - sc.t0) * 0.5, p = local(t, sc.t0 + 0.1 + i * 0.05, 0.4);
          const feed = E.inCubic(seg(t, sc.feed + i * 0.07, sc.feed + i * 0.07 + 0.45));
          const r = lerp(R0 + 40 * hash(i), 30, feed), x = cx + Math.cos(a0) * r, y = cy + Math.sin(a0) * r * 0.92;
          const w = lerp(130, 30, feed), h = w * 1.6;
          c.save(); c.globalAlpha *= p * (1 - seg(feed, 0.85, 1)); c.translate(x, y); c.rotate((hash(i, 3) - 0.5) * 0.4);
          rrect(c, -w / 2, -h / 2, w, h, 10); c.clip(); const s = Math.max(w / im.width, h / im.height); c.drawImage(im, -im.width * s / 2, -im.height * s / 2, im.width * s, im.height * s); c.restore();
        }
        // lock ring
        const pl = E.inOutCubic(seg(t, sc.lock - 0.1, sc.lock + 0.35));
        if (pl > 0) { c.save(); c.strokeStyle = css(RED); c.lineWidth = 8; c.lineCap = 'round'; c.beginPath(); c.arc(cx, cy, 205, -Math.PI / 2, -Math.PI / 2 + TAU * pl); c.stroke();
          const q = E.outBack(seg(t, sc.lock + 0.25, sc.lock + 0.55), 2.5); if (q > 0) { c.translate(cx, cy - 205); c.scale(q, q); c.beginPath(); c.arc(0, 0, 44, 0, TAU); c.fillStyle = css(RED); c.fill(); icon(c, 'lock', -26, -28, 52, '#fff'); } c.restore(); }
        const ps = E.outBack(seg(t, sc.stamp, sc.stamp + 0.3), 2.2);
        if (ps > 0) { c.save(); c.translate(cx, cy + 300); c.rotate(-0.06); c.scale(lerp(1.6, 1, clamp(ps)), lerp(1.6, 1, clamp(ps))); c.globalAlpha *= clamp(ps * 1.5);
          rrect(c, -250, -66, 500, 132, 18); c.strokeStyle = css(RED); c.lineWidth = 6; c.stroke();
          c.font = `900 76px ${ZHSERIF}`; c.fillStyle = css(RED); c.textAlign = 'center'; c.textBaseline = 'middle'; c.transform(1, 0, -0.2, 1, 0, 0); c.fillText(sc.stampText, 0, 4); c.restore(); }
      });
    } };

  // files gathered into a group chat
  C.files = { cues: (sc) => { sc.files.forEach((f) => cue(f.at, 'card', 0.8)); cue(sc.group, 'send'); cue(sc.group + 0.5, 'notify'); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        const gp = E.inOutCubic(seg(t, sc.group, sc.group + 0.55));
        sc.files.forEach((f, i) => {
          const p = local(t, f.at, 0.4); const bx = lerp(150 + i * 400, 540, gp), by = lerp(560, 930, gp), s = lerp(1, 0.2, gp);
          c.save(); c.globalAlpha *= p * (1 - seg(gp, 0.85, 1)); c.translate(bx + 170, by + 190); c.scale(s, s); c.rotate(lerp((i ? 1 : -1) * 0.05, 0, p) + gp * (i ? 0.5 : -0.5));
          glass(c, -170, -190, 340, 380, 24); icon(c, f.icon, -50, -150, 100, i ? css(RED) : col('fg'));
          c.font = serif(34, 700); c.fillStyle = col('fg'); c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(f.name, 0, 10);
          for (let j = 0; j < 4; j++) { c.fillStyle = col('fg', 0.1); rrect(c, -120, 60 + j * 28, 240 * (0.5 + 0.5 * hash(j, i)), 10, 5); c.fill(); }
          c.restore();
        });
        const pg = local(t, sc.group + 0.25, 0.4);
        blurIn(c, pg, () => {
          glass(c, 240, 830, 600, 220, 30); c.beginPath(); c.arc(340, 940, 62, 0, TAU); c.fillStyle = css(RED); c.fill();
          c.font = serif(54, 900); c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('群', 340, 943);
          c.font = serif(40, 900); c.fillStyle = col('fg'); c.textAlign = 'left'; c.fillText('AI 剪辑交流群', 430, 905);
          c.font = serif(30, 600); c.fillStyle = col('dim'); c.fillText('[文件] 提示词.md · SKILL.md', 430, 965);
          const pb = E.outBack(seg(t, sc.group + 0.5, sc.group + 0.8), 3); if (pb > 0) { c.save(); c.translate(800, 845); c.scale(pb, pb); c.beginPath(); c.arc(0, 0, 30, 0, TAU); c.fillStyle = css(RED); c.fill(); c.font = serif(30, 900); c.fillStyle = '#fff'; c.textAlign = 'center'; c.fillText('2', 0, 2); c.restore(); }
        });
      });
    } };

  // comment bubbles stacking (illustrative topics, no names or numbers)
  C.comments = { cues: (sc) => { cue(sc.t0, 'card', 0.6); sc.items.forEach((k) => cue(k.at, 'notify', 0.7)); },
    draw(c, t, sc) {
      env(c, t, sc, 540, 760, () => {
        sc.items.forEach((k, i) => {
          const p = local(t, k.at, 0.4), yy = 420 + i * 170;
          blurIn(c, p, () => {
            glass(c, 120 + (i % 2) * 60, yy, 780, 140, 34); c.beginPath(); c.arc(200 + (i % 2) * 60, yy + 70, 40, 0, TAU); c.fillStyle = col('fg', 0.12); c.fill();
            icon(c, 'user', 176 + (i % 2) * 60, yy + 46, 48, col('dim'));
            c.font = serif(40, 800); c.fillStyle = col('fg'); c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText(k.text, 270 + (i % 2) * 60, yy + 72);
          });
        });
      });
    } };

  // ───────── cues (sound) ─────────
  for (let i = 1; i < LAY.length; i++) cue(LAY[i].t, 'layout');
  for (const ti of TITLES) cue(ti.from, 'title');
  for (const x of CTA) { cue(x.at, 'impact'); }
  for (const sc of SCENES) { const comp = C[sc.kind]; if (!comp) throw new Error(`unknown scene kind ${sc.kind}`); if (sc.sfx) sc.sfx.forEach(([id, g, dt = 0]) => cues.push({ t: sc.t0 + dt, id, gain: g })); else comp.cues?.(sc); }

  function needs(f) {
    const t = f / FPS, list = [['cam', camIdx(t)]];
    const u = layoutU(t);
    if (u < 0.98 || SCENES.some((s) => s.kind === 'orbit' && t >= s.t0 - 0.2 && t <= s.t1 + 0.2)) list.push(['mask', camIdx(t)]);
    for (const sc of SCENES) {
      if (t < sc.t0 - 0.1 || t > sc.t1 + 0.1) continue;
      const seqs = sc.seqs || (sc.seq ? [sc.seq] : []);
      for (const k of seqs) { const n = lib.seq[k]; if (n) { const t0 = sc.kind === 'aigen' ? sc.reveal : sc.t0; list.push([k, seqIdx(n, t, t0)]); } }
    }
    return list;
  }

  return {
    frames: NF, fps: FPS,
    async prepare(f) { await media.need(needs(f)); },
    prefetch(f) { media.prefetch(needs(f)); },
    samples(f) { const t = f / FPS; return LAY.some((L) => Math.abs(t - L.t) < 0.4) ? 2 : 1; },
    draw(c, t, f, tf) {
      const k = themeK(tf); TH = { ...THEMES.dark }; for (const key of ['bg', 'fg', 'dim', 'card', 'line']) TH[key] = mixc(THEMES.dark[key], THEMES.light[key], k); TH.grid = lerp(THEMES.dark.grid, THEMES.light.grid, k);
      drawBg(c, t);
      const u = layoutU(t);
      if (u < 0.999) {
        c.save(); c.globalAlpha = 1 - E.inCubic(clamp(u * 1.6));
        drawTitle(c, t);
        for (const sc of SCENES) if (t >= sc.t0 - 0.05 && t <= sc.t1 + 0.05) C[sc.kind].draw(c, t, sc);
        c.restore();
      }
      drawPerson(c, t, tf, u);
      if (u > 0.5) drawCTA(c, t);
      if (SHOW_CAPTIONS) drawCaption(c, tf, u);
    },
    post() { return { bloom: 0.12, thresh: 0.9, grain: 0.022, vig: 0.12, ca: 0.4, shoulder: 0 }; },
    cues: () => cues.sort((a, b) => a.t - b.t).map((q) => ({ ...q, t: Math.round(q.t * 1000) / 1000 })),
    qa(f) { const t = f / FPS, u = layoutU(t), boxes = QA.boxes.slice(); QA.boxes = [];
      return { u: Math.round(u * 100) / 100, face: faceBox(u > 0.5 ? 1 : 0).map((v) => Math.round(v)), boxes }; },
  };
}
