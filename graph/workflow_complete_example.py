"""
Complete LangGraph Workflow Examples

This module demonstrates the full end-to-end workflow including:
1. Building the workflow graph
2. Executing different task types
3. Handling error cases
4. Processing results
"""

import logging
from pathlib import Path
from typing import Optional
from graph.workflow import build_workflow, run_workflow
from graph.state import AgentStatePydantic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Build and Run Workflow
# ============================================================================

def example_1_basic_workflow_execution():
    """Build workflow and run a simple summarization task."""
    print("\n" + "="*70)
    print("Example 1: Basic Workflow Execution (Summarization)")
    print("="*70)
    
    try:
        # Configuration
        config = {
            "hf_api_key": None,  # Uses HF_API_TOKEN env var
            "timeout": 30,
            "max_retries": 3,
            "model_loading_timeout": 120
        }
        
        # Build the workflow
        print("\n[1] Building workflow...")
        compiled_graph = build_workflow(config)
        print("✓ Workflow built successfully")
        
        # Execute workflow
        print("\n[2] Executing workflow (Summarization task)...")
        user_input = """
        Artificial Intelligence is transforming the world in unprecedented ways.
        From healthcare to education, from transportation to entertainment,
        AI technologies are being deployed to solve complex problems and
        improve human lives. However, this rapid advancement also raises
        important questions about ethics, privacy, and social impact.
        """
        
        final_state = run_workflow(
            compiled_graph,
            user_input=user_input,
            verbose=True
        )
        
        # Display results
        print("\n[3] Results:")
        print(f"  Task Type: {final_state.task_type}")
        print(f"  Error: {final_state.error}")
        if final_state.result:
            print(f"  Summary: {final_state.result.get('content', 'N/A')[:100]}...")
        
        print("\n✓ Example 1 completed successfully")
        
    except Exception as e:
        logger.error("Example 1 failed: %s", e)
        print(f"✗ Error: {e}")


# ============================================================================
# Example 2: Sentiment/Stance Analysis
# ============================================================================

def example_2_stance_detection():
    """Run a stance detection task on various inputs."""
    print("\n" + "="*70)
    print("Example 2: Stance Detection")
    print("="*70)
    
    try:
        config = {
            "hf_api_key": None,
            "timeout": 30,
            "max_retries": 3,
            "model_loading_timeout": 120
        }
        
        print("\n[1] Building workflow...")
        compiled_graph = build_workflow(config)
        
        # Test multiple inputs
        test_inputs = [
            "I love this product! Best purchase ever made!",
            "This is terrible and a complete waste of money.",
            "The product is okay, nothing special.",
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n[2.{i}] Testing: '{user_input}'")
            final_state = run_workflow(compiled_graph, user_input=user_input)
            
            if final_state.result:
                result = final_state.result.get('content', {})
                print(f"  Detected: {result.get('label', 'N/A')}")
                print(f"  Confidence: {result.get('score', 0):.2%}")
        
        print("\n✓ Example 2 completed successfully")
        
    except Exception as e:
        logger.error("Example 2 failed: %s", e)
        print(f"✗ Error: {e}")


# ============================================================================
# Example 3: Image Generation
# ============================================================================

def example_3_image_generation():
    """Generate an image from a text prompt."""
    print("\n" + "="*70)
    print("Example 3: Image Generation")
    print("="*70)
    
    try:
        config = {
            "hf_api_key": None,
            "timeout": 30,
            "max_retries": 3,
            "model_loading_timeout": 120
        }
        
        print("\n[1] Building workflow...")
        compiled_graph = build_workflow(config)
        
        # Generate image
        print("\n[2] Generating image from prompt...")
        prompt = "A serene mountain landscape at sunset with golden light"
        
        final_state = run_workflow(compiled_graph, user_input=prompt, verbose=True)
        
        print("\n[3] Results:")
        if final_state.result:
            size_bytes = final_state.result.get('size_bytes', 0)
            print(f"  Image Size: {size_bytes / 1024:.1f}KB")
            print(f"  Image Content: {type(final_state.result.get('content'))}")
            
            # Optionally save image
            if final_state.result.get('content'):
                output_path = Path("generated_image.png")
                with open(output_path, "wb") as f:
                    f.write(final_state.result['content'])
                print(f"  Saved to: {output_path}")
        
        print("\n✓ Example 3 completed successfully")
        
    except Exception as e:
        logger.error("Example 3 failed: %s", e)
        print(f"✗ Error: {e}")


# ============================================================================
# Example 4: Image Analysis
# ============================================================================

def example_4_image_analysis(image_path: str):
    """Analyze an image to detect objects/classes.
    
    Args:
        image_path: Path to the image file
    """
    print("\n" + "="*70)
    print("Example 4: Image Analysis")
    print("="*70)
    
    try:
        # Read image
        image_path = Path(image_path)
        if not image_path.exists():
            print(f"Image file not found: {image_path}")
            return
        
        print(f"\n[1] Loading image: {image_path}")
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        print(f"✓ Image loaded ({len(image_bytes) / 1024:.1f}KB)")
        
        # Build workflow
        config = {
            "hf_api_key": None,
            "timeout": 30,
            "max_retries": 3,
            "model_loading_timeout": 120
        }
        
        print("\n[2] Building workflow...")
        compiled_graph = build_workflow(config)
        
        # Analyze image
        print("\n[3] Analyzing image...")
        final_state = run_workflow(
            compiled_graph,
            user_input="Analyze this image",  # Dummy text
            image=image_bytes,
            verbose=True
        )
        
        # Display results
        print("\n[4] Results:")
        if final_state.result:
            predictions = final_state.result.get('content', [])
            print(f"  Top predictions:")
            for pred in predictions[:5]:
                score = pred.get('score', 0)
                print(f"    - {pred.get('label')}: {score:.2%}")
        
        print("\n✓ Example 4 completed successfully")
        
    except Exception as e:
        logger.error("Example 4 failed: %s", e)
        print(f"✗ Error: {e}")


# ============================================================================
# Example 5: Workflow with State Inspection
# ============================================================================

def example_5_state_inspection():
    """Run workflow and inspect the full execution state."""
    print("\n" + "="*70)
    print("Example 5: Complete State Inspection")
    print("="*70)
    
    try:
        config = {
            "hf_api_key": None,
            "timeout": 30,
            "max_retries": 3,
            "model_loading_timeout": 120
        }
        
        print("\n[1] Building workflow...")
        compiled_graph = build_workflow(config)
        
        # Execute workflow
        print("\n[2] Executing workflow...")
        user_input = "This is fantastic news and I couldn't be happier!"
        final_state = run_workflow(compiled_graph, user_input=user_input)
        
        # Inspect state
        print("\n[3] Final State Inspection:")
        print(f"  User Input: {final_state.user_input}")
        print(f"  Task Type: {final_state.task_type}")
        print(f"  Has Error: {final_state.is_error()}")
        print(f"  Error Message: {final_state.error}")
        print(f"  Result Type: {final_state.result.get('type') if final_state.result else 'None'}")
        
        print(f"\n  Message Log ({len(final_state.messages)} messages):")
        for msg in final_state.messages:
            print(f"    - {msg}")
        
        print(f"\n  Created At: {final_state.created_at}")
        print(f"  Updated At: {final_state.updated_at}")
        
        # Serialize to dict
        print("\n[4] Serialized State (dict):")
        state_dict = final_state.to_dict()
        for key in ['user_input', 'task_type', 'error', 'result']:
            print(f"  {key}: {str(state_dict.get(key))[:50]}...")
        
        print("\n✓ Example 5 completed successfully")
        
    except Exception as e:
        logger.error("Example 5 failed: %s", e)
        print(f"✗ Error: {e}")


# ============================================================================
# Example 6: Error Handling
# ============================================================================

def example_6_error_handling():
    """Demonstrate error handling in the workflow."""
    print("\n" + "="*70)
    print("Example 6: Error Handling")
    print("="*70)
    
    try:
        config = {
            "hf_api_key": None,
            "timeout": 30,
            "max_retries": 3,
            "model_loading_timeout": 120
        }
        
        print("\n[1] Building workflow...")
        compiled_graph = build_workflow(config)
        
        # Test Case 1: Image analysis without image
        print("\n[2] Test Case 1: Image analysis without image data")
        try:
            final_state = run_workflow(
                compiled_graph,
                user_input="analyze the image",  # Triggers image analysis routing
                image=None  # But no image provided
            )
            
            if final_state.is_error():
                print(f"  ✓ Correctly detected error: {final_state.error}")
            else:
                print(f"  ! Unexpected success")
            
        except Exception as e:
            print(f"  ✓ Exception caught: {str(e)[:50]}...")
        
        # Test Case 2: Very long text for summarization
        print("\n[3] Test Case 2: Long text summarization")
        long_text = " ".join(["This is a test document about AI."] * 100)
        
        try:
            final_state = run_workflow(
                compiled_graph,
                user_input=long_text,
            )
            
            if final_state.result:
                print(f"  ✓ Successfully summarized")
                print(f"    Original length: {len(long_text)}")
                print(f"    Summary length: {len(final_state.result.get('content', ''))}")
            
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        print("\n✓ Example 6 completed successfully")
        
    except Exception as e:
        logger.error("Example 6 failed: %s", e)
        print(f"✗ Error: {e}")


# ============================================================================
# Example 7: Batch Processing
# ============================================================================

def example_7_batch_processing():
    """Process multiple tasks in sequence using the same workflow."""
    print("\n" + "="*70)
    print("Example 7: Batch Processing")
    print("="*70)
    
    try:
        config = {
            "hf_api_key": None,
            "timeout": 30,
            "max_retries": 3,
            "model_loading_timeout": 120
        }
        
        print("\n[1] Building workflow...")
        compiled_graph = build_workflow(config)
        
        # Define batch tasks
        tasks = [
            {
                "input": "The weather is beautiful today!",
                "type": "summarization"
            },
            {
                "input": "I absolutely hate this service.",
                "type": "stance"
            },
            {
                "input": "A colorful autumn forest with falling leaves",
                "type": "image_generation"
            },
        ]
        
        print(f"\n[2] Processing {len(tasks)} tasks in batch...")
        results = []
        
        for i, task in enumerate(tasks, 1):
            print(f"\n  [{i}] Processing: {task['input'][:40]}...")
            
            final_state = run_workflow(
                compiled_graph,
                user_input=task['input'],
            )
            
            results.append({
                "input": task['input'],
                "task_type": str(final_state.task_type),
                "success": not final_state.is_error(),
                "error": final_state.error,
                "result": final_state.result.get('type') if final_state.result else None
            })
            
            print(f"      ✓ Task type: {final_state.task_type}")
            print(f"      ✓ Status: {'Success' if not final_state.is_error() else 'Error'}")
        
        # Summary
        print(f"\n[3] Batch Processing Summary:")
        successful = sum(1 for r in results if r['success'])
        print(f"  Total Tasks: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {len(results) - successful}")
        
        print("\n✓ Example 7 completed successfully")
        
    except Exception as e:
        logger.error("Example 7 failed: %s", e)
        print(f"✗ Error: {e}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("LangGraph Workflow - Complete Examples")
    print("="*70)
    
    # Run examples
    example_1_basic_workflow_execution()
    example_2_stance_detection()
    # example_3_image_generation()  # Uncomment to test image generation
    # example_4_image_analysis("path/to/image.jpg")  # Uncomment with valid image
    example_5_state_inspection()
    example_6_error_handling()
    example_7_batch_processing()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)
