#!/usr/bin/env python3
"""
render.py —— brief.json → 多比例视频封面 PNG（pop-out 技法）。

层次（下→上）：暗化原图(留环境) → 文字 → 全亮抠图人物(与原图同 object-position，原位对齐)。
人物会盖住一点文字，但文字照样可读；这正是“人从场景里跳出来”的设计感来源。

用法:
    python3 src/render.py examples/codex/brief.json output/
"""
import sys, json, base64, html, mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
def template_path(brief):   # 按 brief.template 选模板：popout(默认) / ui
    return ROOT / "assets" / f"template-{brief.get('template', 'popout')}.html"

RATIOS = {
    "16x9": (1280, 720),    # B站 / YouTube
    "4x3":  (1440, 1080),   # 横版紧凑
    "3x4":  (1080, 1440),   # 抖音 / 视频号 竖封面
}
# 每比例的取景焦点（object-position）：原图是竖图，横版要往上取保住头部
FOCUS = {"16x9": "50% 30%", "4x3": "50% 30%", "3x4": "50% 50%"}
SCALE = 2


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _resolve(p: str) -> Path:
    return Path(p) if Path(p).is_absolute() else (ROOT / p)


def cmenu_html(menu) -> str:
    """paper 模板 iOS 右键菜单浮层（嵌进首个高亮里，钉在选区上方）。menu = 字符串列表。"""
    if not menu:
        return ""
    items = "".join(f'<span class="ci">{html.escape(str(x))}</span>' for x in menu)
    return f'<div class="cmenu">{items}</div>'


def title_html(title: str, sel: bool = False, menu_html: str = "") -> str:
    """换行用 \\n（作者断行不被自动回流打散）；关键词高亮用 [方括号]。
    sel=True（paper 模板）时关键词包成 iOS 文本选中（黄底 + 两端手柄）；
    menu_html 注入首个高亮内部，使右键菜单紧贴选区上方。"""
    first_hi = [True]

    def wrap(kw):
        kw = html.escape(kw)
        if not sel:
            return f'<span class="hi">{kw}</span>'
        menu = menu_html if first_hi[0] else ""
        first_hi[0] = False
        return (f'<span class="hi">{menu}<span class="grip s"></span>{kw}'
                f'<span class="grip e"></span></span>')

    lines = []
    for raw in title.split("\n"):
        out, i = [], 0
        while i < len(raw):
            if raw[i] == "[":
                j = raw.find("]", i)
                if j != -1:
                    out.append(wrap(raw[i+1:j]))
                    i = j + 1
                    continue
            out.append(html.escape(raw[i]))
            i += 1
        lines.append(f'<span class="tline">{"".join(out)}</span>')
    return "".join(lines)


def component_html(comp) -> str:
    """可选开发主题钩子组件。详见 references/components.md"""
    if not comp:
        return ""
    t = comp.get("type")
    if t == "terminal":
        rows = "\n".join(html.escape(l) for l in comp.get("lines", []))
        return (f'<div class="hook terminal"><div class="bar">'
                f'<span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>'
                f'&nbsp;{html.escape(comp.get("title","zsh"))}</div><div class="body">{rows}</div></div>')
    if t == "github":
        return (f'<div class="hook github"><div class="bar"><span class="dot g"></span>&nbsp;GITHUB</div>'
                f'<div class="body">{html.escape(comp.get("repo","user/repo"))}\n'
                f'{html.escape(comp.get("desc",""))}\n★ {html.escape(str(comp.get("stars","")))}</div></div>')
    return ""


def kicker_html(t):   return f'<div class="kicker">{html.escape(t)}</div>' if t else ""
def subtitle_html(t): return f'<div class="subtitle">{html.escape(t)}</div>' if t else ""


def ui_kicker_html(t):  # template-ui 顶部小标签
    return f'<div class="cmd-kicker">{html.escape(t)}</div>' if t else ""


def ui_list_html(brief):  # template-ui 结果行：results 列表，缺省用 subtitle 当一行选中
    rows = brief.get("results")
    if not rows:
        sub = brief.get("subtitle")
        rows = [{"label": sub, "icon": "✦", "sel": True}] if sub else []
    out = ""
    for r in rows:
        if isinstance(r, str):
            r = {"label": r}
        cls = "cmd-row sel" if r.get("sel") else "cmd-row"
        ic = f'<span class="ic">{html.escape(r.get("icon","›"))}</span>'
        out += f'<div class="{cls}">{ic}{html.escape(str(r.get("label","")))}</div>'
    return f'<div class="cmd-list">{out}</div>' if out else ""


def build_html(brief: dict):
    tpl = template_path(brief).read_text(encoding="utf-8")

    # 顶层人物（抠图，整幅，{{FOCUS}} 由各比例填）
    person_html = ""
    person = brief.get("person_image")
    if person:
        p = _resolve(person)
        if p.exists():
            person_html = f'<img class="person" src="{data_uri(p)}" style="object-position:{{{{FOCUS}}}}">'
        else:
            print(f"⚠️  人物图不存在: {p}（先跑 src/cutout.py）")

    # 底层原图（压暗，留环境）。无则退化为渐变背景
    photo = brief.get("photo")
    src_wide = ""
    if photo and _resolve(photo).exists():
        bgphoto_html = f'<img class="bg-photo" src="{data_uri(_resolve(photo))}" style="object-position:{{{{FOCUS}}}}">'
        no_photo = ""
        # 横图来源：3:4 改用“上字下图带”，避免裁竖图放大撞脸
        try:
            from PIL import Image
            w0, h0 = Image.open(_resolve(photo)).size
            if w0 / h0 >= 1.2:
                src_wide = " src-wide"
        except Exception:
            pass
    else:
        bgphoto_html = '<div class="bg-grad"></div>'
        no_photo = " no-photo"

    tmpl = brief.get("template", "popout")
    menu_html = cmenu_html(brief.get("menu")) if tmpl == "paper" else ""
    repl = {
        "{{KICKER_HTML}}":   kicker_html(brief.get("kicker", "")),
        "{{TITLE_HTML}}":    title_html(brief.get("title", "未命名标题"),
                                        sel=(tmpl == "paper"), menu_html=menu_html),
        "{{SUBTITLE_HTML}}": subtitle_html(brief.get("subtitle", "")),
        "{{COMPONENT_HTML}}": component_html(brief.get("component")),
        "{{UI_KICKER_HTML}}": ui_kicker_html(brief.get("kicker", "")),
        "{{UI_LIST_HTML}}":  ui_list_html(brief),
        "{{PERSON_HTML}}":   person_html,
        "{{BGPHOTO_HTML}}":  bgphoto_html,
        "{{BRAND_NAME}}":    html.escape(brief.get("brand_name", "@鱼亦乐")),
    }
    side = "person-left" if brief.get("person_side") == "left" else "person-right"
    side += no_photo + src_wide
    if brief.get("person_grade") == "mono":
        side += " grade-mono"
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    return tpl, side


def main():
    if len(sys.argv) < 2:
        print("用法: python3 src/render.py <brief.json> [output_dir]"); sys.exit(1)
    brief = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else (ROOT / "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    base_html, side = build_html(brief)
    name = brief.get("name", "cover")
    focus_override = brief.get("focus")   # str(统一) 或 dict(按比例)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for r in brief.get("ratios", list(RATIOS.keys())):
            if r not in RATIOS:
                print(f"⚠️  跳过未知比例 {r}"); continue
            w, h = RATIOS[r]
            if isinstance(focus_override, str):
                focus = focus_override
            elif isinstance(focus_override, dict):
                focus = focus_override.get(r, FOCUS[r])
            else:
                focus = FOCUS[r]
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=SCALE)
            page.set_content(base_html.replace("{{BODY_CLASS}}", f"{side} ratio-{r}")
                                      .replace("{{FOCUS}}", focus),
                             wait_until="networkidle")
            page.wait_for_timeout(120)
            out = out_dir / f"{name}-{r}.png"
            page.screenshot(path=str(out))
            page.close()
            print(f"✅ {out}  ({w*SCALE}×{h*SCALE})")
        browser.close()


if __name__ == "__main__":
    main()
