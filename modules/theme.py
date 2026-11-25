"""Neythal look: two palettes, CSS transitions, animated shoreline header."""
import html
import streamlit as st

PALETTES = {
    "light": dict(bg="#EEF5F6", surface="#FFFFFF", ink="#0A2530", muted="#47636D",
                  line="#C3D8DD", accent="#0B6E7F", pearl="#8A6314",
                  hero_a="#0A3D4A", hero_b="#0E7C8C"),
    "dark": dict(bg="#06141B", surface="#0D2631", ink="#E6F1F3", muted="#9DB8C0",
                 line="#1E4150", accent="#4FD1C5", pearl="#E3C77D",
                 hero_a="#04222B", hero_b="#0B4F58"),
}

FONTS = ("@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700"
         "&family=Instrument+Sans:wght@400;600&family=Noto+Sans+Tamil:wght@500&display=swap');")

CSS = """
.stApp{background:var(--bg)!important;color:var(--ink);font-family:'Instrument Sans',system-ui,sans-serif;
  transition:background-color .6s ease,color .6s ease}
[data-testid=stHeader]{background:transparent!important}
.stApp h1,.stApp h2,.stApp h3,.stApp h4{font-family:'Bricolage Grotesque',system-ui,sans-serif;color:var(--ink);letter-spacing:-.01em}
.stApp p,.stApp li,.stApp label,.stApp .stMarkdown{color:var(--ink)}
[data-testid=stCaptionContainer],[data-testid=stCaptionContainer] *{color:var(--muted)!important}
[data-testid=stSidebar]{background:var(--surface)!important;border-right:1px solid var(--line);transition:background-color .6s ease}
[data-testid=stSidebar] *{color:var(--ink)}
.block-container{padding-top:2rem;max-width:1180px}
/* page change: remount (new container key) replays this */
[class*="st-key-page_"]{animation:tideIn .55s cubic-bezier(.2,.7,.2,1) both}
@keyframes tideIn{from{opacity:0;transform:translateY(16px);filter:blur(3px)}to{opacity:1;transform:none;filter:none}}
/* header */
.hero{position:relative;overflow:hidden;border-radius:18px;padding:2rem 2rem 3.4rem;color:#fff;
  background:linear-gradient(135deg,var(--hero_a),var(--hero_b));margin-bottom:1.4rem;transition:background .6s ease}
.hero h1,.hero p,.hero span{color:#fff!important;margin:0}
.hero h1{font-size:2.6rem;line-height:1.1}
.hero.page h1{font-size:1.9rem}
.hero .ta{font-family:'Noto Sans Tamil',sans-serif;font-size:1.3rem;opacity:.85;margin-left:.6rem}
.hero p{max-width:60ch;margin-top:.5rem;opacity:.92}
.wave{position:absolute;left:0;bottom:0;width:200%;height:46px;animation:drift 16s linear infinite}
.wave.b{height:34px;animation-duration:10s;animation-direction:reverse}
@keyframes drift{to{transform:translateX(-50%)}}
/* tiles */
[class*="st-key-tile_"]{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:1rem;
  transition:transform .25s ease,border-color .25s ease,background-color .6s ease,box-shadow .25s ease}
[class*="st-key-tile_"]:hover{transform:translateY(-4px);border-color:var(--accent);box-shadow:0 10px 24px -14px var(--accent)}
.tile-t{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.1rem}
.tile-d{color:var(--muted)!important;font-size:.92rem;min-height:2.6em}
.stButton>button,.stDownloadButton>button{border-radius:999px;border:1.5px solid var(--accent);background:transparent;
  color:var(--accent);font-weight:600;transition:all .2s ease}
.stButton>button p,.stDownloadButton>button p{color:inherit!important}
.stButton>button:hover,.stDownloadButton>button:hover{background:var(--accent);color:var(--bg)!important;border-color:var(--accent)}
.stButton>button:focus-visible,input:focus-visible{outline:3px solid var(--pearl)!important;outline-offset:2px}
[data-testid=stMetric]{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:.8rem 1rem;
  transition:background-color .6s ease}
[data-testid=stMetric] *{color:var(--ink)!important}
[data-testid=stMetricLabel] *{color:var(--muted)!important}
[data-baseweb=select]>div,[data-baseweb=input]>div,[data-baseweb=base-input],textarea,input{
  background:var(--surface)!important;color:var(--ink)!important;border-color:var(--line)!important}
[data-baseweb=popover] ul,[data-baseweb=popover] li,[role=listbox]{background:var(--surface)!important;color:var(--ink)!important}
[data-testid=stNumberInput] button{background:var(--surface)!important;color:var(--ink)!important}
[data-baseweb=tab-highlight]{background:var(--accent)!important}
[data-baseweb=tab] p{color:var(--ink)}
[data-testid=stAlert]{background:var(--surface)!important;border:1px solid var(--line);border-radius:12px}
[data-testid=stAlert] *{color:var(--ink)!important}
[data-testid=stExpander]{background:var(--surface);border:1px solid var(--line)!important;border-radius:12px}
[data-testid=stExpander] *{color:var(--ink)}
.chip{display:inline-block;padding:.15rem .7rem;border-radius:999px;font-size:.85rem;font-weight:600;
  border:1.5px solid var(--accent);color:var(--accent);margin:0 .4rem .6rem 0}
.chip.demo{border-color:var(--pearl);color:var(--pearl)}
.foot{color:var(--muted);font-size:.85rem;margin-top:2.5rem;border-top:1px solid var(--line);padding-top:.8rem}
[data-testid=stTable] table,[data-testid=stTable] th,[data-testid=stTable] td{color:var(--ink)!important;
  background:var(--surface)!important;border-color:var(--line)!important}
[data-baseweb=select] *,[data-baseweb=radio] *,[data-testid=stWidgetLabel] *,[data-testid=stCheckbox] *,
[data-testid=stToggle] *,[data-testid=stSlider] *,[data-baseweb=tab-list] button *,
[data-testid=stExpander] summary *,[data-testid=stToolbar] *,[data-testid=stHeader] *{color:var(--ink)!important}
[data-baseweb=tag],[data-baseweb=tag] *{background:var(--accent)!important;color:var(--bg)!important}
::placeholder{color:var(--muted)!important;opacity:1}
[data-baseweb=popover] li:hover,[data-baseweb=popover] [role=option]:hover{background:var(--line)!important}
[data-testid=stPlotlyChart]{border:1px solid var(--line);border-radius:14px;overflow:hidden;
  background:var(--surface);transition:background-color .6s ease}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

WAVE = ('<svg class="wave{c}" viewBox="0 0 1200 60" preserveAspectRatio="none" aria-hidden="true">'
        '<path fill="rgba(255,255,255,{a})" d="M0 30 C75 0 225 60 300 30 S525 0 600 30 S825 60 900 30 '
        'S1125 0 1200 30 V60 H0Z"/></svg>')


def inject(mode: str) -> None:
    p = PALETTES[mode]
    variables = ";".join(f"--{k}:{v}" for k, v in p.items())
    st.markdown(f"<style>{FONTS}:root{{{variables}}}{CSS}</style>", unsafe_allow_html=True)


def hero(title: str, text: str, tamil: str = "", page: bool = False) -> None:
    ta = f'<span class="ta">{html.escape(tamil)}</span>' if tamil else ""
    st.markdown(
        f'<div class="hero{" page" if page else ""}"><h1>{html.escape(title)}{ta}</h1>'
        f'<p>{html.escape(text)}</p>{WAVE.format(c="", a=".14")}{WAVE.format(c=" b", a=".10")}</div>',
        unsafe_allow_html=True)


def chip(text: str, demo: bool = False) -> None:
    st.markdown(f'<span class="chip{" demo" if demo else ""}">{html.escape(text)}</span>',
                unsafe_allow_html=True)
