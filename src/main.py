import os
import time
import random

import telethon
from telethon import sync  # this module must be imported, although never used

from utils import conf, TgMessage, logger, channel_min_msg, db
from ml_ranker import MessageScorer
from train import tokenize_n_lemmatize

msg_scorer = MessageScorer()
msg_scorer.load_model()
logger.info('Session name %s, APP_ID %s', conf.SESSION_NAME, conf.APP_API_ID)

client = telethon.TelegramClient(conf.SESSION_NAME, conf.APP_API_ID, conf.APP_API_HASH)
logger.info(client)
client.start(phone=conf.PHONE_NUMBER)

async def main():
    chats = []
    debug_mode = os.getenv('DEBUG', 'true')
    is_user_authorized = await client.is_user_authorized()
    if is_user_authorized:
        while True:
            msg_cnt = 0
            channel_list = conf.read_channel_list()
            all_messages = db.loaded_messages()
            for channel in channel_list:
                channel_min_msg[channel] = db.get_max_message_id(from_channel=channel)
                async for message in client.iter_messages(
                    channel, wait_time=0, limit=conf.BATCH_SIZE
                ):
                    tg_msg = TgMessage(msg_id=int(message.id), msg_text=message.text, msg_channel=channel, msg_author=message.post_author)
                    if tg_msg.msg_hash in all_messages:
                        continue
                    if tg_msg.check_text() and not db.check_message(tg_msg.msg_hash):
                        if channel_min_msg[channel] is None:
                            channel_min_msg[channel] = tg_msg.id - conf.DEFAULT_SHIFT  # first run (empty DB)
                            logger.info('Min msg_id set to %d for channel %s', channel_min_msg[channel], channel)
                        if tg_msg.id <= channel_min_msg[channel]:
                            logger.info('All messages has been readed, min=%d, cur=%d', channel_min_msg[channel], tg_msg.id)
                            channel_min_msg[channel] = tg_msg.id
                            break
                        score = msg_scorer.score(tg_msg.txt)
                        db.add_message(tg_msg)  # for db insertion
                        msg_cnt += 1
                        if debug_mode == 'true':
                            logger.info('Score: %d, Msg: %s', score, tg_msg.txt)
                            if msg_cnt > 10:
                                raise RuntimeError
                        else:
                            time.sleep(15 + random.randint(-10, 10))
                            if score == 1:
                                await client.send_message(entity=conf.sink_chat, message=tg_msg.link)
                    db.add_message(tg_msg)
            logger.info('%d messages loaded. Waiting for new_messages...', msg_cnt)
            time.sleep(conf.REFRESH_INTERVAL)

if __name__ == '__main__':
    client.loop.run_until_complete(main())
