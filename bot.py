import discord
from discord.ext import commands
import supabase
import random
import string
from datetime import datetime, timedelta
import os

TOKEN = os.getenv("TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

def generate_key(length=16):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def get_days_from_duration(duration: str):
    try:
        days = int(duration.replace("d", ""))
        if days in [1, 7, 14, 30]:
            return days
        return None
    except:
        return None

@bot.command(name="key")
async def create_key(ctx, duration: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ У тебя нет прав создавать ключи!")
        return
    
    days = get_days_from_duration(duration)
    if not days:
        await ctx.send("❌ Используй: `!key 1d`, `!key 7d`, `!key 14d`, `!key 30d`")
        return
    
    key = generate_key()
    expires_at = datetime.now() + timedelta(days=days)
    
    try:
        supabase_client.table("keys").insert({
            "key": key,
            "expires_at": expires_at.isoformat(),
            "created_by": str(ctx.author.id)
        }).execute()
        
        embed = discord.Embed(title="🔑 Новый ключ создан!", color=0x00ff00)
        embed.add_field(name="Ключ", value=f"`{key}`", inline=False)
        embed.add_field(name="Действует до", value=expires_at.strftime("%d.%m.%Y %H:%M"), inline=True)
        embed.add_field(name="Дней", value=f"{days}", inline=True)
        embed.set_footer(text=f"Создал: {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot.command(name="keys")
async def list_keys(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ У тебя нет прав!")
        return
    
    try:
        response = supabase_client.table("keys").select("*").execute()
        keys = response.data
        
        if not keys:
            await ctx.send("📭 Нет активных ключей.")
            return
        
        keys = sorted(keys, key=lambda x: x["created_at"], reverse=True)
        
        embed = discord.Embed(title="📋 Список ключей", color=0x00aaff)
        
        for k in keys[:20]:
            status = "✅" if not k["used"] else "❌"
            expires = datetime.fromisoformat(k["expires_at"]).strftime("%d.%m")
            embed.add_field(
                name=f"{status} `{k['key']}`",
                value=f"До: {expires} | Создан: {k['created_at'][:10]}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot.event
async def on_ready():
    print(f"✅ Бот запущен! Имя: {bot.user.name}")

bot.run(TOKEN)