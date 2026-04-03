import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard import api_client

METRICS = ["rpm", "wob", "torque", "mud_flow_rate", "vibration"]
METRIC_LABELS = {
    "rpm": "Rotary Speed (RPM)",
    "wob": "Weight on Bit (klbs)",
    "torque": "Torque (kNm)",
    "mud_flow_rate": "Mud Flow Rate (L/min)",
    "vibration": "Vibration (g)",
}


def render(device_id: str):
    if st.button("← Back to Overview"):
        st.query_params.clear()
        st.rerun()

    try:
        device = api_client.get_device(device_id)
    except Exception:
        st.error("Device not found")
        return

    status_icon = {"online": "🟢", "offline": "⚫", "alert": "🔴"}.get(device["status"], "⚪")
    st.title(f"{status_icon} {device['name']}")
    st.caption(f"{device['device_type']} — {device['location']} — Status: {device['status'].upper()}")

    # Latest reading
    latest = api_client.get_latest_telemetry(device_id)
    if latest:
        st.subheader("Current Readings")
        cols = st.columns(5)
        for i, metric in enumerate(METRICS):
            cols[i].metric(METRIC_LABELS[metric], f"{latest[metric]:.1f}")

    st.divider()

    # Historical charts
    st.subheader("Telemetry History (last 300 readings)")
    try:
        readings = api_client.get_telemetry(device_id, limit=300)
    except Exception:
        st.warning("Failed to load telemetry data")
        readings = []

    if readings:
        df = pd.DataFrame(readings)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        for metric in METRICS:
            fig = px.line(
                df,
                x="timestamp",
                y=metric,
                title=METRIC_LABELS[metric],
                labels={"timestamp": "Time", metric: METRIC_LABELS[metric]},
            )
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No telemetry data yet")

    st.divider()

    # Device alerts
    st.subheader("Device Alerts")
    try:
        alerts = api_client.get_alerts(device_id=device_id, limit=20)
    except Exception:
        st.warning("Failed to load alerts")
        alerts = []

    if not alerts:
        st.success("No alerts for this device")
    else:
        for alert in alerts:
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(
                alert["severity"], "⚪"
            )
            ack_label = " ✓ Acknowledged" if alert["acknowledged"] else ""
            with st.expander(f"{severity_icon} {alert.get('message', alert['metric'])}{ack_label}"):
                st.text(f"Value: {alert['actual_value']:.2f} (threshold: {alert['threshold_value']})")
                st.text(f"Time: {alert['created_at'][:19]}")
                if not alert["acknowledged"]:
                    if st.button("Acknowledge", key=f"ack_{alert['id']}"):
                        try:
                            api_client.acknowledge_alert(alert["id"])
                            st.rerun()
                        except Exception:
                            st.error("Failed to acknowledge")

    # Auto-refresh
    st.markdown("---")
    st.caption("Auto-refreshes every 5 seconds")
    import time
    time.sleep(5)
    st.rerun()
