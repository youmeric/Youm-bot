import discord
from discord import app_commands
from discord.ext import commands

class ClearCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Supprime un nombre spécifique de messages dans le salon actuel")
    async def clear(self, interaction: discord.Interaction, amount: int):
        """
        Supprime un nombre spécifique de messages dans le salon actuel.
        Usage: /clear <nombre_de_messages>
        """
        # Vérification des permissions dans le code
        if not (interaction.user.guild_permissions.manage_messages or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message("Vous n'avez pas les permissions nécessaires pour utiliser cette commande.", ephemeral=True)
            return

        if amount < 1:
            await interaction.response.send_message("Veuillez spécifier un nombre positif de messages à supprimer.", ephemeral=True)
            return

        # Indique à Discord que le bot est en train de traiter la commande
        await interaction.response.defer()  # Envoie une réponse initiale pour éviter le message "réfléchit..."

        try:
            # Supprime le nombre de messages spécifié
            deleted = await interaction.channel.purge(limit=amount)
            deleted_count = len(deleted)
            print(f"DEBUG: {deleted_count} messages supprimés.")
        except Exception as e:
            print(f"Erreur lors de la suppression des messages : {e}")
            await interaction.followup.send("Une erreur s'est produite lors de la suppression des messages.")
            return

        # Envoie une confirmation après la suppression
        await interaction.followup.send(f"{deleted_count} messages ont été supprimés.", ephemeral=True)

# Fonction asynchrone pour ajouter le cog au bot principal
async def setup(bot):
    await bot.add_cog(ClearCommand(bot))
