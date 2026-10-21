"""Kiểm tra bố cục SVG do figlib sinh ra: chữ đè chữ, chữ vắt ngang viền khung, chữ bị che, mũi tên cụt hoặc lơ lửng, hình vẽ tràn khung.

Chạy: python3 lint.py [--min-font PX] [--json] <file.svg | thư mục> ...

Mỗi SVG được nhúng vào một trang HTML và mở bằng Chrome headless. getBBox() của trình duyệt cho khung bao thật của
từng dòng chữ (đã tính font, cỡ chữ, dấu tiếng Việt), sau đó so sánh với nhau và với các hình trong hình.

NGUYÊN TẮC: lint báo MỌI dấu hiệu nghi ngờ, không im lặng bỏ qua điều gì (trừ nền phủ kín canvas). Lint không biết ý
đồ của hình. Agent đọc từng dòng báo cáo, tự quyết định là lỗi thật hay cố ý:
  - Lỗi thật: sửa gen.py rồi sinh lại hình.
  - Cố ý: giữ nguyên và nêu lý do (ví dụ chữ đặt trên viền làm nhãn, đường chéo cố ý xuyên qua hộp để minh họa khái niệm).
  - Khi bố cục đẹp xung đột với độ chính xác nội dung (số liệu, công thức, quan hệ hình học, thứ tự bước), LUÔN ưu tiên
    độ chính xác nội dung. Không đổi, bớt hay làm sai nội dung chỉ để lint hết báo. Lint sạch không có nghĩa là hình đúng.

Luật ERROR (gần như chắc chắn là lỗi, mã thoát 1):
  OVERLAP          hai dòng chữ chồng lên nhau
  CROSS_EDGE       chữ vắt qua viền một khung chữ nhật
  COVERED          chữ bị hình tô đặc vẽ sau che từ 20% diện tích
  LINE_THROUGH     đường thẳng, đường cong hoặc viền đa giác (đậm, không phải lưới mờ) đi xuyên qua chữ
  OUT_OF_CANVAS    chữ nằm ngoài mép hình
  SHAPE_OUT_OF_CANVAS  hình vẽ (không phải chữ) nằm ngoài mép hình quá 2 px
  ARROW_TOO_SHORT  mũi tên không còn thân (thân thấy được dưới 1 px, chỉ còn đầu mũi tên)
  SHAPE_CROSS_EDGE đường hoặc hình vẽ (không có đầu mũi tên) nằm từ 50% chiều dài trở lên trong một khung nhưng thò ra ngoài
Luật WARN (không đổi mã thoát):
  SMALL_FONT     chữ nhỏ hơn --min-font (mặc định 6.5 px trên viewBox của hình)
  EMPTY_SPACE    khung dư khoảng trống đáy, lớn hơn 2 lần đệm trên/trái của chính nó (làm hình cao hơn cần thiết)
  TIGHT_TEXT     chữ cách viền khung chứa nó (khung cao và rộng trên 8 px, kể cả ô lưới nhỏ) dưới 2.5 px
  BIG_GAP        khoảng trống dọc trên 22 px giữa hai khối nội dung liên tiếp (ví dụ panel cuối và dòng nguồn)
  LOW_CONTRAST   chữ có độ tương phản dưới 3:1 so với nền (chỉ tính nền tô đặc dạng #hex, white, black)
Luật REVIEW (không đổi mã thoát, agent tự phán đoán cố ý hay lỗi). Gồm mọi thứ trước đây bị bỏ qua ngầm:
  HALO_CROSS_EDGE, HALO_LINE_THROUGH, HALO_COVERED  chữ có halo (stroke) mà lẽ ra bị báo CROSS_EDGE, LINE_THROUGH, COVERED
  GRID_THROUGH         nét mờ (sáng hoặc mảnh dưới 0.5 px, thường là lưới) đi xuyên qua chữ (gộp mọi nét của một dòng chữ thành một dòng)
  LINE_UNDER_CHIP      nét đi xuyên qua chữ nhưng đoạn đó bị chip nền đặc che
  COVERED_PARTIAL      chữ bị hình tô đặc vẽ sau che dưới 20% diện tích
  TEXT_TOUCH           hộp bao đầy đủ của hai dòng chữ chạm hoặc chồng nhau nhẹ (không đủ để thành OVERLAP)
  TEXT_NEAR_EDGE       chữ nằm ngoài khung nhưng cách viền dưới 1.5 px, hoặc vắt qua viền dưới ngưỡng CROSS_EDGE (bỏ cạnh chung với ô chứa chính chữ)
  TEXT_NEAR_STROKE     nét đậm sượt sát chữ (cách dưới 1 px) nhưng chưa xuyên qua
  SHAPE_ENTERS_EDGE    đường hoặc hình vẽ cắt viền một khung nhưng dưới 50% chiều dài nằm trong khung đó
  SHAPE_UNDER_FILL     đường hoặc hình vẽ nằm trong khung tô đặc vẽ sau (phần trong bị che, chỉ thấy phần ngoài)
  ARROW_SHORT_SHAFT    mũi tên có thân thấy được từ 1 đến 4 px
  DANGLING_ARROW       đầu hoặc đuôi mũi tên cách mọi hình và chữ hơn 10 px (mũi tên lơ lửng)
  ARROW_THROUGH_BOX    mũi tên đi xuyên qua một khung mà cả hai đầu nằm ngoài khung đó
  ARROWHEAD_ON_TEXT    đầu mũi tên đè lên chữ
  NOT_EVALUATED        hình dùng transform, clipPath, use, mask, filter, foreignObject, svg lồng hoặc marker-start/mid:
                       lint không đánh giá được phần đó, phải xem bằng mắt

Ngoại lệ có chủ ý của lint (không báo): mũi tên bắt đầu trong khung và kết thúc ngoài khung (nối giữa các khối), nét
mờ chỉ sượt gần chữ (không xuyên), nét lưới mờ khi tìm đích của mũi tên. Không đánh giá được nội dung: số liệu,
công thức, hình minh họa có khớp lời giải thích hay không, màu, thẩm mỹ. Vẫn phải xem hình bằng mắt.
"""
import argparse
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

JS = r"""
<script>
function run(minFont) {
  const svg = document.querySelector('svg'), vb = svg.viewBox.baseVal, out = [];
  const all = [...svg.querySelectorAll('*')].filter(e => !e.closest('defs'));
  const idx = new Map(all.map((e, i) => [e, i]));
  const STEP = 1.5;
  const bb = e => { const g = e.getBBox(); return {x: g.x, y: g.y, w: g.width, h: g.height}; };
  const hit = (a, c) => Math.min(a.x + a.w, c.x + c.w) - Math.max(a.x, c.x) > 0 && Math.min(a.y + a.h, c.y + c.h) - Math.max(a.y, c.y) > 0;
  const ident = e => { const t = e.tagName.toLowerCase(), g = n => e.getAttribute(n);
    const s = g('d') ? 'd=' + g('d').slice(0, 26) : t === 'line' ? g('x1') + ',' + g('y1') + '-' + g('x2') + ',' + g('y2')
      : g('points') ? 'pts=' + g('points').slice(0, 26) : g('cx') ? 'c=' + g('cx') + ',' + g('cy') : g('x') ? 'xy=' + g('x') + ',' + g('y') : '';
    return '#' + idx.get(e) + ' ' + t + ' ' + (g('stroke') || g('fill') || '') + ' ' + s; };
  const push = (rule, text, detail, b) => out.push({rule, text, detail: detail || '', x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.w), h: Math.round(b.h)});
  const lum = c => { const m = /^#([0-9a-f]{6})$/i.exec(c || ''); if (!m) return 0;
    const n = parseInt(m[1], 16); return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255; };
  const inBox = (pt, b) => pt.x > b.x + 0.5 && pt.x < b.x + b.w - 0.5 && pt.y > b.y + 0.5 && pt.y < b.y + b.h - 0.5;
  const isBg = g => g.w >= vb.width - 5 && g.h >= vb.height - 5;
  const cache = new Map();
  const samples = e => { if (!cache.has(e)) { const pts = []; let len = 0;
      try { len = e.getTotalLength(); for (let d = 0; d <= len; d += STEP) pts.push(e.getPointAtLength(d)); } catch (_) {}
      cache.set(e, {len, pts}); } return cache.get(e); };

  // construct lint không đánh giá được
  for (const sel of ['[transform]', 'clipPath', 'use', 'mask', 'filter', 'foreignObject', 'svg svg', '[marker-start]', '[marker-mid]']) {
    const n = svg.querySelectorAll(sel).length;
    if (n) push('NOT_EVALUATED', sel, n + ' phần tử, lint không tính phần này', {x: 0, y: 0, w: 0, h: 0}); }

  // chữ: b = lõi 60% chiều cao ở giữa (nét chữ thực), f = hộp bao đầy đủ của getBBox
  const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim());
  const item = texts.map(t => { const g = bb(t);
    return {el: t, i: idx.get(t), b: {x: g.x, y: g.y + g.h * 0.2, w: g.w, h: g.h * 0.6}, f: g, s: t.textContent.trim().slice(0, 40),
      fs: parseFloat(t.getAttribute('font-size') || 12), halo: !!t.getAttribute('stroke')}; });
  const add = (rule, a, detail) => push(rule, a.s, detail, a.f);
  const hn = (rule, a) => a.halo ? 'HALO_' + rule : rule;       // chữ có halo: nhãn cố ý đặt trên viền, đưa sang REVIEW
  const done = new Set();                                       // mỗi cặp (chữ, hình) chỉ báo một lần

  for (let i = 0; i < item.length; i++) {
    const a = item[i], A = a.b;
    if (A.x < -0.5 || A.y < -0.5 || A.x + A.w > vb.width + 0.5 || A.y + A.h > vb.height + 0.5) add('OUT_OF_CANVAS', a);
    for (let j = i + 1; j < item.length; j++) {
      const C = item[j].b;
      const ox = Math.min(A.x + A.w, C.x + C.w) - Math.max(A.x, C.x), oy = Math.min(A.y + A.h, C.y + C.h) - Math.max(A.y, C.y);
      if (ox > 1.5 && oy > 1.5) add('OVERLAP', a, 'với "' + item[j].s + '"');
      else { const F = a.f, G = item[j].f;
        const fx = Math.min(F.x + F.w, G.x + G.w) - Math.max(F.x, G.x), fy = Math.min(F.y + F.h, G.y + G.h) - Math.max(F.y, G.y);
        if (fx > 1 && fy > 1) add('TEXT_TOUCH', a, 'hộp bao chạm "' + item[j].s + '" (chồng ' + Math.round(fx * 10) / 10 + 'x' + Math.round(fy * 10) / 10 + 'px)'); }
    }
  }

  const rects = [...svg.querySelectorAll('rect')].filter(r => {
    const s = r.getAttribute('stroke'); return s && s !== 'none' && +r.getAttribute('width') < vb.width - 5; });
  const rg = r => ({x: +r.getAttribute('x'), y: +r.getAttribute('y'), w: +r.getAttribute('width'), h: +r.getAttribute('height')});
  const holds = (R, b) => b.x >= R.x - 0.5 && b.x + b.w <= R.x + R.w + 0.5 && b.y >= R.y - 0.5 && b.y + b.h <= R.y + R.h + 0.5;
  // hai khung chung một cạnh (ô lưới cạnh nhau): chữ sát cạnh đó đã được tính với khung chứa nó (TIGHT_TEXT)
  const sharesEdge = (P, Q) => [[P.x, Q.x + Q.w], [P.x + P.w, Q.x], [P.y, Q.y + Q.h], [P.y + P.h, Q.y]].some(([u, v]) => Math.abs(u - v) < 1.5);
  for (const r of rects) {
    const rx = +r.getAttribute('x'), ry = +r.getAttribute('y'), rw = +r.getAttribute('width'), rh = +r.getAttribute('height');
    for (const a of item) {
      const b = a.b, f = a.f;
      if (!(f.x < rx + rw + 1.5 && f.x + f.w > rx - 1.5 && f.y < ry + rh + 1.5 && f.y + f.h > ry - 1.5)) continue;
      const inside = b.x >= rx - 0.5 && b.x + b.w <= rx + rw + 0.5 && b.y >= ry - 0.5 && b.y + b.h <= ry + rh + 0.5;
      const contains = b.x <= rx && b.x + b.w >= rx + rw && b.y <= ry && b.y + b.h >= ry + rh;
      if (inside || contains) continue;
      const where = 'khung ' + Math.round(rw) + 'x' + Math.round(rh) + ' tại ' + Math.round(rx) + ',' + Math.round(ry);
      const ox = Math.min(b.x + b.w, rx + rw) - Math.max(b.x, rx), oy = Math.min(b.y + b.h, ry + rh) - Math.max(b.y, ry);
      if (ox > 0.4 && oy > 1.0 && b.x < rx + rw && b.x + b.w > rx && b.y < ry + rh && b.y + b.h > ry) { add(hn('CROSS_EDGE', a), a, where); done.add(a.i + '|' + idx.get(r)); }
      else { const own = rects.map(rg).filter(R => holds(R, b)).sort((p, q) => p.w * p.h - q.w * q.h)[0];
        if (own && sharesEdge(own, rg(r))) continue;
        add('TEXT_NEAR_EDGE', a, where + ' (lõi chữ cách viền dưới 1.5 px hoặc vắt qua dưới ngưỡng)'); }
    }
  }

  // chữ và hình vẽ: tô đặc vẽ sau che chữ, nét cắt qua hoặc sượt sát chữ
  for (const a of item) {
    const b = a.b, f = a.f, area = b.w * b.h, nb = {x: f.x - 1, y: f.y - 1, w: f.w + 2, h: f.h + 2}, grid = [];
    if (area <= 0) continue;
    for (let k = 0; k < all.length; k++) {
      const e = all[k], tag = e.tagName.toLowerCase();
      if (!['rect', 'circle', 'ellipse', 'polygon', 'path', 'image', 'line', 'polyline'].includes(tag)) continue;
      const after = k > a.i;
      let g; try { g = bb(e); } catch (_) { continue; }
      if (isBg(g)) continue;
      if (g.x > f.x + f.w + 3 || g.x + g.w < f.x - 3 || g.y > f.y + f.h + 3 || g.y + g.h < f.y - 3) continue;
      const fill = e.getAttribute('fill'), stroke = e.getAttribute('stroke');
      const filled = fill && fill !== 'none';
      const pair = a.i + '|' + k;
      // 1) hình tô đặc vẽ sau chữ che chữ
      if (after && filled && tag !== 'line' && hit(b, g)) {
        let ratio = 0;
        if (tag === 'rect' || tag === 'circle' || tag === 'ellipse' || tag === 'image') {
          const ox = Math.min(b.x + b.w, g.x + g.w) - Math.max(b.x, g.x), oy = Math.min(b.y + b.h, g.y + g.h) - Math.max(b.y, g.y);
          ratio = ox * oy / area;
        } else if (e.isPointInFill) {
          let h = 0, tot = 0;
          for (let i = 0; i <= 10; i++) for (let j = 0; j <= 2; j++) { tot++;
            if (e.isPointInFill(new DOMPoint(b.x + b.w * i / 10, b.y + b.h * (0.1 + 0.4 * j)))) h++; }
          ratio = h / tot;
        }
        if (ratio >= 0.2) add(hn('COVERED', a), a, 'bởi ' + ident(e));
        else if (ratio > 0.02) add('COVERED_PARTIAL', a, 'bởi ' + ident(e) + ' (che ' + Math.round(ratio * 100) + '%)');
      }
      // 2) nét vẽ cắt qua chữ: lấy mẫu dọc nét, đếm chiều dài nằm trong lõi chữ và sát quanh chữ
      if (tag === 'rect' || tag === 'image' || !stroke || stroke === 'none' || !e.getTotalLength || done.has(pair)) continue;
      const faint = lum(stroke) > 0.8 || parseFloat(e.getAttribute('stroke-width') || 1) < 0.5;
      const sm = samples(e);
      if (!(sm.len > 0)) continue;
      // chip nền đặc vẽ giữa nét và chữ che nét: giao điểm đó không nhìn thấy
      const chips = after ? [] : all.slice(k + 1, a.i).filter(c => {
        const t = c.tagName.toLowerCase(), cf = c.getAttribute('fill');
        return ['rect', 'circle', 'ellipse', 'polygon', 'path'].includes(t) && cf && cf !== 'none' && !c.getAttribute('fill-opacity') && !c.getAttribute('opacity'); });
      const hidden = pt => chips.some(c => { try { return c.isPointInFill(new DOMPoint(pt.x, pt.y)); } catch (_) { return false; } });
      let inside = 0, hid = 0, near = 0;
      for (const pt of sm.pts) {
        if (inBox(pt, b)) { if (hidden(pt)) hid += STEP; else inside += STEP; }
        else if (inBox(pt, nb)) near += STEP; }
      const how = ' (' + Math.round(inside) + 'px trong khung chữ, ' + (after ? 'vẽ sau chữ' : 'vẽ trước chữ') + ')';
      if (inside >= 2.5 && faint) { grid.push(ident(e) + how); done.add(pair); }
      else if (inside >= 2.5) { add(hn('LINE_THROUGH', a), a, ident(e) + how); done.add(pair); }
      else if (hid >= 2.5) { add('LINE_UNDER_CHIP', a, ident(e) + ' (' + Math.round(hid) + 'px bị chip nền che)'); done.add(pair); }
      else if (!faint && inside + near > 0) { add('TEXT_NEAR_STROKE', a, ident(e) + ' (sượt sát chữ ' + Math.round((inside + near) * 10) / 10 + 'px)'); done.add(pair); }
    }
    if (grid.length) add('GRID_THROUGH', a, grid.length + ' nét mờ: ' + grid[0] + (grid.length > 1 ? ' và ' + (grid.length - 1) + ' nét khác' : ''));
  }

  // hình vẽ so với khung và mép hình
  const shapeEls = [...svg.querySelectorAll('path,ellipse,circle,polygon,polyline,line')].filter(e => !e.closest('defs') && e.getTotalLength);
  for (const e of shapeEls) { const g = bb(e);
    if (g.x < -2 || g.y < -2 || g.x + g.w > vb.width + 2 || g.y + g.h > vb.height + 2) push('SHAPE_OUT_OF_CANVAS', ident(e), 'ngoài mép hình', g); }
  for (const r of rects) {
    const rx = +r.getAttribute('x'), ry = +r.getAttribute('y'), rw = +r.getAttribute('width'), rh = +r.getAttribute('height');
    const sd = pt => Math.min(pt.x - rx, rx + rw - pt.x, pt.y - ry, ry + rh - pt.y);   // > 0 trong khung, < 0 ngoài khung
    const rFill = r.getAttribute('fill'), rOpaque = rFill && rFill !== 'none' && !r.getAttribute('fill-opacity') && !r.getAttribute('opacity');
    const where = 'khung ' + Math.round(rw) + 'x' + Math.round(rh) + ' tại ' + Math.round(rx) + ',' + Math.round(ry);
    for (const e of shapeEls) {
      const st = e.getAttribute('stroke');
      if (e.hasAttribute('marker-end') || e.hasAttribute('marker-start') || !st || st === 'none') continue;
      const sm = samples(e); let ins = 0, outs = 0;
      for (const pt of sm.pts) { const k = sd(pt); if (k > 2) ins += STEP; else if (k < -2) outs += STEP; }
      if (ins < 3 || outs < 3) continue;
      const g = bb(e), under = rOpaque && (r.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_PRECEDING);
      const frac = Math.round(100 * ins / sm.len);
      if (under) push('SHAPE_UNDER_FILL', ident(e), where + ' vẽ sau, che phần trong (' + frac + '% nằm trong)', g);
      else if (ins >= 0.5 * sm.len && outs >= 4) push('SHAPE_CROSS_EDGE', ident(e), 'phần lớn nằm trong ' + where + ' nhưng thò ra ngoài khoảng ' + Math.round(outs) + 'px', g);
      else push('SHAPE_ENTERS_EDGE', ident(e), 'cắt viền ' + where + ' (' + frac + '% nằm trong, ' + Math.round(outs) + 'px ngoài)', g);
    }
  }

  // mũi tên: thân nhìn thấy = chiều dài path trừ phần đầu mũi tên nằm lùi sau điểm cuối (refX/viewBox * kích thước marker)
  const arrows = [];
  for (const p of svg.querySelectorAll('[marker-end]')) {
    const m = /url\(#([^)]+)\)/.exec(p.getAttribute('marker-end')), mk = m && svg.getElementById(m[1]);
    if (!mk || !p.getTotalLength || p.closest('defs')) continue;
    let size = mk.markerWidth.baseVal.value;
    if (mk.getAttribute('markerUnits') !== 'userSpaceOnUse') size *= parseFloat(p.getAttribute('stroke-width') || 1);
    const vbw = mk.viewBox.baseVal.width || 10, head = mk.refX.baseVal.value / vbw * size, len = p.getTotalLength();
    const S = p.getPointAtLength(0), E = p.getPointAtLength(len), P = p.getPointAtLength(Math.max(0, len - 1));
    const n = Math.hypot(E.x - P.x, E.y - P.y) || 1, u = {x: (E.x - P.x) / n, y: (E.y - P.y) / n};
    const tipK = (vbw - mk.refX.baseVal.value) / vbw * size;
    arrows.push({e: p, len, size, head, S, T: {x: E.x + u.x * tipK, y: E.y + u.y * tipK}, E, u, b: bb(p)});
  }
  for (const A of arrows) { const shaft = A.len - A.head;
    const info = 'dài ' + Math.round(A.len * 10) / 10 + 'px, đầu mũi tên ' + Math.round(A.head * 10) / 10 + 'px, thân thấy được ' + Math.round(shaft * 10) / 10 + 'px';
    if (shaft < 1) push('ARROW_TOO_SHORT', ident(A.e), info, A.b);
    else if (shaft < 4) push('ARROW_SHORT_SHAFT', ident(A.e), info, A.b);
  }
  // mũi tên lơ lửng: đầu hoặc đuôi không gần hình nào (viền khung, nét, hình tô, chữ)
  const dRect = (pt, g) => { const dx = Math.max(g.x - pt.x, 0, pt.x - g.x - g.w), dy = Math.max(g.y - pt.y, 0, pt.y - g.y - g.h);
    if (dx || dy) return Math.hypot(dx, dy); return Math.min(pt.x - g.x, g.x + g.w - pt.x, pt.y - g.y, g.y + g.h - pt.y); };
  const targets = all.filter(e => ['rect', 'circle', 'ellipse', 'polygon', 'path', 'image', 'line', 'polyline', 'text'].includes(e.tagName.toLowerCase()))
    .filter(e => { if (e.tagName.toLowerCase() === 'text') return e.textContent.trim(); let g; try { g = bb(e); } catch (_) { return false; }
      return !isBg(g) && !(lum(e.getAttribute('stroke')) > 0.8 && !e.getAttribute('fill')); });
  const distTo = (pt, e) => { const t = e.tagName.toLowerCase();
    if (t === 'rect' || t === 'image' || t === 'text') return dRect(pt, bb(e));
    const fl = e.getAttribute('fill'); if (fl && fl !== 'none' && e.isPointInFill && e.isPointInFill(new DOMPoint(pt.x, pt.y))) return 0;
    if (!e.getTotalLength) return 1e9; let d = 1e9; for (const q of samples(e).pts) d = Math.min(d, Math.hypot(q.x - pt.x, q.y - pt.y)); return d; };
  for (const A of arrows) for (const [name, pt] of [['đầu', A.T], ['đuôi', A.S]]) {
    let best = 1e9; for (const e of targets) { if (e === A.e) continue; best = Math.min(best, distTo(pt, e)); if (best <= 10) break; }
    if (best > 10) push('DANGLING_ARROW', ident(A.e), name + ' mũi tên tại ' + Math.round(pt.x) + ',' + Math.round(pt.y) + ' cách hình/chữ gần nhất ' + Math.round(best) + 'px', A.b); }
  // mũi tên đi xuyên qua khung mà cả hai đầu nằm ngoài khung đó
  for (const r of rects) {
    const rx = +r.getAttribute('x'), ry = +r.getAttribute('y'), rw = +r.getAttribute('width'), rh = +r.getAttribute('height');
    if (rw < 20 || rh < 20) continue;
    const sd = pt => Math.min(pt.x - rx, rx + rw - pt.x, pt.y - ry, ry + rh - pt.y);
    for (const A of arrows) { if (sd(A.S) > 2 || sd(A.T) > 2) continue;
      let ins = 0; for (const pt of samples(A.e).pts) if (sd(pt) > 3) ins += STEP;
      if (ins >= 6) push('ARROW_THROUGH_BOX', ident(A.e), 'đi xuyên khung ' + Math.round(rw) + 'x' + Math.round(rh) + ' tại ' + Math.round(rx) + ',' + Math.round(ry) + ' (' + Math.round(ins) + 'px bên trong)', A.b); }
  }
  // đầu mũi tên (tam giác) đè lên chữ
  for (const A of arrows) { const nx = -A.u.y, ny = A.u.x, hw = 0.45 * A.size;
    for (const a of item) { let h = 0;
      for (let s = 0.1; s <= 1; s += 0.15) for (let w = -1; w <= 1; w += 0.5) {
        const pt = {x: A.T.x - A.u.x * s * A.size + nx * w * s * hw, y: A.T.y - A.u.y * s * A.size + ny * w * s * hw};
        if (inBox(pt, a.b)) h++; }
      if (h >= 2) add('ARROWHEAD_ON_TEXT', a, 'bởi đầu mũi tên ' + ident(A.e)); }
  }

  // độ tương phản chữ so với nền tô đặc gần nhất phía sau
  const col = c => { c = (c || '').trim().toLowerCase(); if (c === 'white') c = '#ffffff'; if (c === 'black') c = '#000000';
    let m = /^#([0-9a-f]{6})$/.exec(c); if (m) { const n = parseInt(m[1], 16); return [n >> 16, (n >> 8) & 255, n & 255]; }
    m = /^#([0-9a-f]{3})$/.exec(c); return m ? [...m[1]].map(x => parseInt(x + x, 16)) : null; };
  const rl = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  for (const a of item) {
    if (a.halo) continue;
    const fg = col(a.el.getAttribute('fill') || '#000000'); if (!fg) continue;
    const pt = new DOMPoint(a.f.x + a.f.w / 2, a.f.y + a.f.h / 2); let bg = [255, 255, 255], unknown = false;
    for (let k = 0; k < a.i; k++) { const e = all[k], t = e.tagName.toLowerCase();
      if (t === 'image') { try { if (hit({x: pt.x, y: pt.y, w: 0.1, h: 0.1}, bb(e))) unknown = true; } catch (_) {} continue; }
      if (!['rect', 'circle', 'ellipse', 'polygon', 'path'].includes(t)) continue;
      const c = col(e.getAttribute('fill')); if (!c) continue;
      let inside = false; try { inside = e.isPointInFill(pt); } catch (_) {}
      if (!inside) continue;
      const op = parseFloat(e.getAttribute('fill-opacity') || 1) * parseFloat(e.getAttribute('opacity') || 1);
      bg = bg.map((v, q) => op * c[q] + (1 - op) * v); }
    if (unknown) continue;
    const l1 = rl(fg), l2 = rl(bg), ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    if (ratio < 3) add('LOW_CONTRAST', a, 'tỉ lệ ' + Math.round(ratio * 10) / 10 + ':1 (chữ ' + a.el.getAttribute('fill') + ' trên nền rgb(' + bg.map(Math.round).join(',') + '))');
  }

  // khoảng trống thừa phía đáy khung và chữ sát viền khung
  const gb = e => { if (e.tagName.toLowerCase() === 'text') { if (!e.textContent.trim()) return null; const t = e.getBBox();
      return {x: t.x, y: t.y + t.height * 0.2, w: t.width, h: t.height * 0.6}; }
    try { const t = e.getBBox(); return {x: t.x, y: t.y, w: t.width, h: t.height}; } catch (_) { return null; } };
  const shapes = [...svg.querySelectorAll('text,rect,circle,ellipse,path,polygon,line,polyline,image')]
    .filter(e => !e.closest('defs')).map(e => ({e, b: gb(e)})).filter(i => i.b);
  const bg = i => i.b.w >= vb.width - 5 && i.b.h >= vb.height - 5;
  const boxes = shapes.filter(i => { const st = i.e.getAttribute('stroke');
    return i.e.tagName.toLowerCase() === 'rect' && st && st !== 'none' && i.b.w > 40 && i.b.h > 30 && !bg(i); });
  for (const R of boxes) {
    const r = R.b; let mb = -1e9, mt = 1e9, ml = 1e9, n = 0;
    for (const c of shapes) {
      if (c === R || bg(c)) continue;
      const cx = c.b.x + c.b.w / 2, cy = c.b.y + c.b.h / 2;
      if (cx <= r.x || cx >= r.x + r.w || cy <= r.y || cy >= r.y + r.h || c.b.w * c.b.h >= 0.98 * r.w * r.h) continue;
      n++; mb = Math.max(mb, c.b.y + c.b.h); mt = Math.min(mt, c.b.y); ml = Math.min(ml, c.b.x);
    }
    if (!n) continue;
    const bot = r.y + r.h - mb, pad = Math.max(mt - r.y, ml - r.x, 6);
    if (bot >= 22 && bot >= 2 * pad) out.push({rule: 'EMPTY_SPACE', text: 'khung ' + Math.round(r.w) + 'x' + Math.round(r.h) + ' tại ' + Math.round(r.x) + ',' + Math.round(r.y),
      detail: 'dư ' + Math.round(bot) + 'px dưới đáy, đệm trên/trái chỉ ' + Math.round(pad) + 'px', x: Math.round(r.x), y: Math.round(r.y + r.h), w: Math.round(r.w), h: 0});
  }
  const holders = shapes.filter(i => { const st = i.e.getAttribute('stroke');
    return i.e.tagName.toLowerCase() === 'rect' && st && st !== 'none' && i.b.w > 8 && i.b.h > 8 && !bg(i); });
  for (const a of item) {
    let best = null;
    for (const R of holders) { const r = R.b, b = a.b;
      if (b.x >= r.x - 0.5 && b.y >= r.y - 0.5 && b.x + b.w <= r.x + r.w + 0.5 && b.y + b.h <= r.y + r.h + 0.5 && (!best || r.w * r.h < best.w * best.h)) best = r; }
    if (!best) continue;
    const d = Math.min(a.b.x - best.x, a.b.y - best.y, best.x + best.w - a.b.x - a.b.w, best.y + best.h - a.b.y - a.b.h);
    if (d < 2.5) add('TIGHT_TEXT', a, 'cách viền khung ' + Math.round(d * 10) / 10 + 'px');
  }

  // khoảng trống dọc giữa các khối nội dung (ví dụ giữa panel cuối và dòng nguồn)
  const iv = [];
  for (const sh of shapes) { if (bg(sh)) continue;
    let t; try { t = sh.e.getBBox(); } catch (_) { continue; }
    iv.push([t.y, t.y + t.height]); }
  iv.sort((p, q) => p[0] - q[0]);
  if (iv.length) { let cur = iv[0][1];
    for (const [st, en] of iv) {
      if (st - cur > 22) out.push({rule: 'BIG_GAP', text: 'khoảng trống dọc ' + Math.round(st - cur) + 'px',
        detail: 'từ y=' + Math.round(cur) + ' đến y=' + Math.round(st) + ' (không có phần tử nào)', x: 0, y: Math.round(cur), w: vb.width, h: Math.round(st - cur)});
      cur = Math.max(cur, en); } }

  const small = item.filter(a => a.fs < minFont);
  if (small.length) {
    const s = small.slice().sort((p, q) => p.fs - q.fs);
    out.push({rule: 'SMALL_FONT', text: small.length + ' dòng < ' + minFont + 'px (nhỏ nhất ' + s[0].fs + 'px)',
      detail: 'vd: ' + s.slice(0, 3).map(a => '"' + a.s + '"').join(', '), x: 0, y: 0, w: 0, h: 0});
  }
  const pre = document.createElement('pre'); pre.id = 'res'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
}
window.addEventListener('load', () => run(__MIN_FONT__));
</script>
"""

ERRORS = {"OVERLAP", "CROSS_EDGE", "COVERED", "LINE_THROUGH", "OUT_OF_CANVAS", "SHAPE_OUT_OF_CANVAS", "ARROW_TOO_SHORT", "SHAPE_CROSS_EDGE"}
WARNS = {"SMALL_FONT", "EMPTY_SPACE", "TIGHT_TEXT", "BIG_GAP", "LOW_CONTRAST"}
LEVELS = ("ERROR", "WARN ", "REVIEW")
POLICY = ("Lint chỉ báo dấu hiệu nghi ngờ, không biết ý đồ của hình. Mỗi dòng: sửa nếu là lỗi thật, giữ và nêu lý do nếu cố ý.\n"
          "Khi bố cục xung đột với độ chính xác nội dung (số liệu, công thức, quan hệ hình học), ưu tiên nội dung, không đổi nội dung chỉ để hết báo.")


def level(rule):
    return "ERROR" if rule in ERRORS else "WARN " if rule in WARNS else "REVIEW"


def lint_svg(path, min_font, chrome):
    with open(path, encoding="utf-8") as fh:
        svg = fh.read()
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "page.html")
        with open(page, "w", encoding="utf-8") as fh:
            fh.write('<!doctype html><meta charset="utf-8"><body style="margin:0">' + svg + JS.replace("__MIN_FONT__", str(min_font)))
        r = subprocess.run([chrome, "--headless=new", "--disable-gpu", f"--user-data-dir={tmp}", "--virtual-time-budget=3000",
                            "--dump-dom", "file://" + page], capture_output=True, text=True)
    m = re.search(r'<pre id="res">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise RuntimeError("Chrome không trả kết quả cho " + path)
    seen, issues = set(), []
    for it in json.loads(html.unescape(m.group(1))):
        key = (it["rule"], it["text"], it["detail"])
        if key not in seen:
            seen.add(key)
            issues.append(it)
    return issues


def collect(paths):
    files = []
    for p in paths:
        files += sorted(glob.glob(os.path.join(p, "**", "*.svg"), recursive=True)) if os.path.isdir(p) else [p]
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+", help="file .svg hoặc thư mục (quét đệ quy)")
    ap.add_argument("--min-font", type=float, default=6.5, help="ngưỡng cảnh báo SMALL_FONT, px trên viewBox (mặc định 6.5)")
    ap.add_argument("--json", action="store_true", help="in kết quả dạng JSON")
    args = ap.parse_args()

    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        sys.exit("Cần google-chrome hoặc chromium trong PATH")
    files = collect(args.paths)
    if not files:
        sys.exit("Không tìm thấy file .svg")

    report = {f: lint_svg(f, args.min_font, chrome) for f in files}
    count = {lv: sum(1 for v in report.values() for i in v if level(i["rule"]) == lv) for lv in LEVELS}
    if args.json:
        print(json.dumps({f: [dict(i, level=level(i["rule"]).strip()) for i in v] for f, v in report.items()}, ensure_ascii=False, indent=2))
    else:
        for f, issues in report.items():
            for i in sorted(issues, key=lambda i: (LEVELS.index(level(i["rule"])), i["rule"], i["y"], i["x"])):
                where = f' @({i["x"]},{i["y"]},{i["w"]}x{i["h"]})' if i["rule"] not in ("SMALL_FONT", "NOT_EVALUATED") else ""
                detail = f' {i["detail"]}' if i["detail"] else ""
                print(f'{f}: {level(i["rule"])} {i["rule"]}{where} "{i["text"]}"{detail}' if i["rule"] != "SMALL_FONT"
                      else f'{f}: {level(i["rule"])} {i["rule"]} {i["text"]} ({i["detail"]})')
        print(f"\n{len(files)} file, {count['ERROR']} lỗi, {count['WARN ']} cảnh báo, {count['REVIEW']} cần xem lại\n{POLICY}")
    sys.exit(1 if count["ERROR"] else 0)


if __name__ == "__main__":
    main()
