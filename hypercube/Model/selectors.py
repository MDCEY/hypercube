"""Funcationality that the API calls on. AKA the brain."""
from datetime import datetime as dt
from datetime import timedelta as td
from sqlalchemy.sql import func

from hypercube.model.tesseract_db import Session as tesseract_session
from hypercube.model.tesseract_db import Call, Product, Employ, FSR


def __date_calc(days_to_add=None):
    """Add the defined number of days to the current date.

    Using the `days_to_add` add it to the current datetime to return
    the date that it would be in the specified number of days.

    :example:
        >>> __date_calc(days_to_add=1) == dt.now().date() + td(days=1)
        True

        >>> __date_calc()  == dt.now().date()
        True

    :param days_to_add: Number of days to add to today.
    :type days_to_add: int

    :return: The datetime object after the days to add have been
             applied
    :rtype: datetime.date

    """
    if not days_to_add:
        return dt.now().date()
    return dt.now().date() + td(days=days_to_add)


def booked_in_today():
    """Fetch all calls that have been created today.

    :return: A list of Calls, serial numbers
             and product information of everything that was booked in today
    :rtype: list[ dict[ str, any]]

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

    :return: A list of engineer's repairs
             for the current date, and the total time spent
             according to service reports
    :rtype: list[ dict[ str, any]

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

    :param product: Material number of a piece of equipment
    :type product: str

    :return:
    :rtype: list[ dict[ str, float]]


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

    :param engineer: The engineer number that is being looked up
    :type engineer: str

    :return: Total hours work completed as a decimal, for the provided engineer
    :rtype: float

    Todo:
        * If no record exists, None is returned. I need this to be a zero

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

    :return: A list of calls with the product,
             area and due dates
    :rtype: list[ dict[ str, any]]

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
