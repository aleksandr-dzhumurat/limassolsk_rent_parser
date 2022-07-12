import hashlib
import sqlite3
import os
import logging
import time
from collections import defaultdict


import demoji


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
        self.REFRESH_INTERVAL = 10  #  15 minutes
        self.BATCH_SIZE = 1000
        self.DEFAULT_SHIFT = 500
        self.sink_chat = os.environ['SINK_CHAT']
        self.data_dir = os.environ['DATA_DIR']
        self.db_file = os.path.join(self.data_dir, 'messages.db')
        self.tg_sources_file = os.path.join(self.data_dir, 'channel_list.tsv')
        self.sink_table = 'tg_messages'

conf = Config()

def read_channel_list() -> set:
    res = set()
    with open(conf.tg_sources_file, 'r') as f:
        for row in f.readlines():
            if len(row.strip()) > 0:
                res.add(row.strip())
    return res

class TgMessage:
    def __init__(self, msg_id, msg_text, msg_channel):
        self.id = msg_id
        if msg_text is not None:
            self.txt = demoji.replace(msg_text.replace('\n', ' ').lower().replace("'","_"))
        else:
            self.txt = ''
        self.channel = msg_channel
        self.link = f'https://t.me/{self.channel}/{self.id}'
        self.msg_hash = hashlib.md5(self.txt.encode('utf-8')).hexdigest()
    
    def check_text(self) -> bool:
        res = True
        if len(self.txt) <= 50:
            res = False
        stop_words = ('looking', 'larnaca', 'sale', 'сдан', 'office', 'офис','прода', 'айя', 'пафос', 'никоси', 'banned', 'сним', 'ищет', 'ищу', 'ищем', 'уборк', 'ларнака', 'интересует', 'рассмотрю')
        for word in stop_words:
            if word in self.txt:
                res = False
        return res

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
                    channel TEXT,
                    msg_hash TEXT
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
        sql_str = f"""INSERT INTO  {self.conf.sink_table} VALUES  ({msg.id}, '{msg.txt}', '{msg.channel}', '{msg.msg_hash}')"""
        self.run_sql(sql_str)
    
    def check_message(self, msg_hash: str):
        check = False
        res = self.run_sql(f"""SELECT COUNT(id) FROM {self.conf.sink_table} WHERE msg_hash='{msg_hash}'""")
        if res[0][0] > 0:
            check = True
        return check
    
    def loaded_messages(self) -> set:
        res = set()
        sql_res = self.run_sql(f"""SELECT msg_hash FROM {self.conf.sink_table}""")
        if len(res) > 1:
            for i in sql_res:
                res.add(i)
        logger.info('Total messages in DB: %d', len(res))
        return res


channel_min_msg = defaultdict(def_value)