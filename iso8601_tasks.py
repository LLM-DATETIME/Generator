# -*- coding: utf-8 -*-
"""
iso8601_tasks.py: Various tasks based on an ISO-8601 input datetime

INPUT
ISO-8601 datetime

TARGET
Another ISO-8601 datetime which is the result of some task. Currently supported tasks are:
    - add.day.1 : add 1 day
    - add.day.2 : add 2 days
    - subtract.day.1 : subtract 1 day
    - subtract.day.2 : subtract 2 days

BASE
N/A

MODIFICATIONS

BACKLOG

USAGE
python3 iso8601_tasks.py add.hours.1000 10
python3 iso8601_tasks.py add.day.1 10

# only observations where the month has changed
python3 iso8601_tasks.py add.day.1 10 

python3 iso8601_tasks.py add.day.250 1000 --same_month 0
python3 iso8601_tasks.py add.days.1-250 1000 --same_month 0
"""

# -------
# imports
# -------

from collections import namedtuple
from datetime import date, datetime, time, timedelta
from random import randint
from string import digits, ascii_letters
from typing import Any, List, Set, Dict, Tuple, Optional, Union, Iterable, Iterator

from utils.check_isinstance import check_isinstance
from utils.random_datetime import random_utc_datetime

from utils.training_pair import TrainingPair

# logging
from utils.logger import logger_dl
module_logger = logger_dl.getChild(f"iso8601_tasks")


# -----
# class
# -----

class Generate:

    """
    Generate a sample of dates for training
    """

    def __init__(self, debug : bool = False, debug2 : bool = False):

        self.debug = debug
        self.debug2 = debug2

        # the core datalake type being generated (see Config.core_pandas_type_map)
        self.model_name = "ISO-8601-TASKS"

      
    def generate(self
                , output : str
                , num_observations : int
                , same_month : Optional[int] = None
                , start_date = None # for compatibility with the generic signature of the generate() function
                , end_date = None # for compatibility with the generic signature of the generate() function
                , schemas : List[str] = None
                ) -> Iterator[ Tuple[ TrainingPair, Any] ]:

        """

        :param output: what do generate: pattern

        :param num_observations: amount of numbers to generate; each numner will be generated in various scales, locales, formats, etc.

        :param same_month: define what do to if the month of the output datetime is different to the month of the input datetime
            * 0 or None: all observations are kept, regardless if output month is the same or different from the input month
            
            * 1: only the observations are kept where the output month is the same the input month
            
            * -1: only the observations are kept where the output month is different to the input month
                if the year is different, observation is discarded   
            
        :param start_date: optional; start date(time) of the dates; a default value will be generated if None

        :return: function is a generator -> an iterator of 2-tuples
            1. TrainingPairs (namedtuple)
            2. the input number

        """

        # schemas not supported
        assert schemas is None, "argument 'schemas' not supported"

        check_isinstance(same_month, int, none_ok=True)
        if same_month is None:
            same_month = 0

        if self.debug:
            module_logger.debug(f"Generating {num_observations} observations with output '{output}' for task '{output}' with same_month '{same_month}'")

        # set start date
        if start_date is None:
            start_date = datetime(1970, 1, 1, 0, 0, 0)
        else:
            # assume ISO-8601 and conver
            if not isinstance(start_date, datetime):
                start_date = datetime.fromisoformat(start_date)
            
        if end_date is None:
            end_date = datetime(9999, 12, 31, 0, 0, 0)
        else:
            if not isinstance(end_date, datetime):
                end_date = datetime.fromisoformat(end_date)

        if self.debug:
            module_logger.debug(f"starting on {start_date} ({type(start_date)}) | end_date : {end_date} ({type(end_date)})")

        assert isinstance(output, str)
       
        idx = 0
        while idx != num_observations:

            # NOTE: align with generate16.23 "iso8601" format
            # no microseconds and no timezone => ISO8601 output is '7648-09-12 02:24:13'
            input_dt = random_utc_datetime(start_datetime=start_date
                                           , end_datetime=end_date
                                           , microseconds=False
                                           , timezone=False
                                           )

            if self.debug:
                module_logger.debug(f"input_dt : {input_dt}")
            
            # same ISO8601 format as generate16.23, using isoformat()
            input_str = input_dt.isoformat()
            
            if output == "model":
                output_str = self.model_name
            
            elif output == "add.day.1":
                output_dt = input_dt + timedelta(days=1)
                output_str = output_dt.isoformat()

            elif output == "add.day.2":
                output_dt = input_dt + timedelta(days=2)
                output_str = output_dt.isoformat()

            elif output == "add.day.10":
                output_dt = input_dt + timedelta(days=10)
                output_str = output_dt.isoformat()

            elif output == "add.day.20":
                output_dt = input_dt + timedelta(days=20)
                output_str = output_dt.isoformat()

            elif output == "add.day.50":
                try:
                    output_dt = input_dt + timedelta(days=50)
                except Exception as e:
                    continue
                output_str = output_dt.isoformat()

            elif output == "add.day.100":
                try:
                    output_dt = input_dt + timedelta(days=100)
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue
            
            elif output in ("add.day.250", "add.day.250.x"):
                try:
                    output_dt = input_dt + timedelta(days=250)
                    output_str = output_dt.isoformat()
                    
                except OverflowError as e:
                    # date value out of range
                    continue

                if output.endswith(".x"):
                    # add.day.250.x: input is a dict with the input_sequence and num_days; allows re-using prompts across many different num_days
                    input_str = {
                                    "input_sequence" : input_str
                                    , "num_days" : 250
                        }


            elif output == "add.day.250.i":
                """
                add.day.250.i: input is a dict with the input_sequence, num_days and two rendered examples for Few-Shot prompts
                allows re-using prompts across many different num_days
                """
                try:
                    output_dt = input_dt + timedelta(days=250)
                    output_str = output_dt.isoformat()

                    input_dt_1 = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
                    assert input_dt_1 != input_dt
                    input_str_1 = input_dt_1.isoformat()

                    input_dt_2 = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
                    assert input_dt_2 != input_dt
                    assert input_dt_2 != input_dt_1
                    input_str_2 = input_dt_2.isoformat()

                    input_str = {
                                "input_sequence" : input_str
                                 , "num_days" : 250
                                 , "input_fs_1" : input_str_1
                                 , "target_fs_1" : (input_dt_1 + timedelta(days=250)).isoformat()
                                 , "input_fs_2" : input_str_2
                                 , "target_fs_2" : (input_dt_2 + timedelta(days=250)).isoformat()
                                 }

                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.500":
                try:
                    output_dt = input_dt + timedelta(days=500)
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output in ("add.day.1000", "add.day.1000.x"):
                try:
                    output_dt = input_dt + timedelta(days=1000)
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

                if output.endswith(".x"):
                    # add.day.250.x: input is a dict with the input_sequence and num_days; allows re-using prompts across many different num_days
                    input_str = {
                                    "input_sequence" : input_str
                                    , "num_days" : 1000
                        }

            elif output in ("add.day.2500", "add.day.2500.x"):
                try:
                    output_dt = input_dt + timedelta(days=2500)
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

                if output.endswith(".x"):
                    # add.day.250.x: input is a dict with the input_sequence and num_days; allows re-using prompts across many different num_days
                    input_str = {
                                    "input_sequence" : input_str
                                    , "num_days" : 2500
                        }

            elif output == "add.day.250.i":
                """
                add.day.250.i: input is a dict with the input_sequence and num_days
                allows re-using prompts across many different num_days
                """
                try:
                    output_dt = input_dt + timedelta(days=250)
                    output_str = output_dt.isoformat()

                    input_dt_1 = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
                    assert input_dt_1 != input_dt
                    input_str_1 = input_dt_1.isoformat()

                    input_dt_2 = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
                    assert input_dt_2 != input_dt
                    assert input_dt_2 != input_dt_1
                    input_str_2 = input_dt_2.isoformat()

                    input_str = {
                                "input_sequence" : input_str
                                 , "num_days" : 250
                                 , "input_fs_1" : input_str_1
                                 , "target_fs_1" : (input_dt_1 + timedelta(days=250)).isoformat()
                                 , "input_fs_2" : input_str_2
                                 , "target_fs_2" : (input_dt_2 + timedelta(days=250)).isoformat()
                                 }

                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.1000.i":
                """
                add.day.1000.i: input is a dict with the input_sequence and num_days
                allows re-using prompts across many different num_days
                """
                try:
                    output_dt = input_dt + timedelta(days=1000)
                    output_str = output_dt.isoformat()

                    input_dt_1 = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
                    assert input_dt_1 != input_dt
                    input_str_1 = input_dt_1.isoformat()

                    input_dt_2 = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
                    assert input_dt_2 != input_dt
                    assert input_dt_2 != input_dt_1
                    input_str_2 = input_dt_2.isoformat()

                    input_str = {
                                "input_sequence" : input_str
                                 , "num_days" : 1000
                                 , "input_fs_1" : input_str_1
                                 , "target_fs_1" : (input_dt_1 + timedelta(days=1000)).isoformat()
                                 , "input_fs_2" : input_str_2
                                 , "target_fs_2" : (input_dt_2 + timedelta(days=1000)).isoformat()
                                 }

                except OverflowError as e:
                    # date value out of range
                    continue
            
            elif output == "add.day.2500.i":
                """
                add.day.2500.i: input is a dict with the input_sequence and num_days
                allows re-using prompts across many different num_days
                """
                try:
                    output_dt = input_dt + timedelta(days=2500)
                    output_str = output_dt.isoformat()

                    input_dt_1 = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
                    assert input_dt_1 != input_dt
                    input_str_1 = input_dt_1.isoformat()

                    input_dt_2 = random_utc_datetime(start_datetime=start_date, microseconds=False, timezone=False)
                    assert input_dt_2 != input_dt
                    assert input_dt_2 != input_dt_1
                    input_str_2 = input_dt_2.isoformat()

                    input_str = {
                                "input_sequence" : input_str
                                 , "num_days" : 2500
                                 , "input_fs_1" : input_str_1
                                 , "target_fs_1" : (input_dt_1 + timedelta(days=2500)).isoformat()
                                 , "input_fs_2" : input_str_2
                                 , "target_fs_2" : (input_dt_2 + timedelta(days=2500)).isoformat()
                                 }

                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.2000":
                try:
                    output_dt = input_dt + timedelta(days=2000)
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.days.1-100":
                try:
                    num_days = randint(1, 100)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.days.1-250":
                try:
                    num_days = randint(1, 250)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                , "num_days" : num_days
                                # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.days.1-1000":
                try:
                    num_days = randint(1, 1000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.days.1-2000":
                try:
                    num_days = randint(1, 2000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                , "num_days" : num_days
                                # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.days.1-2500":
                try:
                    num_days = randint(1, 2500)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                , "num_days" : num_days
                                # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue
            
            elif output == "add.day.1-3000":
                try:
                    num_days = randint(1, 3000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.1-4000":
                try:
                    num_days = randint(1, 4000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.1-5000":
                try:
                    num_days = randint(1, 5000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.1-6000":
                try:
                    num_days = randint(1, 6000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue
            
            elif output == "add.day.1-7000":
                try:
                    num_days = randint(1, 7000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                , "num_days" : num_days
                                # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                , "date" : input_dt.date().isoformat()}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.1-8000":
                try:
                    num_days = randint(1, 8000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.1-9000":
                try:
                    num_days = randint(1, 9000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.days.1-10000":
                try:
                    num_days = randint(1, 10000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str
                                 , "num_days" : num_days
                                 # METHODOLOGY: add "date" field for fine-tuning dataset exclusions
                                 , "date" : input_dt.date().isoformat()
                                 }
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.1001-2000":
                try:
                    num_days = randint(1001, 2000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.2001-3000":
                try:
                    num_days = randint(2001, 3000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.2001-4000":
                try:
                    num_days = randint(2001, 4000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.3001-4000":
                try:
                    num_days = randint(3001, 4000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue
            
            elif output == "add.day.4001-5000":
                try:
                    num_days = randint(4001, 5000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.4001-6000":
                try:
                    num_days = randint(4001, 6000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.5001-6000":
                try:
                    num_days = randint(5001, 6000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.6001-7000":
                try:
                    num_days = randint(6001, 7000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.6001-8000":
                try:
                    num_days = randint(6001, 8000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.7001-8000":
                try:
                    num_days = randint(7001, 8000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.8001-9000":
                try:
                    num_days = randint(8001, 9000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.9001-10000":
                try:
                    num_days = randint(9001, 10000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.1-25":
                try:
                    num_days = randint(1, 25)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.26-50":
                try:
                    num_days = randint(26, 50)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.51-75":
                try:
                    num_days = randint(51, 75)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.76-100":
                try:
                    num_days = randint(76, 100)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.day.250-1000":
                try:
                    num_days = randint(250, 1000)
                    output_dt = input_dt + timedelta(days=num_days)

                    # NOTE: output is a dict which are the arguments to the prompt generator
                    input_str = {"input_sequence" : input_str, "num_days" : num_days}
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "add.hours.1000":
                try:
                    output_dt = input_dt + timedelta(hours=1000)
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue


            elif output == "add.minutes.1000":
                try:
                    output_dt = input_dt + timedelta(minutes=1000)
                    output_str = output_dt.isoformat()
                except OverflowError as e:
                    # date value out of range
                    continue

            elif output == "subtract.day.1":
                output_dt = input_dt - timedelta(days=1)
                output_str = output_dt.isoformat()

            elif output == "subtract.day.2":
                output_dt = input_dt - timedelta(days=2)
                output_str = output_dt.isoformat()

            else:
                raise NotImplementedError(f"Unhandled output format '{output}'")
            
            # same month filters
            accepted = False
            if same_month == 0:
                accepted = True
            
            elif same_month == 1:
                accepted = input_dt.month == output_dt.month

            elif same_month == -1:
                # NOTE: if the year is different, observation is discarded
                accepted = (input_dt.month != output_dt.month) and (input_dt.year == output_dt.year)

            else:
                raise ValueError(f"Unhandled 'same_month' : {same_month} ({type(same_month)})")



            if not accepted:
                continue
            
            idx += 1
            yield (TrainingPair(input=input_str, output=output_str, locale=None, aux=None), input_dt)


# -----
# main
# -----

if __name__ == "__main__":

    from argparse import ArgumentParser

    # --- command line args ---
    cmd_line_parser = ArgumentParser(description='driver for Generates')
    cmd_line_parser.add_argument('output', type=str, default=None, help='iso8601, parsestr, model')
    cmd_line_parser.add_argument('num_observations', type=int, default=None, help='number of observations to generate')

    # parameters
    cmd_line_parser.add_argument('--same_month', type=int, help='define behavior if months are different', default=0)
    cmd_line_parser.add_argument('--start_date', type=str, help='start datetime in ISO format, e.g 2022-02-02T06:19:37', default=None)
    cmd_line_parser.add_argument('--end_date', type=str, help='end datetime in ISO format, e.g 2030-12-31T23:59:59', default=None)
    
    # output
    cmd_line_parser.add_argument('--preview_rows', type=int, help='number of rows to preview', default=None)
    cmd_line_parser.add_argument('--inputs', default=False, dest='inputs', action='store_true', help='show inputs only')
    cmd_line_parser.add_argument('--targets', default=False, dest='targets', action='store_true', help='only show targetsuts in compact form')
    cmd_line_parser.add_argument('--outputs', default=False, dest='outputs', action='store_true', help='show outputs only')
    
    cmd_line_parser.add_argument('--debug', default=False, dest='debug', action='store_true', help='debugging')
    cmd_line_parser.add_argument('--debug2', default=False, dest='debug2', action='store_true', help='debugging')
    args = cmd_line_parser.parse_args()

    assert not (args.inputs and args.outputs)

    # create generator
    generator = Generate(debug=args.debug, debug2=args.debug2)

    start_date = datetime.fromisoformat(args.start_date) if args.start_date is not None else None
    end_date = datetime.fromisoformat(args.end_date) if args.end_date is not None else None

    results = generator.generate(args.output
                                 , num_observations=args.num_observations
                                 , same_month=args.same_month
                                 , start_date=start_date
                                 , end_date=end_date
                                 )

    # show output
    if args.preview_rows:
        print(f"\nfirst {args.preview_rows} rows")
    first = True
    
    for idx, (training_pair, raw_input_value) in enumerate(results, start=1):

        if args.inputs:
            print(training_pair.input)
        elif args.targets:
            print(training_pair.output)
        elif args.outputs:
            print(training_pair.output)
        else:

            # show a sample from the start
            if first and args.preview_rows is None or idx <= args.preview_rows:
                print(raw_input_value, "->", training_pair)

                if idx == args.preview_rows:
                    first = False
                    print(f"\nlast {args.preview_rows}")

            # show a sample from the end
            if not first and idx >= args.num_observations - args.preview_rows:
                print(raw_input_value, "->", training_pair)

                #if idx == args.num_observations:
                #    break

