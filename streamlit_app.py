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
st.caption("Project 25 • YOLO + OpenCV + ByteTrack Analytics")

OUTPUT_DIR = Path("output")
DEFAULT_CSV = OUTPUT_DIR / "customer_report.csv"
DEFAULT_TRACKING_CSV = OUTPUT_DIR / "customer_tracking_report.csv"
DEFAULT_SUMMARY_CSV = OUTPUT_DIR / "tracking_id_summary.csv"

REQUIRED_COLUMNS = ["Frame Number", "Time", "Customer Count"]
TRACKING_COLUMNS = [
    "Frame Number", "Processing Time", "Tracking ID", "X1", "Y1", "X2", "Y2"
]
SUMMARY_COLUMNS = [
    "Tracking ID", "First_Frame", "Last_Frame", "Frames_Observed",
    "Detections", "Frame_Span"
]


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


def validate_tracking_data(data):
    missing = [column for column in TRACKING_COLUMNS if column not in data.columns]
    if missing:
        st.error(
            "Tracking CSV format does not match Project 25. Missing column(s): "
            + ", ".join(missing)
        )
        st.info("Expected columns: " + ", ".join(TRACKING_COLUMNS))
        st.stop()

    data = data.copy()
    for column in ["Frame Number", "Tracking ID", "X1", "Y1", "X2", "Y2"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["Frame Number", "Tracking ID"])
    data["Frame Number"] = data["Frame Number"].astype(int)
    data["Tracking ID"] = data["Tracking ID"].astype(int)
    data = data.sort_values(["Frame Number", "Tracking ID"])
    if data.empty:
        st.error("The tracking CSV contains no valid tracking records.")
        st.stop()
    return data


def make_tracking_summary(tracking_data):
    summary = (
        tracking_data.groupby("Tracking ID")
        .agg(
            First_Frame=("Frame Number", "min"),
            Last_Frame=("Frame Number", "max"),
            Frames_Observed=("Frame Number", "nunique"),
            Detections=("Tracking ID", "size"),
        )
        .reset_index()
    )
    summary["Frame_Span"] = summary["Last_Frame"] - summary["First_Frame"] + 1
    return summary.sort_values(
        ["Frames_Observed", "Detections"], ascending=False
    ).reset_index(drop=True)


def make_excel_report(frame_data, tracking_data=None, tracking_summary=None):
    """Create an Excel workbook with the available analytics sheets."""
    metrics = [
        ("Frames analysed", int(len(frame_data))),
        ("Average detected people per frame", round(float(frame_data["Customer Count"].mean()), 2)),
        ("Highest frame count", int(frame_data["Customer Count"].max())),
        ("Lowest frame count", int(frame_data["Customer Count"].min())),
        ("Frame with highest count", int(frame_data.loc[frame_data["Customer Count"].idxmax(), "Frame Number"])),
    ]
    if tracking_data is not None and tracking_summary is not None:
        metrics.extend([
            ("Tracking detections", int(len(tracking_data))),
            ("Distinct observed tracking IDs", int(tracking_data["Tracking ID"].nunique())),
        ])

    summary = pd.DataFrame(metrics, columns=["Metric", "Value"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        frame_data.to_excel(writer, sheet_name="Frame Records", index=False)

        if tracking_data is not None:
            tracking_data.to_excel(writer, sheet_name="Tracking Records", index=False)
        if tracking_summary is not None:
            tracking_summary.to_excel(writer, sheet_name="Tracking ID Summary", index=False)

        widths_by_sheet = {
            "Summary": {"A": 40, "B": 26},
            "Frame Records": {"A": 18, "B": 18, "C": 20},
            "Tracking Records": {
                "A": 16, "B": 20, "C": 16, "D": 12, "E": 12, "F": 12, "G": 12
            },
            "Tracking ID Summary": {
                "A": 16, "B": 16, "C": 16, "D": 20, "E": 16, "F": 16
            },
        }
        for sheet_name, widths in widths_by_sheet.items():
            if sheet_name not in writer.sheets:
                continue
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for col, width in widths.items():
                worksheet.column_dimensions[col].width = width

    output.seek(0)
    return output.getvalue()


# Sidebar: source files
st.sidebar.header("📂 Report files")
frame_upload = st.sidebar.file_uploader(
    "Upload customer_report.csv", type=["csv"], key="frame_csv"
)
tracking_upload = st.sidebar.file_uploader(
    "Upload customer_tracking_report.csv", type=["csv"], key="tracking_csv"
)
summary_upload = st.sidebar.file_uploader(
    "Optional: upload tracking_id_summary.csv", type=["csv"], key="summary_csv"
)
st.sidebar.markdown("---")
st.sidebar.caption("Default local files are read from the output/ folder.")
st.sidebar.caption("The original main.py is not modified by this dashboard.")

# Load frame-count report
if frame_upload is not None:
    raw_data = load_csv(frame_upload)
    source_label = frame_upload.name
elif DEFAULT_CSV.exists():
    raw_data = load_csv(DEFAULT_CSV)
    source_label = str(DEFAULT_CSV)
else:
    raw_data = None
    source_label = None

if raw_data is not None:
    data = validate_data(raw_data)
    st.caption(f"Customer-count source: `{source_label}` • {len(data):,} valid frame records")

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
        "Customer Count is the number of people detected in each frame, not a count "
        "of unique customers. In the original script, Time records computer processing "
        "time rather than the video's exact timestamp."
    )

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Customer count by frame")
        st.line_chart(data.set_index("Frame Number")[["Customer Count"]], height=340)
        st.caption(f"Peak detected count: {max_count} people at frame {peak_frame}.")
    with right:
        st.subheader("Count distribution")
        distribution = (
            data["Customer Count"].value_counts().sort_index()
            .rename_axis("Detected people").to_frame("Frames")
        )
        st.bar_chart(distribution, height=340)

    st.subheader("Frame records")
    min_frame = int(data["Frame Number"].min())
    max_frame = int(data["Frame Number"].max())
    if min_frame == max_frame:
        frame_range = (min_frame, max_frame)
        st.caption(f"Frame filter: {min_frame}")
    else:
        frame_range = st.slider(
            "Filter by frame number",
            min_value=min_frame,
            max_value=max_frame,
            value=(min_frame, max_frame),
            key="frame_range",
        )
    filtered = data[data["Frame Number"].between(frame_range[0], frame_range[1])]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    download_col1, download_col2 = st.columns(2)
    with download_col1:
        st.download_button(
            label="⬇️ Download filtered CSV report",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="customer_report_filtered.csv",
            mime="text/csv",
            key="download_frame_csv",
        )
else:
    filtered = None
    st.warning("Customer-count CSV not found.")
    st.write(
        "Upload `customer_report.csv` using the sidebar, or run the original project "
        "and place the report at `output/customer_report.csv`."
    )

# Load tracking report
if tracking_upload is not None:
    raw_tracking = load_csv(tracking_upload)
    tracking_source = tracking_upload.name
elif DEFAULT_TRACKING_CSV.exists():
    raw_tracking = load_csv(DEFAULT_TRACKING_CSV)
    tracking_source = str(DEFAULT_TRACKING_CSV)
else:
    raw_tracking = None
    tracking_source = None

tracking_data = None
tracking_summary = None
if raw_tracking is not None:
    tracking_data = validate_tracking_data(raw_tracking)
    st.markdown("---")
    st.header("🧭 Customer Tracking Analytics")
    st.caption(
        f"Tracking source: `{tracking_source}` • {len(tracking_data):,} detection records"
    )

    generated_summary = make_tracking_summary(tracking_data)
    if summary_upload is not None:
        uploaded_summary = load_csv(summary_upload)
        missing = [c for c in SUMMARY_COLUMNS if c not in uploaded_summary.columns]
        if missing:
            st.warning(
                "Uploaded tracking summary is missing column(s): "
                + ", ".join(missing)
                + ". A summary will be calculated from the tracking report instead."
            )
            tracking_summary = generated_summary
        else:
            tracking_summary = uploaded_summary[SUMMARY_COLUMNS].copy()
            for col in SUMMARY_COLUMNS:
                tracking_summary[col] = pd.to_numeric(tracking_summary[col], errors="coerce")
            tracking_summary = tracking_summary.dropna(subset=["Tracking ID"])
            tracking_summary = tracking_summary.sort_values(
                ["Frames_Observed", "Detections"], ascending=False
            )
    elif DEFAULT_SUMMARY_CSV.exists():
        disk_summary = load_csv(DEFAULT_SUMMARY_CSV)
        if all(c in disk_summary.columns for c in SUMMARY_COLUMNS):
            tracking_summary = disk_summary[SUMMARY_COLUMNS].copy()
            tracking_summary = tracking_summary.sort_values(
                ["Frames_Observed", "Detections"], ascending=False
            )
        else:
            tracking_summary = generated_summary
    else:
        tracking_summary = generated_summary

    t1, t2, t3 = st.columns(3)
    t1.metric("Tracking detections", f"{len(tracking_data):,}")
    t2.metric("Distinct observed Tracking IDs", f"{tracking_data['Tracking ID'].nunique():,}")
    t3.metric(
        "Max frames observed for one ID",
        f"{int(tracking_summary['Frames_Observed'].max()):,}"
        if not tracking_summary.empty else "0",
    )

    st.warning(
        "Tracking IDs are temporary tracker labels, not verified real-world identities. "
        "An ID may change, be lost during occlusion, or be reassigned. Frames observed "
        "are not exact dwell time or proof of a unique person."
    )

    chart_col, table_col = st.columns([1, 1])
    with chart_col:
        st.subheader("Top Tracking IDs by frames observed")
        top_n = min(20, len(tracking_summary))
        if top_n:
            top_ids = tracking_summary.head(top_n).copy()
            chart_data = top_ids.set_index("Tracking ID")[["Frames_Observed"]]
            st.bar_chart(chart_data, height=380)
        else:
            st.info("No tracking summary rows available.")
    with table_col:
        st.subheader("Tracking ID summary")
        st.dataframe(
            tracking_summary.head(100),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Showing up to 100 IDs, ordered by frames observed.")

    st.subheader("Tracking detection records")
    tracking_min = int(tracking_data["Frame Number"].min())
    tracking_max = int(tracking_data["Frame Number"].max())
    if tracking_min == tracking_max:
        tracking_range = (tracking_min, tracking_max)
        st.caption(f"Tracking frame filter: {tracking_min}")
    else:
        tracking_range = st.slider(
            "Filter tracking records by frame",
            min_value=tracking_min,
            max_value=tracking_max,
            value=(tracking_min, tracking_max),
            key="tracking_range",
        )
    filtered_tracking = tracking_data[
        tracking_data["Frame Number"].between(tracking_range[0], tracking_range[1])
    ]
    st.dataframe(
        filtered_tracking,
        use_container_width=True,
        hide_index=True,
    )

    tc1, tc2 = st.columns(2)
    with tc1:
        st.download_button(
            "⬇️ Download tracking records CSV",
            data=filtered_tracking.to_csv(index=False).encode("utf-8"),
            file_name="customer_tracking_records_filtered.csv",
            mime="text/csv",
            key="download_tracking_csv",
        )
    with tc2:
        st.download_button(
            "⬇️ Download Tracking ID summary CSV",
            data=tracking_summary.to_csv(index=False).encode("utf-8"),
            file_name="tracking_id_summary.csv",
            mime="text/csv",
            key="download_tracking_summary_csv",
        )

    if filtered is not None:
        with st.container():
            st.download_button(
                "📊 Download combined Excel report (.xlsx)",
                data=make_excel_report(filtered, filtered_tracking, tracking_summary),
                file_name="customer_behavior_tracking_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_combined_excel",
            )
else:
    st.markdown("---")
    st.header("🧭 Customer Tracking Analytics")
    st.info(
        "Tracking report not found. Upload `customer_tracking_report.csv` in the sidebar "
        "or place it at `output/customer_tracking_report.csv` to enable tracking analytics."
    )

    if filtered is not None:
        st.download_button(
            "📊 Download Excel report (.xlsx)",
            data=make_excel_report(filtered),
            file_name="customer_behavior_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_basic",
        )

st.caption(
    "Privacy note: analyse only footage you are permitted to use. Follow applicable "
    "privacy rules and the video owner's licence/terms."
)
