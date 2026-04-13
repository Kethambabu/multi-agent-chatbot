"""
Examples demonstrating the use of state classes with LangGraph.

Shows how to use TypedDict, Pydantic, and legacy state classes
in a multi-modal AI workflow.
"""

from graph.state import (
    AgentStateDict,
    AgentStatePydantic,
    WorkflowState,
    TaskType
)


def example_typeddict_state():
    """Example: Using TypedDict state."""
    print("\n=== TypedDict State Example ===")
    
    # Create a state dict
    state: AgentStateDict = {
        "user_input": "Summarize this article about AI.",
        "image": None,
        "task_type": "summary",
        "messages": ["User: Please summarize the article"],
    }
    
    print(f"Task: {state['task_type']}")
    print(f"Input: {state['user_input']}")
    print(f"Messages: {state['messages']}")
    
    # Process task and update state
    state["result"] = "The article discusses the impact of AI on society..."
    state["updated_at"] = "2026-04-11T10:35:00"
    
    print(f"Result: {state['result']}")


def example_pydantic_state():
    """Example: Using Pydantic state with validation."""
    print("\n=== Pydantic State Example ===")
    
    # Create a Pydantic state
    state = AgentStatePydantic(
        user_input="Detect the stance of this review",
        task_type=TaskType.STANCE_DETECTION
    )
    
    print(f"Task: {state.task_type}")
    print(f"Input: {state.user_input}")
    print(f"Created: {state.created_at}")
    
    # Add messages
    state.add_message("User: Analyze stance")
    state.add_message("Agent: Processing...")
    
    # Set result
    state.set_result({
        "label": "positive",
        "score": 0.95,
        "all_scores": {
            "positive": 0.95,
            "negative": 0.03,
            "neutral": 0.02
        }
    })
    
    print(f"Messages: {state.messages}")
    print(f"Result: {state.result}")
    print(f"Is Error: {state.is_error()}")


def example_pydantic_validation():
    """Example: Pydantic validation in action."""
    print("\n=== Pydantic Validation ===")
    
    # Valid state
    try:
        state = AgentStatePydantic(
            user_input="Generate an image",
            task_type=TaskType.IMAGE_GENERATION
        )
        print(f"Valid state created: {state.user_input}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Invalid state: empty input
    try:
        state = AgentStatePydantic(
            user_input="",
            task_type=TaskType.IMAGE_ANALYSIS
        )
    except Exception as e:
        print(f"Validation error caught: {e}")
    
    # Invalid image: empty bytes
    try:
        state = AgentStatePydantic(
            user_input="Analyze image",
            image=b"",  # Empty image
            task_type=TaskType.IMAGE_ANALYSIS
        )
    except Exception as e:
        print(f"Image validation error caught: {e}")


def example_error_handling():
    """Example: Error handling with state."""
    print("\n=== Error Handling ===")
    
    # Create state
    state = AgentStatePydantic(
        user_input="Generate image of a fantasy landscape"
    )
    
    print(f"Initial state - Error: {state.is_error()}")
    
    # Simulate error
    state.set_error("API timeout: Model loading exceeded timeout")
    print(f"After error - Error: {state.is_error()}")
    print(f"Error message: {state.error}")
    
    # Clear error with new result
    state.set_result({"status": "completed"})
    print(f"After recovery - Error: {state.is_error()}")
    print(f"Result: {state.result}")


def example_workflow_state_legacy():
    """Example: Using legacy WorkflowState class."""
    print("\n=== Legacy WorkflowState ===")
    
    # Create state
    state = WorkflowState(
        user_input="Analyze this image",
        task_type="image_analysis"
    )
    
    print(f"Task: {state.task_type}")
    print(f"Input: {state.user_input}")
    
    # Add messages
    state.add_message("Starting image analysis...")
    state.add_message("Loading model...")
    
    # Set result
    state.set_result({
        "predictions": [
            {"label": "dog", "score": 0.92},
            {"label": "animal", "score": 0.07}
        ]
    })
    
    print(f"Messages: {len(state.messages)}")
    print(f"Result set: {state.result is not None}")
    print(f"State: {state}")


def example_langgraph_integration():
    """Example: How to use state with LangGraph nodes."""
    print("\n=== LangGraph Integration Pattern ===")
    
    # Define a node function that works with Pydantic state
    def summarization_node(state: AgentStatePydantic) -> AgentStatePydantic:
        """Node that performs summarization task."""
        state.add_message("Agent: Summarizing text...")
        
        try:
            # Simulate summarization
            summary = f"Summary of: {state.user_input[:50]}..."
            
            state.set_result({
                "summary": summary,
                "length": len(summary),
                "compression_ratio": 0.3
            })
            
            state.add_message(f"Agent: Summary complete")
            
        except Exception as e:
            state.set_error(f"Summarization failed: {str(e)}")
        
        return state
    
    # Use node with state
    state = AgentStatePydantic(
        user_input="AI is transforming industries including healthcare, finance, and education.",
        task_type=TaskType.SUMMARIZATION
    )
    
    # Execute node
    result_state = summarization_node(state)
    
    print(f"Task: {result_state.task_type}")
    print(f"Messages: {result_state.messages}")
    print(f"Result: {result_state.result}")


def example_state_serialization():
    """Example: Serializing state to JSON."""
    print("\n=== State Serialization ===")
    
    state = AgentStatePydantic(
        user_input="Test input",
        task_type=TaskType.IMAGE_GENERATION
    )
    
    state.set_result({"image_size": 768})
    
    # Convert to dict (for JSON)
    state_dict = state.to_dict()
    print(f"As dict: {state_dict}")
    
    # JSON serialization
    import json
    state_json = json.dumps(state_dict, indent=2)
    print(f"\nAs JSON:\n{state_json}")
    
    # Recreate from dict
    state_2 = AgentStatePydantic(**state_dict)
    print(f"\nRecreated from dict: {state_2.user_input}")


def example_message_history():
    """Example: Managing conversation history."""
    print("\n=== Message History ===")
    
    state = AgentStatePydantic(
        user_input="Can you help me?"
    )
    
    # Simulate a multi-turn conversation
    messages = [
        "User: Can you help me summarize this paper?",
        "Agent: I'll summarize it for you. What's the topic?",
        "User: It's about machine learning.",
        "Agent: Summarizing machine learning paper...",
        "Agent: Here's the summary..."
    ]
    
    for msg in messages:
        state.add_message(msg)
        print(f"Message {len(state.messages)}: {msg[:50]}...")
    
    print(f"\nTotal messages: {len(state.messages)}")
    print(f"Last updated: {state.updated_at}")


def example_task_type_usage():
    """Example: Working with different task types."""
    print("\n=== Task Type Usage ===")
    
    # Create states for different tasks
    tasks = [
        ("Summarize this article", TaskType.SUMMARIZATION),
        ("What's the sentiment?", TaskType.STANCE_DETECTION),
        ("Generate a sunset image", TaskType.IMAGE_GENERATION),
        ("Analyze this photo", TaskType.IMAGE_ANALYSIS),
    ]
    
    for input_text, task_type in tasks:
        state = AgentStatePydantic(
            user_input=input_text,
            task_type=task_type
        )
        
        print(f"Task: {state.task_type:15} | Input: {state.user_input}")


def example_comparison():
    """Example: Comparing TypedDict vs Pydantic state."""
    print("\n=== TypedDict vs Pydantic Comparison ===")
    
    print("\nTypedDict (Lightweight):")
    typeddict_state: AgentStateDict = {
        "user_input": "Test",
        "task_type": "summary",
        "messages": [],
        "created_at": "2026-04-11T10:00:00"
    }
    print(f"  - No validation overhead")
    print(f"  - Simple dictionary access: {typeddict_state.get('user_input')}")
    print(f"  - Good for simple workflows")
    
    print("\nPydantic (Full Featured):")
    pydantic_state = AgentStatePydantic(user_input="Test")
    print(f"  - Built-in validation")
    print(f"  - Type hints with IDE support")
    print(f"  - Helper methods: add_message(), set_result(), etc.")
    print(f"  - Automatic serialization")
    print(f"  - Better for complex workflows")


if __name__ == "__main__":
    print("LangGraph State Management Examples")
    print("=" * 60)
    
    # Run examples
    example_typeddict_state()
    example_pydantic_state()
    example_pydantic_validation()
    example_error_handling()
    example_workflow_state_legacy()
    example_langgraph_integration()
    example_state_serialization()
    example_message_history()
    example_task_type_usage()
    example_comparison()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
