"""Funcationality that the API calls on. AKA the brain."""
from datetime import datetime as dt
from datetime import timedelta as td
import asyncio
from sqlalchemy.sql import func, distinct
from sqlalchemy.orm import Query, Load
from sqlalchemy import and_


from .tesseract_db import Session as tesseract_session
from .tesseract_db import Call, Product, Employ, FSR, Site


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


async def booked_in_today():
    """Fetch all calls that have been created today.

    :return: A list of Calls, serial numbers
             and product information of everything that was booked in today
    :rtype: list[ dict[ str, any]]

    """
    session = tesseract_session()
    query = (
        Query(Call, Product)
        .join(Product, Product.Prod_Num == Call.Call_Prod_Num)
        .filter(Call.Call_InDate >= dt.now().date())
        .filter(Call.Call_Status == "WORK")
        .with_entities(
            Call.Call_Num, Call.Call_Ser_Num, Product.Prod_Desc, Call.Call_InDate
        )
        .order_by(Call.Call_Num.desc())
        .limit(20)
    )
    result = session.execute(query)
    data = []
    if result.returns_rows:
        result = result.fetchall()
        for row in result:
            await asyncio.sleep(0)
            data.append(
                {
                    "call": row[0],
                    "serial": row[1],
                    "product": row[2],
                    "addedAt": str(row[3]),
                }
            )
    tesseract_session.remove()
    return data


async def daily_stats():
    """Fetch Engineers repair stats for current day.

    :return: A list of engineer's repairs
             for the current date, and the total time spent
             according to service reports
    :rtype: list[ dict[ str, any]

    """
    session = tesseract_session()
    query = (
        Query([Call, FSR, Employ])
        .join(Employ, Employ.Employ_Num == Call.Call_Employ_Num)
        .join(
            FSR,
            and_(
                FSR.FSR_Call_Num == Call.Call_Num, Call.Call_Last_FSR_Num == FSR.FSR_Num
            ),
        )
        .filter(Call.Job_CDate.between(__date_calc(), __date_calc(1)))
        .filter(Employ.Employ_Para.like("%BK"))
        .filter(~Employ.Employ_Num.in_(["431", "402"]))
        .with_entities(
            func.count(FSR.FSR_Call_Num).label("total"),
            func.sum(FSR.FSR_Work_Time).label("work_time"),
            Employ.Employ_Name.label("engineer_name"),
        )
        .group_by(Employ.Employ_Name)
        .order_by(Employ.Employ_Name)
    )

    result = session.execute(query)
    if result.returns_rows:
        results = result.fetchall()
        data = [
            {
                "engineer_name": result[2].split(" ")[0],
                "total": result[0],
                "work_time": str(result[1]),
            }
            for result in results
        ]
    else:
        data = []
    await asyncio.sleep(0)
    tesseract_session.remove()
    return data


async def update_site(site_number):
    session = tesseract_session()
    query = Query(Site).filter(Site.Site_Num == site_number)
    result = session.execute(query)
    if result.returns_rows:
        result = result.fetchone()
        if result["SCSite_Site_Stock_Serialised"] == "N":
            result["SCSite_Site_Stock_Serialised"] = "Y"
            session.commit()
            print(f"{result['SCSite_Site_Num']} is now serialized")
        else:
            print(f"{result['SCSite_Site_Num']} is already serialized")
    tesseract_session.remove()


async def average_work_time(product):
    """Fetch the average time it takes to repair a unit.

    :param product: Material number of a piece of equipment
    :type product: str

    :return:
    :rtype: list[ dict[ str, float]]


    """
    session = tesseract_session()
    await asyncio.sleep(0.05)

    rows = (
        session.query(FSR, Employ)
        .join(Employ, Employ.Employ_Num == FSR.FSR_Employ_Num)
        .filter(FSR.FSR_Prod_Num == product)
        .filter(Employ.Employ_Para.like("%BK"))
        .with_entities(func.avg(FSR.FSR_Work_Time).label("average_work_time"))
        .one()
    )
    await asyncio.sleep(0.05)
    tesseract_session.remove()
    return [{"averageTime": rows.average_work_time * 60}]


async def __get_engineer_work_time(engineer):
    """Fetch the overall work time of a specified engineer with todays date.

    :param engineer: The engineer number that is being looked up
    :type engineer: str

    :return: Total hours work completed as a decimal, for the provided engineer
    :rtype: float

    Todo:
        * If no record exists, None is returned. I need this to be a zero

    """
    session = tesseract_session()
    query = (
        Query(func.sum(FSR.FSR_Work_Time).label("Work_time"))
        .filter(FSR.FSR_Complete_Date.between(__date_calc(), __date_calc(1)))
        .filter(FSR.FSR_Employ_Num == engineer)
    )
    result = session.execute(query)
    if result.returns_rows:
        result = result.fetchone()[0]
    tesseract_session.remove()
    if not result:
        result = 0
    return result


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
    return [
        {
            "call": row[0].Call_Num,
            "area": row[0].Call_Area_Code,
            "product": row[1].Prod_Desc,
            "dueDate": row[0].Call_InDate
            + td(days=int(row[1].Prod_Ref2) if row[1].Prod_Ref2 else 999),
        }
        for row in rows
    ]
