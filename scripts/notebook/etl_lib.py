"""
etl_lib.py

All the cleaning/feature-engineering functions I use across the
notebooks, in one place, so I'm not copy-pasting the same code into
every notebook (and risking two notebooks doing "the same" cleaning
slightly differently without me noticing).

Rough map of what's in here:
1. Basic cleaning (whitespace, weird casing, placeholder nulls, negative
   numbers that shouldn't be negative, duplicate rows)
2. Calendar stuff (ISO week/weekday, shift number)
3. The LotId traceability code
4. OEE calculations
5. SPC/AQL stuff (control limits, Cp/Cpk)
6. Maintenance stuff (planned vs unplanned downtime)
7. QA stuff (customer complaints, supplier quality)
"""
from __future__ import annotations
import re
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. BASIC CLEANING
# ---------------------------------------------------------------------------

# these are the placeholder values people type when a text field has
# nothing to say -- a dash, a slash, a space. pandas won't treat these as
# missing on its own, so I have to catch them manually or they end up
# looking like a real category (e.g. a "-" technician showing up in a
# groupby)
NULL_TOKENS = {"-", "--", "---", "/", "//", "\\", "n/a", "na", "none", "null", ""}


def normalize_placeholder_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Turns the placeholder tokens above into actual NaN."""
    df = df.copy()
    obj_cols = df.select_dtypes(include="object").columns
    for c in obj_cols:
        stripped = df[c].astype(str).str.strip()
        is_null_token = stripped.str.lower().isin(NULL_TOKENS)
        df.loc[df[c].notna() & is_null_token, c] = np.nan
    return df


def strip_whitespace(df: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    """Trims leading/trailing spaces and collapses double spaces in text columns."""
    df = df.copy()
    cols = cols or df.select_dtypes(include="object").columns.tolist()
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: re.sub(r"\s+", " ", x).strip() if isinstance(x, str) else x)
    return df


def standardize_categories(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Makes 'INJECTION MOLDING', 'injection molding' and 'Injection Molding '
    all turn into the same 'Injection Molding'. I used .title() instead of a
    hardcoded lookup dict so it doesn't break if a new category shows up later."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: x.strip().title() if isinstance(x, str) else x)
    return df


def fix_negative_quantities(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Some scrap/consumption numbers show up negative, which doesn't make
    physical sense (you can't reject -12 units) -- looks like a sign typo
    somewhere upstream. I just take the absolute value instead of dropping
    the row, since the rest of the row is fine."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = df[c].abs()
    return df


def drop_exact_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> tuple[pd.DataFrame, int]:
    """Drops fully duplicated rows and tells you how many it removed, so
    it doesn't just silently disappear data without anyone noticing."""
    before = len(df)
    df = df.drop_duplicates(subset=subset).reset_index(drop=True)
    return df, before - len(df)


def null_report(df: pd.DataFrame) -> pd.Series:
    """Just isna().sum(), wrapped so every notebook calls the same thing."""
    return df.isna().sum().sort_values(ascending=False)


# ---------------------------------------------------------------------------
# 2. CALENDAR STUFF
# ---------------------------------------------------------------------------

def add_iso_calendar_columns(df: pd.DataFrame, date_col: str = "Date") -> pd.DataFrame:
    """Adds ISOWeek and ISOWeekday (1=Monday...7=Sunday).

    I used ISO week numbers instead of plain Python .week because that's
    what's actually used for shift/overtime rules in manufacturing --
    every week is a full Monday-Sunday block, no partial weeks at the
    start/end of the year messing things up.
    """
    df = df.copy()
    dt = pd.to_datetime(df[date_col])
    iso = dt.dt.isocalendar()
    df["ISOWeek"] = iso["week"].astype(int)
    df["ISOWeekday"] = iso["day"].astype(int)
    return df


def compute_shift_number(start_time: pd.Series) -> pd.Series:
    """This is just the Excel IF formula from the brief translated to pandas:

        =IF(AND(StartTime>=06:00, StartTime<14:00), 1,
            IF(AND(StartTime>=14:00, StartTime<22:00), 2, 3))

    Shift 1 = 06:00-13:59, Shift 2 = 14:00-21:59, Shift 3 = everything else.
    """
    t = pd.to_datetime(start_time.astype(str), format="mixed", errors="coerce")
    minutes = t.dt.hour * 60 + t.dt.minute
    shift_number = np.select(
        [
            (minutes >= 6 * 60) & (minutes < 14 * 60),
            (minutes >= 14 * 60) & (minutes < 22 * 60),
        ],
        [1, 2],
        default=3,
    )
    return pd.Series(shift_number, index=start_time.index, name="ShiftNumber")


# ---------------------------------------------------------------------------
# 3. THE LotId CODE
# ---------------------------------------------------------------------------

# process digit from the brief -- note there's no "3", that's not a typo,
# it's just not used (I left it as-is instead of "fixing" it since I
# didn't want to break the agreed code)
PROCESS_CODE = {
    "Blow Molding": "1", "Injection Molding": "2",
    "Screen Printing": "4", "Hot Foil Stamping": "5",
}


def _machine_number(machine_id: str) -> str:
    """ISBM-001 -> 01, IM-004 -> 04, etc."""
    m = re.search(r"(\d+)$", str(machine_id))
    return f"{int(m.group(1)) % 100:02d}" if m else "00"


def _work_order_number(work_order: str) -> str:
    """WO-6005 -> 06005 (just the number part, padded to 5 digits)."""
    m = re.search(r"(\d+)$", str(work_order))
    return f"{int(m.group(1)) % 100000:05d}" if m else "00000"


def build_lot_prefix(date: pd.Series, shift_number: pd.Series, process: pd.Series,
                      machine_id: pd.Series, work_order: pd.Series) -> pd.Series:
    """Builds the first 14 characters of LotId:

        YY WW D T P MM OOOOO
        26 09 2 2 1  01 06005

    year(2) + ISO week(2) + ISO weekday(1) + shift(1) + process(1) +
    machine number(2) + work order number(5)
    """
    dt = pd.to_datetime(date)
    iso = dt.dt.isocalendar()
    yy = (dt.dt.year % 100).astype(int).astype(str).str.zfill(2)
    ww = iso["week"].astype(int).astype(str).str.zfill(2)
    d = iso["day"].astype(int).astype(str)
    t = shift_number.astype(int).astype(str)
    p = process.map(PROCESS_CODE).fillna("0")
    mm = machine_id.apply(_machine_number)
    oo = work_order.apply(_work_order_number)
    return yy + ww + d + t + p + mm + oo


def assign_material_lot_sequence(matcons: pd.DataFrame, wo_col="WorkOrder",
                                  material_lot_col="MaterialLot",
                                  order_col="RecordSeq") -> pd.Series:
    """This is the last 2 digits of LotId -- starts at 01 for a new work
    order, and only goes up when the actual physical material lot changes
    (not just because the shift changed).

    This one took me a couple of tries to get right. `order_col` is a
    record id that keeps the rows in the order they actually happened,
    which matters because the CSV export can come back in a different
    row order and I still need to know which record came first.
    """
    df = matcons.sort_values([wo_col, order_col]).copy()
    seq = np.empty(len(df), dtype=int)
    counter = 0
    prev_wo = None
    prev_lot = None
    for i, (wo_val, lot_val) in enumerate(zip(df[wo_col].values, df[material_lot_col].values)):
        if wo_val != prev_wo:
            counter = 1
        elif lot_val != prev_lot:
            counter += 1
        seq[i] = counter
        prev_wo, prev_lot = wo_val, lot_val
    out = pd.Series(seq, index=df.index, name="MaterialLotSeq")
    return out.reindex(matcons.index)


def ffill_material_lot(matcons: pd.DataFrame, wo_col="WorkOrder", material_lot_col="MaterialLot",
                        order_col="RecordSeq") -> pd.Series:
    """If MaterialLot is blank after the null cleanup, it's almost
    certainly just a case of someone forgetting to write it down, not an
    actual new lot showing up. So I fill it forward with the last known
    value for that work order before counting lot changes -- otherwise
    every blank would look like "a new lot started here" and the sequence
    number in LotId would be wrong.
    """
    df = matcons.sort_values([wo_col, order_col])
    filled = df.groupby(wo_col)[material_lot_col].ffill().bfill()
    return filled.reindex(matcons.index)


def resolve_end_datetime(date: pd.Series, start_time: pd.Series, end_time: pd.Series,
                          duration_hours: pd.Series | None = None) -> pd.Series:
    """The raw tables only store a time-of-day, not a full datetime, so if
    an order runs past midnight I need to figure out the real end date
    myself. If I have the planned duration I just add it to the start.
    Otherwise: if EndTime looks earlier than StartTime, it must have
    rolled into the next day.
    """
    start_dt = pd.to_datetime(date) + pd.to_timedelta(start_time.astype(str))
    if duration_hours is not None:
        return start_dt + pd.to_timedelta(duration_hours.astype(float), unit="h")
    end_t = pd.to_timedelta(end_time.astype(str))
    start_t = pd.to_timedelta(start_time.astype(str))
    rolled = end_t <= start_t
    end_dt = pd.to_datetime(date) + end_t
    end_dt = end_dt.where(~rolled, end_dt + pd.Timedelta(days=1))
    return end_dt


def match_downtime_to_work_order(downtime: pd.DataFrame, production: pd.DataFrame) -> pd.Series:
    """Downtime records don't have a WorkOrder column of their own, so to
    figure out which order was running when a machine stopped, I check
    which order's [start, end) window contains that downtime's timestamp,
    per machine. Returns NaN if nothing was running (e.g. a stoppage
    logged right at the very start of the whole dataset).
    """
    dt_event = pd.to_datetime(downtime["Date"]) + pd.to_timedelta(downtime["StoppageStartTime"].astype(str))
    prod = production[["MachineId", "WorkOrder", "_start_dt", "_end_dt"]].copy()

    result = pd.Series(np.nan, index=downtime.index, dtype=object)
    for machine, idx in downtime.groupby("MachineId").groups.items():
        p = prod[prod["MachineId"] == machine].sort_values("_start_dt")
        if p.empty:
            continue
        events = dt_event.loc[idx]
        pos = np.searchsorted(p["_start_dt"].values, events.values, side="right") - 1
        pos = np.clip(pos, 0, len(p) - 1)
        candidate_wo = p["WorkOrder"].values[pos]
        candidate_end = p["_end_dt"].values[pos]
        valid = events.values < candidate_end
        wo_result = np.where(valid, candidate_wo, np.nan)
        result.loc[idx] = wo_result
    return result


# ---------------------------------------------------------------------------
# 4. OEE
# ---------------------------------------------------------------------------

def add_lead_time_prod(df: pd.DataFrame, start_col="StartTime", end_col="EndTime",
                        duration_hours_col: str | None = None) -> pd.Series:
    """Duration in decimal hours, handling the case where EndTime is
    smaller than StartTime because it rolled past midnight."""
    if duration_hours_col and duration_hours_col in df.columns:
        return df[duration_hours_col].astype(float)
    start = pd.to_timedelta(df[start_col].astype(str))
    end = pd.to_timedelta(df[end_col].astype(str))
    delta = (end - start).dt.total_seconds() / 3600.0
    delta = np.where(delta < 0, delta + 24, delta)
    return pd.Series(delta, index=df.index, name="LeadTimeProdHours")


def compute_oee_components(prod: pd.DataFrame, plan: pd.DataFrame, downtime_by_wo: pd.DataFrame,
                            capacity_lookup: dict) -> pd.DataFrame:
    """Computes OEE and the pieces it's made of, per work order.

    Quick reminder to myself of the formulas (this took a couple of
    re-reads of the brief to get right):
    - Availability = Run Time / Planned Time (Run Time excludes unplanned downtime)
    - Performance = actual pieces/hour vs. the machine's rated pieces/hour
    - Quality = (produced - rejected) / produced -- this is the 100%-count
      yield, NOT the same thing as the AQL sample result from the QC tables
    - OEE = Availability x Performance x Quality
    - plus cycle time, setup time, and the "throughput lead time" (gap
      until the next order starts on the same machine, so it catches idle
      time between orders too, not just the order's own run time)
    """
    df = prod.merge(plan[["WorkOrder", "PlannedHours"]], on="WorkOrder", how="left")
    df["PlannedTimeHours"] = df["PlannedHours"].astype(float)

    unplanned = downtime_by_wo[downtime_by_wo["PlannedStoppage"] == "No"]
    planned_setup = downtime_by_wo[downtime_by_wo["StoppageReason"].str.contains(
        "Change / Setup|Change/Setup", case=False, na=False, regex=True)]

    unpl_min = unplanned.groupby("WorkOrder")["DowntimeDurationMin"].sum()
    setup_min = planned_setup.groupby("WorkOrder")["DowntimeDurationMin"].sum()

    df["UnplannedDowntimeHours"] = df["WorkOrder"].map(unpl_min).fillna(0) / 60.0
    df["SetupTimeHours"] = df["WorkOrder"].map(setup_min).fillna(0) / 60.0
    df["RunTimeHours"] = (df["PlannedTimeHours"].fillna(df["LeadTimeProdHours"]) - df["UnplannedDowntimeHours"]).clip(lower=0.01)

    df["Availability"] = (df["RunTimeHours"] / df["PlannedTimeHours"]).clip(0, 1)

    # capacity_lookup gives me pieces/hour per (machine, tool) -- this
    # already accounts for cavity count on the injection/blow molds, it's
    # the machine's real rated speed
    ideal_rate_per_h = df.apply(lambda r: capacity_lookup.get((r["MachineId"], r["ToolId"]), np.nan), axis=1)
    df["RatedCapacityPcH"] = ideal_rate_per_h
    df["IdealCycleTimeSec"] = 3600.0 / ideal_rate_per_h
    df["Performance"] = ((df["ProducedQty"] / df["RunTimeHours"]) / ideal_rate_per_h).clip(0, 1.3)

    df["Quality"] = ((df["ProducedQty"] - df["RejectedQty"]) / df["ProducedQty"]).clip(0, 1)

    df["OEE"] = df["Availability"] * df["Performance"] * df["Quality"]

    df["ActualCycleTimeSec"] = (df["RunTimeHours"] * 3600.0) / df["ProducedQty"]

    df = df.sort_values(["MachineId", "_start_dt"])
    df["_next_start_dt"] = df.groupby("MachineId")["_start_dt"].shift(-1)
    df["ThroughputLeadTimeHours"] = (df["_next_start_dt"] - df["_start_dt"]).dt.total_seconds() / 3600.0

    return df


# ---------------------------------------------------------------------------
# 5. SPC / AQL STUFF
# ---------------------------------------------------------------------------

# control chart constants for subgroup sizes 2-10 (A2 for the X-bar
# limits, D3/D4 for the R limits) -- pulled these from Montgomery's SPC
# textbook, Table 6.1, didn't want to derive them myself
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


def add_control_limits(df: pd.DataFrame, group_cols: list[str], subgroup_n: int) -> pd.DataFrame:
    """X-bar/R control limits, computed per group (characteristic x
    machine x mold x product) and copied onto every row in that group.
    Doing it this way means a chart can be built straight from the table
    without recalculating anything.
    """
    const = SPC_CONSTANTS[subgroup_n]
    df = df.copy()
    grp = df.groupby(group_cols)
    df["XBarCL"] = grp["XBar"].transform("mean")
    df["RangeRCL"] = grp["RangeR"].transform("mean")
    df["XBarUCL"] = df["XBarCL"] + const["A2"] * df["RangeRCL"]
    df["XBarLCL"] = df["XBarCL"] - const["A2"] * df["RangeRCL"]
    df["RangeRUCL"] = const["D4"] * df["RangeRCL"]
    df["RangeRLCL"] = const["D3"] * df["RangeRCL"]
    df["OutOfControlXBar"] = (df["XBar"] > df["XBarUCL"]) | (df["XBar"] < df["XBarLCL"])
    df["OutOfControlRange"] = (df["RangeR"] > df["RangeRUCL"]) | (df["RangeR"] < df["RangeRLCL"])
    return df


def add_process_capability(df: pd.DataFrame, group_cols: list[str], subgroup_n: int) -> pd.DataFrame:
    """Cp/Cpk and Pp/Ppk per group.

    The way I think about the difference: Cp/Cpk only look at the
    variation *inside* each subgroup, so they tell you what the process
    is capable of on a good day. Pp/Ppk use the total variation
    (including drift between subgroups over time), which is closer to
    what a customer actually sees. If Cpk is a lot lower than Cp, the
    process isn't centered on the target, not just "too spread out."
    """
    d2 = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704,
          8: 2.847, 9: 2.970, 10: 3.078}[subgroup_n]
    df = df.copy()
    grp = df.groupby(group_cols)
    r_bar = grp["RangeR"].transform("mean")
    sigma_within = r_bar / d2
    xbar_grand = grp["XBar"].transform("mean")

    df["Cp"] = (df["USL"] - df["LSL"]) / (6 * sigma_within)
    df["Cpk"] = np.minimum(
        (df["USL"] - xbar_grand) / (3 * sigma_within),
        (xbar_grand - df["LSL"]) / (3 * sigma_within),
    )

    sigma_overall = grp["XBar"].transform("std")
    df["Pp"] = (df["USL"] - df["LSL"]) / (6 * sigma_overall)
    df["Ppk"] = np.minimum(
        (df["USL"] - xbar_grand) / (3 * sigma_overall),
        (xbar_grand - df["LSL"]) / (3 * sigma_overall),
    )
    nominal = (df["USL"] + df["LSL"]) / 2 if "Nominal" not in df.columns else df["Nominal"]
    sigma_t = np.sqrt(sigma_overall ** 2 + (xbar_grand - nominal) ** 2)
    df["Cpm"] = (df["USL"] - df["LSL"]) / (6 * sigma_t)

    df["SigmaLevel"] = df["Cpk"] * 3 + 1.5  # rough short-term sigma-level equivalent
    return df


def add_attribute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """p-chart value, DPU and DPMO for the AQL attribute inspections.
    Assumes 1 opportunity per unit since each row is one characteristic
    on one lot -- would need adjusting if I had a richer opportunity count."""
    df = df.copy()
    df["DefectRateP"] = df["DefectsFound"] / df["SampleSize"]
    df["DPU"] = df["DefectsFound"] / df["SampleSize"]
    df["DPMO"] = df["DPU"] * 1_000_000
    return df


# ---------------------------------------------------------------------------
# 6. MAINTENANCE STUFF
# ---------------------------------------------------------------------------

# keywords that mean "this is a real equipment failure" for MTBF/MTTR --
# changeovers, cleaning, and preventive maintenance are planned, not
# failures, so they need to be kept out or MTBF/MTTR would make the
# equipment look worse than it is
UNPLANNED_FAILURE_KEYWORDS = ["Failure", "Shortage", "Unavailable"]

# every downtime reason tagged planned or not -- this is what I use to
# split the Pareto chart in two. combining them into one chart was
# actually my first attempt and it just showed mold changes at the top
# every time, which isn't useful for anyone trying to fix real problems
PLANNED_STOPPAGE_REASONS = {
    "Mold Change / Setup", "Color Change / Screen Setup", "Ribbon Change / Setup",
    "Scheduled Cleaning", "Screen Cleaning", "Planned Preventive Maintenance",
    "Meal Break (Shift 3 - No Relief Crew, 10Min Shutdown + 60Min Break + 10Min Startup)",
}


def classify_downtime(df: pd.DataFrame, reason_col="StoppageReason", planned_col="PlannedStoppage") -> pd.Series:
    is_failure = df[reason_col].str.contains("|".join(UNPLANNED_FAILURE_KEYWORDS), case=False, na=False)
    is_unplanned = df[planned_col].str.strip().str.lower().eq("no")
    return (is_failure & is_unplanned)


def add_maintenance_flags(downtime: pd.DataFrame) -> pd.DataFrame:
    df = downtime.copy()
    df["DowntimeDurationMin"] = (
        pd.to_timedelta(df["StoppageEndTime"].astype(str)) - pd.to_timedelta(df["StoppageStartTime"].astype(str))
    ).dt.total_seconds() / 60.0
    df["DowntimeDurationMin"] = df["DowntimeDurationMin"].where(df["DowntimeDurationMin"] >= 0,
                                                                  df["DowntimeDurationMin"] + 24 * 60)
    df["UnplannedFailure"] = classify_downtime(df)
    df["IsChangeoverSetup"] = df["StoppageReason"].str.contains("Change / Setup|Change/Setup", case=False, na=False, regex=True)
    df["IsPreventiveMaintenance"] = df["StoppageReason"].str.contains("Preventive Maintenance", case=False, na=False)
    return df


# ---------------------------------------------------------------------------
# 7. QUALITY ASSURANCE STUFF (customer complaints, supplier quality, NC/CAPA)
# ---------------------------------------------------------------------------

def add_days_between(df: pd.DataFrame, start_col: str, end_col: str, out_col: str) -> pd.DataFrame:
    """Generic day-counting helper -- used for supplier response time,
    CAPA closure time, complaint resolution time. Handles open records
    (no end date yet) fine, since subtracting NaT from a date just gives NaN."""
    df = df.copy()
    df[out_col] = (pd.to_datetime(df[end_col]) - pd.to_datetime(df[start_col])).dt.days
    return df


def complaints_per_million_shipped(complaints: pd.DataFrame, sales: pd.DataFrame,
                                    group_cols: list[str] | None = None) -> pd.Series:
    """Normalizes complaint count by volume shipped, so a big customer
    doesn't automatically look "worse" than a small one just because they
    buy more. This is a pretty standard way to compare complaint rates
    across customers/products that ship very different amounts."""
    if group_cols:
        n_complaints = complaints.groupby(group_cols).size()
        n_shipped = sales.groupby(group_cols)["ShippedQty"].sum()
    else:
        n_complaints = pd.Series({"Total": len(complaints)})
        n_shipped = pd.Series({"Total": sales["ShippedQty"].sum()})
    return (n_complaints / n_shipped * 1_000_000).rename("ComplaintsPerMillionShipped")


def supplier_approval_rate(lot_disposition: pd.DataFrame, group_cols: list[str] = ("SupplierId",)) -> pd.DataFrame:
    """Percent of a supplier's incoming lots that got Accepted outright
    (vs. Accepted with Deviation or Rejected)."""
    counts = lot_disposition.groupby(list(group_cols))["FinalDecision"].value_counts(normalize=True).unstack(fill_value=0)
    counts["ApprovalRatePct"] = counts.get("Accepted", 0) * 100
    return counts
