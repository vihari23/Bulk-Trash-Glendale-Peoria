#!/usr/bin/env python3
"""Publish public Glendale section-4 collection dates and Peoria booking reminders."""
from __future__ import annotations
import argparse
import calendar
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
GLENDALE = "https://www.glendaleaz.gov/Community/City-Services/Trash-and-Recycling/Bulk-Trash"
PEORIA = "https://www.peoriaaz.gov/bulktrash"
TIMEZONE = "America/Phoenix"
MONTHS = {m.lower(): n for n, m in enumerate(calendar.month_name) if m}
DATE_RANGE = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s*[-–]\s*(?:(January|February|March|April|May|June|July|August|September|October|November|December)\s+)?(\d{1,2})\s*$", re.I)

class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens = []
        self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.hidden:
            self.hidden -= 1
    def handle_data(self, text):
        if not self.hidden and text.strip():
            self.tokens.append(" ".join(text.split()))

def parse_glendale_page(html, year, section=4):
    """Only accept a complete 12-month, Monday-Friday published section list."""
    p = PageText()
    p.feed(html)
    tokens = p.tokens
    if not re.search(r"\b"+str(year)+r"\s+Bulk Trash Schedule\b", " ".join(tokens), re.I):
        return []
    for i, token in enumerate(tokens):
        if not re.fullmatch(r"Section\s*"+str(section), token, re.I):
            continue
        dates = []
        for t in tokens[i+1:i+40]:
            if re.fullmatch(r"Section\s*[1-4]", t, re.I):
                break
            m = DATE_RANGE.fullmatch(t)
            if not m:
                continue
            a, b, c, d = m.groups()
            try:
                start = date(year, MONTHS[a.lower()], int(b))
                e_month = MONTHS[c.lower()] if c else start.month
                finish = date(year + int(e_month < start.month), e_month, int(d))
            except ValueError:
                continue
            if start.weekday() == 0 and finish.weekday() == 4 and (finish - start).days == 4:
                dates.append(start)
            if len(dates) == 12:
                break
        if len(dates) == 12 and len({x.month for x in dates}) == 12:
            return dates
    return []

def read_reviewed():
    d = json.loads((ROOT/"data/glendale-2026.json").read_text(encoding="utf8"))
    dates = [date.fromisoformat(x) for x in d["collection_mondays"]]
    if d["year"] != 2026 or d["section"] != 4 or len(dates) != 12 or len({x.month for x in dates}) != 12 or any(x.weekday() != 0 for x in dates):
        raise ValueError("Invalid Glendale verified-year data")
    return dates

def fetch_future(year):
    try:
        req = Request(GLENDALE, headers={"User-Agent": "ArizonaBulkTrashCalendar/1.0", "Accept":"text/html"})
        with urlopen(req, timeout=20) as response:
            raw = response.read(2000001)
        if len(raw) > 2000000:
            raise ValueError("Response too large")
        matches = parse_glendale_page(raw.decode("utf8","replace"), year)
        print(f"Official Glendale {year} section 4 found: {len(matches)} collection weeks")
        return matches
    except Exception as e:
        print(f"Official Glendale {year} check unavailable: {e}")
        return []

def esc(s):
    return str(s).replace("\\","\\\\").replace("\r\n","\n").replace("\r","\n").replace("\n","\\n").replace(",","\\,").replace(";","\\;")

def fold(line):
    parts, chunk, size = [], "", 0
    for character in line:
        octets = len(character.encode("utf8"))
        if size + octets > 75:
            parts.append(chunk)
            chunk, size = " " + character, octets + 1
        else:
            chunk, size = chunk + character, size + octets
    parts.append(chunk)
    return "\r\n".join(parts)

def event(uid, day, title, description, url, stamp, alert=None):
    ds = day.strftime("%Y%m%d")
    lines = ["BEGIN:VEVENT","UID:"+uid+"@arizona-bulk-trash",
             "DTSTAMP:"+stamp,"LAST-MODIFIED:"+stamp,
             "DTSTART;TZID=America/Phoenix:"+ds+"T080000",
             "DTEND;TZID=America/Phoenix:"+ds+"T090000",
             "SUMMARY:"+esc(title),"DESCRIPTION:"+esc(description),"URL:"+url,
             "STATUS:CONFIRMED","TRANSP:TRANSPARENT"]
    if alert:
        lines += ["BEGIN:VALARM","ACTION:DISPLAY","TRIGGER:"+alert,"DESCRIPTION:"+esc(title),"END:VALARM"]
    return lines + ["END:VEVENT"]

def serialize(name,events):
    if not events:
        raise ValueError("Empty subscribed calendar")
    lines = ["BEGIN:VCALENDAR","VERSION:2.0",
             "PRODID:-//Arizona Bulk Trash Calendars//EN",
             "METHOD:PUBLISH","CALSCALE:GREGORIAN",
             "X-WR-CALNAME:"+esc(name),"X-WR-TIMEZONE:America/Phoenix",
             "REFRESH-INTERVAL;VALUE=DURATION:P1D","X-PUBLISHED-TTL:PT24H",
             "BEGIN:VTIMEZONE","TZID:America/Phoenix",
             "BEGIN:STANDARD","DTSTART:19700101T000000",
             "TZOFFSETFROM:-0700","TZOFFSETTO:-0700","TZNAME:MST",
             "END:STANDARD","END:VTIMEZONE"]
    for x in events:
        lines += x
    return ("\r\n".join(fold(x) for x in lines + ["END:VCALENDAR"])+"\r\n").encode("utf8")

def generate(today, out, future=()):
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    upcoming=sorted(set(read_reviewed())|set(future))
    city=[]
    for monday in upcoming:
        if monday < today-timedelta(days=14):
            continue
        if monday.weekday() != 0:
            raise ValueError("Collection week must begin on Monday")
        thursday=monday-timedelta(days=4)
        friday=monday+timedelta(days=4)
        week=f"{monday.isoformat()} to {friday.isoformat()}"
        city.append(event("glendale-placement-"+monday.isoformat(),thursday,
            "Glendale bulk trash — placement opens (Section 4)",
            f"Section 4 collection week: {week}. Earliest placement is Thursday. All items must be out by 6:00 AM Monday, BEFORE the 8 AM calendar event. Confirm your street is Section 4. Official source: {GLENDALE}",
            GLENDALE,stamp,"-P1D")))
        city.append(event("glendale-collection-"+monday.isoformat(),monday,
            "Glendale bulk trash — collection week (Section 4)",
            f"Official section 4 collection week: {week}. Collection day and hour are not guaranteed. Placement deadline: 6 AM Monday (before this 8 AM display slot). Official source: {GLENDALE}",
            GLENDALE,stamp,"-P1D")))
    # If no future city weeks are known, publish informational monthly reminders,
    # never placeholders pretending to be actual pickups.
    if not any(monday >= today for monday in upcoming):
        for offset in range(4):
            v=today.year*12+today.month-1+offset
            y,m=divmod(v,12)
            d=date(y,m+1,15)
            city.append(event("glendale-schedule-check-"+d.isoformat(),d,
                "Glendale — check for published future bulk trash schedule",
                f"REMINDER ONLY — not a confirmed collection date. No official upcoming section 4 schedule is verified. Check: {GLENDALE}",
                GLENDALE,stamp,"-P1D")))
    peoria=[]
    for year in range(max(today.year,2027),max(today.year,2027)+4):
        for month in (1,7):
            day=date(year,month,15)
            if day < today-timedelta(days=45):
                continue
            peoria.append(event("aloravita-book-"+day.isoformat(),day,
                "Aloravita — consider booking Peoria bulk trash",
                f"BOOKING REMINDER ONLY — NOT A PICKUP DATE. Peoria provides appointment-only service to eligible city solid-waste customers. Up to two free bookings per calendar year. Verify home eligibility, request a pickup, and wait for confirmation. {PEORIA} | 623-773-7890",
                PEORIA,stamp,"-P7D"))
    names=[("glendale-bulk-trash.ics","Glendale Bulk Trash Section 4",city),
           ("aloravita-bulk-trash.ics","Aloravita Peoria Booking Reminders",peoria),
           ("home-bulk-trash.ics","Home Bulk Trash Glendale and Aloravita",city+peoria)]
    out.mkdir(parents=True, exist_ok=True)
    for filename,label,events in names:
        (out/filename).write_bytes(serialize(label,events))
        print(f"{filename}: {len(events)} events")
    return names

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--offline",action="store_true")
    p.add_argument("--date",type=date.fromisoformat,default=datetime.now().date())
    p.add_argument("--out",type=Path,default=ROOT/"site")
    args=p.parse_args()
    future=[] if args.offline else fetch_future(args.date.year+1)+fetch_future(args.date.year+2)
    generate(args.date,args.out,future)
