# Sidereal Chart · Enochian Reading · Ritual Calendar

A Streamlit app that draws an accurate **sidereal chart** and reads it through John Dee's **Heptarchic (Enochian)
system**, with a **ritual calendar** of the Heptarchic workings, modelled on the Sky Gahshomar app.

## What it does
- **Chart:** topocentric apparent positions of the Sun, Moon and planets from NASA JPL **DE440s** (via Skyfield),
  with the Ascendant and Midheaven, placed in the real **IAU constellations** (Delporte 1930 boundaries, applied in
  their mean B1875 frame). That gives 13 unequal signs including Ophiuchus, with no equal 30° signs and no ayanamsa.
- **Enochian reading:** the Heptarchic King and Prince of the day (from local sunrise by default; midnight optional),
  the 42 ministers in Dee's and James's naming, the Liber Scientiae zodiac Kings, the Part of the Earth of the
  place, a forecast and a plain-English "What does this mean?".
- **Ritual calendar** (pages Today, Month, Year, Watches, Workings, Occasions, How it works, About): the King and
  Prince of each day, the six watches with clock times and ministers, and the moments the Sun, Moon and planets
  enter each IAU constellation (with its zodiac King). It also gives Moon phases and solar and lunar eclipses
  (with local visibility), all timed with JPL DE440s. Each working links to Peterson's editions of Dee's texts on
  esotericarchives.com, and no ritual text is copied. A year can be saved as an **.ics** calendar file.
- **Enochian script:** a sidebar switch spells the screen in Dee's Enochian letters (the words stay English).
- Place search over about 170,000 GeoNames places, with automatic historical time zones, and an optional profile
  (kept for the browser session only on the web).

Dates run from **1850 to 2149**, the range of DE440s.

## Running it
- **Online:** Streamlit Community Cloud from this repository, main file `app.py`. On first start the app downloads
  `de440s.bsp` (about 32 MB) from NASA JPL into `ephem/`.
- **Locally:** see *Run locally* below (run from this folder: the working directory must be the app folder).
- **Windows desktop copy:** a separate release zip with `Start app.bat`, which sets up and starts the app in its own
  window; see its `READ ME FIRST.txt`.

## Run locally

Install the exact, checksum-verified versions the app was tested with (Python 3.12 or newer):

```
python -m venv .venv
.venv\Scripts\python -m pip install --require-hashes --only-binary ":all:" -r requirements.txt
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1
```

`requirements.in` lists the direct components; `requirements.txt` is the full lock with SHA-256
hashes (generated with `uv pip compile requirements.in --universal --python-version 3.12
--generate-hashes --only-binary :all:`). The same lock serves Streamlit Community Cloud.

## Accuracy checks (Nov 2026)
- Constellation entry times against JPL Horizons (21 entries in 2026): the Sun agrees within 22–26 s, Mercury,
  Venus and Mars within 14–32 s, and Saturn within 294 s (under 1″ of its slow motion).
- Solar eclipses 2020–2030: all 24 found with the right date and type.
- Heptarchic day and watch: in 250 random checks over 5 places, the calendar agrees with the chart's day rule.

## Sources, licences and credits
- Program code: MIT License, copyright (c) 2026 Gerad Smith (see `LICENSE`). The licence covers **only the app's
  own code and texts**.
- The correspondence tables (`*.csv`) are transcribed from J. Peterson (ed.), *John Dee's Five Books of Mystery*
  (2003) and G. James, *The Enochian Evocation of Dr John Dee*. Both are in copyright and are **not** covered by the
  MIT License. **Please keep this repository private.** The deployed app can still be shared from Streamlit's
  sharing settings.
- Enochian letters font `assets/fonts/OracleEnochian.ttf`: made from "Enochian - <letter>.svg" by Лорд Алекс
  (Wikimedia Commons), CC BY-SA 4.0, so the font is CC BY-SA 4.0 (see `assets/fonts/OracleEnochian-LICENSE.txt`).
- Planetary data: NASA JPL DE440s via Skyfield. Places: GeoNames (CC BY 4.0). Time zones: IANA tz database.
  Dee's texts are linked (not copied) from Joseph H. Peterson's esotericarchives.com.

## Security and privacy

- The Windows desktop copy of Sidereal Enochian Chart listens on this computer only (127.0.0.1). "Share on this network.bat" can open it to the local network, protected by a new password each time; only the person at the computer sees Quit and data-clearing controls.
- The desktop copy keeps its data and logs in `%LOCALAPPDATA%\SiderealEnochianChart`, checks its program files against `MANIFEST.sha256` at every start, and each release publishes SHA-256 checksums of its zips in `SHA256SUMS.txt`.
- All components are pinned to exact versions and installed with `--require-hashes`.
- The desktop-only code (`desktop.py`) does nothing on a hosted copy: no Quit button is shown there.
- The profile (name, picture, birth details, home place) is kept only for the browser session on a hosted copy; nothing is written to the server. The desktop copy saves it under `%LOCALAPPDATA%\SiderealEnochianChart\profile`, and only for the person at the computer: visitors over a shared network connection get a session-only profile.
- Text typed into the app (place labels, profile names) is HTML-escaped before it is shown; uploaded profile pictures are limited to 15 MB and 50 million pixels and are reduced to 256 x 256 pixels.
