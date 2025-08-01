"""
Chart generation for equity analysis visualization
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional
from models import ScenarioResult, CapTable, EquityCalculator


class EquityCharts:
    """Handles all chart generation for equity analysis"""
    
    @staticmethod
    def create_multi_scenario_comparison(results: List[ScenarioResult]) -> Optional[go.Figure]:
        """Create comparison chart showing option values and exit valuations"""
        if not results:
            return None
        
        scenario_names = [r.scenario_name for r in results]
        option_values = [r.option_value for r in results]
        exit_values = [r.exit_valuation for r in results]
        
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
        if option_values:
            fig.update_yaxes(title_text="Your Option Value ($)", row=1, col=1, range=[0, max(option_values) * 1.15])
        if exit_values:
            fig.update_yaxes(title_text="Company Valuation ($)", row=2, col=1, range=[0, max(exit_values) * 1.15])
        
        return fig
    
    @staticmethod
    def create_liquidation_waterfall(
        cap_table: CapTable, 
        exit_valuation: float, 
        scenario_name: str = "Best Scenario"
    ) -> go.Figure:
        """Create detailed liquidation waterfall chart for a specific exit value"""
        
        calculator = EquityCalculator(cap_table)
        remaining_proceeds = exit_valuation
        waterfall_data = []
        participating_shareholders = []
        
        # Sort funding rounds (newest first for liquidation preferences)
        sorted_rounds = sorted(cap_table.funding_rounds, 
                             key=lambda x: ['Seed', 'Series A', 'Series B', 'Series C'].index(x.name) 
                             if x.name in ['Seed', 'Series A', 'Series B', 'Series C'] else 999, 
                             reverse=True)
        
        # Phase 1: Liquidation preferences
        for round in sorted_rounds:
            if round.shares_issued > 0 and round.capital_raised > 0:
                preference_payout = min(remaining_proceeds, round.liquidation_preference)
                remaining_proceeds -= preference_payout
                
                if round.is_participating:
                    participating_shareholders.append({
                        'round': round.name, 
                        'shares': round.shares_issued
                    })
                
                waterfall_data.append({
                    'Round': f'{round.name} (Pref)',
                    'Payout': preference_payout,
                    'Type': 'Preference'
                })
        
        # Phase 2: Participating preferred and common distribution
        participating_preferred_shares = sum(p['shares'] for p in participating_shareholders)
        total_participating_shares = cap_table.common_shares + participating_preferred_shares
        
        if total_participating_shares > 0:
            price_per_share = remaining_proceeds / total_participating_shares
            common_proceeds = price_per_share * cap_table.common_shares
            
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
            'Preference': '#FF6B6B',      # Red for liquidation preferences
            'Participation': '#4ECDC4',    # Teal for participating preferred
            'Common': '#F7DC6F'           # Yellow for common stock
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
    
    @staticmethod
    def create_roi_analysis(results: List[ScenarioResult], investment_cost: float) -> Optional[go.Figure]:
        """Create ROI analysis chart"""
        if not results:
            return None
        
        roi_data = []
        for result in results:
            roi = result.roi_percentage(investment_cost)
            # Cap very high ROI for display purposes
            display_roi = roi if roi < 999999 else 999999
            roi_data.append({
                'scenario': result.scenario_name,
                'roi': display_roi,
                'absolute_gain': result.option_value - investment_cost
            })
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[d['scenario'] for d in roi_data],
            y=[d['roi'] for d in roi_data],
            name="ROI %",
            marker_color='#28A745',
            text=[f"{d['roi']:.0f}%" if d['roi'] < 999999 else "∞%" for d in roi_data],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Return on Investment (ROI) by Scenario",
            xaxis_title="Scenario",
            yaxis_title="ROI (%)",
            height=450,
            margin=dict(t=60, b=50, l=60, r=50)
        )
        
        return fig


def format_results_table(results: List[ScenarioResult]) -> str:
    """Format scenario results as a markdown table"""
    if not results:
        return "No scenarios to display"
    
    table = "## 📊 Exit Scenario Comparison\n\n"
    table += "| Scenario | Exit Value | Your Option Value | Value per Option | Common Proceeds |\n"
    table += "|----------|------------|-------------------|------------------|------------------|\n"
    
    for result in results:
        table += f"| **{result.scenario_name}** | ${result.exit_valuation:,.0f} | "
        table += f"${result.option_value:,.2f} | ${result.value_per_option:.4f} | "
        table += f"${result.common_proceeds:,.0f} |\n"
    
    return table


def format_equity_summary(summary: dict, results: List[ScenarioResult]) -> str:
    """Format complete equity analysis summary"""
    
    results_table = format_results_table(results)
    
    summary_text = f"""
## 💰 Your Equity Summary

**Your Option Grant:** {summary['your_options']:,} options
**Strike Price:** ${summary['strike_price']:.4f} per share
**Your Equity Stake:** {summary['your_equity_percentage']:.3f}%

{results_table}

## 🏗️ Cap Table Summary

**Total Shares:** {summary['total_shares']:,}
**Common Shares:** {summary['common_shares']:,}
**Preferred Shares:** {summary['preferred_shares']:,}

**Liquidation Terms:** {' | '.join(summary['participating_status']) if summary['participating_status'] else 'No preferred rounds'}

**Break-even Price per Share:** ${summary['break_even_price']:.4f}
*(Price needed for your options to have positive value)*
"""
    
    return summary_text