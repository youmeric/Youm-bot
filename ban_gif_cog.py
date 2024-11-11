import discord
from discord import app_commands
from discord.ext import commands
import sqlite3

# Fonction de vérification personnalisée pour autoriser les administrateurs ou les utilisateurs ayant la permission de gérer les messages
def admin_or_manage_messages():
    async def predicate(interaction: discord.Interaction) -> bool:
        # Vérifie si l'utilisateur est administrateur ou peut gérer les messages
        return interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_messages
    return app_commands.check(predicate)

class BanGif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Connexion à la base de données pour les GIF interdits
        self.conn = sqlite3.connect("banned_gifs.db")
        self.cursor = self.conn.cursor()
        
        # Création de la table si elle n'existe pas
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS banned_gifs (
                server_id INTEGER,
                gif_url TEXT,
                PRIMARY KEY (server_id, gif_url)
            )
        """)
        self.conn.commit()

    def add_banned_gif(self, server_id, gif_url):
        """Ajoute un GIF à la liste des GIF interdits pour un serveur."""
        self.cursor.execute("INSERT OR IGNORE INTO banned_gifs (server_id, gif_url) VALUES (?, ?)", (server_id, gif_url))
        self.conn.commit()
        print(f"DEBUG - GIF interdit ajouté pour le serveur {server_id} : {gif_url}")

    def remove_banned_gif(self, server_id, gif_url):
        """Retire un GIF de la liste des GIF interdits pour un serveur."""
        self.cursor.execute("DELETE FROM banned_gifs WHERE server_id = ? AND gif_url = ?", (server_id, gif_url))
        self.conn.commit()
        print(f"DEBUG - GIF interdit retiré pour le serveur {server_id} : {gif_url}")

    def get_banned_gifs(self, server_id):
        """Récupère la liste des GIF interdits pour un serveur."""
        self.cursor.execute("SELECT gif_url FROM banned_gifs WHERE server_id = ?", (server_id,))
        return [row[0] for row in self.cursor.fetchall()]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Vérifie si le message contient un GIF interdit pour le serveur
        banned_gifs = self.get_banned_gifs(message.guild.id)
        for gif_url in banned_gifs:
            if gif_url in message.content:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Ce GIF est interdit sur ce serveur.", delete_after=5)
                except discord.Forbidden:
                    print("ERREUR - Le bot n'a pas la permission de supprimer des messages dans ce salon.")
                except discord.HTTPException as e:
                    print(f"ERREUR - Problème lors de la suppression du message: {e}")
                break

    @app_commands.command(name="ban_gif", description="Interdit un GIF spécifique sur le serveur")
    #@app_commands.checks.has_permissions(administrator=True)
    @admin_or_manage_messages()
    async def ban_gif(self, interaction: discord.Interaction, gif_url: str):
        """Interdit un GIF spécifique sur le serveur."""
        self.add_banned_gif(interaction.guild.id, gif_url)
        await interaction.response.send_message(f"Le GIF {gif_url} a été interdit sur ce serveur.", ephemeral=True)

    @app_commands.command(name="unban_gif", description="Retire l'interdiction d'un GIF spécifique sur le serveur")
    #@app_commands.checks.has_permissions(administrator=True)
    @admin_or_manage_messages()
    async def unban_gif(self, interaction: discord.Interaction, gif_url: str):
        """Retire l'interdiction d'un GIF spécifique sur le serveur."""
        self.remove_banned_gif(interaction.guild.id, gif_url)
        await interaction.response.send_message(f"Le GIF {gif_url} n'est plus interdit sur ce serveur.", ephemeral=True)

    @app_commands.command(name="show_banned_gifs", description="Affiche la liste des GIF interdits sur ce serveur")
    #@app_commands.checks.has_permissions(administrator=True)
    @admin_or_manage_messages()
    async def show_banned_gifs(self, interaction: discord.Interaction):
        """Affiche la liste des GIF interdits sur le serveur."""
        banned_gifs = self.get_banned_gifs(interaction.guild.id)
        if banned_gifs:
            await interaction.response.send_message("GIFs interdits sur ce serveur:\n" + "\n".join(banned_gifs), ephemeral=True)
        else:
            await interaction.response.send_message("Aucun GIF interdit sur ce serveur.", ephemeral=True)

    def cog_unload(self):
        """Ferme la connexion à la base de données lors du déchargement du cog."""
        self.conn.close()

async def setup(bot):
    await bot.add_cog(BanGif(bot))
