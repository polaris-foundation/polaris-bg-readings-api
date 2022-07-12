from flask_batteries_included.sqldb import db


def reset_database() -> None:
    session = db.session
    session.execute("TRUNCATE TABLE patient_alert cascade")
    session.execute("TRUNCATE TABLE amber_alert cascade")
    session.execute("TRUNCATE TABLE red_alert cascade")
    session.execute("TRUNCATE TABLE patient cascade")
    session.execute("TRUNCATE TABLE hba1c_reading cascade")
    session.execute("TRUNCATE TABLE dose")
    session.execute("TRUNCATE TABLE reading cascade")
    session.execute("TRUNCATE TABLE reading_metadata cascade")
    session.commit()
    session.close()
