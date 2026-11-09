"""Render the "What I work with" panel as two SVGs (light + dark) into assets/.

A markdown table on GitHub always draws a header row, so the stack is drawn
as an image in the same frame as the header instead.

Usage: python tools/stack.py
"""
import base64, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ROWS = [
    ("Languages", "Python, C, C++, JavaScript, HTML, CSS, Bash, PowerShell"),
    ("Hardware", "ESP32, Arduino, Raspberry Pi, Modbus TCP"),
    ("Vision and ML", "OpenCV, MediaPipe, PyTorch, scikit-learn"),
    ("Tools", "Linux, Git, VS Code, SQLite, Node.js"),
    ("Spoken", "Persian (native), English (fluent), German (learning)"),
]
THEMES = {
    "dark": dict(bg="#0b1222", border="#22304b", text="#e6edf7", muted="#93a3bd", signal="#2fcbea"),
    "light": dict(bg="#ffffff", border="#cdd6e4", text="#0c1628", muted="#4a5a73", signal="#0788ad"),
}
W, ROW, PAD = 900, 52, 8


def face(weight):
    with open(os.path.join(ROOT, "assets", "fonts", f"Archivo-{weight}.woff2"), "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f'@font-face {{ font-family: "Archivo"; font-weight: {weight}; src: url(data:font/woff2;base64,{data}) format("woff2"); }}'


def svg(T):
    h = PAD * 2 + ROW * len(ROWS)
    rows = []
    for i, (label, value) in enumerate(ROWS):
        y = PAD + i * ROW
        if i:
            rows.append(f'<line x1="32" x2="{W - 32}" y1="{y + 0.5}" y2="{y + 0.5}" stroke="{T["border"]}"/>')
        mid = y + ROW / 2 + 6
        rows.append(f'<text x="54" y="{mid}" font-size="16" fill="{T["muted"]}">{label}</text>')
        rows.append(f'<text x="214" y="{mid}" font-size="17" fill="{T["text"]}">{value}</text>')
        # a pad on each row's label, the trace look's signature
        rows.append(f'<circle cx="38" cy="{mid - 5.5}" r="3.5" fill="none" stroke="{T["signal"] if i == 0 else T["border"]}" stroke-width="1.5"/>')
    alt = "; ".join(f"{a}: {b}" for a, b in ROWS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{alt}">'
            f'<style>{face(400)}</style>'
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="8" fill="{T["bg"]}" stroke="{T["border"]}"/>'
            f'<g font-family="Archivo, sans-serif">{"".join(rows)}</g></svg>\n')


if __name__ == "__main__":
    for name, T in THEMES.items():
        with open(os.path.join(ROOT, "assets", f"stack-{name}.svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg(T))
    print("assets/stack-dark.svg, assets/stack-light.svg")
