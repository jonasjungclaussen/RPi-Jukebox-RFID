#!/bin/bash
# Setzt go-librespot-Lautstärke (0–100)
PERCENT="$1"

# Wenn go-librespot gerade stoppt → nicht senden
if ! systemctl is-active --quiet go-librespot; then
    exit 0
fi

# Wenn kein Wert übergeben wurde → abbrechen
[ -z "$PERCENT" ] && exit 0

# Lautstärke setzen
curl -s -X POST http://localhost:3678/player/volume \
  -H "Content-Type: application/json" \
  -d "{\"volume\": $PERCENT}"
