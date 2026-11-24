"""Round 2: video email with open + video-click tracking (sent from tyler@goredocean.com via n8n).

Usage:
  python3 round2.py --video "https://www.loom.com/share/..." [--thumb "https://cdn.loom.com/...-with-play.gif"] \
                    [--exclude replied_or_optout.txt]
Writes round2_rows.json (rows for the n8n table "RO Outreach Round 2") and round2_preview.html.

Tracking (n8n workflow "Red Ocean – Outreach tracking"):
  open pixel  https://goredocean.app.n8n.cloud/webhook/ro-open?c=CODE
  video link  https://goredocean.app.n8n.cloud/webhook/ro-video?c=CODE  -> logs, alerts Tyler, redirects to the video
"""
import argparse, hashlib, html, json
from templates import clean_name, group_for, possessive

BASE = "https://goredocean.app.n8n.cloud/webhook"
NAVY = "#010F26"
ADDRESS = "Red Ocean LLC · 1800 Woodland Drive, Wiggins, MS 39577"
TEST_TO = "teggers15@gmail.com"


def code_for(key: str) -> str:
    return hashlib.sha1(("ro2:" + key).encode()).hexdigest()[:10]


def video_block(link: str, thumb: str | None) -> str:
    if thumb:  # a real thumbnail (Loom gives one with a play button built in)
        return (f'<a href="{link}" style="text-decoration:none"><img src="{thumb}" width="480" alt="Play the video" '
                f'style="display:block;width:100%;max-width:480px;height:auto;border:0;border-radius:10px"></a>')
    # image-free video card: still looks like a player when images are blocked
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:480px">'
            f'<tr><td align="center" bgcolor="{NAVY}" style="background:{NAVY};border-radius:10px;padding:34px 20px">'
            f'<a href="{link}" style="color:#ffffff;text-decoration:none;font-family:Helvetica,Arial,sans-serif">'
            f'<span style="display:inline-block;width:58px;height:58px;line-height:58px;border-radius:29px;background:#ffffff;'
            f'color:{NAVY};font-size:24px;text-align:center">&#9654;</span><br>'
            f'<span style="display:inline-block;margin-top:12px;font-size:16px;font-weight:bold">Watch the short video</span><br>'
            f'<span style="font-size:13px;color:#A9B8CE">From Tyler at Red Ocean</span></a></td></tr></table>')


def build(lead: dict, video: str, thumb: str | None, to: str | None = None) -> dict:
    name = lead.get("display_name") or clean_name(lead["name"])
    noun = group_for(lead.get("category", "")).get("noun", "business")
    code = code_for(lead.get("placeId") or lead["to"])
    link = f"{BASE}/ro-video?c={code}"
    pixel = f'<img src="{BASE}/ro-open?c={code}" width="1" height="1" alt="" style="display:block;width:1px;height:1px;border:0">'
    p = 'style="margin:0 0 16px"'
    e = html.escape
    body = f"""<div style="font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:1.6;color:#1F2937;max-width:520px">
<p {p}>Hi,</p>
<p {p}>I emailed last week about {e(possessive(name))} website. Instead of another long note, I recorded a short video that shows what I'd build for a local {e(noun)} like yours.</p>
<div style="margin:0 0 18px">{video_block(link, thumb)}</div>
<p {p}>If it's worth a look, just reply "yes" and I'll put together a free homepage mockup for {e(name)}. It's yours to keep either way.</p>
<p style="margin:0">Tyler Eggers<br>Red Ocean LLC<br><a href="tel:+16015281659" style="color:{NAVY};text-decoration:none">601-528-1659</a> · <a href="https://goredocean.com" style="color:{NAVY}">goredocean.com</a></p>
<p style="margin:22px 0 0;font-size:12px;color:#8A94A6">P.S. If this isn't something you need, just reply "no thanks" and I won't reach out again.<br>{e(ADDRESS)}</p>
{pixel}</div>"""
    return dict(code=code, business=name, email=to or lead["to"], subject=f"quick video for {name}",
                html=body, sent=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="the video's share link (Loom/YouTube)")
    ap.add_argument("--thumb", default=None, help="optional thumbnail image URL with a play button")
    ap.add_argument("--exclude", default=None, help="file of emails to skip (replied, opted out, bounced)")
    ap.add_argument("--per-batch", type=int, default=17)
    a = ap.parse_args()

    queue = json.load(open("final_queue.json"))
    skip = set()
    if a.exclude:
        skip = {l.strip().lower() for l in open(a.exclude) if l.strip()}
    leads = [q for q in queue if q["to"].lower() not in skip]

    rows = [{**build(leads[0], a.video, a.thumb, to=TEST_TO), "code": "test-tyler", "batch": 0}]
    rows[0]["html"] = rows[0]["html"].replace(code_for(leads[0].get("placeId") or leads[0]["to"]), "test-tyler")
    for i, lead in enumerate(leads):
        rows.append({**build(lead, a.video, a.thumb), "batch": i // a.per_batch + 1})
    json.dump(rows, open("round2_rows.json", "w"), indent=1, ensure_ascii=False)
    with open("round2_preview.html", "w") as f:
        f.write("<html><body style='background:#F1F4F8;padding:24px'>" + "".join(
            f"<div style='background:#fff;margin:0 auto 28px;max-width:600px;padding:24px;border-radius:12px'>"
            f"<div style='font:13px Helvetica;color:#6B7280;margin-bottom:12px'>To: {r['email']} · batch {r['batch']} · "
            f"Subject: {html.escape(r['subject'])}</div>{r['html']}</div>" for r in rows[:6]) + "</body></html>")
    from collections import Counter
    print(len(rows) - 1, "prospects +1 test row; batches:", dict(Counter(r["batch"] for r in rows)))
