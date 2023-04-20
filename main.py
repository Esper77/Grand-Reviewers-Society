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
        return [x[0] for x in self._conn.execute("SELECT book_id FROM book")]

    def get_content(self):
        return [book for book in self._conn.execute("SELECT book_id, book_name FROM book")]

    def add(self, name, author):
        self._conn.execute('INSERT INTO book (book_name, author_id) values (?, ?)', (name, author))


class ReviewLibrary:
    def __init__(self, conn):
        self._conn = conn

    def add(self, user_id, book_id):
        self._conn.execute('INSERT INTO review (user_id, book_id) values (?, ?)', (user_id, book_id))
        return self.get_review_id(user_id, book_id)

    def open(self, user_id, book_id):
        self._conn.execute('UPDATE review SET is_closed = 0 WHERE user_id = (?) AND book_id = (?)', (user_id, book_id))

    def close(self, user_id):
        self._conn.execute('UPDATE review SET is_closed = 1 WHERE user_id = (?) AND is_closed = 0', (user_id, ))

    def get_ids(self, is_closed=None):
        if is_closed is None:
            return self._conn.execute("SELECT book_id, user_id FROM review")
        else:
            return self._conn.execute("SELECT book_id, user_id FROM review WHERE is_closed = ?", (is_closed, ))

    def update_specific(self, review_id, content):
        self._conn.execute("UPDATE review SET content = (?) WHERE review_id = (?)", (content, review_id))

    def approve(self, review_id):
        self._conn.execute("UPDATE review SET approved = 1 WHERE review_id = (?)", (review_id, ))

    def get_approval(self, approval=False):
        return [" ".join(x) for x in self._conn.execute("SELECT user_id, book_id FROM review WHERE approved = ?", (approval,))]

    def get_user_id(self, review_id):
        uid = [x for x in self._conn.execute('SELECT user_id FROM review WHERE review_id = (?)', (review_id,))]
        return uid[0][0]

    def get_review_id(self, user_id, book_id):
        rid = [x for x in self._conn.execute('SELECT review_id FROM review WHERE user_id = (?) and book_id = (?)', (user_id, book_id))]
        return rid[0][0]


class UserLibrary:
    def __init__(self, conn):
        self._conn = conn

    def get_ids(self, is_banned=None):
        if is_banned is None:
            return [x[0] for x in self._conn.execute("SELECT user_id FROM user")]
        else:
            return [x[0] for x in self._conn.execute("SELECT user_id FROM user WHERE is_banned = ?", (is_banned, ))]

    def add_id(self, user_id):
        return self._conn.execute('INSERT INTO user (user_id, user_name) values (?, ?)', (user_id, "User"))

    def get_with_perm(self, perms):
        request = f'SELECT user_id FROM user WHERE {perms[0]}=1'
        for perm in range(1, len(perms)):
            request += f" AND {perms[perm]}=1"
        return [x[0] for x in self._conn.execute(request)]

    def perm_grant(self):
        self._conn.execute('UPDATE user SET moderator_perm = 1 WHERE exp>50')
        self._conn.execute('UPDATE user SET author_perm = 1 WHERE exp>30')

    def get_exp(self, user_id):
        output = [x[0] for x in self._conn.execute('SELECT exp FROM user WHERE user_id = (?)', (user_id,))]
        return output[0]

    def give_exp(self, user_id):
        current_exp = self.get_exp(user_id)
        return self._conn.execute('UPDATE user SET exp = (?) WHERE user_id = (?)', (current_exp + 10, user_id))


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
        exp INT DEFAULT 0,
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
        review_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT,
        is_closed BOOL NOT NULL DEFAULT False,
        approved BOOL DEFAULT False 
        );""")
    con.execute("INSERT INTO book (book_name, author_id) values (?, ?)", ("Над пропастью во ржи", "NO"))
    con.execute("INSERT INTO book (book_name, author_id) values (?, ?)", ("Преступление и наказание", "NO"))
    con.execute("INSERT INTO book (book_name, author_id) values (?, ?)", ("Муму", "NO"))
    con.execute("INSERT INTO book (book_name, author_id) values (?, ?)", ("Записки охотника", "NO"))
    con.execute("INSERT INTO book (book_name, author_id) values (?, ?)", ("Метро 2033", "NO"))
    con.execute("INSERT INTO user (user_id, exp) values (?, ?)", (1884650937, 9999))


database_init()


@with_connection
def init_user(con, chat_id):
    if chat_id not in UserLibrary(con).get_ids():
        print("Added")
        con.execute('INSERT INTO user (user_id, user_name) values (?, ?)', (chat_id, "User"))


TOKEN = "5880785142:AAEU12-MT3jdVPk6M5reRQvEIFG3-QOABtk"
bot = telebot.TeleBot(token=TOKEN)


@bot.message_handler(commands=["start", "help"])  # This is a start module
def start(message):
    bot.send_message(message.chat.id, "Этот бот был создан для тренировки написания рецензий, их обмена и обмена книг. Чтобы получить список комманд напишите /commands")

    init_user(message.chat.id)


@bot.message_handler(commands=['commands'])
def commands(message):
    bot.send_message(message.chat.id, """/help - Инфо о боте
    /addbook - добавить книгу (от 30 опыта)
    /exp - посмотреть свой опыт
    /leaderboard - вывести топ-10 и своё место в топе""")

@bot.message_handler(commands=['leaderboard'])
def lb(message):
    pass

@bot.message_handler(commands=["force"])  # This is a forced mailing module for debug
def forced_mailing(message):
    mailing_send()


# Blacklist mode needed here

@bot.message_handler(commands=["addbook"])  # This is addition module for books
@with_connection
def book_add(con, message):
    chat_id = message.chat.id
    library = UserLibrary(con)
    if chat_id in library.get_with_perm(['author_perm']):
        answer = bot.send_message(chat_id, "Введите название книги")
        bot.register_next_step_handler(answer, book_confirmed)
    else:
        bot.send_message(chat_id, "У вас нет прав.")


@bot.message_handler(commands=["exp"])
@with_connection
def get_experience(con, message):
    chat_id = message.chat.id
    experience = UserLibrary(con).get_exp(chat_id)
    bot.send_message(chat_id, f"Ваш опыт: {experience}")


@with_connection
def book_confirmed(con, message):
    library = BookLibrary(con)
    text = message.text
    chat_id = message.chat.id
    library.add(text, chat_id)


# You should finish this already

@bot.callback_query_handler(func=lambda call: True)
@with_connection
def callback_operating(con, call):  # This is actually callback operating module
    library = ReviewLibrary(con)
    callback = call.data
    chat_id = call.message.chat.id
    try:
        if int(callback) in BookLibrary(con).get_ids():
            callback = int(callback)
            review_id = ReviewLibrary(con).add(chat_id, callback)
            if (callback, chat_id) not in library.get_ids():
                library.add(chat_id, callback)
                print(f"Review added ids:{callback, chat_id}")
                ans = bot.send_message(chat_id, "Добавление рецензии\nНапишите вашу рецензию следующим сообщением")
            else:
                library.open(chat_id, callback)
                print(f"Review update request ids: {callback, chat_id}")
                ans = bot.send_message(chat_id, "Обновление рецензии\nНапишите вашу рецензию следующим сообщением")
            bot.register_next_step_handler(ans, lambda message: operate_review(message, review_id))
    except ValueError:
        target_message_id = call.message.message_id
        callback = callback.split()
        empty_keyboard = types.InlineKeyboardMarkup()
        bot.edit_message_reply_markup(chat_id, target_message_id, reply_markup=empty_keyboard)
        if callback[1] == "True":
            UserLibrary(con).give_exp(ReviewLibrary(con).get_user_id(int(callback[0])))
            ReviewLibrary(con).approve(int(callback[0]))
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Обновить рецензию', callback_data=ReviewLibrary(con).get_ids()[0]))
            ans = bot.send_message(ReviewLibrary(con).get_user_id(callback[0]), "Ваша рецензия не была принята, попробуйте её пересмотреть", reply_markup=keyboard)


@with_connection
def operate_review(con, message, review_id):
    chat_id = message.chat.id
    text = message.text
    library = ReviewLibrary(con)
    library.update_specific(review_id, text)
    print("Review content added, data:", (chat_id, text))
    library.close(chat_id)

    approval_send(text, review_id)


@with_connection
def approval_send(con, text, review_id):

    library = UserLibrary(con)
    target_chat = choice(library.get_with_perm(['moderator_perm']))
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text=f"Хорошая", callback_data=f"{review_id} True")
    button2 = types.InlineKeyboardButton(text=f"Плохая", callback_data=f"{review_id} False")
    keyboard.row(button1, button2)
    bot.send_message(target_chat, "Рецензия на проверку:\n" + text, reply_markup=keyboard)


def check():
    schedule.every().saturday.at('19:00').do(mailing_send)
    perm_granting()
    while True:
        schedule.run_pending()
        time.sleep(1)
        print('OK')


@with_connection
def perm_granting(con):
    library = UserLibrary(con)
    library.perm_grant()


@with_connection
def mailing_send(con):  # Mailing module
    library = UserLibrary(con)
    users_data = library.get_ids(is_banned=False)
    books_data = BookLibrary(con).get_content()
    for user_info in users_data:
        keyboard = types.InlineKeyboardMarkup()
        chosen_books = set()
        while len(chosen_books) < 5:
            chosen_books.add(choice(books_data))
        for book in list(chosen_books):
            button1 = types.InlineKeyboardButton(text=f"{book[1]}", callback_data=book[0])
            keyboard.add(button1)
        bot.send_message(user_info, "Выберите книгу", reply_markup=keyboard)


passive_thread = Thread(target=check)

passive_thread.start()

bot.polling()
