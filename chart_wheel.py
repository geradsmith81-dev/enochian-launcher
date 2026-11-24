"""Sidereal chart wheel: 13 IAU ecliptic constellations at their true widths, with planets.

Ecliptic longitude runs counter-clockwise; the Ascendant sits at 9 o'clock (the usual chart
convention). Filled marker = body above the local horizon; open marker = below. Bodies lying in
a constellation outside the zodiac (e.g. Cetus) are labelled with that constellation.
"""
from math import radians
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

ZODIACAL = {'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpius',
            'Ophiuchus', 'Sagittarius', 'Capricornus', 'Aquarius', 'Pisces'}
INK, GREY, ACCENT = '#222222', '#8a8a8a', '#7a3b8f'
LIGHT = dict(fig_bg='white', face='white', band_a='#ececec', band_b='#dcdcdc', band_edge='white', band_text=INK,
             ring=GREY, ink=INK, grey=GREY, up=INK, down_face='white', accent=ACCENT, label_bg='white')


def _style():
    matplotlib.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                                'axes.titlesize': 10, 'savefig.dpi': 300})


def draw_wheel(rows, bands, title, asc, mc, ax=None, theme=None):
    """rows: chart rows (body, ecl_lon, alt, constellation); bands: [(start, abbr, name)]."""
    _style()
    th_ = dict(LIGHT, **(theme or {}))
    if ax is None:
        fig = plt.figure(figsize=(6.4, 6.4))
        ax = fig.add_subplot(projection='polar')
    fig = ax.figure
    fig.patch.set_facecolor(th_['fig_bg']); fig.patch.set_alpha(0 if th_['fig_bg'] == 'none' else 1)
    ax.set_facecolor(th_['face']); ax.patch.set_alpha(th_.get('face_alpha', 1.0))
    ax.set_theta_direction(1)
    ax.set_theta_offset(np.pi - radians(asc))
    ax.set_ylim(0, 1.0)
    ax.set_xticks([]); ax.set_yticks([]); ax.spines['polar'].set_visible(False); ax.grid(False)

    # constellation ring (true unequal widths)
    starts = [b[0] for b in bands]
    ends = starts[1:] + [starts[0] + 360]
    # colour groups: bands alternate shade, except that Ophiuchus takes Scorpius's shade (user request), so
    # the two read as one region. With that pair merged there are 12 groups, which alternate evenly round the ring.
    same = {frozenset(pair) for pair in th_.get('same_colour', (('Sco', 'Oph'),))}
    groups, g = [], 0
    for i, (s, abbr, name) in enumerate(bands):
        if i and frozenset((bands[i - 1][1], abbr)) not in same:
            g += 1
        groups.append(g)
    for i, ((s, abbr, name), e) in enumerate(zip(bands, ends)):
        th = np.radians(np.linspace(s, e, 80))
        shade = th_['band_a'] if groups[i] % 2 == 0 else th_['band_b']
        ax.fill_between(th, 0.84, 1.0, color=shade, lw=0)
        ax.plot([np.radians(s)] * 2, [0.84, 1.0], color=th_['band_edge'], lw=1.2)
        mid = np.radians((s + e) / 2)
        lab = name if (e - s) > 12 else abbr
        rot = np.degrees(mid + ax.get_theta_offset()) - 90
        rot = (rot + 180) % 360 - 180
        if abs(rot) > 90:
            rot += 180
        ax.text(mid, 0.92, lab, ha='center', va='center', fontsize=7.5, color=th_['band_text'], rotation=rot,
                rotation_mode='anchor')
    ax.plot(np.radians(np.linspace(0, 360, 361)), [0.84] * 361, color=th_['ring'], lw=0.6)

    # angles
    for lon, lab in ((asc, 'Asc'), (asc + 180, 'Desc'), (mc, 'MC'), (mc + 180, 'IC')):
        ax.plot([np.radians(lon)] * 2, [0.0, 0.84], color=th_['grey'], lw=0.8 if lab in ('Asc', 'MC') else 0.5,
                ls='-' if lab in ('Asc', 'MC') else ':')
        ax.text(np.radians(lon), 0.80, lab, ha='center', va='center', fontsize=7, color=th_['grey'],
                bbox=dict(fc=th_['label_bg'], ec='none', pad=0.6))

    # bodies, staggered radially when crowded
    bodies = [r for r in rows if r['body'] not in ('Ascendant', 'Midheaven')]
    bodies.sort(key=lambda r: r['ecl_lon'])
    radii, last = [], {}
    for r in bodies:
        lvl = 0
        while any(abs(((r['ecl_lon'] - l + 180) % 360) - 180) < 12 for l in last.get(lvl, [])):
            lvl += 1
        last.setdefault(lvl, []).append(r['ecl_lon'])
        radii.append(0.70 - 0.17 * lvl)
    for r, rad in zip(bodies, radii):
        th = np.radians(r['ecl_lon'])
        up = r.get('alt', 0) > 0
        off = r['constellation'] not in ZODIACAL
        col = th_['accent'] if off else th_['up']
        ax.plot(th, rad, marker='o', ms=7, mfc=col if up else th_['down_face'], mec=col, mew=1.4, ls='none', zorder=5)
        lab = r['body'] + (f"\n(in {r['constellation']})" if off else '')
        right_half = np.cos(th + ax.get_theta_offset()) > 0     # marker on the right of the wheel
        ax.annotate(lab, (th, rad), xytext=(-8 if right_half else 8, 0), textcoords='offset points',
                    ha='right' if right_half else 'left', va='center',
                    fontsize=7, color=th_['accent'] if off else th_['ink'], zorder=6)

    ax.set_title(title, loc='left', fontsize=10, color=th_['ink'], pad=14)
    fig.text(0.02, 0.015, 'Filled = above horizon · open = below · ' + ('rose' if theme else 'purple')
             + ' = outside the 13 ecliptic constellations', fontsize=7, color=th_['grey'])
    return fig
