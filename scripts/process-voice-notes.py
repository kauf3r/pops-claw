#!/usr/bin/env python3
"""Voice Notes Pipeline: Google Drive -> coordination.db

Polls the "Voice Notes" Google Drive folder for new files.
- Monologue HTML shares: extracts title, summary, and transcript
- .txt/.md files: stored directly (pre-transcribed)
- Audio files: transcribed with Whisper (tiny model, CPU)
Processed files are moved to a "Processed" subfolder.
"""

import json
import os
import re
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Config
DRIVE_FOLDER_ID = "1yEXewYOsGDTIbTAoXNeUM6r7aweWg-Wl"
PROCESSED_FOLDER_ID = "1753HmDxXXIZh73_zoMicdP4iy5i64FoH"
ACCOUNT = "theandykaufman@gmail.com"
DB_PATH = Path.home() / "clawd" / "coordination.db"
LOG_FILE = Path.home() / "scripts" / "voice-notes.log"
WHISPER_MODEL = "tiny"
TEXT_EXTENSIONS = {".txt", ".md"}
AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".ogg", ".flac", ".webm", ".mp4"}
ALL_EXTENSIONS = TEXT_EXTENSIONS | AUDIO_EXTENSIONS
MONOLOGUE_MIME = "text/html"


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run_gog(args):
    """Run a gog command and return stdout."""
    cmd = ["gog"] + args + ["--account", ACCOUNT, "--no-input"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"gog error: {result.stderr.strip()}")
        return None
    return result.stdout


def list_drive_files():
    """List processable files in the Voice Notes folder."""
    output = run_gog(["drive", "ls", "--parent", DRIVE_FOLDER_ID, "--json"])
    if not output:
        return []

    data = json.loads(output)
    files = []
    for f in data.get("files", []):
        if f.get("mimeType") == "application/vnd.google-apps.folder":
            continue
        name = f.get("name", "")
        ext = Path(name).suffix.lower()
        mime = f.get("mimeType", "")

        if ext in ALL_EXTENSIONS:
            files.append({
                "id": f["id"],
                "name": name,
                "modified": f.get("modifiedTime", ""),
                "is_text": ext in TEXT_EXTENSIONS,
                "is_monologue": False,
            })
        elif mime == MONOLOGUE_MIME or (not ext and mime.startswith("text/")):
            files.append({
                "id": f["id"],
                "name": name,
                "modified": f.get("modifiedTime", ""),
                "is_text": False,
                "is_monologue": True,
            })
    return files


def download_file(file_id, dest_path):
    """Download a file from Drive."""
    result = run_gog(["drive", "download", file_id, "--out", str(dest_path)])
    return result is not None


def parse_monologue_html(html_content):
    """Extract title, summary, and transcript from Monologue HTML share.

    Monologue embeds data in Next.js RSC payload via self.__next_f.push() calls.
    Natural text chunks (summary + transcript) start with a letter, #, or *.
    React framework chunks start with digits, $, [, or {.
    """
    result = {"title": None, "summary": None, "transcript": None}

    # Extract title from <title> tag
    title_match = re.search(r"<title>([^<]+)</title>", html_content)
    if title_match:
        title = title_match.group(1)
        title = re.sub(r"\s*\|\s*Monologue Notes\s*$", "", title)
        result["title"] = title

    # Extract text chunks from Next.js RSC data
    chunks = re.findall(
        r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)',
        html_content
    )

    text_blocks = []
    for chunk in chunks:
        try:
            unescaped = chunk.encode().decode("unicode_escape")
        except (UnicodeDecodeError, ValueError):
            unescaped = chunk.replace("\\n", "\n").replace('\\"', '"').replace("\\u0026", "&")

        if len(unescaped) < 100:
            continue

        # Skip React/Next.js framework data
        # Catches: 0:{, 5:[, 16:I[, f:I[, e:[, c:, $, [, {
        if re.match(r'^(\w+:|[$\[{])', unescaped):
            continue

        # Keep chunks that look like natural prose (multiple words, not code)
        if re.search(r'[a-z]{3,}\s+[a-z]{3,}', unescaped[:200]):
            text_blocks.append(unescaped)

    # Deduplicate (summary appears twice — SSR + hydration)
    unique_blocks = []
    seen = set()
    for block in text_blocks:
        key = block[:200]
        if key not in seen:
            seen.add(key)
            unique_blocks.append(block)

    if len(unique_blocks) >= 2:
        result["summary"] = unique_blocks[0].strip()
        result["transcript"] = unique_blocks[1].strip()
    elif len(unique_blocks) == 1:
        result["transcript"] = unique_blocks[0].strip()

    return result


def make_title(monologue_title, modified_time, summary=None):
    """Build a title with date/time prefix.

    Uses recording time from Monologue summary (**Time:** 8:06 AM) if available,
    combined with the date from Drive modifiedTime.
    """
    date_str = ""
    time_str = ""

    if modified_time:
        try:
            dt = datetime.fromisoformat(modified_time.replace("Z", "+00:00"))
            dt_pt = dt - timedelta(hours=8)
            date_str = dt_pt.strftime("%Y-%m-%d")
            time_str = dt_pt.strftime("%H:%M")
        except (ValueError, TypeError):
            date_str = modified_time[:10]

    # Extract actual recording time from Monologue's AI summary
    if summary:
        m = re.search(r'\*\*Time:\*\*\s*(\d{1,2}:\d{2}\s*[APap][Mm])', summary)
        if m:
            try:
                t = datetime.strptime(m.group(1).strip(), "%I:%M %p")
                time_str = t.strftime("%H:%M")
            except ValueError:
                pass

    dt_str = f"{date_str} {time_str}".strip() if date_str else time_str

    if monologue_title and dt_str:
        return f"{dt_str} — {monologue_title}"
    elif monologue_title:
        return monologue_title
    elif dt_str:
        return f"{dt_str} — Voice Note"
    else:
        return "Voice Note"


def get_duration(filepath):
    """Get audio duration in seconds via ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(filepath)],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.SubprocessError):
        return 0.0


def transcribe_audio(filepath):
    """Transcribe audio file with Whisper."""
    whisper_bin = Path.home() / "whisper-venv" / "bin" / "whisper"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [str(whisper_bin), str(filepath),
             "--model", WHISPER_MODEL,
             "--language", "en",
             "--output_format", "txt",
             "--output_dir", tmpdir],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            log(f"Whisper error: {result.stderr[:200]}")
            return None

        stem = filepath.stem
        txt_file = Path(tmpdir) / f"{stem}.txt"
        if txt_file.exists():
            return txt_file.read_text().strip()

        for f in Path(tmpdir).glob("*.txt"):
            return f.read_text().strip()

    return None


def move_to_processed(file_id):
    """Move file to Processed subfolder."""
    return run_gog(["drive", "move", file_id, "--parent", PROCESSED_FOLDER_ID])


def main():
    log("Starting voice notes processing")

    if "GOG_KEYRING_PASSWORD" not in os.environ:
        env_file = Path.home() / ".openclaw" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GOG_KEYRING_PASSWORD="):
                    os.environ["GOG_KEYRING_PASSWORD"] = line.split("=", 1)[1]
                    break

    files = list_drive_files()
    if not files:
        log("No new voice notes found")
        print(json.dumps({"processed": 0, "files": []}))
        return

    log(f"Found {len(files)} file(s)")

    conn = sqlite3.connect(str(DB_PATH))
    processed = 0
    results = []

    for f in files:
        file_id = f["id"]
        filename = f["name"]
        is_text = f["is_text"]
        is_monologue = f["is_monologue"]

        count = conn.execute(
            "SELECT COUNT(*) FROM voice_notes WHERE drive_file_id = ?",
            (file_id,)
        ).fetchone()[0]
        if count > 0:
            log(f"Skipping already-processed: {filename}")
            continue

        source_type = "monologue" if is_monologue else ("text" if is_text else "audio")
        log(f"Processing: {filename} ({source_type})")

        with tempfile.TemporaryDirectory() as tmpdir:
            download_path = Path(tmpdir) / filename

            if not download_file(file_id, download_path):
                log(f"ERROR: Failed to download {filename}")
                continue

            title = None
            summary = None
            transcript = None
            duration = 0.0
            source_app = source_type

            if is_monologue:
                html = download_path.read_text(errors="replace")
                parsed = parse_monologue_html(html)
                summary = parsed["summary"]
                transcript = parsed["transcript"]
                title = make_title(parsed["title"], f["modified"], summary=summary)
                if not transcript and summary:
                    transcript = summary
                    summary = None
            elif is_text:
                transcript = download_path.read_text().strip()
                title = make_title(None, f["modified"])
            else:
                duration = get_duration(download_path)
                log(f"Transcribing: {filename} (model={WHISPER_MODEL})")
                transcript = transcribe_audio(download_path)
                title = make_title(None, f["modified"])

            if not transcript:
                log(f"ERROR: No content for {filename}")
                continue

        conn.execute(
            """INSERT INTO voice_notes
               (drive_file_id, filename, title, recorded_at, duration_seconds,
                transcript, summary, source_app)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (file_id, filename, title, f["modified"], duration,
             transcript, summary, source_app)
        )
        conn.commit()
        log(f"Stored: {title or filename} ({len(transcript)} chars, source={source_app})")

        if move_to_processed(file_id):
            log(f"Moved to Processed: {filename}")
        else:
            log(f"WARN: Failed to move {filename} to Processed")

        processed += 1
        results.append({
            "filename": filename,
            "title": title,
            "duration": duration,
            "transcript_length": len(transcript),
            "has_summary": summary is not None,
            "source": source_app,
        })

    conn.close()

    total = sqlite3.connect(str(DB_PATH)).execute(
        "SELECT COUNT(*) FROM voice_notes"
    ).fetchone()[0]

    log(f"Done. Processed: {processed}, Total in DB: {total}")
    print(json.dumps({"processed": processed, "total": total, "files": results}))


if __name__ == "__main__":
    main()
