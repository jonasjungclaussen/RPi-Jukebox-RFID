#!/bin/bash
ACTION="$1"

case "$ACTION" in
  Next)
    curl -s -X POST http://localhost:3678/player/next
    ;;
  Previous)
    curl -s -X POST http://localhost:3678/player/prev
    ;;
  PlayPause)
    curl -s -X POST http://localhost:3678/player/playpause
    ;;
  *)
    exit 1
    ;;
esac
