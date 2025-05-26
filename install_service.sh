#!/bin/bash
# Script d'installation du service de scraping Anime-Sama

# Vérifier si l'utilisateur est root
if [[ $EUID -ne 0 ]]; then
   echo "Ce script doit être exécuté en tant que root" 
   exit 1
fi

# Définir le chemin d'installation
read -p "Entrez le chemin complet vers le dossier AnimeSamaScrapper: " INSTALL_PATH
if [ ! -d "$INSTALL_PATH" ]; then
    echo "Le dossier n'existe pas!"
    exit 1
fi

# Fonction pour détecter l'interpréteur Python avec les packages requis
detect_python() {
    local project_path="$1"
    local python_exec=""
    
    echo "Détection de l'environnement Python..."
    
    # Liste des packages requis
    local required_packages=("requests" "beautifulsoup4" "pymongo" "python-dotenv")
    
    # 1. Chercher un environnement virtuel dans le projet
    local venv_paths=("$project_path/venv" "$project_path/.venv" "$project_path/env" "$project_path/.env")
    
    for venv_path in "${venv_paths[@]}"; do
        # Chemins pour Linux
        if [ -f "$venv_path/bin/python" ]; then
            echo "Environnement virtuel trouvé: $venv_path (Linux)"
            python_exec="$venv_path/bin/python"
            break
        elif [ -f "$venv_path/bin/python3" ]; then
            echo "Environnement virtuel trouvé: $venv_path (Linux)"
            python_exec="$venv_path/bin/python3"
            break
        # Chemins pour Windows
        elif [ -f "$venv_path/Scripts/python.exe" ]; then
            echo "Environnement virtuel trouvé: $venv_path (Windows)"
            python_exec="$venv_path/Scripts/python.exe"
            break
        fi
    done
    
    # 2. Si pas d'environnement virtuel, utiliser le Python système
    if [ -z "$python_exec" ]; then
        echo "Aucun environnement virtuel trouvé, vérification du Python système..."
        for py_cmd in "python3" "python"; do
            if command -v "$py_cmd" &> /dev/null; then
                python_exec=$(command -v "$py_cmd")
                echo "Python système trouvé: $python_exec"
                break
            fi
        done
    fi
    
    # 3. Vérifier que Python est trouvé
    if [ -z "$python_exec" ]; then
        echo "Erreur: Aucun interpréteur Python trouvé!"
        exit 1
    fi
    
    # 4. Vérifier les packages requis
    echo "Vérification des packages requis..."
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! "$python_exec" -c "import ${package//-/_}" &> /dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    # 5. Si des packages manquent, proposer de les installer
    if [ ${#missing_packages[@]} -ne 0 ]; then
        echo "Packages manquants: ${missing_packages[*]}"
        echo "Installation des packages manquants..."
        
        # Essayer d'installer avec pip
        local pip_cmd=""
        if [ -f "$(dirname "$python_exec")/pip" ]; then
            pip_cmd="$(dirname "$python_exec")/pip"
        elif [ -f "$(dirname "$python_exec")/pip3" ]; then
            pip_cmd="$(dirname "$python_exec")/pip3"
        elif command -v pip3 &> /dev/null; then
            pip_cmd="pip3"
        elif command -v pip &> /dev/null; then
            pip_cmd="pip"
        else
            echo "Erreur: pip non trouvé. Veuillez installer les packages manuellement:"
            echo "  ${missing_packages[*]}"
            exit 1
        fi
        
        # Installer les packages manquants
        for package in "${missing_packages[@]}"; do
            echo "Installation de $package..."
            if ! "$pip_cmd" install "$package"; then
                echo "Erreur lors de l'installation de $package"
                exit 1
            fi
        done
    fi
    
    echo "Tous les packages requis sont disponibles."
    echo "Interpréteur Python sélectionné: $python_exec"
    
    # Retourner le chemin Python
    echo "$python_exec"
}

# Détecter l'interpréteur Python approprié
PYTHON_EXEC=$(detect_python "$INSTALL_PATH")

# Vérifier si nous sommes dans un environnement géré en externe et créer un venv si nécessaire
if [[ "$PYTHON_EXEC" != *"/venv/"* && "$PYTHON_EXEC" != *"/.venv/"* && "$PYTHON_EXEC" != *"/env/"* ]]; then
    echo "Aucun environnement virtuel détecté. Vérification de la nécessité d'en créer un..."
    
    # Vérifier si nous sommes dans un environnement géré en externe
    if "$PYTHON_EXEC" -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)" &> /dev/null; then
        echo "Environnement virtuel actif détecté."
    else
        echo "Tentative de création d'un environnement virtuel..."
        VENV_PATH="$INSTALL_PATH/.venv"
        
        # Vérifier si python3-venv est installé
        if ! dpkg -l python3-venv &> /dev/null && ! dpkg -l python3-virtualenv &> /dev/null; then
            echo "Installation de python3-venv..."
            apt-get update && apt-get install -y python3-venv python3-full
        fi
        
        # Créer l'environnement virtuel
        if "$PYTHON_EXEC" -m venv "$VENV_PATH"; then
            echo "Environnement virtuel créé avec succès à $VENV_PATH"
            # Mettre à jour le chemin Python
            if [ -f "$VENV_PATH/bin/python" ]; then
                PYTHON_EXEC="$VENV_PATH/bin/python"
            elif [ -f "$VENV_PATH/bin/python3" ]; then
                PYTHON_EXEC="$VENV_PATH/bin/python3"
            fi
            echo "Nouvel interpréteur Python sélectionné: $PYTHON_EXEC"
        else
            echo "Avertissement: Impossible de créer un environnement virtuel. Tentative de continuer avec Python système."
        fi
    fi
fi

# Définir l'utilisateur qui exécutera le service
read -p "Entrez le nom d'utilisateur qui exécutera le service: " SERVICE_USER
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "L'utilisateur $SERVICE_USER n'existe pas!"
    exit 1
fi

# Vérifier que le fichier requirements.txt existe et installer les dépendances si nécessaire
if [ -f "$INSTALL_PATH/requirements.txt" ]; then
    echo "Installation des dépendances depuis requirements.txt..."
    pip_cmd=""
    if [ -f "$(dirname "$PYTHON_EXEC")/pip" ]; then
        pip_cmd="$(dirname "$PYTHON_EXEC")/pip"
    elif [ -f "$(dirname "$PYTHON_EXEC")/pip3" ]; then
        pip_cmd="$(dirname "$PYTHON_EXEC")/pip3"
    elif command -v pip3 &> /dev/null; then
        pip_cmd="pip3"
    elif command -v pip &> /dev/null; then
        pip_cmd="pip"
    fi
    
    if [ -n "$pip_cmd" ]; then
        # Utilisation de --user pour éviter les problèmes d'environnement géré en externe
        # ou installation dans l'environnement virtuel si détecté
        if [[ "$PYTHON_EXEC" == *"/venv/"* || "$PYTHON_EXEC" == *"/.venv/"* || "$PYTHON_EXEC" == *"/env/"* ]]; then
            "$pip_cmd" install -r "$INSTALL_PATH/requirements.txt"
        else
            "$pip_cmd" install --user -r "$INSTALL_PATH/requirements.txt"
        fi
    fi
fi

# Mise à jour du fichier de service avec le bon interpréteur Python
sed -i "s|User=youruser|User=$SERVICE_USER|g" "$INSTALL_PATH/anime-sama-scraper.service"
sed -i "s|WorkingDirectory=/path/to/AnimeSamaScrapper|WorkingDirectory=$INSTALL_PATH|g" "$INSTALL_PATH/anime-sama-scraper.service"

# Échappement correct des caractères spéciaux dans le chemin Python
PYTHON_EXEC_ESCAPED=$(echo "$PYTHON_EXEC" | sed 's/[\/&]/\\&/g')
sed -i "s|ExecStart=/usr/bin/python3 /path/to/AnimeSamaScrapper/daily_scraper.py|ExecStart=$PYTHON_EXEC_ESCAPED $INSTALL_PATH/daily_scraper.py|g" "$INSTALL_PATH/anime-sama-scraper.service"

# Copier le fichier de service
cp "$INSTALL_PATH/anime-sama-scraper.service" /etc/systemd/system/

# Recharger systemd
systemctl daemon-reload

# Activer le service
systemctl enable anime-sama-scraper.service

# Démarrer le service
systemctl start anime-sama-scraper.service

# Vérifier l'état du service
systemctl status anime-sama-scraper.service

echo "Installation terminée. Le service est configuré pour démarrer automatiquement au boot."
echo "Vous pouvez vérifier les logs avec: journalctl -u anime-sama-scraper.service -f"
