#!/bin/bash

while true; do
    # blockiert, bis MPD ein "mixer"-Event meldet (Lautstärkeänderung)
    printf 'idle mixer\nclose\n' | nc -w 1 localhost 6600 >/dev/null 2>&1 || continue

    # aktuelle MPD-Lautstärke holen
    VOL=$(printf 'status\nclose\n' | nc -w 1 localhost 6600 2>/dev/null | awk -F': ' '/^volume:/ { gsub(/\r/, "", $2); print $2; exit }')

    # nur senden, wenn ein gültiger numerischer Wert vorliegt
    if [[ "$VOL" =~ ^-?[0-9]+([.][0-9]+)?$ ]]; then
        curl -fsS -X POST http://localhost:3678/player/volume \
            -H "Content-Type: application/json" \
            --data "{\"volume\": $VOL}"
    fi
done
