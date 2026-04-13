"""
Main application entry point.
Orchestrates the multi-modal agent workflow.
"""

from config import get_config
from graph.workflow import create_workflow


def main():
    """Initialize and run the main application."""
    config = get_config()
    workflow = create_workflow(config)
    
    # Add your main logic here
    print("Multi-Modal Agent Started")


if __name__ == "__main__":
    main()
