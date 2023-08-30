#!/usr/bin/env bash

set -o errexit      # make your script exit when a command fails.
set -o nounset      # exit when your script tries to use undeclared variables.

case "$1" in
  train)
    python3.10 src/train.py
    ;;
  score)
    python3.10 src/ml_ranker.py
    ;;
  serve)
    python3.10 src/main.py
    ;;
  *)
    exec "$@"
esac