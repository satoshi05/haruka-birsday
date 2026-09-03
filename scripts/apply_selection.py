#!/usr/bin/env python3
"""Copy approved working candidates from read-only source folders into selected/."""

import json
import shutil
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT.parent
ANALYSIS = json.loads((PROJECT / "data" / "media-analysis.json").read_text(encoding="utf-8"))

EVENTS = {
    "グランイルミ": {
        "slug": "06-grand-illumination",
        "title": "グランイルミ",
        "message": "グランイルミ",
        "a": [1, 4, 49, 69],
        "b": [5, 6, 9, 15, 25, 35, 45, 55],
    },
    "伊豆長岡温泉あやめ祭": {
        "slug": "02-ayame-festival",
        "title": "あやめ祭り",
        "message": "あやめ祭り",
        "a": [1],
        "b": [3, 4, 5],
    },
    "山梨井沢旅行＆フルーツ巡り": {
        "slug": "03-yamanashi-trip",
        "title": "ひまわり畑・ホテルの上から見た花火",
        "message": "ひまわり畑・ホテルの上から見た花火",
        "a": [26, 27, 73],
        "b": [1, 10, 18, 24, 25, 28, 33, 57],
    },
    "滝と富士吉原祭とさくらんぼがり、中野の棚田": {
        "slug": "01-first-days-and-festival",
        "title": "さくらんぼ狩り・富士吉原祭り",
        "message": "さくらんぼ狩り・富士吉原祭り",
        "a": [6, 38, 81],
        "b": [1, 4, 10, 32, 37, 40, 54, 79],
    },
    "熱海の海と花火": {
        "slug": "05-atami-sea-fireworks",
        "title": "熱海の海",
        "message": "熱海の海",
        "a": [4, 9, 16],
        "b": [1, 5, 6, 10, 11, 15],
    },
    "長岡花火": {
        "slug": "04-nagaoka-fireworks",
        "title": "長岡花火",
        "message": "長岡花火",
        "a": [3, 6, 24, 32],
        "b": [2, 7, 10, 13, 25, 30, 33],
    },
}

VIDEO_CANDIDATES = [3, 4, 7, 15, 19, 23, 34, 38, 48, 52]


def copy_candidate(source_relative: str, destination: Path) -> None:
    source = SOURCE / source_relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main() -> None:
    selection = {"photos": [], "videos": [], "event_messages": []}
    for event, config in EVENTS.items():
        photos = [photo for photo in ANALYSIS["photos"] if photo["event"] == event]
        selection["event_messages"].append({
            "event": event,
            "slug": config["slug"],
            "title": config["title"],
            "message": config["message"],
            "date_status": "unknown-exif-missing",
        })
        for rank in ("a", "b"):
            for index in config[rank]:
                photo = photos[index - 1]
                destination = PROJECT / "assets" / "photos" / "selected" / config["slug"] / rank.upper() / photo["filename"]
                copy_candidate(photo["path"], destination)
                selection["photos"].append({
                    "rank": rank.upper(),
                    "event": event,
                    "source": photo["path"],
                    "selected_copy": str(destination.relative_to(PROJECT)),
                    "technical_score": photo["technical_score"],
                    "face_count": photo["face_count"],
                    "selection_reason": "visual-review-and-story-balance",
                })

        already_selected = {item["source"] for item in selection["photos"] if item["event"] == event}
        groups = {}
        for photo in photos:
            if photo["path"] not in already_selected:
                groups.setdefault(photo["similarity_group"], []).append(photo)
        for group in groups.values():
            group.sort(key=lambda photo: photo["technical_score"], reverse=True)
            for position, photo in enumerate(group):
                duplicate_of_selected = any(
                    chosen["event"] == event
                    and next(
                        candidate["similarity_group"]
                        for candidate in photos
                        if candidate["path"] == chosen["source"]
                    ) == photo["similarity_group"]
                    for chosen in selection["photos"]
                    if chosen["rank"] in {"A", "B"}
                )
                rank = "D" if photo["technical_score"] < 45 or duplicate_of_selected or position >= 2 else "C"
                reason = (
                    "low-technical-quality" if photo["technical_score"] < 45
                    else "similar-to-stronger-selection" if duplicate_of_selected or position >= 2
                    else "gallery-reserve"
                )
                selection["photos"].append({
                    "rank": rank,
                    "event": event,
                    "source": photo["path"],
                    "selected_copy": None,
                    "technical_score": photo["technical_score"],
                    "face_count": photo["face_count"],
                    "selection_reason": reason,
                })

    for index in VIDEO_CANDIDATES:
        video = ANALYSIS["videos"][index - 1]
        config = EVENTS[video["event"]]
        destination = PROJECT / "assets" / "videos" / "selected" / config["slug"] / video["filename"]
        copy_candidate(video["path"], destination)
        selection["videos"].append({
            "candidate_number": index,
            "event": video["event"],
            "source": video["path"],
            "selected_copy": str(destination.relative_to(PROJECT)),
            "duration_seconds": video["duration_seconds"],
            "selection_reason": "distinctive-motion-or-shared-moment",
        })

    output = PROJECT / "data" / "media-selection.json"
    output.write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "A": sum(item["rank"] == "A" for item in selection["photos"]),
        "B": sum(item["rank"] == "B" for item in selection["photos"]),
        "C": sum(item["rank"] == "C" for item in selection["photos"]),
        "D": sum(item["rank"] == "D" for item in selection["photos"]),
        "videos": len(selection["videos"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
