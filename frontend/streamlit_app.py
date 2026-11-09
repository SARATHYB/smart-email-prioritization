# frontend/streamlit_app.py
"""
Smart Personalized Email Prioritization System - Dashboard
Production-grade Streamlit application featuring live TUDS decay curves,
real-time dynamic re-ranking, and priority-tier inbox management.
Pure Python implementation with Plotly (zero brittle binary dependencies).
"""

import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from datetime import datetime
from collections import Counter
import plotly.graph_objects as go
import streamlit as st

from core.models import EmailCategory, PriorityTier, EmailFolder, TUDSParameters
from core.config import settings
from storage.repository import repository
from ingestion.service import ingestion_service
from tuds.decay_curve import generate_decay_curve_data


st.set_page_config(
    page_title="Smart Email Prioritization | TUDS",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Sleek Modern Look
st.markdown("""
<style>
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700;
        color: #3b82f6;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.78rem;
        font-weight: 600;
        border-radius: 9999px;
        margin-right: 0.4rem;
    }
    .badge-urgent { background-color: #ef4444; color: white; }
    .badge-high { background-color: #f59e0b; color: black; }
    .badge-medium { background-color: #3b82f6; color: white; }
    .badge-low { background-color: #6b7280; color: white; }

    .badge-cat {
        background-color: #1e293b;
        color: #93c5fd;
        border: 1px solid #3b82f6;
    }
    .badge-deadline {
        background-color: #312e81;
        color: #c7d2fe;
    }
</style>
""", unsafe_allow_html=True)


def init_demo_state():
    # Automatically seed mock emails if repository is empty
    if not repository.list_emails(limit=1):
        ingestion_service.run_ingestion_cycle(source="mock")


init_demo_state()


# ==============================================================================
# SIDEBAR CONTROLS & TUDS PARAMETER TUNING
# ==============================================================================
with st.sidebar:
    st.markdown("### 📬 Navigation & Settings")
    st.caption(f"Active Account: **{settings.mock_target_email}**")

    nav_selection = st.radio(
        "View Folder",
        ["📥 Priority Inbox", "⭐ Saved Mails", "🗑️ Trash", "📊 Analytics & Insights", "🔬 TUDS Curve Explorer"],
        index=0
    )

    st.divider()

    st.markdown("### ⚙️ TUDS Tuning Engine")
    st.caption("Adjust formula coefficients to see real-time inbox re-ranking.")

    alpha_param = st.slider(
        "Amplification Factor (α)",
        min_value=0.5,
        max_value=3.0,
        value=1.5,
        step=0.1,
        help="Regulates magnitude of urgency surge as deadline nears"
    )

    with st.expander("Category Weights (User Interest I)", expanded=False):
        w_placement = st.slider("Placement", 0.1, 1.0, 1.0, 0.05)
        w_exam = st.slider("Exam", 0.1, 1.0, 0.95, 0.05)
        w_internship = st.slider("Internship", 0.1, 1.0, 0.90, 0.05)
        w_scholarship = st.slider("Scholarship", 0.1, 1.0, 0.85, 0.05)
        w_event = st.slider("Event", 0.1, 1.0, 0.60, 0.05)
        w_general = st.slider("General", 0.1, 1.0, 0.40, 0.05)

    with st.expander("Category Decay Rates (λ)", expanded=False):
        l_placement = st.slider("λ Placement", 0.01, 0.15, 0.06, 0.01)
        l_exam = st.slider("λ Exam", 0.01, 0.15, 0.07, 0.01)
        l_intern = st.slider("λ Internship", 0.01, 0.15, 0.04, 0.01)
        l_schol = st.slider("λ Scholarship", 0.01, 0.15, 0.05, 0.01)

    tuds_params = TUDSParameters(
        alpha=alpha_param,
        user_interest_weights={
            EmailCategory.PLACEMENT: w_placement,
            EmailCategory.EXAM: w_exam,
            EmailCategory.INTERNSHIP: w_internship,
            EmailCategory.SCHOLARSHIP: w_scholarship,
            EmailCategory.EVENT: w_event,
            EmailCategory.GENERAL: w_general,
        },
        category_lambdas={
            EmailCategory.PLACEMENT: l_placement,
            EmailCategory.EXAM: l_exam,
            EmailCategory.INTERNSHIP: l_intern,
            EmailCategory.SCHOLARSHIP: l_schol,
            EmailCategory.EVENT: 0.03,
            EmailCategory.GENERAL: 0.01,
        }
    )

    if st.button("⚡ Recompute & Re-rank Inbox", use_container_width=True, type="primary"):
        ingestion_service.recompute_all_scores(tuds_params)
        st.toast("Scores recomputed dynamically with updated parameters!", icon="✅")
        st.rerun()

    st.divider()

    st.markdown("### 🔄 Ingestion & Demo Controls")
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("📨 Ingest Mocks", use_container_width=True):
            ingestion_service.run_ingestion_cycle(source="mock", params=tuds_params)
            st.toast("New mock emails ingested!", icon="📥")
            st.rerun()
    with c_btn2:
        if st.button("♻️ Reset Demo", use_container_width=True):
            repository.clear_all()
            ingestion_service.run_ingestion_cycle(source="mock", params=tuds_params)
            st.toast("Database reset and re-seeded!", icon="🔄")
            st.rerun()


# ==============================================================================
# MAIN PAGE HEADER & KPI METRICS
# ==============================================================================
st.title("Smart Personalized Email Prioritization System")
st.caption(
    "Mathematical dynamic ranking using **Temporal Urgency Decay Scoring (TUDS)**: "
    r"$\text{Priority}(t) = (R \times I) \times (1 + \alpha e^{-\lambda t})$"
)

stats = repository.get_stats()
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Inbox Volume", stats["total_inbox"], help="Total active emails in prioritized inbox")
kpi2.metric("Urgent Deadlines 🔥", stats["urgent_count"], help="Emails closing within 24 hours or TUDS >= 0.75")
kpi3.metric("Saved Bookmarks ⭐", stats["total_saved"], help="Critical emails pinned by user")
kpi4.metric("Trash 🗑️", stats["total_trash"], help="Dismissed low-priority items")

st.markdown("---")


# ==============================================================================
# VIEW 1: PRIORITY INBOX / SAVED / TRASH
# ==============================================================================
if nav_selection in ["📥 Priority Inbox", "⭐ Saved Mails", "🗑️ Trash"]:
    target_folder = {
        "📥 Priority Inbox": EmailFolder.INBOX,
        "⭐ Saved Mails": EmailFolder.SAVED,
        "🗑️ Trash": EmailFolder.TRASH
    }[nav_selection]

    # Filters Bar
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_query = st.text_input("🔍 Search emails (subject, sender, content)...", "")
    with f_col2:
        category_options = ["All Categories"] + [c.value.capitalize() for c in EmailCategory]
        selected_cat_str = st.selectbox("Category Filter", category_options)
        selected_category = None
        if selected_cat_str != "All Categories":
            selected_category = EmailCategory(selected_cat_str.lower())
    with f_col3:
        tier_options = ["All Tiers"] + [t.value for t in PriorityTier]
        selected_tier_str = st.selectbox("Urgency Tier", tier_options)
        selected_tier = None
        if selected_tier_str != "All Tiers":
            selected_tier = PriorityTier(selected_tier_str)

    emails = repository.list_emails(
        folder=target_folder,
        category=selected_category,
        priority_tier=selected_tier,
        search_query=search_query if search_query.strip() else None,
        limit=100
    )

    if not emails:
        st.info("No emails found matching your filters. Click 'Ingest Mocks' in sidebar to seed fresh emails.")
    else:
        st.subheader(f"{nav_selection} ({len(emails)} items)")

        for email in emails:
            # Badges
            tier_class = {
                PriorityTier.URGENT: "badge-urgent",
                PriorityTier.HIGH: "badge-high",
                PriorityTier.MEDIUM: "badge-medium",
                PriorityTier.LOW: "badge-low",
            }.get(email.priority_tier, "badge-low")

            tier_icon = {
                PriorityTier.URGENT: "🔥",
                PriorityTier.HIGH: "⚡",
                PriorityTier.MEDIUM: "⏳",
                PriorityTier.LOW: "📁"
            }.get(email.priority_tier, "")

            deadline_desc = email.deadline_str
            if email.hours_remaining is not None:
                if email.hours_remaining <= 0:
                    deadline_desc = f"⚠️ Expired ({abs(email.hours_remaining):.0f}h ago)"
                elif email.hours_remaining < 24:
                    deadline_desc = f"🚨 Due in {email.hours_remaining:.1f} hours ({email.deadline_str})"
                else:
                    days = email.hours_remaining / 24.0
                    deadline_desc = f"📅 Due in {days:.1f} days ({email.deadline_str})"

            with st.container():
                c_card, c_act = st.columns([5, 1])

                with c_card:
                    st.markdown(f"""
                        <div style="margin-bottom: 0.3rem;">
                            <span class="badge {tier_class}">{tier_icon} {email.priority_tier.value} (TUDS: {email.tuds_score:.3f})</span>
                            <span class="badge badge-cat">🏷️ {email.category.value.upper()}</span>
                            <span class="badge badge-deadline">⏰ {deadline_desc}</span>
                        </div>
                        <h4 style="margin: 0.2rem 0;">{email.subject}</h4>
                        <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.4rem;">
                            From: <strong>{email.sender_name}</strong> &lt;{email.sender_email}&gt; • {email.timestamp.strftime('%b %d, %Y %I:%M %p')}
                        </p>
                    """, unsafe_allow_html=True)

                    with st.expander("📄 View Email Content & Breakdown", expanded=False):
                        st.markdown(f"**Cleaned Content:**\n\n{email.cleaned_body}")
                        st.divider()
                        st.caption(
                            f"**TUDS Breakdown:** Base Relevance R={email.relevance_score:.2f} | "
                            f"Category Confidence={email.category_confidence:.2f} | "
                            f"Hours to Deadline: {email.hours_remaining if email.hours_remaining is not None else 'None'}"
                        )

                with c_act:
                    st.write("")
                    st.write("")
                    if target_folder == EmailFolder.INBOX:
                        if st.button("⭐ Save", key=f"save_{email.id}", use_container_width=True):
                            repository.set_folder(email.id, EmailFolder.SAVED)
                            st.rerun()
                        if st.button("🗑️ Trash", key=f"trash_{email.id}", use_container_width=True):
                            repository.set_folder(email.id, EmailFolder.TRASH)
                            st.rerun()
                    elif target_folder == EmailFolder.SAVED:
                        if st.button("📥 Inbox", key=f"inbox_{email.id}", use_container_width=True):
                            repository.set_folder(email.id, EmailFolder.INBOX)
                            st.rerun()
                        if st.button("🗑️ Trash", key=f"trash_saved_{email.id}", use_container_width=True):
                            repository.set_folder(email.id, EmailFolder.TRASH)
                            st.rerun()
                    elif target_folder == EmailFolder.TRASH:
                        if st.button("📥 Restore", key=f"restore_{email.id}", use_container_width=True):
                            repository.set_folder(email.id, EmailFolder.INBOX)
                            st.rerun()

                st.markdown("<hr style='margin: 0.75rem 0; opacity: 0.2;'>", unsafe_allow_html=True)


# ==============================================================================
# VIEW 2: ANALYTICS & INSIGHTS
# ==============================================================================
elif nav_selection == "📊 Analytics & Insights":
    st.subheader("📊 Email Volume & Priority Distribution Analytics")

    all_emails = repository.list_emails(folder=EmailFolder.INBOX, limit=500)
    if not all_emails:
        st.warning("No inbox data available to analyze.")
    else:
        categories = [e.category.value.capitalize() for e in all_emails]
        tiers = [e.priority_tier.value for e in all_emails]
        scores = [e.tuds_score for e in all_emails]
        hours = [e.hours_remaining if e.hours_remaining is not None else 0 for e in all_emails]

        cat_counter = Counter(categories)
        tier_counter = Counter(tiers)

        col_ch1, col_ch2 = st.columns(2)

        with col_ch1:
            st.markdown("#### Category Distribution")
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=list(cat_counter.keys()),
                    y=list(cat_counter.values()),
                    marker_color="#3b82f6"
                )
            ])
            fig_bar.update_layout(
                title="Emails per Category",
                template="plotly_dark",
                xaxis_title="Category",
                yaxis_title="Count"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_ch2:
            st.markdown("#### Urgency Tier Breakdown")
            color_map = {
                "Urgent": "#ef4444",
                "High": "#f59e0b",
                "Medium": "#3b82f6",
                "Low": "#6b7280"
            }
            tier_keys = list(tier_counter.keys())
            tier_vals = list(tier_counter.values())
            tier_colors = [color_map.get(k, "#6b7280") for k in tier_keys]

            fig_donut = go.Figure(data=[
                go.Pie(
                    labels=tier_keys,
                    values=tier_vals,
                    hole=0.45,
                    marker=dict(colors=tier_colors)
                )
            ])
            fig_donut.update_layout(
                title="Priority Tier Proportion",
                template="plotly_dark"
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("#### TUDS Score vs. Deadline Proximity")
        scatter_colors = [color_map.get(e.priority_tier.value, "#3b82f6") for e in all_emails]
        hover_texts = [f"{e.subject[:35]}...<br>Category: {e.category.value}" for e in all_emails]

        fig_scatter = go.Figure(data=[
            go.Scatter(
                x=hours,
                y=scores,
                mode="markers",
                marker=dict(
                    size=[max(12, s * 24) for s in scores],
                    color=scatter_colors,
                    showscale=False
                ),
                text=hover_texts,
                hovertemplate="Hours Remaining: %{x:.1f}h<br>TUDS Score: %{y:.3f}<br>%{text}<extra></extra>"
            )
        ])
        fig_scatter.update_layout(
            title="Email Prioritization Scatter (Urgency surge near 0 hours)",
            xaxis_title="Hours to Deadline (Zero = Imminent)",
            yaxis_title="TUDS Score [0.0 - 1.0]",
            template="plotly_dark"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)


# ==============================================================================
# VIEW 3: TUDS CURVE EXPLORER
# ==============================================================================
elif nav_selection == "🔬 TUDS Curve Explorer":
    st.subheader("🔬 Interactive TUDS Urgency Decay Simulation")
    st.markdown(
        r"""
        This interactive plot demonstrates the core scientific premise of this system:
        as an email approaches its deadline ($t \to 0$), the temporal decay term
        $1 + \alpha e^{-\lambda t}$ exponentially amplifies urgency.
        """
    )

    c_sel1, c_sel2 = st.columns(2)
    with c_sel1:
        sim_category_str = st.selectbox(
            "Select Category to Model",
            [c.value.capitalize() for c in EmailCategory]
        )
        sim_category = EmailCategory(sim_category_str.lower())
    with c_sel2:
        sim_days = st.slider("Simulation Window (Days)", 7, 45, 30)

    # Generate curve coordinates
    curve_data = generate_decay_curve_data(
        category=sim_category,
        params=tuds_params,
        max_days=sim_days,
        steps=100
    )

    x_days = [p["days_remaining"] for p in curve_data]
    y_scores = [p["priority_score"] for p in curve_data]

    fig_curve = go.Figure()

    fig_curve.add_trace(go.Scatter(
        x=x_days,
        y=y_scores,
        mode="lines",
        name=f"{sim_category.value.capitalize()} TUDS Curve",
        line=dict(color="#3b82f6", width=3),
        hovertemplate="Days Remaining: %{x:.1f}d<br>TUDS Score: %{y:.3f}<extra></extra>"
    ))

    # Add threshold regions
    fig_curve.add_hline(y=0.75, line_dash="dash", line_color="#ef4444", annotation_text="Urgent Threshold (0.75)")
    fig_curve.add_hline(y=0.60, line_dash="dash", line_color="#f59e0b", annotation_text="High Priority (0.60)")
    fig_curve.add_hline(y=0.40, line_dash="dash", line_color="#3b82f6", annotation_text="Medium Priority (0.40)")

    fig_curve.update_layout(
        title=f"Exponential Urgency Amplification Curve: {sim_category.value.capitalize()} (α={tuds_params.alpha})",
        xaxis_title="Days Remaining to Deadline (Counts Down → Right to Left)",
        yaxis_title="Dynamic Priority Score [0.0 - 1.0]",
        xaxis=dict(autorange="reversed"),  # Right (30 days) to Left (0 days)
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(fig_curve, use_container_width=True)

    st.info(
        f"💡 Notice: For **{sim_category.value.capitalize()}** with decay rate λ={tuds_params.category_lambdas.get(sim_category, 0.05)}, "
        f"an email that is low/medium priority 20 days prior automatically escalates to Urgent within the final 48 hours."
    )
