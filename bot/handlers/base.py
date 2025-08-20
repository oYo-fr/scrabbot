"""
Classe de base pour les gestionnaires de commandes.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes


class BaseHandler(ABC):
    """Classe de base pour tous les gestionnaires de commandes."""

    def __init__(self):
        """Initialise le gestionnaire."""
        self.name = self.__class__.__name__.replace("Handler", "").lower()

    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Traite la commande.

        Args:
            update: Mise à jour Telegram
            context: Contexte de la mise à jour
        """
        pass

    async def send_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Any] = None,
    ) -> None:
        """
        Envoie un message.

        Args:
            update: Mise à jour Telegram
            text: Texte du message
            parse_mode: Mode de parsing (Markdown, HTML)
            reply_markup: Clavier de réponse
        """
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )

    def get_user_info(self, update: Update) -> Dict[str, Any]:
        """
        Récupère les informations de l'utilisateur.

        Args:
            update: Mise à jour Telegram

        Returns:
            Informations de l'utilisateur
        """
        user = update.effective_user
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code,
            }
        return {}
