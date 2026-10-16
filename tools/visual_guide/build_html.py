#!/usr/bin/env python3
"""Build <topic>/index.html (single static page, no CDN, opens from disk) from <topic>/NN-*/chu-thich.md.

chu-thich.md format: see tmp/02_decisions/2026-10-11_hoc-theo-hinh.md. Parts without a folder are listed in the
table of contents as "chua lam" (names come from the topic README, section "## Tên các phần": rows "| N | name |");
"Hinh N.k" in the text becomes an anchor link when that figure exists, otherwise plain text followed by "(chưa làm)".
A figure block with a line "Trạng thái: chờ <ly do>" and no PNG is rendered as a placeholder card "chưa có số: <ly do>".
"Hình gốc:" paths are relative to the topic directory. The page title is the first heading of the topic README.
Notes: <topic>/NN-*/_notes/<slug>/chu-thich.md (heading "# Ghi chú chuyên đề: <ten>", figures "## Hình C.k (slug) [tier]")
become a popup opened by the "Ghi chú (n)" button of part NN; they are not counted in the learning progress.
Usage: python3 build_html.py [topic_dir ...]   (default: every topic under docs/tools/visual_guide with NN-*/chu-thich.md)
"""
import glob
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TOPIC = HERE        # topic directory being built; set in main()
PART_NAMES = {}     # part number -> name, read from the topic README
FIG_RE = re.compile(r"Hình (\d+)\.(\d+)")
NOTE_FIG_RE = re.compile(r"Hình ([A-Z])\.(\d+)")
TIER_CLASS = {"T1 RK3588": "t1", "T2 chung": "t2", "T3 đo": "t3"}


# ---------------------------------------------------------------- parsing
def split_row(line):
    cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
    return [c.strip().replace("\\|", "|") for c in cells]


def sections(lines, prefix):
    """Split lines into [(heading, [body lines])] at headings starting with prefix."""
    out, cur = [], None
    for ln in lines:
        if ln.startswith(prefix):
            cur = (ln[len(prefix):].strip(), [])
            out.append(cur)
        elif cur is not None:
            cur[1].append(ln)
    return out


def parse_part(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read().split("\n")
    m = re.match(r"# (?:Phần (\d+)|Ghi chú chuyên đề): (.*)", text[0])
    part = dict(num=int(m.group(1)) if m.group(1) else None, title=m.group(2).strip(), dir=os.path.dirname(path), figures=[],
                question="", mistakes=[], quiz=[], sources=[])
    body = text[1:]
    for head, lines in sections(body, "## "):
        content = [ln for ln in lines if ln.strip()]
        if head == "Câu hỏi mở đầu":
            part["question"] = " ".join(content)
        elif head.startswith("Hình "):
            part["figures"].append(parse_figure(head, lines, part["dir"]))
        elif head == "Hiểu sai thường gặp":
            for ln in content:
                if ln.startswith("- "):
                    wrong, _, right = ln[2:].partition(" -> ")
                    part["mistakes"].append((wrong.strip(), right.strip()))
        elif head == "Câu hỏi tự kiểm":
            for h3, l3 in sections(lines, "### "):
                m3 = re.match(r"Câu (\d+) \((.*)\)", h3)
                c3 = [x for x in l3 if x.strip()]
                answer = next((x[len("Đáp án:"):].strip() for x in c3 if x.startswith("Đáp án:")), "")
                question = " ".join(x for x in c3 if not x.startswith("Đáp án:"))
                part["quiz"].append(dict(n=m3.group(1), kind=m3.group(2), q=question, a=answer))
        elif head == "Nguồn":
            for ln in content:
                if ln.startswith("|"):
                    cells = split_row(ln)
                    if len(cells) == 5 and cells[0] != "Hình" and not set(cells[0]) <= set("-: "):
                        part["sources"].append(cells)
    return part


def parse_figure(head, lines, part_dir):
    m = re.match(r"Hình (\d+|[A-Z])\.(\d+) \((.*?)\) \[(.*?)\]", head)
    fig = dict(part=int(m.group(1)) if m.group(1).isdigit() else m.group(1), k=int(m.group(2)), slug=m.group(3), tier=m.group(4), predict="",
               caption=[], more="", measure="", concept="", originals=[], pending="")
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("Dự đoán trước khi xem:"):
            fig["predict"] = s[len("Dự đoán trước khi xem:"):].strip()
        elif s.startswith("Hình gốc:"):
            p = s[len("Hình gốc:"):].strip().split(" ")[0]
            note = s[len("Hình gốc:"):].strip()[len(p):].strip(" ()")
            fig["originals"].append((os.path.relpath(os.path.normpath(os.path.join(TOPIC, p)), TOPIC), note))
        elif s.startswith("Đọc thêm:"):
            more, _, measure = s[len("Đọc thêm:"):].partition("Số đo:")
            fig["more"], fig["measure"] = more.strip(), measure.strip()
        elif s.startswith("Số đo:"):
            fig["measure"] = s[len("Số đo:"):].strip()
        elif s.startswith("Trạng thái:"):
            state = s[len("Trạng thái:"):].strip()
            fig["pending"] = state[len("chờ"):].strip() if state.startswith("chờ") else state
        elif s.startswith("Khái niệm"):
            fig["concept"] = s.split(":", 1)[1].strip()
        else:
            fig["caption"].append(s)
    fig["caption"] = " ".join(fig["caption"])
    return fig


# ---------------------------------------------------------------- rendering
def make_linker(existing):
    def link(text):
        """Escape text; turn 'Hình N.k' into an anchor when the figure exists, else mark it as not done."""
        esc = html.escape(text, quote=False)

        def sub(m):
            key = (int(m.group(1)), int(m.group(2)))
            if key in existing:
                return f'<a class="xref" href="#hinh-{key[0]}-{key[1]}">{m.group(0)}</a>'
            return f'{m.group(0)} <span class="todo">(chưa làm)</span>'
        return FIG_RE.sub(sub, esc)
    return link


def render_figure(fig, part, link, fid=None, learnable=True):
    label = f"{fig['part']}.{fig['k']}"
    fid = fid or f"hinh-{label.replace('.', '-')}"
    png = os.path.relpath(os.path.join(part["dir"], fig["slug"] + ".png"), TOPIC)
    rows = [s for s in part["sources"] if s[0] == label]
    h = [f'<article class="fig" id="{fid}" data-fig="{fid}">',
         f'<header><span class="tier {TIER_CLASS.get(fig["tier"], "t1")}">{html.escape(fig["tier"])}</span>'
         f'<h3>Hình {label} <small>{html.escape(fig["slug"])}</small></h3>'
         + (f'<label class="learned"><input type="checkbox" data-learn="{fid}"> đã học</label>' if learnable else '')
         + '</header>']
    predict = bool(fig["predict"])
    if predict:
        h.append(f'<p class="predict"><b>Dự đoán trước khi xem:</b> {link(fig["predict"])}</p>'
                 f'<button class="reveal" type="button">Xem kết quả</button>')
    h.append(f'<div class="fig-body"{" hidden" if predict else ""}>')
    has_png = os.path.exists(os.path.join(part["dir"], fig["slug"] + ".png"))
    if has_png:
        h.append(f'<img class="zoomable" src="{png}" alt="Hình {label}" loading="lazy">')
    if fig["pending"]:
        h.append(f'<div class="pending"><b>chưa có số:</b> {link(fig["pending"])}</div>')
    h.append(f'<p class="caption">{link(fig["caption"])}</p>')
    meta = []
    if fig["more"]:
        meta.append(f'<span><b>Đọc thêm:</b> {link(fig["more"])}</span>')
    if fig["measure"]:
        meta.append(f'<span><b>Số đo:</b> {link(fig["measure"])}</span>')
    if fig["concept"]:
        meta.append(f'<span><b>Khái niệm:</b> {link(fig["concept"])}</span>')
    if meta:
        h.append('<p class="meta">' + " &nbsp;|&nbsp; ".join(meta) + "</p>")
    if fig["originals"] and not fig["pending"]:
        h.append('<button class="orig-toggle" type="button">Hiện hình gốc</button><div class="originals hidden">')
        for path, note in fig["originals"]:
            h.append(f'<figure><img class="zoomable" src="{path}" alt="hình gốc" loading="lazy">'
                     f'<figcaption>{link(note)}</figcaption></figure>')
        h.append("</div>")
    h.append(f'<details class="src"><summary>Nguồn ({len(rows)} dòng)</summary><table><thead><tr>'
             "<th>Nội dung</th><th>Tier</th><th>Nguồn</th><th>Nguyên văn ngắn</th></tr></thead><tbody>")
    for _, content, tier, src, quote in rows:
        h.append(f"<tr><td>{html.escape(content)}</td><td>{html.escape(tier)}</td><td>{html.escape(src)}</td>"
                 f"<td>{html.escape(quote)}</td></tr>")
    h.append("</tbody></table></details></div></article>")
    return "\n".join(h)


def render_mistakes(part, link, gated=""):
    h = []
    if part["mistakes"]:
        h.append(f'<div class="mistakes"{gated}><h3>Hiểu sai thường gặp</h3><table><thead><tr><th>Hiểu sai</th>'
                 "<th>Đúng, kèm nguồn</th></tr></thead><tbody>")
        for wrong, right in part["mistakes"]:
            h.append(f"<tr><td>{link(wrong)}</td><td>{link(right)}</td></tr>")
        h.append("</tbody></table></div>")
    return h


def render_quiz(part, link):
    h = []
    if part["quiz"]:
        h.append('<div class="quiz"><h3>Câu hỏi tự kiểm</h3>')
        for q in part["quiz"]:
            h.append(f'<div class="q"><p><b>Câu {q["n"]}</b> <span class="kind">{html.escape(q["kind"])}</span><br>'
                     f'{link(q["q"])}</p><details><summary>Đáp án</summary><p>{link(q["a"])}</p></details></div>')
        h.append("</div>")
    return h


def render_part(part, link, notes=()):
    button = (f' <button class="notes-open" type="button" data-notes="{part["num"]}">Ghi chú ({len(notes)})</button>'
              if notes else "")
    h = [f'<section class="part" id="phan-{part["num"]}" data-part="{part["num"]}">',
         f'<h2>Phần {part["num"]}: {html.escape(part["title"])}{button}</h2>',
         f'<p class="opening"><b>Câu hỏi mở đầu.</b> {link(part["question"])}</p>']
    h += [render_figure(f, part, link) for f in part["figures"]]
    gated = " data-gated hidden" if any(f["predict"] for f in part["figures"]) else ""
    h += render_mistakes(part, link, gated) + render_quiz(part, link)
    if notes:
        h.append('<div class="notes-store" hidden>' + "\n".join(render_note(n, part["num"], link) for n in notes)
                 + "</div>")
    h.append("</section>")
    return "\n".join(h)


def render_note(note, part_num, link):
    """One note as a popup unit: opening question, then items (figures, mistakes, quiz) shown one at a time."""
    slug = os.path.basename(note["dir"])
    nid = f"note-{part_num}-{slug}"
    labels = {f"{f['part']}.{f['k']}" for f in note["figures"]}

    def nlink(text):
        def sub(m):
            lab = f"{m.group(1)}.{m.group(2)}"
            if lab in labels:
                return f'<a class="xref note-xref" href="#{nid}-{m.group(1)}-{m.group(2)}" data-label="{lab}">{m.group(0)}</a>'
            return f'{m.group(0)} <span class="todo">(không có trong ghi chú)</span>'
        return NOTE_FIG_RE.sub(sub, link(text))

    items = [(f"{f['part']}.{f['k']}",
              [render_figure(f, note, nlink, fid=f"{nid}-{f['part']}-{f['k']}", learnable=False)]) for f in note["figures"]]
    items += [(name, lines) for name, lines in
              (("Hiểu sai", render_mistakes(note, nlink)), ("Tự kiểm", render_quiz(note, nlink))) if lines]
    h = [f'<div class="note" id="{nid}" data-title="{html.escape(note["title"])}" '
         f'data-question="{html.escape(note["question"])}" data-count="{len(note["figures"])}">',
         f'<h3 class="note-title">{html.escape(note["title"])}</h3>',
         f'<p class="opening"><b>Câu hỏi mở đầu.</b> {nlink(note["question"])}</p>', '<div class="note-items">']
    for label, lines in items:
        h.append(f'<div class="ni" data-label="{html.escape(label)}">' + "\n".join(lines) + "</div>")
    h.append("</div></div>")
    return "\n".join(h)


def render_toc(parts, title, note_counts=None):
    by_num = {p["num"]: p for p in parts}
    h = [f'<nav id="toc"><h1>{html.escape(title)}</h1><p class="progress">Đã học: <b id="prog-all">0/0</b> hình</p><ul>']
    for n in sorted(set(PART_NAMES) | set(by_num)):
        p = by_num.get(n)
        if p is None:
            h.append(f'<li class="todo-part"><span>Phần {n}: {html.escape(PART_NAMES[n])}</span> '
                     '<span class="todo">(chưa làm)</span></li>')
            continue
        h.append(f'<li><a href="#phan-{n}" data-part-link="{n}">Phần {n}: {html.escape(p["title"])}</a> '
                 f'<span class="prog" id="prog-{n}"></span>'
                 + (f' <span class="prog">({note_counts[n]} ghi chú)</span>' if note_counts and note_counts.get(n) else "")
                 + "<ul>")
        for f in p["figures"]:
            h.append(f'<li><a href="#hinh-{f["part"]}-{f["k"]}">Hình {f["part"]}.{f["k"]}</a></li>')
        h.append("</ul></li>")
    h.append("</ul></nav>")
    return "\n".join(h)


CSS = """
:root{--ink:#222;--gray:#777;--line:#ccc;--blue:#1E5BB8;--green:#2E7D32;--red:#C62828;--band:#f5f5f5}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--ink);font:17px/1.55 "Times New Roman",Times,"Liberation Serif",serif;display:flex}
#toc{position:sticky;top:0;align-self:flex-start;width:290px;height:100vh;overflow:auto;padding:14px 16px;
 border-right:1px solid var(--line);background:var(--band);font-size:15px;flex:none}
#toc h1{font-size:19px;margin:0 0 6px}
#toc ul{list-style:none;margin:0;padding:0}
#toc li{margin:3px 0}
#toc ul ul{padding-left:16px;font-size:14px}
#toc a{color:var(--ink);text-decoration:none}
#toc a:hover{text-decoration:underline}
#toc a.current{color:var(--blue);font-weight:700}
.prog,.progress{color:var(--gray);font-size:14px}
.todo,.todo-part{color:var(--gray);font-style:italic}
main{max-width:1100px;padding:10px 28px 80px;min-width:0}
.part{border-top:2px solid var(--ink);margin-top:34px;padding-top:6px}
.part h2{font-size:26px;margin:8px 0}
.opening,.predict{background:var(--band);border-left:4px solid var(--blue);padding:8px 12px;margin:10px 0}
.predict{border-left-color:var(--red)}
.fig{border:1px solid var(--line);border-radius:6px;padding:10px 14px;margin:18px 0}
.fig header{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.fig h3{margin:0;font-size:20px}
.fig h3 small{color:var(--gray);font-weight:400;font-size:14px;margin-left:6px}
.learned{margin-left:auto;font-size:15px;cursor:pointer}
.tier{border:1.8px solid;border-radius:11px;padding:0 9px;font-weight:700;font-size:14px;background:#fff}
.t1{color:var(--blue)}.t2{color:var(--green)}.t3{color:var(--red)}
.fig img{max-width:100%;height:auto;border:1px solid #e3e3e3;cursor:zoom-in;display:block;margin:10px auto}
.caption{margin:8px 0}
.pending{border:2px dashed var(--red);background:#fff8f8;border-radius:6px;padding:26px 16px;margin:10px 0;text-align:center}
.meta{color:#444;font-size:15px;margin:6px 0}
.xref{color:var(--blue)}
button{font:inherit;font-size:15px;border:1px solid #999;background:#fff;border-radius:4px;padding:3px 10px;cursor:pointer}
button:hover{background:var(--band)}
.originals figure{margin:10px 0}
.originals img{border:1px solid var(--line)}
figcaption{font-size:14px;font-style:italic;color:#444;text-align:center}
.hidden,[hidden]{display:none!important}
details.src{margin-top:10px;font-size:15px}
table{border-collapse:collapse;width:100%;font-size:14.5px}
th,td{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
th{background:#e8e8e8}
.mistakes,.quiz{margin:22px 0}
.mistakes h3,.quiz h3{font-size:20px;margin:0 0 6px}
.mistakes{border:1px solid var(--red);border-radius:6px;padding:8px 12px;background:#fff8f8}
.q{border-bottom:1px solid #e6e6e6;padding:6px 0}
.kind{color:var(--gray);font-size:14px;border:1px solid var(--line);border-radius:8px;padding:0 7px}
details summary{cursor:pointer;color:var(--blue)}
#zoom{position:fixed;inset:0;background:rgba(255,255,255,.97);z-index:50;display:none;overflow:hidden;touch-action:none}
#zoom.open{display:block}
#zoom img{position:absolute;left:0;top:0;transform-origin:0 0;max-width:none;border:0;margin:0;cursor:grab;user-select:none}
#zoom .bar{position:fixed;top:8px;right:12px;display:flex;gap:8px;z-index:51}
#zoom .hint{position:fixed;left:12px;bottom:8px;color:var(--gray);font-size:14px}
.notes-open{margin-left:12px;font-size:14px;vertical-align:middle;border-color:var(--blue);color:var(--blue)}
#notes-modal{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:40;display:flex;align-items:center;justify-content:center;padding:3vh 3vw}
#notes-modal[hidden]{display:none}
.nm-box{background:#fff;border-radius:8px;width:min(1100px,94vw);max-height:94vh;display:flex;flex-direction:column;box-shadow:0 8px 30px rgba(0,0,0,.35)}
.nm-bar{display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:1px solid var(--line)}
.nm-title{flex:1;font-size:18px}
.nm-body{overflow:auto;padding:6px 18px 18px}
.nm-filter{width:100%;font:inherit;font-size:15px;padding:4px 8px;margin:8px 0;border:1px solid #999;border-radius:4px}
.nm-card{display:block;width:100%;text-align:left;border:1px solid var(--line);border-radius:6px;padding:8px 12px;margin:8px 0;background:#fff}
.nm-card b{display:block;font-size:18px}
.nm-card span{display:block;color:#444;font-size:15px}
.nm-card small{color:var(--gray)}
.note-title{font-size:22px;margin:10px 0 4px}
.note-nav{display:flex;align-items:center;gap:6px;margin:10px 0;position:sticky;top:0;background:#fff;padding:4px 0;z-index:2}
.note-tabs{display:flex;gap:6px;overflow-x:auto;flex:1;padding-bottom:2px}
.note-tabs button{white-space:nowrap}
.note-tabs button.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.note-pos{color:var(--gray);font-size:14px;white-space:nowrap}
.ni:not(.on){display:none}
@media (max-width:900px){body{display:block}#toc{position:static;width:auto;height:auto}main{padding:10px 14px}}
"""

JS = r"""
(function(){
  var KEY='learned-v1:'+document.title, learned={};
  try{ learned=JSON.parse(localStorage.getItem(KEY)||'{}')||{}; }catch(e){ learned={}; }
  function save(){ try{ localStorage.setItem(KEY, JSON.stringify(learned)); }catch(e){} }
  function updateProgress(){
    var boxes=document.querySelectorAll('input[data-learn]'), done=0, per={}, tot={};
    boxes.forEach(function(b){
      var part=b.closest('.part').dataset.part;
      tot[part]=(tot[part]||0)+1;
      if(b.checked){ done++; per[part]=(per[part]||0)+1; }
    });
    document.getElementById('prog-all').textContent=done+'/'+boxes.length;
    Object.keys(tot).forEach(function(p){
      var el=document.getElementById('prog-'+p);
      if(el) el.textContent='('+(per[p]||0)+'/'+tot[p]+')';
    });
  }
  document.querySelectorAll('input[data-learn]').forEach(function(b){
    b.checked=!!learned[b.dataset.learn];
    b.addEventListener('change',function(){ learned[b.dataset.learn]=b.checked; save(); updateProgress(); });
  });
  updateProgress();

  document.querySelectorAll('.reveal').forEach(function(btn){
    btn.addEventListener('click',function(){
      btn.parentNode.querySelector('.fig-body').hidden=false; btn.hidden=true;
      var pt=btn.closest('.part');
      if(pt) pt.querySelectorAll('[data-gated]').forEach(function(el){ el.hidden=false; });
    });
  });
  document.querySelectorAll('.orig-toggle').forEach(function(btn){
    btn.addEventListener('click',function(){
      var box=btn.nextElementSibling, open=box.classList.toggle('hidden');
      btn.textContent=open?'Hiện hình gốc':'Ẩn hình gốc';
    });
  });

  // current part highlight
  var links={}; document.querySelectorAll('[data-part-link]').forEach(function(a){ links[a.dataset.partLink]=a; });
  var parts=[].slice.call(document.querySelectorAll('.part'));
  function onScroll(){
    var cur=null;
    parts.forEach(function(p){ if(p.getBoundingClientRect().top<=120) cur=p.dataset.part; });
    if(cur===null && parts.length) cur=parts[0].dataset.part;
    Object.keys(links).forEach(function(k){ links[k].classList.toggle('current',k===cur); });
  }
  window.addEventListener('scroll',onScroll,{passive:true}); onScroll();

  // zoom overlay: wheel zoom at cursor, drag to pan, double click resets
  var ov=document.getElementById('zoom'), zi=ov.querySelector('img'), s=1, tx=0, ty=0, fit=1, moved=false, drag=null;
  function apply(){ zi.style.transform='translate('+tx+'px,'+ty+'px) scale('+s+')'; }
  function reset(){
    var w=zi.naturalWidth, h=zi.naturalHeight;
    fit=Math.min(innerWidth/w, innerHeight/h, 1); s=fit;
    tx=(innerWidth-w*s)/2; ty=(innerHeight-h*s)/2; apply();
  }
  function open(src){ zi.onload=reset; zi.src=src; ov.classList.add('open'); if(zi.complete&&zi.naturalWidth) reset(); }
  function close(){ ov.classList.remove('open'); }
  document.addEventListener('click',function(e){
    if(e.target.classList&&e.target.classList.contains('zoomable')) open(e.target.src);
  });
  ov.querySelector('.close').addEventListener('click',close);
  ov.querySelector('.reset').addEventListener('click',reset);
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'){ if(ov.classList.contains('open')) close(); else closeNotes(); }
  });
  ov.addEventListener('wheel',function(e){
    e.preventDefault();
    var f=e.deltaY<0?1.15:1/1.15, ns=Math.max(fit*0.5,Math.min(s*f,12));
    tx=e.clientX-(e.clientX-tx)*(ns/s); ty=e.clientY-(e.clientY-ty)*(ns/s); s=ns; apply();
  },{passive:false});
  ov.addEventListener('pointerdown',function(e){
    if(e.target.closest('.bar')) return;
    drag={x:e.clientX,y:e.clientY,tx:tx,ty:ty}; moved=false; ov.setPointerCapture(e.pointerId);
  });
  ov.addEventListener('pointermove',function(e){
    if(!drag) return;
    var dx=e.clientX-drag.x, dy=e.clientY-drag.y;
    if(Math.abs(dx)+Math.abs(dy)>4) moved=true;
    tx=drag.tx+dx; ty=drag.ty+dy; apply();
  });
  ov.addEventListener('pointerup',function(e){
    var wasClick=drag&&!moved&&e.target===ov; drag=null;
    if(wasClick) close();
  });
  zi.addEventListener('dblclick',reset);

  // notes popup: part button -> list of notes -> one item (figure, mistakes, quiz) at a time
  var nm=document.getElementById('notes-modal'), nbody=nm.querySelector('.nm-body'), ntitle=nm.querySelector('.nm-title'),
      nback=nm.querySelector('.nm-back'), curNote=null, curStore=null, curPart=null, showAt=null;
  function el(tag,cls,text){ var e=document.createElement(tag); if(cls) e.className=cls; if(text!=null) e.textContent=text; return e; }
  function parkNote(){
    if(curNote){
      if(curNote._ph){ curNote._ph.replaceWith(curNote); curNote._ph=null; }
      else if(curStore){ curStore.appendChild(curNote); }
      curNote=null;
    }
  }
  function showList(partNum){
    parkNote(); curPart=partNum; nback.hidden=true;
    curStore=document.querySelector('#phan-'+partNum+' .notes-store');
    var notes=[].slice.call(curStore.children);
    ntitle.textContent='Ghi chú của Phần '+partNum+' ('+notes.length+')';
    nbody.innerHTML='';
    var filter=null;
    if(notes.length>8){
      filter=el('input','nm-filter'); filter.type='search'; filter.placeholder='Lọc theo tiêu đề...';
      nbody.appendChild(filter);
    }
    var cards=notes.map(function(n,i){
      var c=el('button','nm-card'); c.type='button';
      c.appendChild(el('b',null,(i+1)+'. '+n.dataset.title));
      c.appendChild(el('span',null,n.dataset.question));
      c.appendChild(el('small',null,n.dataset.count+' hình'));
      c.addEventListener('click',function(){ openNote(n,true); });
      nbody.appendChild(c); return c;
    });
    if(filter) filter.addEventListener('input',function(){
      var q=filter.value.toLowerCase();
      cards.forEach(function(c,i){ c.hidden=notes[i].dataset.title.toLowerCase().indexOf(q)<0; });
    });
    nm.hidden=false; document.body.style.overflow='hidden';
    if(notes.length===1) openNote(notes[0],false);
  }
  function openNote(n,canBack){
    parkNote();
    var ph=document.createComment('ph');
    n.replaceWith(ph); n._ph=ph;
    nbody.innerHTML=''; nbody.appendChild(n); curNote=n; nback.hidden=!canBack; ntitle.textContent='';
    var items=[].slice.call(n.querySelectorAll('.note-items > .ni'));
    if(!n.querySelector('.note-nav')){
      var nav=el('div','note-nav'), tabs=el('div','note-tabs'), prev=el('button',null,'Trước'), next=el('button',null,'Sau'),
          pos=el('span','note-pos');
      prev.type=next.type='button';
      var tb=items.map(function(it,i){
        var b=el('button',null,it.dataset.label); b.type='button'; b.addEventListener('click',function(){ show(i); }); tabs.appendChild(b); return b;
      });
      function show(i){
        i=Math.max(0,Math.min(items.length-1,i));
        items.forEach(function(it,j){ it.classList.toggle('on',j===i); tb[j].classList.toggle('on',j===i); });
        pos.textContent=(i+1)+'/'+items.length; n._at=i;
        tb[i].scrollIntoView({block:'nearest',inline:'nearest'});
      }
      prev.addEventListener('click',function(){ show(n._at-1); });
      next.addEventListener('click',function(){ show(n._at+1); });
      if(items.length>1){
        nav.appendChild(tabs);
        if(items.length>6){ nav.insertBefore(prev,tabs); nav.appendChild(pos); nav.appendChild(next); }
        n.querySelector('.note-items').before(nav);
      }
      n._show=show; show(0);
    }
    nbody.scrollTop=0;
  }
  function closeNotes(){
    if(nm.hidden) return;
    parkNote(); nm.hidden=true; document.body.style.overflow='';
  }
  nback.addEventListener('click',function(){ showList(curPart); });
  nm.querySelector('.nm-close').addEventListener('click',closeNotes);
  nm.addEventListener('click',function(e){ if(e.target===nm) closeNotes(); });
  document.querySelectorAll('.notes-open').forEach(function(b){
    b.addEventListener('click',function(){ showList(b.dataset.notes); });
  });
  nm.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a.xref');
    if(!a) return;
    if(a.classList.contains('note-xref')){
      e.preventDefault();
      var it=curNote&&[].slice.call(curNote.querySelectorAll('.note-items > .ni')).findIndex(function(x){ return x.dataset.label===a.dataset.label; });
      if(it>=0) curNote._show(it);
    } else closeNotes();
  });
  document.addEventListener('keydown',function(e){
    if(nm.hidden||ov.classList.contains('open')||!curNote||!curNote._show) return;
    if(e.target.tagName==='INPUT') return;
    if(e.key==='ArrowLeft') curNote._show(curNote._at-1);
    else if(e.key==='ArrowRight') curNote._show(curNote._at+1);
  });
})();
"""


NOTES_MODAL = ('<div id="notes-modal" hidden><div class="nm-box"><div class="nm-bar">'
               '<button class="nm-back" type="button" hidden>Quay lại danh sách</button><b class="nm-title"></b>'
               '<button class="nm-close" type="button">Đóng (Esc)</button></div><div class="nm-body"></div></div></div>')


def read_topic_readme(topic):
    """Return (title, {part number: name}) from <topic>/README.md."""
    title, names = os.path.basename(topic), {}
    path = os.path.join(topic, "README.md")
    if os.path.isfile(path):
        in_names = False
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                if ln.startswith("# ") and title == os.path.basename(topic):
                    title = ln[2:].strip()
                elif ln.startswith("## "):
                    in_names = ln.strip() == "## Tên các phần"
                elif in_names and ln.startswith("|"):
                    c = split_row(ln)
                    if len(c) >= 2 and c[0].isdigit():
                        names[int(c[0])] = c[1]
    return title, names


def build(topic):
    global TOPIC
    TOPIC = os.path.abspath(topic)
    title, names = read_topic_readme(TOPIC)
    PART_NAMES.clear()
    PART_NAMES.update(names)
    paths = sorted(glob.glob(os.path.join(TOPIC, "[0-9][0-9]-*", "chu-thich.md")))
    parts = sorted((parse_part(p) for p in paths), key=lambda p: p["num"])
    existing = {(f["part"], f["k"]) for p in parts for f in p["figures"]}
    link = make_linker(existing)
    notes = {p["num"]: [] for p in parts}
    for path in sorted(glob.glob(os.path.join(TOPIC, "[0-9][0-9]-*", "_notes", "*", "chu-thich.md"))):
        owner = next((p for p in parts if p["dir"] == os.path.dirname(os.path.dirname(os.path.dirname(path)))), None)
        if owner is None:
            print(f"bỏ qua ghi chú (phần chưa có chu-thich.md): {os.path.relpath(path, ROOT)}")
            continue
        notes[owner["num"]].append(parse_part(path))
    body = "\n".join(render_part(p, link, notes[p["num"]]) for p in parts)
    page = (f'<!doctype html><html lang="vi"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
            f"{render_toc(parts, title, {n: len(v) for n, v in notes.items()})}<main>{body}</main>"
            '<div id="zoom"><div class="bar"><button class="reset" type="button">Đặt lại</button>'
            '<button class="close" type="button">Đóng (Esc)</button></div><img alt="">'
            '<div class="hint">Cuộn chuột để phóng to, kéo để di chuyển, nhấp ra ngoài hình để đóng.</div></div>'
            + NOTES_MODAL +
            f"<script>{JS}</script></body></html>")
    out = os.path.join(TOPIC, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"{os.path.relpath(out, ROOT)}: {len(parts)} phần, {len(existing)} hình, {len(page) // 1024} KB")


def main():
    topics = sys.argv[1:] or [os.path.dirname(os.path.dirname(p)) for p in
                              sorted(glob.glob(os.path.join(HERE, "*", "[0-9][0-9]-*", "chu-thich.md")))]
    for topic in dict.fromkeys(topics):
        build(topic)


if __name__ == "__main__":
    main()
