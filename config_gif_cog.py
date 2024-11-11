import discord
from discord import app_commands
from discord.ext import commands

# Fonction de vérification personnalisée pour autoriser les administrateurs ou les utilisateurs ayant la permission de gérer les messages
def admin_or_manage_messages():
    async def predicate(interaction: discord.Interaction) -> bool:
        # Vérifie si l'utilisateur est administrateur ou peut gérer les messages
        return interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_messages
    return app_commands.check(predicate)

class LimitGifModal(discord.ui.Modal, title="Définir Limite de GIF"):
    limit = discord.ui.TextInput(label="Nombre maximum de GIFs", style=discord.TextStyle.short, placeholder="Entrez un nombre", required=True)

    def __init__(self, gif_cog):
        super().__init__()
        self.gif_cog = gif_cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.limit.value)
            self.gif_cog.update_channel_config(interaction.guild_id, interaction.channel_id, gif_limit=limit)
            await interaction.response.send_message(f"La limite de GIF a été définie sur {limit} pour ce salon.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Valeur invalide. Veuillez entrer un nombre entier.", ephemeral=True)

class SetTimeWindowModal(discord.ui.Modal, title="Définir Période de Temps"):
    time_window = discord.ui.TextInput(label="Durée en secondes", style=discord.TextStyle.short, placeholder="Entrez un nombre de secondes", required=True)

    def __init__(self, gif_cog):
        super().__init__()
        self.gif_cog = gif_cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            time_window = int(self.time_window.value)
            self.gif_cog.update_channel_config(interaction.guild_id, interaction.channel_id, time_window=time_window)
            await interaction.response.send_message(f"La période de temps pour les GIF a été définie sur {time_window} secondes pour ce salon.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Valeur invalide. Veuillez entrer un nombre entier.", ephemeral=True)

class BanGifModal(discord.ui.Modal, title="Interdire un GIF"):
    gif_url = discord.ui.TextInput(label="URL du GIF à interdire", style=discord.TextStyle.short, placeholder="Entrez l'URL du GIF", required=True)

    def __init__(self, ban_gif_cog):
        super().__init__()
        self.ban_gif_cog = ban_gif_cog

    async def on_submit(self, interaction: discord.Interaction):
        gif_url = self.gif_url.value
        self.ban_gif_cog.add_banned_gif(interaction.guild_id, gif_url)
        await interaction.response.send_message(f"Le GIF {gif_url} a été interdit.", ephemeral=True)

class UnbanGifModal(discord.ui.Modal, title="Autoriser un GIF"):
    gif_url = discord.ui.TextInput(label="URL du GIF à autoriser", style=discord.TextStyle.short, placeholder="Entrez l'URL du GIF", required=True)

    def __init__(self, ban_gif_cog):
        super().__init__()
        self.ban_gif_cog = ban_gif_cog

    async def on_submit(self, interaction: discord.Interaction):
        gif_url = self.gif_url.value
        self.ban_gif_cog.remove_banned_gif(interaction.guild_id, gif_url)
        await interaction.response.send_message(f"Le GIF {gif_url} a été autorisé.", ephemeral=True)

class MainMenuView(discord.ui.View):
    def __init__(self, gif_cog, ban_gif_cog):
        super().__init__(timeout=None)
        self.gif_cog = gif_cog
        self.ban_gif_cog = ban_gif_cog

    @discord.ui.button(label="Limitation de GIF", style=discord.ButtonStyle.primary, custom_id="menu_gif_limit")
    async def menu_gif_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Options de Limitation de GIF", embed=None, view=GifLimitSubMenuView(self.gif_cog))

    @discord.ui.button(label="Gestion des GIFs", style=discord.ButtonStyle.primary, custom_id="menu_gif_management")
    async def menu_gif_management(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Options de Gestion des GIFs", embed=None, view=GifManagementSubMenuView(self.ban_gif_cog))

class GifLimitSubMenuView(discord.ui.View):
    def __init__(self, gif_cog):
        super().__init__(timeout=None)
        self.gif_cog = gif_cog

    @discord.ui.button(label="Définir Limite de GIF", style=discord.ButtonStyle.success, custom_id="set_gif_limit")
    async def set_gif_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LimitGifModal(self.gif_cog))

    @discord.ui.button(label="Définir Période de Temps", style=discord.ButtonStyle.success, custom_id="set_time_window")
    async def set_time_window(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetTimeWindowModal(self.gif_cog))

    @discord.ui.button(label="Activer Limite de GIF (Salon)", style=discord.ButtonStyle.success, custom_id="enable_gif_limit")
    async def enable_gif_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.gif_cog:
            self.gif_cog.update_channel_config(interaction.guild_id, interaction.channel_id, is_enabled=True)
            await interaction.response.send_message("La limitation de GIF a été activée pour ce salon.", ephemeral=True)

    @discord.ui.button(label="Désactiver Limite de GIF (Salon)", style=discord.ButtonStyle.danger, custom_id="disable_gif_limit")
    async def disable_gif_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.gif_cog:
            self.gif_cog.update_channel_config(interaction.guild_id, interaction.channel_id, is_enabled=False)
            await interaction.response.send_message("La limitation de GIF a été désactivée pour ce salon.", ephemeral=True)

    @discord.ui.button(label="Afficher la configuration GIF", style=discord.ButtonStyle.secondary, custom_id="show_gif_config")
    async def show_gif_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.gif_cog:
            gif_limit, time_window, is_enabled = self.gif_cog.get_channel_config(interaction.guild_id, interaction.channel_id)
            status = "activée" if is_enabled else "désactivée"
            await interaction.response.send_message(
                f"Configuration actuelle pour ce salon :\nLimite de GIF : {gif_limit}\nPériode de temps : {time_window} secondes\nStatut : {status}", 
                ephemeral=True
            )

class GifManagementSubMenuView(discord.ui.View):
    def __init__(self, ban_gif_cog):
        super().__init__(timeout=None)
        self.ban_gif_cog = ban_gif_cog

    @discord.ui.button(label="Interdire un GIF", style=discord.ButtonStyle.danger, custom_id="ban_gif")
    async def ban_gif(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BanGifModal(self.ban_gif_cog))

    @discord.ui.button(label="Autoriser un GIF", style=discord.ButtonStyle.success, custom_id="unban_gif")
    async def unban_gif(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UnbanGifModal(self.ban_gif_cog))

    @discord.ui.button(label="Afficher les GIFs Interdits", style=discord.ButtonStyle.secondary, custom_id="show_banned_gifs")
    async def show_banned_gifs(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ban_gif_cog:
            banned_gifs = self.ban_gif_cog.get_banned_gifs(interaction.guild_id)
            if banned_gifs:
                gif_list = "\n".join(banned_gifs)
                await interaction.response.send_message(f"GIFs interdits pour ce serveur:\n{gif_list}", ephemeral=True)
            else:
                await interaction.response.send_message("Aucun GIF interdit pour ce serveur.", ephemeral=True)

    @discord.ui.button(label="Retour", style=discord.ButtonStyle.secondary, custom_id="back_to_main")
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Retour au Menu Principal", embed=None, view=MainMenuView(self.gif_cog, self.ban_gif_cog))

class ConfigGif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gif_cog = bot.get_cog("GifLimit")
        self.ban_gif_cog = bot.get_cog("BanGif")

    @app_commands.command(name="config_gif", description="Affiche les options de configuration pour la gestion des GIFs")
    #@app_commands.checks.has_permissions(administrator=True)
    @admin_or_manage_messages()
    async def config_gif(self, interaction: discord.Interaction):
        """Affiche le menu principal avec des options de gestion des GIFs."""
        
        embed = discord.Embed(
            title="Menu de Configuration des GIFs",
            description="Choisissez une option pour configurer la gestion des GIFs sur ce serveur.",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed, view=MainMenuView(self.gif_cog, self.ban_gif_cog), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigGif(bot))
