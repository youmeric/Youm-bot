import os
from dotenv import load_dotenv
from keep_alive import keep_alive
import discord
from discord.ext import commands
import asyncio


load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Initialisation des intents pour lire le contenu des messages
intents = discord.Intents.default()
intents.message_content = True

# Initialisation du bot avec un préfixe de commande
bot = commands.Bot(command_prefix="!", intents=intents)

async def main():
    # Charger les extensions pour les fonctionnalités (cogs)
    try:
        await bot.load_extension("clear_cog")  # Charger l'extension clear
        print("Extension clear_cog chargée.")
    except Exception as e:
        print(f"Erreur de chargement clear_cog: {e}")

    try:
        await bot.load_extension("gif_cog")  # Charger l'extension gif_limit
        print("Extension gif_cog chargée.")
    except Exception as e:
        print(f"Erreur de chargement gif_cog: {e}")

    try:
        await bot.load_extension("ban_gif_cog")  # Charger l'extension ban_gif
        print("Extension ban_gif_cog chargée.")
    except Exception as e:
        print(f"Erreur de chargement ban_gif_cog: {e}")

    # Lancement du bot avec le token
    keep_alive()
    await bot.start(token)  # Remplace "TON_TOKEN_ICI" par ton token réel

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

# Démarrage du bot avec la fonction main
asyncio.run(main())






#NjE5NjE4MDkxNzgwODAwNTEz.GeVzua.KWObuq4dz6uj0dIc2zMjSpeJmUgXnVna7x1fzs