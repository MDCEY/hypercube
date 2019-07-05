"""The glue the holds the api together."""
__version__ = "0.1.0"

import threading
import time

import hug
from hug import API
from hug.middleware import CORSMiddleware

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

api: API = API(__name__)
api.http.add_middleware(CORSMiddleware(api, allow_origins=["http://127.0.0.1:8080"]))
ROUTER = hug.route.API(__name__)


ROUTER.post('/add')(add_serial)
ROUTER.get('/read')(get_serials_of_interest)
ROUTER.post('/remove')(unregister_interest)
ROUTER.get('/update')(update_serial_of_interest)
ROUTER.get('/recent')(booked_in_today)
ROUTER.get('/stats/today')(daily_stats)
ROUTER.post('/average')(average_work_time)
ROUTER.get('/deadline')(deadline)


def update_db():
    """Run a loop in the background to update the tracked serials database."""
    next_call = time.time()
    while True:
        update_serial_of_interest()
        next_call = next_call + 30
        time.sleep(next_call - time.time())


def main():
    """Kick start web server and background tasks thread."""
    timer_thread = threading.Thread(target=update_db)
    timer_thread.daemon = True
    timer_thread.start()
    hug.development_runner.hug(module=__name__, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
