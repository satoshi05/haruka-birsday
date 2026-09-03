#!/usr/bin/env python3
"""Create web-safe copies and a content manifest from the user's selected media."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageOps


PROJECT = Path(__file__).resolve().parents[1]
PHOTO_ROOT = PROJECT / "assets" / "photos" / "selected"
VIDEO_ROOT = PROJECT / "assets" / "videos" / "selected"
PUBLIC_ROOT = PROJECT / "public" / "media"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}

CHAPTERS = [
    ("01-first-days-and-festival", "さくらんぼ狩り・富士吉原祭り"),
    ("06-grand-illumination", "グランイルミ"),
    ("02-ayame-festival", "あやめ祭り"),
    ("05-atami-sea-fireworks", "熱海の海"),
    ("04-nagaoka-fireworks", "長岡花火"),
    ("03-yamanashi-trip", "ひまわり畑・ホテルの上から見た花火"),
]


def convert_photo(source: Path, destination: Path, max_size: int) -> None:
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, "WEBP", quality=82, method=6)


def convert_video(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
        "-vf", "scale='min(1280,iw)':-2", "-c:v", "libx264", "-preset", "medium",
        "-crf", "25", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "96k",
        str(destination),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    if PUBLIC_ROOT.exists():
        shutil.rmtree(PUBLIC_ROOT)
    manifest = {"title": "OUR DAYS", "chapters": []}
    for chapter_number, (source_slug, title) in enumerate(CHAPTERS, 1):
        web_slug = f"chapter-{chapter_number:02d}"
        photos = sorted(
            path for path in (PHOTO_ROOT / source_slug).rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )
        videos = sorted(
            path for path in (VIDEO_ROOT / source_slug).rglob("*")
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
        )[:1]
        chapter = {"number": chapter_number, "title": title, "photos": [], "videos": []}
        for photo_number, source in enumerate(photos, 1):
            stem = f"photo-{photo_number:02d}"
            large = PUBLIC_ROOT / web_slug / f"{stem}-1280.webp"
            small = PUBLIC_ROOT / web_slug / f"{stem}-768.webp"
            convert_photo(source, large, 1280)
            convert_photo(source, small, 768)
            chapter["photos"].append({
                "src": f"/media/{web_slug}/{stem}-1280.webp",
                "srcSmall": f"/media/{web_slug}/{stem}-768.webp",
                "alt": f"{title}の思い出 {photo_number}",
            })
        for video_number, source in enumerate(videos, 1):
            destination = PUBLIC_ROOT / web_slug / f"video-{video_number:02d}.mp4"
            convert_video(source, destination)
            chapter["videos"].append({
                "src": f"/media/{web_slug}/video-{video_number:02d}.mp4",
                "label": f"{title}の動画 {video_number}",
            })
        manifest["chapters"].append(chapter)

    destination = PROJECT / "data" / "memories.json"
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "chapters": len(manifest["chapters"]),
        "photos": sum(len(chapter["photos"]) for chapter in manifest["chapters"]),
        "videos": sum(len(chapter["videos"]) for chapter in manifest["chapters"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
