"""
Complete LangGraph workflow integration example.

Shows how to build a complete multi-modal agent workflow using LangGraph
with task routing and agent execution.
"""

import logging
from typing import Any

from graph.state import AgentStatePydantic, TaskType
from graph.workflow import TaskRouter, route_task, execute_task, create_workflow


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Simple Sequential Workflow
# ============================================================================

def example_sequential_workflow():
    """Example: Sequential task routing and execution."""
    print("\n=== Sequential Workflow Example ===")
    
    # This would normally be done with LangGraph
    # Here we simulate the workflow manually
    
    router = TaskRouter()
    
    # Test inputs
    test_cases = [
        ("Summarize this article about AI\n" + "AI is transforming the world."),
        ("What's your opinion on AI?"),
        ("Generate an image of a sunset"),
    ]
    
    for user_input in test_cases:
        print(f"\nProcessing: {user_input[:50]}...")
        
        # Create state
        state = AgentStatePydantic(user_input=user_input)
        
        # Route task
        task_type = router.route(user_input)
        state.task_type = task_type
        state.add_message(f"Router: Routed to {task_type.value}")
        
        print(f"  → Task Type: {task_type.value}")
        print(f"  → State: {state.is_error()=}, messages={len(state.messages)}")


# ============================================================================
# Example 2: Branching Workflow
# ============================================================================

def example_branching_workflow():
    """Example: Branching based on task type."""
    print("\n=== Branching Workflow Example ===")
    
    router = TaskRouter()
    
    def process_branching(user_input: str, image: bytes = None):
        """Process input with branching."""
        state = AgentStatePydantic(user_input=user_input, image=image)
        state.add_message("Workflow: Starting")
        
        # Route
        task_type = router.route(user_input, image)
        state.task_type = task_type
        state.add_message(f"Router: Branching to {task_type.value}")
        
        # Branch execution
        if task_type == TaskType.SUMMARIZATION:
            state.add_message("Summarizer: Extracting key points...")
            state.set_result({"summary": "Key points extracted"})
            
        elif task_type == TaskType.STANCE_DETECTION:
            state.add_message("Stance Detector: Analyzing sentiment...")
            state.set_result({"stance": "positive", "confidence": 0.95})
            
        elif task_type == TaskType.IMAGE_GENERATION:
            state.add_message("Image Generator: Creating image...")
            state.set_result({"image_generated": True})
            
        elif task_type == TaskType.IMAGE_ANALYSIS:
            if not image:
                state.set_error("Image required for analysis")
            else:
                state.add_message("Image Analyzer: Analyzing...")
                state.set_result({"labels": ["dog", "animal"]})
        
        state.add_message("Workflow: Complete")
        return state
    
    # Test cases
    cases = [
        ("Summarize this", None),
        ("What do you think?", None),
        ("Create an image", None),
        ("Analyze this", b"image_data"),
    ]
    
    for user_input, image in cases:
        state = process_branching(user_input, image)
        print(f"\nInput: {user_input}")
        print(f"Result: {state.result}")
        print(f"Messages: {len(state.messages)} steps")


# ============================================================================
# Example 3: Error Handling in Workflow
# ============================================================================

def example_error_handling_workflow():
    """Example: Error handling and recovery."""
    print("\n=== Error Handling Workflow ===")
    
    router = TaskRouter()
    
    def process_with_errors(user_input: str, image: bytes = None):
        """Process with error handling."""
        state = AgentStatePydantic(user_input=user_input, image=image)
        
        try:
            # Route task
            task_type = router.route(user_input, image)
            state.task_type = task_type
            state.add_message(f"Router: {task_type.value}")
            
            # Check invalid conditions
            if task_type == TaskType.IMAGE_ANALYSIS and not image:
                raise ValueError("Image analysis requires image input")
            
            if not user_input or len(user_input.strip()) < 1:
                raise ValueError("Empty input")
            
            # Simulate successful execution
            state.set_result({"status": "success"})
            state.add_message("Executor: Task completed")
            
        except ValueError as e:
            state.set_error(f"Validation error: {str(e)}")
            state.add_message(f"Error handler: {str(e)}")
            
        except Exception as e:
            state.set_error(f"Unexpected error: {str(e)}")
            state.add_message(f"Error handler: Unexpected error")
        
        return state
    
    # Test cases with potential errors
    cases = [
        ("Valid input", None, True),
        ("", None, False),  # Empty input
        ("Analyze image", None, False),  # Missing image
        ("Summarize this", None, True),  # Valid
    ]
    
    for user_input, image, should_succeed in cases:
        state = process_with_errors(user_input, image)
        print(f"\nInput: '{user_input}'")
        print(f"Error: {state.is_error()}")
        print(f"Expected success: {should_succeed}, Actual: {not state.is_error()}")


# ============================================================================
# Example 4: Multi-Turn Workflow
# ============================================================================

def example_multi_turn_workflow():
    """Example: Multi-turn conversation workflow."""
    print("\n=== Multi-Turn Workflow ===")
    
    router = TaskRouter()
    
    # Simulate multi-turn conversation
    turns = [
        ("Can you analyze this for me?", None),
        ("Actually, summarize it instead", None),
        ("No wait, tell me your opinion", None),
    ]
    
    state = AgentStatePydantic(user_input="Starting conversation")
    state.add_message("User: Hello, I need help")
    state.add_message("Agent: How can I assist?")
    
    for user_input, image in turns:
        print(f"\nTurn: {user_input}")
        
        # Update state for new turn
        state.user_input = user_input
        
        # Route
        task_type = router.route(user_input, image)
        state.task_type = task_type
        state.add_message(f"User: {user_input}")
        state.add_message(f"Agent: Processing as {task_type.value}")
        
        print(f"  Task: {task_type.value}")
    
    print(f"\nConversation history ({len(state.messages)} messages):")
    for i, msg in enumerate(state.messages, 1):
        print(f"  {i}. {msg}")


# ============================================================================
# Example 5: Custom Router for Specific Domain
# ============================================================================

def example_domain_specific_router():
    """Example: Domain-specific router customization."""
    print("\n=== Domain-Specific Router ===")
    
    # Create medical domain router
    medical_router = TaskRouter(
        rules={
            TaskType.STANCE_DETECTION: {
                "keywords": ["symptom", "sign", "diagnosis", "treatment", "prognosis"],
                "priority": 1
            },
            TaskType.SUMMARIZATION: {
                "keywords": ["summarize", "brief", "overview", "abstract"],
                "priority": 2
            }
        },
        default_task=TaskType.STANCE_DETECTION
    )
    
    medical_inputs = [
        "What are the symptoms of the disease?",
        "Summarize the medical report",
        "What treatment do you recommend?",
    ]
    
    print("Medical Domain Routing:\n")
    for text in medical_inputs:
        task = medical_router.route(text)
        analysis = medical_router.analyze(text)
        
        print(f"Input: {text}")
        print(f"  Task: {task.value}")
        if analysis['matching_rules']:
            print(f"  Matched rules: {list(analysis['matching_rules'].keys())}")
        print()


# ============================================================================
# Example 6: Workflow with Message Accumulation
# ============================================================================

def example_message_accumulation():
    """Example: Accumulating messages throughout workflow."""
    print("\n=== Message Accumulation Workflow ===")
    
    router = TaskRouter()
    state = AgentStatePydantic(user_input="Tell me your opinion about AI")
    
    # Workflow phases
    state.add_message("Phase 1: Validating input...")
    print(f"Messages: {len(state.messages)}")
    
    state.add_message("Phase 2: Routing task...")
    task_type = router.route(state.user_input)
    state.task_type = task_type
    state.add_message(f"Phase 2 Result: Routed to {task_type.value}")
    print(f"Messages: {len(state.messages)}")
    
    state.add_message("Phase 3: Loading model...")
    state.add_message("Phase 3: Model loaded")
    print(f"Messages: {len(state.messages)}")
    
    state.add_message("Phase 4: Executing task...")
    state.set_result({"result": "Analysis complete"})
    state.add_message("Phase 4: Task executed")
    print(f"Messages: {len(state.messages)}")
    
    state.add_message("Phase 5: Formatting response...")
    state.add_message("Workflow complete!")
    print(f"Messages: {len(state.messages)}")
    
    print("\nFinal message history:")
    for i, msg in enumerate(state.messages, 1):
        print(f"  {i:2d}. {msg}")


# ============================================================================
# Example 7: Router Analysis in Workflow
# ============================================================================

def example_router_analysis_in_workflow():
    """Example: Using router analysis for debugging."""
    print("\n=== Router Analysis in Workflow ===")
    
    router = TaskRouter()
    
    # Ambiguous input
    input_text = "Generate a summary of images with analysis"
    
    analysis = router.analyze(input_text)
    
    print(f"Input: '{input_text}'")
    print(f"\nRouter Analysis:")
    print(f"  Final decision: {analysis['task_type']}")
    print(f"  Text length: {analysis['text_length']}")
    print(f"  Fallback used: {analysis['default_fallback']}")
    
    if analysis['matching_rules']:
        print(f"\n  All matching rules:")
        sorted_rules = sorted(
            analysis['matching_rules'].items(),
            key=lambda x: (-x[1]['score'], x[1]['priority'])
        )
        for task, details in sorted_rules:
            print(f"    {task}: score={details['score']}, priority={details['priority']}")


if __name__ == "__main__":
    print("LangGraph Workflow Integration Examples")
    print("=" * 70)
    
    # Run all examples
    example_sequential_workflow()
    example_branching_workflow()
    example_error_handling_workflow()
    example_multi_turn_workflow()
    example_domain_specific_router()
    example_message_accumulation()
    example_router_analysis_in_workflow()
    
    print("\n" + "=" * 70)
    print("All workflow examples completed!")
