"""
etl_lib.py

Cleaning and data-prep functions I use across several notebooks, so I'm
not copying the same code into each one.

What's in here, by section:
1. Basic cleaning (whitespace, mixed-case text, disguised "empty"
   values, negative numbers that shouldn't be negative, duplicate rows)
2. Calendar (ISO week, shift)
3. The LotId traceability code
4. OEE calculation
5. SPC / AQL (control limits, Cp/Cpk)
6. Maintenance (planned vs. unplanned downtime)
7. Quality (customer complaints, suppliers, NC/CAPA)
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. BASIC CLEANING
# ---------------------------------------------------------------------------

# these are the words people type when a text field has nothing to say --
# a dash, a slash, a blank space. pandas doesn't recognize this as a
# missing value on its own, so I have to handle it by hand, otherwise it
# ends up looking like a real category (e.g. a technician named "-"
# showing up in a groupby)
BLANK_WORDS = {"-", "--", "---", "/", "//", "\\", "n/a", "na", "none", "null", ""}


def clean_disguised_blanks(df: pd.DataFrame) -> pd.DataFrame:
    """Replaces the words in BLANK_WORDS with a real empty value (NaN),
    in every text column of the table."""
    df = df.copy()

    # select_dtypes(include="object") picks only the text columns (not the numeric ones)
    text_columns = df.select_dtypes(include="object").columns

    for column in text_columns:
        # step 1: strip whitespace and lowercase, just to compare
        stripped_value = df[column].astype(str).str.strip()
        lowercase_value = stripped_value.str.lower()

        # step 2: check which rows in this column are one of the "blank words"
        is_blank_word = lowercase_value.isin(BLANK_WORDS)

        # step 3: on those rows (and only the ones that weren't already NaN), swap in a real NaN
        df.loc[df[column].notna() & is_blank_word, column] = np.nan

    return df


def strip_extra_spaces(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Trims spaces at the start/end of text and collapses double spaces
    into one. Ex: "  Injection Molding  " -> "Injection Molding" """
    df = df.copy()

    if columns is None:
        columns = df.select_dtypes(include="object").columns.tolist()

    for column in columns:
        if column not in df.columns:
            continue

        def fix_text(value):
            if not isinstance(value, str):
                return value
            return " ".join(value.split())

        df[column] = df[column].apply(fix_text)

    return df


def standardize_categories(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Makes 'INJECTION MOLDING', 'injection molding' and 'Injection
    Molding ' all turn into 'Injection Molding'. I use .title() (capitalizes
    the first letter of each word) instead of a fixed lookup dictionary,
    so it still works if a new category shows up that I didn't plan for."""
    df = df.copy()

    for column in columns:
        if column not in df.columns:
            continue

        def fix_category(value):
            if not isinstance(value, str):
                return value
            return value.strip().title()

        df[column] = df[column].apply(fix_category)

    return df


def fix_negative_quantities(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Some quantity columns (like rejected pieces) show up with a
    negative number, which doesn't make sense -- there's no such thing
    as rejecting -12 pieces. Probably a sign typo somewhere upstream.
    Instead of dropping the whole row (the rest of it is fine), I just
    swap in the positive value with abs()."""
    df = df.copy()

    for column in columns:
        if column in df.columns:
            df[column] = df[column].abs()

    return df


def drop_duplicate_rows(df: pd.DataFrame, columns: list[str] | None = None):
    """Removes rows that are identical across the board, and counts how
    many were removed, so I know about it (instead of data quietly
    disappearing without anyone noticing)."""
    rows_before = len(df)

    df = df.drop_duplicates(subset=columns)
    df = df.reset_index(drop=True)

    rows_removed = rows_before - len(df)
    return df, rows_removed


def count_missing_values(df: pd.DataFrame) -> pd.Series:
    """isna().sum() sorted from most to least, so I'm not typing the
    same line in every notebook."""
    return df.isna().sum().sort_values(ascending=False)


# ---------------------------------------------------------------------------
# 2. CALENDAR
# ---------------------------------------------------------------------------

def add_calendar_columns(df: pd.DataFrame, date_column: str = "Date") -> pd.DataFrame:
    """Adds ISOWeek (week number) and ISOWeekday (day of the week,
    1=Monday...7=Sunday).

    I use the "ISO week" instead of the plain calendar week because
    that's how the plant organizes shifts and overtime: every week is a
    closed Monday-to-Sunday block, with no partial week at the
    start/end of the year."""
    df = df.copy()

    date = pd.to_datetime(df[date_column])
    iso_calendar = date.dt.isocalendar()

    df["ISOWeek"] = iso_calendar["week"].astype(int)
    df["ISOWeekday"] = iso_calendar["day"].astype(int)

    return df


def compute_shift_number(start_time: pd.Series) -> pd.Series:
    """Computes the shift number from the start time:
    - Shift 1: 06:00 to 13:59
    - Shift 2: 14:00 to 21:59
    - Shift 3: everything else (22:00 to 05:59)

    I do this with a simple function applied row by row (.apply),
    because it's easier to read than doing it all in one vectorized
    expression."""

    def shift_for_one_time(time_value):
        time_value = pd.to_datetime(str(time_value), format="mixed", errors="coerce")
        if pd.isna(time_value):
            return 3
        minutes_of_day = time_value.hour * 60 + time_value.minute

        if 6 * 60 <= minutes_of_day < 14 * 60:
            return 1
        elif 14 * 60 <= minutes_of_day < 22 * 60:
            return 2
        else:
            return 3

    return start_time.apply(shift_for_one_time).rename("ShiftNumber")


# ---------------------------------------------------------------------------
# 3. LotId TRACEABILITY CODE
# ---------------------------------------------------------------------------

PROCESS_CODE = {
    "Blow Molding": "1",
    "Injection Molding": "2",
    "Screen Printing": "4",
    "Hot Foil Stamping": "5",
}


def machine_number(machine_id: str) -> str:
    """'ISBM-001' -> '01', 'IM-004' -> '04'.

    MachineId always comes in the format LETTERS-NUMBER, so I just take
    the part after the dash and format it as 2 digits."""
    parts = str(machine_id).split("-")
    number = int(parts[-1])
    return f"{number % 100:02d}"


def work_order_number(work_order: str) -> str:
    """'WO-6005' -> '06005' (just the number, padded to 5 digits)."""
    parts = str(work_order).split("-")
    number = int(parts[-1])
    return f"{number % 100000:05d}"


def build_lotid_prefix(date: pd.Series, shift: pd.Series, process: pd.Series,
                        machine_id: pd.Series, work_order: pd.Series) -> pd.Series:
    """Builds the first 14 characters of the LotId:

        YY WW D T P MM OOOOO
        26 09 2 2 1 01 06005

    year(2) + ISO week(2) + ISO weekday(1) + shift(1) + process(1) +
    machine number(2) + work order number(5)
    """
    date = pd.to_datetime(date)
    iso_calendar = date.dt.isocalendar()

    year = (date.dt.year % 100).astype(int).astype(str).str.zfill(2)
    week = iso_calendar["week"].astype(int).astype(str).str.zfill(2)
    weekday = iso_calendar["day"].astype(int).astype(str)
    shift_text = shift.astype(int).astype(str)
    process_code = process.map(PROCESS_CODE).fillna("0")
    machine_code = machine_id.apply(machine_number)
    order_code = work_order.apply(work_order_number)

    return year + week + weekday + shift_text + process_code + machine_code + order_code


def compute_material_lot_sequence(consumption: pd.DataFrame, order_column="WorkOrder",
                                   lot_column="MaterialLot",
                                   record_order_column="RecordSeq") -> pd.Series:
    """Computes the last 2 digits of the LotId -- starts at 01 for each
    new work order, and only goes up when the PHYSICAL material lot
    actually changes (not just because the shift changed).

    I use a for loop here on purpose: I need to compare each row with
    the previous row, in the order they actually happened, and a loop
    makes that clear (record_order_column keeps track of that real
    order, because the CSV sometimes comes back with rows out of order)."""
    df = consumption.sort_values([order_column, record_order_column]).copy()

    sequences = []
    counter = 0
    previous_order = None
    previous_lot = None

    for current_order, current_lot in zip(df[order_column], df[lot_column]):
        if current_order != previous_order:
            counter = 1
        elif current_lot != previous_lot:
            counter += 1

        sequences.append(counter)
        previous_order = current_order
        previous_lot = current_lot

    result = pd.Series(sequences, index=df.index, name="MaterialLotSeq")
    return result.reindex(consumption.index)


def fill_blank_material_lot(consumption: pd.DataFrame, order_column="WorkOrder",
                             lot_column="MaterialLot",
                             record_order_column="RecordSeq") -> pd.Series:
    """If MaterialLot ended up blank after the null cleanup, it's almost
    certainly the operator forgetting to write it down -- not a new lot
    actually starting there. So I fill it forward with the last known
    value for that work order. Without this, every blank would look
    like "a new lot started here" and the LotId sequence would come out wrong."""
    df = consumption.sort_values([order_column, record_order_column])
    filled = df.groupby(order_column)[lot_column].ffill().bfill()
    return filled.reindex(consumption.index)


def compute_end_datetime(date: pd.Series, start_time: pd.Series, end_time: pd.Series,
                          duration_hours: pd.Series | None = None) -> pd.Series:
    """The raw tables only store the time of day (not the full date and
    time), so if an order runs past midnight I need to work that out
    myself. If I already have the planned duration, I use that.
    Otherwise: if the end time looks earlier than the start time, the
    order must have rolled into the next day."""
    start_datetime = pd.to_datetime(date) + pd.to_timedelta(start_time.astype(str))

    if duration_hours is not None:
        return start_datetime + pd.to_timedelta(duration_hours.astype(float), unit="h")

    end_time_td = pd.to_timedelta(end_time.astype(str))
    start_time_td = pd.to_timedelta(start_time.astype(str))

    rolled_past_midnight = end_time_td <= start_time_td

    end_datetime = pd.to_datetime(date) + end_time_td
    end_datetime = end_datetime.where(~rolled_past_midnight, end_datetime + pd.Timedelta(days=1))

    return end_datetime


def find_work_order_for_stoppage(downtime: pd.DataFrame, production: pd.DataFrame) -> pd.Series:
    """Downtime records don't have their own WorkOrder column, so to
    figure out which order was running when a machine stopped, I
    compare the stoppage time to the start/end time of every order on
    that same machine.

    Sometimes two orders on the same machine have times that overlap a
    little (the next one starts before the previous one fully "closes"
    in the system) -- in those cases, I treat whichever order started
    LAST as the one that was actually running, since it's the most recent.

    Returns NaN when no order was running at that moment (e.g. a
    stoppage logged right at the very start of the whole period)."""
    stoppage_moment = pd.to_datetime(downtime["Date"]) + pd.to_timedelta(downtime["StoppageStartTime"].astype(str))

    result = pd.Series(np.nan, index=downtime.index, dtype=object)

    for machine in downtime["MachineId"].unique():
        machine_orders = production[production["MachineId"] == machine].sort_values("_start_dt", ascending=False)

        if machine_orders.empty:
            continue

        starts = list(machine_orders["_start_dt"])
        ends = list(machine_orders["_end_dt"])
        orders = list(machine_orders["WorkOrder"])

        stoppage_indices = downtime[downtime["MachineId"] == machine].index

        for stoppage_index in stoppage_indices:
            time_of_stoppage = stoppage_moment.loc[stoppage_index]

            for start, end, order in zip(starts, ends, orders):
                if start <= time_of_stoppage < end:
                    result.loc[stoppage_index] = order
                    break

    return result


# ---------------------------------------------------------------------------
# 4. OEE CALCULATION
# ---------------------------------------------------------------------------

def compute_oee_components(production: pd.DataFrame, plan: pd.DataFrame,
                            downtime_by_order: pd.DataFrame,
                            capacity_by_machine: dict) -> pd.DataFrame:
    """Computes OEE (Overall Equipment Effectiveness) and the three
    parts that make it up, for each work order.

    The formulas:
    - Availability = Run Time / Planned Time
      (Run Time already excludes unplanned downtime)
    - Performance = pieces per hour the machine actually made, divided
      by the pieces per hour it was rated to make
    - Quality = (produced - rejected) / produced
    - OEE = Availability x Performance x Quality
    """
    df = production.merge(plan[["WorkOrder", "PlannedHours"]], on="WorkOrder", how="left")
    df["PlannedTimeHours"] = df["PlannedHours"].astype(float)

    unplanned_stoppages = downtime_by_order[downtime_by_order["PlannedStoppage"] == "No"]
    setup_stoppages = downtime_by_order[
        downtime_by_order["StoppageReason"].str.contains("Change / Setup|Change/Setup", case=False, na=False, regex=True)
    ]

    unplanned_minutes = unplanned_stoppages.groupby("WorkOrder")["DowntimeDurationMin"].sum()
    setup_minutes = setup_stoppages.groupby("WorkOrder")["DowntimeDurationMin"].sum()

    df["UnplannedDowntimeHours"] = df["WorkOrder"].map(unplanned_minutes).fillna(0) / 60.0
    df["SetupTimeHours"] = df["WorkOrder"].map(setup_minutes).fillna(0) / 60.0

    planned_time = df["PlannedTimeHours"].fillna(df["LeadTimeProdHours"])
    df["RunTimeHours"] = (planned_time - df["UnplannedDowntimeHours"]).clip(lower=0.01)

    df["Availability"] = (df["RunTimeHours"] / df["PlannedTimeHours"]).clip(0, 1)

    rated_capacity = df.apply(
        lambda row: capacity_by_machine.get((row["MachineId"], row["ToolId"]), np.nan), axis=1
    )
    df["RatedCapacityPcH"] = rated_capacity
    df["IdealCycleTimeSec"] = 3600.0 / rated_capacity
    df["Performance"] = ((df["ProducedQty"] / df["RunTimeHours"]) / rated_capacity).clip(0, 1.3)

    df["Quality"] = ((df["ProducedQty"] - df["RejectedQty"]) / df["ProducedQty"]).clip(0, 1)

    df["OEE"] = df["Availability"] * df["Performance"] * df["Quality"]

    df["ActualCycleTimeSec"] = (df["RunTimeHours"] * 3600.0) / df["ProducedQty"]

    df = df.sort_values(["MachineId", "_start_dt"])
    df["_next_start_dt"] = df.groupby("MachineId")["_start_dt"].shift(-1)
    df["ThroughputLeadTimeHours"] = (df["_next_start_dt"] - df["_start_dt"]).dt.total_seconds() / 3600.0

    return df


def compute_production_time(df: pd.DataFrame, start_column="StartTime", end_column="EndTime",
                             duration_hours_column: str | None = None) -> pd.Series:
    """Computes how many hours an order took, from the start and end
    time. If a planned-duration column already exists, I use it
    directly. Otherwise, I compute it from the difference between the
    two times (if the end looks earlier than the start, the order
    rolled past midnight, so I add 24h)."""
    if duration_hours_column and duration_hours_column in df.columns:
        return df[duration_hours_column].astype(float)

    start = pd.to_timedelta(df[start_column].astype(str))
    end = pd.to_timedelta(df[end_column].astype(str))
    duration_hours = (end - start).dt.total_seconds() / 3600.0
    duration_hours = np.where(duration_hours < 0, duration_hours + 24, duration_hours)

    return pd.Series(duration_hours, index=df.index, name="LeadTimeProdHours")


UNPLANNED_FAILURE_WORDS = ["Failure", "Shortage", "Unavailable"]


def classify_stoppage(df: pd.DataFrame, reason_column="StoppageReason",
                       planned_column="PlannedStoppage") -> pd.Series:
    """Flags whether a stoppage was a genuine unplanned FAILURE (a
    breakdown, a material shortage) -- not just any unplanned stoppage
    (which also includes things like an unplanned mold/tool change)."""
    reason_indicates_failure = df[reason_column].str.contains(
        "|".join(UNPLANNED_FAILURE_WORDS), case=False, na=False
    )
    was_flagged_unplanned = df[planned_column].str.strip().str.lower().eq("no")

    return reason_indicates_failure & was_flagged_unplanned


def add_maintenance_info(downtime: pd.DataFrame) -> pd.DataFrame:
    """Computes the duration of each stoppage (in minutes) and adds
    columns saying whether it was a genuine unplanned failure, a
    changeover/setup, or preventive maintenance."""
    df = downtime.copy()

    start = pd.to_timedelta(df["StoppageStartTime"].astype(str))
    end = pd.to_timedelta(df["StoppageEndTime"].astype(str))
    duration_minutes = (end - start).dt.total_seconds() / 60.0

    df["DowntimeDurationMin"] = duration_minutes.where(duration_minutes >= 0, duration_minutes + 24 * 60)

    df["UnplannedFailure"] = classify_stoppage(df)
    df["IsChangeoverSetup"] = df["StoppageReason"].str.contains(
        "Change / Setup|Change/Setup", case=False, na=False, regex=True
    )
    df["IsPreventiveMaintenance"] = df["StoppageReason"].str.contains(
        "Preventive Maintenance", case=False, na=False
    )

    return df


# ---------------------------------------------------------------------------
# 5. SPC / AQL (statistical process control, quality sampling)
# ---------------------------------------------------------------------------

SPC_CONSTANTS = {
    2: dict(A2=1.880, D3=0.0, D4=3.267),
    3: dict(A2=1.023, D3=0.0, D4=2.574),
    4: dict(A2=0.729, D3=0.0, D4=2.282),
    5: dict(A2=0.577, D3=0.0, D4=2.114),
    6: dict(A2=0.483, D3=0.0, D4=2.004),
    7: dict(A2=0.419, D3=0.076, D4=1.924),
    8: dict(A2=0.373, D3=0.136, D4=1.864),
    9: dict(A2=0.337, D3=0.184, D4=1.816),
    10: dict(A2=0.308, D3=0.223, D4=1.777),
}


def compute_control_limits(df: pd.DataFrame, group_columns: list[str], subgroup_size: int) -> pd.DataFrame:
    """Computes the control limits (X-bar/R chart), per group
    (characteristic x machine x mold x product), and copies the same
    value onto every row in that group. Doing it this way means a chart
    can be built straight from the table, with nothing left to recalculate."""
    constants = SPC_CONSTANTS[subgroup_size]
    df = df.copy()

    group = df.groupby(group_columns)

    df["XBarCL"] = group["XBar"].transform("mean")
    df["RangeRCL"] = group["RangeR"].transform("mean")

    df["XBarUCL"] = df["XBarCL"] + constants["A2"] * df["RangeRCL"]
    df["XBarLCL"] = df["XBarCL"] - constants["A2"] * df["RangeRCL"]
    df["RangeRUCL"] = constants["D4"] * df["RangeRCL"]
    df["RangeRLCL"] = constants["D3"] * df["RangeRCL"]

    df["OutOfControlXBar"] = (df["XBar"] > df["XBarUCL"]) | (df["XBar"] < df["XBarLCL"])
    df["OutOfControlRange"] = (df["RangeR"] > df["RangeRUCL"]) | (df["RangeR"] < df["RangeRLCL"])

    return df


D2_CONSTANT = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704,
               8: 2.847, 9: 2.970, 10: 3.078}


def compute_process_capability(df: pd.DataFrame, group_columns: list[str], subgroup_size: int) -> pd.DataFrame:
    """Computes Cp/Cpk and Pp/Ppk, per group.

    The difference between them: Cp/Cpk only look at the variation
    WITHIN each subgroup -- they show what the process can do on a good
    day. Pp/Ppk use the TOTAL variation (including how much the process
    has drifted over time), which is closer to what the customer
    actually receives. If Cpk is a lot lower than Cp, it means the
    process isn't centered on the target -- not just "too spread out."
    """
    d2 = D2_CONSTANT[subgroup_size]
    df = df.copy()
    group = df.groupby(group_columns)

    average_range = group["RangeR"].transform("mean")
    within_subgroup_std = average_range / d2
    grand_average = group["XBar"].transform("mean")

    df["Cp"] = (df["USL"] - df["LSL"]) / (6 * within_subgroup_std)
    df["Cpk"] = np.minimum(
        (df["USL"] - grand_average) / (3 * within_subgroup_std),
        (grand_average - df["LSL"]) / (3 * within_subgroup_std),
    )

    overall_std = group["XBar"].transform("std")
    df["Pp"] = (df["USL"] - df["LSL"]) / (6 * overall_std)
    df["Ppk"] = np.minimum(
        (df["USL"] - grand_average) / (3 * overall_std),
        (grand_average - df["LSL"]) / (3 * overall_std),
    )

    if "Nominal" in df.columns:
        nominal_value = df["Nominal"]
    else:
        nominal_value = (df["USL"] + df["LSL"]) / 2

    overall_std_with_target_shift = np.sqrt(
        overall_std ** 2 + (grand_average - nominal_value) ** 2
    )
    df["Cpm"] = (df["USL"] - df["LSL"]) / (6 * overall_std_with_target_shift)

    df["SigmaLevel"] = df["Cpk"] * 3 + 1.5

    return df


def compute_attribute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Computes the defect rate (p-chart), DPU and DPMO for the
    attribute (AQL) inspections. Assumes 1 defect opportunity per unit,
    since each row is one characteristic on one lot."""
    df = df.copy()
    df["DefectRateP"] = df["DefectsFound"] / df["SampleSize"]
    df["DPU"] = df["DefectsFound"] / df["SampleSize"]
    df["DPMO"] = df["DPU"] * 1_000_000
    return df


# ---------------------------------------------------------------------------
# 6. MAINTENANCE
# ---------------------------------------------------------------------------

PLANNED_STOPPAGE_REASONS = {
    "Mold Change / Setup", "Color Change / Screen Setup", "Ribbon Change / Setup",
    "Scheduled Cleaning", "Screen Cleaning", "Planned Preventive Maintenance",
    "Meal Break (Shift 3 - No Relief Crew, 10Min Shutdown + 60Min Break + 10Min Startup)",
}

# already defined above: UNPLANNED_FAILURE_WORDS = ["Failure", "Shortage", "Unavailable"]


# ---------------------------------------------------------------------------
# 7. QUALITY -- customer complaints, suppliers, NC/CAPA
# ---------------------------------------------------------------------------

def compute_days_between(df: pd.DataFrame, start_column: str, end_column: str, new_column_name: str) -> pd.DataFrame:
    """Generic helper to compute how many days passed between two dates
    -- I use it for supplier response time, CAPA closure time, complaint
    resolution time. If the end date doesn't exist yet (the record is
    still open), the result is simply left blank (NaN), no special
    handling needed."""
    df = df.copy()
    df[new_column_name] = (pd.to_datetime(df[end_column]) - pd.to_datetime(df[start_column])).dt.days
    return df


def compute_complaints_per_million_shipped(complaints: pd.DataFrame, sales: pd.DataFrame,
                                            group_columns: list[str] | None = None) -> pd.Series:
    """Adjusts the complaint count by the quantity shipped, so a big
    customer doesn't automatically look "worse" than a small one just
    because they buy more. This is the standard way to compare
    complaint rates across customers/products that ship very different volumes."""
    if group_columns:
        complaint_count = complaints.groupby(group_columns).size()
        shipped_quantity = sales.groupby(group_columns)["ShippedQty"].sum()
    else:
        complaint_count = pd.Series({"Total": len(complaints)})
        shipped_quantity = pd.Series({"Total": sales["ShippedQty"].sum()})

    return (complaint_count / shipped_quantity * 1_000_000).rename("ComplaintsPerMillionShipped")


def compute_supplier_approval_rate(lot_disposition: pd.DataFrame,
                                    group_columns: list[str] = ("SupplierId",)) -> pd.DataFrame:
    """Percentage of a supplier's incoming lots that were Accepted
    outright (not counting Accepted with Deviation or Rejected)."""
    counts = (
        lot_disposition.groupby(list(group_columns))["FinalDecision"]
        .value_counts(normalize=True)
        .unstack(fill_value=0)
    )
    counts["ApprovalRatePct"] = counts.get("Accepted", 0) * 100
    return counts
