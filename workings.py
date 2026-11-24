"""The ceremonial workings of the ritual calendar and where to read them (the counterpart of Sky Gahshomar's
prayers.py).

Every text link opens Joseph H. Peterson's edition on esotericarchives.com (Twilit Grotto) in a new tab. The app
copies no ritual text: the short descriptions below are the app's own words. Peterson is also the editor of the
user's chosen source, John Dee's Five Books of Mystery. Links checked 17 Nov 2026 (all pages answered 200 and the
#chap anchors exist).

Each working carries a basis tag, as elsewhere in the app:
  sourced     - stated in Dee's text (page or chapter given)
  inferred    - read out of the source by the app or an editor
  app rule    - the app's own timing rule; Dee does not say this
  marker      - an astronomical moment shown for timing; the app's sources give no rule for it
"""
from html import escape

EA = 'https://www.esotericarchives.com/dee/'
LINKS = {
    'hm':      ('De Heptarchia Mystica (Dee, 1588)', EA + 'hm.htm'),
    'hm3':     ('HM ch. 3: the furniture and circumstances of the Exercise', EA + 'hm.htm#chap3'),
    'hm4':     ('HM ch. 4: how the Kings, Princes and Ministers appeared', EA + 'hm.htm#chap4'),
    'hm5':     ('HM ch. 5: the prayer to God for every day', EA + 'hm.htm#chap5'),
    'hm6':     ('HM ch. 6: the common invitation of the seven Kings', EA + 'hm.htm#chap6'),
    'hm7':     ('HM ch. 7: the offices of each King and Prince on their own day', EA + 'hm.htm#chap7'),
    'chm':     ('Compendium Heptarchiae Mysticae', EA + 'chm.htm'),
    'leh':     ('Liber exercitii Heptarchici (Ashmole 1790)', EA + 'hm1790.htm'),
    'holytab': ('The Holy Table and Lamen', EA + 'holytab.htm#holytab'),
    'mlq':     ('Five Books of Mystery (Sloane 3188): contents', EA + 'sl3188.htm'),
}

WORKINGS = {
    'preparation': dict(
        title='Preparation: the Holy Table, seals and ring',
        when='Before any Heptarchic working',
        about="Dee's notes on what must be ready, and in what order, before the Kings are called.",
        basis='sourced', cites='De Heptarchia Mystica ch. 3; Peterson, Five Books, Book 4',
        links=['hm3', 'holytab', 'leh']),
    'daily_prayer': dict(
        title='The prayer to God for every day',
        when='Every Heptarchic day. The chapter title says three times on each day; Dee names no hours',
        about="Dee's own prayer, said each day before the Kings are invited.",
        basis='sourced', cites="De Heptarchia Mystica ch. 5 (title 'Oratio, ad Deum, singulis diebus, tribus vicibus')",
        links=['hm5']),
    'king_day': dict(
        title='Invitation of the King and Prince of the day',
        when='The whole Heptarchic day, from local sunrise to the next sunrise (app default; midnight optional)',
        about=("The common invitation, with the name of the day's King put in, followed by that King's and "
               "Prince's own offices. 'The King and Prince govern for the hole day' (Compendium)."),
        basis='sourced', cites=('Peterson, Five Books, Book 4 (PDF pp157-164, notes 879-910); De Heptarchia Mystica '
                                'ch. 6-7; Compendium Heptarchiae Mysticae'),
        links=['hm6', 'hm7', 'chm']),
    'watch_ministers': dict(
        title='The ministers of the watch',
        when='Each of the six equal parts of the Heptarchic day',
        about=("'The rest according to the six parts of the day': six of the 42 ministers serve each part. The "
               "app shows Dee's letters and James's seven-letter names side by side."),
        basis='sourced', cites=("Compendium Heptarchiae Mysticae; Peterson PDF p160; Liber exercitii Heptarchici "
                                "('6 tymes 6 ... divyded into the parts of the day'); James App. A PDF p194"),
        links=['chm', 'leh']),
    'whole_day_six': dict(
        title="Sunday: Bobogel's whole-day six",
        when='Sunday only, the whole day',
        about=("The first six, with their King and the seal of their Prince, 'taketh place in the whole body of "
               "the day', to be used 'only on the Sabaoth day'."),
        basis='sourced', cites='Liber exercitii Heptarchici; Peterson PDF p156-157',
        links=['leh', 'mlq']),
    'ensign': dict(
        title='The Ensign of Creation of the day',
        when='With the King and Prince of the day',
        about=("Each King and Prince has an Ensign of Creation of its own. They are made of tin and set at the "
               "seven angles of the Holy Seal."),
        basis='sourced', cites='Peterson, Five Books (PDF p249, p259)',
        links=['holytab']),
    'zodiac_king': dict(
        title="The zodiac King of the Sun's constellation",
        when=("From the moment the Sun enters one of the twelve zodiacal IAU constellations until it leaves "
              "(JPL time). Ophiuchus has no King"),
        about=("Liber Scientiae gives one angelic King to each sign, with a tribe and a quarter of the earth. "
               "Timing these Kings by the Sun's sidereal constellation is the app's own rule."),
        basis='app rule', cites='James, Enochian Evocation App. A (PDF p196) and Book Four table (PDF pp123-133)',
        links=[]),
    'planet_ingress': dict(
        title='A planet comes under a zodiac King',
        when='The moment a classical planet enters a zodiacal IAU constellation (JPL time)',
        about=("The app gives a body in a zodiacal constellation that sign's King (the chart's rule). The calendar "
               "marks the moment this begins."),
        basis='app rule', cites='as for the zodiac Kings', links=[]),
    'part_of_earth': dict(
        title='The Part of the Earth of your place',
        when='Any day; it depends on the place, not the time',
        about="The governing angel of the chart location among Dee's 91 Parts of the Earth.",
        basis='sourced (place match approximate)', cites='James, Book Four (PDF pp122-133)', links=[]),
    'moon': dict(
        title='Moon phases and eclipses',
        when='New and full Moon, quarters, eclipses (JPL time)',
        about=("Shown as astronomical moments for planning. The app's sources (Peterson's Five Books, De "
               "Heptarchia Mystica, James) give no Heptarchic rule for them."),
        basis='marker', cites='-', links=[]),
}

# Dee's own handbook differs from the app's day table on one point (found 17 Nov 2026 while linking the texts).
VARIANCE = ("De Heptarchia Mystica ch. 7 heads MONDAYE with King CARMARA and Prince HAGONEL, followed by King "
            "BLVMAZA and Prince BRALGES (page left blank), and gives FRYDAYE to BALIGON and BAGENOL. This confirms "
            "Blumaza and Bralges for Monday directly; Peterson's Book 4 had them only by elimination. The app's "
            "table identifies Carmara with Baligon (Friday) and Hagonel with Bagenol, after Peterson. That "
            "identification is kept unchanged and this variance is recorded.")


def link_html(key: str) -> str:
    label, url = LINKS[key]
    return (f"<a class='rc-link' href='{escape(url)}' target='_blank' rel='noopener noreferrer'>"
            f"{escape(label)} ↗</a>")


def read_line(keys, label='Read') -> str:
    keys = [k for k in keys if k in LINKS]
    if not keys:
        return ''
    return f"<div class='rc-read'><b>{escape(label)}:</b> " + ' · '.join(link_html(k) for k in keys) + '</div>'


def card_html(key: str) -> str:
    w = WORKINGS[key]
    return (f"<div class='rc-work'><div class='rc-work-t'>{escape(w['title'])} "
            f"<span class='rc-tag rc-tag-{escape(w['basis'].split()[0])}'>{escape(w['basis'])}</span></div>"
            f"<div><b>When:</b> {escape(w['when'])}.</div><div>{escape(w['about'])}</div>"
            f"<div class='rc-src'>{escape(w['cites'])}</div>{read_line(w['links'])}</div>")
