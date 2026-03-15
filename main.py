import os
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = os.environ["BOT_TOKEN"]

user_cities = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "Welcome to *Tell Me The Weather* 🌤\n\n"
        "I can tell you the weather for your city.\n\n"
        "First tell me your city."
    )

    await update.message.reply_text(message, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "📋 *Commands*\n\n"
        "/weather – current weather\n"
        "/forecast – forecast (3, 5 or 7 days)\n"
        "/changecity – change your city\n"
        "/help – show this message"
    )

    await update.message.reply_text(message, parse_mode="Markdown")


async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    city = update.message.text

    user_cities[user_id] = city

    await update.message.reply_text(
        f"City saved: {city}\n\nTry /weather or /forecast"
    )


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_id not in user_cities:
        await update.message.reply_text("Tell me your city first.")
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
        f"Weather in {city}\n🌡 {temp}°C\n💨 {wind} km/h"
    )


async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("3 days", callback_data="forecast_3"),
            InlineKeyboardButton("5 days", callback_data="forecast_5"),
            InlineKeyboardButton("7 days", callback_data="forecast_7"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "How many days forecast?",
        reply_markup=reply_markup
    )


async def forecast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_cities:
        await query.edit_message_text("Tell me your city first.")
        return

    city = user_cities[user_id]

    days = int(query.data.split("_")[1])

    geo = requests.get(
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    ).json()

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    data = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    ).json()

    dates = data["daily"]["time"][:days]
    max_t = data["daily"]["temperature_2m_max"][:days]
    min_t = data["daily"]["temperature_2m_min"][:days]

    msg = f"Forecast for {city}\n\n"

    for d, mx, mn in zip(dates, max_t, min_t):
        msg += f"{d}\n⬆ {mx}°C ⬇ {mn}°C\n\n"

    await query.edit_message_text(msg)


async def change_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tell me your new city.")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("forecast", forecast))
app.add_handler(CommandHandler("changecity", change_city))

app.add_handler(CallbackQueryHandler(forecast_callback, pattern="forecast_"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

print("Bot funcionando...")
app.run_polling()