import sqlite3
import os
import logging
import time
from collections import defaultdict


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler("/srv/data/tg_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def def_value():
    return None

class Config:
    def __init__(self):
        self.SESSION_NAME = str(hash(time.time()))
        self.APP_API_ID = os.environ['APP_API_ID']
        self.APP_API_HASH = os.environ['APP_API_HASH']
        self.PHONE_NUMBER = os.environ['TG_PHONE']
        self.REFRESH_INTERVAL = 15 * 60  #  15 minutes
        self.BATCH_SIZE = 100
        self.DEFAULT_SHIFT = 500
        self.channels = ('CypRusPropertyChat', 'Cyprus_Prop')  # 'Limassolrentsale'
        self.sink_chat = os.environ['SINK_CHAT']
        self.db_file = os.environ['DB_FILENAME']
        self.sink_table = 'channel_messages'

conf = Config()

class TgMessage:
    def __init__(self, msg_id, msg_text, msg_channel):
        self.id = msg_id
        self.txt = msg_text
        self.channel = msg_channel

class DataBase:
    def __init__(self, config):
        self.conn = sqlite3.connect(config.db_file, check_same_thread=True)
        self.conf = config
    
    def run_sql(self, sql_str):
        with self.conn as con:
            res = con.execute(sql_str).fetchall()
        return res

class MessagesDB(DataBase):
    def __init__(self, config):
        super().__init__(config)

    def init_db(self):
        self.run_sql(f"""
                CREATE TABLE IF NOT EXISTS {self.conf.sink_table} (
                    id INTEGER NOT NULL,
                    msg TEXT,
                    channel TEXT
                );
        """)
        logger.info('table %s created', self.conf.sink_table)
    
    def get_max_message_id(self, from_channel: str):
        max_id = None
        res = self.run_sql(f"""SELECT MAX(id) FROM {self.conf.sink_table} WHERE channel='{from_channel}'""")
        if len(res) > 0:
            max_id = res[0][0]
        return max_id
    
    def add_message(self, msg: TgMessage):
        # sql_str = f"""INSERT INTO  {self.conf.sink_table} VALUES  ({msg.id}, '{msg.txt}', '{msg.channel}')"""
        sql_str = f"""INSERT INTO  {self.conf.sink_table} VALUES  ({msg.id}, '{msg.txt}', '{msg.channel}')"""
        self.run_sql(sql_str)

def check_text(msg: str) -> bool:
    res = True
    stop_words = ('looking', 'larnaca', 'sale', 'продажа', 'продаю', 'пафос', 'снимет', 'снимем', 'ищет', 'ищу', 'ищем', 'уборк', 'ларнака', 'интересует', 'рассмотрю')
    for word in stop_words:
        if word in msg:
            res = False
    return res


channel_min_msg = defaultdict(def_value)