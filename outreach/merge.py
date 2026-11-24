"""Combine Google Maps places + website contact scan + PageSpeed audits +
Google search snippets into one lead list and a rendered send queue.

Inputs (raw/):  contacts.json, psi.json, serp.json   (Apify dataset dumps)
                places_clean.json                    (from classify.py)
Outputs:        leads.csv          every business, with status + reason
                send_queue.json    only the emailable ones, subject/body rendered
                call_list.csv      good prospects with no email found (phone only)
"""
import csv, json, re
from templates import render, site_observation

FREE = ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com",
        "live.com", "msn.com", "att.net", "bellsouth.net", "comcast.net", "me.com", "ymail.com",
        "cableone.net", "sparklight.net", "protonmail.com")
JUNK_EMAIL = re.compile(r"(noreply|no-reply|donotreply|example|sentry|wix|squarespace|godaddy|"
                        r"privacy|abuse|webmaster|support@(yelp|facebook)|@(yelp|facebook|bbb|manta|"
                        r"yellowpages|mapquest|nextdoor|chamberofcommerce|bizapedia|opencorporates)\.|^www\.|^accessibility@|"
                        r"^press@|@linktr\.ee|@grubbio\.com|media\.com$|@birdeye|\.read$|^\d+@)", re.I)
SOCIAL_NAMES = {"Facebook": "Facebook", "Instagram": "Instagram", "Linktree": "Linktree", "Yelp": "Yelp"}


def load_items(path):
    try:
        d = json.load(open(path))
    except FileNotFoundError:
        return []
    return d["items"] if isinstance(d, dict) else d


def norm_url(u):
    u = (u or "").strip().lower()
    u = re.sub(r"\?.*$", "", u)
    u = re.sub(r"^https?://(www\.)?", "", u)
    return u.rstrip("/")


def domain_of(u):
    return norm_url(u).split("/")[0]


def tokens(s):
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if len(t) > 2 and t not in
            {"the", "and", "llc", "inc", "biloxi", "iberville", "salon", "shop", "services", "service"}}


def pick_email(emails, site_domain=""):
    """Prefer an address on the business's own domain, then a free mailbox."""
    clean = []
    for e in emails or []:
        e = e.strip().strip(".").lower()
        if not re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", e) or JUNK_EMAIL.search(e):
            continue
        if e not in clean:
            clean.append(e)
    if not clean:
        return "", ""
    for e in clean:
        if site_domain and e.split("@")[1].endswith(site_domain):
            return e, "own-domain"
    for e in clean:
        if e.split("@")[1] in FREE:
            return e, "free-mailbox"
    return clean[0], "other-domain (check it's theirs)"


places = json.load(open("places_clean.json"))
OVERRIDES = json.load(open("manual_overrides.json")).get("by_name", {})
contacts = {norm_url(c.get("websiteUrl")): c for c in load_items("raw/contacts.json")}
contacts_by_domain = {domain_of(c.get("websiteUrl")): c for c in load_items("raw/contacts.json")}
psi = {norm_url(p.get("url")): p for p in load_items("raw/psi.json")}
serp = {}
for s in load_items("raw/serp.json"):
    term = s.get("searchQuery.term") or (s.get("searchQuery") or {}).get("term")
    if term:
        serp[term] = s.get("organicResults") or []

leads, queue, calls = [], [], []
for p in places:
    web, bucket = p["website"], p["bucket"]
    rec = dict(p)
    rec.update(email="", email_source="", email_confidence="", angle="", observation="",
               status="", reason="", psi_score="", psi_lcp_s="", final_url="")

    # ---- find an email -------------------------------------------------
    if bucket in ("OWN_SITE", "BOOKING_ONLY") or (bucket == "SOCIAL" and "linktr" in web):
        c = contacts.get(norm_url(web)) or contacts_by_domain.get(domain_of(web))
        if c:
            rec["final_url"] = c.get("finalUrl") or ""
            e, conf = pick_email(c.get("emails"), domain_of(c.get("finalUrl") or web))
            if e:
                rec.update(email=e, email_source="business website", email_confidence=conf)
    if not rec["email"] and p.get("query"):
        name_toks = tokens(p["name"])
        need = len(name_toks) if len(name_toks) <= 2 else max(2, (len(name_toks) + 1) // 2)
        found = []
        for r in serp.get(p["query"], []):
            url = r.get("url") or ""
            # Only trust the business's own Facebook page (not groups/posts/search
            # pages) or a site whose domain looks like the business name.
            fb_page = re.match(r"https://(www\.|m\.)?facebook\.com/(p/)?[^/?]+/?(\?.*)?$", url) \
                and not re.search(r"facebook\.com/(groups|events|share|fb-answers|watch|reel|photo)", url)
            own_site = any(t in domain_of(url) for t in name_toks if len(t) > 3) and not re.search(
                r"yelp|facebook|instagram|birdeye|manta|bbb\.org|yellowpages|mapquest|familytreenow|"
                r"sos\.|\.gov|sunherald|localnews|chamber|nextdoor|angi|thumbtack|houzz", url)
            sos = "corp.sos.ms.gov" in url and "Business Email:" in (r.get("description") or "")
            if sos:
                m = re.search(r"Business Name:\s*(.+?)\.\s*State", r.get("description") or "")
                if m and len(name_toks & tokens(m.group(1))) >= need:
                    em = re.search(r"Business Email:\s*([^\s]+@[^\s]+?)\.?\s", (r.get("description") or "") + " ")
                    if em:
                        found = [em.group(1)]
                        rec["email_source"] = f"MS Secretary of State filing: {url[:70]}"
                        break
                continue
            if not (fb_page or own_site):
                continue
            title_toks = tokens(r.get("title", "") + " " + r.get("websiteTitle", ""))
            if not name_toks or len(name_toks & title_toks) < need:
                continue  # result isn't clearly about this business
            blob = f"{r.get('title','')} {r.get('description','')}"
            found += re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.(?:com|net|org|us|biz|co)\b", blob)
            if found:
                rec["email_source"] = f"Google result: {url[:90]}"
                break
        e, conf = pick_email(found)
        if e:
            rec.update(email=e, email_confidence=conf)
        else:
            rec["email_source"] = ""

    # ---- decide the angle ---------------------------------------------
    if bucket == "NO_SITE":
        rec["angle"] = "A"
    elif bucket == "SOCIAL":
        rec["angle"], rec["platform"] = "SOCIAL", p.get("platform") or "Facebook"
    elif bucket == "BOOKING_ONLY":
        brand = re.sub(r"\..*$", "", domain_of(web).split(".")[-2] if "." in domain_of(web) else web)
        brand = {"glossgenius": "GlossGenius", "booksy": "Booksy", "square": "Square",
                 "toasttab": "Toast"}.get(brand, brand.title())
        rec["angle"], rec["platform"] = "SOCIAL", f"{brand} booking"
    elif bucket == "DEAD_GOOGLE_SITE":
        rec["angle"] = "DEAD"
        rec["observation"] = ("The \"Website\" button on your Google listing points to a free Google "
                              "Business Profile site, and Google shut those down in 2024.")
    elif bucket == "OWN_SITE":
        a = psi.get(norm_url(web)) or psi.get(norm_url(re.sub(r"\?.*$", "", web)))
        c = contacts.get(norm_url(web)) or contacts_by_domain.get(domain_of(web))
        final = (a or {}).get("finalUrl") or (c or {}).get("finalUrl") or ""
        rec["final_url"] = final
        if a and a.get("performanceScore") is not None:
            rec["psi_score"] = a["performanceScore"]
            rec["psi_lcp_s"] = round((a.get("lcpMs") or 0) / 1000, 1)
        cat = ((c or {}).get("failureReason") or {}).get("category") or ""
        psi_err = (a or {}).get("error") or ""
        # Dead = the domain doesn't resolve, or nothing answers AND Google's test failed too.
        psi_dead = cat == "DOMAIN_NOT_FOUND" or (cat == "SITE_UNREACHABLE" and bool(psi_err))
        scan_dead = cat in ("DOMAIN_NOT_FOUND", "SITE_UNREACHABLE")
        if psi_dead and scan_dead:
            rec["angle"] = "DEAD"
            rec["observation"] = ("I tapped the \"Website\" button on your Google listing and the site "
                                  "wouldn't load for me.")
            rec["reason"] = f"site dead ({cat}); confirm by opening it before sending"
        else:
            obs = site_observation(a, final)
            if obs:
                rec["angle"], rec["observation"] = "OUTDATED", obs
            else:
                rec["status"], rec["reason"] = "skip", "website looks fine in our checks"

    # ---- hand-verified overrides ---------------------------------------
    ov = OVERRIDES.get(p["name"])
    if ov:
        rec.update(ov)

    # ---- final status ---------------------------------------------------
    if not rec["status"]:
        if rec["email"]:
            rec["status"] = "ready"
            subject, body = render({**rec, "score": p["score"], "reviews": p["reviews"]})
            queue.append(dict(placeId=p["placeId"], name=p["name"], to=rec["email"], subject=subject,
                              body=body, angle=rec["angle"], email_confidence=rec["email_confidence"],
                              email_source=rec["email_source"], note=rec["reason"]))
        else:
            rec["status"], rec["reason"] = "call", (rec["reason"] or "no public email found")
            calls.append(rec)
    leads.append(rec)

from collections import Counter as _C
serp_use = _C(r["email"] for r in leads if r["email"] and r["email_source"].startswith("Google"))
seen, deduped = set(), []
for q in queue:
    if q["email_source"].startswith("Google") and serp_use[q["to"]] > 1:
        continue
    if q["to"] in seen:
        continue
    seen.add(q["to"]); deduped.append(q)
dropped = {q["placeId"] for q in queue} - {q["placeId"] for q in deduped}
for r in leads:
    if r["placeId"] in dropped:
        r["status"], r["reason"] = "call", "email shared with another business or duplicate; not used"
queue = deduped

cols = ["status", "name", "category", "city", "street", "phone", "email", "email_confidence",
        "email_source", "angle", "observation", "website", "final_url", "psi_score", "psi_lcp_s",
        "score", "reviews", "reason", "placeId"]
for fn, rows in (("leads.csv", leads), ("call_list.csv", calls)):
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["status"], r["city"], r["category"], r["name"])):
            w.writerow(r)
json.dump(queue, open("send_queue.json", "w"), indent=1, ensure_ascii=False)

from collections import Counter
print("leads:", len(leads), dict(Counter(r["status"] for r in leads)))
print("ready by angle:", dict(Counter(q["angle"] for q in queue)))
print("ready by email confidence:", dict(Counter(q["email_confidence"] for q in queue)))
