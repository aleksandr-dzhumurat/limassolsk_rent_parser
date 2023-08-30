import hashlib
import sqlite3
import os
import logging
import time
from collections import defaultdict

import yaml
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


def prepare_dirs(root_dir: str):
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)

def def_value():
    return None

if os.getenv("CONFIG_PATH") is None:
    config_path = "config.yml"
else:
    config_path = os.environ["CONFIG_PATH"]

with open(config_path, "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

class Config:
    def __init__(self, yml_conf):
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
        # ML data & params
        self.raw_data_file = os.path.join(yml_conf["data_dir"], "labeled_data_corpus.csv")
        self.model_path = os.path.join(yml_conf["data_dir"], yml_conf["model_file_name"])
        self.tf_idf_params = yml_conf["tf_idf_params"]
        self.vectorizer_path = os.path.join(yml_conf["data_dir"], yml_conf["vectorizer_file_name"])

    def read_channel_list(self) -> set:
        res = set()
        with open(self.tg_sources_file, 'r') as f:
            for row in f.readlines():
                if len(row.strip()) > 0:
                    res.add(row.strip())
        return res

conf = Config(config)

class TgMessage:
    def __init__(self, msg_id: str, msg_text: str, msg_channel: str, msg_author: str):
        self.id = msg_id
        if msg_text is not None:
            self.txt = demoji.replace(msg_text.replace('\n', ' ').lower().replace("'","_"))
        else:
            self.txt = ''
        self.channel = msg_channel
        self.link = f'https://t.me/{self.channel}/{self.id}'
        self.msg_hash = hashlib.md5(self.txt.encode('utf-8')).hexdigest()
        if msg_author is None:
            self.author = ''
        else:
            self.author = msg_author.lower()
    
    def check_text(self) -> bool:
        res = True
        if len(self.txt) <= 50:
            res = False
        if 'реклам' in self.author:
            res = False
        stop_words = ('looking', 'larnaca', 'sale', 'сдан', 'office', 'офис','прода', 'айя', 'пафос', 'никоси', 'banned', 'сним', 'ищет', 'ищу', 'ищем', 'уборк', 'ларнака', 'интересует', 'рассмотрю', 'реклам', 'бот', 'зарабатывать')
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
    
    def add_message(self, msg: TgMessage, msg_score=1):
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
        if len(sql_res) > 1:
            for i in sql_res:
                res.add(i[0])
        logger.info('Total messages in DB: %d', len(res))
        return res


channel_min_msg = defaultdict(def_value)

db = MessagesDB(conf)
db.init_db()
logger.info('database created')