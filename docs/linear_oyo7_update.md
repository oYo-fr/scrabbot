# Mise à jour Ticket Linear OYO-7 - Système de Dictionnaires Multilingues

## 🧪 Tests Unitaires pour Validation d'Accès

### Tests Serveur Web (Python)
- **Test d'accès basique** : Vérifier qu'un mot quelconque peut être récupéré depuis la base SQLite
- **Test de validation** : Confirmer qu'un mot valide retourne `True` et un mot invalide retourne `False`
- **Test de performance** : Mesurer le temps de réponse (< 50ms par mot)
- **Test de caractères spéciaux** : Validation des accents, cédilles, etc.
- **Test de connexion** : Établissement/fermeture de connexion SQLite

### Tests Application Godot (GDScript)
- **Test d'accès API** : Vérification des appels HTTP vers le serveur
- **Test de réponse JSON** : Validation du format de réponse
- **Test de timeout** : Gestion des cas de non-réponse du serveur
- **Test hors ligne** : Fallback en cas d'indisponibilité

### Tests d'Intégration
- **Test bout-en-bout** : Godot → API → Serveur → SQLite → Réponse
- **Test de charge** : Validation simultanée de multiples mots
- **Test de synchronisation** : Cohérence entre les systèmes

## 📦 Repository Final - Contenu des Dictionnaires

### Phase 1 - Dictionnaire Français
**Sources de données :**
- **ODS (Officiel Du Scrabble)** : Tous les mots autorisés en tournoi
- **Conjugaisons** : Toutes les formes verbales autorisées
- **Dérivés** : Noms dérivés, adjectifs, adverbes
- **Pluriels** : Formes plurielles standard et irrégulières
- **Définitions** : Chaque mot accompagné de sa définition (Larousse/Wiktionnaire)

### Phase 2 - Dictionnaire Anglais  
**Sources de données :**
- **SOWPODS** : Standard pour tournois internationaux
- **TWL (Tournament Word List)** : Liste nord-américaine
- **Conjugaisons et dérivés** anglais
- **Définitions** : Wiktionary et dictionnaires officiels

## 🗄️ Formats de Stockage (Double Format Requis)

### 1. Format CSV (Source de Vérité)
**Utilité :** Regénération future de la base SQLite, maintenance, audit

**Structure pour français :**
```csv
mot,definition,categorie_grammaticale,points,valide_scrabble,longueur,premiere_lettre,derniere_lettre
CHAT,"Mammifère domestique félin",nom,9,true,4,C,T
CHATS,"Pluriel de chat",nom,14,true,5,C,S
```

**Structure pour anglais :**
```csv
word,definition,part_of_speech,points,scrabble_valid,length,first_letter,last_letter
CAT,"Small domesticated carnivorous mammal",noun,5,true,3,C,T
CATS,"Plural of cat",noun,6,true,4,C,S
```

### 2. Format SQLite (Base de Données de Production)
**Utilité :** Performance optimale, recherche rapide, index

**Tables principales :**
- `mots_fr` : Dictionnaire français avec index optimisés
- `mots_en` : Dictionnaire anglais avec index optimisés
- `dictionnaires` : Métadonnées des versions

**Optimisations :**
- Index sur mots, longueur, première lettre
- Vues pour recherches fréquentes
- Contraintes d'intégrité

## 🛠️ Livrables Techniques

### Scripts et Outils
- **Script de conversion CSV → SQLite** : `csv_to_sqlite.py`
- **Script de validation des données** : `validate_data.py`
- **Script de mise à jour** : `update_dictionnaire.py`

### API REST pour Godot
**Endpoints requis :**
- `GET /api/v1/dictionnaire/fr/valider/{mot}` : Validation mot français
- `GET /api/v1/dictionnaire/en/valider/{word}` : Validation mot anglais
- `GET /api/v1/dictionnaire/fr/definition/{mot}` : Définition française
- `GET /api/v1/dictionnaire/en/definition/{word}` : Définition anglaise

### Structure Repository
```
data/
├── dictionnaires/
│   ├── sources/              # Fichiers CSV sources
│   │   ├── dictionnaire_fr.csv
│   │   └── dictionnaire_en.csv
│   ├── databases/            # Bases SQLite
│   │   ├── french.db
│   │   └── english.db
│   └── scripts/              # Scripts de conversion
└── tests/dictionaries/      # Tests unitaires complets
```

## 📋 Critères d'Acceptation

### Performance
- [ ] Recherche d'un mot : < 50ms
- [ ] Validation batch (10 mots) : < 200ms
- [ ] Taille base SQLite : < 100MB par langue

### Qualité des Données
- [ ] Couverture ODS : 100% des mots officiels français
- [ ] Définitions : Minimum 95% des mots
- [ ] Cohérence points Scrabble : 100%

### Tests
- [ ] Tests unitaires serveur web : Validation d'accès SQLite
- [ ] Tests unitaires Godot : Validation d'accès API
- [ ] Tests d'intégration : Bout-en-bout fonctionnel
- [ ] Couverture de code : > 90%

### Documentation
- [ ] Spécifications techniques complètes
- [ ] Documentation API REST
- [ ] Guide d'utilisation des scripts
- [ ] Procédure de mise à jour des dictionnaires

---

**📎 Spécifications complètes disponibles dans :** `/docs/specifications_dictionnaires_multilingues.md`

