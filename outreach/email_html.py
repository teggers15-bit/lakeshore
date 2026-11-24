"""Designed HTML version of each outreach email (Red Ocean brand: navy #010F26, Jost).

Table-based layout with inline styles so it renders the same in Gmail, Outlook,
Apple Mail and on phones. No images (they get blocked or flagged), two links
(reply button + website). The plain-text version is always sent alongside it.
"""
from html import escape
from urllib.parse import quote
from templates import parts, MAILING_ADDRESS, SENDER_NAME, SENDER_PHONE, WEBSITE

NAVY = "#010F26"
INK = "#1F2937"
MUTED = "#6B7280"
LINE = "#E3E8EF"
SOFT = "#F6F8FB"
PAGE = "#F1F4F8"
REPLY_TO = "teggers15@gmail.com"
SANS = "Helvetica,Arial,sans-serif"
BRAND = "Jost,Helvetica,Arial,sans-serif"
CLIENTS = ["White's Crossing Cattle", "WillCo Land", "Overstreet & Associates Engineering",
           "Fitness Depot", "Rescued Child Clothing Co."]


def _q(s: str) -> str:
    """Escape text, then turn straight quotes into curly ones for nicer type."""
    out, open_ = [], True
    for ch in escape(s, quote=False):
        if ch == '"':
            out.append("“" if open_ else "”"); open_ = not open_
        else:
            out.append(ch)
    return "".join(out).replace("'", "’")


def _p(text: str, style: str = "") -> str:
    return f'<p style="margin:0 0 18px;{style}">{_q(text)}</p>'


def _minify(h: str) -> str:
    return "\n".join(line.strip() for line in h.splitlines() if line.strip())


def render_html(lead: dict) -> str:
    p = parts(lead)
    value, sub, caption, color = p["badge"]
    big = "font-size:30px;" if len(value) <= 4 else "font-size:17px;"
    mailto = (f"mailto:{REPLY_TO}?subject=" + quote(f"Yes, free mockup for {p['name']}")
              + "&body=" + quote("Hi Tyler, yes, I'd like to see the free mockup.\n\n"))
    pre = _q(p["fact_html"])[:110]
    consequence = _p(p["consequence"]) if p["consequence"] else ""
    clients = " &nbsp;·&nbsp; ".join(_q(c) for c in CLIENTS)
    tel = "+1" + "".join(ch for ch in SENDER_PHONE if ch.isdigit())

    return _minify(f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light">
<title>{_q(p['subject'])}</title>
<style>@media only screen and (max-width:480px){{ .ro-tag{{display:none !important;}} .ro-pad{{padding-left:22px !important;padding-right:22px !important;}} }}</style>
</head>
<body style="margin:0;padding:0;background:{PAGE};-webkit-text-size-adjust:100%;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{PAGE};">{pre}&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{PAGE};">
<tr><td align="center" style="padding:28px 12px 36px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="max-width:580px;background:#FFFFFF;border:1px solid {LINE};border-radius:14px;">

  <tr><td style="background:{NAVY};padding:18px 30px;border-radius:13px 13px 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td style="vertical-align:middle;white-space:nowrap;">
        <span style="display:inline-block;width:32px;height:32px;line-height:32px;border-radius:8px;background:#FFFFFF;color:{NAVY};font-family:{BRAND};font-size:14px;font-weight:700;text-align:center;letter-spacing:-0.5px;vertical-align:middle;">RO</span>
        <span style="font-family:{BRAND};font-size:14px;font-weight:600;color:#FFFFFF;letter-spacing:3px;vertical-align:middle;padding-left:10px;">RED OCEAN</span>
      </td>
      <td class="ro-tag" align="right" style="vertical-align:middle;white-space:nowrap;font-family:{SANS};font-size:12px;color:#A9B8CE;letter-spacing:0.4px;">Websites &nbsp;·&nbsp; AI &nbsp;·&nbsp; Meta Ads</td>
    </tr></table>
  </td></tr>

  <tr><td class="ro-pad" style="padding:32px 30px 6px;font-family:{SANS};font-size:16px;line-height:1.65;color:{INK};">
    {_p("Hi there,")}
    {_p(p["opener"], "margin-bottom:22px;")}

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background:{SOFT};border:1px solid {LINE};border-left:4px solid {color};border-radius:10px;margin:0 0 22px;">
      <tr>
        <td width="108" align="center" style="padding:18px 6px 18px 14px;vertical-align:middle;">
          <div style="font-family:{BRAND};{big}font-weight:700;line-height:1.1;color:{color};white-space:nowrap;">{_q(value)}<span style="font-size:13px;font-weight:600;color:{MUTED};">{_q(sub)}</span></div>
          <div style="font-family:{SANS};font-size:10px;font-weight:700;line-height:1.35;color:{MUTED};text-transform:uppercase;letter-spacing:0.9px;margin-top:7px;">{_q(caption)}</div>
        </td>
        <td style="padding:18px 20px 18px 10px;vertical-align:middle;font-family:{SANS};font-size:15px;line-height:1.55;color:{INK};">{_q(p["fact_html"])}</td>
      </tr>
    </table>

    {consequence}
    {_p(p["who_html"])}

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="border-top:1px solid {LINE};border-bottom:1px solid {LINE};margin:2px 0 24px;">
      <tr><td style="padding:13px 0;font-family:{SANS};font-size:12.5px;line-height:1.7;color:{MUTED};">
        <span style="font-weight:700;color:{NAVY};text-transform:uppercase;letter-spacing:1.4px;font-size:11px;">Recent work</span>&nbsp;&nbsp; {clients}
      </td></tr>
    </table>

    {_p(p["offer"], "margin-bottom:22px;")}

    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 10px;"><tr>
      <td style="background:{NAVY};border-radius:8px;">
        <a href="{mailto}" style="display:inline-block;padding:14px 26px;font-family:{SANS};font-size:15px;font-weight:600;color:#FFFFFF;text-decoration:none;border-radius:8px;">Yes, send my free mockup &rarr;</a>
      </td>
    </tr></table>
    <p style="margin:0 0 30px;font-size:13px;color:{MUTED};">Or just hit reply. It comes straight to me.</p>

    <p style="margin:0 0 4px;">Thanks,</p>
    <p style="margin:0;font-family:{BRAND};font-size:17px;font-weight:600;color:{NAVY};">{_q(SENDER_NAME)}</p>
    <p style="margin:0;font-size:14px;color:{MUTED};">Founder, Red Ocean &nbsp;·&nbsp; Wiggins, Mississippi</p>
    <p style="margin:2px 0 28px;font-size:14px;"><a href="tel:{tel}" style="color:{NAVY};text-decoration:none;">{SENDER_PHONE}</a> &nbsp;·&nbsp; <a href="https://{WEBSITE}" style="color:{NAVY};text-decoration:underline;">{WEBSITE}</a></p>
  </td></tr>

  <tr><td style="padding:20px 30px 26px;border-top:1px solid {LINE};font-family:{SANS};font-size:12px;line-height:1.6;color:#8A94A6;">
    <p style="margin:0 0 6px;">P.S. If this isn’t something you need, just reply “no thanks” and I won’t reach out again.</p>
    <p style="margin:0;">Red Ocean LLC &nbsp;·&nbsp; {_q(MAILING_ADDRESS)}</p>
  </td></tr>

</table>
</td></tr></table>
</body></html>""")
