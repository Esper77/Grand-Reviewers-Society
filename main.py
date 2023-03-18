import sqlite3 as sl
import time
import schedule
from random import choice
from threading import Thread
import telebot
from telebot import types


def database_init():
    con = sl.connect("application.db")
    con.execute("""CREATE TABLE user (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT DEFAULT User,
        author_perm BOOL DEFAULT False,
        moderator_perm BOOL DEFAULT False,
        is_banned BOOL DEFAULT False
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
    con.execute("INSERT INTO book (book_name, author_id) values (?, ?)", ("Над пропастью во ржи", "NO"))
    con.commit()
# database_init()


TOKEN = "5880785142:AAEU12-MT3jdVPk6M5reRQvEIFG3-QOABtk"
bot = telebot.TeleBot(token=TOKEN)


@bot.message_handler(commands=["start"])  # This is a start module
def start(message):
    con = sl.connect("application.db")
    chat_id = message.chat.id
    if chat_id not in [x[0] for x in con.execute("SELECT user_id FROM user")]:
        print("Added")
        con.execute('INSERT INTO user (user_id, user_name) values (?, ?)', (chat_id, "User"))
        con.commit()


@bot.message_handler(commands=["force"])
def forced_mailing(message):
    mailing_send()

# Blacklist mode needed here


@bot.message_handler(commands=["add-book"])
def book_add(message):
    con = sl.connect("application.db")
    chat_id = message.chat.id


def mailing_send():  # Mailing module
    con = sl.connect("application.db")
    users_data = [user_info[0] for user_info in con.execute("SELECT user_id FROM user WHERE NOT is_banned")]
    books_data = [book for book in con.execute("SELECT book_id, book_name FROM book")]
    for user_info in users_data:
        keyboard = types.InlineKeyboardMarkup()
        chosen_books = set()
        while len(chosen_books) < 5:
            chosen_books.add(choice(books_data))
            break  # !This is not a solution to the lack of books
        for book in list(chosen_books):
            button1 = types.InlineKeyboardButton(text=f"{book[1]}", callback_data=book[0])
            keyboard.add(button1)
        bot.send_message(user_info, "Выберите книгу", reply_markup=keyboard)


def mailing_check():
    schedule.every().saturday.at('19:00').do(mailing_send)
    while True:
        schedule.run_pending()
        time.sleep(1)
        print('OK')


remind_thread = Thread(target=mailing_check)

remind_thread.start()

bot.polling()
