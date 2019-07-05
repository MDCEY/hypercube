"""All logic relating to the serials of interest are contained within.

Log serial numbers that have been highlighted as problematic.
Scan Tesseracts database for updates on when the last call was
"""

from datetime import datetime as dt

from hypercube.model.local_db import Session as local_session
from hypercube.model.local_db import SerialOfInterest
from hypercube.model.tesseract_db import Session as tesseract_session
from hypercube.model.tesseract_db import Call


def add(serial):
    """Add a serial number to the table.

    :param serial: The serial number to add to the table
    :type serial: str

    :return: True if a serial number has been added. False otherwise
    :rtype: bool

    """
    session = local_session()
    if session.query(SerialOfInterest).filter().count():
        local_session.remove()
        return False
    row = SerialOfInterest(serial_number=serial)
    session.add(row)
    session.commit()
    local_session.remove()
    return True


def read():
    """Fetch all serials of interest from the database.

    :return: A list of all serial numbers along with when the unit was last seen.
    :rtype: list[ dict[ str: any]]

    """
    session = local_session()
    rows = session.query(SerialOfInterest).all()
    local_session.remove()
    return [
        {
            "id": row.id,
            "serial_number": row.serial_number,
            "date_added": row.date_added,
            "date_last_seen": row.date_last_seen,
            "data_pulled_at": dt.now(),
        }
        for row in rows
    ]


def delete(serial):
    """Remove a serial number from the database.

    :param serial: Serial number for removal
    :type serial: str

    :return: True if successful. Otherwise false
    :rtype: bool

    """
    session = local_session()
    row = session.query(SerialOfInterest).filter(SerialOfInterest.serial_number == serial).first()
    if row:
        session.delete(row)
        session.commit()
        session.remove()
        return True
    local_session.remove()
    return False


def update():
    """Update the serial numbers of interest table from tesseract.

    :return: A list of all serial numbers along with when the unit was last seen.
    :rtype: list[ dict[ str, any]]

    """
    l_session = local_session()
    t_session = tesseract_session()

    serials_of_interest = l_session.query(SerialOfInterest).all()
    for row in serials_of_interest:
        unit_history = (
            t_session.query(Call)
            .filter(Call.Call_Ser_Num == row.serial_number)
            .order_by(Call.Call_Num.desc())
            .first()
        )
        if unit_history:
            row.date_last_seen = unit_history.Call_InDate
            l_session.commit()
    local_session.remove()
    tesseract_session.remove()
    return read()
