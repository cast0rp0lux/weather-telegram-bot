import os
import requests

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.environ["BOT_TOKEN"]

user_cities = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¿En qué ciudad estás?")


async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    city = update.message.text

    user_cities[user_id] = city

    await update.message.reply_text(
        f"Perfecto. Guardé tu ciudad: {city}\nAhora usa /weather"
    )


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_id not in user_cities:
        await update.message.reply_text("Primero dime tu ciudad.")
        return

    city = user_cities[user_id]

    geo = requests.get(
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    ).json()

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    data = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    ).json()

    temp = data["current_weather"]["temperature"]
    wind = data["current_weather"]["windspeed"]

    await update.message.reply_text(
        f"Tiempo en {city}\n🌡 {temp}°C\n💨 {wind} km/h"
    )


async def change_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Dime tu nueva ciudad.")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("changecity", change_city))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

print("Bot funcionando...")
app.run_polling()