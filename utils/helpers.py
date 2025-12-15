import datetime


def humanize_date(val):
    if isinstance(val, (datetime.date, datetime.datetime)):
        ret = val.isoformat()
    else:
        ret = str(val)

    return ret