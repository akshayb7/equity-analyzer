"""
Gradio interface components for the equity calculator
"""
import gradio as gr
from typing import Tuple, List, Optional
from models import create_cap_table, EquityCalculator, ExitScenario
from charts import EquityCharts, format_equity_summary


def create_cap_table_inputs():
    """Create the cap table input components"""
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
    
    return [
        total_shares, your_options, strike_price,
        seed_shares, seed_capital, seed_multiple, seed_participating,
        series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
        series_b_shares, series_b_capital, series_b_multiple, series_b_participating
    ]


def create_scenario_inputs():
    """Create the exit scenario input components"""
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
    
    return [
        exit_scenario_1, scenario_1_name,
        exit_scenario_2, scenario_2_name,
        exit_scenario_3, scenario_3_name,
        exit_scenario_4, scenario_4_name,
        exit_scenario_5, scenario_5_name,
        calculate_btn, results_text
    ]


def create_output_components():
    """Create the output chart components"""
    with gr.Row():
        comparison_plot = gr.Plot(label="Multi-Scenario Comparison")
        
    with gr.Row():
        waterfall_plot = gr.Plot(label="Detailed Waterfall (Best Scenario)")
        roi_plot = gr.Plot(label="Return on Investment")
    
    return [comparison_plot, waterfall_plot, roi_plot]


def process_inputs(
    # Cap table inputs
    total_shares, your_options, strike_price,
    seed_shares, seed_capital, seed_multiple, seed_participating,
    series_a_shares, series_a_capital, series_a_multiple, series_a_participating,
    series_b_shares, series_b_capital, series_b_multiple, series_b_participating,
    # Scenario inputs
    exit_scenario_1, scenario_1_name,
    exit_scenario_2, scenario_2_name,
    exit_scenario_3, scenario_3_name,
    exit_scenario_4, scenario_4_name,
    exit_scenario_5, scenario_5_name
) -> Tuple[str, Optional[gr.Plot], Optional[gr.Plot], Optional[gr.Plot]]:
    """Process all inputs and return formatted results and charts"""
    
    # Handle None values with defaults
    total_shares = total_shares or 10000000
    your_options = your_options or 0
    strike_price = strike_price or 0.10
    
    # Validate inputs
    if total_shares <= 0:
        return "Invalid inputs - please check your values", None, None, None
    
    # Create cap table
    try:
        cap_table = create_cap_table(
            total_shares=total_shares,
            your_options=your_options,
            strike_price=strike_price,
            seed_shares=seed_shares or 0,
            seed_capital=seed_capital or 0,
            seed_multiple=seed_multiple or 1.0,
            seed_participating=seed_participating or False,
            series_a_shares=series_a_shares or 0,
            series_a_capital=series_a_capital or 0,
            series_a_multiple=series_a_multiple or 1.0,
            series_a_participating=series_a_participating or False,       
            series_b_shares=series_b_shares or 0,
            series_b_capital=series_b_capital or 0,
            series_b_multiple=series_b_multiple or 1.0,
            series_b_participating=series_b_participating or False
        )
    except Exception as e:
        return f"Error creating cap table: {str(e)}", None, None, None
    
    # Create scenarios
    scenarios = []
    scenario_data = [
        (exit_scenario_1 or 0, scenario_1_name or "Scenario 1"),
        (exit_scenario_2 or 0, scenario_2_name or "Scenario 2"),
        (exit_scenario_3 or 0, scenario_3_name or "Scenario 3"),
        (exit_scenario_4 or 0, scenario_4_name or "Scenario 4"),
        (exit_scenario_5 or 0, scenario_5_name or "Scenario 5")
    ]
    
    for exit_val, name in scenario_data:
        if exit_val > 0:
            scenarios.append(ExitScenario(name=name, exit_valuation=exit_val))
    
    if not scenarios:
        return "Please enter at least one exit scenario with a positive value", None, None, None
    
    # Calculate results
    calculator = EquityCalculator(cap_table)
    try:
        results = calculator.calculate_multiple_scenarios(scenarios)
        summary = calculator.get_liquidation_summary()
    except Exception as e:
        return f"Error calculating results: {str(e)}", None, None, None
    
    if not results:
        return "No valid scenarios to calculate", None, None, None
    
    # Generate charts
    charts = EquityCharts()
    
    try:
        # Multi-scenario comparison
        comparison_chart = charts.create_multi_scenario_comparison(results)
        
        # Detailed waterfall for best scenario
        best_result = max(results, key=lambda x: x.option_value)
        waterfall_chart = charts.create_liquidation_waterfall(
            cap_table, 
            best_result.exit_valuation, 
            best_result.scenario_name
        )
        
        # ROI analysis
        investment_cost = cap_table.your_options * cap_table.strike_price
        roi_chart = charts.create_roi_analysis(results, investment_cost)
        
    except Exception as e:
        return f"Error generating charts: {str(e)}", None, None, None
    
    # Format summary
    try:
        summary_text = format_equity_summary(summary, results)
    except Exception as e:
        return f"Error formatting summary: {str(e)}", comparison_chart, waterfall_chart, roi_chart
    
    return summary_text, comparison_chart, waterfall_chart, roi_chart


def create_help_section():
    """Create the help/documentation section"""
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