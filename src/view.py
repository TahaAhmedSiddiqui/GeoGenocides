from __future__ import annotations
import streamlit as st
import pandas as pd


class View:
    @staticmethod
    def sidebar_data_info(preferred_path_str: str, fallback_path_str: str):
        st.header("Data source")
        st.write(
            f"Place your CSV at **{preferred_path_str}** (preferred) or **{fallback_path_str}**."
        )


    @staticmethod
    def sidebar_filters(regions, statuses, yr_min: int, yr_max: int):
        sel_regions = st.multiselect("Region", options=regions, default=regions)
        sel_status = st.multiselect("Status", options=statuses, default=statuses)
        year_range = st.slider(
            "Start year range",
            min_value=max(1900, yr_min),
            max_value=max(yr_max, yr_min),
            value=(max(1900, yr_min), max(yr_max, yr_min)),
            )
        show_labels = st.checkbox("Show text labels on map", value=False)
        return sel_regions, sel_status, year_range, show_labels


    @staticmethod
    def expander_issues(issues):
        if issues:
            with st.expander("⚠️ Data quality issues (click to expand)"):
                for i, msg in issues:
                    st.write(f"Row {i}: {msg}")


    @staticmethod
    def table(df: pd.DataFrame):
        try:
            import pyarrow # noqa: F401
            st.dataframe(df)
        except Exception as e:
            msg = str(e).split("\n")[0]
            st.warning(f"PyArrow not available/compatible ({msg}). Falling back to HTML table rendering.")
            st.markdown(df.to_html(index=False), unsafe_allow_html=True)

    @staticmethod
    def sources_panel(df: pd.DataFrame):
        if df.empty:
            st.info("No cases match the current filters.")
            return
        for _, row in df.iterrows():
            with st.expander(f"{row['name']} — Sources"):
                for raw in str(row.get("sources", "")).split(";"):
                    url = raw.strip()
                    if not url:
                        continue
                    label = url.replace("https://", "").replace("http://", "")
                    st.markdown(f"- [{label}]({url})")
                if str(row.get("summary", "")).strip():
                    st.write(row.get("summary", ""))