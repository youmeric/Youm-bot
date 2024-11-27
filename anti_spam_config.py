import discord
from discord import app_commands
from discord.ext import commands

# Vérification pour administrateurs uniquement
def admin_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

class StaffRoleModal(discord.ui.Modal, title="Définir le Rôle Staff"):
    staff_role_id = discord.ui.TextInput(
        label="ID du rôle Staff",
        style=discord.TextStyle.short,
        placeholder="Entrez l'ID du rôle Staff",
        required=True
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            role_id = int(self.staff_role_id.value)
            guild = interaction.guild
            role = guild.get_role(role_id)
            if not role:
                await interaction.response.send_message("Rôle introuvable. Assurez-vous que l'ID est correct.", ephemeral=True)
                return
            self.cog.update_server_config(interaction.guild_id, staff_role_id=role_id)
            await interaction.response.send_message(f"Le rôle Staff a été défini sur {role.mention}.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Valeur invalide. Veuillez entrer un ID numérique.", ephemeral=True)

class AlertChannelModal(discord.ui.Modal, title="Définir le Salon d'Alerte"):
    alert_channel_id = discord.ui.TextInput(
        label="ID du salon d'alerte",
        style=discord.TextStyle.short,
        placeholder="Entrez l'ID du salon",
        required=True
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.alert_channel_id.value)
            guild = interaction.guild
            channel = guild.get_channel(channel_id)
            if not channel:
                await interaction.response.send_message("Salon introuvable. Assurez-vous que l'ID est correct.", ephemeral=True)
                return
            self.cog.update_server_config(interaction.guild_id, alert_channel_id=channel_id)
            await interaction.response.send_message(f"Le salon d'alerte a été défini sur {channel.mention}.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Valeur invalide. Veuillez entrer un ID numérique.", ephemeral=True)

class AntiSpamMainMenuView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Définir Limite de Messages Similaires", style=discord.ButtonStyle.success, custom_id="set_spam_limit")
    async def set_spam_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SpamLimitModal(self.cog))

    @discord.ui.button(label="Définir Période de Temps", style=discord.ButtonStyle.success, custom_id="set_time_window")
    async def set_time_window(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SpamTimeWindowModal(self.cog))

    @discord.ui.button(label="Définir Nombre Maximum de Salons", style=discord.ButtonStyle.success, custom_id="set_max_channels")
    async def set_max_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MaxChannelsBeforeBanModal(self.cog))

    @discord.ui.button(label="Définir le Rôle Staff", style=discord.ButtonStyle.primary, custom_id="set_staff_role")
    async def set_staff_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StaffRoleModal(self.cog))

    @discord.ui.button(label="Définir le Salon d'Alerte", style=discord.ButtonStyle.primary, custom_id="set_alert_channel")
    async def set_alert_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AlertChannelModal(self.cog))

    @discord.ui.button(label="Activer l'Anti-Spam", style=discord.ButtonStyle.success, custom_id="enable_anti_spam")
    async def enable_anti_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.update_server_config(interaction.guild_id, is_enabled=True)
        await interaction.response.send_message("L'anti-spam a été activé pour ce serveur.", ephemeral=True)

    @discord.ui.button(label="Désactiver l'Anti-Spam", style=discord.ButtonStyle.danger, custom_id="disable_anti_spam")
    async def disable_anti_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.update_server_config(interaction.guild_id, is_enabled=False)
        await interaction.response.send_message("L'anti-spam a été désactivé pour ce serveur.", ephemeral=True)

    @discord.ui.button(label="Afficher Configuration", style=discord.ButtonStyle.secondary, custom_id="show_config")
    async def show_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        spam_limit, time_window, is_enabled, alert_channel_id, staff_role_id, max_channels_before_ban = self.cog.get_server_config(interaction.guild_id)
        status = "activé" if is_enabled else "désactivé"
        alert_channel = f"<#{alert_channel_id}>" if alert_channel_id else "Aucun"
        staff_role = f"<@&{staff_role_id}>" if staff_role_id else "Aucun"
        await interaction.response.send_message(
            f"**Configuration actuelle de l'Anti-Spam** :\n"
            f"- Limite : {spam_limit}\n"
            f"- Période : {time_window} secondes\n"
            f"- Statut : {status}\n"
            f"- Salon d'alerte : {alert_channel}\n"
            f"- Rôle mentionné : {staff_role}\n"
            f"- Salons avant bannissement : {max_channels_before_ban}",
            ephemeral=True
        )

class AntiSpamConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cog = bot.get_cog("AntiSpam")

    @app_commands.command(name="config_anti_spam", description="Affiche les options de configuration pour l'Anti-Spam.")
    @admin_only()
    async def config_anti_spam(self, interaction: discord.Interaction):
        """Affiche le menu principal de configuration de l'anti-spam."""
        embed = discord.Embed(
            title="Configuration de l'Anti-Spam",
            description="Utilisez les options ci-dessous pour configurer l'anti-spam sur ce serveur.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=AntiSpamMainMenuView(self.cog), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AntiSpamConfig(bot))
