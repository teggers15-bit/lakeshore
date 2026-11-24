"""Final send list: council-reviewed plain-text emails (v3).

Rules from the council review:
- one checkable fact per email, re-verified before sending; drop anything that doesn't reproduce
- plain text, ~120 words, one line about Tyler, Jeff's quote, say what the mockup is, one ask
- no department inboxes (bids@, estimating@, accounting@, sales@): those businesses go to the call list
- day-4 follow-up adds homepage ideas, plain pricing, and the booking link

Inputs: send_queue.json + leads.csv (from merge.py), raw/psi2.json (re-run PageSpeed)
Outputs: final_queue.json, final_send_list.csv, final_dropped.csv
"""
import csv, json, re
from templates import clean_name, possessive, group_for, GROUPS, review_line

ADDRESS = "Red Ocean LLC · 1800 Woodland Drive, Wiggins, MS 39577"
PS = 'P.S. If this isn\'t something you need, just reply "no thanks" and I won\'t reach out again.'
SIG = "Tyler Eggers\nRed Ocean LLC\n601-528-1659\ngoredocean.com"
WHO = ("I'm Tyler Eggers. I run Red Ocean, a small web shop in Wiggins, about 35 minutes up the road. "
       "Jeff at White's Crossing Cattle in Wiggins put it this way: \"I had been putting off creating a "
       "website for far too long... Tyler made it super easy.\"")
DEPT = {"bids", "estimating", "accounting", "ptwaccounting", "sales"}

MOCKUP = {  # what the free mockup shows, by industry group
    "trades": "with your services, your reviews, and a tap-to-call button at the top",
    "appointments": "with your services, prices, and a book-now button at the top",
    "food": "with your menu, hours, and a tap-to-call button at the top",
    "retail": "with what you carry, your hours, and a tap-to-call button at the top",
    None: "with your services and a tap-to-call button at the top",
}
IDEAS = {
    "trades": ["A tap-to-call button with your number.", "Where you work and when you're open, so people know right away you're the right call.",
               "Photos of jobs you've actually done.", "A short \"request an estimate\" form."],
    "appointments": ["A \"Book now\" button that goes straight to your booking.", "Your services and prices, easy to read on a phone.",
                     "Photos of your work.", "A few of your best reviews."],
    "food": ["Your menu, readable on a phone (not a PDF).", "Your hours and a tap-to-call button.",
             "Photos of the food.", "Directions with a map."],
    "retail": ["What you carry, with photos.", "Your hours and directions.",
               "A tap-to-call button.", "A spot for new arrivals."],
    None: ["A tap-to-call button with your number.", "What you offer, in plain words.",
           "Photos of your work.", "A few of your best reviews."],
}


def group_key(category):
    g = group_for(category)
    return next((k for k, v in GROUPS.items() if v is g), None)


def norm(u):
    return re.sub(r"^https?://(www\.)?", "", re.sub(r"\?.*$", "", (u or "").lower())).rstrip("/")


def first_touch(lead, fact_kind, data):
    name = lead.get("display_name") or clean_name(lead["name"])
    gk = group_key(lead["category"])
    g = GROUPS.get(gk) or {"noun": "business", "look_for": "what you offer, your hours, and how to reach you"}
    city = lead["city"]
    search = (lead.get("search") or lead["category"]).lower()
    intro = f"I came across {name} on Google Maps"
    art = "an" if search[:1] in "aeiou" else "a"

    if fact_kind == "score":
        subject = f"{possessive(name)} website on a phone"
        fact = (f"{intro} and ran your website through Google's free mobile speed test (PageSpeed Insights) "
                f"this week. It scored {data} out of 100, which is in the range Google labels \"poor.\" In plain "
                f"terms, it's slow to load on a phone, and that's the version people see when they look you up from one.")
    elif fact_kind == "lcp":
        subject = f"{possessive(name)} website on a phone"
        secs = "over 10 seconds" if data >= 10 else f"about {int(data)} seconds"
        fact = (f"{intro} and ran your website through Google's free mobile speed test (PageSpeed Insights) "
                f"this week. In its simulated phone test, the main part of your homepage took {secs} to show up. "
                f"Real phones are often a bit faster than that test, but it's a sign the site is heavy on a phone, "
                f"and that's the version people see when they look you up from one.")
    elif fact_kind == "insecure":
        subject = f"{possessive(name)} website"
        fact = (f"{intro} and pulled up your website. Chrome shows a \"Not secure\" warning next to the address "
                f"because the site isn't using HTTPS, and a lot of people back out when they see that.")
    elif fact_kind == "nosite":
        subject = f"{name} on Google"
        opener = review_line(name, lead.get("score"), lead.get("reviews"))
        fact = (f"{opener} I noticed your listing "
                f"doesn't have a website linked. When people around {city} look up {art} {search} on their phone, a lot of "
                f"them tap \"Website\" to check {g['look_for']} before they call. If there isn't one, many just call "
                f"the next {g['noun']} on the list.")
    elif fact_kind == "social":
        subject = f"{name} on Google"
        platform = lead.get("platform") or "Facebook"
        if "booking" in platform.lower():
            tail = (f"That's great for booking, but a site of your own, with photos of your work and your reviews, is "
                    f"what helps you show up when someone in {city} searches \"{search} near me\" and hasn't found you yet.")
        else:
            tail = (f"That's a good start, but a real website with {g['look_for']} is what turns a lot of "
                    f"\"near me\" searches into calls.")
        fact = f"{intro}. I noticed the \"Website\" button on your listing goes to your {platform} page. {tail}"
    elif fact_kind == "dead":
        subject = f"{possessive(name)} website link"
        fact = (f"{intro}. When I tapped the \"Website\" button on your listing, it went to {data}, which doesn't "
                f"load anymore, so anyone who taps it right now hits a dead end.")
    else:
        raise ValueError(fact_kind)

    mock = (f"If it would help, I'll make you a free mockup: one image of a new {name} homepage laid out for "
            f"phones, {MOCKUP[gk]}. It's yours to keep either way.")
    body = (f"Hi,\n\n{fact}\n\n{WHO}\n\n{mock}\n\nWant me to put it together? Just reply \"yes.\"\n\n"
            f"{SIG}\n\n{PS}\n\n{ADDRESS}")
    return subject, body


def followup(lead, fact_kind):
    name = lead.get("display_name") or clean_name(lead["name"])
    gk = group_key(lead["category"])
    verb = "redoing" if fact_kind in ("score", "lcp", "insecure", "dead") else "building"
    ideas = "\n".join(f"{i}. {t}" for i, t in enumerate(IDEAS[gk], 1))
    return (f"Hi,\n\nFollowing up with a few ideas you can use whether or not we work together. If I were {verb} "
            f"{possessive(name)} homepage, here's what I'd put at the top, where a phone shows it first:\n\n{ideas}\n\n"
            f"That's what the free mockup would show. And so there's no mystery about what comes after: if you want "
            f"the full site, it's $2,000 up front plus $30 a month for care, or $0 down and $150 a month. You own the "
            f"site and the domain, it takes about two weeks, and there's a 14-day money-back guarantee. If you'd "
            f"rather not, the mockup is still yours.\n\nReply \"yes\" and I'll have it to you in a few days. Or if "
            f"you'd rather talk first, pick a time here: goredocean.com/book\n\nTyler\n601-528-1659\n\n{PS}\n\n{ADDRESS}")


if __name__ == "__main__":
    queue = json.load(open("send_queue.json"))
    leads = {r["placeId"]: r for r in csv.DictReader(open("leads.csv"))}
    overrides = json.load(open("manual_overrides.json")).get("by_name", {})
    psi2 = {norm(p["url"]): p for p in json.load(open("raw/psi2.json"))["items"]}
    searches = {p["placeId"]: p.get("search", "") for p in json.load(open("places_clean.json"))}

    final, dropped = [], []
    for q in queue:
        lead = {**leads[q["placeId"]], **{k: v for k, v in overrides.get(leads[q["placeId"]]["name"], {}).items()
                                          if k in ("display_name",)}}
        lead["search"] = searches.get(q["placeId"], "")
        local = q["to"].split("@")[0].lower()
        if local in DEPT:
            dropped.append((q["name"], q["to"], "department inbox: call the business instead")); continue
        kind, data, note = None, None, ""
        if q["angle"] == "A":
            kind = "nosite"
        elif q["angle"] == "SOCIAL":
            kind = "social"; lead["platform"] = re.search(r"goes to your (.+?) page", q["body"]).group(1)
        elif q["angle"] == "DEAD":
            kind, data = "dead", "gulfcoasthandymanservice.com"
        else:  # OUTDATED: must reproduce on the re-run
            a = psi2.get(norm(lead["website"]))
            s1 = float(lead["psi_score"]) if lead["psi_score"] else None
            l1 = float(lead["psi_lcp_s"]) if lead["psi_lcp_s"] else None
            s2 = a.get("performanceScore") if a else None
            l2 = (a.get("lcpMs") or 0) / 1000 if a and a.get("lcpMs") else None
            fin2 = (a or {}).get("finalUrl") or ""
            if fin2.startswith("http://") and (lead.get("final_url") or "").startswith("http://"):
                kind = "insecure"
            elif s1 is not None and s2 is not None and s1 < 50 and s2 < 50:
                kind, data = "score", int(s2)
            elif l1 and l2 and l1 >= 8 and l2 >= 8:
                kind, data = "lcp", min(l1, l2)
            note = f"run1 score={s1} lcp={l1}s | run2 score={s2} lcp={l2 and round(l2,1)}s final={fin2[:40]}"
            if not kind:
                dropped.append((q["name"], q["to"], "claim didn't reproduce on re-test: " + note)); continue
        subj, body = first_touch(lead, kind, data)
        final.append(dict(placeId=q["placeId"], name=q["name"], to=q["to"], subject=subj, body=body,
                          followup=followup(lead, kind), fact=kind, check=note, city=lead["city"],
                          category=lead["category"], phone=lead["phone"]))

    # interleave so each day's batch has a mix of angles and cities
    final.sort(key=lambda x: (x["fact"], x["city"], x["name"]))
    batches = [final[i::3] for i in range(3)]
    for b, items in enumerate(batches, 1):
        for x in items:
            x["batch"] = b
    final = [x for b in batches for x in b]
    json.dump(final, open("final_queue.json", "w"), indent=1, ensure_ascii=False)
    with open("final_send_list.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["batch", "name", "to", "fact", "subject", "check", "phone", "sent_at", "followup_sent_at", "reply"])
        for x in final:
            w.writerow([x["batch"], x["name"], x["to"], x["fact"], x["subject"], x["check"], x["phone"], "", "", ""])
    with open("final_dropped.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["name", "email", "why"]); w.writerows(dropped)
    from collections import Counter
    print("send:", len(final), dict(Counter(x["fact"] for x in final)), "batches:", [len(b) for b in batches])
    print("dropped:", len(dropped))
    for d in dropped: print("  -", d[0], "|", d[2][:110])
