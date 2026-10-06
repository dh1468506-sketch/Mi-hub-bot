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

# ==========================================
# COMANDO /submit - Enviar un script
# ==========================================
@bot.tree.command(name="submit", description="Envía tu script para que sea revisado")
@app_commands.describe(
    nombre="El nombre de tu script",
    juego="El juego para el que sirve",
    archivo="El archivo .lua o .txt con tu script"
)
async def submit(interaction: discord.Interaction, nombre: str, juego: str, archivo: discord.Attachment):
    await interaction.response.defer(ephemeral=True)
    
    # Intentar leer el archivo con tolerancia a errores de codificación
    try:
        contenido_bytes = await archivo.read()
        try:
            contenido_texto = contenido_bytes.decode('utf-8')
        except UnicodeDecodeError:
            contenido_texto = contenido_bytes.decode('latin-1')
    except Exception as e:
        await interaction.followup.send(f"❌ Error al leer el archivo: {e}", ephemeral=True)
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

# ==========================================
# COMANDO /approve - Aprobar un script y subirlo a GitHub
# ==========================================
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
                await interaction.followup.send(f"✅ Script **{id_script}** aprobado y subido a GitHub correctamente.", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error: {data.get('error', 'Desconocido')}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error en el servidor. Código: {respuesta.status_code}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ No se pudo conectar con el backend: {e}", ephemeral=True)

@approve.error
async def approve_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)

# ==========================================
# Iniciar el bot
# ==========================================
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: No se encontró el TOKEN en las variables de entorno.")
