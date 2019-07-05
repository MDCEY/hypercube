"""Funcationality that the API calls on. AKA the brain."""
from datetime import datetime as dt
from datetime import timedelta as td
from sqlalchemy.sql import func

from hypercube.model.local_db import Session as local_session
from hypercube.model.tesseract_db import Session as tesseract_session
from hypercube.model.local_db import SerialOfInterest
from hypercube.model.tesseract_db import Call, Product, Employ, FSR


def __date_calc(days_to_add=None):
    """Add defined value of days to the current date.

    :param days_to_add: Number of days to add to today.
    :type days_to_add: int

    :return: The datetime object after the days to add have been
             applied
    :rtype: datetime.date

    """
    if not days_to_add:
        return dt.now().date()
    return dt.now().date() + td(days=days_to_add)


def add_serial(serial):
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


def get_serials_of_interest():
    """Fetch all serials of interest from the database.

    Returns:
        A list of all serial numbers along with when the unit was last seen.

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


def unregister_interest(serial):
    """Remove a serial number from the database.

    Args:
        serial (str): The serial number to add to the table

    Returns:
        bool: True if the a row was found a deleted otherwise false

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


def update_serial_of_interest():
    """Update the serial numbers of interest table from tesseract.

    Returns:
        List[Dict[str,Any]: A list of all serial numbers along with when the unit was last seen.

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
    return get_serials_of_interest()


def booked_in_today():
    """Fetch all calls that have been created today.

    Returns:
        List[Dict[str,Any]: A list of Calls, serial numbers
        and product information of everything that was booked in today


    """
    session = tesseract_session()
    rows = (
        session.query(Call, Product)
        .join(Product, Product.Prod_Num == Call.Call_Prod_Num)
        .filter(Call.Call_InDate >= dt.now().date())
        .filter(Call.Call_Status == "WORK")
        .order_by(Call.Call_Num.desc())
    )
    tesseract_session.remove()
    return [
        {
            "call": row[0].Call_Num,
            "serial": row[0].Call_Ser_Num,
            "product": row[1].Prod_Desc,
            "addedAt": row[0].Call_InDate,
        }
        for row in rows
    ]


def daily_stats():
    """Fetch Engineers repair stats for current day.

    Returns:
       List[Dict[str,Any]: A list of engineer's repairs
       for the current date, and the total time spent
       according to service reports

    """
    session = tesseract_session()
    rows = session.query(Call).filter(
        Call.Job_CDate.between(__date_calc(), __date_calc(1)))
    engineers = set(row.Call_Employ_Num for row in rows)
    data = [
        {
            "engineer_name": session.query(Employ)
                             .filter(Employ.Employ_Num == engineer)
                             .first()
                             .Employ_Name,
            "total": session.query(Call)
                     .filter(Call.Job_CDate.between(__date_calc(), __date_calc(1)))
                     .filter(Call.Call_Employ_Num == engineer)
                     .count(),
            "work_time": __get_engineer_work_time(engineer),
        }
        for engineer in engineers
    ]
    tesseract_session.remove()
    return data


def average_work_time(product):
    """Fetch the average time it takes to repair a unit.

    Args:
        product (str): The product code to get the average time off

    Returns:
        List[Dict[str, float]]: The average time it takes for an engineer to repair an product

    """
    session = tesseract_session()
    rows = (
        session.query(FSR, Employ)
        .join(Employ, Employ.Employ_Num == FSR.FSR_Employ_Num)
        .filter(FSR.FSR_Prod_Num == product)
        .filter(Employ.Employ_Para.like("%BK"))
        .with_entities(
            func.avg(FSR.FSR_Work_Time).label("average_work_time")
        )
        .one()
    )
    tesseract_session.remove()
    return [{"averageTime": rows.average_work_time * 60}]


def __get_engineer_work_time(engineer):
    """Fetch the overall work time of a specified engineer with todays date.

    Args:
        engineer (str): The selected engineer to retrieve information off

    Returns:
        float: Total hours work completed as a decimal, for the provided engineer

    Todo:
        * If none then 0

    """
    session = tesseract_session()
    data = (
        session.query(func.sum(FSR.FSR_Work_Time).label("Work_time"))
        .filter(FSR.FSR_Complete_Date.between(__date_calc(), __date_calc(1)))
        .filter(FSR.FSR_Employ_Num == engineer)
        .first()[0]
    )
    tesseract_session.remove()
    return data


def deadline():
    """Fetch a list of all open calls and the time it has to be repaired by.

    Returns:
        List[Dict[str,Any]: A list of calls with the product,
        area and due dates

    """
    session = tesseract_session()
    rows = (
        session.query(Call, Product)
        .join(Product, Product.Prod_Num == Call.Call_Prod_Num)
        .filter(Call.Call_Status == "WORK")
        .filter(Call.Job_CDate is None)
    )
    tesseract_session.remove()
    return [{
        "call": row[0].Call_Num,
        "area": row[0].Call_Area_Code,
        "product": row[1].Prod_Desc,
        "dueDate": row[0].Call_InDate + td(
            days=int(row[1].Prod_Ref2) if row[1].Prod_Ref2 else 999)
    }for row in rows]
