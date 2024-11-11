import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import time
from collections import defaultdict
import re

class GifLimit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gif_count = defaultdict(lambda: {"count": 0, "timestamp": time.time()})

        # Connexion à la base de données
        self.conn = sqlite3.connect("server_config.db")
        self.cursor = self.conn.cursor()
        
        # Création de la table si elle n'existe pas
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS gif_config (
                server_id INTEGER,
                channel_id INTEGER,
                gif_limit INTEGER DEFAULT 5,
                time_window INTEGER DEFAULT 60,
                is_enabled BOOLEAN DEFAULT 0,
                PRIMARY KEY (server_id, channel_id)
            )
        """)
        self.conn.commit()

    def get_channel_config(self, server_id, channel_id):
        """Récupère la configuration de limite de GIF pour un salon spécifique."""
        self.cursor.execute("SELECT gif_limit, time_window, is_enabled FROM gif_config WHERE server_id = ? AND channel_id = ?", (server_id, channel_id))
        config = self.cursor.fetchone()
        if config is None:
            # Si le salon n'a pas encore de configuration, on utilise les valeurs par défaut
            self.cursor.execute("INSERT INTO gif_config (server_id, channel_id) VALUES (?, ?)", (server_id, channel_id))
            self.conn.commit()
            print(f"DEBUG - Nouvelle configuration créée pour le serveur {server_id}, salon {channel_id} avec valeurs par défaut.")
            return 5, 60, False  # valeurs par défaut : 5 GIF, 60 secondes, désactivé
        print(f"DEBUG - Configuration récupérée pour le serveur {server_id}, salon {channel_id}: {config}")
        return config

    def update_channel_config(self, server_id, channel_id, gif_limit=None, time_window=None, is_enabled=None):
        """Mise à jour de la configuration pour un salon spécifique. Crée une entrée si elle n'existe pas."""
        # Vérifier si l'entrée existe déjà pour le salon
        self.cursor.execute("SELECT 1 FROM gif_config WHERE server_id = ? AND channel_id = ?", (server_id, channel_id))
        if self.cursor.fetchone() is None:
            # Insérer une nouvelle entrée si elle n'existe pas
            self.cursor.execute("INSERT INTO gif_config (server_id, channel_id) VALUES (?, ?)", (server_id, channel_id))
            self.conn.commit()
            print(f"DEBUG - Nouvelle entrée créée pour le serveur {server_id}, salon {channel_id}")

        # Mise à jour des paramètres
        if gif_limit is not None:
            print(f"DEBUG - Mise à jour de la limite de GIF pour le serveur {server_id}, salon {channel_id} à {gif_limit}")
            self.cursor.execute("UPDATE gif_config SET gif_limit = ? WHERE server_id = ? AND channel_id = ?", (gif_limit, server_id, channel_id))
        if time_window is not None:
            print(f"DEBUG - Mise à jour de la période de temps pour le serveur {server_id}, salon {channel_id} à {time_window}")
            self.cursor.execute("UPDATE gif_config SET time_window = ? WHERE server_id = ? AND channel_id = ?", (time_window, server_id, channel_id))
        if is_enabled is not None:
            print(f"DEBUG - Activation de la limite de GIF pour le serveur {server_id}, salon {channel_id} : {is_enabled}")
            self.cursor.execute("UPDATE gif_config SET is_enabled = ? WHERE server_id = ? AND channel_id = ?", (is_enabled, server_id, channel_id))
        self.conn.commit()

    def update_server_config(self, server_id, is_enabled):
        """Active ou désactive la limitation de GIF pour tous les salons d'un serveur."""
        print(f"DEBUG - Mise à jour de la limite de GIF pour tous les salons du serveur {server_id} : {is_enabled}")
        self.cursor.execute("UPDATE gif_config SET is_enabled = ? WHERE server_id = ?", (is_enabled, server_id))
        self.conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.author.guild_permissions.administrator:
            return

        # Récupérer la configuration pour le salon
        gif_limit, time_window, is_enabled = self.get_channel_config(message.guild.id, message.channel.id)

        # Si la limitation de GIF n'est pas activée pour ce salon, on ignore le message
        if not is_enabled:
            return

        gif_pattern = re.compile(r"gif", re.IGNORECASE)
        
        if gif_pattern.search(message.content):
            channel_id = message.channel.id
            current_time = time.time()
            channel_data = self.gif_count[channel_id]

            if current_time - channel_data["timestamp"] > time_window:
                channel_data["count"] = 0
                channel_data["timestamp"] = current_time

            channel_data["count"] += 1

            if channel_data["count"] > gif_limit:
                try:
                    await message.delete()
                    await message.channel.send(
                        f"{message.author.mention} Le nombre maximum de GIF autorisés dans ce salon a été atteint. Veuillez patienter avant d'envoyer d'autres GIF.",
                        delete_after=5
                    )
                except discord.Forbidden:
                    print("ERREUR - Le bot n'a pas la permission de supprimer des messages dans ce salon.")
                except discord.HTTPException as e:
                    print(f"ERREUR - Problème lors de la suppression du message: {e}")

    @app_commands.command(name="enable_gif_limit", description="Active la limitation de GIF pour le salon actuel")
    @app_commands.checks.has_permissions(administrator=True)
    async def enable_gif_limit(self, interaction: discord.Interaction):
        """Active la limitation de GIF pour le salon actuel."""
        self.update_channel_config(interaction.guild.id, interaction.channel_id, is_enabled=True)
        await interaction.response.send_message("La limitation de GIF a été activée pour ce salon.", ephemeral=True)

    @app_commands.command(name="disable_gif_limit", description="Désactive la limitation de GIF pour le salon actuel")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_gif_limit(self, interaction: discord.Interaction):
        """Désactive la limitation de GIF pour le salon actuel."""
        self.update_channel_config(interaction.guild.id, interaction.channel_id, is_enabled=False)
        await interaction.response.send_message("La limitation de GIF a été désactivée pour ce salon.", ephemeral=True)

    @app_commands.command(name="enable_gif_limit_server", description="Active la limitation de GIF pour tous les salons du serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def enable_gif_limit_server(self, interaction: discord.Interaction):
        """Active la limitation de GIF pour tous les salons du serveur."""
        self.update_server_config(interaction.guild.id, is_enabled=True)
        await interaction.response.send_message("La limitation de GIF a été activée pour tous les salons du serveur.", ephemeral=True)

    @app_commands.command(name="disable_gif_limit_server", description="Désactive la limitation de GIF pour tous les salons du serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_gif_limit_server(self, interaction: discord.Interaction):
        """Désactive la limitation de GIF pour tous les salons du serveur."""
        self.update_server_config(interaction.guild.id, is_enabled=False)
        await interaction.response.send_message("La limitation de GIF a été désactivée pour tous les salons du serveur.", ephemeral=True)

    @app_commands.command(name="set_gif_limit", description="Définit une nouvelle limite de GIF pour le salon actuel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_gif_limit(self, interaction: discord.Interaction, limit: int):
        """Définit une nouvelle limite de GIF pour le salon actuel."""
        self.update_channel_config(interaction.guild.id, interaction.channel_id, gif_limit=limit)
        await interaction.response.send_message(f"La limite de GIF pour ce salon a été fixée à {limit}.", ephemeral=True)

    @app_commands.command(name="set_time_window", description="Définit une nouvelle période de temps pour le comptage des GIF")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_time_window(self, interaction: discord.Interaction, seconds: int):
        """Définit une nouvelle période de temps pour le comptage des GIF pour le salon actuel."""
        self.update_channel_config(interaction.guild.id, interaction.channel_id, time_window=seconds)
        await interaction.response.send_message(f"La période de vérification pour les GIF a été définie à {seconds} secondes pour ce salon.", ephemeral=True)

    @app_commands.command(name="show_gif_config", description="Affiche la configuration actuelle de GIF pour le salon actuel")
    @app_commands.checks.has_permissions(administrator=True)
    async def show_gif_config(self, interaction: discord.Interaction):
        """Affiche la configuration actuelle de GIF pour le salon actuel."""
        gif_limit, time_window, is_enabled = self.get_channel_config(interaction.guild.id, interaction.channel_id)
        status = "activée" if is_enabled else "désactivée"
        await interaction.response.send_message(f"Configuration actuelle pour ce salon :\nLimite de GIF : {gif_limit}\nPériode de temps : {time_window} secondes\nStatut : {status}", ephemeral=True)

    def cog_unload(self):
        """Fermer la connexion à la base de données à la fermeture du Cog."""
        self.conn.close()

async def setup(bot):
    await bot.add_cog(GifLimit(bot))
