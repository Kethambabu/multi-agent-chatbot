"""
Example usage of the Hugging Face Inference API client.

This demonstrates how to use HFClient for various tasks.
"""

import logging
from hf_client import HFClient, HFClientConfig, HFAPIError, HFModelLoadingError

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_text_generation():
    """Example: Text generation with custom timeout."""
    print("\n=== Text Generation ===")
    
    # Create client with custom config
    config = HFClientConfig(
        timeout=30,
        max_retries=3,
        model_loading_timeout=120
    )
    
    with HFClient(config=config) as client:
        try:
            # Generate text
            prompt = "What is artificial intelligence?"
            response = client.text_generation(
                model="mistralai/Mistral-7B-Instruct-v0.1",
                prompt=prompt,
                max_new_tokens=128,
                temperature=0.7
            )
            print(f"Prompt: {prompt}")
            print(f"Response: {response}")
            
        except HFModelLoadingError as e:
            print(f"Model loading timeout: {e}")
        except HFAPIError as e:
            print(f"API error: {e}")


def example_image_generation():
    """Example: Image generation."""
    print("\n=== Image Generation ===")
    
    with HFClient() as client:
        try:
            # Generate image
            prompt = "A serene landscape with mountains and a lake"
            image_bytes = client.image_generation(
                model="stabilityai/stable-diffusion-2",
                prompt=prompt,
                height=768,
                width=768,
                num_inference_steps=20
            )
            
            # Save image
            with open("generated_image.png", "wb") as f:
                f.write(image_bytes)
            
            print(f"Image generated and saved: generated_image.png")
            print(f"Image size: {len(image_bytes)} bytes")
            
        except HFAPIError as e:
            print(f"Image generation failed: {e}")


def example_question_answering():
    """Example: Question answering."""
    print("\n=== Question Answering ===")
    
    with HFClient() as client:
        try:
            context = """
            Python is a high-level programming language known for its simplicity
            and readability. It was created by Guido van Rossum and released in 1991.
            Python is widely used in web development, data science, and automation.
            """
            
            question = "When was Python released?"
            
            answer = client.question_answering(
                model="deepset/roberta-base-squad2",
                question=question,
                context=context
            )
            
            print(f"Question: {question}")
            print(f"Answer: {answer}")
            
        except HFAPIError as e:
            print(f"Question answering failed: {e}")


def example_sentiment_analysis():
    """Example: Sentiment analysis."""
    print("\n=== Sentiment Analysis ===")
    
    with HFClient() as client:
        try:
            text = "I absolutely love this product! It's amazing and works perfectly."
            
            sentiment = client.sentiment_analysis(
                model="distilbert-base-uncased-finetuned-sst-2-english",
                text=text
            )
            
            print(f"Text: {text}")
            print(f"Sentiment: {sentiment}")
            
        except HFAPIError as e:
            print(f"Sentiment analysis failed: {e}")


def example_custom_request():
    """Example: Custom request for advanced use cases."""
    print("\n=== Custom Request ===")
    
    with HFClient() as client:
        try:
            payload = {
                "inputs": "The capital of France is",
                "parameters": {
                    "max_new_tokens": 10,
                    "temperature": 0.5
                }
            }
            
            response = client.request(
                model="gpt2",
                payload=payload,
                return_json=True
            )
            
            print(f"Custom request response: {response}")
            
        except HFAPIError as e:
            print(f"Custom request failed: {e}")


def example_error_handling():
    """Example: Handling different types of errors."""
    print("\n=== Error Handling ===")
    
    from hf_client import HFAPIAuthError, HFAPITimeoutError
    
    with HFClient() as client:
        try:
            # This will likely timeout or fail - for demo purposes
            response = client.request(
                model="some-very-large-model",
                payload={"inputs": "test"},
                timeout=5  # Very short timeout to simulate timeout
            )
            
        except HFAPIAuthError as e:
            print(f"Authentication error: {e}")
        except HFAPITimeoutError as e:
            print(f"Timeout error: {e}")
        except HFModelLoadingError as e:
            print(f"Model loading error: {e}")
        except HFAPIError as e:
            print(f"General API error: {e}")


if __name__ == "__main__":
    print("Hugging Face Inference API Client Examples")
    print("=" * 50)
    
    # Note: These examples require a valid HF_API_KEY environment variable
    # and available models. Uncomment to run specific examples.
    
    # example_text_generation()
    # example_image_generation()
    # example_question_answering()
    # example_sentiment_analysis()
    # example_custom_request()
    # example_error_handling()
    
    print("\nNote: Set HF_API_KEY environment variable before running these examples")
    print("Examples are commented out. Uncomment to test with real API calls.")
