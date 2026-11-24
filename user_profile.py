"""The user's profile: name, picture, birth details and the place where they live.
Modelled on the profile of the Sidereal Oracle app (user request).

Where it is kept
  * Desktop app (started with "Start app.pyw"; tools/launch.py sets ENOCHIAN_PROFILE_DIR): in
    %LOCALAPPDATA%\SiderealEnochianChart\profile (profile.json and avatar.png), so it is there next time.
    It never leaves the computer. Only the person at this computer reads or changes it: when the app is shared
    on the local network, visitors from other devices get a profile that lasts only while their tab is open.
    Older versions kept it in the folder profile/ inside the app; the launcher moves that folder once.
  * Online (Streamlit Community Cloud) or any other start: only while the app is open in that browser tab.
    Nothing is written to the server's disk, which every visitor shares.

Where you live
  Typed as a town (place search), or found with "Use my location": the browser asks the device for its position
  (GPS / Wi-Fi), and the nearest town in the gazetteer gives the time zone. The position is used only inside the
  app; it is saved in the profile file on this computer and nowhere else.
"""
import base64
import calendar
import datetime as dt
import html
import io
import json
import os
import re
import shutil

import streamlit as st
from PIL import Image, ImageOps

import places

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get('ENOCHIAN_PROFILE_DIR') or os.path.join(HERE, 'profile')
STORE = bool(os.environ.get('ENOCHIAN_PROFILE_DIR'))   # set only by tools/launch.py (desktop copy)
KEY = 'enochian_profile'
MAX_NAME = 40
MAX_UPLOAD_MB = 15
MAX_PIXELS = 50_000_000      # larger pictures (after JPEG reduction on load) are refused
AVATAR_PX = 256
BORDER = '#bde188'          # aurora green (theme.PALETTE['aurora'])
GPS = 'pf_gps'


# ---------------- storage ----------------
def _local():
    """True when the profile is kept on this computer's disk for this visitor: the desktop copy, and the
    visitor is the person at this computer (not a visitor from another device while the app is shared)."""
    if not STORE:
        return False
    try:
        import desktop as dk
        return dk.client_is_local(st)
    except Exception:
        return False


def forget():
    """Drop the profile held for this browser tab (after the stored data was cleared)."""
    st.session_state.pop(KEY, None)


def _read_json(name, default):
    try:
        with open(os.path.join(DIR, name), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _write_json(name, obj):
    os.makedirs(DIR, exist_ok=True)
    tmp = os.path.join(DIR, name + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(DIR, name))


def _read_disk():
    d = _read_json('profile.json', {})
    av = None
    p = os.path.join(DIR, 'avatar.png')
    if os.path.exists(p):
        with open(p, 'rb') as f:
            av = f.read()
    return dict(name=clean_name(d.get('name', '')), avatar=av, birth=_valid_birth(d.get('birth')),
                home=_valid_home(d.get('home')))


def _write_disk(prof):
    _write_json('profile.json', {'name': prof['name'], 'birth': prof.get('birth'), 'home': prof.get('home')})
    p = os.path.join(DIR, 'avatar.png')
    if prof['avatar']:
        with open(p + '.tmp', 'wb') as f:
            f.write(prof['avatar'])
        os.replace(p + '.tmp', p)
    elif os.path.exists(p):
        os.remove(p)


def get():
    """The current profile: dict(name, avatar=PNG bytes or None, birth=dict or None, home=dict or None)."""
    if KEY not in st.session_state:
        st.session_state[KEY] = _read_disk() if _local() else dict(name='', avatar=None, birth=None, home=None)
    return st.session_state[KEY]


def save(name, avatar, birth, home):
    prof = dict(name=clean_name(name), avatar=avatar, birth=_valid_birth(birth), home=_valid_home(home))
    st.session_state[KEY] = prof
    st.session_state.pop('chart_search', None)       # the place search starts again from the (new) home place
    if _local():
        _write_disk(prof)


def delete():
    """Remove the profile from the screen and, on this computer, delete the profile folder."""
    st.session_state[KEY] = dict(name='', avatar=None, birth=None, home=None)
    if _local() and os.path.isdir(DIR):
        shutil.rmtree(DIR, ignore_errors=True)


# ---------------- validation ----------------
def clean_name(name):
    """Trim, collapse spaces, drop control characters, at most MAX_NAME characters."""
    name = re.sub(r'[\x00-\x1f\x7f]', '', str(name or ''))
    return re.sub(r'\s+', ' ', name).strip()[:MAX_NAME]


def _valid_birth(b):
    """Clean birth dict or None. Fields: date YYYY-MM-DD, time HH:MM, time_known, place, lat, lon,
    tz (IANA name or None), utc_offset (hours, of the local clock at birth)."""
    if not isinstance(b, dict):
        return None
    try:
        d = dt.date.fromisoformat(str(b['date']))
        t = dt.time.fromisoformat(str(b.get('time') or '12:00'))
        lat, lon, off = float(b['lat']), float(b['lon']), float(b['utc_offset'])
        if not (1850 <= d.year <= 2149 and -90 <= lat <= 90 and -180 <= lon <= 180 and -14 <= off <= 14):
            return None
        tz = b.get('tz')
        return dict(date=d.isoformat(), time=t.strftime('%H:%M'), time_known=bool(b.get('time_known', True)),
                    place=clean_name(b.get('place', '')) or f'{lat:.2f}, {lon:.2f}',
                    lat=round(lat, 5), lon=round(lon, 5), tz=str(tz)[:64] if tz else None, utc_offset=off)
    except (KeyError, ValueError, TypeError):
        return None


def _valid_home(h):
    """Where the user lives (the starting place of the chart), or None. Fields: name, country, lat, lon, tz,
    elev (ground height, m), src ('town' from the search, 'gps' from the device's position)."""
    if not isinstance(h, dict):
        return None
    try:
        lat, lon = float(h['lat']), float(h['lon'])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        # ground height in whole metres within places.ELEV_MIN..ELEV_MAX (Dead Sea shore to Everest), or None when
        # not known yet (it is then looked up from open elevation data where it is needed)
        e = h.get('elev')
        elev = None if e is None or float(e) < places.ELEV_MIN - 1 else \
            round(min(max(float(e), places.ELEV_MIN), places.ELEV_MAX))
        return dict(name=clean_name(h['name']), country=clean_name(h.get('country', '')),
                    lat=round(lat, 5), lon=round(lon, 5), tz=str(h['tz'])[:64] if h.get('tz') else None,
                    elev=elev, src='gps' if h.get('src') == 'gps' else 'town')
    except (KeyError, ValueError, TypeError):
        return None


def birth_local(b):
    """Local clock datetime of a birth (noon if the time is unknown)."""
    return dt.datetime.combine(dt.date.fromisoformat(b['date']), dt.time.fromisoformat(b['time']))


def birth_text(b):
    if not b:
        return 'no birth details'
    d = dt.date.fromisoformat(b['date'])
    t = b['time'] if b['time_known'] else 'time unknown'
    return f"born {d:%d %b %Y}, {t}, {b['place']}"


def home_text(h):
    return f"lives in {h['name']}, {h['country']}" if h else 'no home place'


# ---------------- pictures ----------------
class PictureTooLarge(ValueError):
    pass


def to_avatar(file_bytes):
    """Picture -> square PNG, AVATAR_PX pixels, turned upright from the camera's EXIF.
    A JPEG is reduced while it is decoded; pictures above MAX_PIXELS are refused (PictureTooLarge)."""
    im = Image.open(io.BytesIO(file_bytes))
    if im.format == 'JPEG':
        im.draft('RGB', (AVATAR_PX * 4, AVATAR_PX * 4))
    w, h = im.size
    if w * h > MAX_PIXELS:
        raise PictureTooLarge(f'{w} x {h} pixels')
    im.thumbnail((AVATAR_PX * 4, AVATAR_PX * 4))
    im = ImageOps.exif_transpose(im).convert('RGB')
    s = min(im.size)
    left, top = (im.width - s) // 2, (im.height - s) // 2
    im = im.crop((left, top, left + s, top + s)).resize((AVATAR_PX, AVATAR_PX), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, format='PNG', optimize=True)
    return out.getvalue()


def img_html(png, size):
    b64 = base64.b64encode(png).decode()
    return (f'<img src="data:image/png;base64,{b64}" width="{size}" height="{size}" alt="profile picture" '
            f'style="border-radius:50%; object-fit:cover; border:2px solid {BORDER}; box-shadow:0 0 14px {BORDER}55;">')


def initials_html(name, size):
    ini = ''.join(w[0] for w in name.split()[:2]).upper() or '✦'
    return (f'<div style="width:{size}px;height:{size}px;border-radius:50%;border:2px solid {BORDER};'
            f'display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;'
            f'font-size:{size * 0.4:.0f}px;color:#ece3e6;background:rgba(189,225,136,0.10);">{html.escape(ini)}</div>')


def avatar_html(size=56):
    p = get()
    if p['avatar']:
        return img_html(p['avatar'], size)
    return initials_html(p['name'], size) if p['name'] else ''


# ---------------- "Use my location" (a little JavaScript in the browser) ----------------
_LOC_JS = r"""
function locate(S) {
  if (!('geolocation' in navigator)) {
    S.status.textContent = 'This browser cannot share its location. Type your town or city instead.';
    return;
  }
  S.status.textContent = 'Asking your device for its position... (allow location if the browser asks)';
  navigator.geolocation.getCurrentPosition((p) => {
    const c = p.coords;
    S.status.textContent = `Found you (within ${Math.round(c.accuracy)} m).`;
    S.send('pick', { lat: c.latitude, lon: c.longitude, acc: c.accuracy, ts: Date.now() });
  }, (err) => {
    let why;
    if (err.code === 1) {
      why = 'Location permission was refused. Allow location for this page in the browser (and, on Windows, '
          + 'turn on Settings > Privacy & security > Location), then press "Use my location" again.';
    } else if (err.code === 3) {
      why = 'The device took too long to find you. Try again, or type your town or city.';
    } else {
      why = 'Your position is not available right now. Try again, or type your town or city.';
    }
    S.status.textContent = why;
  }, { enableHighAccuracy: true, timeout: 25000, maximumAge: 0 });
}

export default function (component) {
  const { parentElement, setTriggerValue } = component;
  let S = parentElement.__enoLocate;
  if (!S || !S.root.isConnected) {
    const root = document.createElement('div');
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'eno-loc-btn';
    btn.textContent = '\u{1F4CD} Use my location';
    const status = document.createElement('div');
    status.className = 'eno-loc-status';
    root.appendChild(btn);
    root.appendChild(status);
    parentElement.appendChild(root);
    S = { root, btn, status };
    btn.addEventListener('click', () => locate(S));
    parentElement.__enoLocate = S;
  }
  S.send = setTriggerValue;
}
"""

_LOC_CSS = """
.eno-loc-btn { width: 100%; min-height: 2.6rem; border-radius: 0.5rem; background-color: #26252c !important;
  color: #ece3e6 !important; border: 1px solid #879574 !important; font: inherit; cursor: pointer; padding: 0.4rem 0.8rem; }
.eno-loc-btn:hover { border-color: #bde188 !important; }
.eno-loc-status { color: #cfc8bd !important; font-size: 0.85rem; margin-top: 0.35rem; min-height: 0.2rem; }
"""

_locator = None
try:
    if hasattr(st, 'components') and hasattr(st.components, 'v2'):
        _locator = st.components.v2.component('enochian_home_locator', js=_LOC_JS, css=_LOC_CSS, isolate_styles=False)
except Exception:                      # an older Streamlit without st.components.v2: the button is not offered
    _locator = None


def _on_locate():
    v = st.session_state.get('pf_locate')
    p = v.get('pick') if hasattr(v, 'get') else None
    if not isinstance(p, dict):
        return
    try:
        lat, lon = float(p['lat']), float(p['lon'])
    except (KeyError, TypeError, ValueError):
        return
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        acc = p.get('acc')
        st.session_state[GPS] = dict(lat=round(lat, 4), lon=round(lon, 4),
                                     acc=float(acc) if isinstance(acc, (int, float)) else None)


def set_gps_for_test(lat, lon, acc=None):
    """Tests only: act as if the browser had reported this position."""
    st.session_state[GPS] = dict(lat=round(float(lat), 4), lon=round(float(lon), 4), acc=acc)


# ---------------- the profile window ----------------
def _start_edit():
    """Fresh state each time the window opens (a cancelled edit leaves nothing behind)."""
    st.session_state.pop(GPS, None)
    for k in ('pf_home_elev', 'pf_home_elev_for', 'pf_home_elev_src'):     # the elevation box starts afresh too
        st.session_state.pop(k, None)
    h = get().get('home') or {}
    if h.get('src') == 'gps':
        st.session_state[GPS] = dict(lat=h['lat'], lon=h['lon'], acc=None, saved=True)


def _date_inputs(prefix, default):
    c1, c2, c3 = st.columns([1.3, 1.4, 1])
    y = c1.number_input('Year', 1850, 2149, default.year, 1, key=prefix + '_y')
    m = c2.selectbox('Month', range(1, 13), index=default.month - 1, format_func=lambda k: calendar.month_abbr[k],
                     key=prefix + '_m')
    nd = calendar.monthrange(int(y), int(m))[1]
    if st.session_state.get(prefix + '_d', 1) > nd:
        st.session_state[prefix + '_d'] = nd
    d = c3.number_input('Day', 1, nd, min(default.day, nd), 1, key=prefix + '_d')
    return dt.date(int(y), int(m), int(d))


def edit_form():
    """The contents of the profile window (also callable without the window, for tests)."""
    p = get()
    b0 = p['birth'] or {}
    ss = st.session_state

    st.markdown('**Name and picture**')
    name = st.text_input('Your name', p['name'], max_chars=MAX_NAME, placeholder='e.g. Gerad', key='pf_name')
    up = st.file_uploader('Profile picture (JPG, PNG or WEBP)', type=['jpg', 'jpeg', 'png', 'webp'], key='pf_pic')
    new_av, err = None, None
    if up is not None:
        data = up.getvalue()
        if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
            err = f'That picture is larger than {MAX_UPLOAD_MB} MB. Please choose a smaller one.'
        else:
            try:
                new_av = to_avatar(data)
            except PictureTooLarge:
                err = (f'That picture has more than {MAX_PIXELS // 1_000_000} million pixels. '
                       'Please choose a smaller one.')
            except Exception:
                err = 'That file could not be read as a picture. Please try a JPG or PNG.'
    if err:
        st.error(err)
    remove = bool(p['avatar']) and new_av is None and st.checkbox('Remove my current picture', key='pf_rm')
    show = new_av if new_av is not None else (None if remove else p['avatar'])
    if show:
        st.markdown(img_html(show, 110), unsafe_allow_html=True)

    # ---- birth ----
    st.markdown('**Birth details** (for "My birth chart")')
    has_birth = st.checkbox('Add my birth date, time and place', value=bool(p['birth']), key='pf_has_birth')
    birth = None
    if has_birth:
        bdate = _date_inputs('pf', dt.date.fromisoformat(b0['date']) if b0 else dt.date(1990, 1, 1))
        unknown = st.checkbox('I do not know my birth time', value=not b0.get('time_known', True), key='pf_unknown')
        btime = dt.time(12, 0) if unknown else st.time_input(
            'Birth time (local clock)', dt.time.fromisoformat(b0['time']) if b0 else dt.time(12, 0), step=60,
            key='pf_time')
        if unknown:
            st.caption('Without the time, noon is used: the day, the Kings and the Part of the Earth are still '
                       'right, but the rising constellation and the part of the day may not be.')
        q = st.text_input('Birthplace (town or city)', b0.get('place', '').split(',')[0] if b0 else '',
                          key='pf_place', placeholder='e.g. London, Mortlake, Kraków')
        hits = places.search(q, n=10) if q else []
        if q and not hits:
            st.warning('No match in the gazetteer (places with at least 1,000 inhabitants). Try a nearby town.')
        if hits:
            same = [k for k, hh in enumerate(hits)
                    if b0 and abs(hh['lat'] - b0['lat']) < 1e-3 and abs(hh['lon'] - b0['lon']) < 1e-3]
            i = st.selectbox('Matches', range(len(hits)), index=same[0] if same else 0,
                             format_func=lambda k: places.label(hits[k]), key='pf_pick')
            h = hits[i]
            off, note = places.utc_offset_hours(h['tz'], dt.datetime.combine(bdate, btime))
            if st.checkbox(f'Override the UTC offset at birth (automatic: {off:+.2f} h)', key='pf_override'):
                off = st.number_input('UTC offset at birth (hours)', -12.0, 14.0, float(off), 0.25, key='pf_off')
            elif note:
                st.caption(note)
            birth = _valid_birth(dict(date=bdate.isoformat(), time=btime.strftime('%H:%M'), time_known=not unknown,
                                      place=f"{h['name']}, {h['country']}", lat=h['lat'], lon=h['lon'], tz=h['tz'],
                                      utc_offset=off))
            st.caption(f"{birth_text(birth)} · {h['lat']:.3f}°, {h['lon']:.3f}° · UTC{off:+.2f}")

    # ---- home ----
    st.markdown('**Where you live** (where the chart starts: "Now, where I live")')
    h0 = p.get('home') or {}
    gps = ss.get(GPS)
    if _locator is not None:
        _locator(key='pf_locate', on_pick_change=_on_locate, width='stretch', height='content')
    home, hh = None, None
    if gps:
        near, dkm = places.nearest(gps['lat'], gps['lon'])
        hh = dict(name=near['name'], country=near['country'], lat=gps['lat'], lon=gps['lon'], tz=near['tz'])
        how = 'Saved position' if gps.get('saved') else (
            'Your position' + (f" (within {gps['acc']:.0f} m)" if gps.get('acc') else ''))
        st.caption(f"{how}: {gps['lat']:.4f}°, {gps['lon']:.4f}°, {dkm:.1f} km from {near['name']}, "
                   f"{near['country']} (the town and time zone used).")
        st.button('Type a town or city instead', key='pf_gps_off', icon=':material/search:', width='stretch',
                  on_click=lambda: ss.pop(GPS, None))
    else:
        hq = st.text_input('Your town or city', h0.get('name', ''), key='pf_home',
                           placeholder='e.g. Mortlake, Kraków, Chicago')
        hhits = places.search(hq, n=10) if hq else []
        if hq and not hhits:
            st.warning('No match in the gazetteer (places with at least 1,000 inhabitants). Try a nearby town.')
        if hhits:
            same_h = [k for k, x in enumerate(hhits)
                      if h0 and abs(x['lat'] - h0['lat']) < 1e-3 and abs(x['lon'] - h0['lon']) < 1e-3]
            j = st.selectbox('Matches', range(len(hhits)), index=same_h[0] if same_h else 0,
                             format_func=lambda k: places.label(hhits[k]), key='pf_home_pick')
            hh = hhits[j]
    if hh:
        # ground height (user request, Nov 2026: 'like in the Sidereal Oracle'): the saved value for the same place,
        # else looked up for the exact spot (your device's position, or the town) from open elevation data. Older
        # profiles saved 0 m by default, so a saved 0 m is looked up again. Also re-seeded when Streamlit dropped the
        # box's own value (it forgets a widget's value while the window is closed).
        tol = 2e-4 if gps else 1e-3
        same_place = bool(h0) and abs(hh['lat'] - h0['lat']) < tol and abs(hh['lon'] - h0['lon']) < tol
        here_h = (round(hh['lat'], 4), round(hh['lon'], 4))
        if ss.get('pf_home_elev_for') != here_h or 'pf_home_elev' not in ss:
            ss['pf_home_elev_for'] = here_h
            saved = h0.get('elev') if same_place else None
            if saved is not None and (abs(float(saved)) < 0.5 or float(saved) < places.ELEV_MIN - 1):
                saved = None
            if saved is not None:
                v, src = float(saved), 'saved'
            else:
                v, src = places.lookup_elevation(hh['lat'], hh['lon'])
            ss['pf_home_elev'] = float(v or 0.0)
            ss['pf_home_elev_src'] = src or 'none'
        src = ss.get('pf_home_elev_src', 'none')
        elev = st.number_input('Ground elevation where you live (metres above sea level)', places.ELEV_MIN,
                               places.ELEV_MAX, step=1.0, format='%.0f', key='pf_home_elev',
                               help='Filled in by itself for the exact spot from open elevation data (AWS Terrain '
                                    'Tiles: SRTM, USGS 3DEP, GMTED2010 and others; Open-Meteo over water or when they '
                                    'cannot be reached). Type over it if you know better. The chart is worked out for '
                                    f'your eyes, {places.EYE_HEIGHT_M:g} m above the ground. It changes sunrise, and so '
                                    'the start of the Heptarchic day, slightly.')
        st.caption({'tiles': 'Ground height read for this spot from open elevation data (AWS Terrain Tiles).',
                    'open-meteo': 'Ground height read for this spot from a terrain map (Open-Meteo, Copernicus DEM).',
                    'saved': 'Ground height as saved in your profile.',
                    'none': 'The elevation data could not be reached, so this starts at 0 m. Type it in if you '
                            'know it.'}.get(src, '')
                   + f' Eye level used for the chart: {float(elev) + places.EYE_HEIGHT_M:.1f} m.')
        home = _valid_home(dict(name=hh['name'], country=hh['country'], lat=hh['lat'], lon=hh['lon'], tz=hh['tz'],
                                elev=elev, src='gps' if gps else 'town'))
        st.caption(f"{hh['name']}, {hh['country']} · {hh['lat']:.4f}°, {hh['lon']:.4f}° · ground {home['elev']:.0f} m · "
                   f"time zone {hh['tz']}")

    local = _local()
    if local:
        st.caption('Your profile is saved on this computer, in your user data folder '
                   '(%LOCALAPPDATA%\\SiderealEnochianChart\\profile), and never leaves it.')
    else:
        st.caption('Your profile is kept only while the app is open in this tab; nothing is stored on '
                   'the server.')
    c1, c2, c3 = st.columns(3)
    saved = c1.button('Save', type='primary', width='stretch', disabled=bool(err), key='pf_save')
    if saved:
        save(name, show, birth if has_birth else None, home)
    cancel = c2.button('Cancel', width='stretch', key='pf_cancel')
    wipe = c3.button('Delete my profile', width='stretch', key='pf_delete',
                     help='Removes your name, picture, birth details and home place'
                          + (' and deletes the profile folder on this computer.' if local else '.'))
    if wipe:
        delete()
    return saved or cancel or wipe


@st.dialog('Your profile', width='large')
def edit_dialog():
    if edit_form():
        st.rerun()


def sidebar_card():
    """Picture, name, birth and home, and the Edit button, at the top of the sidebar."""
    p = get()
    with st.sidebar:
        if p['name'] or p['avatar']:
            sub = ' · '.join(x for x in (birth_text(p['birth']) if p['birth'] else '',
                                         home_text(p['home']) if p['home'] else '') if x)
            st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin:2px 0 6px 0;">{avatar_html(56)}'
                        f'<div><div style="font-family:Georgia,serif;font-size:1.15rem;color:#e7fd9b;">'
                        f'{html.escape(p["name"]) or "&nbsp;"}</div>'
                        f'<div style="font-size:0.75rem;color:#cfc8bd;">{html.escape(sub)}</div></div></div>',
                        unsafe_allow_html=True)
            label = 'Edit profile'
        else:
            label = 'Create your profile'
        if st.button(label, key='profile_btn', icon=':material/account_circle:', width='stretch'):
            _start_edit()
            edit_dialog()
        st.divider()
