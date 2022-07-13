import pickle

from utils import conf, logger
from train import tokenize_n_lemmatize, prepare_nltk

prepare_nltk()

class MessageScorer:
    def __init__(self):
        self.model = None
        self.vectorizer = None

    def load_model(self):
        logger.info('Loading model from %s', conf.model_path)
        with open(conf.model_path, 'rb') as f:
            self.model = pickle.load(f)
            logger.info('Model loaded %s', self.model)
        with open(conf.vectorizer_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
            logger.info('Vectorizer loaded %s', self.vectorizer)
        logger.info('Models created')
    
    def score(self, msg: str):
        input = self.vectorizer.transform([msg])
        msg_score = self.model.predict(input)

        return msg_score[0]


def run_sql(sql_str, db_con, cols = None):
    with db_con as con:
        res = pd.DataFrame(con.execute(sql_str).fetchall(), columns=cols)
    return res

# msg_scorer = MessageScorer()
# msg_scorer.load_model()


if __name__=='__main__':
    import sqlite3
    import pandas as pd

    db_file = '/srv/data/messages.db'
    conn = sqlite3.connect(db_file, check_same_thread=True)
    TABLE_NAME = 'tg_messages'
    table_df = pd.read_sql_query(f"SELECT id, msg from {TABLE_NAME} LIMIT 30", conn)

    for _, row in table_df.iterrows():
        if len(row[1]) > 10:
            print(row[1])
            print(msg_scorer.score(row[1]))
            print('---' * 10)