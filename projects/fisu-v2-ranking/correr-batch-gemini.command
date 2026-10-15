#!/bin/zsh
# Batch de fisu-v2-ranking (ícono del Ranking, D8) con Gemini. Antes: el Chrome aislado de Gemini logueado y en modelo Flash.
cd ~/Desktop/projects/automatic-image-generation
mkdir -p projects/fisu-v2-ranking/state
for vuelta in {1..3}; do
  caffeinate -is .venv/bin/python supervisor.py --project fisu-v2-ranking --engines gemini
  code=$?
  [[ $code -eq 0 || $code -eq 1 || $code -eq 130 ]] && break
  echo "$(date '+%F %T') el supervisor salió con $code; relanzo en 60 s (vuelta $vuelta)" | tee -a projects/fisu-v2-ranking/state/supervisor.log
  rm -f projects/fisu-v2-ranking/state/supervisor.pid
  sleep 60
done
echo "Terminado (código $code). Imágenes en projects/fisu-v2-ranking/output/" | tee -a projects/fisu-v2-ranking/state/supervisor.log
