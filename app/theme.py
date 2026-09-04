"""Bauhaus visual theme — palette, typography, CSS, motion, and small geometric
components shared by every page. Purely presentational: nothing here touches
data or analysis logic (that's lib.py and src/p36/). Every page calls
`inject()` once, right after `st.set_page_config`, and `header()` instead of
`st.title` + `st.caption`.

Charting is Altair only (Vega-Lite) — a Streamlit dependency already, not a
separate package. `inject()` registers a global Altair theme, so most charts
need no per-chart styling beyond `theme.style(chart)` for responsive sizing.
Two chart types Vega-Lite's grammar can't express without dropping to raw
Vega — treemap and choropleth map — are deliberately not used anywhere in
this app; see the pages that would have wanted them (Home, Field Analysis,
International Collaboration) for what was used instead (a donut chart, and a
plain bar chart, respectively).

Palette follows the Bauhaus primary triad (red/blue/yellow) plus black and an
unbleached cream ground, echoing the school's own colour theory (Kandinsky's
geometric-colour associations: square/red, circle/blue, triangle/yellow) —
reused below as the shape assigned to each header accent.

Motion follows the same discipline as the palette: short (150-450ms), linear
or ease-out, no bounce/elastic easing — a poster assembling itself, not a
mascot. Every transition below has a reason tied to feedback (this element
just became interactive / this content just finished loading), not
decoration for its own sake.
"""

import altair as alt
import streamlit as st

RED = "#DA291C"
BLUE = "#0F4C81"
YELLOW = "#FFC20E"
BLACK = "#1A1A1A"
CREAM = "#F2EEE6"
WHITE = "#FFFFFF"
GREY = "#8C8C86"

# Discrete series colour order — primary triad first, then black/grey, so a
# chart with up to 5 categories never needs Vega-Lite's default palette.
PALETTE = [BLUE, RED, YELLOW, BLACK, GREY]

# Continuous colour ranges built from the same three colours: single-hue for
# heatmaps/gradients, and a red-cream-blue range for anything centred on zero
# (gap/growth charts) — pair with diverging_scale() for the domain.
SEQUENTIAL_RANGE = [WHITE, BLUE]
DIVERGING_RANGE = [BLUE, CREAM, RED]

FONT_DISPLAY = "'Archivo Black', sans-serif"
FONT_BODY = "'Space Grotesk', sans-serif"


def diverging_scale(min_val: float, max_val: float) -> alt.Scale:
    """A red-cream-blue colour scale centred on zero, domain fit to the
    actual data range — use for any gap/growth encoding via
    `alt.Color(..., scale=theme.diverging_scale(series.min(), series.max()))`."""
    bound = max(abs(min_val), abs(max_val))
    return alt.Scale(domain=[-bound, 0, bound], range=DIVERGING_RANGE)


def _register_altair_theme() -> None:
    def _bauhaus():
        return {
            "config": {
                "background": "rgba(0,0,0,0)",
                "view": {"stroke": "transparent", "continuousWidth": 400, "continuousHeight": 300},
                "title": {"font": FONT_BODY, "fontSize": 15, "fontWeight": "bold", "color": BLACK, "anchor": "start"},
                "axis": {
                    "domainColor": BLACK,
                    "domainWidth": 2,
                    "gridColor": "#E5E1D8",
                    "gridDash": [2, 2],
                    "labelFont": FONT_BODY,
                    "labelColor": BLACK,
                    "labelFontSize": 11,
                    "titleFont": FONT_BODY,
                    "titleColor": BLACK,
                    "titleFontWeight": "bold",
                    "titleFontSize": 12,
                    "tickColor": BLACK,
                },
                "legend": {
                    "labelFont": FONT_BODY,
                    "titleFont": FONT_BODY,
                    "labelColor": BLACK,
                    "titleColor": BLACK,
                    "orient": "bottom",
                },
                "range": {"category": PALETTE, "ordinal": SEQUENTIAL_RANGE},
                "bar": {"stroke": BLACK, "strokeWidth": 1.2},
                "line": {"strokeWidth": 3, "point": True},
                "point": {"filled": True, "stroke": BLACK, "strokeWidth": 1, "size": 90},
                "circle": {"stroke": BLACK, "strokeWidth": 1},
                "area": {"stroke": BLACK, "strokeWidth": 1.5, "opacity": 0.35},
                "boxplot": {"size": 40},
                "arc": {"stroke": BLACK, "strokeWidth": 1.5},
                "rect": {"stroke": WHITE, "strokeWidth": 0.5},
            }
        }

    alt.themes.register("bauhaus", _bauhaus)
    alt.themes.enable("bauhaus")


def style(chart: alt.Chart, height: int = 340) -> alt.Chart:
    """Responsive sizing so a chart fills its Streamlit column — pair with
    `st.altair_chart(chart, use_container_width=True)`. Call last; returns
    the chart so it can be chained."""
    return chart.properties(width="container", height=height)


def inject() -> None:
    """Register the Bauhaus Altair theme and inject the page stylesheet. Call
    once per page, right after st.set_page_config()."""
    _register_altair_theme()
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Grotesk:wght@400;500;700&display=swap');

        html, body, [class*="css"], .stMarkdown, p, li, label {{
            font-family: {FONT_BODY};
        }}

        /* In-page jump targets for question_panel()'s clickable questions
         * (theme.anchor()) — scroll-margin-top keeps the landing spot from
         * hiding under Streamlit's own sticky header. */
        html {{ scroll-behavior: smooth; }}
        .qanchor {{ scroll-margin-top: 90px; }}
        a.qjump {{
            color: {BLACK};
            text-decoration: none;
            border-bottom: 1.5px dashed {GREY};
            cursor: pointer;
            transition: color 0.12s ease-out, border-color 0.12s ease-out;
        }}
        a.qjump:hover {{ color: {BLUE}; border-bottom-color: {BLUE}; }}
        a.qjump:focus-visible {{ outline: 2px solid {BLUE}; outline-offset: 2px; }}
        h1, h2, h3 {{
            font-family: {FONT_DISPLAY} !important;
            text-transform: uppercase;
            letter-spacing: -0.01em;
            color: {BLACK} !important;
        }}

        /* Flat geometry: no rounded corners, no soft shadows, anywhere */
        div[data-testid="stMetric"], div[data-testid="stDataFrame"],
        .stButton>button, .stSelectbox div, .stSlider, div[data-testid="stExpander"],
        img, .stTextInput input {{
            border-radius: 0 !important;
            box-shadow: none !important;
        }}

        /* ---------------------------------------------------------------
         * Motion: page content assembles on every rerun instead of
         * appearing instantly — the "dynamic feedback" a static theme
         * doesn't give you. Staggered by element position via nth-child
         * so a page with several charts visibly builds top-to-bottom.
         * ------------------------------------------------------------- */
        @keyframes bauhausRise {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes bauhausPop {{
            from {{ transform: scale(0); }}
            to   {{ transform: scale(1); }}
        }}
        .main .block-container > div {{
            animation: bauhausRise 0.45s ease-out backwards;
        }}
        .main .block-container > div:nth-child(1) {{ animation-delay: 0.00s; }}
        .main .block-container > div:nth-child(2) {{ animation-delay: 0.04s; }}
        .main .block-container > div:nth-child(3) {{ animation-delay: 0.08s; }}
        .main .block-container > div:nth-child(4) {{ animation-delay: 0.12s; }}
        .main .block-container > div:nth-child(5) {{ animation-delay: 0.16s; }}
        .main .block-container > div:nth-child(n+6) {{ animation-delay: 0.20s; }}

        /* Metric cards as flat colour blocks with a thick left bar that
         * lifts on hover — the one place a shadow is allowed, because it
         * only appears as feedback, never at rest. */
        div[data-testid="stMetric"] {{
            background: {WHITE};
            border: 2px solid {BLACK};
            border-left: 10px solid {RED};
            padding: 12px 16px;
            transition: transform 0.15s ease-out, box-shadow 0.15s ease-out, border-left-color 0.15s ease-out;
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translate(-2px, -2px);
            box-shadow: 4px 4px 0 {BLACK} !important;
            border-left-color: {BLUE};
        }}
        div[data-testid="stMetricLabel"] {{
            font-family: {FONT_BODY};
            text-transform: uppercase;
            font-weight: 700;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}
        div[data-testid="stMetricValue"] {{
            font-family: {FONT_DISPLAY};
            color: {BLACK};
        }}

        /* Sidebar: solid black ground, cream/yellow text — Bauhaus poster block */
        section[data-testid="stSidebar"] {{
            background: {BLACK};
        }}
        section[data-testid="stSidebar"] * {{
            color: {CREAM} !important;
        }}
        section[data-testid="stSidebar"] a {{
            transition: background 0.12s ease-out, color 0.12s ease-out, padding-left 0.12s ease-out;
            border-left: 4px solid transparent;
        }}
        section[data-testid="stSidebar"] a[aria-current="page"] {{
            background: {RED} !important;
            color: {WHITE} !important;
            font-weight: 700;
            border-left: 4px solid {WHITE};
        }}
        section[data-testid="stSidebar"] a:hover {{
            background: {YELLOW} !important;
            color: {BLACK} !important;
            padding-left: 20px;
        }}

        /* Alert boxes recoloured onto the triad instead of default red/orange/blue */
        div[data-testid="stAlertContentError"] {{ color: {WHITE}; }}
        div[data-testid="stAlert"]:has(div[data-testid="stAlertContentError"]) {{
            background: {BLACK}; border: none;
        }}
        div[data-testid="stAlert"]:has(div[data-testid="stAlertContentWarning"]) {{
            background: {YELLOW}; border: none;
        }}
        div[data-testid="stAlert"]:has(div[data-testid="stAlertContentInfo"]) {{
            background: {BLUE}; border: none;
        }}
        div[data-testid="stAlertContentInfo"], div[data-testid="stAlertContentInfo"] * {{
            color: {WHITE} !important;
        }}
        div[data-testid="stAlert"] {{
            animation: bauhausRise 0.3s ease-out;
        }}

        /* Buttons: solid outline at rest, fill on hover, press feedback on click */
        .stButton>button {{
            border: 2px solid {BLACK};
            font-weight: 700;
            text-transform: uppercase;
            background: {WHITE};
            color: {BLACK};
            transition: background 0.12s ease-out, color 0.12s ease-out, transform 0.08s ease-out;
        }}
        .stButton>button:hover {{
            background: {BLACK};
            color: {WHITE};
            border-color: {BLACK};
        }}
        .stButton>button:active {{
            transform: scale(0.97);
        }}

        /* Selectboxes / multiselect: thick square focus ring instead of the
         * browser's default soft blue glow */
        div[data-baseweb="select"] > div {{
            border-radius: 0 !important;
            border: 2px solid {BLACK} !important;
            transition: border-color 0.12s ease-out, box-shadow 0.12s ease-out;
        }}
        div[data-baseweb="select"]:focus-within > div {{
            border-color: {RED} !important;
            box-shadow: 3px 3px 0 {RED} !important;
        }}

        /* Slider: black track, red square thumb (no rounded handles here either) */
        div[data-testid="stSlider"] [role="slider"] {{
            background-color: {RED} !important;
            border: 2px solid {BLACK} !important;
            border-radius: 0 !important;
            transition: transform 0.1s ease-out;
        }}
        div[data-testid="stSlider"] [role="slider"]:hover {{
            transform: scale(1.2);
        }}
        div[data-testid="stSlider"] > div > div > div {{
            background: {BLACK} !important;
        }}

        /* DataFrame: highlight the row under the cursor */
        div[data-testid="stDataFrame"] {{
            border: 2px solid {BLACK};
        }}
        div[data-testid="stDataFrame"] [role="row"]:hover {{
            background-color: {YELLOW}33 !important;
        }}

        /* Expander header: cursor feedback + colour shift, not just default grey */
        div[data-testid="stExpander"] summary {{
            transition: background 0.12s ease-out;
            border: 2px solid {BLACK};
        }}
        div[data-testid="stExpander"] summary:hover {{
            background: {CREAM};
        }}

        /* Streamlit's own "running" status badge, recoloured onto the palette */
        div[data-testid="stStatusWidget"] {{
            border: 2px solid {BLACK} !important;
            background: {YELLOW} !important;
            color: {BLACK} !important;
        }}
        div[data-testid="stStatusWidget"] svg {{
            fill: {BLACK} !important;
        }}

        header[data-testid="stHeader"] {{
            background: {CREAM} !important;
            border-bottom: 3px solid {BLACK};
        }}

        /* Thin geometric scrollbar instead of the OS default */
        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: {CREAM}; }}
        ::-webkit-scrollbar-thumb {{ background: {BLACK}; border: 2px solid {CREAM}; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {RED}; }}

        /* Vega-Lite chart container: a hairline frame that thickens on
         * hover, signalling "this is interactive". Both testids covered —
         * the exact one Streamlit uses has moved between versions. */
        div[data-testid="stVegaLiteChart"], div[data-testid="stArrowVegaLiteChart"] {{
            border: 2px solid transparent;
            transition: border-color 0.15s ease-out;
        }}
        div[data-testid="stVegaLiteChart"]:hover, div[data-testid="stArrowVegaLiteChart"]:hover {{
            border-color: {BLACK};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    _cross_page_scroll_bridge()


def _cross_page_scroll_bridge() -> None:
    """Makes cross-page `question_panel()` links (href like
    "/Field_Analysis#fa-q1-share") actually land on the anchor, not just the
    top of the target page.

    Same-page anchor links (`#fa-q1-share`) work with pure CSS — the browser
    handles the scroll natively, no JS needed. Cross-page links don't: the
    target `<div id="...">` doesn't exist in the DOM yet at the moment the
    browser processes the URL fragment (Streamlit streams the new page's
    elements in over the websocket after the script starts running), so the
    native jump-on-navigate silently does nothing.

    `st.markdown(..., unsafe_allow_html=True)` can't fix this — Streamlit's
    frontend inserts that HTML via a path that does not execute embedded
    `<script>` tags. `st.iframe` given an HTML string renders in a real,
    executable `<iframe>` instead; same-origin, so it can reach back into
    the actual page via `window.parent` to read the URL hash and scroll
    that document (not the iframe itself). Polls for the target element for
    a few seconds (Streamlit's own render can lag behind the navigation),
    and remembers the last hash it handled on `window.parent` (which
    persists across Streamlit reruns, unlike this component, which
    remounts on every one) so an unrelated widget interaction elsewhere on
    the page doesn't yank the view back to the same anchor a second time.
    """
    st.iframe(
        """
        <script>
        (function () {
            try {
                var hash = window.parent.location.hash;
                if (!hash || window.parent.__qjumpLastHash === hash) return;
                var id = decodeURIComponent(hash.slice(1));
                var attemptsLeft = 30;
                (function tryScroll() {
                    var el = window.parent.document.getElementById(id);
                    if (el) {
                        el.scrollIntoView({behavior: "smooth", block: "start"});
                        window.parent.__qjumpLastHash = hash;
                    } else if (attemptsLeft > 0) {
                        attemptsLeft -= 1;
                        setTimeout(tryScroll, 200);
                    }
                })();
            } catch (e) {}
        })();
        </script>
        """,
        height=1,  # st.iframe requires a positive integer — this component has no visible content
    )


_SHAPES = {
    "square": lambda color: (
        f'<div style="width:30px;height:30px;background:{color};'
        f'display:inline-block;margin-right:16px;flex-shrink:0;'
        f'animation:bauhausPop 0.4s ease-out;"></div>'
    ),
    "circle": lambda color: (
        f'<div style="width:30px;height:30px;border-radius:50%;background:{color};'
        f'display:inline-block;margin-right:16px;flex-shrink:0;'
        f'animation:bauhausPop 0.4s ease-out;"></div>'
    ),
    "triangle": lambda color: (
        f'<div style="width:0;height:0;border-left:16px solid transparent;'
        f'border-right:16px solid transparent;border-bottom:28px solid {color};'
        f'display:inline-block;margin-right:16px;flex-shrink:0;'
        f'animation:bauhausPop 0.4s ease-out;"></div>'
    ),
}


def header(title: str, caption: str, shape: str = "square", color: str = RED) -> None:
    """Bauhaus-style page header: a geometric accent that pops in (square=red /
    circle=blue / triangle=yellow, per Kandinsky's Bauhaus colour-shape
    associations), an all-caps display title, a thick black rule, then the
    caption underneath."""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;">
            {_SHAPES[shape](color)}
            <h1 style="margin:0;font-size:2.1rem;">{title}</h1>
        </div>
        <div style="height:8px;background:{BLACK};width:100%;margin:10px 0 6px 0;"></div>
        <p style="font-size:1rem;color:{GREY};margin-bottom:1.2rem;">{caption}</p>
        """,
        unsafe_allow_html=True,
    )


_STATUS_STYLE = {
    # icon, background, foreground — done/partial/elsewhere match the same
    # semantics as the brief itself: fully answered below, answered but only
    # at an aggregate/qualitative level, or answered on a different page
    # rather than duplicated here. "open" is the honest fourth state: a real
    # sub-question from the brief that this platform does not yet answer.
    "done": ("✓", BLUE, WHITE),
    "partial": ("~", YELLOW, BLACK),
    "elsewhere": ("→", GREY, WHITE),
    "open": ("?", CREAM, BLACK),
}


def question_panel(
    items: list[tuple[str, str] | tuple[str, str, str]],
    title: str = "Sub-questions this page answers",
) -> None:
    """A checklist-style panel mapping this page's charts back to the actual
    sub-questions in the project brief (README Analysis item), instead of
    leaving that link implicit. Each item is (question_text, status) or
    (question_text, status, anchor_id); status is one of "done" (a
    chart/table below answers it directly), "partial" (addressed, but only
    in aggregate or qualitatively), "elsewhere" (answered on a different
    page, not duplicated here), or "open" (not yet addressed anywhere in
    this platform — said plainly rather than omitted).

    When `anchor_id` is given, the question becomes a click-to-jump link.
    Two forms:

    - A bare id ("fa-q1-share") — same-page: jumps to `theme.anchor(id)`
      placed immediately above the `st.subheader()` it should land on. Pure
      CSS/native browser scroll, no JS involved.
    - A path starting with "/" ("/Field_Analysis#fa-q1-share") — cross-page:
      navigates to that page and lands on its anchor, for "elsewhere"
      (answered on a different page) items. Needs
      `_cross_page_scroll_bridge()` (called once by `inject()`) on *both*
      pages — the linking page doesn't need it for the link itself to work,
      but every page that might be a cross-page link *target* does, and
      since any page can in principle be linked to, every page calls
      `inject()` regardless.

    Omit `anchor_id` (2-tuple, or `None`) for "open" items with nothing to
    link to anywhere, or "partial" items answered by a synthesis of several
    sections rather than one specific chart — those stay plain text, not a
    dead link.

    Call right after `theme.header()`.
    """
    rows = []
    for item in items:
        question, status, anchor_id = (*item, None)[:3]
        icon, bg, fg = _STATUS_STYLE[status]
        if anchor_id:
            href = anchor_id if anchor_id.startswith("/") else f"#{anchor_id}"
            question_html = f'<a href="{href}" class="qjump">{question}</a>'
        else:
            question_html = question
        rows.append(
            f'<div style="display:flex;gap:12px;align-items:flex-start;padding:7px 0;'
            f'border-bottom:1px solid #E5E1D8;">'
            f'<span style="flex-shrink:0;width:22px;height:22px;background:{bg};color:{fg};'
            f'font-weight:700;font-family:{FONT_DISPLAY};display:flex;align-items:center;'
            f'justify-content:center;font-size:0.78rem;border:1.5px solid {BLACK};">{icon}</span>'
            f'<span style="font-size:0.92rem;line-height:1.45;padding-top:1px;">{question_html}</span>'
            f"</div>"
        )
    st.markdown(
        f"""
        <div style="border:2px solid {BLACK};background:{WHITE};padding:14px 20px 6px 20px;
                    margin-bottom:1.3rem;animation:bauhausRise 0.4s ease-out;">
            <div style="font-family:{FONT_DISPLAY};text-transform:uppercase;font-size:0.85rem;
                        letter-spacing:0.04em;margin-bottom:6px;">{title}</div>
            {''.join(rows)}
            <div style="font-size:0.78rem;color:{GREY};padding:8px 0 4px 0;">
                <b style="color:{BLACK};">✓</b> answered directly below &nbsp;·&nbsp;
                <b style="color:{BLACK};">~</b> answered, aggregate/qualitative only &nbsp;·&nbsp;
                <b style="color:{BLACK};">→</b> answered on another page &nbsp;·&nbsp;
                <b style="color:{BLACK};">?</b> not yet addressed anywhere in this platform
                &nbsp;·&nbsp; underlined = click to jump to it below
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def anchor(anchor_id: str) -> None:
    """An invisible in-page jump target — place immediately above the
    `st.subheader()` (or other section start) that a `question_panel()` link
    should land on. `scroll-margin-top` (set on `.qanchor` in `inject()`'s
    CSS) keeps the landing spot from hiding under Streamlit's sticky header.
    """
    st.markdown(f'<div id="{anchor_id}" class="qanchor"></div>', unsafe_allow_html=True)


def rule(color: str = BLACK, height: int = 3) -> None:
    """A thin geometric divider — use between major sections on a page instead
    of st.divider()'s default hairline."""
    st.markdown(
        f'<div style="height:{height}px;background:{color};margin:18px 0;'
        f'animation:bauhausRise 0.4s ease-out;"></div>',
        unsafe_allow_html=True,
    )
