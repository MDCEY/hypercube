"""Funcationality that the API calls on. AKA the brain."""
from datetime import datetime as dt
import datetime
from datetime import timedelta as td
from typing import List, Dict, Any

from sqlalchemy.sql import func


def __date_calc(days_to_add=None) -> datetime.date:
    if not days_to_add:
        return dt.now().date()
    return dt.now().date() + td(days=days_to_add)


def add_serial(session, table, serial) -> bool:
    def __add_serial_to_local(session, table, serial):
        row = table(serial_number=serial)
        session.add(row)
        session.commit()

    def __serial_already_exists(session, table, serial) -> bool:
        if session.query(table).filter(table.serial_number == serial).count():
            return False
        return True
    # TODO: Code flow doesn't make sense
    if __serial_already_exists(session, table, serial):
        __add_serial_to_local(session, table, serial)
        return True
    else:
        return False


def get_serials_of_interest(session, table) -> List[Dict[str, Any]]:
    rows = session.query(table).all()
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


def unregister_interest(session, table, serial) -> bool:
    row = session.query(table).filter(table.serial_number == serial).first()
    if row:
        session.delete(row)
        session.commit()
        return True
    return False


def update_serial_of_interest(local_session, tesseract_session,
                              local_db, tesseract_db) -> List[Dict[str, Any]]:
    print("Updating SOI last seen")
    serials_of_interest = local_session.query(local_db).all()
    for row in serials_of_interest:
        unit_history = (
            tesseract_session.query(tesseract_db)
            .filter(tesseract_db.Call_Ser_Num == row.serial_number)
            .order_by(tesseract_db.Call_Num.desc())
            .first()
        )
        if unit_history:
            row.date_last_seen = unit_history.Call_InDate
            local_session.commit()

    return get_serials_of_interest(local_session, local_db)


def booked_in_today(tesseract_session, t_calls, t_prod) -> List[Dict[str, Any]]:
    rows = (
        tesseract_session.query(t_calls, t_prod)
        .join(t_prod, t_prod.Prod_Num == t_calls.Call_Prod_Num)
        .filter(t_calls.Call_InDate >= dt.now().date())
        .filter(t_calls.Call_Status == "WORK")
        .order_by(t_calls.Call_Num.desc())
    )
    return [
        {
            "call": row[0].Call_Num,
            "serial": row[0].Call_Ser_Num,
            "product": row[1].Prod_Desc,
            "addedAt": row[0].Call_InDate,
        }
        for row in rows
    ]


def daily_stats(tesseract_session, t_calls, t_employee, t_fsr) -> List[Dict[str, Any]]:
    rows = tesseract_session.query(t_calls).filter(
        t_calls.Job_CDate.between(__date_calc(), __date_calc(1)))
    engineers = set(row.Call_Employ_Num for row in rows)
    data = [
        {
            "engineer_name": tesseract_session.query(t_employee)
                             .filter(t_employee.Employ_Num == engineer)
                             .first()
                             .Employ_Name,
            "total": tesseract_session.query(t_calls)
                     .filter(t_calls.Job_CDate.between(__date_calc(), __date_calc(1)))
                     .filter(t_calls.Call_Employ_Num == engineer)
                     .count(),
            "work_time": __get_engineer_work_time(tesseract_session,
                                                  t_fsr, engineer),
        }
        for engineer in engineers
    ]
    return data


def average_work_time(tesseract_session, t_fsr, product, t_employee) -> List[Dict[str, float]]:
    rows = (
        tesseract_session.query(t_fsr, t_employee)
        .join(t_employee, t_employee.Employ_Num == t_fsr.FSR_Employ_Num)
        .filter(t_fsr.FSR_Prod_Num == product)
        .filter(t_employee.Employ_Para.like("%BK"))
        .with_entities(
            func.avg(t_fsr.FSR_Work_Time).label("average_work_time")
        )
        .one()
    )
    return [{"averageTime": rows.average_work_time * 60}]


def __get_engineer_work_time(tesseract_session, t_fsr, engineer) -> float:
    # TODO: If none then 0
    data = (
        tesseract_session.query(func.sum(
            t_fsr.FSR_Work_Time).label("Work_time"))
        .filter(
            t_fsr.FSR_Complete_Date.between(
                __date_calc(), __date_calc(1)
            )
        )
        .filter(t_fsr.FSR_Employ_Num == engineer)
        .first()[0]
    )
    return data


def deadline(tesseract_session, t_calls, t_prod) -> List[Dict[str, Any]]:
    rows = (
        tesseract_session.query(t_calls, t_prod)
        .join(t_prod, t_prod.Prod_Num == t_calls.Call_Prod_Num)
        .filter(t_calls.Call_Status == "WORK")
        .filter(t_calls.Job_CDate is None)
    )
    return [{
        "call": row[0].Call_Num,
        "area": row[0].Call_Area_Code,
        "product": row[1].Prod_Desc,
        "dueDate": row[0].Call_InDate + td(
            days=int(row[1].Prod_Ref2) if row[1].Prod_Ref2 else 999)
    }for row in rows]
