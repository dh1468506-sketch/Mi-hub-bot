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
    usuario_roblox="Tu nombre de usuario de Roblox (para mostrar tu foto)",
    archivo="El archivo .lua o .txt con tu script"
)
async def submit(interaction: discord.Interaction, nombre: str, juego: str, usuario_roblox: str, archivo: discord.Attachment):
    await interaction.response.defer(ephemeral=True)
    
    try:
        contenido_bytes = await archivo.read()
        try:
            contenido_texto = contenido_bytes.decode('utf-8')
        except UnicodeDecodeError:
            contenido_texto = contenido_bytes.decode('latin-1')
    except Exception as e:
        await interaction.followup.send(f"❌ Error al leer el archivo: {e}", ephemeral=True)
        return

    data = {
        "nombre": nombre,
        "juego": juego,
        "autor": str(interaction.user),
        "autor_roblox": usuario_roblox,
        "codigo": contenido_texto
    }

    try:
        respuesta = requests.post(BACKEND_URL, json=data)
        if respuesta.status_code == 200:
            await interaction.followup.send(f"✅ ¡Gracias! Tu script **{nombre}** fue enviado a revisión.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error en el servidor.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ No se pudo conectar con el servidor.", ephemeral=True)

@bot.tree.command(name="approve", description="Aprueba un script pendiente y lo sube a GitHub")
@app_commands.describe(id_script="El ID del script que aparece en el embed de moderación")
@app_commands.checks.has_permissions(administrator=True)
async def approve(interaction: discord.Interaction, id_script: str):
    await interaction.response.defer(ephemeral=True)
    url = f"{BACKEND_URL.replace('/submit', '')}/approve/{id_script}"
    try:
        respuesta = requests.post(url)
        if respuesta.status_code == 200:
            data = respuesta.json()
            if data.get("status") == "aprobado":
                await interaction.followup.send(f"✅ Script **{id_script}** aprobado y subido a GitHub.", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error: {data.get('error', 'Desconocido')}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error en el servidor.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ No se pudo conectar.", ephemeral=True)

@approve.error
async def approve_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ No tienes permisos.", ephemeral=True)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: No se encontró el TOKEN.")
