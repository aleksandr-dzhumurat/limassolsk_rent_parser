"""
----------------------------
Train model
----------------------------
"""

import os
from typing import Dict
import requests
import pickle

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score, recall_score, confusion_matrix, roc_auc_score
import pymorphy2

from utils import conf, logger

from sklearn.ensemble import StackingClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC

from utils import prepare_dirs

url_stopwords_ru = "https://raw.githubusercontent.com/stopwords-iso/stopwords-ru/master/stopwords-ru.txt"

def get_text(url, encoding='utf-8', to_lower=True):
    logger.info('Wanting for %s', url)
    url = str(url)
    if url.startswith('http'):
        r = requests.get(url)
        if not r.ok:
            r.raise_for_status()
        return r.text.lower() if to_lower else r.text
    elif os.path.exists(url):
        with open(url, encoding=encoding) as f:
            return f.read().lower() if to_lower else f.read()
    else:
        raise Exception('parameter [url] can be either URL or a filename')

morph = pymorphy2.MorphAnalyzer()
stopwords = get_text(url_stopwords_ru).splitlines()

def normalize_tokens(tokens):
    return [morph.parse(tok)[0].normal_form for tok in tokens]

def remove_stopwords(tokens, stopwords=None, min_length=2):
    if not stopwords:
        return tokens
    stopwords = set(stopwords)
    tokens = [tok
            for tok in tokens
            if tok not in stopwords and len(tok) >= min_length]
    return tokens

def tokenize_n_lemmatize(text, regexp=r'(?u)\b\w{4,}\b'):
    from nltk import sent_tokenize, regexp_tokenize
    
    words = [w for sentence in sent_tokenize(text)
            for w in regexp_tokenize(sentence, regexp)]

    words = remove_stopwords(words, stopwords)
    words = normalize_tokens(words)
    return words

def prepare_nltk(root_data_dir: str = '/srv/data'):
    nltk_data_dir = os.path.join(root_data_dir, 'nltk_data')
    prepare_dirs(nltk_data_dir)
    import nltk

    nltk.download('punkt', download_dir=nltk_data_dir)
    nltk.download('stopwords', download_dir=nltk_data_dir)
    nltk.download('wordnet', download_dir=nltk_data_dir)  # Lemmas
    nltk.download('omw-1.4', download_dir=nltk_data_dir)  # Lemmas
    nltk.download(
        'averaged_perceptron_tagger',
        download_dir=nltk_data_dir)  # POS tags
    # тут почему-то корневую надо указывать ¯\_(ツ)_/¯
    nltk.data.path.append(nltk_data_dir)

if __name__ == '__main__':
    prepare_nltk()

    input_file = conf.raw_data_file
    if not os.path.exists(input_file):
        raise RuntimeError(f'No input file: {input_file}')
    df = pd.read_csv(input_file)
    train_df = df[df['subset'] == 'train']
    test_df = df[df['subset'] == 'test']
    logger.info('num rows for train: %d', train_df.shape[0])

    X_train = train_df['msg'].values
    y_train = train_df['label']

    X_test = test_df['msg'].values
    y_true = test_df['label']
    # fit 
    vectorizer = TfidfVectorizer(**conf.tf_idf_params).fit(X_train)
    X_train_csr = vectorizer.transform(X_train)
    lr = LogisticRegression().fit(X_train_csr, y_train)
    # predict
    X_test_csr = vectorizer.transform(X_test)
    y_pred = lr.predict(X_test_csr)
    cur_score = f1_score(y_true, y_pred)

    logger.info('best_score %.5f', cur_score)

    # ------ YOUR CODE HERE ----------- #
    print('Dataset collecting...')

    vectorizer = TfidfVectorizer(tokenizer=tokenize_n_lemmatize).fit(X_train)
    X_train_csr = vectorizer.transform(X_train)
    X_test_csr = vectorizer.transform(X_test)

    base_models = [('svm', SVC(gamma=0.44, random_state=0)), ('mnb', MultinomialNB(alpha=0.35))]
    meta_model = LogisticRegression()
    print('Training StackingClassifier...')
    stacking_model = StackingClassifier(estimators=base_models, 
                                        final_estimator=meta_model, 
                                        passthrough=True, 
                                        cv=2).fit(X_train_csr, y_train)
    y_train_pred = stacking_model.predict(X_train_csr)
    y_pred = stacking_model.predict(X_test_csr)

    logger.info('Confusion Matrix:\n%s', str(confusion_matrix(y_true, y_pred)))

    logger.info('train_f1: {:.5f} f1: {:.5f} accuracy: {:.5f} recall_score:{:.5f} AUC_score: {:.5f}'.format( 
                                f1_score(y_train, y_train_pred),
                                f1_score(y_true, y_pred),
                                accuracy_score(y_true, y_pred),
                                recall_score(y_true, y_pred),
                                roc_auc_score(y_true, y_pred)))

    with open(conf.vectorizer_path, 'wb') as fin:
        pickle.dump(vectorizer, fin)

    with open(conf.model_path, 'wb') as fin:
        pickle.dump(stacking_model, fin)
    # --------------------------------- #