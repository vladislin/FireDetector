from telegram.ext import Updater, CommandHandler
import psycopg2 as sq
from threading import Thread
from PIL import Image
import io


BOT_TOKEN = "800792656:AAF3UcFpElvjeG3q3b-Q9JjRVSEn_c_Y6JE"
database = sq.connect('postgres://lzfllcfvvyspsq:ce5e2cb0b0e63af2a6afef0a4077018567ce8638750d9f7'
                      '56c76b86e78255a9c@ec2-54-247-85-251.eu-west-1.compute.amazonaws.com:5432'
                      '/ddmeddrk3fhuln', sslmode='require')


class TelegramUsersDataBase:
    def __init__(self):
        self.telegram_database = database
        self.cursor = self.telegram_database.cursor()

    def create_table(self):
        try:
            self.cursor.execute("""CREATE TABLE telegram_user(first_name TEXT DEFAULT NULL ,
                                        last_name TEXT DEFAULT NULL,username TEXT NOT NULL ,
                                        chat_id INTEGER NOT NULL UNIQUE,
                                        user_referrer INTEGER DEFAULT NULL )""")
            print("DONE")
            self.telegram_database.commit()
        except:
            self.telegram_database.rollback()
            return

    def add_new_user(self, *args):
        try:
            self.cursor.execute("""INSERT INTO telegram_user VALUES (%s, %s, %s, %s)""", args)
            self.telegram_database.commit()
        except:
            self.telegram_database.rollback()

    def add_referral(self, referrer_id, referral_id):
        try:
            self.cursor.execute("""UPDATE telegram_user SET user_referrer = %s WHERE user_referrer is NULL AND
                                    chat_id = %s""", (referrer_id, referral_id,))
            self.telegram_database.commit()
        except:
            self.telegram_database.rollback()

    def select_referrals(self, referral_id):
        self.cursor.execute("""SELECT chat_id FROM telegram_user WHERE user_referrer = %s"""
                            , (referral_id,))
        return self.cursor.fetchall()

    def get_img(self, chat_id):
        try:
            self.cursor.execute("""SELECT img FROM telegram_user WHERE chat_id = %s""",
                                (chat_id,))
            return self.cursor.fetchone()[0]
        except:
            self.telegram_database.rollback()
            return 0

    @staticmethod
    def check_user_exist(chat_id):
        try:
            cursor = database.cursor()
            cursor.execute("""SELECT EXISTS(SELECT 1 FROM telegram_user
                                            WHERE chat_id = %s)""", (chat_id,))
            return cursor.fetchone()[0]
        except:
            database.rollback()
            return


class TelegramBot:
    def __init__(self):
        self.updater = Updater(token=BOT_TOKEN)
        self.bot_users_database = TelegramUsersDataBase
        self.bot_users_database().create_table()
        self.bot_url = 'https://t.me/Fire_DetectorBot'
        self.updater.dispatcher.add_handler(CommandHandler('start', self.new_chat_user))
        self.updater.dispatcher.add_handler(CommandHandler('help', self.help_message))
        self.updater.dispatcher.add_handler(CommandHandler('check', self.send_check_photo))
        self.updater.dispatcher.add_handler(CommandHandler('settings', self.user_settings))
        self.updater.dispatcher.add_handler(CommandHandler('my_referral_link', self.get_referral_link))

    @staticmethod
    def get_bot_commands():
        return {'/start': 'Begin your chat', '/my_referral_link': 'Get referral link',
                '/check': 'Take a photo at the moment', '/help': 'List of bot commands'}

    def start_bot(self):
        self.updater.start_polling()

    def help_message(self, bot, update):
        chat_id = update.message.chat_id
        command = self.get_bot_commands()
        help_message = ''
        for key in command.keys():
            help_message += "{0} - {1}\n".format(key, command[key])
        bot.sendMessage(chat_id=chat_id, text=help_message)

    def new_chat_user(self, bot, update):
        chat_id = update.message.chat_id
        message = update.message.text.split('/start ', 1)
        if self.bot_users_database.check_user_exist(chat_id):
            bot.sendMessage(chat_id=chat_id, text="{0}, you're already start this bot".
                            format(update.message.from_user.first_name))
        else:
            try:
                self.bot_users_database().add_new_user(update.message.from_user.first_name,
                                                       update.message.from_user.last_name,
                                                       update.message.from_user.username,chat_id)
                bot.sendMessage(chat_id=chat_id, text="Hello, {0}".format(update.message.from_user.first_name))
            except:
                bot.sendMessage(chat_id=chat_id, text="Please, try later")
        if len(message) == 2:
            self.bot_users_database().add_referral(message[1], chat_id)

    def send_check_photo(self, bot, update):
        chat_id = update.message.chat_id
        photo = self.bot_users_database().get_img(chat_id)
        if photo == 0:
            bot.sendMessage(chat_id=chat_id, text='Please, try later')
        photo_file = io.BytesIO(photo)
        image = Image.open(photo_file)
        photo_file.name = 'image.jpg'
        image.save(photo_file, 'JPEG')
        photo_file.seek(0)
        bot.sendPhoto(chat_id=chat_id, photo=photo_file)
        referrals_id = self.bot_users_database().select_referrals(referral_id=chat_id)
        if len(referrals_id) > 0:
            for ref_id in referrals_id:
                Thread(target=self.send_to_referrals, args=(bot, ref_id[0], chat_id,)).start()

    def send_to_referrals(self, bot, ref_id, chat_id):
        photo = self.bot_users_database().get_img(chat_id)
        photo_file = io.BytesIO(photo)
        image = Image.open(photo_file)
        photo_file.name = 'image.jpg'
        image.save(photo_file, 'JPEG')
        photo_file.seek(0)
        bot.sendPhoto(chat_id=ref_id, photo=photo_file)

    def user_settings(self, bot, update):
        pass

    def get_referral_link(self, bot, update):
        chat_id = update.message.chat_id
        referral_link = self.bot_url + '?start=' + str(chat_id)
        bot.sendMessage(chat_id=chat_id, text=referral_link)

if __name__ == '__main__':
    x = TelegramBot()
    x.start_bot()
