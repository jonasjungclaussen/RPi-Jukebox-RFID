#!/bin/bash
ACTION="$1"

post_player_command() {
  curl -fsS --connect-timeout 2 --max-time 30 -X POST "http://localhost:3678$1" -o /dev/null
}

case "$ACTION" in
  Next)
    post_player_command /player/next
    ;;
  Previous)
    post_player_command /player/prev
    ;;
  PlayPause)
    post_player_command /player/playpause
    ;;
  *)
    exit 1
    ;;
esac
