"""Build index.html from the sourced launch list.

Normalizes issuer names to their brand, drops funds that aren't new launches, derives a week date for rows that
only have a launch week, tags each issuer's partner status, and inlines the result into src/template.html.
Scoring happens in the page so the weights stay adjustable.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAXWELL_POST = "https://www.linkedin.com/feed/update/urn:li:activity:7487674434464444416/"
TIM_POST = "https://www.linkedin.com/feed/update/urn:li:share:7514408231171973120/"
CAREERS = "https://www.blossomsocial.com/careers"
BLOSSOMCON = "https://blossomcon2026.com/"

# Issuers Blossom has named publicly: BlossomCon 2026 sponsors first, then clients named in a team post, then the
# careers page's "all the Canadian Banks". Exchanges, brokers and dealers on those lists don't launch ETFs, so they
# appear in the partner chips but never match a launch.
PARTNERS = [
    ("Harvest ETFs", BLOSSOMCON), ("BMO", BLOSSOMCON), ("CIBC", BLOSSOMCON), ("Global X", BLOSSOMCON),
    ("Dynamic", BLOSSOMCON), ("Fidelity", BLOSSOMCON), ("Ninepoint", BLOSSOMCON), ("Brompton", BLOSSOMCON),
    ("TD", BLOSSOMCON), ("Hamilton ETFs", BLOSSOMCON), ("RBC", BLOSSOMCON), ("Red Cloud", BLOSSOMCON),
    ("State Street", TIM_POST), ("VanEck", TIM_POST), ("Moomoo", TIM_POST), ("NYSE", TIM_POST), ("Nasdaq", TIM_POST),
    ("Scotiabank", CAREERS), ("National Bank", CAREERS),
]
# Issuers whose funds appeared in the app's Featured ETFs module during one session on Oct 22, 2026
SEEN = ["Evolve", "Invesco"]

# Canonical issuer brand, matched by regex against the source's issuer field. First match wins.
ALIASES = [
    (r"\bharvest\b", "Harvest ETFs"), (r"\bhamilton\b", "Hamilton ETFs"), (r"\bbmo\b", "BMO"), (r"\bcibc\b", "CIBC"),
    (r"\bfidelity\b", "Fidelity"), (r"global ?x", "Global X"), (r"\bdynamic\b", "Dynamic"), (r"\bninepoint\b", "Ninepoint"),
    (r"^td\b|\btd asset|\btd global", "TD"), (r"\bbrompton\b", "Brompton"), (r"\brbc\b", "RBC"),
    (r"state street|\bspdr\b|\bssga\b", "State Street"), (r"\bvaneck\b", "VanEck"), (r"\bscotia", "Scotiabank"),
    (r"national bank|\bnbi\b", "National Bank"), (r"\bevolve\b", "Evolve"), (r"\binvesco\b", "Invesco"),
    (r"\bishares\b|\bblackrock\b", "iShares (BlackRock)"), (r"\bvanguard\b", "Vanguard"), (r"\bschwab\b", "Schwab"),
    (r"\bfranklin\b", "Franklin Templeton"), (r"\bj\.?p\.? ?morgan\b", "J.P. Morgan"), (r"\bfirst trust\b", "First Trust"),
    (r"\bproshares\b", "ProShares"), (r"\bdirexion\b", "Direxion"), (r"\broundhill\b", "Roundhill"), (r"\byieldmax\b", "YieldMax"),
    (r"\bdefiance\b", "Defiance"), (r"\btidal\b", "Tidal"), (r"\bamplify\b", "Amplify"), (r"\bgranite ?shares\b", "GraniteShares"),
    (r"\brex\b", "REX Shares"), (r"\bpurpose\b", "Purpose Investments"), (r"\bmackenzie\b", "Mackenzie"),
    (r"\bci\b|\bci global|\bci financial", "CI Global"), (r"\bmanulife\b", "Manulife"), (r"\bdimensional\b", "Dimensional"),
    (r"\bgoldman\b", "Goldman Sachs"), (r"\bpimco\b", "PIMCO"), (r"\bark\b", "ARK Invest"), (r"\bwisdomtree\b", "WisdomTree"),
    (r"\bkraneshares\b", "KraneShares"), (r"\bbitwise\b", "Bitwise"), (r"\bgrayscale\b", "Grayscale"), (r"\binnovator\b", "Innovator"),
    (r"\bneos\b", "NEOS"), (r"\bpacer\b", "Pacer"), (r"\bcalamos\b", "Calamos"), (r"\bjanus\b", "Janus Henderson"),
    (r"\bt\.? ?rowe\b", "T. Rowe Price"), (r"\bcapital group\b", "Capital Group"), (r"\bavantis\b", "Avantis"),
    (r"\bmorgan stanley\b|\beaton vance\b|\bparametric\b", "Morgan Stanley"), (r"\bbny\b", "BNY"),
    (r"\bdesjardins\b", "Desjardins"), (r"\baccelerate\b", "Accelerate"),
]
CATEGORIES = {"income/covered-call", "leveraged/single-stock", "crypto", "thematic", "active equity", "fixed income",
              "buffer/defined-outcome", "dividend", "broad index", "all-in-one", "other"}

# Share-class additions, mutual-fund conversions and reorganizations. They aren't new funds looking for their
# first buyers, so they don't count as launches.
NOT_NEW = {"BAGX", "BRSV", "BUSM", "RJCA", "ZINN", "ZDIS", "CTAG", "TIZE", "FFLX", "HWIV", "HWO", "HWGV", "HWMV", "DLCU",
           "DFGV", "SECA"}
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
WEEK_URL = re.compile(r"this-week-(?P<m1>[a-z]+)-(?P<d1>\d+)-(?:(?P<m2>[a-z]+)-)?(?P<d2>\d+)-(?P<y>\d{4})")


def week_end(url):
    """ETF Central recaps name their week in the URL; return that week's Friday as an ISO date."""
    m = WEEK_URL.search(url or "")
    if not m or (m["m2"] or m["m1"]) not in MONTHS:
        return None
    return f"{m['y']}-{MONTHS[m['m2'] or m['m1']]:02d}-{int(m['d2']):02d}"


def canon(raw):
    s = (raw or "").strip()
    for pat, name in ALIASES:
        if re.search(pat, s.lower()):
            return name
    return s or "Unknown issuer"


def main():
    src = json.loads((ROOT / "data" / "launches.json").read_text(encoding="utf-8"))
    launches, seen_keys, dropped, not_new = [], set(), 0, 0
    for row in src["launches"]:
        if not row.get("source_url") or not row.get("issuer"):
            dropped += 1
            continue
        market, ticker = row["market"], (row.get("ticker") or "").upper()
        if market == "US" and ticker in NOT_NEW:
            not_new += 1
            continue
        # One fund per base ticker: ZACU, ZACU.U and ZACU.F are unit classes of the same launch
        key = (market, (ticker or (row.get("name") or "").upper()).split(".")[0])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        launches.append({
            "ticker": row.get("ticker"), "name": row.get("name"), "issuer": canon(row["issuer"]),
            "issuer_raw": row["issuer"], "launch_date": row.get("launch_date"),
            "week_end": None if row.get("launch_date") else week_end(row["source_url"]), "exchange": row.get("exchange"),
            "category": row["category"] if row.get("category") in CATEGORIES else "other",
            "market": market, "source_url": row["source_url"],
        })

    partner_src = dict(PARTNERS)
    for l in launches:
        if l["issuer"] in partner_src:
            l["status"], l["status_source"] = "partner", partner_src[l["issuer"]]
        else:
            l["status"], l["status_source"] = ("seen" if l["issuer"] in SEEN else "new"), None

    notes = [f"{market}: {text}" for market, text in src["coverage_notes"].items()] + [
        "Most US rows come from ETF Central's weekly recaps, which give the launch week but not the first trading day. Those rows show \"wk of\" and the week's Monday. Recency counts from that week's Friday.",
        f"{len(NOT_NEW)} US share-class additions and mutual-fund conversions are left out because they aren't new funds.",
        "Canadian unit classes of one fund (for example ZACU, ZACU.U and ZACU.F) count as a single launch.",
        "Partner status comes only from the BlossomCon 2026 sponsor page, a Blossom team post and Blossom's careers page. Blossom's real client list is longer, so some \"new prospects\" may already be clients.",
        "\"Seen in app\" means the issuer's fund appeared in the Featured ETFs module during one session on Oct 22, 2026. Whether that placement is paid isn't public.",
        "Fit weights are my judgment, based on Blossom's public topics and its \"get rich slow\" positioning. The sliders let the team set their own.",
    ]
    if dropped:
        notes.append(f"{dropped} rows were dropped because they had no issuer or no source link.")

    data = {
        "collected": src["collected"], "window": src["window"], "launches": launches,
        "partners": [{"name": n, "source_url": s} for n, s in PARTNERS], "seen": [{"name": n} for n in SEEN], "notes": notes,
    }
    page = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    page = page.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (ROOT / "index.html").write_text('<!doctype html>\n<html lang="en">\n' + page + "</html>\n", encoding="utf-8")

    issuers = {l["issuer"] for l in launches}
    partners = {l["issuer"] for l in launches if l["status"] == "partner"}
    print(f"{len(launches)} launches from {len(issuers)} issuers ({len(partners)} current partners); "
          f"skipped {not_new} not-new, dropped {dropped}")


if __name__ == "__main__":
    main()
