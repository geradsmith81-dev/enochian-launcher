"""Aurora theme (text contrast >= 4.5:1 checked over the brightest aurora behind the panels)
 for the app: palette sampled from the user's photograph IMG_0263.CR2
(aurora over snow-covered mountains and spruce at night) and the page CSS.

Palette roles (hex sampled from the photo unless noted):
  night      #1c1b21  page base (darkened night sky)
  panel      #26252c  panels and cards (darkened night sky)
  sky        #3b3a3e  night sky, upper left of the photo
  spruce     #1b1612  treeline
  aurora     #bde188  aurora, brightest 10 % of pixels   -> primary accent
  glow       #e7fd9b  aurora, brightest 1 %              -> headings
  aurora_mid #a0b180  body of the aurora
  aurora_muted #879574 aurora edges                   -> borders, rules
  snow       #c7b9ba  snow on the peaks (95th percentile)
  snow_text  #ece3e6  snow, lifted for body text (derived)
  mist       #cfc8bd  moonlit snow in shadow (#aca69a), lifted for 4.5:1 contrast -> secondary text
  alpenglow  #e0b4c6  pink cast of the snow, saturated (derived) -> off-zodiac flag
"""
import base64, os

PALETTE = {'night': '#1c1b21', 'panel': '#26252c', 'sky': '#3b3a3e', 'spruce': '#1b1612', 'aurora': '#bde188', 'glow': '#e7fd9b', 'aurora_mid': '#a0b180', 'aurora_muted': '#879574', 'snow': '#c7b9ba', 'mist': '#cfc8bd', 'lavender': '#c9b3e0', 'snow_text': '#ece3e6', 'alpenglow': '#e0b4c6'}

WHEEL_THEME = dict(
    fig_bg='none', face=PALETTE['night'], face_alpha=0.82, band_a=PALETTE['sky'], band_b='#4a4850', band_edge=PALETTE['night'],
    band_text=PALETTE['snow_text'], ring=PALETTE['aurora_muted'], ink=PALETTE['snow_text'], grey=PALETTE['mist'],
    up=PALETTE['aurora'], down_face=PALETTE['night'], accent=PALETTE['alpenglow'], label_bg=PALETTE['night'])


def css(bg_path='assets/background.jpg'):
    p = PALETTE
    bg = ''
    if os.path.exists(bg_path):
        b64 = base64.b64encode(open(bg_path, 'rb').read()).decode()
        bg = (f"background-image: linear-gradient(180deg, rgba(20,19,25,0.25) 0%, rgba(20,19,25,0.55) 55%, "
              f"rgba(20,19,25,0.90) 100%), url('data:image/jpeg;base64,{b64}');"
              "background-size: cover; background-position: center top; background-attachment: fixed;")
    return f"""<style>
    .stApp {{ {bg} }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] > div:first-child {{ background: rgba(28,27,33,0.80); backdrop-filter: blur(6px);
        border-right: 1px solid {p['aurora_muted']}55; }}
    .block-container {{ background: rgba(28,27,33,0.50); border-radius: 16px; padding: 2rem 2.2rem calc(7rem + env(safe-area-inset-bottom, 0px));
        margin-top: 1.2rem; backdrop-filter: blur(5px); border: 1px solid {p['aurora_muted']}40; }}
    /* tablets and phones (user request, Nov 2026): more room at the bottom, so the last lines are not hidden behind
       the browser toolbar, the iPad home bar or Streamlit's 'Manage app' badge */
    @media (pointer: coarse), (max-width: 1100px) {{
        .block-container {{ padding-bottom: calc(10rem + env(safe-area-inset-bottom, 0px)) !important; }} }}
    h1, h2, h3 {{ font-family: Georgia, 'Palatino Linotype', 'Book Antiqua', serif !important;
        color: {p['glow']} !important; letter-spacing: 0.01em; }}
    h1 {{ text-shadow: 0 0 18px {p['aurora']}55; }}
    [data-testid="stMetricValue"] {{ color: {p['aurora']}; font-family: Georgia, serif; }}
    [data-testid="stCaptionContainer"], .stCaption {{ color: {p['mist']} !important; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{ border-color: {p['aurora_muted']} !important;
        background: rgba(38,37,44,0.55); }}
    code {{ color: {p['glow']}; background: rgba(189,225,136,0.10); }}
    a {{ color: {p['aurora']}; }}
    </style>""" + force_css()


# Streamlit's own widgets, text and menus (user request, Nov 2026: Light mode must look the same as Dark mode).
# These rules set the colours directly, so the app reads the same, light text on the dark aurora, whether the
# browser, the tablet or Streamlit's menu is in light or dark mode, and even if .streamlit/config.toml is missing
# (GitHub's web upload can drop the hidden .streamlit folder). Adapted from Sky Gahshomar's FORCE_CSS.
# Contrast of every pair is at least 8:1 (text on panel 12.1:1, mist 9.1:1, aurora 10.3:1, night on aurora 11.6:1).
def force_css():
    p = PALETTE
    T, M, G, A, N, C, H, B = (p['snow_text'], p['mist'], p['glow'], p['aurora'], p['night'], p['panel'], p['sky'],
                              p['aurora_muted'])
    return f"""<style>
    :root {{ color-scheme: dark; }}
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stBottom"] > div {{ color: {T}; }}
    .stApp {{ background-color: {N}; }}
    [data-testid="stHeader"] button, [data-testid="stHeader"] a, [data-testid="stToolbar"] *,
    [data-testid="stSidebarCollapseButton"] *, [data-testid="stExpandSidebarButton"] *,
    [data-testid="stSidebarCollapsedControl"] * {{ color: {T} !important; fill: currentColor; }}
    [data-testid="stSidebar"] {{ background-color: {C} !important; color: {T}; }}
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] strong, [data-testid="stText"], [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p, label, legend, [data-testid="stRadio"] label, [data-testid="stRadio"] p,
    [data-testid="stCheckbox"] p, [data-testid="stToggle"] p, [data-testid="stMetricLabel"] p {{ color: {T} !important; }}
    [data-testid="stMetricValue"] {{ color: {A} !important; }}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p, .stCaption, small,
    [data-testid="stWidgetLabel"] [data-testid="stTooltipIcon"] {{ color: {M} !important; }}
    [data-testid="stMarkdownContainer"] a, [data-testid="stCaptionContainer"] a {{ color: {A} !important; }}
    [data-testid="stMarkdownContainer"] code {{ background: rgba(189,225,136,0.10); color: {G}; }}
    h1, h2, h3, h4, h5, h6, [data-testid="stHeading"] * {{ color: {G} !important; }}
    /* text boxes, number boxes, select boxes and their menus */
    [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"], [data-baseweb="select"] > div,
    [data-testid="stNumberInputContainer"], [data-testid="stDateInput"] [data-baseweb="input"],
    [data-testid="stTimeInput"] [data-baseweb="select"] > div {{
      background-color: {C} !important; border-color: {B} !important; color: {T} !important; }}
    [data-baseweb="input"] input, [data-baseweb="base-input"] input, textarea, [data-baseweb="select"] input,
    [data-baseweb="select"] div, [data-baseweb="select"] span {{ color: {T} !important; -webkit-text-fill-color: {T};
      background-color: transparent; }}
    input::placeholder, textarea::placeholder {{ color: {M} !important; -webkit-text-fill-color: {M}; opacity: 1; }}
    [data-baseweb="select"] svg, [data-testid="stNumberInputContainer"] svg {{ color: {T} !important; fill: currentColor; }}
    [data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] {{ background: {C} !important;
      color: {T} !important; }}
    [data-baseweb="popover"] > div, [data-baseweb="popover"] ul, [data-baseweb="menu"], [role="listbox"] {{
      background-color: {C} !important; color: {T} !important; border-color: {B} !important; }}
    [data-baseweb="popover"] li, [role="option"] {{ color: {T} !important; background-color: {C}; }}
    [data-baseweb="popover"] li:hover, [role="option"]:hover, [role="option"][aria-selected="true"] {{
      background-color: {H} !important; }}
    [data-baseweb="tag"] {{ background-color: {H} !important; color: {T} !important; }}
    [data-baseweb="tag"] * {{ color: {T} !important; }}
    [data-baseweb="calendar"], [data-baseweb="calendar"] * {{ background-color: {C}; color: {T}; }}
    [data-baseweb="tooltip"], [data-baseweb="tooltip"] * {{ background-color: {C} !important; color: {T} !important; }}
    /* buttons */
    [data-testid^="stBaseButton-secondary"], [data-testid="stDownloadButton"] button, .stButton > button {{
      background-color: {C} !important; color: {T} !important; border: 1px solid {B} !important; }}
    [data-testid^="stBaseButton-secondary"]:hover, [data-testid="stDownloadButton"] button:hover,
    .stButton > button:hover {{ background-color: {H} !important; border-color: {A} !important; }}
    [data-testid^="stBaseButton-primary"] {{ background-color: {A} !important; color: {N} !important;
      border: 1px solid {G} !important; }}
    [data-testid^="stBaseButton-primary"]:hover {{ background-color: {G} !important; }}
    [data-testid^="stBaseButton"] p {{ color: inherit !important; }}
    /* radio dots, check boxes and toggles stay visible on the dark ground */
    [data-testid="stRadio"] [role="radio"] > div:first-child, [data-baseweb="radio"] > div:first-child {{
      border-color: {A} !important; }}
    [data-baseweb="checkbox"] [role="checkbox"], [data-baseweb="checkbox"] > div:first-child {{ border-color: {A} !important; }}
    /* expanders, tabs, alerts, dialogs, tables */
    [data-testid="stExpander"] details, [data-testid="stExpander"] > details {{ background-color: {C} !important;
      border-color: {B} !important; color: {T} !important; }}
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {{ color: {G} !important;
      background-color: transparent; }}
    [data-testid="stExpander"] summary:hover {{ background-color: {H} !important; }}
    [data-baseweb="tab"], [data-baseweb="tab"] p {{ color: {T} !important; }}
    [data-baseweb="tab"][aria-selected="true"], [data-baseweb="tab"][aria-selected="true"] p {{ color: {G} !important; }}
    [data-testid="stAlertContainer"], [data-testid="stAlert"] > div {{ background-color: {C} !important;
      color: {T} !important; border: 1px solid {B}; }}
    [data-testid="stAlertContainer"] *, [data-testid="stAlert"] * {{ color: {T} !important; }}
    div[role="dialog"], [data-testid="stDialog"] div[role="dialog"] {{ background-color: {N} !important;
      color: {T} !important; border: 1px solid {B}; }}
    div[role="dialog"] button[aria-label="Close"] {{ color: {T} !important; }}
    [data-testid="stTable"] table, [data-testid="stTable"] th, [data-testid="stTable"] td {{ color: {T} !important;
      background-color: {C} !important; border-color: {B} !important; }}
    [data-testid="stTable"] th {{ color: {G} !important; }}
    [data-testid="stSpinner"], [data-testid="stSpinner"] * {{ color: {T} !important; }}
    [data-testid="stToast"] {{ background-color: {C} !important; color: {T} !important; }}
    hr {{ border-color: {B} !important; }}
    </style>"""
