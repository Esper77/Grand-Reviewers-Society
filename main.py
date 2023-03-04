import sqlite3 as sl
import time
import schedule
from random import randint
from threading import Thread
import telebot
from telebot import types


con = sl.connect("application.db")
con.execute("""CREATE TABLE user (
    user_id INT PRIMARY KEY NOT NULL,
    user_name TEXT DEFAULT User,
    author_perm BOOL DEFAULT False
    );""")
con.commit()

TOKEN = "5880785142:AAEU12-MT3jdVPk6M5reRQvEIFG3-QOABtk"
bot = telebot.TeleBot(token=TOKEN)

# List of ids declined the mailing
blacklist_ids = set()

# Dict of all ids for specification
mailing_queue = {}

# This is a start module


@bot.message_handler(commands=["start"])
def start(message):
    con = sl.connect("application.db")
    chat_id = message.chat.id
    print(type(chat_id))
    if chat_id not in con.execute("SELECT user_id FROM user"):
        con.executemany('INSERT INTO user (user_id, name) values(?, ?)', [(chat_id, "User")])

bot.polling()
