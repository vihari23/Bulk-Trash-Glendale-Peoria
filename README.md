# Glendale & Aloravita Bulk Trash Calendars

An independent Apple Calendar subscription project. **No home addresses or personal booking confirmations** are published.

### Subscription links (after first successful GitHub Actions run)

- Both homes: https://raw.githubusercontent.com/vihari23/Bulk-Trash-Glendale-Peoria/main/site/home-bulk-trash.ics
- Glendale monthly collection weeks: https://raw.githubusercontent.com/vihari23/Bulk-Trash-Glendale-Peoria/main/site/glendale-bulk-trash.ics
- Aloravita / Peoria appointment reminders: https://raw.githubusercontent.com/vihari23/Bulk-Trash-Glendale-Peoria/main/site/aloravita-bulk-trash.ics

In Apple Calendar, choose **New Calendar Subscription**, paste one URL, select iCloud if offered and set Auto-refresh (e.g. daily). **Subscribe** rather than importing a downloaded ICS. Use combined OR individual feeds to avoid duplicates.

Optional information site: https://vihari23.github.io/Bulk-Trash-Glendale-Peoria/ (requires GitHub Pages → Source: GitHub Actions).

### Glendale

The city's official [2026 Section 4 pickup weeks](https://www.glendaleaz.gov/Community/City-Services/Trash-and-Recycling/Bulk-Trash) are included. Placement is permitted starting the Thursday before the pickup week and must be completed by **6:00 AM Monday**. The 8–9 AM events are display markers, **not the actual pickup hour or placement deadline**. **Confirm your Glendale home is Section 4 before relying on this feed.** Future years are shown only if city dates can be verified; otherwise use schedule-check reminders.

### Peoria / Aloravita

The [City of Peoria](https://www.peoriaaz.gov/bulktrash) uses appointment-only bulk trash pickup (up to two free pickups annually for eligible City solid-waste customers); there is **no recurring fixed pickup day**. This feed contains booking reminders only, not pickup appointments. Contact Peoria and wait for confirmation before setting items out. An optional local web form can export a one-time ICS for a **confirmed** appointment without publishing personal data.

### Publishing and privacy

A GitHub Actions workflow regenerates calendars at 8 AM Phoenix time daily, writes ICS files to `site/`, and optionally deploys a public Pages site when enabled. Failed source checks must not invent future pickup dates. Published ICS files are public: do not include home addresses, private appointment details, or secrets. Making this repository private will break raw.githubusercontent.com subscription URLs for Apple Calendar; GitHub Pages on private repos requires an eligible paid GitHub plan and may still be publicly viewable.
