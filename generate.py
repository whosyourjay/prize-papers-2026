#!/usr/bin/env python3

import argparse
import calendar
import html
import re
import sys
import tomllib
from collections import defaultdict
from datetime import timedelta
from pathlib import Path


ROOT = Path(__file__).parent
DATA_PATH = ROOT / "talks.toml"
TEMPLATE_PATH = ROOT / "template.html"
OUTPUT_PATH = ROOT / "index.html"


def escape(value):
    return html.escape(str(value), quote=True)


def month_day(day, *, padded=False, full_month=False):
    month = calendar.month_name[day.month] if full_month else calendar.month_abbr[day.month]
    number = f"{day.day:02d}" if padded else str(day.day)
    return f"{month} {number}"


def date_range(first, last, *, include_year=True):
    if first.year != last.year:
        return (
            f"{month_day(first, full_month=True)}, {first.year} — "
            f"{month_day(last, full_month=True)}, {last.year}"
        )

    first_label = month_day(first, full_month=True)
    last_label = str(last.day) if first.month == last.month else month_day(last, full_month=True)
    result = f"{first_label} — {last_label}"
    return f"{result}, {first.year}" if include_year else result


def load_data():
    with DATA_PATH.open("rb") as source:
        data = tomllib.load(source)

    seminar = data["seminar"]
    talks = sorted(data["talks"], key=lambda talk: talk["date"])
    ids = [talk["id"] for talk in talks]
    dates = [talk["date"] for talk in talks]

    if len(ids) != len(set(ids)):
        raise ValueError("Talk IDs must be unique")
    if len(dates) != len(set(dates)):
        raise ValueError("Only one talk per calendar day is currently supported")
    if seminar["calendar_start"].weekday() != calendar.SUNDAY:
        raise ValueError("calendar_start must be a Sunday")
    if seminar["calendar_end"].weekday() != calendar.SATURDAY:
        raise ValueError("calendar_end must be a Saturday")
    if any(not seminar["calendar_start"] <= day <= seminar["calendar_end"] for day in dates):
        raise ValueError("Every talk must fall inside the calendar range")

    return seminar, talks


def calendar_label(day):
    is_sunday = day.weekday() == calendar.SUNDAY
    starts_month_block = is_sunday and day.day <= 7
    crosses_month = is_sunday and (day + timedelta(days=6)).month != day.month
    if day.day == 1 or starts_month_block or crosses_month:
        return month_day(day)
    return str(day.day)


def render_calendar(seminar, talks):
    first = seminar["calendar_start"]
    last = seminar["calendar_end"]
    talks_by_date = {talk["date"]: talk for talk in talks}
    days = [first + timedelta(days=offset) for offset in range((last - first).days + 1)]
    rows = []

    for week_start in range(0, len(days), 7):
        cells = []
        for day in days[week_start:week_start + 7]:
            talk = talks_by_date.get(day)
            label = escape(calendar_label(day))
            if talk is None:
                cells.append(f'                  <td><span class="date-number">{label}</span></td>')
                continue

            speaker = talk["speaker"]
            talk_time = talk.get("time", seminar["default_time"])
            if talk_time != seminar["default_time"]:
                speaker = f"{speaker} · {talk_time.split('–', 1)[0]}"
            cells.append(
                "\n".join(
                    [
                        '                  <td class="event-day">',
                        f'                    <span class="date-number">{label}</span>',
                        f'                    <a href="#talk-{escape(talk["id"])}">',
                        f'                      <strong>{escape(talk.get("short_title", talk["title"]))}</strong>',
                        f'                      <span>{escape(speaker)}</span>',
                        "                    </a>",
                        "                  </td>",
                    ]
                )
            )
        rows.append("                <tr>\n" + "\n".join(cells) + "\n                </tr>")

    title = date_range(first, last)
    aria = f"{month_day(first, full_month=True)} through {month_day(last, full_month=True)}, {last.year} seminar calendar"
    return "\n".join(
        [
            '        <div class="calendar-card">',
            f"          <h3>{escape(title)}</h3>",
            '          <div class="calendar-scroll">',
            f'            <table aria-label="{escape(aria)}">',
            "              <thead>",
            "                <tr>",
            *[f'                  <th scope="col">{name}</th>' for name in ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")],
            "                </tr>",
            "              </thead>",
            "              <tbody>",
            *rows,
            "              </tbody>",
            "            </table>",
            "          </div>",
            "        </div>",
        ]
    )


def datetime_value(talk, default_time):
    value = talk["date"].isoformat()
    talk_time = talk.get("time", default_time)
    if talk_time != default_time:
        start = re.split("[–-]", talk_time, maxsplit=1)[0]
        value += f"T{start}"
    return value


def render_sources(links):
    classes = "sources sources-three" if len(links) > 2 else "sources"
    lines = [f'          <div class="{classes}" aria-label="Reading links">']
    for link in links:
        label = escape(link["label"])
        if "url" in link:
            lines.append(f'            <a href="{escape(link["url"])}">{label}</a>')
        else:
            lines.append(f'            <span class="unavailable">{label} —</span>')
    lines.append("          </div>")
    return "\n".join(lines)


def render_talk(talk, seminar):
    talk_time = talk.get("time", seminar["default_time"])
    room = talk.get("room", seminar["default_room"])
    time_class = ' class="earlier"' if talk_time != seminar["default_time"] else ""
    return "\n".join(
        [
            f'        <article class="talk" id="talk-{escape(talk["id"])}">',
            f'          <time datetime="{escape(datetime_value(talk, seminar["default_time"]))}">',
            f"            <span>{calendar.day_abbr[talk['date'].weekday()]}</span>",
            f"            <strong>{month_day(talk['date'], padded=True)}</strong>",
            "          </time>",
            '          <div class="talk-details">',
            f"            <p>{escape(talk['speaker'])}</p>",
            f"            <h4>{escape(talk['title'])}</h4>",
            "          </div>",
            '          <div class="meeting">',
            f"            <span{time_class}>{escape(talk_time)}</span>",
            f"            <span>{escape(room)}</span>",
            "          </div>",
            render_sources(talk.get("links", [])),
            "        </article>",
        ]
    )


def render_schedule(seminar, talks):
    talks_by_month = defaultdict(list)
    for talk in talks:
        talks_by_month[(talk["date"].year, talk["date"].month)].append(talk)

    sections = []
    for (_, month), month_talks in talks_by_month.items():
        count = len(month_talks)
        noun = "talk" if count == 1 else "talks"
        sections.extend(
            [
                '      <div class="month">',
                f"        <h3>{calendar.month_name[month]}</h3>",
                f"        <span>{count} {noun}</span>",
                "      </div>",
                "",
                '      <div class="talk-list">',
                "\n\n".join(render_talk(talk, seminar) for talk in month_talks),
                "      </div>",
            ]
        )
    return "\n".join(sections)


def render_page():
    seminar, talks = load_data()
    template = TEMPLATE_PATH.read_text()
    replacements = {
        "{{SEMINAR_DATES}}": escape(
            date_range(talks[0]["date"], talks[-1]["date"], include_year=False)
        ),
        "{{DEFAULT_TIME}}": escape(seminar["default_time"]),
        "{{DEFAULT_ROOM}}": escape(seminar["default_room"]),
        "{{CALENDAR}}": render_calendar(seminar, talks),
        "{{SCHEDULE}}": render_schedule(seminar, talks),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    if "{{" in template or "}}" in template:
        raise ValueError("Unresolved template marker")
    return template


def main():
    parser = argparse.ArgumentParser(description="Generate index.html from talks.toml")
    parser.add_argument("--check", action="store_true", help="fail if index.html is out of date")
    args = parser.parse_args()

    rendered = render_page()
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text() != rendered:
            print("index.html is out of date; run python3 generate.py", file=sys.stderr)
            raise SystemExit(1)
        return

    OUTPUT_PATH.write_text(rendered)
    print(f"Wrote {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
