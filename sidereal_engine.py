"""
Sidereal chart engine — steps 1 & 2.

Step 1 (astronomy): apparent topocentric positions from NASA JPL DE440s,
    reduced by Skyfield using IAU standards (ICRS frame, IAU 2000A/2006
    precession-nutation, aberration, light-time, deflection).
Step 2 (zodiac): each body / chart angle is assigned to the IAU constellation
    (Delporte 1930 boundaries, Roman 1987 lookup) that contains it.
    Bodies are placed by their *actual* RA/Dec, so a planet off the ecliptic
    can fall in a non-zodiacal constellation (e.g. Orion, Cetus, Sextans).
    Ascendant and Midheaven are ecliptic points (latitude 0).

Valid date range with DE440s: 1849-12-26 to 2150-01-22.
"""
from math import atan2, cos, sin, tan, radians, degrees
from skyfield.api import Loader, wgs84
from skyfield.framelib import ecliptic_frame
from skyfield.positionlib import position_of_radec
from skyfield import nutationlib, earthlib
from skyfield.api import load_constellation_map, load_constellation_names
from skyfield.framelib import ICRS_to_J2000
from skyfield.functions import load_bundled_npy, mxv, to_spherical
from skyfield.precessionlib import compute_precession
from skyfield.timelib import julian_date_of_besselian_epoch
import numpy as _np

_load = Loader('ephem')
ts = _load.timescale()
eph = _load('de440s.bsp')
_const_name = dict(load_constellation_names())

# IAU constellation lookup in the MEAN equator and equinox of B1875.0, the frame in which Delporte (1930) drew the
# boundaries. Skyfield's load_constellation_map() rotates to the TRUE equator of 1875 (its nutation included),
# which shifts every boundary by a few arcseconds: the Sun's entry times then differ from JPL Horizons by 2-10
# minutes. With the mean frame (checked against Horizons quantity 29, Nov 2026, 21 entries in 2026) the Sun's entries
# agree to 22-26 s, Mercury/Venus/Mars to 14-32 s and Saturn to 294 s (about 0.4 arcsec of its slow motion).
_C = load_bundled_npy('constellations.npz')
_SRA, _SDEC, _R2I, _ABBR = _C['sorted_ra'], _C['sorted_dec'], _C['radec_to_index'], _C['indexed_abbreviations']
_PB1875 = compute_precession(julian_date_of_besselian_epoch(1875)) @ ICRS_to_J2000


def _const_at(position):
    """IAU constellation abbreviation(s) of a Skyfield position (scalar or array)."""
    _, dec, ra = to_spherical(mxv(_PB1875, position.position.au))
    i = _np.searchsorted(_SRA, (_np.degrees(ra) / 15.0) % 24.0)
    j = _np.searchsorted(_SDEC, _np.degrees(dec), side='right')
    return _ABBR[_R2I[i, j]]

BODIES = {
    'Sun': 'sun', 'Moon': 'moon', 'Mercury': 'mercury', 'Venus': 'venus',
    'Mars': 'mars barycenter',  # DE440s has no Mars body centre; offset is centimetres
    'Jupiter': 'jupiter barycenter', 'Saturn': 'saturn barycenter',
    'Uranus': 'uranus barycenter', 'Neptune': 'neptune barycenter',
    'Pluto': 'pluto barycenter',
}


def constellation_of(pos):
    abbr = _const_at(pos)
    return abbr, _const_name[abbr]


def ecliptic_point_constellation(lon_deg, t):
    """IAU constellation containing the ecliptic-of-date point (lon, lat=0)."""
    eps = radians(_true_obliquity_deg(t))
    lam = radians(lon_deg)
    ra = atan2(sin(lam) * cos(eps), cos(lam)) % (2 * 3.141592653589793)
    dec = degrees(__import__('math').asin(sin(eps) * sin(lam)))
    pos = position_of_radec(degrees(ra) / 15.0, dec, epoch=t)
    return constellation_of(pos)


def _true_obliquity_deg(t):
    mean = nutationlib.mean_obliquity(t.tdb) / 3600.0
    _, deps = nutationlib.iau2000a_radians(t)
    return mean + degrees(deps)


def angles(t, lat_deg, lon_deg):
    """Ascendant and Midheaven (ecliptic longitude of date, degrees)."""
    ramc = radians((t.gast * 15.0 + lon_deg) % 360.0)
    eps = radians(_true_obliquity_deg(t))
    phi = radians(lat_deg)
    asc = degrees(atan2(cos(ramc), -(sin(ramc) * cos(eps) + tan(phi) * sin(eps)))) % 360
    mc = degrees(atan2(sin(ramc), cos(ramc) * cos(eps))) % 360
    return asc, mc


def chart(utc, lat_deg, lon_deg, elev_m=0.0):
    """utc: (Y, M, D, h, m, s). Returns list of dict rows."""
    t = ts.utc(*utc)
    observer = eph['earth'] + wgs84.latlon(lat_deg, lon_deg, elevation_m=elev_m)
    rows = []
    for name, key in BODIES.items():
        app = observer.at(t).observe(eph[key]).apparent()
        ra, dec, dist = app.radec(epoch='date')
        elat, elon, _ = app.frame_latlon(ecliptic_frame)
        alt, az, _ = app.altaz()
        abbr, cname = constellation_of(app)
        rows.append(dict(body=name, ra_h=ra.hours, dec_deg=dec.degrees,
                         ecl_lon=elon.degrees, ecl_lat=elat.degrees,
                         alt=alt.degrees, az=az.degrees, dist_au=dist.au,
                         const=abbr, constellation=cname))
    asc, mc = angles(t, lat_deg, lon_deg)
    for name, lon in (('Ascendant', asc), ('Midheaven', mc)):
        abbr, cname = ecliptic_point_constellation(lon, t)
        rows.append(dict(body=name, ecl_lon=lon, ecl_lat=0.0, const=abbr,
                         constellation=cname))
    return t, rows


def ecliptic_constellation_bands(t, step=0.01):
    """Where the ecliptic of date crosses IAU boundaries: list of (start_lon, abbr, name)."""
    bands, prev = [], None
    n = int(360 / step)
    for i in range(n):
        lon = i * step
        abbr, cname = ecliptic_point_constellation(lon, t)
        if abbr != prev:
            bands.append((round(lon, 2), abbr, cname))
            prev = abbr
    return bands
