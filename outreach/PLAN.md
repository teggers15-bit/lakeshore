# Red Ocean: D'Iberville & Biloxi outreach

## What was built (Nov 24, 2026)
- Pulled 620 Google Maps businesses (20 local categories x D'Iberville + Biloxi).
  Dropped chains, franchises, dealerships, and closed places, leaving **533**.
- Bucketed every business by website status:
  - no website on the listing: 206
  - "Website" button goes to Facebook/Instagram/Linktree or a booking app: 39
  - own website: 288. Checked each site with Google PageSpeed (mobile) and for HTTPS.
    182 looked fine and were skipped. The rest have a specific, checkable problem
    (poor mobile score, 10+ second mobile load, "Not secure", or a dead domain).
- Found emails on the business's own site, its own Facebook page, or its MS
  Secretary of State filing. Every search-sourced match was hand-checked; 14 wrong
  matches (same name, different state) were removed.

## Files
- `leads_ready.csv`: **62 businesses** with a verified email and a personalized email ready
- `send_queue.json`: the exact subject + body for each of those 62
- `call_list.csv`: 261 good prospects with no public email (phone numbers, best first)
- `leads.csv`: every business and why it was or wasn't included
- Google Drive copies: "Red Ocean – D'Iberville & Biloxi email leads (Nov 2026)"
  and "... call list (no email found)"

## Email angles
| Angle    | Hook |
|----------|------|
| A        | No website on your Google listing; people tap "Website" before they call |
| SOCIAL   | Your "Website" button goes to Facebook / a booking page |
| OUTDATED | Your Google PageSpeed mobile score / load time / "Not secure" |
| DEAD     | The website link on your listing doesn't load |

Every email: one specific observation, a short line about AI (receptionist, booking,
or after-hours answering, matched to the industry), and one soft ask: a free homepage mockup.
Plain text, no links, sent individually (never BCC), with an opt-out line and postal address (CAN-SPAM).

## Send plan (after approval)
1. Fill in the mailing address in `templates.py` (`MAILING_ADDRESS`), re-run `python3 merge.py`.
2. Skip Thanksgiving week. Start **Mon Nov 30 / Tue Dec 1**, around 9 to 10am CT.
3. 20 to 25 emails per day from Gmail (protects your sender reputation), so 62 takes 3 days.
4. Day 4 to 5 after each batch: one follow-up reply (`render_followup`) to anyone who hasn't
   answered. Never email again anyone who says no or doesn't reply to the follow-up.
5. Log each send in the `sent_at` column of the Drive sheet.

## Update: client proof, ads, proposals
- Each email names two past clients matched to the prospect's industry:
  - trades and contractors: Overstreet & Associates Engineering (Biloxi) + Wilco Land Management
  - salons, barbers, spas: Fitness Depot (AI customer response system) + Overstreet & Associates
  - food and retail: Rescued Child Clothing + Fitness Depot
- Every email now says we also run Facebook and Google ads.
- `proposal.py "<Business Name>"` writes a 3-option proposal (Website / + AI / + AI + Ads)
  to `proposals/`, using the same problem we pointed out in that business's email.
  Website pricing comes from the Continental Genetics proposal ($1,545 + $20/mo).
  AI and ads prices are left in [brackets] for Tyler to set.
