import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def calculate_single_scenario(
    exit_valuation, total_shares, your_options, strike_price,
    seed_shares, seed_capital, seed_multiple, seed_participating,
    series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
    series_b_shares, series_b_capital, series_b_multiple, series_b_participating
):
    """Calculate equity value for a single exit scenario"""
    
    # Calculate common shares
    total_preferred_shares = seed_shares + series_a_shares + series_b_shares
    common_shares = total_shares - total_preferred_shares
    
    if common_shares <= 0:
        return {
            'exit_valuation': exit_valuation,
            'option_value': 0,
            'price_per_share': 0,
            'common_proceeds': 0,
            'error': 'Preferred shares exceed total shares'
        }
    
    # Phase 1: Pay liquidation preferences
    remaining_proceeds = exit_valuation
    participating_shareholders = []
    
    # Series B (most recent)
    series_b_preference_payout = 0
    if series_b_shares > 0 and series_b_capital > 0:
        series_b_preference = series_b_capital * series_b_multiple
        series_b_preference_payout = min(remaining_proceeds, series_b_preference)
        remaining_proceeds -= series_b_preference_payout
        if series_b_participating:
            participating_shareholders.append({'shares': series_b_shares})
    
    # Series A
    series_a_preference_payout = 0
    if series_a_shares > 0 and series_a_capital > 0:
        series_a_preference = series_a_capital * series_a_multiple
        series_a_preference_payout = min(remaining_proceeds, series_a_preference)
        remaining_proceeds -= series_a_preference_payout
        if series_a_participating:
            participating_shareholders.append({'shares': series_a_shares})
    
    # Seed
    seed_preference_payout = 0
    if seed_shares > 0 and seed_capital > 0:
        seed_preference = seed_capital * seed_multiple
        seed_preference_payout = min(remaining_proceeds, seed_preference)
        remaining_proceeds -= seed_preference_payout
        if seed_participating:
            participating_shareholders.append({'shares': seed_shares})
    
    # Phase 2: Handle non-participating conversions
    participating_preferred_shares = sum([p['shares'] for p in participating_shareholders])
    total_participating_shares = common_shares + participating_preferred_shares
    
    # Check conversions for non-participating preferred
    if series_b_shares > 0 and series_b_capital > 0 and not series_b_participating:
        conversion_value = (series_b_shares / total_shares) * exit_valuation
        if conversion_value > series_b_preference_payout:
            remaining_proceeds += series_b_preference_payout
            total_participating_shares += series_b_shares
    
    if series_a_shares > 0 and series_a_capital > 0 and not series_a_participating:
        conversion_value = (series_a_shares / total_shares) * exit_valuation
        if conversion_value > series_a_preference_payout:
            remaining_proceeds += series_a_preference_payout
            total_participating_shares += series_a_shares
    
    if seed_shares > 0 and seed_capital > 0 and not seed_participating:
        conversion_value = (seed_shares / total_shares) * exit_valuation
        if conversion_value > seed_preference_payout:
            remaining_proceeds += seed_preference_payout
            total_participating_shares += seed_shares
    
    # Final distribution
    if total_participating_shares > 0:
        price_per_participating_share = remaining_proceeds / total_participating_shares
        common_proceeds = price_per_participating_share * common_shares
    else:
        common_proceeds = remaining_proceeds
    
    price_per_common_share = common_proceeds / common_shares if common_shares > 0 else 0
    option_value_per_share = max(0, price_per_common_share - strike_price)
    total_option_value = option_value_per_share * your_options
    
    return {
        'exit_valuation': exit_valuation,
        'option_value': total_option_value,
        'price_per_share': price_per_common_share,
        'common_proceeds': common_proceeds,
        'error': None
    }

def calculate_equity_value(
    # Cap table inputs
    total_shares, your_options, strike_price,
    # Seed round
    seed_shares, seed_capital, seed_multiple, seed_participating,
    # Series A
    series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
    # Series B
    series_b_shares, series_b_capital, series_b_multiple, series_b_participating,
    # Multiple exit scenarios
    exit_scenario_1, scenario_1_name,
    exit_scenario_2, scenario_2_name,
    exit_scenario_3, scenario_3_name,
    exit_scenario_4, scenario_4_name,
    exit_scenario_5, scenario_5_name
):
    """Calculate startup equity value with liquidation preferences for multiple exit scenarios"""
    
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
    
    # Handle exit scenarios
    exit_scenario_1 = exit_scenario_1 or 0
    exit_scenario_2 = exit_scenario_2 or 0
    exit_scenario_3 = exit_scenario_3 or 0
    exit_scenario_4 = exit_scenario_4 or 0
    exit_scenario_5 = exit_scenario_5 or 0
    scenario_1_name = scenario_1_name or "Scenario 1"
    scenario_2_name = scenario_2_name or "Scenario 2"
    scenario_3_name = scenario_3_name or "Scenario 3"
    scenario_4_name = scenario_4_name or "Scenario 4"
    scenario_5_name = scenario_5_name or "Scenario 5"
    
    # Input validation
    if total_shares <= 0:
        return "Invalid inputs - please check your values", None, None, None
    
    # Calculate scenarios
    scenarios = []
    exit_values = [exit_scenario_1, exit_scenario_2, exit_scenario_3, exit_scenario_4, exit_scenario_5]
    scenario_names = [scenario_1_name, scenario_2_name, scenario_3_name, scenario_4_name, scenario_5_name]
    
    for exit_val, name in zip(exit_values, scenario_names):
        if exit_val > 0:  # Only calculate scenarios with positive exit values
            scenario_result = calculate_single_scenario(
                exit_val, total_shares, your_options, strike_price,
                seed_shares, seed_capital, seed_multiple, seed_participating,
                series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
                series_b_shares, series_b_capital, series_b_multiple, series_b_participating
            )
            scenario_result['name'] = name
            scenarios.append(scenario_result)
    
    if not scenarios:
        return "Please enter at least one exit scenario with a positive value", None, None, None

    # Calculate common shares and basic info
    total_preferred_shares = seed_shares + series_a_shares + series_b_shares
    common_shares = total_shares - total_preferred_shares
    your_equity_percentage = (your_options / total_shares) * 100 if total_shares > 0 else 0
    
    # Build results summary
    participating_status = []
    if seed_shares > 0: participating_status.append(f"Seed: {'Participating' if seed_participating else 'Non-Participating'}")
    if series_a_shares > 0: participating_status.append(f"Series A: {'Participating' if series_a_participating else 'Non-Participating'}")
    if series_b_shares > 0: participating_status.append(f"Series B: {'Participating' if series_b_participating else 'Non-Participating'}")
    
    # Create scenario comparison table
    scenario_table = "## 📊 Exit Scenario Comparison\n\n"
    scenario_table += "| Scenario | Exit Value | Your Option Value | Value per Option | Common Proceeds |\n"
    scenario_table += "|----------|------------|-------------------|------------------|------------------|\n"
    
    for scenario in scenarios:
        scenario_table += f"| **{scenario['name']}** | ${scenario['exit_valuation']:,.0f} | "
        scenario_table += f"${scenario['option_value']:,.2f} | ${scenario['option_value']/your_options if your_options > 0 else 0:.4f} | "
        scenario_table += f"${scenario['common_proceeds']:,.0f} |\n"
    
    results = f"""
## 💰 Your Equity Summary

**Your Option Grant:** {your_options:,} options
**Strike Price:** ${strike_price:.4f} per share
**Your Equity Stake:** {your_equity_percentage:.3f}%

{scenario_table}

## 🏗️ Cap Table Summary

**Total Shares:** {total_shares:,}
**Common Shares:** {common_shares:,}
**Preferred Shares:** {total_preferred_shares:,}

**Liquidation Terms:** {' | '.join(participating_status) if participating_status else 'No preferred rounds'}

**Break-even Price per Share:** ${strike_price:.4f}
*(Price needed for your options to have positive value)*
"""

    # Create comparison bar chart
    if scenarios:
        scenario_names = [s['name'] for s in scenarios]
        option_values = [s['option_value'] for s in scenarios]
        exit_values = [s['exit_valuation'] for s in scenarios]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Your Option Value by Scenario", "Exit Valuation by Scenario"),
            vertical_spacing=0.20,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # Option values bar chart
        fig.add_trace(
            go.Bar(
                x=scenario_names,
                y=option_values,
                name="Option Value",
                marker_color='#2E86AB',
                text=[f"${val:,.0f}" for val in option_values],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Exit valuations bar chart
        fig.add_trace(
            go.Bar(
                x=scenario_names,
                y=exit_values,
                name="Exit Valuation",
                marker_color='#F18F01',
                text=[f"${val:,.0f}" for val in exit_values],
                textposition='outside',
                showlegend=False
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Multi-Scenario Equity Analysis",
            height=650,
            showlegend=True,
            margin=dict(t=80, b=50, l=80, r=50)
        )
        
        # Add extra space for text labels above bars
        fig.update_yaxes(title_text="Your Option Value ($)", row=1, col=1, range=[0, max(option_values) * 1.15])
        fig.update_yaxes(title_text="Company Valuation ($)", row=2, col=1, range=[0, max(exit_values) * 1.15])
        
        comparison_chart = fig
    else:
        comparison_chart = None

    # Create detailed breakdown chart for the highest scenario
    if scenarios:
        # Find the scenario with highest option value for detailed analysis
        best_scenario = max(scenarios, key=lambda x: x['option_value'])
        
        # Create a detailed waterfall for this scenario
        detailed_fig = calculate_single_scenario_waterfall(
            best_scenario['exit_valuation'], total_shares, your_options, strike_price,
            seed_shares, seed_capital, seed_multiple, seed_participating,
            series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
            series_b_shares, series_b_capital, series_b_multiple, series_b_participating
        )
        
        detailed_chart = detailed_fig
    else:
        detailed_chart = None
    
    # Create ROI comparison
    if scenarios and your_options > 0:
        roi_data = []
        investment_cost = your_options * strike_price
        
        for scenario in scenarios:
            if investment_cost > 0:
                roi = ((scenario['option_value'] - investment_cost) / investment_cost) * 100
            else:
                roi = float('inf') if scenario['option_value'] > 0 else 0
            
            roi_data.append({
                'scenario': scenario['name'],
                'roi': roi if roi != float('inf') else 999999,  # Cap at very high number for display
                'absolute_gain': scenario['option_value'] - investment_cost
            })
        
        roi_fig = go.Figure()
        roi_fig.add_trace(go.Bar(
            x=[d['scenario'] for d in roi_data],
            y=[d['roi'] for d in roi_data],
            name="ROI %",
            marker_color='#28A745',
            text=[f"{d['roi']:.0f}%" if d['roi'] < 999999 else "∞%" for d in roi_data],
            textposition='outside'
        ))
        
        roi_fig.update_layout(
            title="Return on Investment (ROI) by Scenario",
            xaxis_title="Scenario",
            yaxis_title="ROI (%)",
            height=450,
            margin=dict(t=60, b=50, l=60, r=50)
        )
        
        roi_chart = roi_fig
    else:
        roi_chart = None
    
    return results, comparison_chart, detailed_chart, roi_chart

def calculate_single_scenario_waterfall(
    exit_valuation, total_shares, your_options, strike_price,
    seed_shares, seed_capital, seed_multiple, seed_participating,
    series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
    series_b_shares, series_b_capital, series_b_multiple, series_b_participating
):
    """Create detailed waterfall chart for a single scenario"""
    
    common_shares = total_shares - (seed_shares + series_a_shares + series_b_shares)
    remaining_proceeds = exit_valuation
    waterfall_data = []
    participating_shareholders = []
    
    # Phase 1: Liquidation preferences
    if series_b_shares > 0 and series_b_capital > 0:
        series_b_preference = series_b_capital * series_b_multiple
        series_b_payout = min(remaining_proceeds, series_b_preference)
        remaining_proceeds -= series_b_payout
        
        if series_b_participating:
            participating_shareholders.append({'round': 'Series B', 'shares': series_b_shares})
        
        waterfall_data.append({
            'Round': 'Series B (Pref)',
            'Payout': series_b_payout,
            'Type': 'Preference'
        })
    
    if series_a_shares > 0 and series_a_capital > 0:
        series_a_preference = series_a_capital * series_a_multiple
        series_a_payout = min(remaining_proceeds, series_a_preference)
        remaining_proceeds -= series_a_payout
        
        if series_a_participating:
            participating_shareholders.append({'round': 'Series A', 'shares': series_a_shares})
        
        waterfall_data.append({
            'Round': 'Series A (Pref)',
            'Payout': series_a_payout,
            'Type': 'Preference'
        })
    
    if seed_shares > 0 and seed_capital > 0:
        seed_preference = seed_capital * seed_multiple
        seed_payout = min(remaining_proceeds, seed_preference)
        remaining_proceeds -= seed_payout
        
        if seed_participating:
            participating_shareholders.append({'round': 'Seed', 'shares': seed_shares})
        
        waterfall_data.append({
            'Round': 'Seed (Pref)',
            'Payout': seed_payout,
            'Type': 'Preference'
        })
    
    # Phase 2: Check conversions and final distribution
    participating_preferred_shares = sum([p['shares'] for p in participating_shareholders])
    total_participating_shares = common_shares + participating_preferred_shares
    
    # Simplified conversion logic for visualization
    if total_participating_shares > 0:
        price_per_share = remaining_proceeds / total_participating_shares
        common_proceeds = price_per_share * common_shares
        
        # Add participating preferred distributions
        for participant in participating_shareholders:
            participating_payout = price_per_share * participant['shares']
            waterfall_data.append({
                'Round': f"{participant['round']} (Part.)",
                'Payout': participating_payout,
                'Type': 'Participation'
            })
    else:
        common_proceeds = remaining_proceeds
    
    # Add common stock
    waterfall_data.append({
        'Round': 'Common Stock',
        'Payout': common_proceeds,
        'Type': 'Common'
    })
    
    # Create the chart
    fig = go.Figure()
    
    color_map = {
        'Preference': '#FF6B6B',
        'Participation': '#4ECDC4',
        'Common': '#F7DC6F'
    }
    
    for item in waterfall_data:
        if item['Payout'] > 0:
            color = color_map.get(item['Type'], '#96CEB4')
            fig.add_trace(go.Bar(
                x=[item['Round']],
                y=[item['Payout']],
                name=f"{item['Round']} (${item['Payout']:,.0f})",
                marker_color=color,
                text=f"${item['Payout']:,.0f}",
                textposition='outside'
            ))
    
    fig.update_layout(
        title=f"Liquidation Waterfall - ${exit_valuation:,.0f} Exit",
        xaxis_title="Stakeholder",
        yaxis_title="Payout ($)",
        height=450,
        showlegend=True,
        margin=dict(t=60, b=50, l=80, r=50)
    )
    
    return fig

# Create Gradio interface
with gr.Blocks(title="Startup Equity Calculator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🚀 Startup Equity Calculator")
    gr.Markdown("Calculate the value of your stock options based on cap table structure and liquidation preferences")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("## Cap Table Structure")
            total_shares = gr.Number(label="Total Fully Diluted Shares", value=10000000, precision=0)
            your_options = gr.Number(label="Your Option Grant", value=0, precision=0)
            strike_price = gr.Number(label="Strike Price per Share ($)", value=0.10, precision=4)
            
            gr.Markdown("## Funding Rounds")
            
            with gr.Accordion("Seed Round", open=False):
                seed_shares = gr.Number(label="Seed Shares Issued", value=0, precision=0)
                seed_capital = gr.Number(label="Seed Capital Raised ($)", value=0, precision=0)
                seed_multiple = gr.Number(label="Liquidation Multiple", value=1.0, precision=1)
                seed_participating = gr.Checkbox(label="Participating Preferred", value=False)
            
            with gr.Accordion("Series A", open=False):
                series_a_shares = gr.Number(label="Series A Shares Issued", value=0, precision=0)
                series_a_capital = gr.Number(label="Series A Capital Raised ($)", value=0, precision=0)
                series_a_multiple = gr.Number(label="Liquidation Multiple", value=1.0, precision=1)
                series_a_participating = gr.Checkbox(label="Participating Preferred", value=False)
            
            with gr.Accordion("Series B", open=False):
                series_b_shares = gr.Number(label="Series B Shares Issued", value=0, precision=0)
                series_b_capital = gr.Number(label="Series B Capital Raised ($)", value=0, precision=0)
                series_b_multiple = gr.Number(label="Liquidation Multiple", value=1.0, precision=1)
                series_b_participating = gr.Checkbox(label="Participating Preferred", value=False)
        
        with gr.Column():
            gr.Markdown("## Exit Scenarios")
            gr.Markdown("*Define multiple exit scenarios to compare side-by-side*")
            
            with gr.Row():
                with gr.Column():
                    scenario_1_name = gr.Textbox(label="Scenario 1 Name", value="Conservative", placeholder="e.g., Conservative")
                    exit_scenario_1 = gr.Number(label="Exit Valuation ($)", value=25000000, precision=0)
                
                with gr.Column():
                    scenario_2_name = gr.Textbox(label="Scenario 2 Name", value="Base Case", placeholder="e.g., Base Case")
                    exit_scenario_2 = gr.Number(label="Exit Valuation ($)", value=50000000, precision=0)
            
            with gr.Row():
                with gr.Column():
                    scenario_3_name = gr.Textbox(label="Scenario 3 Name", value="Optimistic", placeholder="e.g., Optimistic")
                    exit_scenario_3 = gr.Number(label="Exit Valuation ($)", value=100000000, precision=0)
                
                with gr.Column():
                    scenario_4_name = gr.Textbox(label="Scenario 4 Name", value="", placeholder="e.g., Moon Shot")
                    exit_scenario_4 = gr.Number(label="Exit Valuation ($)", value=0, precision=0)
            
            with gr.Row():
                with gr.Column():
                    scenario_5_name = gr.Textbox(label="Scenario 5 Name", value="", placeholder="e.g., IPO")
                    exit_scenario_5 = gr.Number(label="Exit Valuation ($)", value=0, precision=0)
            
            calculate_btn = gr.Button("🚀 Calculate All Scenarios", variant="primary", size="lg")
            
            results_text = gr.Markdown()
            
    with gr.Row():
        comparison_plot = gr.Plot(label="Multi-Scenario Comparison")
        
    with gr.Row():
        waterfall_plot = gr.Plot(label="Detailed Waterfall (Best Scenario)")
        roi_plot = gr.Plot(label="Return on Investment")
    
    # Set up the calculation trigger
    inputs = [
        total_shares, your_options, strike_price,
        seed_shares, seed_capital, seed_multiple, seed_participating,
        series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
        series_b_shares, series_b_capital, series_b_multiple, series_b_participating,
        exit_scenario_1, scenario_1_name,
        exit_scenario_2, scenario_2_name,
        exit_scenario_3, scenario_3_name,
        exit_scenario_4, scenario_4_name,
        exit_scenario_5, scenario_5_name
    ]
    
    outputs = [results_text, comparison_plot, waterfall_plot, roi_plot]
    
    calculate_btn.click(calculate_equity_value, inputs=inputs, outputs=outputs)
    
    # Auto-calculate on input changes
    for input_component in inputs:
        input_component.change(calculate_equity_value, inputs=inputs, outputs=outputs)
    
    gr.Markdown("""
    ## 📚 How to Use This Calculator
    
    ### 🎯 Multi-Scenario Analysis
    **This is where the real value lies!** Instead of guessing one exit value, define multiple realistic scenarios:
    - **Conservative**: What if growth is slower than expected?
    - **Base Case**: Most likely scenario based on current trajectory
    - **Optimistic**: If everything goes right
    - **Moon Shot**: Best case scenario (10x+ returns)
    
    ### 📊 Key Outputs
    1. **Comparison Table**: Side-by-side option values across all scenarios
    2. **Visual Charts**: See how your returns scale with different exits
    3. **ROI Analysis**: Understand your return on investment potential
    4. **Detailed Waterfall**: How liquidation preferences affect distributions
    
    ### 💡 Decision Framework
    Use this to evaluate:
    - **Risk vs Reward**: How much upside vs downside?
    - **Opportunity Cost**: Compare to other job offers or investments
    - **Negotiation Power**: Understanding your equity's potential value range
    
    ### 🔧 Liquidation Preferences
    - **Non-Participating**: Investors choose preference OR convert to common (better for employees)
    - **Participating**: Investors get preference AND share upside (worse for employees)
    - **Multiples**: How many times their investment investors get back first
    
    **Pro Tip**: Try toggling participating preferred on/off to see the dramatic impact on your equity value!
    """)

if __name__ == "__main__":
    app.launch()