__version__ = '0.1.0'

import sched, time
import threading

from Model.local_db import Session as lsession, SerialOfInterest
from Model.tesseract_db import Session as tsession, Call, Product
from Model.selectors import add_serial, get_serials_of_interest, unregister_interest, update_serial_of_interest, booked_in_today
import hug

s = sched.scheduler(time.time, time.sleep)


api = hug.API(__name__)
api.http.add_middleware(hug.middleware.CORSMiddleware(api, max_age=10))

@hug.post('/add')
def add_register_interest(serial:hug.types.text):
    session = lsession()
    data = add_serial(session,SerialOfInterest,serial)
    lsession.remove()
    return data

@hug.get('/read')
def fetch_serials():
    session = lsession()

    data = get_serials_of_interest(session,SerialOfInterest)
    lsession.remove()

    return data

@hug.post('/remove')
def remove_serial(serial:hug.types.text):
    session = lsession()

    data = unregister_interest(session, SerialOfInterest, serial)
    lsession.remove()

    return data

@hug.get('/update')
def update_soi():
    tesseract_session = tsession()
    local_session = lsession()
    data = update_serial_of_interest(local_session,tesseract_session,SerialOfInterest,Call)
    tsession.remove()
    lsession.remove()
    return data

@hug.get('/recent')
def recently_added_calls():
    tesseract_session = tsession()
    data = booked_in_today(tesseract_session, Call, Product)
    tsession.remove()
    if not data:
        return False
    return data



def update_db():
    next_call = time.time()
    while True:
        update_soi()
        next_call = next_call + 30
        time.sleep(next_call - time.time())
    
timerThread = threading.Thread(target=update_db)
timerThread.daemon = True
timerThread.start()