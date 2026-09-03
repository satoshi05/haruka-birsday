#!/usr/bin/env python3
"""Analyze the connected Haruka media folders without modifying originals."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import imagehash
import imageio_ffmpeg
import numpy as np
from PIL import ExifTags, Image, ImageDraw, ImageFont, ImageOps


PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".webm", ".mkv"}
DATE_TAGS = {306, 36867, 36868}
CONTACT_SIZE = (320, 240)
FACE_DETECTOR = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def iso_exif_date(image: Image.Image) -> str | None:
    try:
        exif = image.getexif()
        for tag in DATE_TAGS:
            value = exif.get(tag)
            if value:
                return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S").isoformat()
    except (ValueError, TypeError, OSError):
        pass
    return None


def safe_image(path: Path) -> Image.Image:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    return image.convert("RGB")


def detect_faces(gray: np.ndarray) -> list[list[int]]:
    height, width = gray.shape[:2]
    scale = min(1.0, 960.0 / max(width, height))
    sample = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else gray
    faces = FACE_DETECTOR.detectMultiScale(
        sample, scaleFactor=1.15, minNeighbors=5, minSize=(32, 32)
    )
    if scale < 1:
        faces = np.asarray(faces, dtype=float) / scale
    return [list(map(int, face)) for face in faces]


def analyze_photo(path: Path, source_root: Path) -> dict:
    image = safe_image(path)
    rgb = np.asarray(image)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    width, height = image.size
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    faces = detect_faces(gray)
    phash = str(imagehash.phash(image))
    quality = min(100.0, (
        min(sharpness / 700.0, 1.0) * 42
        + min(contrast / 65.0, 1.0) * 22
        + max(0.0, 1.0 - abs(brightness - 128.0) / 128.0) * 18
        + min((width * height) / 3_000_000, 1.0) * 18
    ))
    return {
        "path": str(path.relative_to(source_root)),
        "event": path.relative_to(source_root).parts[0],
        "filename": path.name,
        "width": width,
        "height": height,
        "aspect_ratio": round(width / height, 4),
        "exif_datetime": iso_exif_date(image),
        "filesystem_mtime": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "sharpness": round(sharpness, 2),
        "face_count": len(faces),
        "faces": faces,
        "phash": phash,
        "technical_score": round(quality, 2),
    }


def cluster_similar(photos: list[dict], threshold: int = 7) -> None:
    groups: list[tuple[imagehash.ImageHash, int]] = []
    next_id = 1
    for photo in sorted(photos, key=lambda p: (p["event"], p["filename"])):
        value = imagehash.hex_to_hash(photo["phash"])
        match = None
        for representative, group_id in groups:
            if value - representative <= threshold:
                match = group_id
                break
        if match is None:
            match = next_id
            next_id += 1
            groups.append((value, match))
        photo["similarity_group"] = match


def probe_video(path: Path) -> dict:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError("Video could not be opened")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps else 0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    capture.release()
    return {
        "duration_seconds": round(duration, 3),
        "width": width,
        "height": height,
        "frame_rate": round(fps, 3),
    }


def video_thumbnails(path: Path, output_dir: Path, duration: float, ffmpeg: str) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ratios = (0.03, 0.25, 0.50, 0.75, 0.97)
    outputs = []
    for index, ratio in enumerate(ratios, 1):
        second = max(0.0, duration * ratio)
        output = output_dir / f"frame-{index}.jpg"
        command = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{second:.3f}", "-i", str(path), "-frames:v", "1",
            "-vf", "scale='min(960,iw)':-2", "-q:v", "3", str(output),
        ]
        subprocess.run(command, check=True)
        outputs.append(str(output))
    return outputs


def make_contact_sheet(items: list[dict], source_root: Path, output: Path, title: str) -> None:
    columns = 4
    cell_w, cell_h = 360, 300
    header_h = 70
    rows = math.ceil(len(items) / columns)
    canvas = Image.new("RGB", (columns * cell_w, header_h + rows * cell_h), "#f4f0e8")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((20, 20), title, fill="#171717", font=font)
    for index, item in enumerate(items):
        row, col = divmod(index, columns)
        x, y = col * cell_w, header_h + row * cell_h
        try:
            image = safe_image(source_root / item["path"])
            thumb = ImageOps.fit(image, CONTACT_SIZE, method=Image.Resampling.LANCZOS)
            canvas.paste(thumb, (x + 20, y + 10))
        except Exception:
            draw.rectangle((x + 20, y + 10, x + 340, y + 250), fill="#2a2a2a")
        label = f'{index + 1:03d} {item["filename"][-34:]}'
        metrics = f'faces:{item["face_count"]} tech:{item["technical_score"]:.0f} sim:{item["similarity_group"]}'
        draw.text((x + 20, y + 255), label, fill="#171717", font=font)
        draw.text((x + 20, y + 272), metrics, fill="#555555", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=88, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    source_root = args.source.resolve()
    project = args.project.resolve()
    event_dirs = [p for p in source_root.iterdir() if p.is_dir() and p != project]
    photo_paths = sorted(
        p for d in event_dirs for p in d.rglob("*") if p.is_file() and p.suffix.lower() in PHOTO_EXTENSIONS
    )
    video_paths = sorted(
        p for d in event_dirs for p in d.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )

    photos = []
    errors = []
    for path in photo_paths:
        try:
            photos.append(analyze_photo(path, source_root))
        except Exception as exc:
            errors.append({"path": str(path.relative_to(source_root)), "error": str(exc)})
    cluster_similar(photos)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    videos = []
    for index, path in enumerate(video_paths, 1):
        relative = path.relative_to(source_root)
        item = {"path": str(relative), "event": relative.parts[0], "filename": path.name}
        try:
            meta = probe_video(path)
            item.update(meta)
            thumb_dir = project / "assets" / "video-thumbnails" / f"video-{index:03d}"
            item["thumbnails"] = video_thumbnails(path, thumb_dir, meta["duration_seconds"], ffmpeg)
            videos.append(item)
        except Exception as exc:
            item["error"] = str(exc)
            videos.append(item)

    by_event: dict[str, list[dict]] = defaultdict(list)
    for photo in photos:
        by_event[photo["event"]].append(photo)
    for event, items in by_event.items():
        safe_name = f"event-{sorted(by_event).index(event) + 1:02d}.jpg"
        make_contact_sheet(items, source_root, project / "data" / "contact-sheets" / safe_name, event)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "source_root": str(source_root),
        "originals_modified": False,
        "photo_count": len(photos),
        "video_count": len(videos),
        "events": sorted(by_event),
        "photos": photos,
        "videos": videos,
        "errors": errors,
    }
    output = project / "data" / "media-analysis.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("photo_count", "video_count", "events", "errors")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
