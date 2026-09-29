#!/bin/bash

STATE=/home/pi/.config/go-librespot/state.json
BAK="$STATE.bak"

if [ -f "$STATE" ]; then
  if [ ! -s "$STATE" ] || ! tr -d '\000' < "$STATE" | cmp -s - "$STATE"; then
    echo "state.json beschaedigt"
    if [ -f "$BAK" ]; then cp "$BAK" "$STATE"; else rm -f "$STATE"; fi
  else
    cp "$STATE" "$BAK"   # intakten Stand sichern
  fi
fi
