#!/usr/bin/env bash
# ==============================================================================
# GEN PEN: Gunluk Gecici Medya Dosyasi Temizleme Scripti
# Pardus 23 GNU/Linux
# ==============================================================================

set -euo pipefail

CACHE_DIR="${HOME}/.cache/genpen/incoming"
LOG_TAG="genpen-cleaner"

if [ -d "${CACHE_DIR}" ]; then
    logger -t "${LOG_TAG}" "Gen Pen gecici onbellegi kontrol ediliyor: ${CACHE_DIR}"
    
    # 24 saatten (1 gun) eski olan gecici klasor ve dosyalari bul ve sil
    find "${CACHE_DIR}" -mindepth 1 -maxdepth 1 -type d -mtime +0 -exec rm -rf {} +
    
    logger -t "${LOG_TAG}" "Dunden kalan gecici cizim ve fotograflar basariyla temizlendi."
else
    logger -t "${LOG_TAG}" "Onbellek dizini henuz olusmamis, islem atlandi."
fi
