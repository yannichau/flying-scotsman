from pathlib import Path
import re

svg_path = Path(__file__).resolve().parents[1] / "_includes" / "london-map.svg"
text = svg_path.read_text(encoding="utf-8")
text = re.sub(r"<text\b[^>]*>.*?</text>", "", text, flags=re.IGNORECASE | re.DOTALL)
svg_path.write_text(text, encoding="utf-8")
print(f"Removed SVG text elements from {svg_path}")
