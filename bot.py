from telegram import Bot as TelegramBot
from telegram import  Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram import Update

from dotenv import load_dotenv

import psycopg2
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

bot = TelegramBot(token=bot_token)

def sendMessage(chat_id, msg):
	bot.sendMessage(chat_id=chat_id, text=msg)

def saveDb():
	global database, database_lock
	while database_lock:
		time.sleep(0.1)
	database_lock = True
	open("data.json", "w").write(json.dumps(database))
	database_lock = False

def getItem(key, default_val=[]):
	item = database.get(key, -1)
	if item == -1:
		item = default_val
		database[key] = item
		saveDb()
	return item

def get_credits():
	conn = psycopg2.connect(db_conn_string)
	cursor = conn.cursor()
	cursor.execute("SELECT SUM(credits) FROM weekly_usage WHERE week=(SELECT week FROM weekly_usage ORDER BY week DESC LIMIT 1)")
	res = cursor.fetchone()
	conn.close()
	return int(res[0])

last_credits_notified = getItem("last_credits_notified", -1)

def credits_check():
	global last_credits_notified
	credits_now = get_credits()
	if credits_now != last_credits_notified:
		new_credits = 0
		if credits_now < last_credits_notified:
			new_credits = credits_now
		else:
			new_credits = credits_now - last_credits_notified
		database["last_credits_notified"] = credits_now
		saveDb()
		for chat_id in getItem("chats_to_notify"):
			sendMessage(f"Since last message, {new_credits} were used. Total this week: {credits_now}", chat_id)

def credits_loop():
	while True:
		credits_check()
		time.sleep(6 * 60 * 60) # 6 hrs

def start_command(update: Update, context: CallbackContext) -> None:
	update.message.reply_text("What are you even doing here?")

def now_command(update: Update, context: CallbackContext) -> None:
	update.message.reply_text("Ok boss.")
	credits_check()

def register_command(update: Update, context: CallbackContext) -> None:
	global database
	args = context.args
	if len(args) != 1:
		update.message.reply_text("Please pass your register password as an argument")
		return
	if args[0] != register_pass:
		update.message.reply_text("Nice try.")
		return
	chat_id = update.message.chat_id
	chats_to_notify = getItem("chats_to_notify")
	if chat_id not in chats_to_notify:
		chats_to_notify.append(chat_id)
	database["chats_to_notify"] = chats_to_notify
	saveDb()
	update.message.reply_text("Done, boss.")
	credits_check()

def startBot():
	updater = Updater(token=bot_token, use_context=True)
	dispatcher = updater.dispatcher
	start_handler = CommandHandler('start', start_command)
	register_handler = CommandHandler('register', register_command)
	now_handler = CommandHandler('now', now_command)
	dispatcher.add_handler(start_handler)
	dispatcher.add_handler(register_handler)
	dispatcher.add_handler(now_handler)
	updater.start_polling()

def main():
	while True:
		time.sleep(5)

if __name__ == "__main__":
	t = threading.Thread(target=startBot)
	t.start()
	main()