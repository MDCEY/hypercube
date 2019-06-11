from datetime import datetime as dt

def add_serial(session, table, serial):
    existing_serial = session.query(table).filter(table.serial_number==serial).count()
    if existing_serial != 0:
        return False
    else:
        row = table(serial_number=serial)
        session.add(row)
        session.commit()
        return True

def get_serials_of_interest(session, table):
    rows = session.query(table).all()
    for row in rows:
        print(row)
    return [{
        'id': row.id,
        'serial_number': row.serial_number,
        'date_added': row.date_added,
        'date_last_seen': row.date_last_seen,
        'data_pulled_at': dt.now()
    } for row in rows]

def unregister_interest(session, table, serial):
    row = session.query(table).filter(table.serial_number==serial).first()
    if not row:
        return False
    else:
        session.delete(row)
        session.commit()
        return True

def update_serial_of_interest(local_session, tesseract_session, local_db, tesseract_db):
    print("Updating SOI last seen")
    serials_of_interest = local_session.query(local_db).all()
    for row in serials_of_interest:
        unit_history = tesseract_session.query(tesseract_db).filter(tesseract_db.Call_Ser_Num == row.serial_number).order_by(tesseract_db.Call_Num.desc()).first()
        if unit_history:
            row.date_last_seen = unit_history.Call_InDate
            local_session.commit()

    return get_serials_of_interest(local_session,local_db)
