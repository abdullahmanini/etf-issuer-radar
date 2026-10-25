# ETF Issuer Radar

A ranked list of the fund companies that launched ETFs in the US and Canada between July 1 and October 23, 2026,
scored as partnership prospects for Blossom Social. Blossom is a Canadian social investing app that earns revenue
from advertising partnerships with asset managers. The list covers 382 sourced launches from 133 issuers, checks each
issuer against Blossom's publicly named partners, ranks the rest with adjustable weights, and copies out as CSV for
a CRM.

**Live site:** https://abdullahmanini.github.io/etf-issuer-radar/ · **Built by:** Abdullah Al Mneni, BTM, Toronto Metropolitan University

> **Independent prototype.** Made for an internship conversation with Blossom Social. It isn't affiliated with or
> endorsed by Blossom. It uses public web pages only and does not touch Blossom's app, data or systems. Partner
> status reflects only what Blossom has said in public.

## Why it exists

Fund issuers pay Blossom to put their products in front of its investors. An issuer that has just launched an ETF
needs its first buyers, so a list of recent launches is a list of warm prospects. The radar turns public launch news
into a sourced, ranked list a partnerships team could work through.

## Results at the default weights

- 382 launches from 133 issuers. 13 of those issuers are already named Blossom partners; 120 aren't.
- Top new prospects overall: First Trust (92), Direxion (81), XFUNDS (81), Harbor Capital (78), Amplify (77).
- Top in Canada: NEI Investments (67), Evolve (60), Mackenzie (55), CI Global (53).

The ranks move with the weights. They are a starting point for a sales conversation, not a forecast.

## How it works

1. **Collect.** Every ETF that started trading in the window, with ticker, issuer, date, category and the URL of the
   page that states it. Canadian rows come from issuer press releases, newswires and monthly roundups. US rows come
   from ETF Central's weekly launch recaps.
2. **Clean.** Issuer names are normalized to the brand ("Global X Canada" and "Global X" become one issuer). Unit
   classes of one fund (ZACU, ZACU.U, ZACU.F) count once. Share-class additions and mutual-fund conversions are left
   out because they aren't new funds.
3. **Match.** Issuers are checked against 19 partners Blossom names in public: the BlossomCon 2026 sponsor page, a
   Blossom team post listing clients, and the careers page. Partners are hidden by default and can be shown as upsell
   leads for their new funds.
4. **Score.** Each issuer gets four components between 0 and 1, combined as
   `score = 100 × Σ(weight × component) / Σ weight`:

   | Component | Definition | Default weight |
   |---|---|---|
   | Launch count | ln(1 + funds) / ln(1 + most funds by any issuer) | 35 |
   | Recency | 1 − (days since latest launch / days in window) | 20 |
   | Fit | Average fit of the issuer's funds by category (below) | 35 |
   | US push | 1 if the issuer launched in the US, else 0 | 10 |

   The page has sliders for all four weights.
5. **Pitch and export.** Each issuer gets a suggested pitch tied to a Blossom surface (Passive Income and Dividends
   topics, Learn lessons, Daily Buzz, New Listings Alert, BlossomCon), and the ranked list copies out as CSV.

### Fit by category

Blossom describes its members as long-term investors who want to "get rich slow", and its main topics are ETFs,
Passive Income, Dividends and Beginner Investors. Fit follows that:

| Category | Fit |
|---|---|
| income/covered-call, dividend | 1.00 |
| all-in-one | 0.90 |
| broad index | 0.85 |
| thematic | 0.70 |
| active equity | 0.60 |
| crypto | 0.55 |
| fixed income, other | 0.50 |
| buffer/defined-outcome | 0.45 |
| leveraged/single-stock | 0.15 |

## Limits

- Most US rows have a launch week, not a first trading day. The page shows them as "wk of" the week's Monday.
- The week of Oct 19 to 23 is missing for the US because its recap wasn't published at collection time. Late-October
  Canadian launches may also be incomplete.
- Each row rests on one source. Categories and fit values are my judgment.
- Blossom's real client list is longer than what it says in public, so some "new prospects" may already be clients.
- Launch data was gathered with AI-assisted web research. Sample rows were checked against their cited pages, but
  not every row was checked by hand.

## Repository

| Path | What it is |
|---|---|
| `data/launches.json` | The sourced launch list: one row per fund with its source URL, plus coverage notes |
| `scripts/build_site.py` | Normalizes issuers, applies the inclusion rules, tags partner status, builds `index.html` |
| `src/template.html` | The page: layout, scoring, filters and CSV export (vanilla HTML, CSS and JavaScript) |
| `index.html` | The built site served by GitHub Pages |

## Reproduce

Python 3.9+ standard library only.

```bash
python3 scripts/build_site.py
open index.html
```

## Built with

Python, HTML, CSS and JavaScript, with Google Fonts. Built with Claude Code.
