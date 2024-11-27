import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

# Vérification pour administrateurs uniquement
def admin_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_messages = defaultdict(lambda: defaultdict(list))  # {server_id: {user_id: [(message_content, message, timestamp)]}}
        self.conn = sqlite3.connect("anti_spam_config.db")
        self.cursor = self.conn.cursor()

        # Création de la table pour les paramètres anti-spam au niveau serveur
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS spam_config (
                server_id INTEGER PRIMARY KEY,
                spam_limit INTEGER DEFAULT 3,
                time_window INTEGER DEFAULT 10,
                is_enabled BOOLEAN DEFAULT 0,
                alert_channel_id INTEGER,
                staff_role_id INTEGER,
                max_channels_before_ban INTEGER DEFAULT 4
            )
        """)
        self.conn.commit()

    def get_server_config(self, server_id):
        """Récupère la configuration anti-spam pour un serveur."""
        self.cursor.execute(
            "SELECT spam_limit, time_window, is_enabled, alert_channel_id, staff_role_id, max_channels_before_ban FROM spam_config WHERE server_id = ?",
            (server_id,),
        )
        config = self.cursor.fetchone()
        if config is None:
            # Si la configuration n'existe pas encore, la créer avec des valeurs par défaut
            self.cursor.execute(
                "INSERT INTO spam_config (server_id) VALUES (?)",
                (server_id,),
            )
            self.conn.commit()
            return 3, 10, False, None, None, 5  # Par défaut : 3 messages, 10 secondes, désactivé, pas de salon, max 5 salons avant ban
        return config

    def update_server_config(self, server_id, **kwargs):
        """Mise à jour des paramètres anti-spam d'un serveur."""
        self.cursor.execute(
            "SELECT 1 FROM spam_config WHERE server_id = ?",
            (server_id,),
        )
        if self.cursor.fetchone() is None:
            # Insérer une configuration par défaut si elle n'existe pas
            self.cursor.execute(
                "INSERT INTO spam_config (server_id) VALUES (?)",
                (server_id,),
            )
            self.conn.commit()

        # Mise à jour des paramètres existants
        for key, value in kwargs.items():
            if value is not None:
                self.cursor.execute(
                    f"UPDATE spam_config SET {key} = ? WHERE server_id = ?",
                    (value, server_id),
                )
        self.conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Récupérer la configuration pour le serveur
        spam_limit, time_window, is_enabled, alert_channel_id, staff_role_id, max_channels_before_ban = self.get_server_config(message.guild.id)

        if not is_enabled:
            return  # Anti-spam désactivé pour ce serveur

        user_id = message.author.id
        server_id = message.guild.id
        now = datetime.utcnow()

        # Filtrer les messages récents dans la période définie
        self.user_messages[server_id][user_id] = [
            (msg_content, msg_obj, timestamp)
            for msg_content, msg_obj, timestamp in self.user_messages[server_id][user_id]
            if now - timestamp <= timedelta(seconds=time_window)
        ]

        # Ajouter le message actuel
        self.user_messages[server_id][user_id].append((message.content, message, now))

        # Compter les messages identiques
        identical_messages = [
            (msg_obj, msg_obj.channel) for msg_content, msg_obj, _ in self.user_messages[server_id][user_id]
            if msg_content == message.content
        ]

        if len(identical_messages) > spam_limit:
            # Supprimer tous les messages identiques, y compris les 3 premiers
            for msg_to_delete, _ in identical_messages:
                try:
                    await msg_to_delete.delete()
                except discord.Forbidden:
                    print("ERREUR - Permissions insuffisantes pour supprimer un message.")
                except discord.HTTPException as e:
                    print(f"ERREUR - Problème lors de la suppression : {e}")

            # Construire la liste des salons
            spam_channels = {channel.mention for _, channel in identical_messages}

            # Préparer la mention du rôle
            staff_mention = f"<@&{staff_role_id}>" if staff_role_id else "le staff"

            # Si l'utilisateur a spammé dans plus de max_channels_before_ban salons, expulsion et bannissement
            if len(spam_channels) > max_channels_before_ban:
                try:
                    await message.guild.ban(message.author, reason="Spam détecté dans plusieurs salons")
                    if alert_channel_id:
                        alert_channel = message.guild.get_channel(alert_channel_id)
                        if alert_channel:
                            await alert_channel.send(
                                f"🔔 **Alerte anti-spam** 🔔\n"
                                f"{staff_mention}, l'utilisateur {message.author.mention} a été **banni** pour spam dans **{len(spam_channels)} salons**.\n"
                                f"Message répété : `{message.content}`\n"
                                f"Salons concernés : {', '.join(spam_channels)}"
                            )
                except discord.Forbidden:
                    print("ERREUR - Impossible de bannir l'utilisateur.")
                except discord.HTTPException as e:
                    print(f"ERREUR - Problème lors du bannissement : {e}")
            else:
                # Envoyer une alerte au staff
                if alert_channel_id:
                    alert_channel = message.guild.get_channel(alert_channel_id)
                    if alert_channel:
                        await alert_channel.send(
                            f"🔔 **Alerte anti-spam** 🔔\n"
                            f"{staff_mention}, une activité suspecte a été détectée.\n"
                            f"**Utilisateur** : {message.author.mention} (`{message.author.id}`)\n"
                            f"**Message répété** : `{message.content}`\n"
                            f"**Salons concernés** : {', '.join(spam_channels)}\n"
                            f"Veuillez vérifier l'activité de cet utilisateur."
                        )

            await message.channel.send(
                f"{message.author.mention}, vous êtes détecté comme spammeur. Veuillez ralentir.",
                delete_after=4,
            )

    @app_commands.command(name="set_spam_limit", description="Définit la limite de messages similaires pour tout le serveur.")
    @admin_only()
    async def set_spam_limit(self, interaction: discord.Interaction, limit: int):
        self.update_server_config(interaction.guild.id, spam_limit=limit)
        await interaction.response.send_message(f"La limite de messages similaires a été fixée à {limit} pour ce serveur.", ephemeral=True)

    @app_commands.command(name="set_spam_timeframe", description="Définit la période de temps pour l'anti-spam.")
    @admin_only()
    async def set_spam_timeframe(self, interaction: discord.Interaction, seconds: int):
        self.update_server_config(interaction.guild.id, time_window=seconds)
        await interaction.response.send_message(f"La période de temps pour l'anti-spam a été fixée à {seconds} secondes pour ce serveur.", ephemeral=True)

    @app_commands.command(name="set_spam_alert_channel", description="Définit le salon pour les alertes anti-spam.")
    @admin_only()
    async def set_spam_alert_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.update_server_config(interaction.guild.id, alert_channel_id=channel.id)
        await interaction.response.send_message(f"Le salon d'alerte anti-spam a été défini sur {channel.mention}.", ephemeral=True)

    @app_commands.command(name="set_staff_role", description="Définit le rôle à mentionner pour les alertes anti-spam.")
    @admin_only()
    async def set_staff_role(self, interaction: discord.Interaction, role: discord.Role):
        self.update_server_config(interaction.guild.id, staff_role_id=role.id)
        await interaction.response.send_message(f"Le rôle mentionné pour les alertes anti-spam est maintenant {role.mention}.", ephemeral=True)

    @app_commands.command(name="set_max_channels_before_ban", description="Définit le nombre maximum de salons avant bannissement.")
    @admin_only()
    async def set_max_channels_before_ban(self, interaction: discord.Interaction, max_channels: int):
        self.update_server_config(interaction.guild.id, max_channels_before_ban=max_channels)
        await interaction.response.send_message(
            f"Le nombre maximum de salons avant bannissement a été fixé à {max_channels}.", ephemeral=True
        )

    @app_commands.command(name="show_spam_config", description="Affiche la configuration anti-spam pour le serveur.")
    @admin_only()
    async def show_spam_config(self, interaction: discord.Interaction):
        spam_limit, time_window, is_enabled, alert_channel_id, staff_role_id, max_channels_before_ban = self.get_server_config(interaction.guild.id)
        status = "activé" if is_enabled else "désactivé"
        alert_channel = f"<#{alert_channel_id}>" if alert_channel_id else "Aucun"
        staff_role = f"<@&{staff_role_id}>" if staff_role_id else "Aucun"
        await interaction.response.send_message(
            f"Configuration anti-spam pour ce serveur :\n"
            f"Limite : {spam_limit}\n"
            f"Période : {time_window} secondes\n"
            f"Statut : {status}\n"
            f"Salon d'alerte : {alert_channel}\n"
            f"Rôle mentionné : {staff_role}\n"
            f"Nombre de salons avant bannissement : {max_channels_before_ban}",
            ephemeral=True,
        )

    @app_commands.command(name="enable_anti_spam", description="Active l'anti-spam pour tout le serveur.")
    @admin_only()
    async def enable_anti_spam(self, interaction: discord.Interaction):
        self.update_server_config(interaction.guild.id, is_enabled=True)
        await interaction.response.send_message("L'anti-spam a été activé pour ce serveur.", ephemeral=True)

    @app_commands.command(name="disable_anti_spam", description="Désactive l'anti-spam pour tout le serveur.")
    @admin_only()
    async def disable_anti_spam(self, interaction: discord.Interaction):
        self.update_server_config(interaction.guild.id, is_enabled=False)
        await interaction.response.send_message("L'anti-spam a été désactivé pour ce serveur.", ephemeral=True)

    def cog_unload(self):
        self.conn.close()

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
