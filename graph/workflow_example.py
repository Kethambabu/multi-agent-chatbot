"""
Examples demonstrating the TaskRouter for multi-modal agent.

Shows how to use the router to intelligently determine task types
based on user input and image presence.
"""

import logging
from graph.workflow import TaskRouter
from graph.state import TaskType


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_basic_routing():
    """Example: Basic task routing with default rules."""
    print("\n=== Basic Task Routing ===")
    
    router = TaskRouter()
    
    # Test cases with expected routing
    test_cases = [
        ("Summarize this article about AI", TaskType.SUMMARIZATION),
        ("What do you think about climate change?", TaskType.STANCE_DETECTION),
        ("Generate an image of a sunset", TaskType.IMAGE_GENERATION),
        ("Describe what's in this image", TaskType.IMAGE_ANALYSIS),
    ]
    
    for text, expected in test_cases:
        result = router.route(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' → {result.value}")


def example_image_priority():
    """Example: Image takes priority over text."""
    print("\n=== Image Priority ===")
    
    router = TaskRouter()
    
    # Create dummy image bytes
    image_bytes = b"fake_image_data"
    
    # Even though text says "generate image", image analysis takes priority
    text = "Generate an image of this"
    
    result_no_image = router.route(text, image=None)
    result_with_image = router.route(text, image=image_bytes)
    
    print(f"Without image: '{text}' → {result_no_image.value}")
    print(f"With image:    '{text}' → {result_with_image.value}")


def example_keyword_matching():
    """Example: Keyword matching examples."""
    print("\n=== Keyword Matching ===")
    
    router = TaskRouter()
    
    keywords_by_task = {
        TaskType.SUMMARIZATION: ["summarize", "condense", "overview"],
        TaskType.STANCE_DETECTION: ["opinion", "sentiment", "believe"],
        TaskType.IMAGE_GENERATION: ["generate", "create", "draw"],
        TaskType.IMAGE_ANALYSIS: ["analyze", "describe", "identify"],
    }
    
    test_inputs = [
        "Can you summarize this?",
        "I think this is great",
        "Generate a beautiful landscape",
        "What is this animal?",
    ]
    
    for text in test_inputs:
        result = router.route(text)
        print(f"'{text}' → {result.value}")


def example_custom_rules():
    """Example: Adding custom routing rules."""
    print("\n=== Custom Routing Rules ===")
    
    router = TaskRouter()
    
    # Add custom keywords for stance detection
    router.add_rule(
        TaskType.STANCE_DETECTION,
        keywords=["agree", "disagree", "like", "dislike", "pro", "con"],
        priority=1
    )
    
    print("Added custom stance detection keywords")
    
    test_cases = [
        "I disagree with this proposal",
        "Do you like this approach?",
        "What's the pro and con?",
    ]
    
    for text in test_cases:
        result = router.route(text)
        print(f"  '{text}' → {result.value}")


def example_pattern_matching():
    """Example: Using regex patterns for matching."""
    print("\n=== Pattern Matching ===")
    
    router = TaskRouter()
    
    # Add pattern-based rules for image generation
    router.add_rule(
        TaskType.IMAGE_GENERATION,
        keywords=["generate", "create"],
        patterns=[
            r"generate\s+(?:an?\s+)?image",
            r"draw\s+(?:an?\s+)?picture",
            r"create\s+(?:an?\s+)?(?:image|art)"
        ],
        priority=2
    )
    
    print("Added pattern-based image generation rules\n")
    
    test_cases = [
        "Generate an image of a cat",
        "Draw a picture of mountains",
        "Create a beautiful artwork",
        "Make something artistic",
    ]
    
    for text in test_cases:
        result = router.route(text)
        print(f"  '{text}' → {result.value}")


def example_router_analysis():
    """Example: Detailed routing analysis."""
    print("\n=== Router Analysis ===")
    
    router = TaskRouter()
    
    text = "Can you summarize this article and tell me your opinion?"
    image = None
    
    # Analyze routing decision
    analysis = router.analyze(text, image)
    
    print(f"Input: '{text}'")
    print(f"\nAnalysis Results:")
    print(f"  Task Type: {analysis['task_type']}")
    print(f"  Has Image: {analysis['has_image']}")
    print(f"  Text Length: {analysis['text_length']}")
    print(f"  Default Fallback: {analysis['default_fallback']}")
    
    if analysis['matching_rules']:
        print(f"\nMatching Rules:")
        for task, details in analysis['matching_rules'].items():
            print(f"  {task}:")
            print(f"    Score: {details['score']}")
            print(f"    Priority: {details['priority']}")
            if details['matched_keywords']:
                print(f"    Keywords: {', '.join(details['matched_keywords'])}")


def example_ambiguous_input():
    """Example: Handling ambiguous input."""
    print("\n=== Ambiguous Input ===")
    
    router = TaskRouter()
    
    # This input matches multiple rules
    ambiguous = "Generate a summary of images"
    
    analysis = router.analyze(ambiguous)
    
    print(f"Ambiguous input: '{ambiguous}'\n")
    print(f"Final decision: {analysis['task_type'].upper()}")
    print(f"\nAll matching rules (by score):")
    
    for task, details in sorted(
        analysis['matching_rules'].items(),
        key=lambda x: (-x[1]['score'], x[1]['priority'])
    ):
        print(f"  {task}: score={details['score']}, priority={details['priority']}")


def example_default_fallback():
    """Example: Default fallback for unmatched input."""
    print("\n=== Default Fallback ===")
    
    # Create router with STANCE_DETECTION as default
    router = TaskRouter(
        default_task=TaskType.STANCE_DETECTION
    )
    
    # Input that doesn't match any rules
    generic_input = "Hello, how are you?"
    
    result = router.route(generic_input)
    analysis = router.analyze(generic_input)
    
    print(f"Input: '{generic_input}'")
    print(f"Result: {result.value}")
    print(f"Used default fallback: {analysis['default_fallback']}")


def example_case_insensitive():
    """Example: Case-insensitive routing."""
    print("\n=== Case Insensitive Routing ===")
    
    router = TaskRouter()
    
    test_cases = [
        "SUMMARIZE THIS TEXT",
        "Summarize this text",
        "summarize this text",
        "SuMmArIzE tHiS tExT",
    ]
    
    print("Testing case insensitivity:\n")
    for text in test_cases:
        result = router.route(text)
        print(f"  '{text}' → {result.value}")


def example_priority_resolution():
    """Example: Priority-based rule resolution."""
    print("\n=== Priority Resolution ===")
    
    router = TaskRouter()
    
    # Input that matches multiple rules
    text = "Generate a summary image"
    
    # Check what rules match
    analysis = router.analyze(text)
    
    print(f"Input: '{text}'\n")
    print("Matching rules (sorted by priority):")
    
    for task, details in sorted(
        analysis['matching_rules'].items(),
        key=lambda x: (x[1]['priority'], -x[1]['score'])
    ):
        print(f"  {task}: priority={details['priority']}, score={details['score']}")
    
    print(f"\nWinner: {analysis['task_type']}")


def example_batch_routing():
    """Example: Batch routing multiple inputs."""
    print("\n=== Batch Routing ===")
    
    router = TaskRouter()
    
    inputs = [
        ("Summarize the news", None),
        ("What do you think?", None),
        ("Create a poster", None),
        ("Analyze this", b"dummy_image"),
        ("Tell me about this photo", b"dummy_image"),
    ]
    
    print("Batch routing results:\n")
    results = []
    
    for text, image in inputs:
        task_type = router.route(text, image)
        has_image = "✓" if image else " "
        results.append((text, task_type.value, has_image))
    
    for text, task, img in results:
        print(f"[{img}] {text:30} → {task}")


def example_router_with_state():
    """Example: Using router with agent state."""
    print("\n=== Router with Agent State ===")
    
    from graph.state import AgentStatePydantic
    from graph.workflow import route_task
    
    router = TaskRouter()
    
    # Create state with user input
    state = AgentStatePydantic(
        user_input="Summarize the following article: AI is revolutionizing..."
    )
    
    print(f"Initial state:")
    print(f"  user_input: {state.user_input}")
    print(f"  task_type: {state.task_type}")
    
    # Route the task
    updated_state = route_task(state, router)
    
    print(f"\nAfter routing:")
    print(f"  task_type: {updated_state.task_type}")
    print(f"  messages: {updated_state.messages}")


def example_custom_router():
    """Example: Creating a custom router for specific domain."""
    print("\n=== Custom Domain-Specific Router ===")
    
    # Create router with custom rules for medical domain
    custom_rules = {
        TaskType.STANCE_DETECTION: {
            "keywords": ["symptoms", "diagnose", "treatment", "prognosis"],
            "priority": 1
        },
        TaskType.SUMMARIZATION: {
            "keywords": ["medical", "summary", "patient", "condition"],
            "priority": 2
        }
    }
    
    router = TaskRouter(
        rules=custom_rules,
        default_task=TaskType.STANCE_DETECTION
    )
    
    medical_inputs = [
        "What are the symptoms of diabetes?",
        "Summarize the medical report",
        "What diagnosis do you suggest?",
    ]
    
    print("Medical domain routing:\n")
    for text in medical_inputs:
        result = router.route(text)
        print(f"  '{text}' → {result.value}")


if __name__ == "__main__":
    print("TaskRouter Examples")
    print("=" * 70)
    
    # Run all examples
    example_basic_routing()
    example_image_priority()
    example_keyword_matching()
    example_custom_rules()
    example_pattern_matching()
    example_router_analysis()
    example_ambiguous_input()
    example_default_fallback()
    example_case_insensitive()
    example_priority_resolution()
    example_batch_routing()
    example_router_with_state()
    example_custom_router()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
