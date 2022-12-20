from telegram import Bot as TelegramBot
from telegram import  Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram import Update

from dotenv import load_dotenv

import threading
import requests
import time
import json
import os

f = open("data.json", "r")
database = json.loads(f.read().strip())
database_lock = False
f.close()

load_dotenv() 

db_conn_string = os.environ.get('DB_CONN_STRING')
bot_token = os.environ.get('BOT_TOKEN')
register_pass = os.environ.get('REGISTER_PASSWORD')

def saveDb():
	global database, database_lock
	while database_lock:
		time.sleep(0.1)
	database_lock = True
	open("database.json", "w").write(json.dumps(database))
	database_lock = False

print(db_conn_string, bot_token, register_pass)