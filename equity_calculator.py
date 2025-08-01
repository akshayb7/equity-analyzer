import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def calculate_equity_value(
    # Cap table inputs
    total_shares, your_options, strike_price,
    # Seed round
    seed_shares, seed_capital, seed_multiple, seed_participating,
    # Series A
    series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
    # Series B
    series_b_shares, series_b_capital, series_b_multiple, series_b_participating,
    # Exit
    exit_valuation
):
    """Calculate startup equity value with liquidation preferences"""
    
    # Handle None values and provide defaults
    total_shares = total_shares or 10000000
    your_options = your_options or 0
    strike_price = strike_price or 0
    seed_shares = seed_shares or 0
    seed_capital = seed_capital or 0
    seed_multiple = seed_multiple or 1.0
    seed_participating = seed_participating or False
    series_a_shares = series_a_shares or 0
    series_a_capital = series_a_capital or 0
    series_a_multiple = series_a_multiple or 1.0
    series_a_participating = series_a_participating or False
    series_b_shares = series_b_shares or 0
    series_b_capital = series_b_capital or 0
    series_b_multiple = series_b_multiple or 1.0
    series_b_participating = series_b_participating or False
    exit_valuation = exit_valuation or 0
    
    # Input validation
    if total_shares <= 0 or your_options < 0 or exit_valuation < 0:
        return "Invalid inputs - please check your values", None, None
    
    # Calculate common shares (total - preferred shares issued)
    total_preferred_shares = seed_shares + series_a_shares + series_b_shares
    common_shares = total_shares - total_preferred_shares
    
    if common_shares <= 0:
        return "Error: Preferred shares exceed total shares", None, None
    
    # Build liquidation waterfall with participating/non-participating logic
    remaining_proceeds = exit_valuation
    waterfall_data = []
    participating_shareholders = []  # Track participating preferred for later distribution
    
    # Phase 1: Pay liquidation preferences first
    
    # Series B gets paid first (most recent round)
    series_b_preference_payout = 0
    if series_b_shares > 0 and series_b_capital > 0:
        series_b_preference = series_b_capital * series_b_multiple
        series_b_preference_payout = min(remaining_proceeds, series_b_preference)
        remaining_proceeds -= series_b_preference_payout
        
        if series_b_participating:
            participating_shareholders.append({
                'round': 'Series B',
                'shares': series_b_shares,
                'preference_paid': series_b_preference_payout
            })
        
        waterfall_data.append({
            'Round': 'Series B (Pref)',
            'Preference': series_b_preference,
            'Payout': series_b_preference_payout,
            'Remaining': remaining_proceeds,
            'Type': 'Preference'
        })
    
    # Series A gets paid next
    series_a_preference_payout = 0
    if series_a_shares > 0 and series_a_capital > 0:
        series_a_preference = series_a_capital * series_a_multiple
        series_a_preference_payout = min(remaining_proceeds, series_a_preference)
        remaining_proceeds -= series_a_preference_payout
        
        if series_a_participating:
            participating_shareholders.append({
                'round': 'Series A',
                'shares': series_a_shares,
                'preference_paid': series_a_preference_payout
            })
        
        waterfall_data.append({
            'Round': 'Series A (Pref)',
            'Preference': series_a_preference,
            'Payout': series_a_preference_payout,
            'Remaining': remaining_proceeds,
            'Type': 'Preference'
        })
    
    # Seed gets paid last among preferred
    seed_preference_payout = 0
    if seed_shares > 0 and seed_capital > 0:
        seed_preference = seed_capital * seed_multiple
        seed_preference_payout = min(remaining_proceeds, seed_preference)
        remaining_proceeds -= seed_preference_payout
        
        if seed_participating:
            participating_shareholders.append({
                'round': 'Seed',
                'shares': seed_shares,
                'preference_paid': seed_preference_payout
            })
        
        waterfall_data.append({
            'Round': 'Seed (Pref)',
            'Preference': seed_preference,
            'Payout': seed_preference_payout,
            'Remaining': remaining_proceeds,
            'Type': 'Preference'
        })
    
    # Phase 2: Distribute remaining proceeds
    
    # Calculate total shares eligible for remaining distribution
    # This includes: common shares + participating preferred shares
    participating_preferred_shares = sum([p['shares'] for p in participating_shareholders])
    total_participating_shares = common_shares + participating_preferred_shares
    
    # For non-participating preferred, we need to check if conversion is better
    # than taking the liquidation preference
    
    # Series B non-participating conversion check
    if series_b_shares > 0 and series_b_capital > 0 and not series_b_participating:
        # Calculate what they'd get if they converted to common
        conversion_value = (series_b_shares / total_shares) * exit_valuation
        if conversion_value > series_b_preference_payout:
            # They convert - add back their preference and include them in common distribution
            remaining_proceeds += series_b_preference_payout
            total_participating_shares += series_b_shares
            # Update waterfall data
            for item in waterfall_data:
                if item['Round'] == 'Series B (Pref)':
                    item['Round'] = 'Series B (Converted)'
                    item['Payout'] = 0  # They'll get paid in common distribution
                    item['Type'] = 'Conversion'
    
    # Series A non-participating conversion check
    if series_a_shares > 0 and series_a_capital > 0 and not series_a_participating:
        conversion_value = (series_a_shares / total_shares) * exit_valuation
        if conversion_value > series_a_preference_payout:
            remaining_proceeds += series_a_preference_payout
            total_participating_shares += series_a_shares
            for item in waterfall_data:
                if item['Round'] == 'Series A (Pref)':
                    item['Round'] = 'Series A (Converted)'
                    item['Payout'] = 0
                    item['Type'] = 'Conversion'
    
    # Seed non-participating conversion check
    if seed_shares > 0 and seed_capital > 0 and not seed_participating:
        conversion_value = (seed_shares / total_shares) * exit_valuation
        if conversion_value > seed_preference_payout:
            remaining_proceeds += seed_preference_payout
            total_participating_shares += seed_shares
            for item in waterfall_data:
                if item['Round'] == 'Seed (Pref)':
                    item['Round'] = 'Seed (Converted)'
                    item['Payout'] = 0
                    item['Type'] = 'Conversion'
    
    # Final distribution to common + participating preferred
    if total_participating_shares > 0:
        price_per_participating_share = remaining_proceeds / total_participating_shares
        common_proceeds = price_per_participating_share * common_shares
        
        # Add participating preferred payouts to waterfall
        for participant in participating_shareholders:
            participating_payout = price_per_participating_share * participant['shares']
            waterfall_data.append({
                'Round': f"{participant['round']} (Participating)",
                'Preference': 0,
                'Payout': participating_payout,
                'Remaining': remaining_proceeds - participating_payout,
                'Type': 'Participation'
            })
    else:
        price_per_participating_share = 0
        common_proceeds = remaining_proceeds
    
    # Calculate price per common share
    if common_shares > 0:
        price_per_common_share = common_proceeds / common_shares
    else:
        price_per_common_share = 0
    
    # Calculate your option value
    option_value_per_share = max(0, price_per_common_share - strike_price)
    total_option_value = option_value_per_share * your_options
    
    # Calculate your equity percentage
    your_equity_percentage = (your_options / total_shares) * 100 if total_shares > 0 else 0
    
    # Build results summary
    participating_status = []
    if seed_shares > 0: participating_status.append(f"Seed: {'Participating' if seed_participating else 'Non-Participating'}")
    if series_a_shares > 0: participating_status.append(f"Series A: {'Participating' if series_a_participating else 'Non-Participating'}")
    if series_b_shares > 0: participating_status.append(f"Series B: {'Participating' if series_b_participating else 'Non-Participating'}")
    
    results = f"""
## 💰 Your Equity Value

**Total Option Value:** ${total_option_value:,.2f}
**Value per Option:** ${option_value_per_share:.4f}
**Your Equity Stake:** {your_equity_percentage:.3f}%

## 📊 Liquidation Analysis

**Exit Valuation:** ${exit_valuation:,.2f}
**Common Stock Proceeds:** ${common_proceeds:,.2f}
**Price per Common Share:** ${price_per_common_share:.4f}

**Liquidation Terms:** {' | '.join(participating_status) if participating_status else 'No preferred rounds'}

**Break-even Exit Value:** ${(strike_price * total_shares):,.2f}
*(Exit value needed for your options to have value)*

## 🏗️ Cap Table Summary

**Total Shares:** {total_shares:,}
**Common Shares:** {common_shares:,}
**Preferred Shares:** {total_preferred_shares:,}
"""
    
    # Create waterfall chart
    if waterfall_data:
        waterfall_df = pd.DataFrame(waterfall_data)
        
        fig = go.Figure()
        
        # Color coding for different types
        color_map = {
            'Preference': '#FF6B6B',  # Red for liquidation preferences
            'Participation': '#4ECDC4',  # Teal for participating preferred
            'Conversion': '#45B7D1'   # Blue for converted preferred
        }
        
        for i, row in waterfall_df.iterrows():
            color = color_map.get(row.get('Type', 'Preference'), '#96CEB4')
            fig.add_trace(go.Bar(
                x=[row['Round']],
                y=[row['Payout']],
                name=f"{row['Round']} (${row['Payout']:,.0f})",
                marker_color=color,
                text=f"${row['Payout']:,.0f}" if row['Payout'] > 0 else "Converted",
                textposition='inside'
            ))
        
        # Add common stock proceeds
        if common_proceeds > 0:
            fig.add_trace(go.Bar(
                x=['Common Stock'],
                y=[common_proceeds],
                name=f"Common Stock (${common_proceeds:,.0f})",
                marker_color='#F7DC6F',
                text=f"${common_proceeds:,.0f}",
                textposition='inside'
            ))
        
        fig.update_layout(
            title="Liquidation Waterfall (Preferences → Participation → Common)",
            xaxis_title="Stakeholder",
            yaxis_title="Payout ($)",
            showlegend=True,
            height=400
        )
        
        waterfall_chart = fig
    else:
        # Simple pie chart if no preferred rounds
        fig = go.Figure(data=[go.Pie(
            labels=['Your Options', 'Other Common'],
            values=[your_options, common_shares - your_options],
            hole=0.3
        )])
        fig.update_layout(title="Your Share of Common Stock")
        waterfall_chart = fig
    
    # Create sensitivity analysis
    exit_values = [exit_valuation * i for i in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]]
    option_values = []
    
    for ev in exit_values:
        # Recalculate for each exit value with participating logic
        temp_remaining = ev
        temp_participating_shareholders = []
        
        # Pay preferences first
        if series_b_shares > 0 and series_b_capital > 0:
            temp_payout = min(temp_remaining, series_b_capital * series_b_multiple)
            temp_remaining -= temp_payout
            if series_b_participating:
                temp_participating_shareholders.append({'shares': series_b_shares})
        
        if series_a_shares > 0 and series_a_capital > 0:
            temp_payout = min(temp_remaining, series_a_capital * series_a_multiple)
            temp_remaining -= temp_payout
            if series_a_participating:
                temp_participating_shareholders.append({'shares': series_a_shares})
        
        if seed_shares > 0 and seed_capital > 0:
            temp_payout = min(temp_remaining, seed_capital * seed_multiple)
            temp_remaining -= temp_payout
            if seed_participating:
                temp_participating_shareholders.append({'shares': seed_shares})
        
        # Handle non-participating conversion decisions
        temp_total_participating = common_shares + sum([p['shares'] for p in temp_participating_shareholders])
        
        # Check non-participating conversions (simplified for sensitivity)
        if series_b_shares > 0 and not series_b_participating:
            conversion_value = (series_b_shares / total_shares) * ev
            preference_value = series_b_capital * series_b_multiple
            if conversion_value > preference_value:
                temp_remaining += min(temp_remaining + preference_value, preference_value)
                temp_total_participating += series_b_shares
        
        if series_a_shares > 0 and not series_a_participating:
            conversion_value = (series_a_shares / total_shares) * ev
            preference_value = series_a_capital * series_a_multiple
            if conversion_value > preference_value:
                temp_remaining += min(temp_remaining + preference_value, preference_value)
                temp_total_participating += series_a_shares
        
        if seed_shares > 0 and not seed_participating:
            conversion_value = (seed_shares / total_shares) * ev
            preference_value = seed_capital * seed_multiple
            if conversion_value > preference_value:
                temp_remaining += min(temp_remaining + preference_value, preference_value)
                temp_total_participating += seed_shares
        
        # Calculate common proceeds
        if temp_total_participating > 0:
            temp_common_proceeds = (common_shares / temp_total_participating) * temp_remaining
        else:
            temp_common_proceeds = temp_remaining
        
        temp_price_per_share = temp_common_proceeds / common_shares if common_shares > 0 else 0
        temp_option_value = max(0, temp_price_per_share - strike_price) * your_options
        option_values.append(temp_option_value)
    
    sensitivity_fig = go.Figure()
    sensitivity_fig.add_trace(go.Scatter(
        x=exit_values,
        y=option_values,
        mode='lines+markers',
        name='Option Value',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8)
    ))
    
    sensitivity_fig.update_layout(
        title="Sensitivity Analysis: Exit Value vs Option Value",
        xaxis_title="Exit Valuation ($)",
        yaxis_title="Your Option Value ($)",
        height=400
    )
    
    return results, waterfall_chart, sensitivity_fig

# Create Gradio interface
with gr.Blocks(title="Startup Equity Calculator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🚀 Startup Equity Calculator")
    gr.Markdown("Calculate the value of your stock options based on cap table structure and liquidation preferences")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("## Cap Table Structure")
            total_shares = gr.Number(label="Total Fully Diluted Shares", value=10000000, precision=0)
            your_options = gr.Number(label="Your Option Grant", value=50000, precision=0)
            strike_price = gr.Number(label="Strike Price per Share ($)", value=0.10, precision=4)
            
            gr.Markdown("## Funding Rounds")
            
            with gr.Accordion("Seed Round", open=True):
                seed_shares = gr.Number(label="Seed Shares Issued", value=2000000, precision=0)
                seed_capital = gr.Number(label="Seed Capital Raised ($)", value=2000000, precision=0)
                seed_multiple = gr.Number(label="Liquidation Multiple", value=1.0, precision=1)
                seed_participating = gr.Checkbox(label="Participating Preferred", value=False)
            
            with gr.Accordion("Series A", open=True):
                series_a_shares = gr.Number(label="Series A Shares Issued", value=1500000, precision=0)
                series_a_capital = gr.Number(label="Series A Capital Raised ($)", value=10000000, precision=0)
                series_a_multiple = gr.Number(label="Liquidation Multiple", value=1.0, precision=1)
                series_a_participating = gr.Checkbox(label="Participating Preferred", value=False)
            
            with gr.Accordion("Series B", open=False):
                series_b_shares = gr.Number(label="Series B Shares Issued", value=0, precision=0)
                series_b_capital = gr.Number(label="Series B Capital Raised ($)", value=0, precision=0)
                series_b_multiple = gr.Number(label="Liquidation Multiple", value=1.0, precision=1)
                series_b_participating = gr.Checkbox(label="Participating Preferred", value=False)
        
        with gr.Column():
            gr.Markdown("## Exit Scenario")
            exit_valuation = gr.Number(label="Exit Valuation ($)", value=50000000, precision=0)
            
            calculate_btn = gr.Button("Calculate Equity Value", variant="primary", size="lg")
            
            results_text = gr.Markdown()
            
    with gr.Row():
        waterfall_plot = gr.Plot(label="Liquidation Waterfall")
        sensitivity_plot = gr.Plot(label="Sensitivity Analysis")
    
    # Set up the calculation trigger
    inputs = [
        total_shares, your_options, strike_price,
        seed_shares, seed_capital, seed_multiple, seed_participating,
        series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
        series_b_shares, series_b_capital, series_b_multiple, series_b_participating,
        exit_valuation
    ]
    
    outputs = [results_text, waterfall_plot, sensitivity_plot]
    
    calculate_btn.click(calculate_equity_value, inputs=inputs, outputs=outputs)
    
    # Auto-calculate on input changes
    for input_component in inputs:
        input_component.change(calculate_equity_value, inputs=inputs, outputs=outputs)
    
    gr.Markdown("""
    ## 📚 How it Works
    
    ### Liquidation Waterfall
    1. **Liquidation Preferences**: Preferred shareholders get their money back first (with multipliers)
    2. **Participating vs Non-Participating**:
       - **Non-Participating**: Investors choose either their preference OR convert to common (whichever is better)
       - **Participating**: Investors get their preference AND participate in remaining proceeds ("double dipping")
    3. **Conversion Decision**: Non-participating preferred will convert if their pro-rata share of total exit > liquidation preference
    4. **Your Options**: Get value from whatever is left for common shareholders
    
    ### Visual Guide
    - **Red bars**: Liquidation preferences paid first
    - **Teal bars**: Participating preferred getting their share of remaining proceeds  
    - **Blue bars**: Non-participating preferred that chose to convert to common
    - **Yellow bars**: Final proceeds available to common stock (including your options)
    
    ### Key Insight
    **Participating preferred significantly reduces common stock value** because investors get both their money back AND a share of the upside. Toggle the participating checkboxes to see the dramatic difference in your option value!
    
    **Note**: This calculator assumes basic liquidation preferences. Real cap tables may include anti-dilution provisions, participation caps, and other complex terms.
    """)

if __name__ == "__main__":
    app.launch()