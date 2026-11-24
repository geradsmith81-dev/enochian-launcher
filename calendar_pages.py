"""The ritual-calendar pages of the Sidereal Enochian Chart (modelled on Sky Gahshomar):
Today, Month, Year, Watches, Workings, Occasions, How it works, About.

ctx (built in app.py): lat, lon, elev, tzname (IANA name or None), off (UTC offset in hours, used when tzname is
None), tz (tzinfo), place (label), conv ('sunrise' | 'midnight'), moment (aware local datetime of the chosen
moment), mode.
"""
from __future__ import annotations

import calendar
import datetime as dt
import io
from html import escape as esc

import pandas as pd
import streamlit as st
from skyfield import almanac

import enochian_layer as el
import enochian_script
import ritual_calendar as rc
import theme
import workings as W

P = theme.PALETTE
WEEK = [6, 0, 1, 2, 3, 4, 5]                        # Sunday first (python weekday numbers)
SHORT = {k: v.split(' (')[0] for k, v in zip(el.BY_DAY.index, el.BY_DAY['king'])}
KIND_LABELS = {'sun': 'Sun entries', 'planet': 'Planet entries', 'moon_in': "Moon's constellation entries",
               'phase': 'Moon phases', 'eclipse': 'Eclipses'}


def css() -> str:
    a, g, m, n, pn, mu, al = P['aurora'], P['glow'], P['mist'], P['night'], P['panel'], P['aurora_muted'], P['alpenglow']
    return f"""<style>
    .rc-card {{ background: rgba(38,37,44,0.62); border: 1px solid {mu}80; border-radius: 12px; padding: .8rem 1rem;
        margin: 0 0 .8rem; }}
    .rc-card h4 {{ margin: 0 0 .45rem; color: {g}; font-family: Georgia, serif; font-size: 1.08rem; }}
    .rc-big {{ font-family: Georgia, serif; font-size: 1.55rem; color: {a}; line-height: 1.25; }}
    .rc-muted {{ color: {m}; font-size: .9rem; }}
    .rc-note {{ border-left: 3px solid {al}; padding: .3rem .6rem; margin: .45rem 0; color: {P['snow_text']};
        background: rgba(224,180,198,0.08); font-size: .92rem; }}
    .rc-src {{ color: {m}; font-size: .8rem; margin-top: .15rem; }}
    .rc-read {{ margin-top: .3rem; font-size: .9rem; }}
    a.rc-link {{ color: {a}; text-decoration: none; border-bottom: 1px dotted {a}; }}
    .rc-tag {{ font-size: .72rem; padding: .05rem .4rem; border-radius: 8px; margin-left: .3rem; white-space: nowrap;
        border: 1px solid {mu}; color: {m}; }}
    .rc-tag-sourced {{ border-color: {a}; color: {a}; }} .rc-tag-app {{ border-color: {al}; color: {al}; }}
    .rc-work {{ border-top: 1px solid {mu}55; padding: .55rem 0 .5rem; }}
    .rc-work-t {{ font-weight: 700; color: {P['snow_text']}; }}
    .rc-watches {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: .35rem; margin: .4rem 0; }}
    .rc-watch {{ border: 1px solid {mu}70; border-radius: 9px; padding: .35rem .45rem; font-size: .82rem; }}
    .rc-watch b {{ color: {g}; }} .rc-watch.rc-now {{ border: 2px solid {a}; background: rgba(189,225,136,0.12); }}
    .rc-scroll {{ overflow-x: auto; }}
    table.rc-grid {{ border-collapse: separate; border-spacing: 4px; width: 100%; table-layout: fixed; min-width: 700px; }}
    table.rc-grid th {{ color: {g}; font-weight: 600; font-size: .85rem; text-align: left; padding: 0 .3rem; }}
    table.rc-grid td {{ vertical-align: top; background: rgba(38,37,44,0.66); border: 1px solid {mu}55; border-radius: 8px;
        padding: .3rem .35rem; height: 6.4rem; font-size: .78rem; overflow: hidden; }}
    table.rc-grid td.rc-empty {{ background: transparent; border: none; }}
    table.rc-grid td.rc-today {{ border: 2px solid {a}; }} table.rc-grid td.rc-sel {{ box-shadow: 0 0 0 2px {al} inset; }}
    .rc-dn {{ font-size: 1.05rem; font-weight: 700; color: {P['snow_text']}; }}
    .rc-king {{ color: {a}; font-family: Georgia, serif; }} .rc-prince {{ color: {m}; font-size: .72rem; }}
    .rc-chip {{ display: block; margin-top: .12rem; line-height: 1.15; color: {P['snow_text']}; }}
    .rc-chip.rc-k-eclipse {{ color: {al}; font-weight: 700; }} .rc-chip.rc-k-sun {{ color: {g}; font-weight: 600; }}
    .rc-chip.rc-k-moon_in {{ color: {m}; font-size: .7rem; }}
    table.rc-times {{ border-collapse: collapse; width: 100%; font-size: .86rem; }}
    table.rc-times th, table.rc-times td {{ text-align: left; padding: .28rem .45rem; border-bottom: 1px solid {mu}55;
        white-space: nowrap; }}
    table.rc-times th {{ color: {g}; }} table.rc-times tr.rc-today-row td {{ background: rgba(189,225,136,0.12); }}
    .rc-mini {{ font-size: .84rem; }} .rc-mini div {{ margin: .1rem 0; }}
    </style>"""


# ------------------------------------------------------------------------------------------------ helpers
def card(title: str, body: str) -> str:
    return f"<div class='rc-card'><h4>{title}</h4>{body}</div>"


def hm(d: dt.datetime) -> str:
    return d.strftime('%H:%M')


def dhm(d: dt.datetime) -> str:
    return d.strftime('%a %d %b %H:%M')


@st.cache_data(show_spinner=False, max_entries=12)
def occ_year(year: int) -> list[dict]:
    return rc.occasions(year)


def occ_between(start: dt.datetime, end: dt.datetime) -> list[dict]:
    """Occasions with start <= time < end (aware datetimes)."""
    s_u, e_u = start.astimezone(dt.timezone.utc), end.astimezone(dt.timezone.utc)
    seen, out = set(), []
    for y in range(max(s_u.year, 1850), min(e_u.year, 2149) + 1):
        for e in occ_year(y):
            key = (e['kind'], e.get('body'), e.get('phase'), round(e['tt'], 4))
            if key in seen or not (s_u <= e['utc'] < e_u):
                continue
            seen.add(key)
            out.append(e)
    return sorted(out, key=lambda e: e['tt'])


def kind_of(e: dict) -> str:
    if e['kind'] == 'ingress':
        return 'sun' if e['body'] == 'Sun' else ('moon_in' if e['body'] == 'Moon' else 'planet')
    return e['kind']


@st.cache_data(show_spinner=False, max_entries=64)
def hdays(d0: dt.date, d1: dt.date, lat, lon, elev, tzname, off, conv):
    return rc.heptarchic_days(d0, d1, lat, lon, elev, rc.tzinfo(tzname, off), conv)


def hdays_ctx(ctx, d0, d1):
    return hdays(d0, d1, ctx['lat'], ctx['lon'], ctx['elev'], ctx['tzname'], ctx['off'], ctx['conv'])


def hday_at(ctx, moment: dt.datetime):
    d = moment.date()
    for h in hdays_ctx(ctx, d - dt.timedelta(days=1), d + dt.timedelta(days=1)):
        if h.start <= moment < h.end:
            return h
    return hdays_ctx(ctx, d, d)[0]


def chip(e: dict, tz, with_date=False) -> str:
    k = kind_of(e)
    t = e['utc'].astimezone(tz)
    when = dhm(t) if with_date else hm(t)
    if e['kind'] == 'ingress':
        txt = f"{rc.GLYPH[e['body']]}→{e['to_abbr']}"
        if e['zodiac_king'] and e['body'] != 'Moon':
            txt += f" {e['zodiac_king']}"
    elif e['kind'] == 'phase':
        txt = f"{rc.PHASE_GLYPH[e['phase']]} {e['name']}"
    else:
        txt = rc.title(e)
    return f"<span class='rc-chip rc-k-{k}' title='{esc(rc.title(e))}: {esc(rc.detail(e))}'>{esc(txt)} {when}</span>"


def range_ok(d: dt.date) -> bool:
    return rc.FIRST <= d <= rc.LAST


def tz_label(ctx) -> str:
    return ctx['tzname'] or f"UTC{ctx['off']:+.2f}"


def ministers_html(weekday: str, n: int) -> str:
    m = el.ministers_for(weekday, n)['part']
    if not m or not m['names_dee_letters']:
        return "<span class='rc-muted'>-</span>"
    return f"<code>{esc(m['names_dee_letters'])}</code><br><span class='rc-muted'>{esc(m['names_james_rotation'] or '')}</span>"


def table(df: pd.DataFrame):
    enochian_script.table(df)


# ------------------------------------------------------------------------------------------------ Today
def render_today(ctx):
    m, tz = ctx['moment'], ctx['tz']
    if not range_ok(m.date()):
        st.html(card('Today', '<p>This date is outside 1850–2149, the range of the JPL DE440s ephemeris.</p>'))
        return
    h = hday_at(ctx, m)
    g = el.BY_DAY.loc[h.weekday]
    before = ''
    if h.civil != m.date():
        before = (f"<div class='rc-note'>Before sunrise: the Heptarchic day that began at sunrise on "
                  f"{h.start:%a %d %b} is still running.</div>")
    fb = (f"<div class='rc-note'>{esc(h.convention)}</div>" if h.fallback else '')
    body = (f"<div class='rc-big'>King {esc(h.king)} · Prince {esc(h.prince)}</div>"
            f"<div>{esc(h.weekday)} · {esc(h.realm)}</div>"
            f"<div class='rc-muted'>{'From sunrise' if h.convention.startswith('sunrise') else 'From midnight (LMT)'} "
            f"{dhm(h.start)} to {dhm(h.end)} · {esc(ctx['place'])} · {esc(tz_label(ctx))}</div>{before}{fb}"
            f"<div class='rc-src'>{esc(g['day_basis'][:220])}… ({esc(g['cites'])})</div>"
            + W.read_line(W.WORKINGS['king_day']['links'] + ['hm5'], 'Read the working'))
    st.html(card(f"The Heptarchic day · {m:%A %d %B %Y}, {m:%H:%M}", body))

    # --- the six watches
    now_n = h.watch_at(m)
    cells = []
    for n, a, b in h.watches:
        cls = 'rc-watch rc-now' if n == now_n else 'rc-watch'
        cells.append(f"<div class='{cls}'><b>Part {n}</b> {hm(a)}–{hm(b)}<br>{ministers_html(h.weekday, n)}</div>")
    wb = ''
    if now_n:
        wb += f"<div><b>Now:</b> part {now_n} of 6 of {esc(h.weekday)}'s day.</div>"
    wb += "<div class='rc-watches'>" + ''.join(cells) + "</div>"
    whole = el.ministers_for(h.weekday, 1)['whole_day']
    if whole and whole['names_dee_letters']:
        wb += (f"<div class='rc-note'>Whole-day six of this day (Peterson): <code>{esc(whole['names_dee_letters'])}</code>"
               f"</div>" + W.read_line(W.WORKINGS['whole_day_six']['links']))
    wb += ("<div class='rc-muted'>The six parts are equal sixths of this sunrise-to-sunrise day, so their length "
           "changes with the season. Upper line: Dee's letters (one angel per letter); lower line: James's names.</div>"
           + W.read_line(W.WORKINGS['watch_ministers']['links']))
    st.html(card('The six watches · ministers of each part', wb))

    # --- occasions in this Heptarchic day and coming
    here = occ_between(h.start, h.end)
    if here:
        fb2 = ''.join(f"<div>{chip(e, tz, True)} <span class='rc-muted'>{esc(rc.detail(e))}</span></div>" for e in here)
    else:
        fb2 = "<div class='rc-muted'>No ingress, phase or eclipse during this Heptarchic day.</div>"
    nxt = [e for e in occ_between(m, min(m + dt.timedelta(days=45), dt.datetime(2149, 12, 30, tzinfo=dt.timezone.utc)))
           if kind_of(e) != 'moon_in' and e['utc'] > h.end.astimezone(dt.timezone.utc)][:6]
    if nxt:
        fb2 += "<div style='margin-top:.45rem'><b>Coming:</b></div>" + ''.join(
            f"<div>{chip(e, tz, True)}</div>" for e in nxt)
    st.html(card('Occasions (JPL DE440s times, your clock)', fb2))

    # --- Sun and Moon now
    t = rc.ts.from_datetime(m)
    sun_c = rc.se._const_name[str(rc._const('sun', t.tt))]
    moon_c = rc.se._const_name[str(rc._const('moon', t.tt))]
    illum = float(almanac.fraction_illuminated(rc.eph, 'moon', t))
    waxing = float(almanac.moon_phase(rc.eph, t).degrees) < 180
    zk = el.ZK.loc[sun_c]['zodiac_king'] if sun_c in el.ZK.index else None
    sun_next = [e for e in occ_between(m, m + dt.timedelta(days=50)) if kind_of(e) == 'sun'][:1]
    sb = (f"<div>☉ The Sun is in <b>{esc(sun_c)}</b>: "
          + (f"zodiac King <b>{esc(zk)}</b>." if zk else "no zodiac King (Ophiuchus or another non-zodiacal "
             "constellation).") + "</div>")
    if sun_next:
        e = sun_next[0]
        sb += f"<div class='rc-muted'>Enters {esc(e['to_name'])} {dhm(e['utc'].astimezone(tz))}.</div>"
    sb += (f"<div style='margin-top:.3rem'>☽ The Moon is in <b>{esc(moon_c)}</b>, {illum * 100:.0f}% lit, "
           f"{'waxing' if waxing else 'waning'}.</div>")
    ph = [e for e in occ_between(m, m + dt.timedelta(days=32)) if e['kind'] == 'phase'][:4]
    sb += "<div class='rc-muted'>" + ' · '.join(
        f"{rc.PHASE_GLYPH[e['phase']]} {esc(e['name'])} {dhm(e['utc'].astimezone(tz))}" for e in ph) + "</div>"
    sb += ("<div class='rc-src'>Constellations are geocentric here; the Chart page is topocentric (the Moon can "
           "differ near a boundary).</div>")
    st.html(card('Sun and Moon', sb))


# ------------------------------------------------------------------------------------------------ Month
def _shift_month(k: int):
    y, mo = st.session_state['rc_month']
    mo += k
    y, mo = y + (mo - 1) // 12, (mo - 1) % 12 + 1
    st.session_state['rc_month'] = (min(max(y, 1850), 2149), mo)


def _this_month(d: dt.date):
    st.session_state['rc_month'] = (d.year, d.month)


def render_month(ctx):
    m, tz = ctx['moment'], ctx['tz']
    if 'rc_month' not in st.session_state:
        st.session_state['rc_month'] = (m.year, m.month)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.6])
    c1.button('◀ Previous', key='rc_prev', width='stretch', on_click=_shift_month, args=(-1,))
    c2.button('This month', key='rc_this', width='stretch', on_click=_this_month, args=(m.date(),))
    c3.button('Next ▶', key='rc_next', width='stretch', on_click=_shift_month, args=(1,))
    show_moon = c4.toggle("Show the Moon's constellation entries", value=True, key='rc_moon_in')
    y, mo = st.session_state['rc_month']
    first = dt.date(y, mo, 1)
    n = calendar.monthrange(y, mo)[1]
    last = dt.date(y, mo, n)
    first_c, last_c = max(first, rc.FIRST), min(last, rc.LAST)
    days = hdays_ctx(ctx, first_c, last_c)
    by = {h.civil: h for h in days}
    evs = occ_between(dt.datetime(y, mo, 1, tzinfo=tz) - dt.timedelta(hours=1),
                      dt.datetime(last.year, last.month, last.day, 23, 59, tzinfo=tz) + dt.timedelta(hours=1))
    evday: dict = {}
    for e in evs:
        if kind_of(e) == 'moon_in' and not show_moon:
            continue
        evday.setdefault(e['utc'].astimezone(tz).date(), []).append(e)
    st.html(f"<div class='rc-big'>{calendar.month_name[mo]} {y}</div>"
            f"<div class='rc-muted'>{esc(ctx['place'])} · times in {esc(tz_label(ctx))} · "
            f"Heptarchic day from {'local sunrise' if ctx['conv'] == 'sunrise' else 'LMT midnight'}</div>")
    lead = WEEK.index(first.weekday())
    cells = ["<td class='rc-empty'></td>"] * lead
    for k in range(n):
        d = first + dt.timedelta(days=k)
        h = by.get(d)
        cls = ['rc-cell'] + (['rc-today'] if d == dt.date.today() else []) + (['rc-sel'] if d == m.date() else [])
        king = (f"<div class='rc-king'>{esc(SHORT[h.weekday])}</div><div class='rc-prince'>{esc(h.prince.split(' (')[0])}"
                f" · ☉↑ {hm(h.start)}</div>") if h else ''
        chips = ''.join(chip(e, tz) for e in evday.get(d, []))
        cells.append(f"<td class='{' '.join(cls)}'><div class='rc-dn'>{d.day}</div>{king}{chips}</td>")
    while len(cells) % 7:
        cells.append("<td class='rc-empty'></td>")
    head = ''.join(f"<th>{calendar.day_abbr[w]} · {esc(SHORT[el.WEEKDAYS[w]])}</th>" for w in WEEK)
    rows = ''.join('<tr>' + ''.join(cells[i:i + 7]) + '</tr>' for i in range(0, len(cells), 7))
    st.html(f"<div class='rc-scroll'><table class='rc-grid'><tr>{head}</tr>{rows}</table></div>")
    st.html("<div class='rc-muted'>Each cell is a civil day. It shows the King and Prince of the Heptarchic day whose "
            "sunrise falls on that date (☉↑ = sunrise, when the day and its first watch begin), and every occasion "
            "with its local clock time: ☉☽☿♀♂♃♄→ an entry into an IAU constellation (with its zodiac King), "
            "🌑🌓🌕🌗 Moon phases, 🌒🌘 eclipses. Hover over an occasion for details.</div>")


# ------------------------------------------------------------------------------------------------ Year
def render_year(ctx):
    tz = ctx['tz']
    y = int(st.number_input('Year', 1850, 2149, ctx['moment'].year, 1, key='rc_year'))
    evs = occ_between(dt.datetime(y, 1, 1, tzinfo=tz), dt.datetime(y + 1, 1, 1, tzinfo=tz) if y < 2149
                      else dt.datetime(2149, 12, 30, tzinfo=tz))
    allsun = [e for e in occ_between(dt.datetime(y, 1, 1, tzinfo=tz) - dt.timedelta(days=50),
                                     dt.datetime(y, 12, 31, tzinfo=tz) + dt.timedelta(days=50)) if kind_of(e) == 'sun']
    rows = []
    for i, e in enumerate(allsun):
        loc = e['utc'].astimezone(tz)
        if loc.year != y:
            continue
        nxt = allsun[i + 1]['utc'] if i + 1 < len(allsun) else None
        rows.append({'Sun enters': e['to_name'], 'Local date and time': f"{loc:%a %d %b %Y %H:%M:%S}",
                     'UTC': f"{e['utc']:%Y-%m-%d %H:%M:%S}",
                     'Days there': '' if nxt is None else f"{(nxt - e['utc']).total_seconds() / 86400:.1f}",
                     'Zodiac King': e['zodiac_king'] or '— (none)', 'Sign': e['zodiac_sign'] or '',
                     'Tribe': e['tribe'] or '', 'Face': e['quarter'] or ''})
    st.subheader(f"The Sun's sidereal year {y}: entries into the IAU constellations")
    table(pd.DataFrame(rows))
    st.caption("The Sun crosses 13 constellations of unequal size (Ophiuchus included), so the 'months' of the zodiac "
               "Kings run from about 7 to 45 days. Times: NASA JPL DE440s, geocentric, IAU boundaries in their own "
               "B1875 frame. Checked against JPL Horizons' constellation for 2026: the Sun's entries agree to within about "
               "30 seconds; Mercury, Venus and Mars to within 35 seconds; slow Saturn to about 5 minutes (under 1 "
               "arcsecond of its motion).")
    ecl = [e for e in evs if e['kind'] == 'eclipse']
    st.subheader('Eclipses')
    if ecl:
        er = []
        for e in ecl:
            lv = rc.eclipse_local(e, ctx['lat'], ctx['lon'], ctx['elev'])
            seen = ('yes' + (f", greatest {dhm(rc.ts.tt_jd(lv['tt']).utc_datetime().astimezone(tz))}" if e['body'] == 'Sun'
                             else '') + (f", magnitude {lv['magnitude']:.2f}" if 'magnitude' in lv else '')) if lv['visible'] else 'no'
            er.append({'Eclipse': e['ecl_type'], 'Greatest (local)': dhm(e['utc'].astimezone(tz)),
                       'UTC': f"{e['utc']:%Y-%m-%d %H:%M}", f"Seen from {ctx['place']}": seen,
                       'Detail': rc.detail(e)})
        table(pd.DataFrame(er))
        st.caption("Solar eclipses: 'greatest' is for the whole Earth; the local column gives the best moment at "
                   "your place if the Sun is up and the discs overlap there. Lunar eclipses: seen if the Moon is "
                   "above your horizon at greatest eclipse.")
    else:
        st.caption('No eclipse this year.')
    st.subheader('Month by month')
    cols = st.columns(3)
    for mo in range(1, 13):
        lst = [e for e in evs if e['utc'].astimezone(tz).month == mo and kind_of(e) in ('sun', 'eclipse', 'phase')
               and (e['kind'] != 'phase' or e['phase'] in (0, 2))]
        body = "<div class='rc-mini'>" + (''.join(f"<div>{chip(e, tz, True)}</div>" for e in lst) or
                                         "<div class='rc-muted'>-</div>") + "</div>"
        with cols[(mo - 1) % 3]:
            st.html(card(f"{calendar.month_name[mo]} {y}", body))


# ------------------------------------------------------------------------------------------------ Watches
def render_watches(ctx):
    m = ctx['moment']
    c1, c2 = st.columns(2)
    start = c1.date_input('From', value=min(max(m.date(), rc.FIRST), rc.LAST - dt.timedelta(days=41)),
                          min_value=rc.FIRST, max_value=rc.LAST - dt.timedelta(days=41), key='rc_w_from',
                          format='DD/MM/YYYY')
    ndays = int(c2.slider('Days', 7, 40, 14, key='rc_w_days'))
    days = hdays_ctx(ctx, start, start + dt.timedelta(days=ndays - 1))
    rows = []
    for h in days:
        cls = " class='rc-today-row'" if h.civil == m.date() else ''
        w = ''.join(f"<td>{hm(a)}</td>" for _, a, _ in h.watches)
        flag = esc(h.convention) if h.fallback else ''
        rows.append(f"<tr{cls}><td>{h.civil:%a %d %b %Y}</td><td>{esc(SHORT[h.weekday])} · "
                    f"{esc(h.prince.split(' (')[0])}</td>{w}<td>{dhm(h.end)}</td><td>{flag}</td></tr>")
    head = ("<tr><th>Civil date</th><th>King · Prince</th><th>Part 1 (sunrise)</th><th>Part 2</th><th>Part 3</th>"
            "<th>Part 4</th><th>Part 5</th><th>Part 6</th><th>Day ends (next sunrise)</th><th></th></tr>")
    if ctx['conv'] != 'sunrise':
        head = head.replace('Part 1 (sunrise)', 'Part 1 (midnight LMT)').replace('Day ends (next sunrise)', 'Day ends')
    st.html(f"<div class='rc-muted'>Start of each of the six parts at {esc(ctx['place'])} ({esc(tz_label(ctx))}). "
            f"Sunrise from JPL DE440s for your latitude, longitude and elevation.</div>"
            f"<div class='rc-scroll'><table class='rc-times'>{head}{''.join(rows)}</table></div>")
    wd = st.selectbox('Ministers of', el.WEEKDAYS, index=el.WEEKDAYS.index(hday_at(ctx, m).weekday)
                      if range_ok(m.date()) else 0, key='rc_w_day')
    trs = ''.join(f"<tr><td>Part {n}</td><td>{ministers_html(wd, n)}</td></tr>" for n in range(1, 7))
    whole = el.ministers_for(wd, 1)['whole_day']
    if whole and whole['names_dee_letters']:
        trs = f"<tr><td>Whole day</td><td><code>{esc(whole['names_dee_letters'])}</code></td></tr>" + trs
    g = el.BY_DAY.loc[wd]
    st.html(card(f"The ministers of {esc(wd)}: King {esc(g['king'])}, Prince {esc(g['prince'])}",
                 f"<table class='rc-times'>{trs}</table>" + W.card_html('watch_ministers')))


# ------------------------------------------------------------------------------------------------ Workings
def render_workings(ctx):
    st.html(card('About these workings',
                 "<p>The calendar shows <b>when</b> each working falls; the texts themselves are read on Joseph H. "
                 "Peterson's esotericarchives.com, which opens in a new tab. The app copies no ritual text. Tags: "
                 "<span class='rc-tag rc-tag-sourced'>sourced</span> stated in Dee's text, "
                 "<span class='rc-tag rc-tag-app'>app rule</span> the app's own timing rule, "
                 "<span class='rc-tag'>marker</span> astronomical moment with no rule in the sources.</p>"
                 f"<div class='rc-note'><b>Source variance.</b> {esc(W.VARIANCE)}</div>"))
    st.html(card('The workings', ''.join(W.card_html(k) for k in W.WORKINGS)))
    st.html(card('All texts', '<div>' + '</div><div>'.join(W.link_html(k) for k in W.LINKS) + '</div>'))


# ------------------------------------------------------------------------------------------------ Occasions
def _ics_escape(s: str) -> str:
    return s.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def _fold(line: str) -> str:
    b, out = line.encode('utf-8'), []
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(b[:cut].decode('utf-8'))
        b = b' ' + b[cut:]
    out.append(b.decode('utf-8'))
    return '\r\n'.join(out)


def ics(events: list[dict]) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Sidereal Enochian Chart//Ritual calendar//EN',
         'CALSCALE:GREGORIAN', 'X-WR-CALNAME:Enochian ritual calendar']
    for e in events:
        u = e['utc']
        L += ['BEGIN:VEVENT', f"UID:{e['kind']}-{e.get('body', e.get('phase', ''))}-{u:%Y%m%dT%H%M%S}@sidereal-enochian",
              f'DTSTAMP:{stamp}', f'DTSTART:{u:%Y%m%dT%H%M%SZ}',
              f"DTEND:{(u + dt.timedelta(minutes=1)):%Y%m%dT%H%M%SZ}",
              'SUMMARY:' + _ics_escape(rc.title(e)), 'DESCRIPTION:' + _ics_escape(rc.detail(e) + ' (NASA JPL DE440s)'),
              'END:VEVENT']
    L.append('END:VCALENDAR')
    return '\r\n'.join(_fold(x) for x in L) + '\r\n'


def render_occasions(ctx):
    tz = ctx['tz']
    c1, c2 = st.columns([1, 3])
    y = int(c1.number_input('Year', 1850, 2149, ctx['moment'].year, 1, key='rc_o_year'))
    kinds = c2.multiselect('Show', list(KIND_LABELS), default=['sun', 'planet', 'phase', 'eclipse'],
                           format_func=KIND_LABELS.get, key='rc_o_kinds')
    evs = [e for e in occ_between(dt.datetime(y, 1, 1, tzinfo=tz),
                                  dt.datetime(y + 1, 1, 1, tzinfo=tz) if y < 2149 else dt.datetime(2149, 12, 30, tzinfo=tz))
           if kind_of(e) in kinds]
    work = {'sun': 'zodiac_king', 'planet': 'planet_ingress', 'moon_in': 'planet_ingress', 'phase': 'moon',
            'eclipse': 'moon'}
    rows = [{'Local date': f"{e['utc'].astimezone(tz):%a %d %b %Y}", 'Local time': f"{e['utc'].astimezone(tz):%H:%M:%S}",
             'UTC': f"{e['utc']:%Y-%m-%d %H:%M:%S}", 'Occasion': rc.title(e), 'Detail': rc.detail(e),
             'Working': W.WORKINGS[work[kind_of(e)]]['title']} for e in evs]
    df = pd.DataFrame(rows)
    st.caption(f"{len(df)} occasions in {y} · {ctx['place']} · local times in {tz_label(ctx)} · NASA JPL DE440s")
    table(df)
    b1, b2 = st.columns(2)
    b1.download_button('Add to my calendar (.ics)', ics(evs), file_name=f'enochian_ritual_calendar_{y}.ics',
                       mime='text/calendar', width='stretch', on_click='ignore')
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    b2.download_button('Download as a table (.csv)', buf.getvalue().encode('utf-8-sig'),
                       file_name=f'enochian_ritual_calendar_{y}.csv', mime='text/csv', width='stretch',
                       on_click='ignore')
    st.caption("The .ics file opens in Outlook, Google Calendar or Apple Calendar; each occasion is a one-minute event "
               "at its exact JPL time, so your calendar shows it in your own time zone.")


# ------------------------------------------------------------------------------------------------ How / About
def render_how(ctx):
    try:
        with open('HOW_IT_WORKS.md', encoding='utf-8') as f:
            st.markdown(f.read())
    except FileNotFoundError:
        st.info('HOW_IT_WORKS.md is missing from the app folder.')


def render_about(ctx):
    st.markdown(
        "**Sidereal Enochian Chart · ritual calendar.** An accurate sidereal sky (IAU constellations, NASA JPL "
        "DE440s via Skyfield) read through John Dee's Heptarchia, with a calendar of the workings modelled on the "
        "Sky Gahshomar app.\n\n"
        "**Sources.** Joseph H. Peterson (ed.), *John Dee's Five Books of Mystery*; Geoffrey James, *The Enochian "
        "Evocation of Dr John Dee*; Dee's *De Heptarchia Mystica*, *Compendium Heptarchiae Mysticae* and *Liber "
        "exercitii Heptarchici* in Peterson's editions at esotericarchives.com (linked, not copied).\n\n"
        "**Data.** Planetary positions: NASA JPL DE440s. Constellation boundaries: IAU (Delporte 1930; Roman 1987 "
        "lookup). Places: GeoNames (CC BY 4.0). Time zones: IANA tz database. Elevation: Terrain Tiles on the AWS "
        "Registry of Open Data (Mapzen/Tilezen: SRTM, USGS 3DEP, GMTED2010 and others) and the Open-Meteo Elevation "
        "API (Copernicus DEM GLO-90). To fill in the elevation, the app sends only the coordinates of the place "
        "(never your name or birth details) to those services.\n\n"
        "**Enochian letters.** The 'Enochian script' switch uses the font Oracle Enochian, made from the drawings "
        "'Enochian - <letter>.svg' by Лорд Алекс (Wikimedia Commons, CC BY-SA 4.0). The font is therefore CC BY-SA 4.0: "
        "see assets/fonts/OracleEnochian-LICENSE.txt. The letter forms follow Dee's table of 6 May 1583 (Sloane MS "
        "3188, f. 104).")
    st.subheader('Sources and certainty')
    table(pd.read_csv('uncertainty_log.csv', encoding='utf-8'))
