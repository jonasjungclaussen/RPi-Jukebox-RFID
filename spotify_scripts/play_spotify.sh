#!/bin/bash
CONTENT_ID="$1"

# MPD-Lautstärke auslesen
START_VOLUME=$(echo -e "status\nclose" | nc -w 1 localhost 6600 | grep -o -P '(?<=volume: ).*')
START_VOLUME="${START_VOLUME:-30}"

# MPD stoppen
echo -e "stop\nclose" | nc -w 1 localhost 6600

# Lautstärke setzen
curl -s -X POST http://localhost:3678/player/volume \
  -H "Content-Type: application/json" \
  -d "{\"volume\": $START_VOLUME}"

# Spotify-URI starten
curl -s -X POST http://localhost:3678/player/play \
  -H "Content-Type: application/json" \
  -d "{\"uri\": \"spotify:$CONTENT_ID\"}"

echo "spotify" > /home/pi/RPi-Jukebox-RFID/state/player
