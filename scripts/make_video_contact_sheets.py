#!/usr/bin/env python3
"""Build event-level video contact sheets from generated five-frame previews."""

import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT = Path(__file__).resolve().parents[1]
ANALYSIS = PROJECT / "data" / "media-analysis.json"
OUTPUT = PROJECT / "data" / "contact-sheets"


def main() -> None:
    payload = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    groups = defaultdict(list)
    for index, video in enumerate(payload["videos"], 1):
        groups[video["event"]].append((index, video))
    font = ImageFont.load_default()
    for event_number, event in enumerate(sorted(groups), 1):
        videos = groups[event]
        row_height = 170
        canvas = Image.new("RGB", (1200, 60 + len(videos) * row_height), "#f4f0e8")
        draw = ImageDraw.Draw(canvas)
        draw.text((18, 18), event, fill="#171717", font=font)
        for row, (global_index, video) in enumerate(videos):
            y = 60 + row * row_height
            draw.text((18, y + 8), f'{global_index:03d} {video["filename"]}', fill="#171717", font=font)
            draw.text((18, y + 26), f'{video.get("duration_seconds", 0):.1f}s', fill="#555555", font=font)
            for frame_index, thumbnail in enumerate(video.get("thumbnails", [])):
                image = Image.open(thumbnail).convert("RGB")
                image = ImageOps.fit(image, (190, 120), method=Image.Resampling.LANCZOS)
                canvas.paste(image, (220 + frame_index * 194, y + 8))
        destination = OUTPUT / f"videos-event-{event_number:02d}.jpg"
        canvas.save(destination, quality=88, optimize=True)
        print(destination)


if __name__ == "__main__":
    main()
