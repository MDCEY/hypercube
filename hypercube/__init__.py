__version__ = "0.1.0"

import sched
import threading
import time

import hug

from hypercube.Model.local_db import SerialOfInterest
from hypercube.Model.local_db import Session as lsession
from hypercube.Model.selectors import (
    add_serial,
    booked_in_today,
    get_serials_of_interest,
    unregister_interest,
    update_serial_of_interest,
    daily_stats,
    average_work_time,
    deadline
)
from hypercube.Model.tesseract_db import Call, Product, Employ, FSR
from hypercube.Model.tesseract_db import Session as tsession

s = sched.scheduler(time.time, time.sleep)


api = hug.API(__name__)
api.http.add_middleware(hug.middleware.CORSMiddleware(api, max_age=10))


@hug.post("/add")
def add_register_interest(serial: hug.types.text):
    session = lsession()
    data = add_serial(session, SerialOfInterest, serial)
    lsession.remove()
    return data


@hug.get("/read")
def fetch_serials():
    session = lsession()

    data = get_serials_of_interest(session, SerialOfInterest)
    lsession.remove()

    return data


@hug.post("/remove")
def remove_serial(serial: hug.types.text):
    session = lsession()

    data = unregister_interest(session, SerialOfInterest, serial)
    lsession.remove()

    return data


@hug.get("/update")
def update_soi():
    tesseract_session = tsession()
    local_session = lsession()
    data = update_serial_of_interest(
        local_session, tesseract_session, SerialOfInterest, Call
    )
    tsession.remove()
    lsession.remove()
    return data


@hug.get("/recent")
def recently_added_calls():
    tesseract_session = tsession()
    data = booked_in_today(tesseract_session, Call, Product)
    tsession.remove()
    if not data:
        return False
    return data

@hug.get("/stats/today")
def todays_stats():
    tesseract_session = tsession()
    data = daily_stats(tesseract_session, Call, Employ, FSR)
    tsession.remove()
    if not data:
        return False
    return data

@hug.post("/average")
def fetch_average(product):
    session = tsession()
    data = average_work_time(session, FSR, product, Employ)
    tsession.remove()
    return data

@hug.get("/deadline")
def fetch_deadlines():
    session = tsession()
    data = deadline(session, Call, Product)
    tsession.remove()
    return data

def update_db():
    next_call = time.time()
    while True:
        update_soi()
        next_call = next_call + 30
        time.sleep(next_call - time.time())


def main():
    timerThread = threading.Thread(target=update_db)
    timerThread.daemon = True
    timerThread.start()
    hug.development_runner._start_api(api, "127.0.0.1", 8000, False, show_intro=False)
