"""Check and index regenerated archived-data figures (not fresh experiments)."""
from pathlib import Path
import hashlib
import json
import math
from PIL import Image, ImageDraw, ImageStat

root = Path(__file__).resolve().parents[1]
figures = sorted((root / "paper-figures").rglob("*.png"))
assert figures, "No regenerated figures"
assert {p.parent.name for p in figures} >= {"streaming", "latency", "throughput"}
index = []
columns, tile_w, tile_h = 4, 360, 270
sheet = Image.new("RGB", (columns * tile_w, math.ceil(len(figures) / columns) * tile_h), "white")
draw = ImageDraw.Draw(sheet)
for i, path in enumerate(figures):
    with Image.open(path) as original:
        original.verify()
    with Image.open(path) as original:
        rgb = original.convert("RGB")
        assert min(rgb.size) >= 200, path
        assert max(ImageStat.Stat(rgb).stddev) > 5, f"Blank figure: {path}"
        index.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                      "size": list(rgb.size), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        rgb.thumbnail((tile_w - 10, tile_h - 38))
        x, y = (i % columns) * tile_w, (i // columns) * tile_h
        sheet.paste(rgb, (x + 5, y + 30))
        draw.text((x + 5, y + 4), path.name[:49], fill="black")
out = root / "artifacts" / "reproduction"
out.mkdir(parents=True, exist_ok=True)
sheet.save(out / "contact-sheet.png")
report = {"kind": "authors_archived_data_figure_regeneration", "figure_count": len(index),
          "groups": sorted({p.parent.name for p in figures}), "figures": index,
          "fresh_network_experiments": False}
(out / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "figures"}))
