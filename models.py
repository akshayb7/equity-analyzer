"""
Data models and core equity calculation logic
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class FundingRound:
    """Represents a funding round (Seed, Series A, etc.)"""
    name: str
    shares_issued: int
    capital_raised: float
    liquidation_multiple: float
    is_participating: bool
    
    @property
    def liquidation_preference(self) -> float:
        """Total liquidation preference for this round"""
        return self.capital_raised * self.liquidation_multiple


@dataclass
class CapTable:
    """Represents the company's capitalization table"""
    total_shares: int
    your_options: int
    strike_price: float
    funding_rounds: List[FundingRound]
    
    @property
    def total_preferred_shares(self) -> int:
        """Total preferred shares across all rounds"""
        return sum(round.shares_issued for round in self.funding_rounds)
    
    @property
    def common_shares(self) -> int:
        """Total common shares available"""
        return self.total_shares - self.total_preferred_shares
    
    @property
    def your_equity_percentage(self) -> float:
        """Your equity percentage of total company"""
        return (self.your_options / self.total_shares) * 100 if self.total_shares > 0 else 0


@dataclass
class ExitScenario:
    """Represents an exit scenario with name and valuation"""
    name: str
    exit_valuation: float


@dataclass
class ScenarioResult:
    """Result of calculating equity value for one exit scenario"""
    scenario_name: str
    exit_valuation: float
    option_value: float
    price_per_share: float
    common_proceeds: float
    error: Optional[str] = None
    
    @property
    def value_per_option(self) -> float:
        """Value per individual option"""
        return self.price_per_share
    
    def roi_percentage(self, investment_cost: float) -> float:
        """Calculate ROI percentage"""
        if investment_cost <= 0:
            return float('inf') if self.option_value > 0 else 0
        return ((self.option_value - investment_cost) / investment_cost) * 100


class EquityCalculator:
    """Core equity calculation engine"""
    
    def __init__(self, cap_table: CapTable):
        self.cap_table = cap_table
    
    def calculate_scenario(self, exit_scenario: ExitScenario) -> ScenarioResult:
        """Calculate equity value for a single exit scenario"""
        
        if self.cap_table.common_shares <= 0:
            return ScenarioResult(
                scenario_name=exit_scenario.name,
                exit_valuation=exit_scenario.exit_valuation,
                option_value=0,
                price_per_share=0,
                common_proceeds=0,
                error='Preferred shares exceed total shares'
            )
        
        # Phase 1: Pay liquidation preferences (newest rounds first)
        remaining_proceeds = exit_scenario.exit_valuation
        participating_shareholders = []
        
        # Sort funding rounds by reverse order (newest first)
        sorted_rounds = sorted(self.cap_table.funding_rounds, 
                             key=lambda x: ['Seed', 'Series A', 'Series B', 'Series C'].index(x.name) 
                             if x.name in ['Seed', 'Series A', 'Series B', 'Series C'] else 999, 
                             reverse=True)
        
        preference_payouts = {}
        
        for round in sorted_rounds:
            if round.shares_issued > 0 and round.capital_raised > 0:
                preference_payout = min(remaining_proceeds, round.liquidation_preference)
                remaining_proceeds -= preference_payout
                preference_payouts[round.name] = preference_payout
                
                if round.is_participating:
                    participating_shareholders.append({
                        'round': round.name,
                        'shares': round.shares_issued
                    })
        
        # Phase 2: Handle non-participating conversions
        participating_preferred_shares = sum(p['shares'] for p in participating_shareholders)
        total_participating_shares = self.cap_table.common_shares + participating_preferred_shares
        
        # Check if non-participating preferred should convert
        for round in sorted_rounds:
            if (round.shares_issued > 0 and round.capital_raised > 0 
                and not round.is_participating):
                
                # Calculate conversion value vs preference value
                conversion_value = (round.shares_issued / self.cap_table.total_shares) * exit_scenario.exit_valuation
                preference_value = preference_payouts.get(round.name, 0)
                
                if conversion_value > preference_value:
                    # They convert - add back their preference and include in common distribution
                    remaining_proceeds += preference_value
                    total_participating_shares += round.shares_issued
        
        # Phase 3: Final distribution to common + participating preferred
        if total_participating_shares > 0:
            price_per_participating_share = remaining_proceeds / total_participating_shares
            common_proceeds = price_per_participating_share * self.cap_table.common_shares
        else:
            common_proceeds = remaining_proceeds
        
        # Calculate option value
        price_per_common_share = common_proceeds / self.cap_table.common_shares if self.cap_table.common_shares > 0 else 0
        option_value_per_share = max(0, price_per_common_share - self.cap_table.strike_price)
        total_option_value = option_value_per_share * self.cap_table.your_options
        
        return ScenarioResult(
            scenario_name=exit_scenario.name,
            exit_valuation=exit_scenario.exit_valuation,
            option_value=total_option_value,
            price_per_share=price_per_common_share,
            common_proceeds=common_proceeds
        )
    
    def calculate_multiple_scenarios(self, scenarios: List[ExitScenario]) -> List[ScenarioResult]:
        """Calculate equity value for multiple exit scenarios"""
        results = []
        for scenario in scenarios:
            if scenario.exit_valuation > 0:  # Only calculate positive exit values
                result = self.calculate_scenario(scenario)
                results.append(result)
        return results
    
    def get_liquidation_summary(self) -> Dict[str, Any]:
        """Get summary of liquidation terms"""
        participating_status = []
        for round in self.cap_table.funding_rounds:
            if round.shares_issued > 0:
                status = 'Participating' if round.is_participating else 'Non-Participating'
                participating_status.append(f"{round.name}: {status}")
        
        return {
            'total_shares': self.cap_table.total_shares,
            'common_shares': self.cap_table.common_shares,
            'preferred_shares': self.cap_table.total_preferred_shares,
            'your_options': self.cap_table.your_options,
            'your_equity_percentage': self.cap_table.your_equity_percentage,
            'strike_price': self.cap_table.strike_price,
            'participating_status': participating_status,
            'break_even_price': self.cap_table.strike_price
        }


def create_cap_table(
    total_shares: int, your_options: int, strike_price: float,
    seed_shares: int = 0, seed_capital: float = 0, seed_multiple: float = 1.0, seed_participating: bool = False,
    series_a_shares: int = 0, series_a_capital: float = 0, series_a_multiple: float = 1.0, series_a_participating: bool = False,
    series_b_shares: int = 0, series_b_capital: float = 0, series_b_multiple: float = 1.0, series_b_participating: bool = False
) -> CapTable:
    """Factory function to create a CapTable from individual parameters"""
    
    funding_rounds = []
    
    if seed_shares > 0 or seed_capital > 0:
        funding_rounds.append(FundingRound(
            name='Seed',
            shares_issued=seed_shares,
            capital_raised=seed_capital,
            liquidation_multiple=seed_multiple,
            is_participating=seed_participating
        ))
    
    if series_a_shares > 0 or series_a_capital > 0:
        funding_rounds.append(FundingRound(
            name='Series A',
            shares_issued=series_a_shares,
            capital_raised=series_a_capital,
            liquidation_multiple=series_a_multiple,
            is_participating=series_a_participating
        ))
    
    if series_b_shares > 0 or series_b_capital > 0:
        funding_rounds.append(FundingRound(
            name='Series B',
            shares_issued=series_b_shares,
            capital_raised=series_b_capital,
            liquidation_multiple=series_b_multiple,
            is_participating=series_b_participating
        ))
    
    return CapTable(
        total_shares=total_shares,
        your_options=your_options,
        strike_price=strike_price,
        funding_rounds=funding_rounds
    )