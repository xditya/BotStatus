# (c) @xditya
# This file is a part of https://github.com/xditya/BotStatus

import asyncio
import logging
import time
import datetime

import pytz
from decouple import config
from telethon import TelegramClient, functions
from telethon.sessions import StringSession

# initializing logger
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s"
)
log = logging.getLogger("BotStatus")

# fetching variales from env
try:
    APP_ID = config("APP_ID", cast=int)
    API_HASH = config("API_HASH")
    SESSION = config("SESSION")
    LIST_BOTS = config("BOTS")
    CHANNEL_ID = config("CHANNEL_ID", cast=int)
    MESSAGE_ID = config("MESSAGE_ID", cast=int)
    CHANNEL_NAME = config("CHANNEL_NAME", default="@BotzHub")
    TIME_ZONE = config("TIME_ZONE", default="Asia/Kolkata")
except BaseException as ex:
    log.info(ex)
    exit(1)

BOTS = LIST_BOTS.split()

log.info("Connecting bot.")
try:
    client = TelegramClient(
        StringSession(SESSION), api_id=APP_ID, api_hash=API_HASH
    ).start()
except BaseException as e:
    log.warning(e)
    exit(1)


# perform checks
async def check_bots():
    start_time = time.time()
    bot_stats = {}
    log.info("[CHECK] Started periodic checks...")
    channel_current_msg = await client.get_messages(CHANNEL_ID, ids=MESSAGE_ID)
    new_message = (
        "⚠️ **New periodic check in progress...** ⚠️\n\n" + channel_current_msg.text
    )
    try:
        await client.edit_message(CHANNEL_ID, MESSAGE_ID, new_message)
    except BaseException as e:
        log.warning("[EDIT] Unable to edit message in the channel!")
        log.error(e)

    for bot in BOTS:
        time_before_sending = time.time()
        try:
            # send a msg to the bot
            sent_msg = await client.send_message(bot, "/start")
            await asyncio.sleep(10)
            history = await client(
                functions.messages.GetHistoryRequest(
                    peer=bot,
                    offset_id=0,
                    offset_date=None,
                    add_offset=0,
                    limit=1,
                    max_id=0,
                    min_id=0,
                    hash=0,
                )
            )
            if sent_msg.id == history.messages[0].id:
                # save stats in a dict
                bot_stats[bot] = {
                    "response_time": None,
                    "status": "❌",
                }
            else:
                time_after_sending = time.time()
                time_taken_for_response = time_after_sending - time_before_sending

                # save stats in a dict.
                bot_stats[bot] = {
                    "response_time": f"`{round(time_taken_for_response * 1000, 3)}ms`",  # convert to ms for readability
                    "status": "✅",
                }
        except BaseException:
            bot_stats[bot] = {
                "response_time": "",
                "status": "❌",
            }
        await client.send_read_acknowledge(bot)
        log.info(f"[CHECK] Checked @{bot} - {bot_stats[bot]['status']}.")

    end_time = time.time()
    total_time_taken = end_time - start_time
    log.info("[CHECK] Completed periodic checks.")

    # form the message
    status_message = f"**{CHANNEL_NAME}** - __Bot Status__\n\n"
    for bot, value in bot_stats.items():
        status_message += (
            f"» {value['status']} @{bot}\n"
            if bot_stats[bot]["response_time"] is None
            else f"» {bot_stats[bot]['status']} @{bot} [ {bot_stats[bot]['response_time']} ]\n"
        )

    # add time taken to check
    hours = int(total_time_taken // 3600)
    minutes = int((total_time_taken % 3600) // 60)
    seconds = int(total_time_taken % 60)
    status_message += f"\n**Checked in** `"
    time_added = False
    if hours > 0:
        time_added = True
        status_message += f"{hours}h "
    if minutes > 0:
        time_added = True
        status_message += f"{minutes}m "
    if seconds > 0:
        time_added = True
        status_message += f"{seconds}s "
    if not time_added:
        status_message += f"{round(total_time_taken * 1000)}ms"
    status_message += "`\n"

    # add last checked time
    current_time_utc = datetime.datetime.now(pytz.utc)
    current_time = current_time_utc.astimezone(pytz.timezone(TIME_ZONE))
    status_message += f"**Last checked at** `{current_time.strftime('%H:%M:%S - %d %B %Y')}` [ __{TIME_ZONE}__ ]"

    # add auto check message
    status_message += f"\n\n**This message will be updated every 2 hours.**"

    # edit the message in the channel
    try:
        await client.edit_message(CHANNEL_ID, MESSAGE_ID, status_message)
    except BaseException as e:
        log.warning("[EDIT] Unable to edit message in the channel!")
        log.error(e)
        return


client.loop.run_until_complete(check_bots())
