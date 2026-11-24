"""Ritual calendar engine: when the Heptarchic workings fall, timed with NASA JPL DE440s (via Skyfield).

Modelled on Sky Gahshomar (its Today / Month / Year / Gahs / Festivals pages), but for John Dee's Heptarchia.

1. Heptarchic days and the six watches.  Same rule as enochian_layer.day_governance(): by default the day runs from
   local sunrise to the next local sunrise (Sun's upper limb on a horizon of -0.8333 deg minus the dip for the
   elevation), and the King and Prince govern the whole day, "the rest according to the six partes of the day"
   (Peterson, Five Books, PDF p160). The six parts are six equal parts of that sunrise-to-sunrise day. Option:
   local-mean-time midnight. With no sunrise (polar day or night) the day falls back to LMT midnight and is flagged.
   A civil date shows the Heptarchic day whose sunrise falls on that date (as in Sky Gahshomar's month grid).

2. Sidereal ingresses.  The moment a body passes from one IAU constellation into another (Delporte 1930
   boundaries, the same lookup the chart uses), for the Sun, Moon, Mercury, Venus, Mars, Jupiter and Saturn.
   Positions are GEOCENTRIC apparent (the convention of published ephemerides), so the times do not depend on the
   place; the chart itself is topocentric, which can move the Moon's entry by up to about two hours.
   Times are found by sampling and then bisection to better than one second.

3. Moon phases (Skyfield almanac.moon_phases), lunar eclipses (Skyfield eclipselib, umbra and penumbra with the
   Danjon enlargement) and solar eclipses (found here: at each new Moon the least geocentric Sun-Moon separation is
   compared with the parallaxes and semi-diameters, the classical criterion in Meeus, Astronomical Algorithms
   ch. 54). For the chosen place the app also checks whether the eclipse can be seen there (Sun or Moon above
   the horizon, and for a solar eclipse a topocentric overlap of the discs).

Valid 1850-2149 (DE440s).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from math import sqrt, asin, degrees
from zoneinfo import ZoneInfo

import numpy as np
from skyfield import almanac, eclipselib
from skyfield.api import wgs84

import sidereal_engine as se
import enochian_layer as el

ts, eph = se.ts, se.eph
EARTH, SUN, MOON = eph['earth'], eph['sun'], eph['moon']
FIRST, LAST = dt.date(1850, 1, 2), dt.date(2149, 12, 30)

# body -> (ephemeris key, sampling step in hours)
BODIES = {'Sun': ('sun', 6), 'Moon': ('moon', 1), 'Mercury': ('mercury', 6), 'Venus': ('venus', 8),
          'Mars': ('mars barycenter', 12), 'Jupiter': ('jupiter barycenter', 24), 'Saturn': ('saturn barycenter', 24)}
GLYPH = {'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂', 'Jupiter': '♃', 'Saturn': '♄'}
PHASES = ['New Moon', 'First quarter', 'Full Moon', 'Last quarter']
PHASE_GLYPH = ['🌑', '🌓', '🌕', '🌗']
R_EARTH, R_MOON, R_SUN = 6378.137, 1737.4, 696000.0      # km (IAU 2015 nominal solar radius; IAU Moon radius)


# ------------------------------------------------------------------------------------------- time helpers
def tzinfo(tzname: str | None, offset_h: float = 0.0):
    if tzname:
        try:
            return ZoneInfo(tzname)
        except Exception:
            pass
    return dt.timezone(dt.timedelta(hours=offset_h))


def to_local(t, tz) -> dt.datetime:
    """Skyfield Time (scalar) -> aware local datetime, rounded to the second."""
    u = t.utc_datetime()
    return (u + dt.timedelta(microseconds=500_000)).replace(microsecond=0).astimezone(tz)


def _t(d: dt.datetime):
    return ts.from_datetime(d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc))


# ------------------------------------------------------------------------------------------- Heptarchic days
@dataclass
class HeptDay:
    civil: dt.date                 # civil date this Heptarchic day is shown on
    weekday: str
    king: str
    prince: str
    realm: str
    start: dt.datetime             # aware local datetimes
    end: dt.datetime
    convention: str
    fallback: bool = False
    watches: list = field(default_factory=list)   # [(n, start, end)]

    def watch_at(self, moment: dt.datetime):
        for n, a, b in self.watches:
            if a <= moment < b:
                return n
        return None


def _horizon(elev_m: float) -> float:
    return -0.8333 - (0.0293 * sqrt(elev_m) if elev_m > 0 else 0.0)


def _risings(lat, lon, elev, d0: dt.date, d1: dt.date):
    obs = EARTH + wgs84.latlon(lat, lon, elevation_m=elev)
    t0 = ts.utc(d0.year, d0.month, d0.day) - 1.5
    t1 = ts.utc(d1.year, d1.month, d1.day) + 2.5
    tr, ok = almanac.find_risings(obs, SUN, t0, t1, horizon_degrees=_horizon(elev))
    return [t for t, o in zip(tr, ok) if o]


def _lmt_weekday(t, lon) -> str:
    return el.WEEKDAYS[(t.utc_datetime() + dt.timedelta(hours=lon / 15.0)).weekday()]


def _mk_day(civil, start_t, end_t, lon, tz, convention, fallback=False) -> HeptDay:
    wd = _lmt_weekday(start_t, lon)
    g = el.BY_DAY.loc[wd]
    a, b = to_local(start_t, tz), to_local(end_t, tz)
    step = (end_t.tt - start_t.tt) / 6.0
    watches = [(k + 1, to_local(ts.tt_jd(start_t.tt + k * step), tz),
                to_local(ts.tt_jd(start_t.tt + (k + 1) * step), tz) if k < 5 else b) for k in range(6)]
    return HeptDay(civil, wd, g['king'], g['prince'], g['realm'], a, b, convention, fallback, watches)


def _lmt_midnight_day(civil: dt.date, lon, tz, fallback=False) -> HeptDay:
    u0 = dt.datetime(civil.year, civil.month, civil.day, tzinfo=dt.timezone.utc) - dt.timedelta(hours=lon / 15.0)
    t0, t1 = _t(u0), _t(u0 + dt.timedelta(days=1))
    conv = 'midnight (LMT)' + (' - FALLBACK: no sunrise at this latitude/date' if fallback else '')
    return _mk_day(civil, t0, t1, lon, tz, conv, fallback)


def heptarchic_days(d0: dt.date, d1: dt.date, lat, lon, elev, tz, convention='sunrise') -> list[HeptDay]:
    """One HeptDay per civil date d0..d1 (inclusive)."""
    out, n = [], (d1 - d0).days + 1
    dates = [d0 + dt.timedelta(days=k) for k in range(n)]
    if convention != 'sunrise':
        return [_lmt_midnight_day(d, lon, tz) for d in dates]
    rises = _risings(lat, lon, elev, d0, d1)
    loc = [to_local(r, tz).date() for r in rises]
    for d in dates:
        idx = [i for i, ld in enumerate(loc) if ld == d]
        if idx and idx[0] + 1 < len(rises):
            i = idx[0]
            out.append(_mk_day(d, rises[i], rises[i + 1], lon, tz, 'sunrise (local)'))
        else:
            out.append(_lmt_midnight_day(d, lon, tz, fallback=True))
    return out


def heptarchic_day_at(moment: dt.datetime, lat, lon, elev, tz, convention='sunrise') -> HeptDay:
    """The Heptarchic day running at an aware local moment (before sunrise = yesterday's day)."""
    d = moment.date()
    for h in heptarchic_days(d - dt.timedelta(days=1), d + dt.timedelta(days=1), lat, lon, elev, tz, convention):
        if h.start <= moment < h.end:
            return h
    return heptarchic_days(d, d, lat, lon, elev, tz, convention)[0]


# ------------------------------------------------------------------------------------------- ingresses
def _const(key, tt):
    t = ts.tt_jd(tt)
    return se._const_at(EARTH.at(t).observe(eph[key]).apparent())


def ingresses(t0_tt: float, t1_tt: float, bodies=None) -> list[dict]:
    """Constellation changes of each body between two TT Julian dates (geocentric apparent)."""
    out = []
    for body in bodies or BODIES:
        key, step_h = BODIES[body]
        grid = np.arange(t0_tt, t1_tt + step_h / 24.0, step_h / 24.0)
        c = _const(key, grid)
        ch = np.nonzero(c[1:] != c[:-1])[0]
        if not len(ch):
            continue
        lo, hi = grid[ch].copy(), grid[ch + 1].copy()
        c_lo = c[ch]
        for _ in range(26):                                     # step / 2**26 -> < 0.1 s even for 24 h
            mid = (lo + hi) / 2
            cm = _const(key, mid)
            same = cm == c_lo
            lo = np.where(same, mid, lo)
            hi = np.where(same, hi, mid)
        to_c = _const(key, hi)
        for k in range(len(ch)):
            out.append(dict(kind='ingress', body=body, tt=float(hi[k]), from_abbr=str(c_lo[k]),
                            to_abbr=str(to_c[k]), from_name=se._const_name[str(c_lo[k])],
                            to_name=se._const_name[str(to_c[k])]))
    return out


# ------------------------------------------------------------------------------------------- Moon and eclipses
def moon_phases(t0_tt, t1_tt) -> list[dict]:
    t, y = almanac.find_discrete(ts.tt_jd(t0_tt), ts.tt_jd(t1_tt), almanac.moon_phases(eph))
    return [dict(kind='phase', phase=int(p), name=PHASES[int(p)], tt=float(ti.tt)) for ti, p in zip(t, y)]


def lunar_eclipses(t0_tt, t1_tt) -> list[dict]:
    t, y, details = eclipselib.lunar_eclipses(ts.tt_jd(t0_tt), ts.tt_jd(t1_tt), eph)
    names = ['Penumbral', 'Partial', 'Total']
    out = []
    for i, (ti, k) in enumerate(zip(t, y)):
        out.append(dict(kind='eclipse', body='Moon', ecl_type=names[int(k)] + ' lunar eclipse', tt=float(ti.tt),
                        umbral_mag=float(details['umbral_magnitude'][i]),
                        penumbral_mag=float(details['penumbral_magnitude'][i])))
    return out


def _sun_moon(t, observer=None):
    o = (observer or EARTH).at(t)
    s, m = o.observe(SUN).apparent(), o.observe(MOON).apparent()
    return s, m


def _sep_geo(tt):
    t = ts.tt_jd(tt)
    s, m = _sun_moon(t)
    return s.separation_from(m).degrees


def solar_eclipses(t0_tt, t1_tt) -> list[dict]:
    """Solar eclipses visible somewhere on Earth, found at each new Moon (geocentric criterion, Meeus ch. 54)."""
    out = []
    for nm in [p for p in moon_phases(t0_tt - 2, t1_tt + 2) if p['phase'] == 0]:
        if not (t0_tt <= nm['tt'] <= t1_tt):
            continue
        tm = nm['tt']
        for half, step in ((0.4, 5 / 1440), (6 / 1440, 5 / 86400)):    # least separation: 5-min grid, then 5-s grid
            grid = tm + np.arange(-half, half + 1e-12, step)
            tm = float(grid[int(np.argmin(_sep_geo(grid)))])
        t = ts.tt_jd(tm)
        s, m = _sun_moon(t)
        sep = s.separation_from(m).degrees
        dm, ds = m.distance().km, s.distance().km
        pm, ps = degrees(asin(R_EARTH / dm)), degrees(asin(R_EARTH / ds))
        rm, rs = degrees(asin(R_MOON / dm)), degrees(asin(R_SUN / ds))
        if sep >= pm - ps + rm + rs:                              # the penumbral cone misses the Earth
            continue
        if sep < (pm - ps) * 0.9966:                              # the shadow axis meets the Earth (flattening ~ 1/298)
            rm_s, rs_s = degrees(asin(R_MOON / (dm - R_EARTH))), degrees(asin(R_SUN / (ds - R_EARTH)))
            rm_c, rs_c = degrees(asin(R_MOON / dm)), degrees(asin(R_SUN / ds))
            if rm_s > rs_s and rm_c > rs_c * 1.0:
                kind = 'Total'
            elif rm_s < rs_s and rm_c < rs_c:
                kind = 'Annular'
            else:
                kind = 'Hybrid'
        else:
            kind = 'Partial'
        out.append(dict(kind='eclipse', body='Sun', ecl_type=kind + ' solar eclipse', tt=tm, sep_deg=sep))
    return out


def eclipse_local(ev: dict, lat, lon, elev) -> dict:
    """Can this eclipse be seen from the place? Returns {'visible': bool, 'tt': time of greatest local phase}."""
    obs = EARTH + wgs84.latlon(lat, lon, elevation_m=elev)
    if ev['body'] == 'Moon':
        alt = obs.at(ts.tt_jd(ev['tt'])).observe(MOON).apparent().altaz()[0].degrees
        return dict(visible=bool(alt > 0), tt=ev['tt'], alt=float(alt))
    grid = ev['tt'] + np.arange(-0.15, 0.15 + 1e-9, 2 / 1440)          # +-3.6 h, 2-minute steps
    t = ts.tt_jd(grid)
    o = obs.at(t)
    s, m = o.observe(SUN).apparent(), o.observe(MOON).apparent()
    sep = s.separation_from(m).degrees
    rm = np.degrees(np.arcsin(R_MOON / m.distance().km))
    rs = np.degrees(np.arcsin(R_SUN / s.distance().km))
    alt = s.altaz()[0].degrees
    ok = (sep < rm + rs) & (alt > -0.8333)
    if not ok.any():
        return dict(visible=False, tt=ev['tt'])
    k = int(np.argmin(np.where(ok, sep, 99)))
    mag = float((rm[k] + rs[k] - sep[k]) / (2 * rs[k]))
    return dict(visible=True, tt=float(grid[k]), magnitude=round(mag, 2), alt=float(alt[k]))


# ------------------------------------------------------------------------------------------- the year's occasions
def occasions(year: int) -> list[dict]:
    """All timed occasions of a civil year (UTC-based window with a day of margin), sorted by time.
    Each dict has 'kind' in {'ingress', 'phase', 'eclipse'} and 'tt' (TT Julian date)."""
    y0 = max(dt.date(year, 1, 1) - dt.timedelta(days=1), FIRST)
    y1 = min(dt.date(year, 12, 31) + dt.timedelta(days=2), LAST)
    t0, t1 = ts.utc(y0.year, y0.month, y0.day).tt, ts.utc(y1.year, y1.month, y1.day).tt
    ev = ingresses(t0, t1) + moon_phases(t0, t1) + lunar_eclipses(t0, t1) + solar_eclipses(t0, t1)
    for e in ev:
        e['utc'] = ts.tt_jd(e['tt']).utc_datetime().replace(microsecond=0)
        if e['kind'] == 'ingress':
            z = el.ZK.loc[e['to_name']] if e['to_name'] in el.ZK.index else None
            e['zodiac_king'] = None if z is None else z['zodiac_king']
            e['zodiac_sign'] = None if z is None else z['sign']
            e['tribe'] = None if z is None else z['tribe']
            e['quarter'] = None if z is None else z['quarter']
            h = el.BY_PLANET.loc[e['body']]
            e['hept_king'], e['hept_prince'] = h['king'], h['prince']
    return sorted(ev, key=lambda e: e['tt'])


def title(e: dict) -> str:
    if e['kind'] == 'ingress':
        return f"{GLYPH[e['body']]} {e['body']} enters {e['to_name']}"
    if e['kind'] == 'phase':
        return f"{PHASE_GLYPH[e['phase']]} {e['name']}"
    return ('🌘 ' if e['body'] == 'Moon' else '🌒 ') + e['ecl_type']


def detail(e: dict) -> str:
    if e['kind'] == 'ingress':
        k = (f"zodiac King {e['zodiac_king']} ({e['zodiac_sign']}, tribe {e['tribe']}, {e['quarter']})"
             if e['zodiac_king'] else "no zodiac King (not one of the twelve signs)")
        return f"from {e['from_name']}; {k}; the {e['body']}'s Heptarchic King is {e['hept_king']}"
    if e['kind'] == 'eclipse':
        if e['body'] == 'Moon':
            return f"umbral magnitude {e['umbral_mag']:.2f}"
        return 'visible from part of the Earth'
    return ''
