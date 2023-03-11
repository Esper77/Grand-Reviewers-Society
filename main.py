import sqlite3 as sl
import time
import schedule
from random import randint
from threading import Thread
import telebot
from telebot import types


def database_init():
    con = sl.connect("application.db")
    con.execute("""CREATE TABLE user (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT DEFAULT User,
        author_perm BOOL DEFAULT False
        mod_perm BOOL DEFAULT False
        );""")
    con.execute("""CREATE TABLE book (
        book_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        book_name TEXT NOT NULL,
        author_id INTEGER NOT NULL
        );""")
    con.execute("""CREATE TABLE review (
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT,
        approved BOOL DEFAULT False
        );""")
    con.execute("""CREATE TABLE users_books (
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        started DATE NOT NULL
        );""")
    con.commit()

TOKEN = "5880785142:AAEU12-MT3jdVPk6M5reRQvEIFG3-QOABtk"
bot = telebot.TeleBot(token=TOKEN)

# This is a start module

@bot.message_handler(commands=["start"])
def start(message):
    con = sl.connect("application.db")
    chat_id = message.chat.id
    if chat_id not in [x[0] for x in con.execute("SELECT user_id FROM user")]:
        print("Added")
        con.execute('INSERT INTO user (user_id, user_name) values (?, ?)', (chat_id, "User"))
        con.commit()


bot.polling()
