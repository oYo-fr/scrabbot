"""
Gestionnaire pour la commande /help.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .base import BaseHandler


class HelpHandler(BaseHandler):
    """Handler for /help command."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Traite la commande /help.

        Args:
            update: Mise à jour Telegram
            context: Contexte de la mise à jour
        """
        help_message = """
📚 *Commandes disponibles :*

*🎮 Commandes de jeu :*
• /newgame - Créer une nouvelle partie
• /join <id> - Rejoindre une partie
• /play <mot> <position> - Jouer un mot
• /pass - Passer son tour
• /exchange <lettres> - Échanger des lettres

*📋 Commandes d'information :*
• /start - Start the bot
• /help - Afficher cette aide
• /rules - Voir les règles du jeu
• /status - État de la partie actuelle
• /stats - Vos statistiques

*⚙️ Commandes de configuration :*
• /language <fr/en> - Changer la langue
• /difficulty <facile/moyen/difficile> - Niveau IA

*💡 Exemples :*
• `/newgame` - Créer une partie solo
• `/play CHAT H8` - Placer "CHAT" en H8
• `/exchange QZ` - Échanger Q et Z

*Besoin d'aide ?* Contactez @support
        """.strip()

        # Create inline buttons for quick actions
        keyboard = [
            [
                InlineKeyboardButton("🎮 Nouvelle partie", callback_data="newgame"),
                InlineKeyboardButton("📚 Règles", callback_data="rules"),
            ],
            [
                InlineKeyboardButton("📊 Statistiques", callback_data="stats"),
                InlineKeyboardButton("⚙️ Configuration", callback_data="settings"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.send_message(
            update=update,
            context=context,
            text=help_message,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
