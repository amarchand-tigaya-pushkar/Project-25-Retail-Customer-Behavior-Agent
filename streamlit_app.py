from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Project 25 | Retail Customer Analytics",
    page_icon="🛍️",
    layout="wide",
)

st.title("🛍️ Retail Store Customer Behavior Dashboard")
st.caption("Project 25 • YOLO + OpenCV CSV Analytics")

DEFAULT_CSV = Path("output") / "customer_report.csv"
REQUIRED_COLUMNS = ["Frame Number", "Time", "Customer Count"]


@st.cache_data
def load_csv(file_or_path):
    return pd.read_csv(file_or_path)


def validate_data(data):
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        st.error(
            "CSV format does not match Project 25. Missing column(s): "
            + ", ".join(missing)
        )
        st.info("Expected columns: " + ", ".join(REQUIRED_COLUMNS))
        st.stop()

    data = data.copy()
    data["Frame Number"] = pd.to_numeric(data["Frame Number"], errors="coerce")
    data["Customer Count"] = pd.to_numeric(data["Customer Count"], errors="coerce")
    data = data.dropna(subset=["Frame Number", "Customer Count"])
    data = data.sort_values("Frame Number")
    if data.empty:
        st.error("The CSV contains no valid frame/count rows.")
        st.stop()
    return data


def make_excel_report(data):
    """Create a workbook with summary and frame-level records."""
    summary = pd.DataFrame(
        {
            "Metric": [
                "Frames analysed",
                "Average detected people per frame",
                "Highest frame count",
                "Lowest frame count",
                "Frame with highest count",
            ],
            "Value": [
                int(len(data)),
                round(float(data["Customer Count"].mean()), 2),
                int(data["Customer Count"].max()),
                int(data["Customer Count"].min()),
                int(data.loc[data["Customer Count"].idxmax(), "Frame Number"]),
            ],
        }
    )

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        data.to_excel(writer, sheet_name="Frame Records", index=False)

        # Basic spreadsheet formatting for readability.
        for sheet_name, widths in {
            "Summary": {"A": 38, "B": 24},
            "Frame Records": {"A": 18, "B": 18, "C": 20},
        }.items():
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for col, width in widths.items():
                worksheet.column_dimensions[col].width = width

    output.seek(0)
    return output.getvalue()


uploaded_file = st.sidebar.file_uploader("Upload customer_report.csv", type=["csv"])
st.sidebar.markdown("---")
st.sidebar.caption("By default, the dashboard reads output/customer_report.csv.")
st.sidebar.caption("The original main.py is not modified by this dashboard.")

if uploaded_file is not None:
    raw_data = load_csv(uploaded_file)
    source_label = uploaded_file.name
elif DEFAULT_CSV.exists():
    raw_data = load_csv(DEFAULT_CSV)
    source_label = str(DEFAULT_CSV)
else:
    st.warning("CSV report not found.")
    st.write(
        "Run the original project first, then place its report at "
        "`output/customer_report.csv`, or upload the CSV using the sidebar."
    )
    st.stop()

data = validate_data(raw_data)

st.caption(f"Data source: `{source_label}` • {len(data):,} valid frame records")

avg_count = data["Customer Count"].mean()
max_count = int(data["Customer Count"].max())
min_count = int(data["Customer Count"].min())
frame_count = len(data)
peak_frame = int(data.loc[data["Customer Count"].idxmax(), "Frame Number"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Frames analysed", f"{frame_count:,}")
c2.metric("Average people per frame", f"{avg_count:.2f}")
c3.metric("Highest frame count", f"{max_count:,}")
c4.metric("Lowest frame count", f"{min_count:,}")

st.info(
    "Interpretation: Customer Count is the number of people detected in each frame. "
    "It is not a count of unique customers. The Time column in the current original "
    "script records the computer's processing time, not the video's exact timestamp."
)

left, right = st.columns([2, 1])
with left:
    st.subheader("Customer count by frame")
    st.line_chart(data.set_index("Frame Number")[["Customer Count"]], height=340)
    st.caption(f"Peak detected count: {max_count} people at frame {peak_frame}.")

with right:
    st.subheader("Count distribution")
    distribution = (
        data["Customer Count"]
        .value_counts()
        .sort_index()
        .rename_axis("Detected people")
        .to_frame("Frames")
    )
    st.bar_chart(distribution, height=340)

st.subheader("Frame records")
min_frame = int(data["Frame Number"].min())
max_frame = int(data["Frame Number"].max())
frame_range = st.slider(
    "Filter by frame number",
    min_value=min_frame,
    max_value=max_frame,
    value=(min_frame, max_frame),
)
filtered = data[data["Frame Number"].between(frame_range[0], frame_range[1])]
st.dataframe(filtered, use_container_width=True, hide_index=True)

download_col1, download_col2 = st.columns(2)
with download_col1:
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download filtered CSV report",
        data=csv_bytes,
        file_name="customer_report_filtered.csv",
        mime="text/csv",
    )

with download_col2:
    excel_bytes = make_excel_report(filtered)
    st.download_button(
        label="📊 Download Excel report (.xlsx)",
        data=excel_bytes,
        file_name="customer_behavior_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.caption(
    "Privacy note: analyse only footage you are permitted to use. Follow applicable "
    "privacy rules and the video owner's licence/terms."
)
