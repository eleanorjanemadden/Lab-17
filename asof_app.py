"""Lab 17: python3 -m streamlit run asof_app.py."""
from datetime import date, datetime
from io import StringIO
import re

import numpy as np
import pandas as pd
import requests
import streamlit as st

SERIES = {
    "BAA": "Moody's Baa corporate bond yield",
    "FEDFUNDS": "Federal funds rate",
    "DGS10": "10-year Treasury yield",
    "MORTGAGE30US": "30-year mortgage rate",
}


def parse_csv(text, series_id, vintage=None):
    """Keep missing days missing; ALFRED appends the vintage to its column name."""
    frame = pd.read_csv(StringIO(text), na_values=["."])
    expected = series_id if vintage is None else f"{series_id}_{vintage:%Y%m%d}"
    if len(frame.columns) != 2 or frame.columns[1] != expected:
        raise ValueError(f"Unexpected CSV for {series_id}; expected {expected}.")
    frame.columns = ["date", "value"]
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["value"] = pd.to_numeric(frame["value"], errors="raise")
    if frame["date"].duplicated().any():
        raise ValueError("Duplicate observation dates in download.")
    return frame.set_index("date").sort_index()["value"]


@st.cache_data(ttl=3600, show_spinner=False)
def download_today(series_id, download_day):
    """One public FRED CSV request; the day also prevents overnight stale caching."""
    response = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                            params={"id": series_id}, timeout=30)
    response.raise_for_status()
    values = parse_csv(response.text, series_id)
    values.attrs = {"url": response.url, "downloaded": datetime.now().astimezone().isoformat(),
                    "raw_csv": response.text}
    return values


@st.cache_data(ttl=3600, show_spinner=False)
def download_asof(series_id, asof_date, download_day):
    """Ask ALFRED for the vintage, rather than date-filtering today's values."""
    response = requests.get("https://alfred.stlouisfed.org/graph/alfredgraph.csv",
                            params={"id": series_id, "vintage_date": asof_date.isoformat()}, timeout=30)
    response.raise_for_status()
    values = parse_csv(response.text, series_id, asof_date)
    values.attrs = {"url": response.url, "downloaded": datetime.now().astimezone().isoformat(),
                    "raw_csv": response.text}
    return values


def compare_series(series_id, today, known):
    current, past = today.dropna(), known.dropna()
    common = pd.concat([past.rename("known"), current.rename("today")], axis=1).dropna()
    revised = int((~np.isclose(common["known"], common["today"], rtol=0, atol=1e-9)).sum())
    last_known = past.index.max() if len(past) else None
    return {
        "Series": f"https://fred.stlouisfed.org/series/{series_id}",
        "Last measured as known": last_known.strftime("%Y-%m-%d") if last_known is not None else None,
        "Value as known": float(past.iloc[-1]) if len(past) else None,
        "Last measured today": current.index[-1].strftime("%Y-%m-%d") if len(current) else None,
        "Value today": float(current.iloc[-1]) if len(current) else None,
        "Later values": int((current.index > last_known).sum()) if last_known is not None else len(current),
        "Revised values": revised,
    }


def main():
    st.set_page_config(page_title="Point-in-Time Rates Audit", layout="wide")
    today = date.today()
    st.title("Point-in-Time Rates Audit")
    st.caption(f"Data from FRED and ALFRED, Federal Reserve Bank of St. Louis, downloaded today ({today}); "
               "built with AI help, a learning demonstration, not investment advice.")
    selected = st.sidebar.multiselect("Series", list(SERIES), default=list(SERIES),
                                     format_func=lambda key: f"{key} — {SERIES[key]}")
    extra = st.sidebar.text_input("Add another FRED series ID", help="Try GS10 (my series) or PAYEMS.").strip().upper()
    start = st.sidebar.date_input("Start date", date(2020, 1, 1), min_value=date(1776, 1, 1), max_value=today)
    asof_date = st.sidebar.date_input("As known on", today, min_value=date(1776, 1, 1), max_value=today)
    if extra:
        if re.fullmatch(r"[A-Z0-9_]+", extra):
            if extra not in selected:
                selected.append(extra)
        else:
            st.error("Enter one FRED series ID using letters, digits, or underscores.")
    rows = []
    for series_id in selected:
        st.subheader(f"{series_id} — {SERIES.get(series_id, 'Additional FRED series')}")
        try:
            current = download_today(series_id, today)
            known = download_asof(series_id, asof_date, today)
            row = compare_series(series_id, current, known)
            chart = current.loc[current.index >= pd.Timestamp(start)].rename(series_id)
            if chart.dropna().empty:
                st.info("No observations in the selected chart period.")
            else:
                st.line_chart(chart, x_label="Date measured", y_label="Series units (see source)")
            st.caption(f"Last date measured known on {asof_date}: {row['Last measured as known'] or 'none'}; "
                       f"value: {row['Value as known'] if row['Value as known'] is not None else 'N/A'}. "
                       f"Retrieved {current.attrs['downloaded']}.")
            st.markdown(f"[FRED series and units]({row['Series']}) · [ALFRED vintage CSV]({known.attrs['url']})")
            rows.append(row)
        except (requests.RequestException, ValueError, KeyError) as error:
            st.error(f"{series_id}: could not load this series: {error}")
    st.subheader("As-known comparison")
    st.caption("Counts use all downloaded history; Start date changes charts only. Later values are nonmissing "
               "observations after the last known measured date. Revisions compare nonmissing values on shared "
               "dates (absolute tolerance 0.000000001). Missing days are never filled.")
    if rows:
        table = pd.DataFrame(rows)
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            "Series": st.column_config.LinkColumn("Series", display_text=r"https://fred\.stlouisfed\.org/series/(.*)"),
            "Value as known": st.column_config.NumberColumn(format="%.2f"),
            "Value today": st.column_config.NumberColumn(format="%.2f"),
        })
        st.download_button("Download comparison CSV", table.to_csv(index=False), "asof_comparison.csv", "text/csv")
    else:
        st.info("Select a series to see the comparison.")
    st.caption("A vintage date is a day-level cutoff, not proof of availability before a same-day trade. "
               "Use a verified release time or trade the following session.")


if __name__ == "__main__":
    main()
