"""Render the profile header SVGs with Tehran's temperature and the render time.

Usage: python tools/header.py <out-dir>
Run by .github/workflows/header.yml. GitHub delays scheduled runs by hours, so
the render time is drawn as "updated", never as a clock that looks current.
"""
import base64, json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone

# Iran dropped daylight saving in 2022, so Tehran is a fixed UTC+3:30
TZ = timezone(timedelta(hours=3, minutes=30))
WEATHER = ("https://api.open-meteo.com/v1/forecast?latitude=35.69&longitude=51.39"
           "&current=temperature_2m&timezone=Asia%2FTehran")

# 3x5 pixel font, like the u8g2 fonts on deskpal
FONT = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
    "A": ["010", "101", "111", "101", "101"], "B": ["110", "101", "110", "101", "110"],
    "C": ["111", "100", "100", "100", "111"], "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"],
    "G": ["111", "100", "101", "101", "111"], "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"], "J": ["001", "001", "001", "101", "111"],
    "K": ["101", "101", "110", "101", "101"], "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"], "N": ["110", "101", "101", "101", "101"],
    "O": ["111", "101", "101", "101", "111"], "P": ["111", "101", "111", "100", "100"],
    "R": ["110", "101", "110", "101", "101"], "S": ["111", "100", "111", "001", "111"],
    "T": ["111", "010", "010", "010", "010"], "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"], "W": ["101", "101", "111", "111", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    ":": ["0", "1", "0", "1", "0"], "-": ["000", "000", "111", "000", "000"],
    " ": ["0", "0", "0", "0", "0"], "o": ["11", "11", "00", "00", "00"],
}

# A2M33 "control room" palette (notes/design/tokens.css): green-grey panels,
# amber only for the live lamp. The OLED keeps its real black and blue-white.
THEMES = {
    "dark": dict(bg="#1b211e", border="#3d4741", text="#e2e6e0", muted="#9aa59d",
                 amber="#f0ab2a", board="#242b27", hole="#1b211e", pin="#9aa59d",
                 screen="#000000", px="#dbe9ff"),
    "light": dict(bg="#f4f5f2", border="#b9bfb7", text="#1d2420", muted="#56605a",
                  amber="#d99211", board="#e3e5e0", hole="#f4f5f2", pin="#56605a",
                  screen="#000000", px="#dbe9ff"),
}

# GitHub shows the header through <img>, which can't fetch fonts, so Barlow
# (subset to ASCII, OFL) is embedded as data URIs.
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")


def font_face(family, weight, name):
    with open(os.path.join(FONTS, name), "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return (f'@font-face {{ font-family: "{family}"; font-weight: {weight}; '
            f'src: url(data:font/woff2;base64,{data}) format("woff2"); }}')


# OLED is 128x64; drawn at 1.5x inside the screen rect
SX, SY, U = 628, 76, 1.5


def oled_rect(x, y, w, h, op=1.0, extra=""):
    o = "" if op >= 1 else f' opacity="{op}"'
    return f'<rect x="{SX + x * U:g}" y="{SY + y * U:g}" width="{w * U:g}" height="{h * U:g}"{o}{extra}/>'


def width(s, scale):
    return sum((len(FONT[ch][0]) + 1) * scale for ch in s) - scale


def text(s, x, y, scale):
    out = []
    for ch in s:
        glyph = FONT[ch]
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == "1":
                    out.append(oled_rect(x + c * scale, y + r * scale, scale, scale))
        x += (len(glyph[0]) + 1) * scale
    return out


def temperature():
    try:
        with urllib.request.urlopen(WEATHER, timeout=15) as r:
            return f"{round(json.load(r)['current']['temperature_2m'])}oC"
    except Exception:
        return "--oC"


def screen_pixels(now, temp):
    px = text("TEHRAN", 6, 4, 2)
    date = now.strftime("%a %d %b").upper()
    px += text(date, 122 - width(date, 1.5), 5, 1.5)
    px.append(oled_rect(6, 17, 116, 0.67, 0.35))
    px += text(temp, (128 - width(temp, 5)) // 2, 22, 5)
    updated = now.strftime("UPDATED %H:%M")
    px += text(updated, (128 - width(updated, 1.5)) / 2, 54, 1.5)
    return px


def svg(t, now, temp):
    T = THEMES[t]
    pins = "".join(
        f'<circle cx="{694 + i * 20}" cy="58" r="4" fill="{T["pin"]}"/>'
        f'<text x="{694 + i * 20}" y="48" text-anchor="middle">{lab}</text>'
        for i, lab in enumerate(["GND", "VCC", "SCL", "SDA"])
    )
    holes = "".join(
        f'<circle cx="{x}" cy="{y}" r="5" fill="{T["hole"]}" stroke="{T["border"]}"/>'
        for x, y in [(612, 52), (836, 52), (612, 196), (836, 196)]
    )
    label = f"Amin Mohammadi. Python, embedded and automation. Tehran, {temp.replace('o', '°')}, updated {now:%H:%M}."
    faces = font_face("Barlow", 400, "Barlow-Regular.woff2") + font_face("Barlow Tag", 600, "BarlowSemiCondensed-SemiBold.woff2")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240" role="img" aria-label="{label}">
  <style>
    {faces}
    .led {{ animation: led 2.4s ease-in-out infinite; }}
    @keyframes led {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{ .led {{ animation: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="899" height="239" rx="6" fill="{T["bg"]}" stroke="{T["border"]}"/>
  <text x="54" y="112" font-family="'Barlow Tag', Barlow, sans-serif" font-size="52" font-weight="600" fill="{T["text"]}">Amin Mohammadi</text>
  <g font-family="Barlow, sans-serif">
    <text x="56" y="146" font-size="20" fill="{T["muted"]}">Python, embedded and automation</text>
    <circle cx="62" cy="182" r="5" fill="{T["amber"]}"/>
    <text x="76" y="188" font-size="16" fill="{T["muted"]}">Tehran, Iran. I build tools that touch hardware.</text>
  </g>
  <rect x="600" y="36" width="248" height="172" rx="6" fill="{T["board"]}" stroke="{T["border"]}"/>
  {holes}
  <g font-family="'Barlow Tag', Barlow, sans-serif" font-size="9" fill="{T["muted"]}">{pins}</g>
  <circle class="led" cx="824" cy="58" r="3.5" fill="{T["amber"]}"/>
  <text x="812" y="61" font-family="'Barlow Tag', Barlow, sans-serif" font-size="9" fill="{T["muted"]}" text-anchor="end">PWR</text>
  <rect x="622" y="70" width="204" height="108" rx="3" fill="{T["screen"]}"/>
  <g fill="{T["px"]}">
    {"".join(screen_pixels(now, temp))}
  </g>
</svg>
'''


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = sys.argv[1]
    now = datetime.now(TZ)
    temp = temperature()
    os.makedirs(out, exist_ok=True)
    for t in THEMES:
        with open(os.path.join(out, f"header-{t}.svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg(t, now, temp))
    print(f"{now:%Y-%m-%d %H:%M} {temp}")


if __name__ == "__main__":
    main()
