"""Forecast: a written summary of the chart's angelic influences, with its strengths.

Weaknesses were removed from the readings at the user's request (Nov 2026): no rule of kind 'weakness' is applied
or shown, and those rules were taken out of forecast_rules.csv.

Sources: the correspondence tables (Peterson; James). The summary only restates them.
The strengths are APP INTERPRETIVE RULES: Dee gives no such judgements.
Each rule's wording is in forecast_rules.csv and can be edited or switched off there
(enabled = False). The conditions that trigger each rule are defined in this file.
"""
import pandas as pd

CLASSICAL = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
CANON = {'CADAAMP': 'CADDAMP', 'ARFAOLG': 'ARFALOG'}   # Book Four table vs James App. A spellings
CLEAR_KM = 500


def _canon(k):
    return CANON.get(str(k).upper(), str(k).upper()) if isinstance(k, str) else None


def _lc(s):
    return s[0].lower() + s[1:] if s else s


def _join(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def build(summary, tab, rules_csv='forecast_rules.csv', corr_csv='heptarchia_correspondences.csv'):
    rules = pd.read_csv(rules_csv, encoding='utf-8')
    rules = rules[rules['enabled'].astype(str).str.lower().isin(['true', '1', 'yes'])].set_index('rule_id')
    corr = pd.read_csv(corr_csv, encoding='utf-8').set_index('weekday')
    T = tab.set_index('body')
    out = {'strength': []}
    items = []                       # (kind, rule_id, values): lets the plain-English window re-tell each line

    def fire(rid, **kw):
        if rid in rules.index:
            kind = rules.loc[rid, 'kind']
            if kind != 'strength':           # weaknesses are not part of the readings (user request)
                return
            out[kind].append(rules.loc[rid, 'text'].format(**kw))
            items.append((kind, rid, kw))

    wd = summary['weekday']
    king, prince = summary['day_king'], summary['day_prince']
    realm = _lc(summary['day_realm'])
    planet = corr.loc[wd, 'planet_trad']
    pe = summary['part_of_the_earth']
    part = pe['parts'][0] if pe['parts'] else None
    place_king = _canon(part['zodiac_king']) if part else None

    # ---------- summary paragraph (restates the sourced tables) ----------
    m = summary['ministers']
    para = [f"The Heptarchic day is {wd}, governed by King {king} and Prince {prince}; "
            f"their realm is {realm}."]
    if m.get('part') and m['part'].get('names_dee_letters'):
        para.append(f"In part {summary['part_of_day']} of the six parts of the day the serving ministers are "
                    f"{m['part']['names_dee_letters']} (James's names: {m['part']['names_james_rotation']}).")
    if m.get('whole_day'):
        para.append(f"The whole day is also held by the six {m['whole_day']['names_dee_letters']}.")
    if part:
        para.append(f"The place lies under {part['angel']}, the Part of the Earth for {part['country']}, "
                    f"in the Aethyr {part['aire']} with {part['ministers']:,} ministers, under the zodiac King "
                    f"{part['zodiac_king']} ({part['sign']}), tribe of {part['tribe']}, facing {part['quarter']}.")
    asc = T.loc['Ascendant'] if 'Ascendant' in T.index else None
    if asc is not None:
        zk = asc.get('zodiac_king')
        para.append(f"The rising constellation is {asc['iau_constellation']}"
                    + (f", under the zodiac King {zk}." if isinstance(zk, str) else ", which has no zodiac King."))

    # ---------- rules ----------
    if 'FALLBACK' in str(summary.get('convention', '')):
        fire('no_sunrise')
    if planet in T.index:
        p = T.loc[planet]
        fire('day_planet_up' if p['above_horizon'] else 'day_planet_down', planet=planet, king=king, realm=realm)
        if not isinstance(p.get('zodiac_king'), str):
            fire('planet_ophiuchus' if p['iau_constellation'] == 'Ophiuchus' else 'day_planet_offzodiac',
                 planet=planet, body=planet, king=king, constellation=p['iau_constellation'])
        elif place_king and _canon(p['zodiac_king']) == place_king:
            fire('day_place_concord', planet=planet, zking=p['zodiac_king'])
    cl = T.loc[[b for b in CLASSICAL if b in T.index]]
    groups = cl[cl['zodiac_king'].apply(lambda x: isinstance(x, str))].groupby('zodiac_king')
    for zk, g in groups:
        if len(g) >= 3:
            fire('concentration', n=len(g), bodies=_join(g.index), zking=zk, sign=g['zodiac_sign'].iloc[0],
                 kings=_join(g['heptarchic_king']))
    for b, r in cl.iterrows():
        if b == planet or isinstance(r.get('zodiac_king'), str):
            continue
        if r['iau_constellation'] == 'Ophiuchus':
            fire('planet_ophiuchus', body=b)
        else:
            fire('planet_offzodiac', body=b, constellation=r['iau_constellation'], king=r['heptarchic_king'],
                 realm=_lc(r['realm']))
    if asc is not None and place_king and _canon(asc.get('zodiac_king')) == place_king:
        fire('rising_place_concord', constellation=asc['iau_constellation'], zking=asc['zodiac_king'])
    if part:
        d = pe.get('dist_km')
        fire('place_clear' if d is not None and d <= CLEAR_KM else 'place_approximate',
             dist=d, country=part['country'], angel=part['angel'], aire=part['aire'])
    else:
        fire('place_none')

    return dict(summary=' '.join(para), strengths=out['strength'], items=items,
                note='The summary restates the source tables. The strengths come from the app\'s '
                     'interpretive rules (forecast_rules.csv), not from Dee. For study and reflection, not prediction.')


def as_text(fc, header=''):
    lines = [header, '', 'FORECAST', '', fc['summary'], '', 'Strengths:']
    lines += [f'  + {s}' for s in fc['strengths']] or ['  (none)']
    lines += ['', fc['note']]
    return '\n'.join(lines).strip() + '\n'
