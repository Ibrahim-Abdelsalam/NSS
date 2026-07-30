"""Results display and visualization for the NSS Streamlit app."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def _render_summary_metrics(results: Dict[str, Any], model_params: Dict[str, Any], nurses_list: List[str], scenarios_df: Optional[pd.DataFrame]) -> None:
    """Render the top-level summary metrics."""
    st.header("📊 Summary Metrics")

    if scenarios_df is not None:
        total_demand = scenarios_df["demand"].sum()
        num_scenarios = len(scenarios_df["scenario"].unique())
        avg_demand_per_scenario = total_demand / num_scenarios if num_scenarios else 0
    else:
        avg_demand_per_scenario = 0

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        total_cost = results.get('cost_breakdown', {}).get('total_cost', 0)
        st.metric(
            "Total Cost",
            f"${total_cost:,.0f}",
            help="Total optimization cost inclusive of regular, overtime, and expected recourse costs.",
        )
    with col2:
        st.metric(
            "Expected Shortage",
            f"{results.get('expected_shortage', 0):.1f} nurses",
            help="Average understaffing across all scenarios.",
        )

    if results.get("fatigue_metrics", {}).get("enabled"):
        st.write("---")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.metric("Average Fatigue", f"{results['fatigue_metrics'].get('avg_fatigue', 0):.2f}")
        with f_col2:
            st.metric("Peak Fatigue", f"{results['fatigue_metrics'].get('max_fatigue', 0):.2f}")

    st.divider()


def _render_roster_tab(results: Dict[str, Any], model_params: Dict[str, Any]) -> None:
    """Render the roster tab."""
    st.header("👥 Nurse Work Schedule")
    roster_df = results["roster_df"]

    col1, col2 = st.columns([3, 1])
    with col2:
        show_summary = st.checkbox("Show Summary Columns", value=True)

    styler = roster_df.style
    start_date_str = model_params.get("start_date")
    weekend_cols = []
    complete_weekends = []

    def highlight_off_weekends(row):
        styles = pd.Series("", index=row.index)
        for sat_col, sun_col in complete_weekends:
            if sat_col in row.index and sun_col in row.index:
                if row[sat_col] == "OFF" and row[sun_col] == "OFF":
                    styles[sat_col] = "background-color: #fff8c4"
                    styles[sun_col] = "background-color: #fff8c4"
        return styles

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            day_cols = [col for col in roster_df.columns if col.startswith("D") and col[1:].isdigit()]
            day_nums_sorted = sorted([int(col[1:]) for col in day_cols])

            for day_num in day_nums_sorted:
                current_date = start_date + timedelta(days=day_num - 1)
                if current_date.weekday() >= 5:
                    weekend_cols.append(f"D{day_num}")

            for i in range(len(day_nums_sorted) - 1):
                day1_num, day2_num = day_nums_sorted[i], day_nums_sorted[i + 1]
                date1 = start_date + timedelta(days=day1_num - 1)
                date2 = start_date + timedelta(days=day2_num - 1)
                if date1.weekday() == 5 and date2.weekday() == 6 and (day2_num - day1_num == 1):
                    complete_weekends.append((f"D{day1_num}", f"D{day2_num}"))

            if weekend_cols:
                styler = styler.set_properties(subset=weekend_cols, **{"background-color": "#f5f3ff", "font-weight": "bold"})

            if complete_weekends:
                styler = styler.apply(highlight_off_weekends, axis=1)
        except Exception as e:
            st.warning(f"Could not highlight weekends: {e}")

    if show_summary:
        st.dataframe(styler, use_container_width=True, height=400)
    else:
        day_cols = [col for col in roster_df.columns if col.startswith("D") and col[1:].isdigit()]
        display_df = roster_df[["Nurse"] + day_cols].copy()
        st.dataframe(display_df.style, use_container_width=True, height=400)

    csv_roster = roster_df.to_csv(index=False)
    st.download_button("⬇️ Download Roster (CSV)", csv_roster, "nurse_roster.csv", "text/csv")

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=12,
            alignment=1,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#667eea"),
            spaceAfter=6,
            spaceBefore=12,
        )

        story.append(Paragraph("NURSE ROSTER REPORT", title_style))
        story.append(Paragraph(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("COMPLETE NURSE ROSTER", heading_style))

        day_cols = [col for col in roster_df.columns if col.startswith("D")]
        schedule_cols = ["Nurse"] + day_cols
        schedule_view = roster_df[schedule_cols]
        schedule_data = [schedule_view.columns.tolist()]
        for _, row in schedule_view.iterrows():
            schedule_data.append(row.tolist())

        num_sched_cols = len(schedule_cols)
        available_width = 7.5 * inch
        nurse_col_width = 1.0 * inch
        day_col_width = (available_width - nurse_col_width) / (num_sched_cols - 1)
        sched_col_widths = [nurse_col_width] + [day_col_width] * (num_sched_cols - 1)

        roster_table = Table(schedule_data, colWidths=sched_col_widths, repeatRows=1)
        roster_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#667eea")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 6),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("FONTSIZE", (0, 1), (-1, -1), 5),
                    ("ALIGN", (0, 1), (0, -1), "LEFT"),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                ]
            )
        )
        story.append(roster_table)
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("WORKLOAD SUMMARY", heading_style))
        summary_cols = ["Nurse", "Total_Regular", "Total_Overtime", "Total_Nights", "Total_Shifts"]
        summary_view = roster_df[summary_cols]
        summary_data = [summary_view.columns.tolist()] + [row.tolist() for _, row in summary_view.iterrows()]
        summary_col_widths = [1.5 * inch] + [1.2 * inch] * (len(summary_cols) - 1)
        metrics_table = Table(summary_data, colWidths=summary_col_widths, repeatRows=1)
        metrics_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a5568")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("ALIGN", (0, 1), (0, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
                ]
            )
        )
        story.append(metrics_table)
        story.append(PageBreak())
        doc.build(story)

        st.download_button(
            "⬇️ Download Roster Report (PDF)",
            pdf_buffer.getvalue(),
            "nurse_roster_report.pdf",
            "application/pdf",
            use_container_width=True,
        )
    except (ValueError, ImportError):
        st.write("")


def _render_heatmap(roster_df: pd.DataFrame, nurses_list: List[str]) -> None:
    """Render the shift distribution heatmap."""
    st.subheader("📊 Shift Distribution Heatmap")
    day_cols = [col for col in roster_df.columns if col.startswith("D") and col[1:].isdigit()]
    heatmap_data = roster_df[["Nurse"] + day_cols].set_index("Nurse")

    shift_names = {
        "OFF": "OFF",
        "E": "Early",
        "D": "Day",
        "L": "Late",
        "N": "Night",
        "E (OT)": "E OT",
        "D (OT)": "D OT",
        "L (OT)": "L OT",
        "N (OT)": "N OT",
    }
    heatmap_display = heatmap_data.replace(shift_names)

    color_mode = st.selectbox(
        "Heatmap color mode",
        ["Categorical", "Discrete"],
        key="heatmap_color_mode",
    )

    shift_map = {"OFF": 0, "E": 1, "D": 2, "L": 3, "N": 4, "E (OT)": 5, "D (OT)": 6, "L (OT)": 7, "N (OT)": 8}
    cat_map = {"OFF": 0, "Early": 1, "Day": 2, "Late": 3, "Night": 4, "E OT": 5, "D OT": 6, "L OT": 7, "N OT": 8}

    if color_mode == "Categorical":
        heatmap_numeric = heatmap_data.replace(shift_map)
        fig_heatmap = px.imshow(
            heatmap_numeric,
            labels=dict(x="Day", y="Nurse", color="Shift"),
            x=day_cols,
            y=heatmap_data.index,
            aspect="auto",
            title="Nurse Schedule - Color-Coded Heatmap",
        )
    else:
        heatmap_numeric = heatmap_data.replace(cat_map)
        fig_heatmap = px.imshow(
            heatmap_numeric,
            labels=dict(x="Day", y="Nurse", color="Shift"),
            x=day_cols,
            y=heatmap_data.index,
            aspect="auto",
            title="Nurse Schedule - Color-Coded Heatmap (Discrete)",
        )

    heatmap_x_axis = day_cols
    heatmap_y_axis = list(heatmap_data.index)
    for nurse_idx, nurse_name in enumerate(heatmap_y_axis):
        nurse_row = roster_df[roster_df["Nurse"] == nurse_name].iloc[0]
        for i in range(len(heatmap_x_axis) - 1):
            sat_col, sun_col = heatmap_x_axis[i], heatmap_x_axis[i + 1]
            try:
                if nurse_row[sat_col] == "OFF" and nurse_row[sun_col] == "OFF":
                    sat_x_idx = heatmap_x_axis.index(sat_col)
                    fig_heatmap.add_shape(
                        type="rect",
                        x0=sat_x_idx - 0.5,
                        x1=sat_x_idx + 0.5,
                        y0=nurse_idx - 0.5,
                        y1=nurse_idx + 0.5,
                        line=dict(width=0),
                        fillcolor="rgba(255, 248, 196, 0.35)",
                    )
            except Exception:
                pass

    fig_heatmap.update_traces(customdata=heatmap_display.values)
    fig_heatmap.update_layout(height=max(600, len(nurses_list or []) * 25))
    st.plotly_chart(fig_heatmap, use_container_width=True)

    try:
        img_bytes = fig_heatmap.to_image(format="png", width=1400, height=max(600, len(nurses_list or []) * 25))
        st.download_button(
            "⬇️ Download Heatmap (PNG Image)",
            img_bytes,
            "nurse_schedule_heatmap.png",
            "image/png",
        )
    except Exception:
        st.write("")


def _render_cost_tab(results: Dict[str, Any], model_params: Dict[str, Any]) -> None:
    """Render the cost analysis tab."""
    st.header("💵 Detailed Cost Breakdown")
    cost = results["cost_breakdown"]
    total_overtime = cost["total_overtime_shifts"]
    total_emergency = sum(results["scenario_df"]["shortage_shifts"])

    if total_emergency > 0 and total_overtime == 0:
        num_nurses = len(results.get("roster_df", []))
        baseline_demand = cost.get("total_regular_shifts", 0)
        max_regular = num_nurses * model_params.get("n1", 15)
        if baseline_demand < max_regular * 0.8:
            st.info("No overtime needed - regular shifts sufficient")
        else:
            st.warning("No overtime used, all extra demand handled by emergency staff!")
    elif total_overtime > 0 and total_emergency > 0:
        overtime_pct = total_overtime / (total_overtime + total_emergency) * 100
        st.info(f"Mix of overtime and emergency staff used: {overtime_pct:.1f}% overtime")
    elif total_overtime > 0:
        st.success("Overtime effectively utilized!")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stage 1: Baseline Costs")
        st.metric("Regular Shift Costs", f"${cost['stage1_regular_cost']:,.0f}")
        st.metric("Overtime Shift Costs", f"${cost['stage1_overtime_cost']:,.0f}")
        st.metric("Stage 1 Total", f"${cost['stage1_total']:,.0f}")
    with col2:
        st.subheader("Stage 2: Recourse Costs")
        st.metric("Expected Recourse Cost", f"${cost['stage2_expected_cost']:,.0f}")
        st.metric("Cost per Nurse", f"${cost['avg_cost_per_nurse']:,.0f}")
        st.metric("Grand Total", f"${cost['total_cost']:,.0f}")

    st.subheader("📊 Cost Distribution")
    cost_data = pd.DataFrame(
        {
            "Category": ["Regular Wages", "Overtime Wages", "Emergency Recourse"],
            "Amount": [cost["stage1_regular_cost"], cost["stage1_overtime_cost"], cost["stage2_expected_cost"]],
        }
    )
    fig_pie = px.pie(cost_data, values="Amount", names="Category", title="Cost Distribution", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📈 Shift Allocation")
    scenario_df = results["scenario_df"]
    avg_emergency = scenario_df["shortage_shifts"].mean() if not scenario_df.empty else 0
    shift_data = pd.DataFrame(
        {
            "Category": ["Regular", "Overtime", "Emergency (Avg)"],
            "Count": [cost["total_regular_shifts"], cost["total_overtime_shifts"], avg_emergency],
            "Color": ["#6366F1", "#818CF8", "#EF4444"],
        }
    )
    fig_bar = px.bar(
        shift_data,
        y="Category",
        x="Count",
        orientation="h",
        text="Count",
        color="Category",
        color_discrete_map={"Regular": "#6366F1", "Overtime": "#A5B4FC", "Emergency (Avg)": "#F87171"},
        template="plotly_white",
    )
    fig_bar.update_traces(texttemplate="<b>%{text:.1f}</b> Shifts", textposition="outside", hovertemplate="<b>%{y}</b><br>Count: %{x:.1f} shifts<extra></extra>", marker_line_width=0, width=0.6)
    fig_bar.update_layout(
        title={"text": "<b>Staffing Mix Distribution</b>", "y": 0.95, "x": 0.5, "xanchor": "center", "yanchor": "top", "font": {"size": 20, "color": "#1E293B"}},
        bargap=0.15,
        height=350,
        showlegend=False,
        xaxis_visible=False,
        yaxis_title="",
        yaxis_autorange="reversed",
        margin=dict(l=20, r=80, t=60, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=14, color="#475569"),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})


def _render_coverage_tab(results: Dict[str, Any]) -> None:
    """Render the coverage analysis tab."""
    st.header("📊 Daily Coverage Analysis")
    coverage_df = results["coverage_df"]
    fig_coverage = px.bar(coverage_df, x="day", y="assigned_nurses", color="shift", title="Assigned Nurses by Day and Shift", labels={"assigned_nurses": "Number of Nurses", "day": "Day"}, barmode="group")
    st.plotly_chart(fig_coverage, use_container_width=True)
    st.subheader("📋 Coverage Details")
    coverage_pivot = coverage_df.pivot(index="shift", columns="day", values="assigned_nurses")
    st.dataframe(coverage_pivot, use_container_width=True)


def _render_risk_tab(results: Dict[str, Any]) -> None:
    """Render the risk assessment tab."""
    st.header("⚠️ Risk Metrics & Analysis")
    risk = results["risk_metrics"]
    scenario_df = results["scenario_df"]
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Model Configuration")
        st.info(f"**Model Type:** {risk['model_type']}")
        st.info(f"**Scenarios Analyzed:** {risk['num_scenarios']}")
        if risk["model_type"] == "SDM-CVaR":
            st.success(f"**Confidence Level (σ):** {risk['confidence_level']:.1%}")
            st.success(f"**CVaR Limit (μ):** {risk['cvar_limit']:.2f} shifts")
            st.success(f"**Actual VaR (ξ):** {risk.get('var_value', 0):.2f} shifts")
    with col2:
        st.subheader("Shortage Statistics")
        st.metric("Mean Shortage", f"{scenario_df['shortage_shifts'].mean():.2f}")
        st.metric("Max Shortage", f"{scenario_df['shortage_shifts'].max():.0f}")
        st.metric("Std Dev", f"{scenario_df['shortage_shifts'].std():.2f}")
    st.subheader("📊 Shortage Distribution")
    fig_dist = px.histogram(scenario_df, x="shortage_shifts", nbins=20, title="Distribution of Shortages Across Scenarios", labels={"shortage_shifts": "Shortage (shifts)"}, marginal="box")
    st.plotly_chart(fig_dist, use_container_width=True)


def _render_scenario_tab(results: Dict[str, Any]) -> None:
    """Render the scenario comparison tab."""
    st.header("🔬 Scenario-by-Scenario Analysis")
    scenario_df = results["scenario_df"]
    fig_scenarios = go.Figure()
    fig_scenarios.add_trace(go.Bar(name="Shortage", x=scenario_df["scenario"], y=scenario_df["shortage_shifts"], marker_color="indianred"))
    fig_scenarios.add_trace(go.Bar(name="Overage", x=scenario_df["scenario"], y=scenario_df["overage_shifts"], marker_color="lightseagreen"))
    fig_scenarios.update_layout(title="Shortage vs Overage by Scenario", xaxis_title="Scenario", yaxis_title="Number of Shifts", barmode="group")
    st.plotly_chart(fig_scenarios, use_container_width=True)
    st.subheader("📋 Detailed Scenario Results")
    st.dataframe(scenario_df, use_container_width=True)
    csv_scenarios = scenario_df.to_csv(index=False)
    st.download_button("⬇️ Download Scenario Analysis (CSV)", csv_scenarios, "scenario_analysis.csv", "text/csv")


def _render_report_tab(results: Dict[str, Any], nurses_list: List[str]) -> None:
    """Render the comprehensive report tab."""
    st.header("📄 Comprehensive Report")
    st.markdown(
        f"""
        ## Executive Summary

        **Optimization Model:** {results['risk_metrics']['model_type']}  
        **Total Nurses:** {len(nurses_list) if nurses_list else 0}  
        **Planning Period:** {len(results['coverage_df']['day'].unique())} days  
        **Demand Scenarios:** {results['risk_metrics']['num_scenarios']}

        ---

        ### Financial Summary

        - **Total Cost:** ${results['cost_breakdown']['total_cost']:,.2f}
        - **Stage 1 (Baseline):** ${results['cost_breakdown']['stage1_total']:,.2f}
          - Regular Shifts: ${results['cost_breakdown']['stage1_regular_cost']:,.2f}
          - Overtime Shifts: ${results['cost_breakdown']['stage1_overtime_cost']:,.2f}
        - **Stage 2 (Expected Recourse):** ${results['cost_breakdown']['stage2_expected_cost']:,.2f}
        - **Average Cost per Nurse:** ${results['cost_breakdown']['avg_cost_per_nurse']:,.2f}

        ---

        ### Staffing Summary

        - **Total Regular Shifts:** {int(results['cost_breakdown']['total_regular_shifts'])}
        - **Total Overtime Shifts:** {int(results['cost_breakdown']['total_overtime_shifts'])}
        - **Total Shifts:** {int(results['cost_breakdown']['total_regular_shifts'] + results['cost_breakdown']['total_overtime_shifts'])}

        ---

        ### Risk Summary

        - **Average Shortage:** {results['scenario_df']['shortage_shifts'].mean():.2f} shifts
        - **Maximum Shortage:** {results['scenario_df']['shortage_shifts'].max():.0f} shifts
        - **Shortage Std Dev:** {results['scenario_df']['shortage_shifts'].std():.2f}
        """
    )

    if results["risk_metrics"]["model_type"] == "SDM-CVaR":
        st.markdown(
            f"""
            ### CVaR Risk Metrics

            - **Confidence Level (σ):** {results['risk_metrics']['confidence_level']:.1%}
            - **Target CVaR Limit (μ):** {results['risk_metrics']['cvar_limit']:.2f} shifts
            - **Actual VaR (ξ):** {results['risk_metrics'].get('var_value', 0):.2f} shifts

            The model successfully controlled the worst-case shortage risk.
            """
        )

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=0.5 * inch, leftMargin=0.5 * inch, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#1a1a2e"), spaceAfter=12, alignment=1)
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#667eea"), spaceAfter=6, spaceBefore=12)

    story.append(Paragraph("NURSE SCHEDULING OPTIMIZATION REPORT", title_style))
    story.append(Paragraph(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))

    summary_data = [["Model Type:", results['risk_metrics']['model_type']], ["Total Nurses:", str(len(nurses_list) if nurses_list else 0)], ["Planning Period:", f"{len(results['coverage_df']['day'].unique())} days"], ["Demand Scenarios:", str(results['risk_metrics']['num_scenarios'])]]
    summary_table = Table(summary_data, colWidths=[2 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')), ('TEXTCOLOR', (0, 0), (-1, -1), colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(summary_table)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("FINANCIAL SUMMARY", heading_style))

    financial_data = [["Total Cost:", f"${results['cost_breakdown']['total_cost']:,.2f}"], ["Stage 1 Cost:", f"${results['cost_breakdown']['stage1_total']:,.2f}"], ["  Regular Wages:", f"${results['cost_breakdown']['stage1_regular_cost']:,.2f}"], ["  Overtime Wages:", f"${results['cost_breakdown']['stage1_overtime_cost']:,.2f}"], ["Stage 2 Recourse:", f"${results['cost_breakdown']['stage2_expected_cost']:,.2f}"], ["Cost per Nurse:", f"${results['cost_breakdown']['avg_cost_per_nurse']:,.2f}"]]
    financial_table = Table(financial_data, colWidths=[2 * inch, 2.5 * inch])
    financial_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#667eea')), ('TEXTCOLOR', (0, 0), (0, 0), colors.white), ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e6f2ff')), ('TEXTCOLOR', (0, 1), (-1, -1), colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'), ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(financial_table)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("STAFFING SUMMARY", heading_style))
    staffing_data = [["Regular Shifts:", str(int(results['cost_breakdown']['total_regular_shifts']))], ["Overtime Shifts:", str(int(results['cost_breakdown']['total_overtime_shifts']))], ["Total Shifts:", str(int(results['cost_breakdown']['total_regular_shifts'] + results['cost_breakdown']['total_overtime_shifts']))]]
    staffing_table = Table(staffing_data, colWidths=[2 * inch, 2.5 * inch])
    staffing_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')), ('TEXTCOLOR', (0, 0), (-1, -1), colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(staffing_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("RISK SUMMARY", heading_style))
    risk_data = [["Average Shortage:", f"{results['scenario_df']['shortage_shifts'].mean():.2f} shifts"], ["Maximum Shortage:", f"{results['scenario_df']['shortage_shifts'].max():.0f} shifts"], ["Std Deviation:", f"{results['scenario_df']['shortage_shifts'].std():.2f}"]]
    risk_table = Table(risk_data, colWidths=[2 * inch, 2.5 * inch])
    risk_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')), ('TEXTCOLOR', (0, 0), (-1, -1), colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(risk_table)
    story.append(PageBreak())

    story.append(Paragraph("COMPLETE NURSE ROSTER", heading_style))
    roster_df = results['roster_df']
    day_cols = [col for col in roster_df.columns if col.startswith("D")]
    schedule_cols = ['Nurse'] + day_cols
    schedule_view = roster_df[schedule_cols]
    schedule_data = [schedule_view.columns.tolist()] + [row.tolist() for _, row in schedule_view.iterrows()]
    num_sched_cols = len(schedule_cols)
    available_width = 7.5 * inch
    nurse_col_width = 1.0 * inch
    day_col_width = (available_width - nurse_col_width) / (num_sched_cols - 1)
    sched_col_widths = [nurse_col_width] + [day_col_width] * (num_sched_cols - 1)
    roster_table = Table(schedule_data, colWidths=sched_col_widths, repeatRows=1)
    roster_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 6), ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('FONTSIZE', (0, 1), (-1, -1), 5), ('ALIGN', (0, 1), (0, -1), 'LEFT'), ('ALIGN', (1, 1), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])]))
    story.append(roster_table)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("WORKLOAD SUMMARY", heading_style))
    summary_cols = ['Nurse', 'Total_Regular', 'Total_Overtime', 'Total_Nights', 'Total_Shifts']
    summary_view = roster_df[summary_cols]
    summary_data_list = [summary_view.columns.tolist()] + [row.tolist() for _, row in summary_view.iterrows()]
    summary_col_widths = [1.5 * inch] + [1.2 * inch] * (len(summary_cols) - 1)
    metrics_table = Table(summary_data_list, colWidths=summary_col_widths, repeatRows=1)
    metrics_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 8), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTSIZE', (0, 1), (-1, -1), 8), ('ALIGN', (0, 1), (0, -1), 'LEFT'), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')])]))
    story.append(metrics_table)
    story.append(PageBreak())

    story.append(Paragraph("COVERAGE ANALYSIS BY DAY AND SHIFT", heading_style))
    coverage_df = results['coverage_df']
    coverage_pivot = coverage_df.pivot(index='day', columns='shift', values='assigned_nurses').reset_index()
    coverage_data = [coverage_pivot.columns.tolist()] + [row.tolist() for _, row in coverage_pivot.iterrows()]
    coverage_col_widths = [0.8 * inch] + [1.2 * inch] * (len(coverage_pivot.columns) - 1)
    coverage_table = Table(coverage_data, colWidths=coverage_col_widths, repeatRows=1)
    coverage_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 8), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTSIZE', (0, 1), (-1, -1), 7), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])]))
    story.append(coverage_table)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("SCENARIO-BY-SCENARIO ANALYSIS", heading_style))
    scenario_df = results['scenario_df']
    scenario_data = [['Scenario', 'Shortage Shifts', 'Overage Shifts', 'Recourse Cost']]
    for _, row in scenario_df.iterrows():
        scenario_data.append([str(row['scenario']), f"{row['shortage_shifts']:.2f}", f"{row['overage_shifts']:.2f}", f"${row['recourse_cost']:.2f}"])
    scenario_table = Table(scenario_data, colWidths=[1.2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    scenario_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 8), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTSIZE', (0, 1), (-1, -1), 7), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])]))
    story.append(scenario_table)
    doc.build(story)

    st.download_button("⬇️ Download Complete Report (PDF)", pdf_buffer.getvalue(), "nurse_scheduling_complete_report.pdf", "application/pdf", use_container_width=True)


def render_results(results: Dict[str, Any], model_params: Dict[str, Any], nurses_list: List[str], scenarios_df: Optional[pd.DataFrame]) -> None:
    """Render all result tabs and the welcome screen when no results exist."""
    if results is None:
        st.info(
            """
            ### 👋 Welcome to the Nurse Scheduling Optimization System!

            This application uses advanced **Two-Stage Stochastic Programming** to create optimal nurse schedules
            while managing uncertainty in patient demand.

            #### 🚀 Quick Start:
            1. **Choose your data source** in the left sidebar (Sample Data or Upload)
            2. **Configure cost parameters** and work rules
            3. **Select optimization model** (Cost-focused or Risk-aware)
            4. **Click "RUN OPTIMIZATION"** to generate schedules

            #### 📊 What You'll Get:
            - ✅ Optimal nurse work schedules
            - 💰 Detailed cost breakdowns
            - 📈 Coverage analysis
            - ⚠️ Risk assessments
            - 📄 Downloadable reports

            #### 🎯 Model Types:
            - **SDM (Stochastic Demand Model):** Minimizes total cost
            - **SDM-CVaR:** Minimizes cost while controlling worst-case shortage risk

            ---

            💡 **Tip:** Start with sample data to explore the system's capabilities!
            """
        )
        return

    cost_breakdown = results.get("cost_breakdown", {})
    if not cost_breakdown:
        st.error("🚨 **Optimization Failed to Return Results**")
        st.error(
            "The solver did not find an optimal solution. This could be due to:\n"
            "- **Infeasibility:** The constraints are too strict and demand cannot be met.\n"
            "- **Time Limit Reached:** The solver timed out before finding a feasible solution.\n"
            "- **License Limits:** If using a commercial solver (like Gurobi), the problem may exceed your license limits."
        )
        st.info("Try checking your parameters, increasing the time limit, or selecting the HiGHS solver.")
        return

    _render_summary_metrics(results, model_params, nurses_list, scenarios_df)

    tabs = st.tabs(["📅 Nurse Roster", "💵 Cost Analysis", "📊 Coverage Analysis", "⚠️ Risk Assessment", "🔬 Scenario Comparison", "📄 Full Report"])
    with tabs[0]:
        _render_roster_tab(results, model_params)
        roster_df = results["roster_df"]
        _render_heatmap(roster_df, nurses_list)
    with tabs[1]:
        _render_cost_tab(results, model_params)
    with tabs[2]:
        _render_coverage_tab(results)
    with tabs[3]:
        _render_risk_tab(results)
    with tabs[4]:
        _render_scenario_tab(results)
    with tabs[5]:
        _render_report_tab(results, nurses_list)

    st.divider()
    st.markdown(
        """
        <div class="footer">
            <h2 style="color: #1a1a2e; margin-bottom: 1.5rem; font-size: 2rem;">Nurse Scheduling System</h2>
            <p style="font-size: 1.1rem; margin: 1rem 0; color: #4a5568;">
                <strong>Technology:</strong> Python • PuLP • Streamlit • HiGHS • Plotly
            </p>
            <p style="font-size: 1rem; color: #718096; margin: 1rem 0;">
                Two-Stage Stochastic Programming with CVaR Risk Management
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
