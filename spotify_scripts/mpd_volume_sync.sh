#!/bin/bash

while true; do
    # blockiert, bis MPD ein "mixer"-Event meldet (Lautstärkeänderung)
    echo -e "idle mixer\nclose" | nc localhost 6600 > /dev/null

    # aktuelle MPD-Lautstärke holen
    VOL=$(echo -e "status\nclose" | nc -w 1 localhost 6600 | grep -o -P '(?<=volume: ).*')

    # wenn Wert vorhanden → an go-librespot senden
    if [ -n "$VOL" ]; then
        curl -s -X POST http://localhost:3678/player/volume \
            -H "Content-Type: application/json" \
            -d "{\"volume\": $VOL}"
    fi
done
