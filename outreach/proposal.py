"""Fill the Red Ocean proposal template for a lead who said yes.

Usage:  python3 proposal.py "Fortenberry Roofing Inc"   -> proposals/<name>.md
Prices in [brackets] are Tyler's to set before sending.
"""
import datetime, json, re, sys
from pathlib import Path
from templates import clean_name, group_for

PRICES = {
    "website_build": "$1,545",            # from the Continental Genetics proposal
    "hosting": "$20/mo",
    "ai_setup": "[$ AI setup]",
    "ai_monthly": "[$ AI monthly]",
    "ads_mgmt": "[$ ads management / mo]",
    "ads_budget": "[$ suggested ad budget / mo]",
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
### Websites · AI · Ads

## Proposal for {name}
Prepared {date}

Thank you for the opportunity to work with {name}. {why}

Below you'll find three options, from a new website on its own up to a full system that brings in
customers and answers them for you. Everything is built and managed by Red Ocean, so you can stay
focused on running {name} while we handle the rest.

## Option 1: Website
- Custom, mobile-friendly design that looks sharp on phones, tablets, and desktops
- Core pages: Home, About, Services, and Contact
- Contact form, plus click-to-call and click-to-text buttons
- Basic on-page SEO so people searching on the Coast can find you
- Google Business Profile check-up: website link, hours, photos, and categories
- Domain connection and full launch

## Option 2: Website + AI Assistant
Everything in Option 1, plus an AI assistant on your phone line, website, and texts:
{ai_scope}

## Option 3: Website + AI Assistant + Local Ads
Everything in Option 2, plus Facebook, Instagram, and Google ads aimed at customers in Biloxi,
D'Iberville, Ocean Springs, and Gulfport:
- Campaign setup, targeting, and ad creative (images and copy)
- Ads send people to your new site, where the AI assistant answers and books them
- Monthly report in plain English: what you spent, how many calls and leads it produced

## Investment

| Item | Type | Price |
|---|---|---|
| Website design & build | One-time | {website_build} |
| Hosting & maintenance | Monthly | {hosting} |
| AI assistant setup (Options 2 and 3) | One-time | {ai_setup} |
| AI assistant (Options 2 and 3) | Monthly | {ai_monthly} |
| Ads management (Option 3) | Monthly | {ads_mgmt} |
| Ad budget, paid directly to Meta/Google (Option 3) | Monthly | {ads_budget} suggested |

The monthly hosting covers secure hosting, an SSL certificate, software and security updates,
uptime monitoring, and small content edits as your business changes.

## Recent Work
- **Overstreet & Associates Engineering** (Biloxi): website
- **Fitness Depot** (gyms): AI customer response system and AI email assistant
- **White's Crossing Cattle Co.** (Wiggins): website
- **Wilco Land Management**: website
- **Rescued Child Clothing**: website
- **What Is Water?** (whatiswaterbook.com): book website with reader sign-ups

## Next Steps
1. Reply with the option you'd like, or any changes you want.
2. The one-time fees are due upfront before work begins.
3. We gather your content (logo, photos, services, prices) and set a start date.
4. Red Ocean builds everything and shares it with you for review.
5. After your approval, we launch, and the monthly plan begins.

We're excited to work with you. Call or text with any questions: 601-528-1659.

Tyler Eggers
Red Ocean
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
