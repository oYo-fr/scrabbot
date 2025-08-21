"""
Gestionnaire pour la commande /start.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from ..config import get_settings
from ..utils.godot_launcher import launch_godot_project
from .base import BaseHandler


class StartHandler(BaseHandler):
    """Gestionnaire pour la commande /start."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Traite la commande /start.

        Args:
            update: Mise à jour Telegram
            context: Contexte de la mise à jour
        """
        user_info = self.get_user_info(update)

        welcome_message = f"""
🎲 *Bienvenue dans Scrabbot !*

Bonjour {user_info.get('first_name', 'Joueur')} !

Je suis votre partenaire de jeu de Scrabble intelligent.
Avec moi, vous pouvez :

• 🎮 Jouer en solo contre l'IA
• 👥 Jouer avec vos amis
• 📚 Consulter les règles du jeu
• 📊 Voir vos statistiques

Utilisez /help pour voir toutes les commandes disponibles.

*Bon jeu !* 🎯
        """.strip()

        # Lancer la scène Godot (jeu) côté local (desktop)
        settings = get_settings()
        launched = False
        if settings.godot_executable_path:
            launched = launch_godot_project(
                executable_path=settings.godot_executable_path,
                project_dir=settings.godot_project_path,
            )

        suffix = ""
        reply_markup = None
        if settings.godot_web_url:
            # Ajoute des boutons pour ouvrir la Mini App (plein écran) et un fallback navigateur
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🎮 Ouvrir en plein écran (Mini App)",
                            web_app=WebAppInfo(url=settings.godot_web_url),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🌐 Ouvrir dans le navigateur",
                            url=settings.godot_web_url,
                        )
                    ],
                ]
            )
            suffix = "\n\nAstuce: utilisez le bouton ‘Mini App’ pour le plein écran."
        elif launched:
            suffix = "\n\n🖥️ Lancement de l'interface Godot..."

        await self.send_message(
            update=update,
            context=context,
            text=welcome_message + (suffix or "\n\n⚠️ Godot n'a pas pu être lancé automatiquement."),
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
