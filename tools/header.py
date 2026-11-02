"""Render the profile header SVGs with Tehran's current time and temperature.

Usage: python tools/header.py <out-dir>
Run by .github/workflows/header.yml every 15 minutes.
"""
import json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone

OUT = sys.argv[1]
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

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", text="#e6edf3", muted="#8b949e",
                 accent="#3fb950", board="#161b22", hole="#0d1117", pin="#d29922",
                 screen="#000000", px="#dbe9ff"),
    "light": dict(bg="#ffffff", border="#d0d7de", text="#1f2328", muted="#59636e",
                  accent="#1a7f37", board="#f6f8fa", hole="#ffffff", pin="#bf8700",
                  screen="#0d1117", px="#dbe9ff"),
}

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
                    cls = ' class="blink"' if ch == ":" else ""
                    out.append(oled_rect(x + c * scale, y + r * scale, scale, scale, 1.0, cls))
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
    px += text(temp, 122 - width(temp, 2), 4, 2)
    px.append(oled_rect(6, 17, 116, 0.67, 0.35))
    clock = now.strftime("%H:%M")
    px += text(clock, (128 - width(clock, 5)) // 2, 22, 5)
    date = now.strftime("%a %d %b").upper()
    px += text(date, (128 - width(date, 1.5)) / 2, 54, 1.5)
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
    label = f"Amin Mohammadi. Python, embedded and automation. Tehran, {now:%H:%M}, {temp.replace('o', '°')}."
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240" role="img" aria-label="{label}">
  <style>
    .blink {{ animation: blink 2s steps(1) infinite; }}
    .led {{ animation: led 2.4s ease-in-out infinite; }}
    .cur {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @keyframes led {{ 0%, 100% {{ opacity: .35; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{ .blink, .led, .cur {{ animation: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="899" height="239" rx="16" fill="{T["bg"]}" stroke="{T["border"]}"/>
  <g font-family="ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace">
    <text x="56" y="70" font-size="14" fill="{T["muted"]}">~/A2M33 $</text>
    <rect class="cur" x="137" y="58" width="8" height="15" fill="{T["accent"]}"/>
    <text x="56" y="194" font-size="14" fill="{T["accent"]}">Tehran, Iran · building tools that touch hardware</text>
  </g>
  <g font-family="-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif">
    <text x="54" y="126" font-size="48" font-weight="700" letter-spacing="-1" fill="{T["text"]}">Amin Mohammadi</text>
    <text x="56" y="158" font-size="19" fill="{T["muted"]}">Python, embedded and automation</text>
  </g>
  <rect x="600" y="36" width="248" height="172" rx="10" fill="{T["board"]}" stroke="{T["border"]}"/>
  {holes}
  <g font-family="ui-monospace, Consolas, monospace" font-size="8" fill="{T["muted"]}">{pins}</g>
  <circle class="led" cx="824" cy="58" r="3" fill="{T["accent"]}"/>
  <text x="812" y="61" font-family="ui-monospace, Consolas, monospace" font-size="8" fill="{T["muted"]}" text-anchor="end">PWR</text>
  <rect x="622" y="70" width="204" height="108" rx="3" fill="{T["screen"]}"/>
  <g fill="{T["px"]}">
    {"".join(screen_pixels(now, temp))}
  </g>
</svg>
'''


now = datetime.now(TZ)
temp = temperature()
os.makedirs(OUT, exist_ok=True)
for t in THEMES:
    with open(os.path.join(OUT, f"header-{t}.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg(t, now, temp))
print(f"{now:%Y-%m-%d %H:%M} {temp}")
