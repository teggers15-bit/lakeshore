"""Fill the Red Ocean proposal template for a lead who said yes.

Usage:  python3 proposal.py "Fortenberry Roofing Inc"   -> proposals/<name>.md
Prices in [brackets] are Tyler's to set before sending.
"""
import datetime, json, re, sys
from pathlib import Path
from templates import clean_name, group_for

PRICES = {   # website prices from goredocean.com/pricing and /start (Nov 24, 2026)
    "ai_setup": "[$ AI setup]",
    "ai_monthly": "[$ AI monthly]",
    "ads_mgmt": "[$ ads management / mo]",
    "ads_budget": "[$ / mo]",
}

AI_SCOPE = {
    "trades": ["Answers calls and texts when you're on a job or after hours",
               "Asks the right questions (address, type of job, photos) and books the estimate",
               "Sends you a text summary of every new lead"],
    "appointments": ["Books, moves, and confirms appointments by text or phone, 24/7",
                     "Answers common questions (prices, hours, services, parking)",
                     "Sends reminders to cut down on no-shows"],
    "food": ["Answers the phone for hours, directions, and menu questions",
             "Takes catering and large-order requests and sends them to you",
             "Handles the after-hours calls you'd otherwise miss"],
    "retail": ["Answers questions about hours, stock, and new arrivals by text or chat",
               "Captures customer phone numbers for promotions",
               "Handles after-hours questions"],
}
AI_DEFAULT = ["Answers calls and texts after hours", "Answers your most common questions",
              "Books appointments and sends you a summary of every new lead"]

TEMPLATE = """# RED OCEAN
### Websites · AI · Meta Ads · goredocean.com

## Proposal for {name}
Prepared {date}

Thank you for the opportunity to work with {name}. {why}

Below you'll find three options, from a new website on its own up to a full system that brings in
customers and answers them for you. Everything is built and managed by Red Ocean, so you can stay
focused on running {name} while we handle the rest.

## Option 1: Custom Website
- **Custom 5-page website**, designed around your work, not a template
- **Your domain name**, registered in your name for $100 a year, or we connect the one you have
- **Looks right on every phone**, where most of your customers will see it first
- **Local SEO setup**, so nearby searches actually find you
- **Contact form**: inquiries go straight to your phone and email
- **Google Business Profile integration**: reviews and map listing tied in
- **Hosting, SSL, and security**, handled so you never think about it
- **Admin dashboard**: edit your own text and photos any time, free

## Option 2: Website + AI Assistant
Everything in Option 1, plus an AI assistant on your phone line, website, and texts:
{ai_scope}

## Option 3: Website + AI Assistant + Meta Ads
Everything in Option 2, plus Facebook and Instagram ads aimed at customers in Biloxi, D'Iberville,
Ocean Springs, and Gulfport:
- Campaign setup, audience targeting, and ad creative (images and copy)
- Ads send people to your new site, where the AI assistant answers and books them
- A monthly report in plain English: what you spent, and how many calls and leads it produced

## Investment

**Website: pick how you'd like to pay**

| Plan | Due today | Monthly |
|---|---|---|
| Pay in Full | $2,000 once | + $30/mo care (Done With You) or $75/mo (Done For You) |
| Monthly Plan | $0 down | $150/mo (Done With You) or $300/mo (Done For You), starting the month after launch |

*Done With You:* you make your own edits any time through your admin dashboard. *Done For You:* we
make the changes for you. Both include fast, secure hosting with SSL, software and security updates,
and automatic backups. Monthly Plan: cancel anytime with 30 days' notice.

**Add-ons**

| Item | Type | Price |
|---|---|---|
| AI assistant setup (Options 2 and 3) | One-time | {ai_setup} |
| AI assistant (Options 2 and 3) | Monthly | {ai_monthly} |
| Meta ads management (Option 3) | Monthly | {ads_mgmt} |
| Ad budget, paid directly to Meta (Option 3) | Monthly | {ads_budget} suggested |

**Our promises**
- You see and approve the design before launch. We revise until it's right.
- 14-day money-back guarantee. No fine print.
- You own your website and your domain, free and clear. No lock-in, ever.

## Recent Work
- **White's Crossing Cattle** (wxcattle.com): custom website
- **WillCo Land LLC** (willcolandllc.com): custom website
- **Overstreet & Associates Engineering** (Biloxi): website
- **Fitness Depot** (gyms): AI customer response system and AI email assistant
- **Rescued Child Clothing Co.** (rescuedchildclothing.com): online apparel store
- **What Is Water?** (whatiswaterbook.com): book website with reader sign-ups

> "I had been putting off creating a website for far too long. I knew I needed one but had no idea
> where to begin. Tyler made it super easy. We were up and running in no time, and I have had lots
> of favorable feedback. I should have done this much sooner."
> **Jeff White, White's Crossing Cattle**

## Next Steps
1. Reply with the option and plan you'd like, or any changes you want.
2. Start your build at goredocean.com/start. We kick off within one business day.
3. We gather your content (logo, photos, services, prices) and design your site for your approval.
4. Most sites launch about two weeks after kickoff.

Questions? Call or text 601-528-1659, or email tyler@goredocean.com.

Tyler Eggers
Red Ocean · Wiggins, Mississippi
"""


def build(lead: dict) -> str:
    g = group_for(lead.get("category", ""))
    group_key = next((k for k, v in AI_SCOPE.items() if g.get("match") and
                      any(m in (lead.get("category") or "").lower() for m in g["match"])), None)
    scope = AI_SCOPE.get(group_key) if group_key else AI_DEFAULT
    name = lead.get("display_name") or clean_name(lead["name"])
    why = {
        "A": "Right now there's no website on your Google listing, so people who find you there "
             "have nowhere to go to see your work or reach you after hours.",
        "SOCIAL": "Right now your Google listing's \"Website\" button goes to a social or booking page "
                  "instead of a site of your own.",
        "DEAD": "Right now the website link on your Google listing doesn't load, so people who tap it "
                "hit a dead end.",
    }.get(lead.get("angle"), "")
    if lead.get("angle") == "OUTDATED" and lead.get("observation"):
        why = (lead["observation"].replace("I ran it through", "We ran your current site through")
               .replace("Chrome marks it", "Chrome marks your current site", 1)
               .replace("Chrome also marks it", "Chrome also marks it"))
    return TEMPLATE.format(name=name, date=datetime.date.today().strftime("%B %-d, %Y"), why=why,
                           ai_scope="\n".join(f"- {s}" for s in scope), **PRICES)


if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else None
    queue = json.load(open("send_queue.json"))
    leads = {r["placeId"]: r for r in __import__("csv").DictReader(open("leads.csv"))}
    for q in queue:
        if want and q["name"] != want:
            continue
        lead = {**leads[q["placeId"]], "angle": q["angle"]}
        out = Path("proposals") / (re.sub(r"[^A-Za-z0-9]+", "-", q["name"]).strip("-") + ".md")
        out.parent.mkdir(exist_ok=True)
        out.write_text(build(lead))
        print("wrote", out)
        if want:
            break
