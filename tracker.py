import logging
import requests
import time
import json
import _thread
import time
import rel
import os
import sys

import websocket
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

try:
    with open("zones.json", "r") as f:
        TERROR_ZONES = json.loads(f.read())
except FileNotFoundError:
    logger.error("No zones.json file found.")
    TERROR_ZONES = {}

last_dclone = None
cur_tz = None
next_tz = None

def on_error(ws, error):
    logger.error("WebSocket error: %s", error)

def on_close(ws, close_status_code, close_msg):
    logger.warning("WebSocket connection closed. Status code: %s, Message: %s", close_status_code, close_msg)

def on_open(ws):
    logger.info("WebSocket connection established")

def on_message(ws, message):
    logger.debug("Message received %s", message)
    data = json.loads(message)
    if "dclone" in data:
        dclone_handler(data)
    elif "tz" in data:
        tz_handler(data)
    else:
        pass

def tz_handler(data):
    global cur_tz, next_tz
    """
    Handles terror zone messages from the websocket
    Example message structure:
    {"tz": {"current": ["65"], "current_immunities": ["f", "p", "l", "m"], "current_num_boss_packs": [6, 8], 
    "current_superuniques": [], "delay": 600, "next": ["4"], "next_available_time_utc": 1741514999}}
    """
    for period in ["current", "next"]:
        if period not in data['tz']:
            logger.debug("%s not found in terror zone data", period)
            continue
            
        zone_ids = data['tz'][period]
        if not isinstance(zone_ids, list):
            logger.error("zone_ids is not a list")
            continue
        if not zone_ids:
            logger.debug("Empty zone_ids list received")
            continue

        zone_id = zone_ids[0]
        zone_data = TERROR_ZONES.get(str(zone_id))
        if zone_data:
            # Skip if zone hasn't changed
            if period == "current" and cur_tz == zone_id:
                logger.debug("Current terror zone has not changed")
                continue
            if period == "next" and next_tz == zone_id:
                logger.debug("Next terror zone has not changed")
                continue
            
            # Update tracked zones
            if period == "current":
                cur_tz = zone_id
            else:
                next_tz = zone_id
            
            logger.info("Terror zone info - period: %s, location: %s, tier: %s", 
                         period, zone_data['location'], zone_data['tier'])
            content = f"**{period.title()}** {zone_data['location']} -- {zone_data['tier']}-Tier"
            if zone_data['tier'] == 'S':
                content = f"{content}\nS-Tier Terror Zone - {os.getenv('TZONE_NOTIFY')}"
            message_discord(os.getenv('TZONE_WEBHOOK'), content)

        else:
            logger.error("Unknown zone ID: %s", zone_id)

def dclone_handler(data):
    global last_dclone
    hc_ladder_data = {}

    for k, v in data['dclone'].items():
        for val in ["krLadderHardcore", "usLadderHardcore", "euLadderHardcore"]:
            if k == val:
                del v['updated_at']
                hc_ladder_data[k] = v
    current = hc_ladder_data
    logger.debug("dclone handler - last: %s, current: %s", last_dclone, current)
    build_and_send_message(last_dclone, current)
    last_dclone = current

def build_and_send_message(last_dclone, current):
    keymap = {
                "krLadderHardcore": "Asia", 
                "usLadderHardcore": "US", 
                "euLadderHardcore": "Europe"
            }

    valmap = {
                0: "Terror gazes upon Sanctuary.", 
                1: "Terror approaches Sanctuary.", 
                2: "Terror begins to form within Sanctuary.", 
                3: "Terror spreads across Sanctuary.", 
                4: "Terror is about to be unleashed upon Sanctuary.", 
                5: "Diablo has invaded Sanctuary."
                }

    for k,v in current.items():
        if not last_dclone or last_dclone.get(k) != v:
            logger.info("Change detected in %s", {keymap[k]})
            content = f"**{keymap[k]}** Step {v['status']+1}/6: {valmap[v['status']]}>"
            if v['status'] != 0:
                content = f"{os.getenv('DCLONE_NOTIFY')} {content}"
            message_discord(os.getenv('DCLONE_WEBHOOK'), content)

def message_discord(webhook_url, content):
    logger.debug("Sending message to Discord %s", content)
    data = {
        "content": content,
    }
    try:
        r = requests.post(webhook_url, json=data)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Error sending message to Discord: %s", e)

if __name__ == "__main__":
    while True:
        try:
            ws = websocket.WebSocketApp("wss://d2emu.com/ws",
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close,
                                      on_open=on_open,
                                      header={"Authorization":"Basic {}".format(os.getenv('D2EMU_AUTH'))})
            ws.run_forever(dispatcher=rel, reconnect=5)
            rel.signal(2, rel.abort)  # Keyboard Interrupt
            rel.dispatch()
        except Exception as e:
            logger.error("Connection failed: %s. Retrying in 5 seconds...", e)
            time.sleep(5)