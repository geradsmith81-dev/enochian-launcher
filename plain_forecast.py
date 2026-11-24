"""'What does this mean?': the Forecast retold in plain English (user request; modelled on the plain-English
window of the Sidereal Oracle app).

It restates the Forecast box without the technical terms, in five parts:
  1. In short: how many good signs the rules pick out;
  2. who is in charge today (the day's King and Prince, with their realm in everyday words);
  3. right now: which of the day's six parts this is, its clock times, and the ministering angels on duty;
  4. where you are: the Part of the Earth for the location;
  5. the good signs, line by line, in plain words.
Cautions (weaknesses) were removed from the readings at the user's request (Nov 2026).
The everyday wordings are app wording, kept in the 'plain' column of forecast_rules.csv and the 'realm_plain'
column of heptarchia_correspondences.csv, so they can be edited in Excel like the Forecast's own wording.
"""
import datetime as dt
from collections import defaultdict

import pandas as pd

DISCLAIMER = ('This reading applies fixed rules from Dee\'s angelic tables to the real sky. It is offered for '
              'reflection and study, as a structured prompt for thinking about the day, not as a prediction; '
              'there is no scientific evidence that it foretells events.')


def _fmt(template, values):
    return str(template).format_map(defaultdict(lambda: '…', values))


def _in_short(n_s):
    if n_s == 0:
        return 'None of the rules picked out anything special about this moment.'
    return (f"The rules pick out **{n_s} good {'sign' if n_s == 1 else 'signs'}** at this moment"
            + (': a good moment to lean into the day\'s theme.' if n_s >= 2 else '.'))


def part_window(summary, utc_dt, lon, tz_hours):
    """Local clock times (start, end) of the current part of the Heptarchic day."""
    if summary.get('day_start_utc') and summary.get('next_day_start_utc'):
        start = dt.datetime.fromisoformat(summary['day_start_utc'].replace('Z', '+00:00')).replace(tzinfo=None)
        end = dt.datetime.fromisoformat(summary['next_day_start_utc'].replace('Z', '+00:00')).replace(tzinfo=None)
    else:                                         # midnight convention: Local Mean Time midnight to midnight
        lmt = utc_dt + dt.timedelta(hours=lon / 15.0)
        start = dt.datetime.combine(lmt.date(), dt.time()) - dt.timedelta(hours=lon / 15.0)
        end = start + dt.timedelta(days=1)
    n = int(summary['part_of_day'])
    step = (end - start) / 6
    a, b = start + step * (n - 1), start + step * n
    shift = dt.timedelta(hours=tz_hours)
    return a + shift, b + shift, start + shift


def build(summary, fc, utc_dt, lon, tz_hours, rules_csv='forecast_rules.csv',
          corr_csv='heptarchia_correspondences.csv'):
    """Markdown sections of the plain-English reading."""
    rules = pd.read_csv(rules_csv, encoding='utf-8').set_index('rule_id')
    corr = pd.read_csv(corr_csv, encoding='utf-8').set_index('weekday')
    wd = summary['weekday']
    row = corr.loc[wd]
    goods = [_fmt(rules.loc[r, 'plain'], v) for k, r, v in fc.get('items', []) if k == 'strength' and r in rules.index]
    out = {}
    out['In short'] = _in_short(len(goods))

    a, b, day0 = part_window(summary, utc_dt, lon, tz_hours)
    start_word = 'sunrise' if summary.get('day_start_utc') else 'midnight'
    out['Who is in charge today'] = (
        f"In Dee's angelic week this is **{wd}**, counted from {start_word} ({day0:%H:%M} local time). "
        f"It is overseen by **King {summary['day_king']}** and his **Prince {summary['day_prince']}**, linked with "
        f"{'the ' if row['planet_trad'] in ('Sun', 'Moon') else ''}{row['planet_trad']}. In everyday words, their area is "
        f"**{row['realm_plain']}**.")

    m = summary['ministers']
    part = m.get('part') or {}
    txt = (f"The angelic day is split into six equal parts, and this is **part {summary['part_of_day']}**, "
           f"about **{a:%H:%M}–{b:%H:%M}** local time.")
    if part.get('names_dee_letters'):
        txt += (f" Seven ministering angels serve in this part. Dee wrote each one as a single letter: "
                f"**{part['names_dee_letters']}**; James reads them as the names {part['names_james_rotation']}.")
    else:
        txt += ' The source does not record the names of the ministering angels for this part.'
    if m.get('whole_day') and m['whole_day'].get('names_dee_letters'):
        txt += f" Six more, **{m['whole_day']['names_dee_letters']}**, stand by the King for the whole day."
    out['Right now'] = txt

    pe = summary['part_of_the_earth']
    if pe.get('parts'):
        p = pe['parts'][0]
        out['Where you are'] = (
            f"Dee divided the world known in his day into 91 regions, each with a guardian angel. This place falls "
            f"in **{p['country']}** (roughly {p['modern_identification']}), guarded by **{p['angel']}**, under the "
            f"sign-angel {p['zodiac_king']} ({p['sign']}). The match is made by distance to the region's approximate "
            f"centre, so treat it as a guide.")
    else:
        out['Where you are'] = ("Dee's 91 regions cover only the world known in his day; this place is outside "
                                "them, so no regional guardian applies.")
    out['The good signs'] = '\n'.join(f'- {x}' for x in goods) or '_None at this moment._'
    out['How to read this'] = DISCLAIMER
    return out


def as_text(sections):
    return '\n\n'.join(f'{k.upper()}\n{v}' for k, v in sections.items()).replace('**', '') + '\n'


def show(sections):
    """Render inside the Streamlit dialog."""
    import streamlit as st
    for k, v in sections.items():
        if k == 'How to read this':
            st.caption(v)
        else:
            st.markdown(f'**{k}**')
            st.markdown(v)
