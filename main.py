import sqlite3 as sl
import time
import schedule
from random import choice
from threading import Thread
import telebot
from telebot import types


class BookLibrary:
    def __init__(self, conn):
        self._conn = conn

    def get_ids(self):
        return self._conn.execute("SELECT book_id FROM book")


class ReviewLibrary:
    def __init__(self, conn):
        self._conn = conn

    def add(self, user_id, book_id):
        self._conn.execute('INSERT INTO review (user_id, book_id) values (?, ?)', (user_id, book_id))

    def get_ids(self, is_closed=None):
        if is_closed is None:
            return self._conn.execute("SELECT book_id, user_id FROM review")
        else:
            return self._conn.execute("SELECT book_id, user_id FROM review WHERE is_closed = ?", (is_closed, ))

    def update_specific(self, user_id, content):
        self._conn.execute("UPDATE review SET content = (?) WHERE user_id = (?) AND is_closed = 0", (content, user_id))


class UserLibrary:
    def __init__(self, conn):
        self._conn = conn

    def ids(self, is_banned=None):
        if is_banned is None:
            return [x[0] for x in self._conn.execute("SELECT user_id FROM user")]
        else:
            return [x[0] for x in self._conn.execute("SELECT user_id FROM user WHERE is_banned = ?", (is_banned, ))]

    def add_id(self, user_id):
        return self._conn.execute('INSERT INTO user (user_id, user_name) values (?, ?)', (user_id, "User"))


def get_connection():
    return sl.connect("application.db")


def with_connection(func):
    def wrapper(*args):
        conn = get_connection()
        func(conn, *args)
        conn.commit()
        conn.close()

    return wrapper


@with_connection
def database_init(con):
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
        is_closed BOOL NOT NULL DEFAULT False,
        approved BOOL DEFAULT False
        );""")
    con.execute("INSERT INTO book (book_name, author_id) values (?, ?)", ("Над пропастью во ржи", "NO"))


# database_init()


@with_connection
def init_user(con, chat_id):
    if chat_id not in UserLibrary(con).ids():
        print("Added")
        con.execute('INSERT INTO user (user_id, user_name) values (?, ?)', (chat_id, "User"))


TOKEN = "5880785142:AAEU12-MT3jdVPk6M5reRQvEIFG3-QOABtk"
bot = telebot.TeleBot(token=TOKEN)


@bot.message_handler(commands=["start"])  # This is a start module
def start(message):
    init_user(message.chat.id)


@bot.message_handler(commands=["force"])  # This is a forced mailing module for debug
def forced_mailing(message):
    mailing_send()


# Blacklist mode needed here

"""
@bot.message_handler(commands=["add-book"])
def book_add(message):
    con = sl.connect("application.db")
    chat_id = message.chat.id
"""


@bot.callback_query_handler(func=lambda call: True)
@with_connection
def callback_operating(con, call):
    library = ReviewLibrary(con)
    callback = call.data
    chat_id = call.message.chat.id
    if callback not in BookLibrary(con).get_ids():
        if (callback, chat_id) not in library.get_ids():
            library.add(chat_id, callback)
            print(f"Review added ids:{callback, chat_id}")
            ans = bot.send_message(chat_id, "Напишите вашу рецензию следующим сообщением")
            bot.register_next_step_handler(ans, operate_review)


@with_connection
def operate_review(con, message):
    chat_id = message.chat.id
    text = message.text
    library = ReviewLibrary(con)
    library.update_specific(chat_id, text)
    print("Review content added, data:", (chat_id, text))


def mailing_check():
    schedule.every().saturday.at('19:00').do(mailing_send)
    while True:
        schedule.run_pending()
        time.sleep(1)
        print('OK')


@with_connection
def mailing_send(con):  # Mailing module
    library = UserLibrary(con)
    users_data = library.ids(is_banned=False)
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


remind_thread = Thread(target=mailing_check)

remind_thread.start()

bot.polling()
