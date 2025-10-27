import matplotlib.pyplot as plt
import numpy as np
import os

def create_performance_chart():
    """
    Generates and saves a grouped bar chart comparing agent performance
    based on the test results.
    """
    
    # --- Data from the Report ---
    # The categories for our agent models
    agents = ['AOSS v1 (8B RAG)', 'Monolithic (70B)', 'AOSS v2 (8B RAG)']
    
    # Data for each category, corresponding to the agents list
    plan_results = {
        'Correct Plan': [2, 4, 4],
        'Incorrect Plan': [5, 2, 3],
        'Critical Failure': [0, 1, 0]
    }
    
    # Colors for each category
    colors = {
        'Correct Plan': '#4CAF50',  # Green
        'Incorrect Plan': '#FFC107', # Amber/Orange
        'Critical Failure': '#F44336' # Red
    }
    
    # --- Chart Setup ---
    x = np.arange(len(agents))  # The label locations
    width = 0.25  # The width of the bars
    multiplier = 0
    
    fig, ax = plt.subplots(layout='constrained', figsize=(10, 6))
    
    # Iterate over the result types and plot them
    for attribute, measurement in plan_results.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, label=attribute, color=colors[attribute])
        ax.bar_label(rects, padding=3, fmt='%d')
        multiplier += 1
        
    # --- Add labels, title, and legend ---
    ax.set_title('Agent Plan Correctness by Model Version (Total 7 SRE and Sys Admin Tests)', fontsize=16, pad=20)
    ax.set_ylabel('Number of Plans', fontsize=12)
    ax.set_xticks(x + width, agents, fontsize=11)
    ax.legend(loc='upper left', ncols=3, fontsize=10)
    
    # Set Y-axis to show integer values since we're counting plans
    ax.set_ylim(0, 8)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    # Add a subtle grid for readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # --- Save and Show the Chart ---
    chart_filename = 'agent_performance_chart.png'
    try:
        plt.savefig(chart_filename, dpi=300)
        print(f"Chart successfully saved as: {os.path.abspath(chart_filename)}")
    except Exception as e:
        print(f"Error saving chart: {e}")
        
    plt.show()

if __name__ == '__main__':
    # Ensure matplotlib is installed
    try:
        import matplotlib
    except ImportError:
        print("Matplotlib is not installed. Please install it with 'pip install matplotlib'")
        exit()
        
    create_performance_chart()
