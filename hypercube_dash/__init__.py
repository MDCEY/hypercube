__version__ = '0.1.0'

from Model.local_db import Session as lsession, SerialOfInterest
from Model.tesseract_db import Session as tsession, Call
from Model.selectors import add_serial, get_serials_of_interest, unregister_interest, update_serial_of_interest
import hug

api = hug.API(__name__)
api.http.add_middleware(hug.middleware.CORSMiddleware(api, max_age=10))

@hug.post('/add')
def add_register_interest(serial:hug.types.text):
    session = lsession()
    return add_serial(session,SerialOfInterest,serial)

@hug.get('/read')
def fetch_serials():
    session = lsession()
    return get_serials_of_interest(session,SerialOfInterest)

@hug.post('/remove')
def remove_serial(serial:hug.types.text):
    session = lsession()
    return unregister_interest(session, SerialOfInterest, serial)

@hug.get('/update')
def update_soi():
    return update_serial_of_interest(lsession(),tsession(),SerialOfInterest,Call)



