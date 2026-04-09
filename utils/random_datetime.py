# -*- coding: utf-8 -*-
"""
random_datetime.py: Generate a random datetime between two datetimes
"""

from datetime import date, datetime
from pytz import utc
from random import randint

def random_date(start_date : date, end_date : date = date(9999, 12, 31)):

    """
    random_date: generate a random date with year, month and day

    NOTE: you can then use dt.localize() to then cast to another datetime

    :param start_date: 

    :param end_date: 

    :return: a date with year, month and day
    """
    

    dt = None

    # keep looping until we find a valid date
    # this is not very elegant/efficient but handles the cases where we don't know that maximum number of days possible in a month, as this depends on the month, leap year, leap century, etc
    attempt = 0
    while dt is None:
        day = None
        month = None
        year = None
            
        try:
            year = randint(start_date.year, end_date.year)
            month = randint(start_date.month, end_date.month)
            day = randint(start_date.day, end_date.day)

            dt = date( year=year, month=month, day=day)

        except Exception as e:
            attempt += 1

            if attempt >= 50:
                module_logger.warning(f"Error creating random datetime ({e}) | day : {day}, month : {month}, year : {year} => trying again")

                # reset counter
                attempt = 0
                
                # try again...

    return dt

def random_utc_datetime(start_datetime : datetime, end_datetime : datetime = None, microseconds : bool = True, timezone : bool = True):

    """
    random_utc_datetime: generate a random datetime with year, month, day, hour, minute and second with UTC timezone

    NOTE: you can then use dt.localize() to then cast to another datetime

    :param start_datetime: start datetime; default is 1 1 1970

    :param end_datetime: end datetime; default is 31 12 9999

    :param microseconds: if True, random microseconds are added
        if False, no microseconds are added (set to 0)

    :param timezone: if True, UTC timezone is added
        if False, no timezone are added (set to None)

    :return: a datetime with year, month, day, hour, minute and second with UTC timezone
    """

    if end_datetime is None:
        end_datetime = datetime(9999, 12, 31, 23, 59, 59, 999999)
    

    dt = None



    # keep looping until we find a valid datetime
    # this is not very elegant/efficient but handles the cases where we don't know that maximum number of days possible in a month, as this depends on the month, leap year, leap century, etc
    attempt = 0
    while dt is None:
        try:
            year=randint(start_datetime.year, end_datetime.year)
            month=randint(start_datetime.month, end_datetime.month)
            day=randint(start_datetime.day, end_datetime.day)

            dt = datetime(  year=year
                            , month=month
                            , day=day
                            , hour=randint(start_datetime.hour, end_datetime.hour)
                            , minute=randint(start_datetime.minute, end_datetime.minute)
                            , second=randint(start_datetime.second, end_datetime.second)
                            , microsecond=randint(start_datetime.microsecond, end_datetime.microsecond) if microseconds else 0

                            # add UTC into the datetime
                            # NOTE: you can then use dt.localize() to then cast to another datetime
                            , tzinfo=utc if timezone else None
                        )
        except Exception as e:
            attempt += 1

            
            #module_logger.warning(f"Error creating random datetime ({e}) | attempt {attempt} | day : {day}, month : {month}, year : {year} => trying again")
                

    return dt

if __name__ == "__main__":

    def main():

        start_datetime = datetime(1970, 1, 1, 0, 0, 0)
        print(f"random_utc_datetime : {random_utc_datetime(start_datetime=start_datetime)}")

    # main entry point
    main()

    