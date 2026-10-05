#!/usr/bin/env python3
"""mdslides: Markdown 转单文件 HTML 幻灯片。

用法: python -m mdslides deck.md -o deck.html [--title T] [--theme dark|light]
幻灯片以 `---` 独占一行分隔。输出为单个 HTML 文件，零外部请求。
"""
import argparse
import html
import os
import re
import sys

VERSION = "0.1.0"

# ---------- 行内解析 ----------

def inline(text):
    """**粗体** *斜体* `代码` ![img](src) [text](url)"""
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                  lambda m: '<img src="%s" alt="%s">' % (
                      html.escape(m.group(2), quote=True),
                      html.escape(m.group(1), quote=True)), text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  lambda m: '<a href="%s">%s</a>' % (
                      html.escape(m.group(2), quote=True), m.group(1)), text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


# ---------- 块解析 ----------

HR_RE = re.compile(r"^\s*---\s*$")
NOTE_RE = re.compile(r"<!--\s*note:\s*(.*?)\s*-->", re.S)


def md_to_html(md):
    """返回 (slides_html_list, notes_list)。"""
    lines = md.split("\n")
    # 切分幻灯片
    raw_slides, cur = [], []
    in_fence = False
    for ln in lines:
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            cur.append(ln)
            continue
        if HR_RE.match(ln) and not in_fence:
            raw_slides.append(cur)
            cur = []
        else:
            cur.append(ln)
    raw_slides.append(cur)

    slides, notes = [], []
    for raw in raw_slides:
        body = "\n".join(raw)
        m = NOTE_RE.search(body)
        note = m.group(1).strip() if m else ""
        body = NOTE_RE.sub("", body)
        notes.append(note)
        slides.append(render_slide(body))
    # 丢掉全空幻灯片（首尾多余分隔符）
    kept = [(s, n) for s, n in zip(slides, notes) if s.strip() or n]
    if kept:
        slides, notes = zip(*kept)
    else:
        slides, notes = [], []
    return list(slides), list(notes)


def render_slide(body):
    out = []
    i, lines = 0, body.split("\n")
    in_fence = False
    fence_buf = []
    para = []

    def flush_para():
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    def render_list(items, ordered):
        tag = "ol" if ordered else "ul"
        out.append("<%s>%s</%s>" % (
            tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))

    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        if stripped.startswith("```"):
            if not in_fence:
                flush_para()
                in_fence = True
                fence_buf = []
            else:
                in_fence = False
                code = html.escape("\n".join(fence_buf))
                out.append("<pre><code>%s</code></pre>" % code)
            i += 1
            continue
        if in_fence:
            fence_buf.append(ln)
            i += 1
            continue
        if not stripped:
            flush_para()
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            flush_para()
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1
            continue
        if stripped.startswith(">"):
            flush_para()
            quotes = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quotes.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(quotes)))
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if m:
            flush_para()
            items = []
            while i < len(lines):
                mm = re.match(r"^(\d+)\.\s+(.*)$", lines[i].strip())
                if not mm:
                    break
                items.append(mm.group(2))
                i += 1
            render_list(items, True)
            continue
        if re.match(r"^[-*]\s+", stripped):
            flush_para()
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            render_list(items, False)
            continue
        para.append(stripped)
        i += 1
    flush_para()
    return "\n".join(out)


# ---------- HTML 模板 ----------

CSS = """
:root{
  --bg:#1a1d23; --fg:#e8eaed; --accent:#7aa2f7;
  --muted:#9aa0a6; --code-bg:#24272e; --card:#22252c;
}
[data-theme="light"]{
  --bg:#ffffff; --fg:#1f2328; --accent:#0969da;
  --muted:#59636e; --code-bg:#f6f8fa; --card:#f6f8fa;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--bg);color:var(--fg);
  font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
  overflow:hidden}
.deck{height:100%;position:relative}
.slide{display:none;height:100%;padding:8vh 10vw;overflow:auto;
  flex-direction:column;justify-content:center}
.slide.active{display:flex}
.slide h1{font-size:2.6em;margin-bottom:.5em;color:var(--accent)}
.slide h2{font-size:1.9em;margin:.4em 0}
.slide h3{font-size:1.4em;margin:.4em 0}
.slide p{font-size:1.25em;line-height:1.7;margin:.4em 0}
.slide ul,.slide ol{font-size:1.2em;line-height:1.8;margin:.4em 0 .4em 1.2em}
.slide blockquote{border-left:4px solid var(--accent);
  padding:.4em 1em;margin:.6em 0;color:var(--muted);font-size:1.15em}
.slide pre{background:var(--code-bg);border-radius:8px;
  padding:1em;margin:.6em 0;overflow:auto;font-size:.95em}
.slide code{background:var(--code-bg);border-radius:4px;padding:.1em .35em}
.slide pre code{background:none;padding:0}
.slide img{max-width:100%;max-height:55vh;border-radius:8px;margin:.5em 0}
.slide a{color:var(--accent)}
#bar{position:fixed;top:0;left:0;height:4px;background:var(--accent);
  width:0;transition:width .25s;z-index:10}
#count{position:fixed;bottom:14px;right:20px;color:var(--muted);
  font-size:.9em;z-index:10}
#notes{position:fixed;bottom:0;left:0;right:0;background:var(--card);
  color:var(--fg);padding:1em 10vw;display:none;z-index:10;
  border-top:1px solid var(--muted);font-size:1em;line-height:1.6}
#notes.show{display:block}
#notes::before{content:"\\8bb2\\8005\\7a3f\\ff1a ";color:var(--accent);font-weight:bold}
.hint{position:fixed;bottom:14px;left:20px;color:var(--muted);
  font-size:.8em;z-index:10}
@media print{
  body{overflow:visible}
  .slide{display:flex!important;height:auto;min-height:90vh;
    page-break-after:always;border-bottom:1px solid #ccc}
  #bar,#count,.hint,#notes{display:none!important}
}
"""

JS = """
(function(){
var slides=[].slice.call(document.querySelectorAll('.slide'));
var notes=[].slice.call(document.querySelectorAll('#notes .n'));
var cur=parseInt(location.hash.slice(1)||'1',10)-1;
if(cur<0||cur>=slides.length)cur=0;
function show(i){
  cur=(i+slides.length)%slides.length;
  slides.forEach(function(s,k){s.classList.toggle('active',k===cur)});
  document.getElementById('count').textContent=(cur+1)+' / '+slides.length;
  document.getElementById('bar').style.width=((cur+1)/slides.length*100)+'%';
  var box=document.getElementById('notes');
  box.querySelector('.n').textContent=notes[cur]?notes[cur].textContent:'';
  try{history.replaceState(null,'','#'+(cur+1))}catch(e){}
}
function toggleNotes(){
  document.getElementById('notes').classList.toggle('show');
}
document.addEventListener('keydown',function(e){
  if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown')show(cur+1);
  else if(e.key==='ArrowLeft'||e.key==='PageUp')show(cur-1);
  else if(e.key==='Home')show(0);
  else if(e.key==='End')show(slides.length-1);
  else if(e.key==='f'||e.key==='F'){
    if(document.fullscreenElement)document.exitFullscreen();
    else document.documentElement.requestFullscreen();
  }
  else if(e.key==='n'||e.key==='N')toggleNotes();
});
document.addEventListener('click',function(e){
  if(e.target.closest('a'))return;
  show(cur+1);
});
show(cur);
})();
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="{theme}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div id="bar"></div>
<div class="deck">
{slides}
</div>
<div id="notes"><span class="n"></span></div>
<div id="count"></div>
<div class="hint">方向键/空格/点击 翻页 · f 全屏 · n 讲稿</div>
<div style="display:none">{notes_data}</div>
<script>{js}</script>
</body>
</html>
"""


def build(title, slides, notes, theme):
    secs = []
    for i, s in enumerate(slides):
        secs.append('<section class="slide" id="s%d">\n%s\n</section>' % (i + 1, s))
    notes_data = "".join(
        '<span class="n">%s</span>' % html.escape(n) for n in notes)
    return TEMPLATE.format(
        title=html.escape(title), theme=theme, css=CSS, js=JS,
        slides="\n".join(secs), notes_data=notes_data)


# ---------- CLI ----------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="mdslides",
        description="Markdown 转单文件 HTML 幻灯片（零外部请求）")
    ap.add_argument("input", nargs="?", help="输入 Markdown 文件")
    ap.add_argument("-o", "--output", default="deck.html", help="输出 HTML 文件")
    ap.add_argument("--title", default="Slides", help="网页标题")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark",
                    help="主题")
    ap.add_argument("--version", action="version", version="mdslides " + VERSION)
    args = ap.parse_args(argv)

    if not args.input:
        ap.error("需要指定输入的 Markdown 文件")
    if not os.path.isfile(args.input):
        sys.stderr.write("error: 文件不存在：%s\n" % args.input)
        return 1
    with open(args.input, encoding="utf-8") as f:
        md = f.read()
    if not md.strip():
        sys.stderr.write("error: 输入文件为空，没有可生成的幻灯片\n")
        return 1

    slides, notes = md_to_html(md)
    if not slides:
        sys.stderr.write("error: 输入文件为空，没有可生成的幻灯片\n")
        return 1
    out = build(args.title, slides, notes, args.theme)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(out)
    print("已生成：%s（%d 页，主题 %s）" % (args.output, len(slides), args.theme))
    return 0


if __name__ == "__main__":
    sys.exit(main())
