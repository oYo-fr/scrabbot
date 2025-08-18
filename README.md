# 🎲 Scrabbot - Bot de Scrabble Intelligent

Un bot Telegram de Scrabble intelligent capable de jouer contre des humains ou d'autres bots, avec une interface graphique moderne développée en Godot.

## 🎯 Objectif

Développer un bot de Scrabble capable de jouer intelligemment, d'analyser les parties et d'aider les joueurs à améliorer leurs compétences grâce à l'intelligence artificielle.

## 🚀 Fonctionnalités

### Phase 1 - Structure de base et CI/CD
- [x] Structure de base du bot Telegram
- [ ] Écran "Hello World" avec Godot
- [ ] Mise en place des tests unitaires
- [ ] Configuration de la CI/CD (GitHub Actions)
- [ ] Documentation de base

### Phase 1.5 - Menu du jeu et gestion des parties
- [ ] Menu principal multilingue (FR/EN)
- [ ] Mode solo avec 3 niveaux de difficulté
- [ ] Mode multijoueur avec invitations Telegram
- [ ] Gestion des parties en cours
- [ ] Système de reprise de parties

### Phase 2 - Intelligence Artificielle
- [ ] Algorithme de minimax pour la prise de décision
- [ ] Évaluation de position
- [ ] Stratégie offensive et défensive
- [ ] 3 niveaux de difficulté (facile, moyen, difficile)

### Phase 3 - Interface de jeu complète
- [ ] Interface Godot moderne et interactive
- [ ] Visualisation du plateau en temps réel
- [ ] Système de drag and drop des tuiles
- [ ] Historique des parties
- [ ] Statistiques de jeu

### Phase 4 - Fonctionnalités Avancées
- [ ] Mode entraînement
- [ ] Analyse de parties
- [ ] Suggestions de coups
- [ ] Tournois et classements
- [ ] Fonctionnalités sociales

## 🛠️ Technologies

- **Bot Telegram** : Python avec python-telegram-bot
- **Moteur de jeu** : Python (logique métier)
- **Interface graphique** : Godot 4.x (GDScript/C#)
- **Base de données** : SQLite pour les dictionnaires
- **IA** : Algorithmes de recherche, minimax
- **Communication** : API REST entre Telegram et Godot
- **Tests** : pytest, Godot tests
- **CI/CD** : GitHub Actions
- **Déploiement** : Docker, VPS/Cloud

## 📋 Règles du Jeu

Le projet respecte les règles officielles du Scrabble français :
- Distribution des lettres standard (102 tuiles)
- Calcul des scores avec cases bonus
- Validation des mots via dictionnaire
- Règles de contestation

## 🎲 Matériel de Référence

- Plateau 15x15
- 102 tuiles (100 lettres + 2 jokers)
- Valeurs des lettres standardisées
- Cases bonus (double/triple lettre/mot)

## 📚 Dictionnaires

- **Français** : ODS, Larousse, Wiktionnaire
- **Anglais** : SOWPODS, TWL, Wiktionary
- Stockage local SQLite avec définitions
- Recherche optimisée pour les algorithmes IA

## 🏗️ Architecture

```
scrabbot/
├── bot/                 # Bot Telegram
│   ├── handlers/        # Gestionnaires de commandes
│   ├── config/          # Configuration
│   └── utils/           # Utilitaires
├── godot/              # Projet Godot
│   ├── scenes/         # Scènes du jeu
│   ├── scripts/        # Scripts GDScript
│   └── assets/         # Ressources graphiques
├── shared/             # Code partagé
│   ├── models/         # Modèles de données
│   └── api/            # API REST
├── tests/              # Tests
│   ├── bot/            # Tests du bot
│   └── godot/          # Tests Godot
├── data/               # Dictionnaires, règles
└── docs/               # Documentation
```

## 🚀 Installation

### Prérequis

- Python 3.11+
- Godot 4.x
- Git

### Installation du bot

```bash
# Cloner le repository
git clone https://github.com/yoanndiguet/scrabbot.git
cd scrabbot

# Installer les dépendances Python
cd bot
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos tokens Telegram
```

### Installation de l'interface Godot

```bash
# Ouvrir le projet Godot
cd godot
# Ouvrir Godot et importer le projet
```

## 🧪 Tests

```bash
# Tests du bot
cd bot
pytest

# Tests Godot (si applicable)
cd godot
# Utiliser l'interface de test de Godot
```

## 📊 Métriques de Succès

- Performance du bot (win rate)
- Temps de réponse Telegram
- Qualité des suggestions
- Expérience utilisateur
- Couverture des règles de jeu
- Performance Godot (FPS, fluidité)
- Couverture de tests (>80%)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🔗 Liens utiles

- [Règles du jeu](https://www.notion.so/yoanndiguet/Scrabble-R-gles-du-jeu-2535567a9a9c80ab9195daff3a3e556d)
- [Documentation technique](https://www.notion.so/yoanndiguet/Scrabbot-2535567a9a9c805b9fe8d65998296874)
- [Projet Linear](https://linear.app/oyo-fr/project/scrabbot-3d6f70e33e88)

## 👥 Équipe

- **Yoann Diguet** - Développeur principal

---

*Ce projet est développé avec ❤️ pour les amateurs de Scrabble et d'intelligence artificielle.*
