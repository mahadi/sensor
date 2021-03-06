# coding=utf8

import sys
import time
import traceback
import signal
import telepot
from telepot.loop import MessageLoop
from sensor.DS18B20 import DS18B20
from sensor.HTU21D import HTU21D
from sensor.BMP180 import BMP180
from sensor.LCD1602 import LCD1602

"""
$ python3 indoor.py <token> <user_id>

An indoor climate monitor with 3 sensors and an LCD display.

It also comes with a Telegram bot that can report data periodically.

To know more about Telegram Bot and telepot, go to:
  https://github.com/nickoala/telepot
"""

ds = DS18B20('28-00000736781c')
htu = HTU21D(1, 0x40)
bmp = BMP180(1, 0x77)
lcd = LCD1602(1, 0x27)
lcd.clear()

def read_all():
    return ds.temperature(), htu.humidity(), bmp.pressure()

# Read sensors and display on LCD
def lcd_display():
    t, h, p = read_all()
    lcd.display('%.1f C    %.1f%%' % (t.C, h.RH), 1)
    lcd.display('   %.1f hPa' % p.hPa, 2)

# Read sensors and send to user
def read_send(chat_id):
    t, h, p = read_all()
    msg = '{:.1f}°C  {:.1f}%  {:,.1f}hPa'.format(t.C, h.RH, p.hPa)
    bot.sendMessage(chat_id, msg)

def handle(msg):
    global last_report, report_interval

    msg_type, chat_type, chat_id = telepot.glance(msg)

    # ignore non-text message
    if msg_type != 'text':
        return

    # only respond to one user
    if chat_id != USER_ID:
        return

    command = msg['text'].strip().lower()

    if command == '/now':
        read_send(chat_id)
    elif command == '/1m':
        read_send(chat_id)
        last_report = time.time()
        report_interval = 60    # report every 60 seconds
    elif command == '/1h':
        read_send(chat_id)
        last_report = time.time()
        report_interval = 3600  # report every 3600 seconds
    elif command == '/cancel':
        last_report = None
        report_interval = None  # clear periodic reporting
        bot.sendMessage(chat_id, "OK")
    else:
        bot.sendMessage(chat_id, "I don't understand")


def on_sigterm(signum, frame):
    sys.exit(0)
    # raise SystemExit so the `finally` clause gets executed

# catch termination signal so LCD is cleared
signal.signal(signal.SIGTERM, on_sigterm)


TOKEN = sys.argv[1]
USER_ID = int(sys.argv[2])

bot = telepot.Bot(TOKEN)

MessageLoop(bot, handle).run_as_thread()

# variables for periodic reporting
last_report = None
report_interval = None

try:
    while 1:
        lcd_display()

        # Is it time to report again?
        now = time.time()
        if report_interval is not None and last_report is not None and now - last_report >= report_interval:
            try:
                read_send(USER_ID)
                last_report = now
            except:
                traceback.print_exc()

        time.sleep(1)
finally:
    lcd.clear()
