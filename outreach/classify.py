"""Merge the Google Maps datasets, drop chains/closed places, and bucket each
business by website status."""
import json, re, collections, csv

CHAINS = re.compile(r"(firestone|goodyear|great clips|supercuts|sport clips|fantastic sams|"
    r"mcdonald|burger king|wendy|taco bell|subway|domino|pizza hut|papa john|popeyes|"
    r"chick-fil-a|sonic|waffle house|cracker barrel|applebee|olive garden|red lobster|"
    r"outback|chili's|ihop|denny|starbucks|dunkin|krispy|whataburger|zaxby|raising cane|"
    r"wingstop|buffalo wild|longhorn|texas roadhouse|o'reilly|autozone|advance auto|"
    r"jiffy lube|valvoline|take 5|midas|meineke|pep boys|monro|ntb|discount tire|big o|"
    r"mavis|tire kingdom|walmart|sam's club|target|ulta|sally beauty|regis|smartstyle|"
    r"cost cutters|massage envy|hand & stone|petsmart|petco|servpro|roto-rooter|"
    r"mr\. rooter|one hour|ars|rescue rooter|terminix|orkin|molly maid|merry maids|"
    r"chuck e|panda express|arby|kfc|hardee|jack in the box|five guys|dairy queen|"
    r"marco's|little caesars|hooters|ruth's chris|fuddruckers|shipley|tropical smoothie|"
    r"smoothie king|jersey mike|jimmy john|firehouse subs|mcalister|newk|"
    r"casino|hotel|inn & suites|hampton|holiday inn|beau rivage|hard rock|ip casino|"
    r"golden nugget|harrah|boomtown|treasure bay|palace casino|scarlet pearl|margaritaville|"
    r"aaa |u-haul|enterprise|hertz|state farm|allstate|h&r block|jackson hewitt)", re.I)

SOCIAL = {"facebook.com": "Facebook", "m.facebook.com": "Facebook", "fb.com": "Facebook",
          "instagram.com": "Instagram", "linktr.ee": "Linktree", "tiktok.com": "TikTok",
          "yelp.com": "Yelp"}
BOOKING = ("booksy.com", "vagaro.com", "squareup.com", "square.site", "toasttab.com",
           "styleseat.com", "schedulicity.com", "genbook.com", "glossgenius.com",
           "fresha.com", "clover.com", "order.online", "doordash.com", "ubereats.com",
           "grubhub.com", "menufy.com", "mysite.com", "setmore.com")

def host(url):
    h = re.sub(r"^https?://", "", url.strip().lower()).split("/")[0].split("?")[0]
    return h[4:] if h.startswith("www.") else h

rows = {}
for fn, area in (("raw/diberville.json", "D'Iberville"), ("raw/biloxi.json", "Biloxi")):
    for x in json.load(open(fn))["items"]:
        pid = x.get("placeId")
        if not pid or pid in rows:
            continue
        x["area"] = area
        rows[pid] = x

domain_count = collections.Counter(host(x["website"]) for x in rows.values() if x.get("website"))

out, dropped = [], collections.Counter()
for x in rows.values():
    name, web = x.get("title", ""), (x.get("website") or "").strip()
    city = x.get("city") or x["area"]
    if x.get("permanentlyClosed") or x.get("temporarilyClosed"):
        dropped["closed"] += 1; continue
    if city not in ("Biloxi", "D'Iberville", "D’Iberville", "Diberville"):
        dropped[f"outside:{city}"] += 1; continue
    if CHAINS.search(name) or CHAINS.search(web):
        dropped["chain"] += 1; continue
    h = host(web) if web else ""
    if web and h not in SOCIAL and not any(h.endswith(b) for b in BOOKING) and (domain_count[h] >= 3 or re.search(r"/(locations?|stores?|salons?)/", web, re.I)):
        dropped["multi-location"] += 1; continue
    if not web:
        bucket, platform = "NO_SITE", ""
    elif h in SOCIAL:
        bucket, platform = "SOCIAL", SOCIAL[h]
    elif h.endswith("business.site") or "sites.google.com" in web:
        bucket, platform = "DEAD_GOOGLE_SITE", "Google Business Site"
    elif any(h.endswith(b) for b in BOOKING):
        bucket, platform = "BOOKING_ONLY", h
    else:
        bucket, platform = "OWN_SITE", ""
    out.append(dict(placeId=x["placeId"], name=name, category=x.get("categoryName") or "",
        search=x.get("searchString") or "", city="D'Iberville" if "iberville" in city.lower() else city,
        street=x.get("street") or "", phone=x.get("phone") or "", website=web, host=h,
        score=x.get("totalScore") or "", reviews=x.get("reviewsCount") or 0,
        bucket=bucket, platform=platform))

json.dump(out, open("places_clean.json", "w"), indent=1)
print("kept", len(out), "| dropped", dict(dropped.most_common()))
print(collections.Counter((r["city"], r["bucket"]) for r in out).most_common())
