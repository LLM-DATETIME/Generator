# -*- coding: utf-8 -*-
"""
datetime_natural_form_tasks.py: Various tasks based on an  natural form input datetimes

INPUT
natural form datetime (e.g "5904|01|22 ,19:19:39 da tarde +05:00")

TARGET
An ISO-8601 datetime which is the result of some task. Currently supported tasks are:
    - add.day.1 : add 1 day
    - add.day.2 : add 2 days
    - subtract.day.1 : subtract 1 day
    - subtract.day.2 : subtract 2 days


EVENT_PREPARATION PROMPTS
I need {prep_days} days to prepare for an event. I can work any day of the week. The event is on {deadline_natural}. If I start preparing on {start_natural}, will I be ready in time? Answer with yes or no.

I need {prep_days} days to prepare for an event. I can work any day of the week. I am not available to start preparing until {start_natural}. The event is on {deadline_natural}, but everything needs to be ready by {natural date before the deadline}. Will I be ready in time?" Answer with yes or no.

I need {prep_days} days to prepare for an event, followed by {days_2} days required for testing. I can work any day of the week. The event is on {deadline}. If I start preparing on {start}, will I be ready in time?" Answer with yes or no.

I need {prep_days} days to prepare for an event, followed by {days_2} days required for testing. I can work any day of the week. I am not available to start preparing until {start_natural}. The event is on {deadline}. If I start preparing on {start}, will I be ready in time?" Answer with yes or no.

BASE
iso8601_tasks.py

MODIFICATIONS
1. input string is in natural form datetime (e.g "5904|01|22 ,19:19:39 da tarde +05:00")

BACKLOG

USAGE
python3 datetime_natural_form_tasks.py add.day.250 10

python3 datetime_natural_form_tasks.py "event_prep_1(250)" 10 --start_date "2027-01-01 00:00:00" --end_date "2035-01-01 00:00:00"
python3 datetime_natural_form_tasks.py "event_prep_1(200, 300)" 10 --start_date "2027-01-01 00:00:00" --end_date "2035-01-01 00:00:00"
"""

# -------
# imports
# -------

from collections import namedtuple
from datetime import date, datetime, time, timedelta
from random import randint, choice
from string import digits, ascii_letters
from typing import Any, List, Set, Dict, Tuple, Optional, Union, Iterable, Iterator

from utils.check_isinstance import check_isinstance
from utils.parse_function_args import parse_function_args
from utils.random_datetime import random_utc_datetime

from utils.training_pair import TrainingPair
from utils.load_generator import LoadGenerator

# logging
from utils.logger import logger_dl
module_logger = logger_dl.getChild(f"datetime_natural_form_tasks")


# -----
# class
# -----

class Generate:

    """
    Generate a sample of dates for training
    """

    MARGIN_BANDS = {
        "clear_yes":    list(range(5, 31))
        , "clear_no":   list(range(-30, -5))
        , "boundary_yes": [2, 3]
        , "boundary_no":  [-3, -2]
    }

    def __init__(self, debug : bool = False, debug2 : bool = False):

        self.debug = debug
        self.debug2 = debug2

        # the core datalake type being generated (see Config.core_pandas_type_map)
        self.model_name = "DATETIME-NATURAL-FORM-TASKS"

        self.source_generator_name = "dates/datetime/generate16.25.py"

        self.source_generator = LoadGenerator(self.source_generator_name, debug=self.debug2)

        # to ensure all datetimes in the prompt will have the same formatting, we need a custom_formatter
        if not hasattr(self.source_generator.generator, "custom_formatter"):
            raise RuntimeError("Generator {self.source_generator_name} does not have custom_formatter 'custom_formatter")
        
        self.custom_formatter = self.source_generator.generator.custom_formatter

      
    def generate(self
                , output : str
                , num_observations : int
                , same_month : Optional[int] = None
                , month_schema : str = None
                , start_date : datetime = None
                , end_date : datetime = None
                , date_schemas : List[str] = None
                , time_schemas : List[str] = None
                , locale_schema : str = "mini.10"
                , remove_random_component_probability : float = 0.05
                ) -> Iterator[ Tuple[ TrainingPair, Any] ]:

        """

        :param output: what do generate: pattern

        :param num_observations: amount of numbers to generate; each numner will be generated in various scales, locales, formats, etc.

        :param same_month: define what do to if the month of the output datetime is different to the month of the input datetime
            * 0 or None: all observations are kept, regardless if output month is the same or different from the input month
            
            * 1: only the observations are kept where the output month is the same the input month
            
            * -1: only the observations are kept where the output month is different to the input month
                if the year is different, observation is discarded   

        :param schemas: optional; list schemas to be used; at the moment only month-day and day-month are supported
            a schema is a group of formats, grouped according to some logic, e.g day first, month first, etc
            if None, all available schemas are used

        :param month_schema: specifies the month formats
            possible values:
            - "all": arabic and roman numerals
            - "arabic": arabic numerals only (1, 2, 3, ...)
            - "roman" : (i, ii, iii, ...)
            - "unambiguous" : MMM and MMMM

        :param start_date: optional; start date(time) of the dates; a default value will be generated if None

        :param end_date: optional; end date(time) of the dates; a default value will be generated if None

        :param remove_random_component_probability: generate16.11; probability for removing a component at random
            - default is 0.05
            - if None, no component is remove (equivalent to probability = 0.0)

        :return: function is a generator -> an iterator of 2-tuples
            1. TrainingPairs (namedtuple)
            2. the input number

        """

        check_isinstance(same_month, int, none_ok=True)
        if same_month is None:
            same_month = 0

        if self.debug:
            module_logger.debug(f"Generating {num_observations} observations with output '{output}' for task '{output}' with same_month '{same_month}'")
            module_logger.debug(f"date_schemas : {date_schemas} | time_schemas : {time_schemas}")
            module_logger.debug(f"start_date : {start_date} ({type(start_date)}) | end_date : {end_date} ({type(end_date)})")

        # set start date
        if start_date is None:
            start_date = datetime(1970, 1, 1, 0, 0, 0)
        else:
            if not isinstance(start_date, datetime):
                start_date = datetime.fromisoformat(start_date)

        # set end date
        if end_date is None:
            end_date = datetime(9999, 12, 31, 0, 0, 0)
        else:
            if not isinstance(end_date, datetime):
                end_date = datetime.fromisoformat(end_date)
            
        if self.debug:
            module_logger.debug(f"starting on {start_date} ({type(start_date)}) | end_date : {end_date} ({type(end_date)})")

        assert isinstance(output, str)

        # use the source generator to generate a datetime in human form
        source = self.source_generator.generate("model"
                                                , num_observations * 3000
                                                , locale_schema=locale_schema
                                                , date_schemas=date_schemas
                                                , time_schemas=time_schemas
                                                , month_schema=month_schema
                                                , microseconds=False
                                                , add_timezone=False
                                                , store_visible_components=True
                                                , remove_random_component_probability=remove_random_component_probability
                                                , start_date=start_date
                                                , end_date=end_date
                                                )
       
        idx = 0
        while idx != num_observations:

            training_pair, _dt = next(source)

            
            assert "visible_components" in training_pair.aux
            #print(f"{idx} | input : {training_pair.input}")
            #print(f"visible_components : {training_pair.aux}") 

            if "minute" not in training_pair.aux["visible_components"]:
                continue

            if "second" not in training_pair.aux["visible_components"]:
                continue

            input_dt = _dt
                #datetime(year=_dt.year
                #                , month=_dt.month
                #                , day=_dt.day
                #                , hour=_dt.hour
                #                , minute=_dt.minute if "minute" in training_pair.aux["visible_components"] else 0
                #                , second=_dt.second if "second" in training_pair.aux["visible_components"] else 0
                #                )   
            

            assert "year" in training_pair.aux["visible_components"]
            assert "month" in training_pair.aux["visible_components"]
            assert "day" in training_pair.aux["visible_components"]
            assert "hour" in training_pair.aux["visible_components"]

            
            #module_logger.error(f"debug exit")
            #exit(1)
            
            input_str = training_pair.input
            
            if output == "model":
                output_str = self.model_name

            elif output.startswith("event_prep"):
                """
                Event preparation.

                EXAMPLES
                I need {prep_days} days to prepare for an event. I can work any day of the week. The event is on {deadline_natural}. If I start preparing on {start_natural}, will I be ready in time? Answer with yes or no.

                I need {prep_days} days to prepare for an event. I can work any day of the week. I am not available to start preparing until {start_natural}. The event is on {deadline_natural}, but everything needs to be ready by {natural date before the deadline}. Will I be ready in time?" Answer with yes or no.

                I need {prep_days} days to prepare for an event, followed by {days_2} days required for testing. I can work any day of the week. The event is on {deadline}. If I start preparing on {start}, will I be ready in time?" Answer with yes or no.

                I need {prep_days} days to prepare for an event, followed by {days_2} days required for testing. I can work any day of the week. I am not available to start preparing until {start_natural}. The event is on {deadline}. If I start preparing on {start}, will I be ready in time?" Answer with yes or no.

                """

                event_start_date = input_dt

                if self.debug:
                    module_logger.debug(f"event_start_date : {event_start_date} | {output} | training_pair : {training_pair}")


                # METHODOLOGY: decide label first => balanced distribution of Yes/No cases
                label = choice([True, False])
                band_type = choice(["clear", "boundary"])
                label_name = "yes" if label else "no"
                band_key = f"{band_type}_{label_name}"

                # METHODOLOGY: decide margins => ex-post diagnostics and ensure no edge cases that could be ambiguous
                margin = choice(self.MARGIN_BANDS[band_key])

                if self.debug:
                    module_logger.debug(f"label : {label} | label_name : {label_name}")
                    module_logger.debug(f"band_type : {band_type} | band_key : {band_key} | margin : {margin}")


                # parse args event_prep_1(200, 300)
                output_args = parse_function_args(output)
                if len(output_args) == 1:
                    num_days_lb, num_days_ub = output_args[0], output_args[0]
                elif len(output_args) == 2:
                    num_days_lb = output_args[0]
                    num_days_ub = output_args[1]
                else:
                    raise ValueError(f"Invalid arguments {output_args} for output '{output}' | only 1 or 2 arguments supported")

                # lead time args
                lead_days_lb = output_args.get("lead_lb", 0)
                lead_days_ub = output_args.get("lead_ub", 0)

                if self.debug:
                    module_logger.debug(f"num_days_lb : {num_days_lb} | num_days_ub : {num_days_ub}")
                    module_logger.debug(f"lead_days_lb : {lead_days_lb} | lead_days_ub : {lead_days_ub}")
                    module_logger.debug(f"input_dt : {input_dt} | input_str : {input_str}")

                # 1. numer of days for preparation
                # METHODOLOGY:  The preparation time is the anchor and constant; for example if set to 250, then
                # we need to fix the add-250, since extensive experiments and fine.tuning prove this is possible. the rest can change and are control variables
                prep_days = randint(num_days_lb, num_days_ub)

                # ready_by_date: task needs to be completed by this date
                # METHODOLOGY: allow a one-day buffer to allow for any possible ambiguity
                ready_by_date = event_start_date + timedelta(days=prep_days - 1 + margin)
                lead_days = randint(lead_days_lb, lead_days_ub)
                event_date = ready_by_date + timedelta(days=lead_days)

                if self.debug:
                    module_logger.debug(f"prep_days : {prep_days}")
                    module_logger.debug(f"ready_by_date : {ready_by_date} | margin : {margin} | event_date : {event_date}")

                # same condition => same gold label
                assert (event_start_date + timedelta(days=prep_days - 1) <= ready_by_date) == label # visible components for the task
                assert (event_start_date + timedelta(days=prep_days - 1) + timedelta(days=lead_days) <= event_date) == label # NOTE: correct but redundant and could be confusing
                assert event_date >= ready_by_date

                # METHODOLOGY: ensure all datetimes in the prompt will have the same formatting, as it's unrealistic 
                # need to format the deadline date in the same style as the 
                # a same user will have two different formatting styles
                format_spec = training_pair.aux["format_spec"]
                locale = training_pair.aux["locale"]
                
                ready_by_date_str = self.custom_formatter.apply(format_spec, ready_by_date, locale=locale)
                event_date_str = self.custom_formatter.apply(format_spec, event_date, locale=locale)


                if self.debug:
                    module_logger.debug(f"ready_by_date_str : {ready_by_date_str} | ready_by_date : {ready_by_date} | format_spec : {format_spec} | locale : {locale}")
                    module_logger.debug(f"event_date_str : {event_date_str} | event_date : {event_date} | format_spec : {format_spec} | locale : {locale}")
                
                # label consistency
                assert (margin >= 0) == label, (
                    f"margin sign {margin} contradicts label {label}"
                )

                # margin is within expected band
                assert margin in self.MARGIN_BANDS[band_key], (
                    f"margin {margin} not in band {band_key}"
                )

                # hour-ambiguity safety: no razor-edge cases
                assert abs(margin) >= 2, (
                    f"margin {margin} too close to boundary, hour ambiguity risk"
                )

                # start date is in the future range
                assert 2026 <= event_start_date.year <= 2050, (
                    f"start date {event_start_date} outside range 2026-2050"
                )

                input_str = {
                    "start_date": input_str
                    , "prep_days": prep_days
                    , "lead_days" : lead_days
                    , "margin": margin
                    , "margin_band": band_key
                    , "ready_by_date": ready_by_date_str
                    , "event_date" : event_date_str
                    , "input_sequence" : input_str # for compatibility

                    # pass along ISO formats for post-processing
                    , "start_dt" : event_start_date.isoformat()
                    , "ready_by_date_dt" : ready_by_date.isoformat()
                    , "event_date_dt" : event_date.isoformat()

                    # # METHODOLOGY: for fine-tuning, this is the exclusion criterion
                    , "input_dt" : event_start_date.date().isoformat()
                }

                output_str = label_name # Yes or No (str)
            
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
                output_dt = input_dt + timedelta(days=50)
                output_str = output_dt.isoformat()

            elif output == "add.day.100":
                output_dt = input_dt + timedelta(days=100)
                output_str = output_dt.isoformat()
            
            elif output == "add.day.250":
                try:
                    output_dt = input_dt + timedelta(days=250)
                    output_str = output_dt.isoformat()
                except Exception as e:
                    #module_logger.warning(f"input_dt : {input_dt} | {e}")
                    continue

            elif output == "add.day.1000":
                try:
                    output_dt = input_dt + timedelta(days=1000)
                    output_str = output_dt.isoformat()
                except Exception as e:
                    #module_logger.warning(f"input_dt : {input_dt} | {e}")
                    continue

            elif output == "add.day.2500":
                try:
                    output_dt = input_dt + timedelta(days=2500)
                    output_str = output_dt.isoformat()
                except Exception as e:
                    #module_logger.warning(f"input_dt : {input_dt} | {e}")
                    continue

            elif output == "add.day.250.i":
                """
                add.day.250.i: input is a dict with the input_sequence, num_days and two rendered examples for Few-Shot prompts
                allows re-using prompts across many different num_days
                """
                try:
                    output_dt = input_dt + timedelta(days=250)
                    output_str = output_dt.isoformat()

                    # NOTE: the few-shot examples must be rendered in the same type of format as the input_sequence
                    while True:
                        training_pair1, input_dt_1 = next(source)
                        input_str_1 = training_pair1.input

                        training_pair2, input_dt_2 = next(source)
                        input_str_2 = training_pair2.input

                        # ensure we get few-shot examples different to the input_sequence and different from each other
                        if input_dt_1 != input_dt and input_dt_2 != input_dt and input_dt_1 != input_dt_2:
                            break
                    

                    input_str = {
                                "input_sequence" : input_str
                                , "input_dt" : input_dt.isoformat()
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
                add.day.1000.i: input is a dict with the input_sequence, num_days and two rendered examples for Few-Shot prompts
                allows re-using prompts across many different num_days
                """
                try:
                    output_dt = input_dt + timedelta(days=1000)
                    output_str = output_dt.isoformat()

                    # NOTE: the few-shot examples must be rendered in the same type of format as the input_sequence
                    while True:
                        training_pair1, input_dt_1 = next(source)
                        input_str_1 = training_pair1.input

                        training_pair2, input_dt_2 = next(source)
                        input_str_2 = training_pair2.input

                        # ensure we get few-shot examples different to the input_sequence and different from each other
                        if input_dt_1 != input_dt and input_dt_2 != input_dt and input_dt_1 != input_dt_2:
                            break

                    input_str = {
                                "input_sequence" : input_str
                                , "input_dt" : input_dt.isoformat()
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
                add.day.2500.i: input is a dict with the input_sequence, num_days and two rendered examples for Few-Shot prompts
                allows re-using prompts across many different num_days
                """
                try:
                    output_dt = input_dt + timedelta(days=2500)
                    output_str = output_dt.isoformat()

                    # NOTE: the few-shot examples must be rendered in the same type of format as the input_sequence
                    while True:
                        training_pair1, input_dt_1 = next(source)
                        input_str_1 = training_pair1.input

                        training_pair2, input_dt_2 = next(source)
                        input_str_2 = training_pair2.input

                        # ensure we get few-shot examples different to the input_sequence and different from each other
                        if input_dt_1 != input_dt and input_dt_2 != input_dt and input_dt_1 != input_dt_2:
                            break

                    input_str = {
                                "input_sequence" : input_str
                                , "input_dt" : input_dt.isoformat()
                                 , "num_days" : 2500
                                 , "input_fs_1" : input_str_1
                                 , "target_fs_1" : (input_dt_1 + timedelta(days=2500)).isoformat()
                                 , "input_fs_2" : input_str_2
                                 , "target_fs_2" : (input_dt_2 + timedelta(days=2500)).isoformat()
                                 }

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
    cmd_line_parser = ArgumentParser(description='driver for Generate')
    cmd_line_parser.add_argument('output', type=str, default=None, help='iso8601, parsestr, model')
    cmd_line_parser.add_argument('num_observations', type=int, default=None, help='number of observations to generate')

    # parameters
    cmd_line_parser.add_argument('--same_month', type=int, help='define behavior if months are different', default=0)
    cmd_line_parser.add_argument('--month_schema', type=str, help="month format: all, arabic, roman or unambiguous", default=None)
    cmd_line_parser.add_argument('--locale_schema', type=str, help="locale schema: en_US, mini.10, sap.dominant, babel.all, all", default='mini.10')
    cmd_line_parser.add_argument('--start_date', type=str, help='start datetime in ISO format, e.g 2022-02-02T06:19:37', default=None)
    cmd_line_parser.add_argument('--end_date', type=str, help='end datetime in ISO format, e.g 2030-12-31T23:59:59', default=None)
    cmd_line_parser.add_argument('--remove_components', type=float, help='remove components randomly', default=0.0)
    cmd_line_parser.add_argument('--date_schemas', type=str, help="comma-separated list of date templates, e.g. 'day-month-yyyy, day-month-weekday-yyyy, month-day-yyyy, month-day-weekday-yyyy'", default=None)
    cmd_line_parser.add_argument('--time_schemas', type=str, help="comman-separated lust of time templates, 'hours, hours-minutes, hours-minutes-seconds'", default=None)
    
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

    date_schemas = [s.strip() for s in args.date_schemas.split(",")] if args.date_schemas is not None else None
    time_schemas = [s.strip() for s in args.time_schemas.split(",")] if args.time_schemas is not None else None

    results = generator.generate(args.output
                                 , num_observations=args.num_observations
                                 , same_month=args.same_month
                                 , month_schema=args.month_schema
                                 , locale_schema=args.locale_schema
                                 , start_date=start_date
                                 , end_date=end_date
                                 , remove_random_component_probability=args.remove_components
                                 , date_schemas=date_schemas
                                 , time_schemas=time_schemas
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

