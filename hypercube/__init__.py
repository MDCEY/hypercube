"""The glue the holds the api together."""
__version__ = "0.1.0"
import threading
import asyncio
import json
import os
import time
import tkinter
from tkinter import *
from datetime import datetime as dt
import logging
from functools import wraps
from functools import partial
import pusher
from contextlib import suppress
import traceback
import tracemalloc
import requests
import socket
import urllib3

# from model import serials_of_interest
from model.selectors import (
    booked_in_today,
    daily_stats,
    average_work_time,
    deadline,
    update_site,
)

channels_client = pusher.Pusher(
    app_id=os.getenv("PUSHER_APP_ID"),
    key=os.getenv("PUSHER_APP_KEY"),
    secret=os.getenv("PUSHER_APP_SECRET"),
    cluster="eu",
    ssl=True,
)


async def run_tk(root, interval=0.01):
    try:
        while True:
            root.update()
            await asyncio.sleep(interval)
    except tkinter.TclError as e:
        if "application has been destroyed" not in e.args[0]:
            raise


async def pusher_update():
    last_call = {"stats": [], "calls": []}
    while True:
        while pusher_radio_val.get():
            print(f"{dt.now()}: Running stats")
            data_out = {"stats": await daily_stats(), "calls": await booked_in_today()}
            if not last_call == data_out:
                data_age.set(f"Data last updated at\n{str(dt.now())}")
                try:
                    print(json.dumps(data_out))
                    channels_client.trigger("hypercube", "update", json.dumps(data_out))
                except requests.exceptions.ProxyError:
                    print("Proxy connection failed. Retrying in 15 seconds")
                    await asyncio.sleep(15)
                    continue
                last_call = data_out
            elif  pusher_force_val.get():
                print(f"{dt.now()}: Forced")
                data_age.set(f"Data last updated at\n{str(dt.now())}")
                try:
                    channels_client.trigger("hypercube", "update", json.dumps(data_out))
                except requests.exceptions.ProxyError:
                    print("Proxy connection failed. Retrying in 15 seconds")
                    await asyncio.sleep(15)
                    continue
                except socket.timeout:
                    print("Connection Timedout. Retrying in 15 seconds")
                    await asyncio.sleep(15)
                    continue
                except urllib3.exceptions.ReadTimeoutError:
                    print("Connection Timedout. Retrying in 15 seconds")
                    await asyncio.sleep(15)
                    continue                   
                except requests.exceptions.ReadTimeout:
                    print("Connection Timedout. Retrying in 15 seconds")
                    await asyncio.sleep(15)
                    continue   
                last_call = data_out
            await asyncio.sleep(30) 
        await asyncio.sleep(30)

        

def toggle_pusher(value):
    global active

    print(f"Toggling server state to {value}")
    active = value


async def main():
    await asyncio.gather(run_tk(root), pusher_update())


root = Tk()
root.wm_attributes("-topmost", 1)
root.geometry("200x600")
for i in range(11):
    root.columnconfigure(i, {"minsize": 10})

# Pusher GUI
Label(root, text="Hypercube").pack(fil=X)

pusher_group = LabelFrame(root, text="Pusher", padx=5, pady=5)
pusher_group.pack(fill=X, expand=1, padx=10, pady=10, side=TOP)
data_age = StringVar()
data_age.set("Awaiting First Sync")
label_data_age = Label(pusher_group, textvariable=data_age)
label_data_age.pack(fill=X, expand=1)
pusher_radio_val = BooleanVar()
pusher_radio_1 = Radiobutton(
    pusher_group, text="On", value=True, variable=pusher_radio_val
)
pusher_radio_1.pack(expand=1, side=RIGHT)
pusher_radio_2 = Radiobutton(
    pusher_group, text="Off", value=False, variable=pusher_radio_val
)
pusher_radio_2.pack(expand=1, side=LEFT)

pusher_force_val = BooleanVar()
pusher_force = Checkbutton(
    pusher_group, text="Force", variable=pusher_force_val, onvalue=True, offvalue=False
)
pusher_force.pack(side=LEFT)

# Serialize Site
site_group = LabelFrame(root, text="Site Add", padx=5, pady=5)
site_group.pack(fill=X, expand=1, padx=10, pady=10, side=TOP)
site_label = Label(site_group, text="Site Number")
site_label.pack(fill=X, expand=1)
site_entry = Entry(site_group)
site_entry.pack(fill=X, expand=1)


def trigger_site_update():
    global site_entry
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(update_site(site_entry.get()), loop=loop)
    site_entry.delete(0, END)


site_submit = Button(site_group, text="Submit", command=trigger_site_update)
site_submit.pack(fill=X, expand=1)
asyncio.run(main())

# command=partial(toggle_pusher, False)
