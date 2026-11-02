import random, sys, os

OUT = sys.argv[1]

FONT = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "7": ["111", "001", "001", "001", "001"],
    ":": ["000", "010", "000", "010", "000"],
    "o": ["11", "11", "00", "00", "00"],
    "C": ["111", "100", "100", "100", "111"],
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


def text(s, x, y, scale):
    out = []
    for ch in s:
        for r, row in enumerate(FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1":
                    cls = ' class="blink"' if ch == ":" else ""
                    out.append(oled_rect(x + c * scale, y + r * scale, scale, scale, 1.0, cls))
        x += 4 * scale
    return out


def screen_pixels():
    px = text("14:07", 6, 5, 3)
    px += text("22oC", 90, 7, 2)
    px.append(oled_rect(6, 25, 116, 0.67, 0.35))
    rng = random.Random(33)
    cols, rows, x0, y0 = 26, 7, 12, 30
    levels = [0.12, 0.35, 0.65, 1.0]
    for c in range(cols):
        for r in range(rows):
            w = rng.random() * (0.4 + 0.6 * c / cols)
            lvl = levels[min(3, int(w * 4.4))]
            extra = ""
            if rng.random() < 0.22:
                extra = f' class="tw" style="animation-delay:{rng.random() * 6:.2f}s"'
            px.append(oled_rect(x0 + c * 4, y0 + r * 4, 3, 3, lvl, extra))
    return px


def svg(t):
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
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240" role="img" aria-label="Amin Mohammadi. Python, embedded and automation. Tehran to Germany, looking for an Ausbildung.">
  <style>
    .blink {{ animation: blink 2s steps(1) infinite; }}
    .tw {{ animation: tw 6s ease-in-out infinite; }}
    .led {{ animation: led 2.4s ease-in-out infinite; }}
    .cur {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @keyframes tw {{ 0%, 100% {{ opacity: .12; }} 40%, 60% {{ opacity: 1; }} }}
    @keyframes led {{ 0%, 100% {{ opacity: .35; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{ .blink, .tw, .led, .cur {{ animation: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="899" height="239" rx="16" fill="{T["bg"]}" stroke="{T["border"]}"/>
  <g font-family="ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace">
    <text x="56" y="70" font-size="14" fill="{T["muted"]}">~/A2M33 $</text>
    <rect class="cur" x="137" y="58" width="8" height="15" fill="{T["accent"]}"/>
    <text x="56" y="194" font-size="14" fill="{T["accent"]}">Tehran → Germany · looking for an Ausbildung</text>
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
    {"".join(screen_pixels())}
  </g>
</svg>
'''


for t in THEMES:
    with open(os.path.join(OUT, f"header-v4-{t}.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg(t))
