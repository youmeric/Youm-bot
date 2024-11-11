import os
from dotenv import load_dotenv
from keep_alive import keep_alive
import discord
from discord.ext import commands
import asyncio

# Charger le token depuis le fichier .env
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Initialisation des intents pour lire le contenu des messages
intents = discord.Intents.default()
intents.message_content = True

# Initialisation du bot avec un préfixe de commande
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    print("Extensions actuellement chargées :", bot.extensions)

    # Définir l'activité du bot
    activity = discord.Game(name="Surveiller les serveurs")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Synchroniser les commandes slash avec Discord
    print("Synchronisation des commandes slash...")
    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées avec succès : {[command.name for command in synced]}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes slash : {e}")

async def load_extensions():
    """Fonction pour charger les extensions"""
    try:
        await bot.load_extension("clear_cog")
        print("Extension clear_cog chargée.")
    except Exception as e:
        print(f"Erreur de chargement clear_cog: {e}")

    try:
        await bot.load_extension("gif_cog")
        print("Extension gif_cog chargée.")
    except Exception as e:
        print(f"Erreur de chargement gif_cog: {e}")

    try:
        await bot.load_extension("ban_gif_cog")
        print("Extension ban_gif_cog chargée.")
    except Exception as e:
        print(f"Erreur de chargement ban_gif_cog: {e}")

    try:
        await bot.load_extension("config_gif_cog")
        print("Extension config_gif_cog chargée.")
    except Exception as e:
        print(f"Erreur de chargement config_gif_cog: {e}")

async def main():
    await load_extensions()  # Charger toutes les extensions
    #keep_alive()  # Démarrer le service keep_alive si nécessaire
    await bot.start(token)  # Démarrer le bot avec le token

# Démarrage du bot avec la fonction main
asyncio.run(main())
