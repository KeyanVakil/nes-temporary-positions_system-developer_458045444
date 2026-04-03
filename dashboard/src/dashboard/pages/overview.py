import streamlit as st

from dashboard import api_client

STATUS_COLORS = {
    "online": "🟢",
    "offline": "⚫",
    "alert": "🔴",
}


def render():
    st.title("DrillSense — Equipment Monitoring")

    try:
        stats = api_client.get_stats()
    except Exception:
        st.error("Cannot connect to API. Is the backend running?")
        return

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Devices", stats["total_devices"])
    col2.metric("Online", stats["online_devices"])
    col3.metric("Total Readings", f"{stats['total_readings']:,}")
    col4.metric("Active Alerts", stats["active_alerts"])

    st.divider()

    # Device grid
    st.subheader("Devices")
    try:
        devices = api_client.get_devices()
    except Exception:
        st.error("Failed to load devices")
        return

    if not devices:
        st.info("No devices registered yet. Waiting for simulator...")
        return

    cols = st.columns(min(len(devices), 3))
    for i, device in enumerate(devices):
        with cols[i % 3]:
            status_icon = STATUS_COLORS.get(device["status"], "⚪")
            st.markdown(f"### {status_icon} {device['name']}")
            st.caption(f"{device['device_type']} — {device['location']}")
            st.text(f"Status: {device['status'].upper()}")
            if device.get("last_seen_at"):
                st.text(f"Last seen: {device['last_seen_at'][:19]}")
            if st.button("View Details", key=f"dev_{device['id']}"):
                st.query_params["device"] = device["id"]
                st.rerun()

    st.divider()

    # Active alerts
    st.subheader("Active Alerts")
    try:
        alerts = api_client.get_alerts(acknowledged=False, limit=20)
    except Exception:
        st.warning("Failed to load alerts")
        return

    if not alerts:
        st.success("No active alerts")
        return

    for alert in alerts:
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(
            alert["severity"], "⚪"
        )
        with st.expander(f"{severity_icon} [{alert['severity'].upper()}] {alert.get('message', alert['metric'])}", expanded=alert["severity"] in ("critical", "high")):
            st.text(f"Device: {alert['device_id'][:8]}...")
            st.text(f"Metric: {alert['metric']} = {alert['actual_value']:.2f} (threshold: {alert['threshold_value']})")
            st.text(f"Time: {alert['created_at'][:19]}")
            if st.button("Acknowledge", key=f"ack_{alert['id']}"):
                try:
                    api_client.acknowledge_alert(alert["id"])
                    st.rerun()
                except Exception:
                    st.error("Failed to acknowledge alert")

    # Auto-refresh
    st.markdown("---")
    st.caption("Auto-refreshes every 5 seconds")
    import time
    time.sleep(5)
    st.rerun()
