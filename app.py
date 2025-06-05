import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

# Funnel stages in order
stages = ["Expression of Interest", "Conversations", "Deep Conversations", "Proposals", "Wins"]

# Define colors per stage
color_map = {
    "Expression of Interest": "#1f77b4",
    "Conversations": "#ff7f0e",
    "Deep Conversations": "#2ca02c",
    "Proposals": "#d62728",
    "Wins": "#9467bd"
}

def create_funnel_plan(duration='weekly', total_periods=26, target_wins=4, conversion_rate=0.5):
    final_counts = {}
    multiplier = 1
    for stage in reversed(stages):
        final_counts[stage] = target_wins * multiplier
        multiplier /= conversion_rate
    final_counts = {stage: int(round(val)) for stage, val in final_counts.items()}

    time_label = 'Week' if duration == 'weekly' else 'Day'
    time = np.arange(total_periods)
    data = {time_label: time}
    for stage in stages:
        data[stage] = np.linspace(0, final_counts[stage], total_periods)

    df = pd.DataFrame(data)
    return df, time_label

def plot_funnel_comparison(df, time_label, actual_df=None):
    fig = go.Figure()
    for stage in stages:
        color = color_map[stage]
        fig.add_trace(go.Scatter(
            x=df[time_label], y=df[stage],
            mode='lines', name=f"Planned - {stage}",
            line=dict(color=color, dash='dash', width=3),
            hoverinfo='x+y'
        ))
        if actual_df is not None and stage in actual_df.columns:
            fig.add_trace(go.Scatter(
                x=actual_df[time_label], y=actual_df[stage],
                mode='lines+markers', name=f"Actual - {stage}",
                line=dict(color=color, dash='solid', width=4),
                marker=dict(size=8, symbol='circle-open'),
                hoverinfo='x+y'
            ))
    fig.update_layout(
        title=dict(text="Planned vs Actual Sales Funnel", x=0.5, font=dict(size=24)),
        xaxis_title=time_label,
        yaxis_title="Leads",
        hovermode="x unified",
        template="plotly_white",
        height=600,
        margin=dict(l=70, r=70, t=100, b=70),
        legend=dict(orientation='h', y=1.1, x=0.01),
    )
    return fig

# --- Streamlit App ---

st.set_page_config(layout="wide")
st.title("Sales Funnel Planning Dashboard")

with st.sidebar:
    st.header("Configuration")
    duration = st.selectbox("Time Interval", options=["weekly", "daily"])
    total_periods = st.slider("Number of Periods", min_value=4, max_value=180, value=26)
    target_wins = st.slider("Target Wins", min_value=1, max_value=20, value=4)
    conversion_rate = st.slider("Stage Conversion Rate", min_value=0.1, max_value=1.0, value=0.5, step=0.05)

st.subheader("Enter Actual Data Points")

num_points = st.number_input("Number of Actual Data Points", min_value=0, max_value=20, value=1, step=1)

actual_data = []
for i in range(num_points):
    with st.expander(f"Actual Data Point #{i + 1}", expanded=True):
        t = st.slider(f"Period for Point #{i + 1}", min_value=0, max_value=total_periods - 1, value=0, key=f"t_{i}")
        stage_values = {}
        cols = st.columns(2)
        for j, stage in enumerate(stages):
            with cols[j % 2]:
                val = st.number_input(f"{stage} (Point #{i + 1})", min_value=0, value=0, step=1, key=f"{stage}_{i}")
                stage_values[stage] = val
        actual_data.append((t, stage_values))

# Generate planned data
planned_df, time_label = create_funnel_plan(duration, total_periods, target_wins, conversion_rate)

# Build actual dataframe
actual_df = pd.DataFrame({time_label: planned_df[time_label]})
for stage in stages:
    actual_df[stage] = 0  # Start all actuals at 0

# Apply each actual data point
for t, values in actual_data:
    for stage in stages:
        val = values[stage]
        linear_vals = np.linspace(0, val, t + 1) if t > 0 else [val]
        actual_df.loc[actual_df[time_label] <= t, stage] = linear_vals
        actual_df.loc[actual_df[time_label] > t, stage] = val

# Plotting
st.plotly_chart(plot_funnel_comparison(planned_df, time_label, actual_df), use_container_width=True)

# Table
st.subheader("Tabular View of Planned vs Actual")
combined = pd.DataFrame({time_label: planned_df[time_label]})
for stage in stages:
    combined[f"Planned - {stage}"] = planned_df[stage].round(1)
    combined[f"Actual - {stage}"] = actual_df[stage].round(1)
st.dataframe(combined.style.format(precision=1), use_container_width=True)
