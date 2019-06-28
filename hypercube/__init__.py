"""The glue the holds the api together."""
__version__ = "0.1.0"

import threading
import time
import typing

import hug
from hug import API
from hug.middleware import CORSMiddleware

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
    deadline,
)
from hypercube.Model.tesseract_db import Call, Product, Employ, FSR
from hypercube.Model.tesseract_db import Session as tsession


api: API = API(__name__)
api.http.add_middleware(CORSMiddleware(api, allow_origins=["http://127.0.0.1:8080"]))
router = hug.route.API(__name__)


def add_register_interest(serial: hug.types.text):
    """Request a Serial Number to be added to the tracker.

    Args:
        serial (str): serial number to add to tracker

    Returns:
        Whether or not adding the serial was successful

    """
    session = lsession()
    data = add_serial(session, SerialOfInterest, serial)
    lsession.remove()
    return data
router.post('/add')(add_register_interest)

def fetch_serials():
    """Fetch all tracked serial numbers from the local database.

    Returns:
        Tracked serial numbers from database

    """
    session = lsession()

    data = get_serials_of_interest(session, SerialOfInterest)
    lsession.remove()

    return data
router.get('/read')(fetch_serials)

def remove_serial(serial: hug.types.text) -> None:
    """Remove Serial from the tracking list.

    Args:
        serial (str): Serial number to be removed from tracker

    Returns:
        No value is returned

    """
    session = lsession()

    data = unregister_interest(session, SerialOfInterest, serial)
    lsession.remove()

    return data
router.post('/remove')(remove_serial)

def update_soi():
    """Request a scan of tesseract database for updates on the tracked serials.

    Returns:
        Tracked serial numbers from database

    """
    tesseract_session = tsession()
    local_session = lsession()
    data = update_serial_of_interest(
        local_session, tesseract_session, SerialOfInterest, Call
    )
    tsession.remove()
    lsession.remove()
    return data
router.get('/update')(update_soi)

def recently_added_calls():
    """Get a list of calls that have been created today.

    Returns:
        Calls created on the day of request

    """
    tesseract_session = tsession()
    data = booked_in_today(tesseract_session, Call, Product)
    tsession.remove()
    if not data:
        return []
    return data
router.get('/recent')(recently_added_calls)

def todays_stats():
    """Fetch all completed jobs and total worktime for today.

    Returns:
        A list of stats broken down by engineer. Includes work time and repair count

    """
    tesseract_session = tsession()
    data = daily_stats(tesseract_session, Call, Employ, FSR)
    tsession.remove()
    if not data:
        return False
    return data
router.get('/stats/today')(todays_stats)

def fetch_average(product: hug.types.text):
    """Fetch the average worktime of a product.

    Args:
        product: The product code for the unit in question

    Returns:
        Average time that it takes to repair an item

    """
    session = tsession()
    data = average_work_time(session, FSR, product, Employ)
    tsession.remove()
    return data
router.post('/average')(fetch_average)

def fetch_deadlines():
    """Fetch deadlines of open calls.

    Returns:
        All open calls and the deadline for their repair

    """
    session = tsession()
    data = deadline(session, Call, Product)
    tsession.remove()
    return data
router.get('/deadline')(fetch_deadlines)

def update_db():
    """Run a loop in the background to update the tracked serials database."""
    next_call = time.time()
    while True:
        update_soi()
        next_call = next_call + 30
        time.sleep(next_call - time.time())


def main():
    """Kick start web server and background tasks thread."""
    timerThread.daemon = True
    timerThread.start()
    hug.development_runner._start_api(api, "127.0.0.1", 8000, False, show_intro=False)
