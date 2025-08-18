"""
Gestionnaire pour la commande /start.
"""

from .base import BaseHandler
from telegram import Update
from telegram.ext import ContextTypes


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
        
        await self.send_message(
            update=update,
            text=welcome_message,
            parse_mode="Markdown"
        )
