import discord
from discord import app_commands
from discord.ext import commands
import requests
import os

TOKEN = os.getenv("DISCORD_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/submit")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Bot conectado como {bot.user} y {len(synced)} comandos sincronizados.")
    except Exception as e:
        print(f"❌ Error al sincronizar comandos: {e}")

@bot.tree.command(name="submit", description="Envía tu script para que sea revisado")
@app_commands.describe(
    nombre="El nombre de tu script",
    juego="El juego para el que sirve",
    archivo="El archivo .lua o .txt con tu script"
)
async def submit(interaction: discord.Interaction, nombre: str, juego: str, archivo: discord.Attachment):
    await interaction.response.defer(ephemeral=True)
    
    # Intentar leer el archivo
    try:
        contenido_bytes = await archivo.read()
        contenido_texto = contenido_bytes.decode('utf-8')
    except Exception as e:
        # Aquí mostramos el error exacto para saber qué pasa
        await interaction.followup.send(f"❌ Error al leer el archivo: {e}. Asegúrate de que sea un texto válido.", ephemeral=True)
        return

    # Preparar datos para el backend
    data = {
        "nombre": nombre,
        "juego": juego,
        "autor": str(interaction.user),
        "codigo": contenido_texto
    }

    # Enviar al backend
    try:
        respuesta = requests.post(BACKEND_URL, json=data)
        if respuesta.status_code == 200:
            await interaction.followup.send(f"✅ ¡Gracias! Tu script **{nombre}** fue enviado a revisión.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error en el servidor (Código: {respuesta.status_code}). Inténtalo más tarde.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ No se pudo conectar con el servidor: {e}", ephemeral=True)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: No se encontró el TOKEN en las variables de entorno.")
