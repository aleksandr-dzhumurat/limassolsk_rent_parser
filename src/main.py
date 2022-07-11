import os
import time

import telethon
from telethon import sync  # this module must be imported, although never used
from src.helpers import MessagesDB, conf, TgMessage, logger, check_text, channel_min_msg


logger.info('Session name %s, APP_ID %s', conf.SESSION_NAME, conf.APP_API_ID)
db = MessagesDB(conf)
db.init_db()
logger.info('database created')

client = telethon.TelegramClient(conf.SESSION_NAME, conf.APP_API_ID, conf.APP_API_HASH)
logger.info(client)
client.start(phone=conf.PHONE_NUMBER)

async def main():
    chats = []
    is_user_authorized = await client.is_user_authorized()
    if is_user_authorized:
        while True:
            msg_cnt = 0
            for channel in conf.channels:
                curr_msg_id = None
                channel_min_msg[channel] = db.get_max_message_id(from_channel=channel)
                logger.info('Min msg_id in database %s for channel', channel_min_msg[channel])
                async for message in client.iter_messages(
                    channel, wait_time=0, limit=conf.BATCH_SIZE
                ):
                    if len(message.text) > 10:
                        curr_msg_id = message.id
                        if channel_min_msg[channel] is None:
                            channel_min_msg[channel] = curr_msg_id - conf.DEFAULT_SHIFT  # first run (empty DB)
                            logger.info('Min msg_id set to %d for channel %s', channel_min_msg[channel], channel)
                        if curr_msg_id <= channel_min_msg[channel]:
                            logger.info('All messages has been readed, min=%d, cur=%d', channel_min_msg[channel], curr_msg_id)
                            break
                        cur_msg_text = message.text.replace('\n', ' ').lower()
                        if check_text(cur_msg_text):
                            db.add_message(TgMessage(msg_id=int(curr_msg_id), msg_text=cur_msg_text, msg_channel=channel))  # for db insertion
                            msg_cnt += 1
                            # await client.forward_messages(entity=conf.sink_chat, messages=curr_msg_id, from_peer=conf.channel_username)
                            await client.send_message(entity=conf.sink_chat, message=f'https://t.me/{channel}/{curr_msg_id}')
            logger.info('%d messages loaded. Waiting for new_messages...', msg_cnt)
            time.sleep(conf.REFRESH_INTERVAL)


if __name__ == '__main__':
    client.loop.run_until_complete(main())
