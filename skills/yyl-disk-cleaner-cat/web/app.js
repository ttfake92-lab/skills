/* app.js — 像素小猫清理页
 * 左：canvas 像素公寓（room.png 背景）+ 沿确认路线打扫的蓝白小猫
 * 右：清理清单（学到的安全类别预勾选）+ 永久删除确认
 * SSE 实时进度 → 小猫走到对应房间的垃圾堆打扫，堆随真实删除缩小、扫完变干净
 */
(() => {
'use strict';

// ---------------------------------------------------------------- 工具
const $ = (s, r = document) => r.querySelector(s);
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;

// Quiet Place 色板：薄荷绿 / 奶油 / 森林绿 + 珊瑚红强调
const CREAM = '#eef0e2', CREAMHI = '#f6f7ee', MINT = '#d3e3d7', MINT2 = '#c2d8c8',
      SAGE = '#9fbfa6', SAGE_D = '#6b8f7a', SAGE_DD = '#4a6b57',
      FOREST = '#2e4a3d', LINE = '#34433b', CORAL = '#e5897c', CORAL_D = '#d4756a', WATER = '#a7c5bd';
// 蓝白英短猫色
const C_GREY = '#9aa7ad', C_GREY_D = '#7c8a90', C_WHITE = '#f4f3ea', C_WHITE_D = '#d8d9cc',
      C_PINK = '#e3a0a4', C_OUT = '#3f4a44', C_EYE = '#33403a';
const WOOD = '#a98d63', WOOD_D = '#80623e';

const CAT_META = {
  dev_caches:    { label: '开发者缓存', color: SAGE_D },
  system_caches: { label: '系统缓存',   color: SAGE_DD },
  large_files:   { label: '大文件',     color: CORAL },
};
// 像素公寓四间房 → 主题色（背景用 room.png，垃圾按主题画）
const ROOM_THEME = { office: 'dev', server: 'system', living: 'download', bedroom: 'large' };
const THEME_COLOR = { dev: SAGE_D, system: SAGE_DD, download: '#cdb37a', large: CORAL };
// 每个清理项归到哪个房间：开发缓存→办公室、系统缓存→机房、大文件(下载→客厅 / 其余→卧室)
const ITEM_ROOM = {};
function itemRoom(it) {
  if (it.category === 'dev_caches') return 'office';
  if (it.category === 'system_caches') return 'server';
  const p = ((it.detail || '') + ' ' + (it.paths || []).join(' ')).toLowerCase();
  return /download|下载/.test(p) ? 'living' : 'bedroom';
}

// 模拟预览：默认关闭（正式版真实扫描 + 真实删除）。在网址后加 ?demo=1 即进入安全模拟：
// 全程假数据 + 假删除，只看小猫打扫动画，绝不碰真实文件。
const DEMO = new URLSearchParams(location.search).has('demo');

let SCAN = null;
let selectedSizes = {};   // id -> size
const piles = {};         // roomId -> {total, remaining, theme, color}

// ---------------------------------------------------------------- 数据加载
async function loadScan() {
  if (DEMO) {
    SCAN = demoScan();             // 模拟模式：直接用假数据，不碰真实扫描
  } else {
    try {
      const r = await fetch('/api/scan');
      if (!r.ok) throw new Error('bad');
      SCAN = await r.json();
      if (!SCAN || !SCAN.cleanable) throw new Error('empty');
    } catch (e) {
      SCAN = demoScan();           // 离线/直开文件时的演示数据
    }
  }
  renderMemo();
  renderDisk();
  renderLists();
  renderAdvisories();
  buildPiles();
  if (DEMO) {
    const w = $('#reviewWarn');
    if (w) { w.textContent = '🐱 模拟演示：这是假数据，点「开始打扫」只看小猫走房间的动画，不会删除任何文件。'; w.classList.remove('warn'); w.classList.add('demo-note'); }
  }
}

function demoScan() {
  const mk = (id, cat, label, size, checked, detail) => ({ id, category: cat, label, size, paths: ['~/demo'], detail, checked, auto_default: checked, deletable: true });
  return {
    disk: { total_h: '926GB', used_h: '705GB', avail_h: '221GB', used_pct: 76 },
    memory_summary: { runs: 3, last: '2026-06-18T10:20:00', total_freed_h: '12.4GB' },
    total_reclaimable_h: '8.2GB', pre_checked_h: '6.1GB',
    cleanable: {
      dev_caches: { label: '开发者缓存', items: [
        mk('dev:npm', 'dev_caches', 'npm 缓存', 2.1e9, true, '~/.npm/_cacache'),
        mk('dev:xcode_dd', 'dev_caches', 'Xcode DerivedData', 3.4e9, true, '~/Library/Developer/Xcode/DerivedData'),
        mk('dev:brew', 'dev_caches', 'Homebrew 缓存', 0.6e9, true, '~/Library/Caches/Homebrew'),
      ]},
      system_caches: { label: '系统与应用缓存', items: [
        mk('sys:cache:Chrome', 'system_caches', '应用缓存 · Google', 0.9e9, true, '~/Library/Caches/Google'),
        mk('sys:trash', 'system_caches', '废纸篓', 0.4e9, true, '~/.Trash'),
      ]},
      large_files: { label: '大文件与下载', items: [
        // 模拟模式下默认也勾上，好让小猫把客厅 / 卧室也走一遍（真实版大文件仍需手动勾）
        mk('big:dl', 'large_files', 'project-final-v3.mov', 1.8e9, DEMO, '~/Downloads/project-final-v3.mov，120 天未动'),
        mk('big:mov', 'large_files', 'old-render.mov', 2.3e9, DEMO, '~/Movies/old-render.mov，很久没看了'),
      ]},
    },
    advisories: {
      performance: { label: '性能优化建议', items: [
        { title: '内存压力', level: 'bad', body: '已用 23.3GB / 共 24.0GB · swap 占用 4.5GB', hint: '内存吃紧（swap 偏高，已在压硬盘）。注：『清内存』在 macOS 上无效，不做。' },
        { title: '资源占用大户', level: 'info', body: '下面这些最吃 CPU / 内存，确认不用就自己关掉，能立刻变快：', rows: [
          { label: 'Google Chrome Helper', sub: 'CPU 22.4%' }, { label: 'WindowServer', sub: 'CPU 18.1%' }, { label: 'Photos', sub: '内存 1.2GB' },
        ] },
        { title: '后台自启（2 个 · 可一键禁用）', level: 'warn', body: '后台常驻、吃内存与电。确认无用可禁用——只是挪开、随时还原，不删除：', rows: [
          { label: 'com.google.keystone.agent', sub: '用户级常驻', action: { type: 'disable_agent', target: '~/Library/LaunchAgents/com.google.keystone.agent.plist' } },
          { label: 'com.github.syncthing', sub: '用户级常驻', action: { type: 'disable_agent', target: '~/Library/LaunchAgents/com.github.syncthing.plist' } },
        ] },
      ]},
      network: { label: '网络优化建议', items: [
        { title: 'DNS 实测延迟', level: 'warn', body: '当前 192.168.1.1：38ms', rows: [
          { label: '223.5.5.5 阿里', sub: '9ms' }, { label: '1.1.1.1 Cloudflare', sub: '12ms' }, { label: '8.8.8.8 Google', sub: '21ms' },
        ], hint: '实测最快是 223.5.5.5（9ms）。切换需管理员，命令如右：', command: 'networksetup -setdnsservers "Wi-Fi" 223.5.5.5 1.1.1.1' },
        { title: '网络延迟 / 丢包', level: 'ok', body: '外网延迟 41ms · 丢包 0% · 到路由器 3ms', hint: '丢包高或延迟大：靠近路由器、换 5GHz、或重启路由器。' },
        { title: '刷新 DNS 缓存', level: 'action', body: '网页解析错乱时常能解决', command: 'sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder', hint: '需输入开机密码，终端手动执行。' },
      ]},
    },
  };
}

// ---------------------------------------------------------------- 渲染：信息区
function renderMemo() {
  const m = SCAN.memory_summary || {};
  const last = m.last ? new Date(m.last).toLocaleDateString('zh-CN') : '从未';
  $('#memo').innerHTML = `已清理 <b>${m.runs || 0}</b> 次 · 累计释放 <b>${m.total_freed_h || '0B'}</b> · 上次：${last}`;
}
function renderDisk() {
  const d = SCAN.disk || {};
  $('#diskCard').innerHTML =
    `<div class="disk-title">磁盘占用 ${d.used_pct ?? '—'}%</div>
     <div class="disk-bar"><div class="disk-used" style="width:${d.used_pct || 0}%"></div></div>
     <div class="disk-meta"><span>已用 ${d.used_h || '—'}</span><span>可用 ${d.avail_h || '—'}</span></div>`;
}

// ---------------------------------------------------------------- 渲染：清理清单
function renderLists() {
  const wrap = $('#cleanLists'); wrap.innerHTML = '';
  selectedSizes = {};
  for (const [cat, group] of Object.entries(SCAN.cleanable)) {
    if (!group.items.length) continue;
    const gsize = group.items.reduce((s, i) => s + i.size, 0);
    const g = el('div', 'cat-group');
    g.appendChild(el('h4', null, `<span>${dotFor(cat)} ${group.label}</span><span class="gsize">${human(gsize)}</span>`));
    for (const it of group.items) {
      const row = el('label', 'row');
      row.dataset.id = it.id; row.dataset.cat = cat;
      const cb = el('input'); cb.type = 'checkbox'; cb.checked = !!it.checked;
      if (it.checked) selectedSizes[it.id] = it.size;
      cb.addEventListener('change', () => {
        if (cb.checked) selectedSizes[it.id] = it.size; else delete selectedSizes[it.id];
        updateSelSum();
      });
      row.appendChild(cb);
      row.appendChild(el('span', 'lbl', `${escapeHtml(it.label)}<small>${escapeHtml(it.detail || '')}</small>`));
      row.appendChild(el('span', 'sz', human(it.size)));
      g.appendChild(row);
    }
    wrap.appendChild(g);
  }
  $('#reclaimTotal').textContent = `可释放 ${SCAN.total_reclaimable_h}`;
  updateSelSum();
}
function dotFor(cat) {
  const c = CAT_META[cat] ? CAT_META[cat].color : '#7bdff2';
  return `<span class="dot" style="background:${c};width:9px;height:9px;display:inline-block"></span>`;
}
function updateSelSum() {
  const ids = Object.keys(selectedSizes);
  const total = ids.reduce((s, id) => s + selectedSizes[id], 0);
  $('#selSum').textContent = ids.length ? `已选 ${ids.length} 项，约释放 ${human(total)}` : '未勾选任何项目';
  $('#startBtn').disabled = ids.length === 0;
}

// ---------------------------------------------------------------- 渲染：建议
function renderAdvisories() {
  const host = $('#advisories'); host.innerHTML = '';
  for (const adv of Object.values(SCAN.advisories || {})) {
    if (!adv.items || !adv.items.length) continue;
    const card = el('div', 'adv-col');
    card.appendChild(el('h3', null, adv.label));
    for (const it of adv.items) {
      const node = el('div', 'adv-item');
      node.appendChild(el('div', 'at', `<span class="dot ${it.level || 'info'}"></span>${escapeHtml(it.title)}`));
      if (it.body) node.appendChild(el('div', 'ab', escapeHtml(it.body)));
      if (it.hint) node.appendChild(el('div', 'ah', escapeHtml(it.hint)));
      if (it.rows && it.rows.length) {
        const list = el('div', 'adv-rows');
        for (const r of it.rows) {
          const row = el('div', 'adv-row');
          row.appendChild(el('span', 'arl', `${escapeHtml(r.label)}${r.sub ? `<small>${escapeHtml(r.sub)}</small>` : ''}`));
          if (r.action) {
            const enable = r.action.type === 'enable_agent';
            const btn = el('button', 'mini-btn' + (enable ? ' alt' : ''), enable ? '还原' : '禁用');
            btn.addEventListener('click', () => doAction(r, btn, row));
            row.appendChild(btn);
          }
          list.appendChild(row);
        }
        node.appendChild(list);
      }
      if (it.command) {
        const c = el('div', 'cmd', escapeHtml(it.command) + '  📋');
        c.title = '点击复制';
        c.addEventListener('click', () => { navigator.clipboard?.writeText(it.command); c.innerHTML = escapeHtml(it.command) + '  ✓ 已复制'; });
        node.appendChild(c);
      }
      card.appendChild(node);
    }
    host.appendChild(card);
  }
}

// 性能板块的安全一键（禁用/还原用户级自启）
async function doAction(r, btn, row) {
  const enable = r.action.type === 'enable_agent';
  const verb = enable ? '还原' : '禁用';
  if (!confirm(`${verb} ${r.label}？\n${enable ? '会重新加载这个后台自启。' : '只是挪开（不删除），随时能在「已禁用」里还原。'}`)) return;
  btn.disabled = true; btn.textContent = '…';
  try {
    const res = await fetch('/api/action', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(r.action) });
    const j = await res.json();
    if (j.ok) { row.classList.add('row-done'); btn.textContent = enable ? '已还原' : '已禁用'; log('ok', j.message); }
    else { btn.disabled = false; btn.textContent = verb; log('err', j.message || '操作失败'); }
  } catch (e) {
    btn.disabled = false; btn.textContent = verb; log('err', '操作失败（小猫服务未连接）');
  }
}

// ---------------------------------------------------------------- 垃圾堆
function buildPiles() {
  for (const k in piles) delete piles[k];
  const acc = {};
  for (const group of Object.values(SCAN.cleanable))
    for (const it of group.items) {
      const rid = itemRoom(it); ITEM_ROOM[it.id] = rid;
      acc[rid] = (acc[rid] || 0) + it.size;
    }
  for (const rid of ['office', 'living', 'server', 'bedroom']) {
    const tot = acc[rid] || 0;
    if (tot > 0) piles[rid] = { total: tot, remaining: tot, theme: ROOM_THEME[rid], color: THEME_COLOR[ROOM_THEME[rid]] };
  }
}

// ================================================================ 像素动画（room.png 背景 + 路线驱动的小猫）
const canvas = $('#room'), ctx = canvas.getContext('2d');
ctx.imageSmoothingEnabled = false;
const W = canvas.width, H = canvas.height;             // 960 x 540
const ROOM_W = 2048, ROOM_H = 1152, SC = W / ROOM_W;   // room.png → 画布缩放
const rx = v => v * SC;                                 // room 坐标 → 画布坐标

// 背景图（room.png）
const roomImg = new Image();
let bgReady = false;
roomImg.onload = () => { bgReady = true; };
roomImg.src = '/room.png';

// 墙体图层（与原图等尺寸的透明 PNG，直接整张盖到最顶层，无需对位）
const WALL_SRCS = ['/room1-2.png', '/room2-3.png', '/room2-4.png'];
const wallImgs = WALL_SRCS.map(src => { const im = new Image(); im.src = src; return im; });
function drawWalls() {
  for (const im of wallImgs) if (im.complete && im.naturalWidth) ctx.drawImage(im, 0, 0, W, H);
}

// ---- 关键坐标（room.png 像素系，已逐版确认的路线）----
const PT = {
  home: [110, 855], office: [470, 800], living: [960, 775], server: [1490, 500], bedroom: [1480, 955],
  opU: [635, 495], dA: [1350, 460], dB: [1360, 720],
  mUp: [240, 800], mOL: [810, 745], mLS: [1180, 700], mLB: [1300, 700],
};
const SPOT = { office: PT.office, living: PT.living, server: PT.server, bedroom: PT.bedroom, home: PT.home };

// ---- 房间走廊图：客厅是枢纽，机房/卧室是叶子，办公室连客厅与猫窝（边=从A走到B的航点，末点=B站位）----
const GRAPH = {
  home:    { office: [PT.mUp, PT.office] },
  office:  { home: [PT.mUp, PT.home], living: [PT.opU, PT.mOL, PT.living] },
  living:  { office: [PT.mOL, PT.opU, PT.office], server: [PT.mLS, PT.dA, PT.server], bedroom: [PT.mLB, PT.dB, PT.bedroom] },
  server:  { living: [PT.dA, PT.mLS, PT.living] },
  bedroom: { living: [PT.dB, PT.mLB, PT.living] },
};
function roomPath(from, to) {
  if (from === to) return [from];
  const prev = { [from]: null }, q = [from];
  while (q.length) {
    const n = q.shift();
    for (const nb in GRAPH[n]) if (!(nb in prev)) {
      prev[nb] = n;
      if (nb === to) { const p = [to]; let c = to; while (prev[c] != null) { c = prev[c]; p.unshift(c); } return p; }
      q.push(nb);
    }
  }
  return [to];
}
// 生成到目标房间的画布航点（沿门洞/开口走，不穿墙）
function pathTo(toRoom) {
  const rooms = roomPath(cat.node, toRoom), pts = [];
  for (let i = 0; i < rooms.length - 1; i++)
    for (const p of GRAPH[rooms[i]][rooms[i + 1]]) pts.push({ x: rx(p[0]), y: rx(p[1]) });
  if (!pts.length) pts.push({ x: rx(SPOT[toRoom][0]), y: rx(SPOT[toRoom][1]) });  // 已在该房间：原地打扫
  return pts;
}
function setPath(points, goalRoom, targetRoom) {
  cat.path = points.slice(); cat.goalRoom = goalRoom; cat.targetRoom = targetRoom || null;
  advanceWP();
}
function advanceWP() { if (cat.path && cat.path.length) { const w = cat.path.shift(); cat.tx = w.x; cat.ty = w.y; } }

// ---- 圆角矩形路径 ----
function rr(x, y, w, h, r) {
  ctx.beginPath();
  if (ctx.roundRect) { ctx.roundRect(x, y, w, h, r); return; }
  ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

// 家具遮挡已移除：之前那些手对位矩形会把家具周围的地毯也盖回猫身上（甚至整只吞掉）→「穿过地毯下方」。
// 新落点让小猫都在家具前的地面打扫、走位也走开阔地，不需要躲家具；真正的门框遮挡交给 drawWalls 的三张精准墙图层。

// ---- 背景 ----
function drawScene() {
  if (bgReady) ctx.drawImage(roomImg, 0, 0, W, H);
  else { ctx.fillStyle = MINT; ctx.fillRect(0, 0, W, H); }
}

// ---- 每个房间的垃圾（4 种不同外观）+ 剩余量小标签 ----
function drawPiles() {
  for (const rid in piles) {
    const p = piles[rid], s = SPOT[rid];
    const cx = rx(s[0]), cy = rx(s[1]), frac = clamp(p.remaining / p.total, 0, 1);
    if (frac > 0.02) drawGarbage(p.theme, cx, cy, frac);
    else drawSparkle(cx, cy);
    drawPileTag(cx, cy, frac <= 0.02 ? '✓' : human(p.remaining));
  }
}
function drawGarbage(theme, cx, cy, frac) {
  const n = Math.max(2, Math.round(frac * 8));
  for (let i = 0; i < n; i++) {
    const a = i * 2.4, rad = (6 + (i % 3) * 10) * (0.5 + frac * 0.5);
    const x = (cx + Math.cos(a) * rad) | 0, y = (cy + Math.sin(a) * rad * 0.55) | 0;
    if (theme === 'dev') {                 // 缓存碎片：小软盘 / 方块
      ctx.fillStyle = i % 4 === 0 ? CORAL : (i % 2 ? '#cfe0d2' : '#9fb6a6');
      ctx.fillRect(x, y, 7, 7); ctx.fillStyle = '#3a4a40'; ctx.fillRect(x + 1, y + 1, 4, 1.5);
    } else if (theme === 'system') {       // 灰尘团
      ctx.fillStyle = i % 3 ? '#9cb1a3' : '#7e9486';
      ctx.beginPath(); ctx.arc(x, y, 3.5 + (i % 2), 0, 7); ctx.fill();
    } else if (theme === 'download') {     // 下载：纸箱 / 牛皮纸堆
      ctx.fillStyle = i % 2 ? '#e2c98f' : '#cdb37a'; ctx.fillRect(x, y, 9, 7);
      ctx.fillStyle = '#7a6249'; ctx.fillRect(x, y, 9, 1.5);
    } else {                               // 大文件：木箱
      ctx.fillStyle = i % 2 ? WOOD : '#cbb892'; ctx.fillRect(x, y, 11, 9);
      ctx.strokeStyle = WOOD_D; ctx.lineWidth = 1; ctx.strokeRect(x + .5, y + .5, 10, 8);
    }
  }
}
function drawSparkle(x, y) {
  const t = performance.now() / 200; ctx.fillStyle = '#f2c14e';
  for (let i = 0; i < 4; i++) { const a = t + i * Math.PI / 2, r = 7 + Math.sin(t * 2) * 3; ctx.fillRect((x + Math.cos(a) * r) | 0, (y + Math.sin(a) * r * 0.6) | 0, 3, 3); }
}
function drawPileTag(cx, cy, txt) {
  const done = txt === '✓', label = done ? '✓ 干净' : txt;
  ctx.font = "bold 11px 'JetBrains Mono','Courier New',monospace";
  const tw = ctx.measureText(label).width + 14, h = 16, x = cx - tw / 2, y = cy - 36;
  rr(x, y, tw, h, 5); ctx.fillStyle = 'rgba(40,60,50,0.82)'; ctx.fill();
  ctx.fillStyle = done ? '#8fe0b0' : '#fff4dc'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(label, cx, y + h / 2 + 1);
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
}

// ---- 小猫 ----
const cat = { x: rx(PT.home[0]), y: rx(PT.home[1]), tx: rx(PT.home[0]), ty: rx(PT.home[1]), face: 1, state: 'idle', sweep: 0, walkPhase: 0, blink: 0, path: [], node: 'home', goalRoom: null, targetRoom: null };
let particles = [];
let mode = 'idle';   // idle | cleaning | done
let lastT = performance.now();

function spawnDust(x, y, color) {
  for (let i = 0; i < 5; i++) particles.push({
    x: x + (Math.random() - .5) * 14, y: y - 6 - Math.random() * 6,
    vx: (Math.random() - .5) * 30, vy: -20 - Math.random() * 30,
    life: .6 + Math.random() * .4, max: 1, size: 2 + (Math.random() * 2 | 0),
    color: color || SAGE_DD, kind: 'dust',
  });
}
function spawnHeart(x, y) {
  particles.push({ x: x + (Math.random() - .5) * 26, y: y - 30, vx: (Math.random() - .5) * 12, vy: -22, life: 1.2, max: 1.2, size: 6, color: CORAL, kind: 'heart' });
}

// ---- 像素小猫（程序化绘制，会打扫）----
function drawCat(dt) {
  const dx = cat.tx - cat.x, dy = cat.ty - cat.y, dist = Math.hypot(dx, dy);
  if (dist > 3) {
    const sp = 150 * dt;
    cat.x += dx / dist * Math.min(sp, dist);
    cat.y += dy / dist * Math.min(sp, dist);
    if (Math.abs(dx) > 1.2) cat.face = dx >= 0 ? 1 : -1;
    cat.walkPhase += dt * 10; cat.state = 'walk';
  } else if (cat.path && cat.path.length) {
    advanceWP(); cat.state = 'walk';                 // 到航点 → 走向下一个
  } else {
    if (cat.goalRoom) { cat.node = cat.goalRoom; cat.goalRoom = null; }   // 到达目标房间
    if (mode === 'cleaning') { cat.state = 'sweep'; cat.sweep += dt * 9; }
    else if (mode === 'done') { cat.state = 'happy'; }
    else { cat.state = 'idle'; }
  }

  const s = 2.7;                 // 像素缩放
  const bob = (cat.state === 'walk') ? Math.abs(Math.sin(cat.walkPhase)) * 4
            : Math.sin(performance.now() / 400) * 1.5;
  const bx = cat.x, by = cat.y - bob;
  const f = cat.face;

  ctx.fillStyle = 'rgba(46,74,61,0.18)';
  ctx.beginPath(); ctx.ellipse(cat.x, cat.y + 4, 24, 7, 0, 0, Math.PI * 2); ctx.fill();

  const OUT = C_OUT, OR = C_GREY, ORD = C_GREY_D, CR = C_WHITE, PK = C_PINK, EYE = C_EYE;
  const R = (ax, ay, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(Math.round(bx + ax * s * f - (f < 0 ? w * s : 0)), Math.round(by - ay * s - h * s), Math.round(w * s), Math.round(h * s)); };

  const tw = Math.sin(performance.now() / 300) * 2;
  R(5, 2, 2, 5, ORD); R(6.5, 4 + tw * 0.3, 2, 4, ORD); R(7.5, 6 + tw * 0.5, 2, 3, OR);   // 尾巴

  const legA = cat.state === 'walk' ? Math.sin(cat.walkPhase) * 2 : 0;
  R(-4, 0, 3, 4 + legA, CR); R(1, 0, 3, 4 - legA, CR);
  R(-4, 0, 3, 1.2, OUT); R(1, 0, 3, 1.2, OUT);

  body(R, OUT, OR, CR);
  head(R, OUT, OR, ORD, CR, PK, EYE);
  drawBroom(bx, by, s, f, R, OUT);
}
function body(R, OUT, OR, CR) {
  R(-5, 3, 10, 11, OR);
  R(-6, 4, 1, 9, OR); R(5, 4, 1, 9, OR);
  R(-5, 3, 10, 1, OUT);
  R(-6, 4, 1, 9, OUT); R(5, 4, 1, 9, OUT);
  R(-2.5, 3.5, 5, 9, CR);
}
function head(R, OUT, OR, ORD, CR, PK, EYE) {
  R(-6, 23, 3, 3, OR); R(3, 23, 3, 3, OR);
  R(-6, 25, 2, 2, OR); R(4, 25, 2, 2, OR);
  R(-5.4, 23.4, 1.4, 1.6, PK); R(4, 23.4, 1.4, 1.6, PK);
  R(-7, 12, 14, 12, OR);
  R(-7, 23, 14, 1, OR);
  R(-7.5, 13, 1, 10, OUT); R(6.5, 13, 1, 10, OUT);
  R(-7, 23.6, 14, 0.6, OUT);
  R(-4.5, 22, 9, 1.4, ORD);
  R(-3.6, 12.6, 7.2, 3.6, CR);
  R(-2.6, 11.4, 5.2, 1.6, CR);
  const open = cat.blink > 0 ? 0.5 : 2.3;
  R(-4.6, 16, 2.1, open, EYE); R(2.5, 16, 2.1, open, EYE);
  if (cat.blink <= 0) { R(-4.2, 17.1, 0.8, 0.8, CR); R(2.9, 17.1, 0.8, 0.8, CR); }
  R(-0.7, 14.2, 1.6, 1.2, PK);
}
function drawBroom(bx, by, s, f, R, OUT) {
  const swing = (cat.state === 'sweep') ? Math.sin(cat.sweep) * 0.5 : 0.15;
  R(2.5, 6, 2.5, 2.5, C_WHITE); R(2.5, 6, 2.5, 0.8, C_OUT);
  ctx.save();
  const px = bx + 4.5 * s * f, py = by - 7 * s;
  ctx.translate(px, py); ctx.rotate((0.5 + swing) * f);
  ctx.fillStyle = '#7a6249'; ctx.fillRect(-1.5, -2, 3, 32);
  ctx.fillStyle = '#9a7e5e'; ctx.fillRect(0, -2, 1, 32);
  ctx.fillStyle = FOREST; ctx.fillRect(-6, 30, 12, 4);
  ctx.fillStyle = '#cdb486';
  for (let i = -5; i <= 5; i += 2) ctx.fillRect(i, 33, 1.4, 9 + ((i & 2) ? 2 : 0));
  ctx.restore();
}

// ---- 粒子 ----
function drawParticles(dt) {
  for (const p of particles) {
    p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 60 * dt; p.life -= dt;
    ctx.globalAlpha = clamp(p.life / p.max, 0, 1);
    if (p.kind === 'heart') { ctx.font = `${p.size + 8}px serif`; ctx.fillText('♥', p.x, p.y); }
    else { ctx.fillStyle = p.color; ctx.fillRect(p.x | 0, p.y | 0, p.size, p.size); }
  }
  ctx.globalAlpha = 1;
  particles = particles.filter(p => p.life > 0);
}

// ---- 主循环 ----
function loop(now) {
  const dt = Math.min(0.05, (now - lastT) / 1000); lastT = now;
  cat.blink -= dt; if (cat.blink < -3) cat.blink = 0.12;
  ctx.clearRect(0, 0, W, H);
  drawScene();                                  // room.png 背景
  drawPiles();                                  // 各房间垃圾 + 标签
  if (mode === 'cleaning' && cat.state === 'sweep' && Math.random() < 0.4)
    spawnDust(cat.x + cat.face * 22, cat.y, piles[cat.targetRoom]?.color);
  if (mode === 'done' && Math.random() < 0.06) spawnHeart(cat.x, cat.y);
  drawParticles(dt);
  drawCat(dt);
  drawWalls();                                  // 三张透明墙图层整张盖到最顶 → 穿门精准（唯一遮挡）
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

// ================================================================ 清理流程
$('#startBtn').addEventListener('click', startClean);
$('#closeBtn').addEventListener('click', async () => {
  try { await fetch('/api/shutdown', { method: 'POST' }); } catch (e) {}
  document.body.innerHTML = '<div style="font-family:\'JetBrains Mono\',monospace;color:#7d9285;text-align:center;margin-top:30vh;line-height:2">小猫去打盹了 ｡ﾟ(つ˘ω˘)つ ﾟ｡<br>可以关掉这个标签页了。</div>';
});

let cleanedLog = [];   // 本次清理逐项记录（用于卡内总结）

async function startClean() {
  const ids = Object.keys(selectedSizes);
  if (!ids.length) return;
  const total = ids.reduce((s, id) => s + selectedSizes[id], 0);
  const ask = DEMO
    ? `模拟演示：假装清理 ${ids.length} 项（约 ${human(total)}）。\n不会删除任何真实文件，只看小猫一间间打扫的动画。\n\n开始？`
    : `即将永久删除 ${ids.length} 项，约释放 ${human(total)}。\n（不进废纸篓，无法恢复）\n\n确定让小猫开始打扫？`;
  if (!confirm(ask)) return;

  // 每个房间的「待清理量」= 该房间被勾选项之和；没勾的房间保持原样（垃圾不动、不显示干净）
  const selByRoom = {};
  for (const group of Object.values(SCAN.cleanable))
    for (const it of group.items) if (selectedSizes[it.id]) {
      const rid = ITEM_ROOM[it.id]; selByRoom[rid] = (selByRoom[rid] || 0) + it.size;
    }
  for (const rid in piles) if (selByRoom[rid] > 0) { piles[rid].total = selByRoom[rid]; piles[rid].remaining = selByRoom[rid]; }

  // 卡片切到「打扫中」：收起清单/提示，展开向上滚动的 trace
  cleanedLog = [];
  $('#reviewTitle').textContent = '打扫中…';
  $('#paneHint').textContent = '小猫正在一间间清理';
  $('#reviewWarn').classList.add('hidden');
  $('#cleanLists').classList.add('hidden');
  $('#selSum').classList.add('hidden');
  $('#startBtn').classList.add('hidden');
  const tr = $('#trace'); tr.innerHTML = ''; tr.classList.remove('hidden');
  mode = 'cleaning';
  traceLine('sys', DEMO ? '🐱 模拟开始，小猫拿起扫帚去打扫…' : '小猫拿起扫帚，开始打扫…');

  if (DEMO) { runDemoClean(ids); return; }   // 模拟模式：永不调用真实删除接口
  try {
    const r = await fetch('/api/clean', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids }) });
    if (!r.ok) throw new Error('clean failed');
    listenSSE();
  } catch (e) {
    runDemoClean(ids);   // 离线演示
  }
}

function listenSSE() {
  const es = new EventSource('/api/events');
  es.onmessage = (m) => {
    let ev; try { ev = JSON.parse(m.data); } catch (e) { return; }
    handleEvent(ev);
    if (ev.type === 'finished') es.close();
  };
  es.onerror = () => { /* 服务结束会自然断开 */ };
}

function handleEvent(ev) {
  if (ev.type === 'item_start') {
    setCatTarget(ev);
    setStatus(`正在清理：${ev.label}`);
    markRow(ev.id, 'cleaning-now');
    traceLine('run', `清理 ${ev.label} …`);
  } else if (ev.type === 'item_done') {
    const rid = ITEM_ROOM[ev.id];
    if (piles[rid]) piles[rid].remaining = Math.max(0, piles[rid].remaining - ev.freed);
    setFreed(ev.freed_total_h, ev.index, ev.total);
    markRow(ev.id, 'cleaned');
    cleanedLog.push({ label: ev.label, freed: ev.freed || 0, freed_h: ev.freed_h, category: ev.category, error: ev.error });
    traceLine(ev.error ? 'err' : 'ok', `${ev.label} → 释放 ${ev.freed_h}${ev.error ? '（' + ev.error + '）' : ''}`);
  } else if (ev.type === 'finished') {
    finishClean(ev);
  }
}
// 让小猫走到该清理项所在房间的垃圾堆旁（沿门洞，不穿墙）
function setCatTarget(ev) {
  const rid = ITEM_ROOM[ev.id];
  if (!rid || !piles[rid]) return;
  setPath(pathTo(rid), rid, rid);
}

function finishClean(ev) {
  mode = 'done';
  setPath(pathTo('home'), 'home', null);   // 原路返回猫窝；没勾的房间垃圾保留
  setStatus('打扫完成，小猫很满意 ★');
  $('#progressBar').style.width = '100%';
  $('#freedNow').textContent = ev.freed_total_h;
  traceLine('sys', `★ 全部完成，共释放 ${ev.freed_total_h}`);
  $('#reviewTitle').textContent = '打扫完成 ★';
  $('#paneHint').textContent = '小猫打扫完啦';
  const sum = $('#clnSummary'); sum.innerHTML = buildSummary(ev); sum.classList.remove('hidden');
  $('#closeBtn').classList.remove('hidden');
}

// 卡内完成总结：总释放 + 逐类别明细
function buildSummary(ev) {
  const byCat = {};
  for (const it of cleanedLog) {
    const k = it.category || 'other';
    (byCat[k] = byCat[k] || { freed: 0, n: 0 });
    byCat[k].freed += it.freed || 0; byCat[k].n += 1;
  }
  let rows = '';
  for (const [k, v] of Object.entries(byCat)) {
    const name = (CAT_META[k] && CAT_META[k].label) || (SCAN.cleanable[k] && SCAN.cleanable[k].label) || k;
    const color = (CAT_META[k] && CAT_META[k].color) || SAGE;
    rows += `<li><span class="cs-dot" style="background:${color}"></span><span class="cs-name">${escapeHtml(name)}</span><span class="cs-n">${v.n} 项</span><span class="cs-sz">${human(v.freed)}</span></li>`;
  }
  return `<div class="cs-title">★ 打扫完成</div>
    <div class="cs-freed">${escapeHtml(ev.freed_total_h)}</div>
    <div class="cs-sub">成功清理 <b>${ev.count_done}</b> 项${ev.count_error ? `，<b>${ev.count_error} 项跳过</b>` : ''} · 记忆已更新，下次更懂你</div>
    <ul class="cs-list">${rows}</ul>`;
}

// ---- 模拟清理：由「小猫真正走到该房间」驱动，垃圾扫完才清掉 → 动画与走位一致 ----
function runDemoClean(ids) {
  const items = [];
  for (const group of Object.values(SCAN.cleanable))
    for (const it of group.items) if (selectedSizes[it.id]) items.push(it);
  let i = 0, freed = 0;
  const SWEEP_MS = 900;     // 到房间后挥扫的时长
  const MAX_WAIT = 12000;   // 兜底：万一走不到也别卡死（要 > 最长一段路程的耗时）

  const startItem = () => {
    if (i >= items.length) { finishClean({ type: 'finished', freed_total_h: human(freed), count_done: items.length, count_error: 0 }); return; }
    const it = items[i];
    handleEvent({ type: 'item_start', id: it.id, label: it.label, category: it.category, index: i, total: items.length });  // → 小猫出发
    const rid = ITEM_ROOM[it.id];
    const t0 = performance.now();
    const arrived = () => (cat.node === rid && (!cat.path || cat.path.length === 0)
                           && Math.hypot(cat.tx - cat.x, cat.ty - cat.y) < 5) || (performance.now() - t0 > MAX_WAIT);
    const waitArrive = () => {
      if (!arrived()) { setTimeout(waitArrive, 100); return; }
      setTimeout(() => {                      // 到了 → 扫一会儿 → 清掉这项
        freed += it.size;
        handleEvent({ type: 'item_done', id: it.id, label: it.label, category: it.category, freed: it.size, freed_h: human(it.size), freed_total_h: human(freed), index: i, total: items.length });
        i++; setTimeout(startItem, 350);
      }, SWEEP_MS);
    };
    setTimeout(waitArrive, 200);
  };
  startItem();
}

// ---------------------------------------------------------------- UI 小工具
function markRow(id, cls) {
  const row = document.querySelector(`.row[data-id="${cssEsc(id)}"]`);
  if (row) { row.classList.remove('cleaning-now'); row.classList.add(cls); }
}
function setStatus(t) { $('#catStatus').textContent = t; }
function setFreed(h, idx, total) {
  $('#freedNow').textContent = h;
  if (total) $('#progressBar').style.width = `${Math.round((idx + 1) / total * 100)}%`;
}
// 卡内 trace：新行从底部滑入，容器自动滚到底 → 旧行向上滚动
function traceLine(kind, msg) {
  const tr = $('#trace'); if (!tr) return;
  const line = el('span', 'tl ' + (kind || 'sys')); line.textContent = `› ${msg}`;
  tr.appendChild(line); tr.scrollTop = tr.scrollHeight;
}
function log(kind, msg) { traceLine(kind, msg); }   // 兼容旧调用（安全一键反馈等）
function human(n) {
  n = +n || 0; const u = ['B', 'KB', 'MB', 'GB', 'TB']; let i = 0;
  while (Math.abs(n) >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return (i === 0 ? n | 0 : n.toFixed(1)) + u[i];
}
function escapeHtml(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
function cssEsc(s) { return String(s).replace(/["\\]/g, '\\$&'); }

loadScan();
})();
