"""
Main application file - Startup Equity Calculator
Entry point for the Gradio web application
"""
import gradio as gr
from interface import (
    create_cap_table_inputs, 
    create_scenario_inputs, 
    create_output_components,
    process_inputs,
    create_help_section
)


def create_app():
    """Create and configure the Gradio application"""
    
    with gr.Blocks(title="Startup Equity Calculator", theme=gr.themes.Soft()) as app:
        
        # Header
        gr.Markdown("# 🚀 Startup Equity Calculator")
        gr.Markdown("Calculate the value of your stock options based on cap table structure and liquidation preferences")
        
        # Main interface
        with gr.Row():
            # Left column: Cap table inputs
            cap_table_components = create_cap_table_inputs()
            
            # Right column: Scenario inputs and results
            scenario_components = create_scenario_inputs()
        
        # Output charts
        output_components = create_output_components()
        
        # Extract components for event handling
        calculate_btn = scenario_components[-2]  # Second to last component
        results_text = scenario_components[-1]   # Last component
        
        # All input components
        all_inputs = cap_table_components + scenario_components[:-2]  # Exclude button and results
        
        # All output components  
        all_outputs = [results_text] + output_components
        
        # Set up event handlers
        calculate_btn.click(
            process_inputs,
            inputs=all_inputs,
            outputs=all_outputs
        )
        
        # Auto-calculate on input changes (optional - can be enabled/disabled)
        for input_component in cap_table_components:
            input_component.change(
                process_inputs,
                inputs=all_inputs,
                outputs=all_outputs
            )
        
        # Help section
        create_help_section()
    
    return app


def main():
    """Main function to launch the application"""
    print("🚀 Starting Startup Equity Calculator...")
    print("📊 Loading models and interface...")
    
    try:
        app = create_app()
        print("✅ Application created successfully!")
        print("🌐 Launching web interface...")
        
        # Launch with custom settings
        app.launch(
            server_name="0.0.0.0",  # Allow external access
            server_port=7860,       # Default Gradio port
            share=False,            # Set to True to create public link
            debug=False,            # Set to True for development
            show_error=True         # Show detailed errors
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required modules (models.py, charts.py, interface.py) are in the same directory")
        
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        print("Check that all dependencies are installed: gradio, plotly, pandas")


if __name__ == "__main__":
    main()