import re
import unicodedata

"""Red Ocean cold-outreach email templates (D'Iberville / Biloxi campaign).

Plain-text on purpose: it reads like a personal note, and it lands in the
inbox more often than designed HTML email.

Each lead gets one of these angles:
  A        no website on the Google listing
  SOCIAL   the listing's "Website" button goes to Facebook/Instagram/etc.
  DEAD     the listing's website is dead (e.g. a shut-down Google business.site)
  OUTDATED the site loads but has a specific, checkable problem
"""

SENDER_NAME = "Tyler Eggers"
SENDER_PHONE = "601-528-1659"
# CAN-SPAM requires a valid physical postal address in every commercial email.
MAILING_ADDRESS = "1800 Woodland Drive, Wiggins, MS 39577"
WEBSITE = "goredocean.com"

# --- per-industry wording -------------------------------------------------

GROUPS = {
    "trades": {
        "proof": "WillCo Land and White's Crossing Cattle",
        "match": ["contractor", "roof", "plumb", "hvac", "air condition", "heating",
                  "landscap", "lawn", "pressure wash", "power wash", "clean",
                  "tow", "auto repair", "mechanic", "tire", "detail", "car wash",
                  "body shop", "electric", "paint", "fence", "remodel", "handyman",
                  "pest", "pool", "glass", "transmission", "oil change", "auto"],
        "noun": "company",
        "look_for": "photos of past work, reviews, and an easy way to get a quote",
        "ai": "an AI assistant that answers your calls and texts while you're on a job and books the estimate",
    },
    "appointments": {
        "proof": "Fitness Depot (we built their AI customer response system) and whatiswaterbook.com",
        "match": ["salon", "barber", "nail", "spa", "massage", "groom", "tattoo",
                  "pierc", "lash", "brow", "wax", "beauty", "hair", "esthetic"],
        "noun": "shop",
        "look_for": "your services, prices, and how to book",
        "ai": "an AI assistant that books appointments by text or phone 24/7, even when your hands are full",
    },
    "food": {
        "proof": "Rescued Child Clothing Co. and Fitness Depot (we built their AI customer response system)",
        "match": ["restaurant", "bakery", "cafe", "coffee", "grill", "bar", "food",
                  "pizza", "seafood", "bbq", "barbecue", "diner", "kitchen", "donut",
                  "taco", "mexican", "chinese", "sushi", "catering", "deli", "dessert",
                  "cake", "sandwich", "burger", "wings", "steak", "po' boy", "thai",
                  "vietnamese", "japanese", "italian", "american"],
        "noun": "place",
        "look_for": "your menu, hours, and photos of the food",
        "ai": "an AI assistant that answers the phone for hours, menu questions, and catering orders",
    },
    "retail": {
        "proof": "Rescued Child Clothing Co. and Fitness Depot (we built their AI customer response system)",
        "match": ["boutique", "store", "shop", "clothing", "gift", "jewel", "florist"],
        "noun": "shop",
        "look_for": "what you carry, your hours, and what's new",
        "ai": "an AI assistant that answers questions about hours, stock, and new arrivals by text, day or night",
    },
}

DEFAULT_GROUP = {
    "proof": "White's Crossing Cattle and Fitness Depot (we built their AI customer response system)",
    "noun": "business",
    "look_for": "what you offer, your hours, and how to reach you",
    "ai": "an AI assistant that answers calls and texts after hours and books appointments for you",
}


def group_for(category: str) -> dict:
    c = (category or "").lower()
    for name in ("appointments", "food", "trades", "retail"):
        if any(k in c for k in GROUPS[name]["match"]):
            return GROUPS[name]
    return DEFAULT_GROUP


def review_line(name: str, score, count) -> str:
    try:
        score, count = float(score or 0), int(count or 0)
    except (TypeError, ValueError):
        return f"I came across {name} on Google Maps."
    if count >= 15 and score >= 4.5:
        return (f"I came across {name} on Google Maps. {score:g} stars from {count} reviews "
                f"says a lot about how you treat people.")
    if count >= 8 and score >= 4.2:
        return f"I came across {name} on Google Maps and saw the great reviews."
    return f"I came across {name} on Google Maps."


def site_observation(psi: dict | None, final_url: str | None) -> str | None:
    """Build one honest, checkable sentence about a site's problems, or None
    if nothing measurable is wrong (then we don't pitch that business)."""
    parts = []
    insecure = bool(final_url and final_url.startswith("http://"))
    failed = set((psi or {}).get("failedAudits") or [])
    score = (psi or {}).get("performanceScore")
    lcp = (psi or {}).get("lcpMs")
    if score is not None and score <= 1:      # some tools report 0-1
        score = round(score * 100)
    if score is not None and score < 50:
        parts.append(f"I ran it through Google's free PageSpeed test and it scored {int(score)} out of "
                     f"100 on mobile, which Google rates as poor.")
    elif lcp and lcp >= 10000:
        parts.append("I ran it through Google's free PageSpeed test, and in its mobile test the main "
                     "content took over 10 seconds to show up. A lot of people back out after just a "
                     "few seconds.")
    elif lcp and lcp >= 8000:
        parts.append(f"I ran it through Google's free PageSpeed test, and in its mobile test the main "
                     f"content took about {int(lcp // 1000)} seconds to show up. A lot of people back out "
                     f"after just a few seconds.")
    if "viewport" in failed:
        parts.append("Google's test also flags it as not set up for phones, so it shows up "
                     "as a shrunk-down desktop page.")
    # NB: Lighthouse's "is-on-https" also fails for mixed content on HTTPS
    # pages, so only the final URL itself counts as "Not secure".
    if insecure:
        parts.append("Chrome also marks it \"Not secure\" because it isn't using HTTPS, and that "
                     "warning scares a lot of people off.")
    if not parts:
        return None
    # Smooth the "also" when the first point is the viewport/HTTPS one.
    parts[0] = parts[0].replace(" also ", " ", 1)
    return " ".join(parts)


def signature() -> str:
    return (
        f"Thanks,\n{SENDER_NAME}\nRed Ocean\n{SENDER_PHONE} · {WEBSITE}\n\n"
        f"P.S. If this isn't something you need, just reply \"no thanks\" and I won't reach out again.\n\n"
        f"Red Ocean LLC · {MAILING_ADDRESS}"
    )


OFFER = ("Would it help if I put together a free homepage mockup for {name}? "
         "No cost and no obligation. If you like it, we can talk from there.")

WHO = ("I'm Tyler with Red Ocean, here on the Coast. We do websites, AI tools, and Facebook and "
       "Instagram ads for small businesses like {proof}. For you, that could include {ai}.")
WHO_REBUILD = ("I'm Tyler with Red Ocean, here on the Coast. We do fast, mobile-friendly websites, AI tools, "
               "and Facebook and Instagram ads for small businesses like {proof}. For you, that could include {ai}.")


def clean_name(raw: str) -> str:
    """Turn a Google Maps title into how a person would write the name."""
    n = re.split(r"\s+[|/:–—-]\s+|:\s", raw)[0].strip()
    n = re.sub(r"[,\s]+(LLC|L\.L\.C\.?|Inc\.?|Incorporated|Co\.|Corp\.?)$", "", n, flags=re.I).strip(" ,.")
    n = unicodedata.normalize("NFKC", n)
    if n.isupper() and len(n) > 4:
        n = n.title().replace("'S ", "'s ")
    return n


def possessive(n: str) -> str:
    return n + ("'" if n.endswith("s") else "'s")


def parts(lead: dict) -> dict:
    """Every piece of one email, shared by the plain-text and HTML versions."""
    name = lead.get("display_name") or clean_name(lead["name"])
    g = group_for(lead.get("category", ""))
    city = lead.get("city") or "the area"
    search = (lead.get("search") or lead.get("category") or "business").lower()
    opener = review_line(name, lead.get("score"), lead.get("reviews"))
    angle = lead["angle"]
    p = dict(name=name, angle=angle, ai=g["ai"], proof=g["proof"], consequence="")

    if angle == "A":
        p["subject"] = f"{name} on Google"
        p["fact"] = "I noticed there's no website on your listing, though."
        p["fact_html"] = "There's no website linked on your Google listing."
        p["consequence"] = (f"When someone in {city} searches \"{search} near me,\" a lot of them tap "
                            f"\"Website\" to check {g['look_for']} before they call. If there isn't one, "
                            f"many just call the next {g['noun']} on the list.")
        p["badge"] = ("None", "", "Website on your listing", "#D93025")
    elif angle == "SOCIAL":
        p["subject"] = f"{name} on Google"
        platform = lead.get("platform", "Facebook")
        p["fact"] = f"I noticed the \"Website\" button on your listing goes to your {platform} page."
        p["fact_html"] = f"The \"Website\" button on your Google listing goes to your {platform} page."
        if "booking" in platform.lower():
            p["consequence"] = (f"That's great for booking, but a real website with photos of your work, your "
                                f"reviews, and your story is what helps you show up when someone in {city} "
                                f"searches \"{search} near me\" and hasn't found you yet.")
        else:
            p["consequence"] = (f"That's a good start, but when someone in {city} searches \"{search} near me,\" "
                                f"a real website with {g['look_for']} is what turns a lot of those searches into calls.")
        short = platform.replace(" booking", "")
        p["badge"] = (short, "", "Where “Website” goes", "#E37400")
    elif angle == "DEAD":
        p["subject"] = f"{possessive(name)} website link"
        p["fact"] = p["fact_html"] = lead["observation"]
        p["consequence"] = (f"So anyone who taps it right now hits a dead end, and a lot of them will just "
                            f"call the next {g['noun']} on the list.")
        p["badge"] = ("Offline", "", "Your website link", "#D93025")
    elif angle == "OUTDATED":
        p["subject"] = f"quick idea for {possessive(name)} website"
        opener = f"I came across {name} on Google Maps and pulled up your website."
        fact = lead["observation"]
        if "rates as poor" in fact and "back out" not in fact:
            fact += " Slow sites lose a lot of visitors before the page even finishes loading."
        p["fact"] = p["fact_html"] = fact
        score, lcp = lead.get("psi_score"), lead.get("psi_lcp_s")
        try:
            score = float(score) if score not in ("", None) else None
            lcp = float(lcp) if lcp not in ("", None) else None
        except ValueError:
            score = lcp = None
        if score is not None and score < 50:
            p["badge"] = (f"{int(score)}", "/100", "Google PageSpeed · mobile", "#D93025")
        elif lcp and lcp >= 8:
            p["badge"] = ("10+" if lcp >= 10 else f"{int(lcp)}", " sec", "Mobile load time", "#E37400")
        else:
            p["badge"] = ("⚠", "", "“Not secure” warning", "#D93025")
    else:
        raise ValueError(f"unknown angle {angle!r}")

    p["opener"] = opener
    rebuild = angle == "OUTDATED"
    p["who"] = (WHO_REBUILD if rebuild else WHO).format(ai=g["ai"], proof=g["proof"], noun=g["noun"])
    p["who_html"] = ("I'm Tyler with Red Ocean, here on the Coast. We do "
                     + ("fast, mobile-friendly websites" if rebuild else "websites")
                     + f", AI tools, and Facebook and Instagram ads for small businesses. "
                       f"For you, that could include {g['ai']}.")
    p["offer"] = (f"Would you be open to a free mockup of a refreshed homepage for {name}? No cost and no obligation."
                  if rebuild else OFFER.format(name=name))
    return p


def render(lead: dict) -> tuple[str, str]:
    """Plain-text version: (subject, body)."""
    p = parts(lead)
    middle = f"{p['fact']} {p['consequence']}".strip()
    body = f"Hi there,\n\n{p['opener']}\n\n{middle}\n\n{p['who']}\n\n{p['offer']}\n\n{signature()}"
    return p["subject"], body


if __name__ == "__main__":
    demo = [
        dict(name="Coastal Fades Barber Shop", category="Barber shop", city="D'Iberville",
             search="barber shop", score=4.8, reviews=112, angle="A"),
        dict(name="Gulf Breeze Roofing", category="Roofing contractor", city="Biloxi",
             search="roofing contractor", score=4.6, reviews=23, angle="OUTDATED",
             observation="It isn't set up for phones, so on a phone it shows up as a "
                         "shrunk-down desktop page that's hard to read and tap."),
    ]
    for d in demo:
        s, b = render(d)
        print("SUBJECT:", s, "\n", b, "\n", "=" * 70, sep="")


def render_followup(lead: dict) -> tuple[str, str]:
    """Short bump, sent as a reply in the same thread ~4 business days later,
    only to people who haven't answered or opted out."""
    name = lead.get("display_name") or clean_name(lead["name"])
    body = (
        "Hi there,\n\n"
        "Just bumping this up in case it got buried. The offer stands: I'll put together a free "
        f"homepage mockup for {name}, no strings attached. Just reply \"yes\" and I'll have it to "
        "you this week.\n\n"
        "If now's not a good time, no worries at all.\n\n"
        f"{signature()}"
    )
    return "", body   # empty subject = keep the original thread subject
