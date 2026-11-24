## How the ritual calendar works

The calendar shows **when** John Dee's Heptarchic workings fall at your place, timed with NASA JPL's DE440s
ephemeris (through Skyfield) and the IAU constellations. Its pages follow the Sky Gahshomar app: **Today**,
**Month**, **Year**, **Watches** (Sky Gahshomar's Gahs), **Workings** (its Prayers) and **Occasions** (its Festivals).
Change the date, time and place in the sidebar.

### 1. The Heptarchic day and its six watches
- Each weekday has a **King and Prince** (Peterson, *Five Books*, Book 4; De Heptarchia Mystica ch. 7). "The King
  and Prince govern for the hole day: the rest according to the six parts of the day" (Compendium Heptarchiae
  Mysticae; Peterson PDF p160).
- **When the day begins.** Dee was never told. The app's default is **local sunrise**: the Sun's upper edge on a
  horizon of -0.833° (refraction), lowered for your elevation. The elevation is the ground height of the spot,
  looked up from open elevation data (AWS Terrain Tiles; Open-Meteo over water or as a stand-by) or taken from your
  profile at home, plus 1.7 m for your eyes; it can be typed over. LMT midnight is an option in the sidebar. With no
  sunrise (polar day or night) the day falls back to LMT midnight, and this is flagged.
- **The six watches** are six equal parts of the time from sunrise to the next sunrise. Each watch has six of the
  42 ministers, in Dee's letters (one angel per letter) and James's seven-letter names (James App. A, PDF p194).
  Sunday also has Bobogel's whole-day six.
- A civil date shows the Heptarchic day whose sunrise falls on that date. Before sunrise, the Today page shows the
  previous day, which is still running.

### 2. Sidereal entries (ingresses)
- An **entry** is the moment a body passes into another IAU constellation (Delporte 1930 boundaries): the Sun,
  Moon, Mercury, Venus, Mars, Jupiter and Saturn. When the body enters one of the twelve zodiacal constellations,
  the calendar names that sign's **zodiac King** from Liber Scientiae (James App. A), with its tribe and face.
  Ophiuchus and non-zodiacal constellations such as Cetus have none.
- Times are found by sampling the JPL positions and then halving the interval to well under a second. Positions are
  **geocentric** apparent places, as in published almanacs, so the times are the same everywhere. Only the clock
  shown changes with your time zone.
- The boundaries are applied in their own frame, the mean equator and equinox of B1875.0. Checked on 17 Nov 2026
  against JPL Horizons' constellation (quantity 29) for 21 entries in 2026: the Sun's 13 entries agree to 22–26 s,
  Mercury, Venus and Mars to 14–32 s, and Saturn to 294 s (about 5 min; for its slow motion that is under 1″ of
  arc). The chart's constellations use the same lookup.
- The Chart page uses topocentric positions (seen from your place). Near a boundary, the Moon can therefore differ
  from the calendar by up to about two hours.

### 3. Moon phases and eclipses
- New Moon, first quarter, full Moon and last quarter come from Skyfield's almanac on DE440s.
- **Lunar eclipses** come from Skyfield's eclipse module (umbra and penumbra). The Year page says whether the Moon
  is above your horizon at greatest eclipse.
- **Solar eclipses** are found by the app. At each new Moon the least Sun–Moon separation is compared with the
  parallaxes and semi-diameters (the classical test in Meeus, *Astronomical Algorithms* ch. 54). Every solar
  eclipse from 2020 to 2030 (24) came out with the right date and type, including the hybrid of 20 Apr 2023. For
  your place the app checks whether the Sun is up and the two discs overlap.
- The sources give **no Heptarchic rule** for the Moon or eclipses. They are shown as timing markers only.

### 4. The workings and their texts
Each working links to Joseph H. Peterson's edition on **esotericarchives.com**, opening in a new tab: *De Heptarchia
Mystica* ch. 3–7, the *Compendium*, the *Liber exercitii Heptarchici* and the Holy Table. The app copies no ritual
text. Each working is tagged **sourced** (stated by Dee), **app rule** (the app's own timing) or **marker**.

**Source variance.** De Heptarchia Mystica ch. 7 heads Monday with King Carmara and Prince Hagonel, as well as
Blumaza and Bralges. The app keeps Peterson's identification of Carmara with Friday's Baligon. See *Sources and
certainty* on the About page.

### 5. Downloads
The **Occasions** page saves the year as an **.ics** calendar file (Outlook, Google Calendar, Apple Calendar) or as
a **.csv** table. Each occasion is a one-minute event at its exact JPL time.

### 6. Enochian script
The **Enochian script** switch at the top of the sidebar spells the screen in Dee's Enochian letters (his table of
6 May 1583), the same as in The Foul-Mouthed Oracle. The words stay English underneath. Digits, symbols and the
switch itself stay readable. Font: Oracle Enochian (CC BY-SA 4.0, drawings by Лорд Алекс, Wikimedia Commons).

Valid dates: 1850–2149, the range of DE440s.
