import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def calculate_equity_value(
    # Cap table inputs
    total_shares, your_options, strike_price,
    # Seed round
    seed_shares, seed_capital, seed_multiple,
    # Series A
    series_a_shares, series_a_capital, series_a_multiple,
    # Series B
    series_b_shares, series_b_capital, series_b_multiple,
    # Exit
    exit_valuation
):
    """Calculate startup equity value with liquidation preferences"""
    
    # Input validation
    if total_shares <= 0 or your_options < 0 or exit_valuation < 0:
        return "Invalid inputs", None, None
    
    # Calculate common shares (total - preferred shares issued)
    total_preferred_shares = seed_shares + series_a_shares + series_b_shares
    common_shares = total_shares - total_preferred_shares
    
    if common_shares <= 0:
        return "Error: Preferred shares exceed total shares", None, None
    
    # Build liquidation waterfall
    remaining_proceeds = exit_valuation
    waterfall_data = []
    
    # Series B gets paid first (most recent round)
    if series_b_shares > 0 and series_b_capital > 0:
        series_b_preference = series_b_capital * series_b_multiple
        series_b_payout = min(remaining_proceeds, series_b_preference)
        remaining_proceeds -= series_b_payout
        waterfall_data.append({
            'Round': 'Series B',
            'Preference': series_b_preference,
            'Payout': series_b_payout,
            'Remaining': remaining_proceeds
        })
    
    # Series A gets paid next
    if series_a_shares > 0 and series_a_capital > 0:
        series_a_preference = series_a_capital * series_a_multiple
        series_a_payout = min(remaining_proceeds, series_a_preference)
        remaining_proceeds -= series_a_payout
        waterfall_data.append({
            'Round': 'Series A',
            'Preference': series_a_preference,
            'Payout': series_a_payout,
            'Remaining': remaining_proceeds
        })
    
    # Seed gets paid last among preferred
    if seed_shares > 0 and seed_capital > 0:
        seed_preference = seed_capital * seed_multiple
        seed_payout = min(remaining_proceeds, seed_preference)
        remaining_proceeds -= seed_payout
        waterfall_data.append({
            'Round': 'Seed',
            'Preference': seed_preference,
            'Payout': seed_payout,
            'Remaining': remaining_proceeds
        })
    
    # Remaining proceeds go to common stock
    common_proceeds = max(0, remaining_proceeds)
    
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
    results = f"""
## 💰 Your Equity Value

**Total Option Value:** ${total_option_value:,.2f}
**Value per Option:** ${option_value_per_share:.4f}
**Your Equity Stake:** {your_equity_percentage:.3f}%

## 📊 Liquidation Analysis

**Exit Valuation:** ${exit_valuation:,.2f}
**Common Stock Proceeds:** ${common_proceeds:,.2f}
**Price per Common Share:** ${price_per_common_share:.4f}

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
        
        # Add bars for each round's payout
        y_pos = 0
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        for i, row in waterfall_df.iterrows():
            fig.add_trace(go.Bar(
                x=[row['Round']],
                y=[row['Payout']],
                name=f"{row['Round']} (${row['Payout']:,.0f})",
                marker_color=colors[i % len(colors)],
                text=f"${row['Payout']:,.0f}",
                textposition='inside'
            ))
        
        # Add common stock proceeds
        if common_proceeds > 0:
            fig.add_trace(go.Bar(
                x=['Common'],
                y=[common_proceeds],
                name=f"Common Stock (${common_proceeds:,.0f})",
                marker_color='#F7DC6F',
                text=f"${common_proceeds:,.0f}",
                textposition='inside'
            ))
        
        fig.update_layout(
            title="Liquidation Waterfall",
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
        # Recalculate for each exit value
        temp_remaining = ev
        
        # Subtract preferred liquidation preferences
        if series_b_shares > 0 and series_b_capital > 0:
            temp_remaining -= min(temp_remaining, series_b_capital * series_b_multiple)
        if series_a_shares > 0 and series_a_capital > 0:
            temp_remaining -= min(temp_remaining, series_a_capital * series_a_multiple)
        if seed_shares > 0 and seed_capital > 0:
            temp_remaining -= min(temp_remaining, seed_capital * seed_multiple)
        
        temp_common_proceeds = max(0, temp_remaining)
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
            
            with gr.Accordion("Series A", open=True):
                series_a_shares = gr.Number(label="Series A Shares Issued", value=1500000, precision=0)
                series_a_capital = gr.Number(label="Series A Capital Raised ($)", value=10000000, precision=0)
                series_a_multiple = gr.Number(label="Liquidation Multiple", value=1.0, precision=1)
            
            with gr.Accordion("Series B", open=False):
                series_b_shares = gr.Number(label="Series B Shares Issued", value=0, precision=0)
                series_b_capital = gr.Number(label="Series B Capital Raised ($)", value=0, precision=0)
                series_b_multiple = gr.Number(label="Liquidation Multiple", value=1.0, precision=1)
        
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
        seed_shares, seed_capital, seed_multiple,
        series_a_shares, series_a_capital, series_a_multiple,
        series_b_shares, series_b_capital, series_b_multiple,
        exit_valuation
    ]
    
    outputs = [results_text, waterfall_plot, sensitivity_plot]
    
    calculate_btn.click(calculate_equity_value, inputs=inputs, outputs=outputs)
    
    # Auto-calculate on input changes
    for input_component in inputs:
        input_component.change(calculate_equity_value, inputs=inputs, outputs=outputs)
    
    gr.Markdown("""
    ## 📚 How it Works
    
    1. **Liquidation Preferences**: Preferred shareholders (investors) typically get their money back first, often with a multiplier
    2. **Waterfall Structure**: Series B → Series A → Seed → Common Stock
    3. **Your Options**: Get value from the residual amount available to common shareholders
    4. **Break-even**: The exit value where your options start having value after all preferences are paid
    
    **Note**: This calculator assumes non-participating preferred stock. In reality, cap tables can be more complex with participating preferred, anti-dilution provisions, and other terms.
    """)

if __name__ == "__main__":
    app.launch()