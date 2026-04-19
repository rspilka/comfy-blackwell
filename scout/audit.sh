#!/bin/bash

# Konfiguration der Pfade auf der großen NVMe
BIG_DISK_BASE="/opt/scoutdata"
export TMPDIR="$BIG_DISK_BASE/tmp"
export DOCKER_SCOUT_CACHE_DIR="$BIG_DISK_BASE/cache"

# Farben
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verzeichnisse vorbereiten
mkdir -p "$TMPDIR"
mkdir -p "$DOCKER_SCOUT_CACHE_DIR"

echo -e "${YELLOW}--- Starte Heavy-Duty Audit (Sequenziell & Eindeutig) ---${NC}"
echo -e "Nutze Speicherplatz auf: ${BLUE}/windata${NC}\n"

# Eindeutige Images anhand der ID sammeln, um doppelte Scans zu vermeiden
UNIQUE_IMAGE_LIST=$(docker images --format '{{.ID}}\t{{.Repository}}:{{.Tag}}' | grep -v "<none>" | sort -u -k1,1 | awk '{print $2}')

DECLARE_RESULTS=()

for img in $UNIQUE_IMAGE_LIST; do
    echo -e "📦 Verarbeite: ${YELLOW}$img${NC}"
    
    # 1. Quickview für die Live-Ansicht am Terminal
    docker scout quickview "$img"
    
    # 2. Daten für die Zusammenfassung extrahieren
    # Wir nutzen hier die cves-Zusammenfassung für präzises Parsing
    STATS=$(docker scout cves "$img" --format summary 2>/dev/null)
    
    CRIT=$(echo "$STATS" | grep -oE '[0-9]+ critical' | awk '{print $1}')
    HIGH=$(echo "$STATS" | grep -oE '[0-9]+ high' | awk '{print $1}')
    MED=$(echo "$STATS" | grep -oE '[0-9]+ medium' | awk '{print $1}')
    LOW=$(echo "$STATS" | grep -oE '[0-9]+ low' | awk '{print $1}')

    # Defaults setzen
    CRIT=${CRIT:-0}; HIGH=${HIGH:-0}; MED=${MED:-0}; LOW=${LOW:-0}

    # Status-Logik
    if [ "$CRIT" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
        STATUS="${RED}[CRIT/HIGH]${NC}"
    elif [ "$MED" -gt 0 ] || [ "$LOW" -gt 0 ]; then
        STATUS="${YELLOW}[LOW/MED]  ${NC}"
    else
        STATUS="${GREEN}[CLEAN]    ${NC}"
    fi

    DECLARE_RESULTS+=("$STATUS - $img (${RED}${CRIT}C ${YELLOW}${HIGH}H ${BLUE}${MED}M ${NC}${LOW}L)")
    
    # Zwischenreinigung des Temp-Ordners nach jedem Image
    rm -rf "$TMPDIR"/*
    echo -e "--------------------------------------------------------\n"
done

# --- FINALE ZUSAMMENFASSUNG ---
echo -e "${YELLOW}========================================================${NC}"
echo -e "${YELLOW}           DETAILLIERTE AUDIT-ZUSAMMENFASSUNG${NC}"
echo -e "${YELLOW}========================================================${NC}"
for res in "${DECLARE_RESULTS[@]}"; do
    echo -e "$res"
done
echo -e "${YELLOW}========================================================${NC}"

# Optional: Cache am Ende leeren, wenn man den Platz sofort wieder will
# rm -rf "$BIG_DISK_BASE"
