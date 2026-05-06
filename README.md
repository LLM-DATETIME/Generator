# PRIMETIME

## Overview

PRIMETIME is a fully synthetic benchmark for evaluating how Large Language Models handle datetimes. It covers:

- **Translation**: converting messy natural-form datetimes to ISO 8601
- **Addition**: adding a fixed or variable number of days to a datetime
- **Event Planning**: compositional tasks requiring date addition and comparison in a conversational context

The generator produces ground-truth datasets with high variation in surface forms — millions of natural representations of the same underlying datetime. Generated datasets can be used to fine-tune and evaluate models on translation and multi-step reasoning tasks in the datetime domain.

## Related Paper
PRIMETIME: Limits of LLMs in Temporal Primitives (under review, NeurIPS 2026, Evaluations & Datasets Track).

## Requirements

- Python 3.8+

- Key requirements:
* Babel==2.9.1
* num2words==0.5.10
* roman==3.3
* colorlog

- All dependencies: see `requirements.txt`

## Quick Start
```
# 0. Choose a target location
mkdir /tmp/datetime_generator
cd /tmp/datetime_generator

# 1. Clone
git clone https://github.com/LLM-DATETIME/Generator.git
cd Generator
git checkout v2

# 2. Create clean environment
python3 -m venv venv --clear
source venv/bin/activate
pip3 install Babel==2.9.1
pip3 install num2words==0.5.10
pip3 install roman==3.3
pip3 install colorlog

# 3. Test iso8601 generator
python3 iso8601_tasks.py add.day.250 100 --preview_rows 5

# 4. Test natural form generator
python3 datetime_natural_form_tasks.py add.day.250 100 --preview_rows 5

# 5. Test event planning task
python3 datetime_natural_form_tasks.py "event_prep_1(250)" 100 \
        --start_date 2027-01-01T00:00:00 \
        --end_date 2036-12-31T23:59:59 \
        --locale_schema "en_US" \
        --month_schema "unambiguous" \
        --preview_rows 5

# 6. Cleanup
deactivate
cd ..
rm -rf Generator

```


## Generators

The repository contains two generator scripts:

### `iso8601_tasks.py`

Generates instances where both input and output are in ISO 8601 format.

**Positional arguments:**

| Argument | Description |
|----------|-------------|
| `output` | Task type (see task list below) |
| `num_observations` | Number of instances to generate |

**Optional arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `--same_month` | Month-boundary filter. `0`: keep all. `1`: same-month only. `-1`: month-crossing only (same year) | `0` |
| `--start_date` | Lower bound for input dates (ISO 8601) | `1970-01-01T00:00:00` |
| `--end_date` | Upper bound for input dates (ISO 8601) | `9999-12-31T00:00:00` |
| `--inputs` | Print only input sequences | `False` |
| `--targets` | Print only target sequences | `False` |
| `--preview_rows` | Number of rows to preview | `None` |

**Supported tasks:**

*Fixed-offset addition:*
- `add.day.1`, `add.day.2`, `add.day.10`, `add.day.20`, `add.day.50`, `add.day.100`, `add.day.250`
- `add.hours.1000`, `add.minutes.1000`

*Variable-offset addition (random within range):*
- `add.days.1-250`, `add.day.1-25`, `add.day.26-50`, `add.day.51-75`, `add.day.76-100`
- `add.day.250-1000`, `add.day.9001-10000`

*Subtraction:*
- `subtract.day.1`, `subtract.day.2`

**Examples:**

```bash
# Add-250 with month-boundary crossing enforced
python3 iso8601_tasks.py add.day.250 1000 --same_month -1

# Variable-offset addition, restricted to 2027-2036
python3 iso8601_tasks.py add.days.1-250 500 \
        --start_date 2027-01-01T00:00:00 \
        --end_date 2036-12-31T23:59:59

# Preview first 5 rows of a subtraction task
python3 iso8601_tasks.py subtract.day.1 100 --preview_rows 5
```

---

### `datetime_natural_form_tasks.py`

Generates instances where the input is a natural-form datetime representation (e.g. `5904|01|22 ,19:19:39 da tarde +05:00`). Targets are either ISO 8601 datetimes (for translation and addition tasks) or binary yes/no labels (for Event Planning tasks).

**Positional arguments:**

| Argument | Description |
|----------|-------------|
| `output` | Task type. For Event Planning tasks, arguments are passed in parentheses, e.g. `"event_prep_1(250)"` for fixed 250-day preparation or `"event_prep_1(200, 300)"` for variable duration |
| `num_observations` | Number of instances to generate |

**Optional arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `--same_month` | Month-boundary filter. `0`: keep all. `1`: same-month only. `-1`: month-crossing only (same year) | `0` |
| `--month_schema` | Month rendering. `all`: all formats. `arabic`: numeric. `roman`: Roman numerals. `unambiguous`: abbreviated and full names only | `None` (all) |
| `--locale_schema` | Locale selection. `en_US`, `mini.10`, `sap.dominant`, `babel.all`, `all` | `mini.10` |
| `--start_date` | Lower bound for input dates (ISO 8601) | `1970-01-01T00:00:00` |
| `--end_date` | Upper bound for input dates (ISO 8601) | `9999-12-31T00:00:00` |
| `--remove_components` | Probability of randomly removing a datetime component | `0.0` |
| `--date_schemas` | Comma-separated date orderings, e.g. `"day-month-yyyy, month-day-weekday-yyyy"` | All available |
| `--time_schemas` | Comma-separated time granularities, e.g. `"hours, hours-minutes, hours-minutes-seconds"` | All available |
| `--inputs` | Print only input sequences | `False` |
| `--targets` | Print only target sequences | `False` |
| `--preview_rows` | Number of rows to preview | `None` |

**Supported tasks:**

*Fixed-offset addition:*
- `add.day.1`, `add.day.2`, `add.day.10`, `add.day.20`, `add.day.50`, `add.day.100`, `add.day.250`, `add.day.1000`, `add.day.2500`

*Fixed-offset addition with few-shot exemplars:*
- `add.day.250.i`, `add.day.1000.i`, `add.day.2500.i` — output includes two decontaminated few-shot examples rendered in the same format

*Subtraction:*
- `subtract.day.1`, `subtract.day.2`

*Event Planning (binary yes/no):*
- `event_prep_1(N)` — single-hop, direct. Fixed preparation of N days
- `event_prep_1(N, M)` — single-hop, direct. Variable preparation sampled from [N, M]

**Examples:**

```bash
# Event Planning with fixed 250-day preparation, English, 2027-2036
python3 datetime_natural_form_tasks.py "event_prep_1(250)" 1000 \
        --start_date 2027-01-01T00:00:00 \
        --end_date 2036-12-31T23:59:59 \
        --locale_schema "en_US" \
        --month_schema "unambiguous" \
        --remove_components 0.0

# Event Planning with variable preparation (200-300 days)
python3 datetime_natural_form_tasks.py "event_prep_1(200, 300)" 1000 \
        --start_date 2027-01-01T00:00:00 \
        --end_date 2036-12-31T23:59:59

# Add-250 translation with all locales, month-crossing enforced
python3 datetime_natural_form_tasks.py add.day.250 500 \
        --same_month -1 \
        --locale_schema "babel.all"

# Add-250 with embedded few-shot exemplars
python3 datetime_natural_form_tasks.py add.day.250.i 500 \
        --locale_schema "en_US"
```

## Citation
Stay tuned.

## License
Apache 2.0
