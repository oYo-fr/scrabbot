#!/bin/bash

# Script pour lancer Scrabbot en mode test local

set -e

WORKDIR="/workspaces/scrabbot"
WEB_DIR="$WORKDIR/build/web"
WEB_PORT=8080

echo "🎮 Scrabbot - Démarrage du jeu"
echo "================================"

# Vérifier que nous sommes dans le bon répertoire
cd "$WORKDIR"

# Créer le dossier web s'il n'existe pas
mkdir -p "$WEB_DIR"

# Vérifier que l'interface web existe
if [ ! -f "$WEB_DIR/index.html" ]; then
    echo "❌ Interface web manquante dans $WEB_DIR/index.html"
    exit 1
fi

# Fonction pour nettoyer les processus en arrière-plan
cleanup() {
    echo ""
    echo "🧹 Nettoyage des processus..."
    
    # Tuer le serveur web s'il existe
    if [ ! -z "$WEB_PID" ]; then
        kill $WEB_PID 2>/dev/null || true
        echo "   Serveur web arrêté"
    fi
    
    # Tuer les autres serveurs Python sur le port 8080
    pkill -f "python.*http.server.*8080" 2>/dev/null || true
    
    echo "✅ Nettoyage terminé"
    exit 0
}

# Configurer le nettoyage sur interruption
trap cleanup SIGINT SIGTERM

# Vérifier si le port est déjà utilisé
if lsof -i:$WEB_PORT >/dev/null 2>&1; then
    echo "⚠️  Port $WEB_PORT déjà utilisé, tentative d'arrêt des processus..."
    pkill -f "python.*http.server.*$WEB_PORT" 2>/dev/null || true
    sleep 2
fi

# Démarrer le serveur web en arrière-plan
echo "🌐 Démarrage du serveur web sur le port $WEB_PORT..."
cd "$WEB_DIR"
python3 -m http.server $WEB_PORT > /dev/null 2>&1 &
WEB_PID=$!

# Attendre que le serveur démarre
sleep 2

# Vérifier que le serveur fonctionne
if ! curl -s http://localhost:$WEB_PORT >/dev/null; then
    echo "❌ Impossible de démarrer le serveur web"
    cleanup
fi

echo "✅ Serveur web démarré (PID: $WEB_PID)"
echo "🔗 Interface disponible sur: http://localhost:$WEB_PORT"

# Retourner au répertoire de travail
cd "$WORKDIR"

# Configurer l'environnement pour le bot
export GODOT_WEB_URL="http://localhost:$WEB_PORT"
export TELEGRAM_BOT_TOKEN="test-token"

echo ""
echo "🤖 Démarrage du test du bot..."
echo "==============================="

# Lancer le test du bot
python3 test_local.py

# Le nettoyage sera appelé automatiquement à la fin
