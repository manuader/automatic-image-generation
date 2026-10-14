#!/bin/zsh
# Batch de fisu-v2-blue (E14b B9+B14) con Gemini. Antes: elegí el modelo Flash en el Chrome aislado de Gemini.
cd ~/Desktop/projects/automatic-image-generation
mkdir -p projects/fisu-v2-blue/state
# Abre (o reusa) el Chrome aislado de Gemini. No gasta cuota.
.venv/bin/python generate.py --engine gemini --launch
read "?En esa ventana: iniciá sesión si te la pide y elegí el modelo Flash. Después apretá Enter… "
for vuelta in {1..30}; do
  caffeinate -is .venv/bin/python supervisor.py --project fisu-v2-blue --engines gemini
  code=$?
  [[ $code -eq 0 || $code -eq 1 || $code -eq 130 ]] && break
  echo "$(date '+%F %T') el supervisor salió con $code; relanzo en 60 s (vuelta $vuelta)" | tee -a projects/fisu-v2-blue/state/supervisor.log
  rm -f projects/fisu-v2-blue/state/supervisor.pid
  sleep 60
done
echo "Terminado (código $code). Imágenes en projects/fisu-v2-blue/output/"
