# Phoniebox + Spotify (go-librespot) – Setup Guide

Reference for a complete rebuild. MPD remains unchanged for all regular
cards; go-librespot runs in parallel and is only activated for Spotify cards.

## 1. Preparation

- Register your own Spotify Developer app (client ID/secret) in the Spotify
  Developer Dashboard.
- Check architecture:
  ```bash
  dpkg --print-architecture
  ```
  On a 32-bit OS (armhf) on Raspberry Pi: use the **`armv6_rpi`** binary
  (ARMv6 binaries also run on ARMv7 hardware).
- Determine the ALSA device:
  ```bash
  aplay -l
  ```
  Note the correct device string (e.g. `hw:0,0`, or `plughw:0,0` if the
  hardware device doesn't support the format directly).

## 2. Install & configure go-librespot

Download the binary, make it executable, place it at a sensible path, e.g.
`/home/pi/go-librespot/go-librespot`.

Example `config.yml`:

```yaml
# --- Spotify Login ---
credentials:
  type: interactive
  client_id: "..."
  client_secret: "..."

# --- Device info ---
device:
  name: "phoniebox"
  type: "speaker"
  volume: 30

# --- Audio backend ---
audio:
  backend: "alsa"
  format: "S16"
  device: "hw:0,0"   # or plughw:0,0 if needed

# --- Cache & storage ---
cache:
  enabled: true
  dir: "/var/cache/librespot"

# --- Logging ---
log:
  level: "info"

# --- Server (control API) ---
server:
  enabled: true
  port: 3678
```

**Important:**
- The config key is `credentials:`, **not** `auth:`.
- Use `type: interactive` (OAuth), **not** `client-credentials` – the latter
  has no user context and cannot start playback.

### One-time OAuth login

1. Start go-librespot, open the login link from the console.
2. If go-librespot runs on a different device than your browser: after the
   redirect fails, copy the complete `localhost:<port>/callback?...` URL
   from the browser's address bar and call it **from the Phoniebox itself**:
   ```bash
   curl "http://localhost:<port>/callback?code=...&state=..."
   ```
   Alternative: set up SSH port forwarding, then open the link normally in
   your local browser:
   ```bash
   ssh -L <port>:localhost:<port> pi@<phoniebox-ip>
   ```
3. Confirm successful login in the logs; credentials are stored in
   `state.json` in the cache directory.

### Testing

```bash
curl -X POST http://127.0.0.1:3678/player/load \
  -H "Content-Type: application/json" \
  -d '{"uri": "spotify:album:XXXXXXXXXXXX", "play": true}'
```
Let it run for several minutes and check whether the next track starts
automatically.

Control endpoints:

| Purpose | Endpoint |
|---|---|
| Load album/track and play | `POST /player/load` (body: `uri`, `play`, optional `shuffle`) |
| Toggle play/pause | `POST /player/play-pause` |
| Pause | `POST /player/pause` |
| Resume | `POST /player/resume` |
| Next track | `POST /player/next` |
| Previous track | `POST /player/prev` |

## 3. Systemd services

Once:
```bash
loginctl enable-linger pi
```

- **go-librespot.service** – user service (`~/.config/systemd/user/`)
- **mpd-volume-sync.service** – user service; listens for `idle mixer`
  events from MPD and mirrors volume changes to the go-librespot API
- **spotify-add.service** – system service (`/etc/systemd/system/`), see
  example below

After creating each one:
```bash
sudo systemctl daemon-reload   # for system services
systemctl --user daemon-reload # for user services
systemctl enable --now <service>
```

Example `spotify-add.service`:
```ini
[Unit]
Description=Spotify Add web tool for Phoniebox
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/spotify_add.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Always stop cleanly, never `kill -9`** (otherwise the state file can get
corrupted, e.g. `state.json` with an invalid `\x00` character):
```bash
systemctl --user stop go-librespot
```

## 4. Integration scripts for Phoniebox

### `play_spotify.sh`
1. Stop MPD
2. Read the current MPD volume (used as the starting volume for Spotify)
3. Send volume + album to go-librespot via `POST /player/load`

### `spotify_transport.sh`
Play/pause/next/prev via the go-librespot API endpoints
(`/player/play-pause`, `/player/next`, `/player/prev`).

### Patch in `rfid_trigger_play.sh`
After the `$FOLDER` is determined: check whether a `spotify.uri` file exists
in the folder. If so, call `play_spotify.sh` instead of the normal MPD logic.

### Patch in `playout_controls.sh`
At the three spots `playernext` / `playerprev` / `playerpause`, additionally
call `spotify_transport.sh` in parallel.

## 5. Deploy spotify_add.py

- Copy the file to the box, adjust the `AUDIOFOLDERS_BASE` path inside it
- Install Flask:
  ```bash
  pip3 install flask==1.1.4
  ```
- Start it via `spotify-add.service`
- Test in the browser: `http://<pi-ip>:5050`

Feature overview of the tool:
- Spotify links (album/playlist/track, including `?si=` parameters or
  `intl-xx/` prefixes) are parsed via regex and converted to `type:id`
- Radio buttons for category **Audiobook** (`hoerbuch/spotify/…`) or
  **Music** (`musik/spotify/…`)
- The folder name is appended to the category path; subfolders (`/` in
  the field) are supported
- Path traversal protection: each path segment is sanitized individually
  (no `..`, only allowed characters)
- A list of all existing folders/subfolders is shown below the form

## 6. Create a test card & end-to-end test

1. Use the `spotify_add.py` form to create a test folder with a Spotify link
2. In the regular Phoniebox web UI, assign an RFID card to that folder
3. Scan the card → check:
   - MPD stops
   - go-librespot takes over and starts playback
   - The album plays through, including automatic track transitions
   - Volume sync works
   - GPIO buttons (play/pause/next/prev) work

## Known pitfalls

- **Config key:** `credentials:`, not `auth:`
- **Auth type:** `interactive` for playback, not `client-credentials`
  (no user context, playback not possible)
- **API endpoint:** `/player/load`, not `/player/play`
- **Shutdown:** always use `SIGTERM`/clean stop, never `kill -9`
  (risk of state file corruption)
- **ALSA `Invalid argument` on `snd_pcm_open`:** usually a wrong device
  string, or MPD still holding the device exclusively – check `aplay -l`,
  try `plughw:` instead of `hw:` if needed
- **32-bit OS:** despite a 64-bit-capable CPU, the `armv6_rpi` binary may
  be required – check `dpkg --print-architecture` beforehand
- **Known, unresolved librespot-ecosystem bug** (`context is not
  available`, `ResourceExhausted`) affects the Rust codebase (spotifyd,
  librespot-org); go-librespot is an independent Go reimplementation and
  not currently known to be affected – hence the recommended choice over
  spotifyd
