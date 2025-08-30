# 📚 Spécifications - Système de Dictionnaires Multilingues et Algorithmes de Recherche

## 🎯 Objectif du Ticket

Développer un système complet de dictionnaires multilingues pour le projet Scrabbot avec validation d'accès depuis le serveur web et l'application Godot.

## 🔧 Tests Unitaires Requis

### Tests de Validation d'Accès aux Dictionnaires

#### 1. **Tests Serveur Web (Python)**
- **Test d'accès basique** : Vérifier qu'un mot quelconque peut être récupéré depuis la base SQLite
- **Test de performance** : Mesurer le temps de réponse pour la recherche d'un mot
- **Test de validation** : Confirmer qu'un mot valide retourne `True` et un mot invalide retourne `False`
- **Test de caractères spéciaux** : Vérifier la gestion des accents, cédilles, etc.
- **Test de connexion** : Valider l'établissement et la fermeture de connexion à la base SQLite

```python
def test_acces_dictionnaire_serveur():
    """Test que le serveur web peut accéder à un mot du dictionnaire"""
    dictionnaire = DictionnaireFR()
    assert dictionnaire.valider_mot("CHAT") == True
    assert dictionnaire.valider_mot("INEXISTANT") == False
    assert dictionnaire.obtenir_definition("CHAT") is not None
```

#### 2. **Tests Application Godot (GDScript)**
- **Test d'accès API** : Vérifier l'appel HTTP vers le serveur de validation
- **Test de réponse JSON** : Valider le format de réponse du serveur
- **Test de timeout** : Gérer les cas de non-réponse du serveur
- **Test hors ligne** : Fallback en cas d'indisponibilité du serveur

```gdscript
func test_acces_dictionnaire_godot():
    # Test d'accès à un mot via l'API
    var result = await api_dictionnaire.valider_mot("CHAT")
    assert(result.valide == true)
    assert(result.definition != "")
```

#### 3. **Tests d'Intégration**
- **Test bout-en-bout** : Godot → API → Serveur → SQLite → Réponse
- **Test de charge** : Validation simultanée de multiple mots
- **Test de synchronisation** : Cohérence entre les deux systèmes

## 📦 Structure du Repository Final

### 1. **Dictionnaires Français (Phase 1)**

#### Sources de Données
- **ODS (Officiel Du Scrabble)** : Dictionnaire officiel français
- **Conjugaisons** : Toutes les formes verbales autorisées
- **Dérivés** : Noms dérivés, adjectifs, adverbes
- **Pluriels** : Formes plurielles standard et irrégulières
- **Définitions** : Issues du Larousse, Wiktionnaire

#### Contenu Requis
```
Mot | Définition | Catégorie | Points | Validité_Scrabble
CHAT | Mammifère domestique félin | nom | 9 | true
CHATS | Pluriel de chat | nom | 14 | true
CHATTER | Communiquer par chat en ligne | verbe | 19 | false
```

### 2. **Dictionnaires Anglais (Phase 2)**

#### Sources de Données
- **SOWPODS** : Standard pour tournois internationaux
- **TWL (Tournament Word List)** : Liste nord-américaine
- **Wiktionary** : Définitions et étymologies
- **Conjugaisons et dérivés** anglais

## 🗄️ Formats de Stockage

### 1. **Format CSV (Source de Vérité)**

#### Structure `dictionnaire_fr.csv`
```csv
mot,definition,categorie_grammaticale,points,valide_scrabble,longueur,premiere_lettre,derniere_lettre,voyelles,consonnes,date_ajout,source
CHAT,"Mammifère domestique félin",nom,9,true,4,C,T,A,CHT,2024-01-15,ODS
CHATS,"Pluriel de chat",nom,14,true,5,C,S,A,CHTS,2024-01-15,ODS
CHIEN,"Mammifère domestique canin",nom,10,true,5,C,N,IE,CHN,2024-01-15,ODS
```

#### Structure `dictionnaire_en.csv`
```csv
word,definition,part_of_speech,points,scrabble_valid,length,first_letter,last_letter,vowels,consonants,date_added,source
CAT,"Small domesticated carnivorous mammal",noun,5,true,3,C,T,A,CT,2024-01-15,SOWPODS
CATS,"Plural of cat",noun,6,true,4,C,S,A,CTS,2024-01-15,SOWPODS
DOG,"Domesticated carnivorous mammal",noun,5,true,3,D,G,O,DG,2024-01-15,SOWPODS
```

### 2. **Format SQLite (Base de Données)**

#### Schema `dictionnaire.db`

```sql
-- Table des dictionnaires disponibles
CREATE TABLE dictionnaires (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_langue CHAR(2) NOT NULL, -- 'fr', 'en'
    nom TEXT NOT NULL,
    version TEXT NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL
);

-- Table principale des mots français
CREATE TABLE mots_fr (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mot TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    categorie_grammaticale TEXT,
    points INTEGER NOT NULL,
    valide_scrabble BOOLEAN DEFAULT true,
    longueur INTEGER NOT NULL,
    premiere_lettre CHAR(1) NOT NULL,
    derniere_lettre CHAR(1) NOT NULL,
    voyelles TEXT,
    consonnes TEXT,
    date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL,
    UNIQUE(mot)
);

-- Table principale des mots anglais
CREATE TABLE mots_en (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    part_of_speech TEXT,
    points INTEGER NOT NULL,
    scrabble_valid BOOLEAN DEFAULT true,
    length INTEGER NOT NULL,
    first_letter CHAR(1) NOT NULL,
    last_letter CHAR(1) NOT NULL,
    vowels TEXT,
    consonants TEXT,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL,
    UNIQUE(word)
);

-- Index pour optimiser les recherches
CREATE INDEX idx_mots_fr_mot ON mots_fr(mot);
CREATE INDEX idx_mots_fr_longueur ON mots_fr(longueur);
CREATE INDEX idx_mots_fr_premiere_lettre ON mots_fr(premiere_lettre);
CREATE INDEX idx_mots_en_word ON mots_en(word);
CREATE INDEX idx_mots_en_length ON mots_en(length);
CREATE INDEX idx_mots_en_first_letter ON mots_en(first_letter);

-- Vue pour recherche rapide français
CREATE VIEW recherche_fr AS 
SELECT mot, definition, points, valide_scrabble, longueur 
FROM mots_fr 
WHERE valide_scrabble = true;

-- Vue pour recherche rapide anglais
CREATE VIEW recherche_en AS 
SELECT word, definition, points, scrabble_valid, length 
FROM mots_en 
WHERE scrabble_valid = true;
```

### 3. **Scripts de Conversion**

#### Script `csv_to_sqlite.py`
```python
#!/usr/bin/env python3
"""
Script de conversion CSV → SQLite pour les dictionnaires Scrabbot
Usage: python csv_to_sqlite.py dictionnaire_fr.csv dictionnaire.db
"""

import sqlite3
import csv
import argparse
from datetime import datetime

def convertir_csv_vers_sqlite(fichier_csv: str, fichier_db: str, langue: str):
    """Convertit un fichier CSV en base SQLite"""
    # Implémentation de la conversion
    pass

if __name__ == "__main__":
    # Point d'entrée du script
    pass
```

## 🛠️ Architecture Technique

### 1. **Structure des Répertoires**
```
scrabbot/
├── data/
│   ├── dictionnaires/
│   │   ├── sources/          # Fichiers CSV sources
│   │   │   ├── dictionnaire_fr.csv
│   │   │   └── dictionnaire_en.csv
│   │   ├── databases/        # Bases SQLite
│   │   │   ├── french.db
│   │   │   └── english.db
│   │   └── scripts/          # Scripts de conversion
│   │       ├── csv_to_sqlite.py
│   │       ├── update_dictionnaire.py
│   │       └── validate_data.py
├── bot/
│   ├── services/
│   │   ├── dictionnaire_service.py    # Service de validation
│   │   └── api_dictionnaire.py        # API REST
├── shared/
│   ├── models/
│   │   └── dictionnaire.py            # Modèles de données
└── tests/
    ├── dictionnaires/
    │   ├── test_acces_serveur.py       # Tests serveur web
    │   ├── test_acces_godot.py         # Tests Godot/API
    │   └── test_integration.py         # Tests d'intégration
```

### 2. **API REST pour Godot**

#### Endpoints
```python
# Validation d'un mot
GET /api/v1/dictionnaire/fr/valider/{mot}
GET /api/v1/dictionnaire/en/valider/{word}

# Obtenir une définition
GET /api/v1/dictionnaire/fr/definition/{mot}
GET /api/v1/dictionnaire/en/definition/{word}

# Recherche par critères
GET /api/v1/dictionnaire/fr/recherche?longueur=5&commence_par=CH
GET /api/v1/dictionnaire/en/search?length=5&starts_with=CA
```

#### Format de Réponse JSON
```json
{
    "mot": "CHAT",
    "valide": true,
    "definition": "Mammifère domestique félin",
    "points": 9,
    "longueur": 4,
    "categorie": "nom"
}
```

## 📈 Critères de Validation

### 1. **Performance**
- Recherche d'un mot : < 50ms
- Validation batch (10 mots) : < 200ms
- Taille base SQLite : < 100MB par langue

### 2. **Qualité des Données**
- Couverture ODS : 100% des mots officiels
- Définitions : Minimum 95% des mots
- Cohérence points Scrabble : 100%

### 3. **Tests**
- Couverture de code : > 90%
- Tests d'intégration : 100% des endpoints
- Tests de performance : Validation automatisée

## 📋 Livrable Final

### Phase 1 - Français
- [ ] Base SQLite française complète (ODS + conjugaisons + dérivés)
- [ ] Fichier CSV source correspondant
- [ ] Scripts de conversion et validation
- [ ] Tests unitaires complets (serveur + Godot)
- [ ] API REST fonctionnelle
- [ ] Documentation d'utilisation

### Phase 2 - Anglais
- [ ] Base SQLite anglaise (SOWPODS/TWL)
- [ ] Fichier CSV source correspondant
- [ ] Extension des tests pour le support multilingue
- [ ] API multilingue
- [ ] Sélection automatique de langue

## 🔧 Scripts d'Automatisation

### Script de Mise à Jour
```bash
#!/bin/bash
# update_dictionnaires.sh
# Met à jour les dictionnaires depuis les sources officielles

echo "🔄 Mise à jour des dictionnaires Scrabbot..."
python data/dictionnaires/scripts/csv_to_sqlite.py \
    data/dictionnaires/sources/dictionnaire_fr.csv \
    data/dictionnaires/databases/french.db \
    --langue fr

python data/dictionnaires/scripts/csv_to_sqlite.py \
    data/dictionnaires/sources/dictionnaire_en.csv \
    data/dictionnaires/databases/english.db \
    --langue en

echo "✅ Dictionnaires mis à jour avec succès!"
```

---

**Note** : Cette spécification servira de base pour l'implémentation du système de dictionnaires multilingues robuste et performant pour Scrabbot.
