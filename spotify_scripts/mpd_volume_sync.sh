#!/bin/bash

while true; do
    # Wait for an MPD mixer event; mpc idle blocks until the event occurs.
    if ! mpc idle mixer >/dev/null; then
        sleep 1
        continue
    fi

    # aktuelle MPD-Lautstärke holen
    VOL=$(printf 'status\nclose\n' | nc -w 1 localhost 6600 2>/dev/null | awk -F': ' '/^volume:/ { gsub(/\r/, "", $2); print $2; exit }')

    # nur senden, wenn ein gültiger numerischer Wert vorliegt
    if [[ "$VOL" =~ ^-?[0-9]+([.][0-9]+)?$ ]]; then
        curl -fsS --connect-timeout 2 --max-time 5 -X POST http://localhost:3678/player/volume \
            -H "Content-Type: application/json" \
            --data "{\"volume\": $VOL}" >/dev/null
    fi
done
