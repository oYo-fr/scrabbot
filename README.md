# 🎲 Scrabbot - Intelligent Scrabble Bot

An intelligent Telegram Scrabble bot capable of playing against humans or other bots, with a modern graphical interface developed in Godot.

## 🎯 Objective

Develop a Scrabble bot capable of playing intelligently, analyzing games, and helping players improve their skills through artificial intelligence.

## 🚀 Features

### Phase 1 - Basic structure and CI/CD
- [x] Basic Telegram bot structure
- [ ] "Hello World" screen with Godot
- [ ] Unit tests setup
- [ ] CI/CD configuration (GitHub Actions)
- [ ] Basic documentation

### Phase 1.5 - Game menu and game management
- [ ] Multilingual main menu (FR/EN)
- [ ] Solo mode with 3 difficulty levels
- [ ] Multiplayer mode with Telegram invitations
- [ ] Current games management
- [ ] Game resume system

### Phase 2 - Artificial Intelligence
- [ ] Minimax algorithm for decision making
- [ ] Position evaluation
- [ ] Offensive and defensive strategy
- [ ] 3 difficulty levels (easy, medium, hard)

### Phase 3 - Complete game interface
- [ ] Modern and interactive Godot interface
- [ ] Real-time board visualization
- [ ] Tile drag and drop system
- [ ] Game history
- [ ] Game statistics

### Phase 4 - Advanced Features
- [ ] Training mode
- [ ] Game analysis
- [ ] Move suggestions
- [ ] Tournaments and rankings
- [ ] Social features

## 🛠️ Technologies

- **Telegram Bot**: Python with python-telegram-bot
- **Game Engine**: Python (business logic)
- **Graphical Interface**: Godot 4.x (GDScript/C#)
- **Database**: SQLite for dictionaries
- **AI**: Search algorithms, minimax
- **Communication**: REST API between Telegram and Godot
- **Testing**: pytest, Godot tests
- **CI/CD**: GitHub Actions
- **Deployment**: Docker, VPS/Cloud

## 📋 Game Rules

The project follows official French Scrabble rules:
- Standard letter distribution (102 tiles)
- Score calculation with bonus squares
- Word validation via dictionary
- Challenge rules

## 🎲 Reference Material

- 15x15 board
- 102 tiles (100 letters + 2 blanks)
- Standardized letter values
- Bonus squares (double/triple letter/word)

## 📚 Dictionaries

- **French**: ODS, Larousse, Wiktionnaire
- **English**: SOWPODS, TWL, Wiktionary
- Local SQLite storage with definitions
- Optimized search for AI algorithms

## 🏗️ Architecture

```
scrabbot/
├── bot/                 # Telegram Bot
│   ├── handlers/        # Command handlers
│   ├── config/          # Configuration
│   └── utils/           # Utilities
├── godot/              # Godot Project
│   ├── scenes/         # Game scenes
│   ├── scripts/        # GDScript scripts
│   └── assets/         # Graphic resources
├── shared/             # Shared code
│   ├── models/         # Data models
│   └── api/            # REST API
├── tests/              # Tests
│   ├── bot/            # Bot tests
│   └── godot/          # Godot tests
├── data/               # Dictionaries, rules
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

## 📊 Success Metrics

- Bot performance (win rate)
- Telegram response time
- Suggestion quality
- User experience
- Game rules coverage
- Godot performance (FPS, fluidity)
- Test coverage (>80%)

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is under MIT license. See the `LICENSE` file for more details.

## 🔗 Useful Links

- [Game Rules](https://www.notion.so/yoanndiguet/Scrabble-R-gles-du-jeu-2535567a9a9c80ab9195daff3a3e556d)
- [Technical Documentation](https://www.notion.so/yoanndiguet/Scrabbot-2535567a9a9c805b9fe8d65998296874)
- [Linear Project](https://linear.app/oyo-fr/project/scrabbot-3d6f70e33e88)

## 👥 Team

- **Yoann Diguet** - Lead Developer

---

*This project is developed with ❤️ for Scrabble and artificial intelligence enthusiasts.*
