---
title: Startup Equity Calculator
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# Startup Equity Calculator

A comprehensive tool to calculate and compare the value of startup stock options across multiple exit scenarios.

## 🌐 Live App

**Try it now:** [https://huggingface.co/spaces/akshay7/startup-equity-calculator](https://huggingface.co/spaces/akshay7/startup-equity-calculator)

*The app is hosted on Hugging Face Spaces and is free to use.*

## Features

- 📊 **Multi-scenario analysis** - Compare conservative, base case, and optimistic exits
- ⚖️ **Liquidation preferences** - Handles participating vs non-participating preferred stock
- 📈 **Visual analytics** - Interactive charts showing option values and ROI
- 🧮 **Detailed calculations** - Liquidation waterfall showing how proceeds are distributed

## How to Use

1. **Enter your cap table details**: Total shares, your options, strike price
2. **Add funding rounds**: Include any Seed, Series A, or Series B rounds  
3. **Define exit scenarios**: Create multiple scenarios to compare outcomes
4. **Analyze results**: Review the comparison table and visual charts

## Example Use Cases

- **Job Negotiation**: Compare equity packages from different startups
- **Career Planning**: Understand the risk/reward profile of your options
- **Investment Decisions**: Evaluate whether to exercise options early
- **Financial Planning**: Model different exit scenarios for personal budgeting

## Technical Details

- **Backend**: Python with clean data models and robust calculations
- **Frontend**: Gradio for interactive web interface
- **Charts**: Plotly for professional visualizations
- **Hosting**: Hugging Face Spaces (free tier)

## Disclaimer

This tool is for educational purposes only. Consult with financial and tax professionals before making investment decisions. The calculations are simplified models and may not reflect all complexities of real equity structures.