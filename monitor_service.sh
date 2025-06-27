#!/bin/bash

# Script de surveillance du service AnimeSamaScraper (Linux)
# À exécuter régulièrement pour vérifier l'état du service

# Options
DETAILED=false
RESTART_IF_DOWN=false
EMAIL_ALERT=false

# Analyse des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --detailed|-d)
            DETAILED=true
            shift
            ;;
        --restart|-r)
            RESTART_IF_DOWN=true
            shift
            ;;
        --email|-e)
            EMAIL_ALERT=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --detailed, -d    Affichage détaillé"
            echo "  --restart, -r     Redémarrer le service s'il est arrêté"
            echo "  --email, -e       Envoyer une alerte email en cas de problème"
            echo "  --help, -h        Afficher cette aide"
            exit 0
            ;;
        *)
            echo "Option inconnue: $1"
            echo "Utilisez --help pour voir les options disponibles"
            exit 1
            ;;
    esac
done

SERVICE_NAME="anime-sama-scraper"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== SURVEILLANCE ANIMESAMASCRAPER - $TIMESTAMP ==="

# Variables pour le résumé
SERVICE_OK=true
HAS_ERRORS=false
DISK_OK=true
NETWORK_OK=true

# 1. Vérifier le statut du service systemd
echo ""
echo "[CHECK 1] Statut du service systemd:"

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service '$SERVICE_NAME' fonctionne correctement"
    SERVICE_OK=true
elif systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "⚠️  Service '$SERVICE_NAME' installé mais arrêté"
    SERVICE_OK=false
    
    if [ "$RESTART_IF_DOWN" = true ]; then
        echo "🔄 Tentative de redémarrage..."
        if sudo systemctl start "$SERVICE_NAME"; then
            sleep 3
            if systemctl is-active --quiet "$SERVICE_NAME"; then
                echo "✅ Service redémarré avec succès"
                SERVICE_OK=true
            else
                echo "❌ Échec du redémarrage"
                SERVICE_OK=false
            fi
        else
            echo "❌ Erreur lors du redémarrage"
            SERVICE_OK=false
        fi
    fi
else
    echo "❌ Service '$SERVICE_NAME' non trouvé ou non installé"
    SERVICE_OK=false
fi

# 2. Vérifier les logs récents
echo ""
echo "[CHECK 2] Analyse des logs récents:"

TODAY=$(date '+%Y%m%d')
LOG_FILE="logs/anime_sama_scraper_$TODAY.log"

if [ -f "$LOG_FILE" ]; then
    if [ -s "$LOG_FILE" ]; then
        # Chercher les dernières exécutions et erreurs
        LAST_EXECUTIONS=$(grep "DÉBUT DU PROCESSUS" "$LOG_FILE" | tail -3)
        RECENT_ERRORS=$(grep "ERROR" "$LOG_FILE" | tail -5)
        RECENT_WARNINGS=$(grep "WARNING" "$LOG_FILE" | tail -5)
        
        echo "📊 Dernières exécutions:"
        if [ -n "$LAST_EXECUTIONS" ]; then
            echo "$LAST_EXECUTIONS" | while read -r line; do
                echo "   $line"
            done
        else
            echo "   Aucune exécution trouvée aujourd'hui"
        fi
        
        if [ -n "$RECENT_ERRORS" ]; then
            echo "⚠️  Erreurs récentes:"
            echo "$RECENT_ERRORS" | while read -r line; do
                echo "   $line"
            done
            HAS_ERRORS=true
        else
            echo "✅ Aucune erreur récente"
            HAS_ERRORS=false
        fi
        
        if [ "$DETAILED" = true ] && [ -n "$RECENT_WARNINGS" ]; then
            echo "⚠️  Avertissements récents:"
            echo "$RECENT_WARNINGS" | while read -r line; do
                echo "   $line"
            done
        fi
    else
        echo "⚠️  Fichier de log vide"
        HAS_ERRORS=false
    fi
else
    echo "⚠️  Fichier de log d'aujourd'hui non trouvé: $LOG_FILE"
    HAS_ERRORS=false
fi

# 3. Vérifier l'espace disque
echo ""
echo "[CHECK 3] Espace disque:"

DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
AVAILABLE_GB=$(df -h . | tail -1 | awk '{print $4}')

echo "💾 Espace disponible: $AVAILABLE_GB (${DISK_USAGE}% utilisé)"

if [ "$DISK_USAGE" -gt 90 ]; then
    echo "⚠️  ATTENTION: Espace disque critique!"
    DISK_OK=false
elif [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  Espace disque en diminution"
    DISK_OK=true
else
    echo "✅ Espace disque suffisant"
    DISK_OK=true
fi

# 4. Vérifier la connectivité réseau
echo ""
echo "[CHECK 4] Connectivité réseau:"

if ping -c 1 -W 5 anime-sama.fr >/dev/null 2>&1; then
    echo "✅ Connexion vers anime-sama.fr OK"
    NETWORK_OK=true
else
    echo "❌ Impossible de joindre anime-sama.fr"
    NETWORK_OK=false
fi

# 5. Vérifier les processus Python liés
echo ""
echo "[CHECK 5] Processus Python:"

PYTHON_PROCESSES=$(pgrep -f "python.*daily_scraper\|python.*main\.py" | wc -l)
if [ "$PYTHON_PROCESSES" -gt 0 ]; then
    echo "✅ $PYTHON_PROCESSES processus Python détectés"
    if [ "$DETAILED" = true ]; then
        echo "Processus actifs:"
        ps aux | grep -E "python.*(daily_scraper|main\.py)" | grep -v grep | while read -r line; do
            echo "   $line"
        done
    fi
else
    echo "⚠️  Aucun processus Python détecté"
fi

# 6. Résumé global
echo ""
echo "[RÉSUMÉ] État global du système:"

if [ "$SERVICE_OK" = true ] && [ "$HAS_ERRORS" = false ] && [ "$DISK_OK" = true ] && [ "$NETWORK_OK" = true ]; then
    echo "🎉 TOUT VA BIEN - Système opérationnel"
    EXIT_CODE=0
else
    echo "⚠️  PROBLÈMES DÉTECTÉS - Attention requise"
    echo "   - Service OK: $SERVICE_OK"
    echo "   - Pas d'erreurs: $([ "$HAS_ERRORS" = false ] && echo true || echo false)"
    echo "   - Disque OK: $DISK_OK"
    echo "   - Réseau OK: $NETWORK_OK"
    EXIT_CODE=1
    
    # Actions recommandées
    echo ""
    echo "[ACTIONS RECOMMANDÉES]:"
    
    if [ "$SERVICE_OK" = false ]; then
        echo "• Redémarrer le service: sudo systemctl start $SERVICE_NAME"
        echo "• Vérifier les logs: journalctl -u $SERVICE_NAME -f"
    fi
    
    if [ "$HAS_ERRORS" = true ]; then
        echo "• Analyser les erreurs dans les logs: tail -100 $LOG_FILE"
        echo "• Vérifier la configuration de la base de données"
    fi
    
    if [ "$DISK_OK" = false ]; then
        echo "• Nettoyer l'espace disque: sudo apt clean && sudo journalctl --vacuum-time=7d"
        echo "• Archiver les anciens logs: find logs/ -name '*.log' -mtime +30 -exec gzip {} \\;"
    fi
    
    if [ "$NETWORK_OK" = false ]; then
        echo "• Vérifier la connexion Internet: ping google.com"
        echo "• Vérifier si anime-sama.fr est accessible depuis un navigateur"
    fi
fi

echo ""
echo "=== FIN DE LA SURVEILLANCE ==="

# Option: envoyer une alerte email (nécessite configuration de mail/sendmail)
if [ "$EMAIL_ALERT" = true ] && [ "$EXIT_CODE" -ne 0 ]; then
    echo ""
    echo "📧 Alerte email activée"
    # Exemple d'implémentation avec mail (si configuré):
    # echo "Problème détecté sur AnimeSamaScraper à $(date)" | mail -s "Alert AnimeSamaScraper" admin@example.com
    echo "   (Configuration mail nécessaire pour l'envoi d'alertes)"
fi

exit $EXIT_CODE
