#!/usr/bin/env python3
"""
Kleines Zusatz-Tool für die Phoniebox: legt per Web-Formular einen Ordner
unter shared/audiofolders/<name> an und schreibt eine spotify.uri-Datei
mit dem Inhalt "typ:id" (z.B. "album:01JrN7TzqiE7Vs1JNJ3Mkl").

Start:
    python3 spotify_add.py

Standardmäßig erreichbar unter http://<pi-ip>:5050/
"""

import os
import re
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Pfad zu den Phoniebox-Audiofolders - ggf. anpassen
AUDIOFOLDERS_BASE = "/home/pi/RPi-Jukebox-RFID/shared/audiofolders"

# Erkennt open.spotify.com-Links (mit oder ohne Query-String wie ?si=...)
# sowie reine spotify:typ:id URIs, falls die mal direkt eingefügt werden.
URL_PATTERN = re.compile(
    r"open\.spotify\.com/(?:intl-[a-z]{2}/)?(album|playlist|track|artist|show|episode)/([a-zA-Z0-9]+)"
)
URI_PATTERN = re.compile(
    r"spotify:(album|playlist|track|artist|show|episode):([a-zA-Z0-9]+)"
)

PAGE = """
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <title>Spotify-Ordner anlegen</title>
    <style>
        body { font-family: sans-serif; max-width: 480px; margin: 40px auto; }
        label { display: block; margin-top: 16px; font-weight: bold; }
        input[type=text] { width: 100%; padding: 8px; box-sizing: border-box; }
        button { margin-top: 20px; padding: 10px 20px; }
        .msg { margin-top: 20px; padding: 10px; }
        .ok { background: #dff0d8; color: #3c763d; }
        .error { background: #f2dede; color: #a94442; }
    </style>
</head>
<body>
    <h2>Spotify-Ordner für Phoniebox anlegen</h2>
    <form method="post">
        <label>Kategorie</label>
        <div>
            <label style="font-weight: normal; display: inline;">
                <input type="radio" name="category" value="hoerbuch"
                       {{ 'checked' if category != 'musik' else '' }}> Hörbuch
            </label>
            &nbsp;&nbsp;
            <label style="font-weight: normal; display: inline;">
                <input type="radio" name="category" value="musik"
                       {{ 'checked' if category == 'musik' else '' }}> Musik
            </label>
        </div>

        <label for="folder">Ordnername (wird unter hoerbuch/spotify/ bzw. musik/spotify/ angelegt)</label>
        <input type="text" id="folder" name="folder" required
               value="{{ folder or '' }}" placeholder="z.B. Peter_und_der_Wolf oder Hoerspiele/Peter_und_der_Wolf">

        <label for="url">Spotify-Link (Album, Playlist oder Track)</label>
        <input type="text" id="url" name="url" required
               value="{{ url or '' }}"
               placeholder="https://open.spotify.com/album/...">

        <button type="submit">Anlegen</button>
    </form>

    {% if message %}
    <div class="msg {{ 'ok' if success else 'error' }}">{{ message }}</div>
    {% endif %}

    <h3>Vorhandene Ordner</h3>
    {% if existing_folders %}
    <ul>
        {% for f in existing_folders %}
        <li>{{ f }}</li>
        {% endfor %}
    </ul>
    {% else %}
    <p>Noch keine Ordner vorhanden.</p>
    {% endif %}
</body>
</html>
"""


def extract_spotify_uri(text: str):
    """Extrahiert 'typ:id' aus einer open.spotify.com-URL oder einer spotify:-URI."""
    text = text.strip()

    match = URL_PATTERN.search(text)
    if match:
        content_type, content_id = match.groups()
        return f"{content_type}:{content_id}"

    match = URI_PATTERN.search(text)
    if match:
        content_type, content_id = match.groups()
        return f"{content_type}:{content_id}"

    return None


def sanitize_folder_name(name: str) -> str:
    """Erlaubt Unterordner (z.B. 'Kinder/Peter_und_der_Wolf'), verhindert aber
    Pfad-Traversal (../) und unerwuenschte Zeichen in jedem einzelnen Segment."""
    name = name.strip().replace("\\", "/")
    segments = [s for s in name.split("/") if s not in ("", ".", "..")]
    cleaned_segments = [re.sub(r"[^A-Za-z0-9._\-]", "_", s) for s in segments]
    return "/".join(cleaned_segments)


CATEGORY_PREFIXES = {
    "hoerbuch": "hoerbuch/spotify",
    "musik": "musik/spotify",
}


def list_existing_folders():
    """Listet alle vorhandenen Ordner/Unterordner unter AUDIOFOLDERS_BASE relativ auf, sortiert."""
    if not os.path.isdir(AUDIOFOLDERS_BASE):
        return []

    result = []
    for root, dirs, _files in os.walk(AUDIOFOLDERS_BASE):
        dirs.sort()
        for d in dirs:
            full_path = os.path.join(root, d)
            rel_path = os.path.relpath(full_path, AUDIOFOLDERS_BASE)
            result.append(rel_path)
    return sorted(result)


@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    success = False
    folder_value = ""
    url_value = ""
    category_value = "hoerbuch"

    if request.method == "POST":
        folder_input = request.form.get("folder", "")
        url_input = request.form.get("url", "")
        category_input = request.form.get("category", "hoerbuch")
        folder_value = folder_input
        url_value = url_input
        category_value = category_input

        prefix = CATEGORY_PREFIXES.get(category_input)
        folder_name = sanitize_folder_name(folder_input)
        uri = extract_spotify_uri(url_input)

        if not prefix:
            message = "Ungueltige Kategorie."
        elif not folder_name:
            message = "Bitte einen gueltigen Ordnernamen angeben."
        elif not uri:
            message = "Konnte keine Spotify-ID aus dem Link/URI extrahieren."
        else:
            full_relative_path = f"{prefix}/{folder_name}"
            target_dir = os.path.join(AUDIOFOLDERS_BASE, full_relative_path)
            try:
                os.makedirs(target_dir, exist_ok=True)
                uri_file = os.path.join(target_dir, "spotify.uri")
                with open(uri_file, "w") as f:
                    f.write(uri)
                message = f"Ordner '{full_relative_path}' angelegt mit Inhalt: {uri}"
                success = True
                folder_value = ""
                url_value = ""
            except OSError as exc:
                message = f"Fehler beim Anlegen: {exc}"

    return render_template_string(
        PAGE,
        message=message,
        success=success,
        folder=folder_value,
        url=url_value,
        category=category_value,
        existing_folders=list_existing_folders(),
    )


if __name__ == "__main__":
    # host="0.0.0.0" macht es im lokalen Netzwerk erreichbar, nicht nur von der Box selbst
    app.run(host="0.0.0.0", port=5050)
