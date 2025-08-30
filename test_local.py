#!/usr/bin/env python3
"""
Simulateur local pour tester le bot Scrabbot sans token Telegram.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any


# Configuration to simulate Telegram
@dataclass
class MockUser:
    id: int
    first_name: str
    username: str = None
    last_name: str = None
    language_code: str = "fr"


@dataclass
class MockChat:
    id: int
    type: str = "private"


@dataclass
class MockMessage:
    message_id: int
    text: str
    chat: MockChat
    from_user: MockUser


@dataclass
class MockUpdate:
    update_id: int
    message: MockMessage = None
    callback_query: Any = None
    effective_chat: MockChat = None
    effective_user: MockUser = None


class MockContext:
    def __init__(self):
        self.bot = self
        self.user_data = {}

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = None,
        reply_markup=None,
    ):
        print(f"\n📤 Message envoyé au chat {chat_id}:")
        print(f"   {text}")
        if reply_markup:
            print(f"   Boutons: {reply_markup}")
        return MockMessage(999, text, MockChat(chat_id), MockUser(1, "Bot", "bot", None, "fr"))


def create_mock_update(text: str, user_id: int = 123, chat_id: int = 123) -> MockUpdate:
    """Create a mock update to simulate a command."""
    user = MockUser(user_id, "TestUser", "testuser", "Dupont", "fr")
    chat = MockChat(chat_id)
    message = MockMessage(1, text, chat, user)

    update = MockUpdate(1, message)
    update.effective_chat = chat
    update.effective_user = user

    return update


async def test_bot_commands():
    """Test bot commands locally."""
    from bot.handlers.help import HelpHandler
    from bot.handlers.start import StartHandler

    print("🎮 Scrabbot - Test Local")
    print("=" * 50)

    # Test environment configuration
    import os

    os.environ["GODOT_WEB_URL"] = "http://localhost:8080"
    os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"

    context = MockContext()

    # Test the /start command
    print("\n🚀 Test de la commande /start")
    print("-" * 30)
    start_handler = StartHandler()
    start_update = create_mock_update("/start")
    await start_handler.handle(start_update, context)

    # Test the /help command
    print("\n❓ Test de la commande /help")
    print("-" * 30)
    help_handler = HelpHandler()
    help_update = create_mock_update("/help")
    await help_handler.handle(help_update, context)

    print("\n✅ Tests terminés !")
    print("🌐 Interface web disponible sur: http://localhost:8080")


async def interactive_test():
    """Interactive mode to test commands."""
    # Environment configuration
    import os

    from bot.handlers.help import HelpHandler
    from bot.handlers.start import StartHandler

    os.environ["GODOT_WEB_URL"] = "http://localhost:8080"
    os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"

    context = MockContext()
    handlers = {"start": StartHandler(), "help": HelpHandler()}

    print("\n🎮 Scrabbot - Mode Interactif")
    print("=" * 50)
    print("Commandes disponibles:")
    print("  /start - Start the bot")
    print("  /help  - Afficher l'aide")
    print("  quit   - Quitter")
    print("-" * 50)

    while True:
        try:
            command = input("\n> Tapez une commande: ").strip()

            if command.lower() in ["quit", "exit", "q"]:
                break

            if command.startswith("/"):
                cmd = command[1:]
                if cmd in handlers:
                    update = create_mock_update(command)
                    await handlers[cmd].handle(update, context)
                else:
                    print(f"❌ Commande inconnue: {command}")
            else:
                print("❌ Les commandes doivent commencer par '/'")

        except KeyboardInterrupt:
            break

    print("\n👋 Au revoir !")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Choisissez un mode de test:")
    print("1. Tests automatiques")
    print("2. Mode interactif")

    try:
        choice = input("\nVotre choix (1 ou 2): ").strip()

        if choice == "1":
            asyncio.run(test_bot_commands())
        elif choice == "2":
            asyncio.run(interactive_test())
        else:
            print("Choix invalide. Lancement des tests automatiques...")
            asyncio.run(test_bot_commands())

    except KeyboardInterrupt:
        print("\n\n👋 Test interrompu par l'utilisateur.")
