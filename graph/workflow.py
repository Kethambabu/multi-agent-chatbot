"""
Workflow implementation using LangGraph.

Orchestrates the multi-modal agent workflow with intelligent task routing
and execution of specialized agents for different task types.
"""

import logging
import re
import base64
from typing import Optional, Tuple, Callable, Dict, Any, Union
from enum import Enum

from graph.state import TaskType, AgentStatePydantic
from agents.summarizer import SummarizerAgent
from agents.stance import StanceAgent
from agents.text2image_v2 import Text2ImageV2Agent
from agents.image_analysis import ImageAnalysisAgent
from utils.hf_client import HFClient, HFClientConfig


logger = logging.getLogger(__name__)


def normalize_state(state: Union[dict, AgentStatePydantic]) -> AgentStatePydantic:
    """Normalize workflow state input to AgentStatePydantic.

    LangGraph may pass a raw dict or a Pydantic model instance into node
    functions. This helper ensures the workflow always works with a valid
    AgentStatePydantic object.
    """
    if isinstance(state, AgentStatePydantic):
        return state
    return AgentStatePydantic(**state)


# ============================================================================
# Task Router
# ============================================================================

class TaskRouter:
    """Intelligent task router for multi-modal agent using LLM-based intent classification.
    
    Routes user inputs to the appropriate task type based on:
    - LLM-based intent classification (primary)
    - Image presence (contextual hint)
    - Fallback to rule-based routing (backup)
    
    Features:
    - Zero-shot classification with HuggingFace models
    - Image context awareness
    - Confidence scoring
    - Rule-based fallback for robustness
    - Logging for debugging
    - Graceful degradation on API errors
    """
    
    # Task labels for zero-shot classification
    TASK_LABELS = {
        TaskType.SUMMARIZATION: "summarize text content",
        TaskType.STANCE_DETECTION: "analyze sentiment or opinion",
        TaskType.IMAGE_GENERATION: "generate image from text description",
        TaskType.IMAGE_ANALYSIS: "analyze or describe image content"
    }
    
    # Default keywords and patterns for fallback rule-based routing
    DEFAULT_RULES = {
        TaskType.IMAGE_ANALYSIS: {
            "keywords": ["analyze", "describe", "identify", "classify", "what is", "tell me about"],
            "priority": 3
        },
        TaskType.SUMMARIZATION: {
            "keywords": ["summarize", "summerize", "summary", "condense", "abstract", "overview", "brief"],
            "priority": 2
        },
        TaskType.IMAGE_GENERATION: {
            "keywords": ["generate", "create", "draw", "make", "design", "image of"],
            "patterns": [
                r"draw\s+.*image",
                r"generate\s+.*image",
                r"create\s+.*image",
                r"make\s+.*image"
            ],
            "priority": 2
        },
        TaskType.STANCE_DETECTION: {
            "keywords": ["opinion", "sentiment", "stance", "feel", "think about", "believe", "agree", "disagree"],
            "priority": 1
        }
    }
    
    # HuggingFace zero-shot classification model
    INTENT_MODEL = "facebook/bart-large-mnli"
    
    def __init__(
        self,
        rules: Optional[dict] = None,
        default_task: TaskType = TaskType.SUMMARIZATION,
        use_llm: bool = True,
        hf_client: Optional[HFClient] = None
    ):
        """Initialize task router.
        
        Args:
            rules: Custom routing rules for fallback. If None, uses DEFAULT_RULES.
            default_task: Fallback task type if all classification fails
            use_llm: Whether to use LLM-based classification (vs rule-based only)
            hf_client: HuggingFace client instance. If None, creates new instance.
        """
        self.rules = rules or self.DEFAULT_RULES.copy()
        self.default_task = default_task
        self.use_llm = use_llm
        self.logger = logging.getLogger(__name__)
        
        # Initialize HF client for intent classification
        self.hf_client = hf_client
        if use_llm and not hf_client:
            try:
                config = HFClientConfig()
                self.hf_client = HFClient(config)
                self.logger.info("Initialized HFClient for LLM-based intent classification")
            except Exception as e:
                self.logger.warning(
                    "Failed to initialize HFClient, falling back to rule-based routing: %s",
                    e
                )
                self.use_llm = False
        
        self.logger.info(
            "Initialized TaskRouter with LLM=%s, %d rule sets, default_task=%s",
            use_llm,
            len(self.rules),
            default_task
        )
    
    def route(
        self,
        user_input: str,
        image: Optional[bytes] = None
    ) -> TaskType:
        """Route user input to appropriate task type.
        
        Uses explicit rule-based routing first, then LLM-based intent classification,
        and finally rule-based fallback if classification fails.
        
        Args:
            user_input: User's text input
            image: Optional image bytes
            
        Returns:
            Determined TaskType
        """
        # Special case 1: Image with ambiguous text -> analyze image
        if image is not None and (not user_input or len(user_input.strip()) < 3):
            self.logger.info("Image detected with minimal text, routing to IMAGE_ANALYSIS")
            return TaskType.IMAGE_ANALYSIS

        # Prefer explicit text rules when a clear task keyword appears
        explicit_task = self._check_explicit_task(user_input)
        if explicit_task:
            self.logger.info("Explicit task keyword matched, routing to %s", explicit_task)
            return explicit_task
        
        # Try LLM-based classification when explicit routing is ambiguous
        if self.use_llm and self.hf_client:
            try:
                task_type = self._classify_intent_llm(user_input, image)
                if task_type:
                    return task_type
            except Exception as e:
                self.logger.warning("LLM classification failed, falling back to rules: %s", e)
        
        # Final fallback: Rule-based routing
        return self._route_by_rules(user_input, image)
    
    def _classify_intent_llm(
        self,
        user_input: str,
        image: Optional[bytes] = None
    ) -> Optional[TaskType]:
        """Classify intent using LLM zero-shot classification.
        
        Args:
            user_input: User's text input
            image: Optional image bytes for context
            
        Returns:
            Classified TaskType or None if classification fails
        """
        if not user_input or not user_input.strip():
            return None
        
        try:
            # Prepare candidate labels
            candidate_labels = [self.TASK_LABELS[task] for task in TaskType]
            
            # Call zero-shot classification
            payload = {
                "inputs": user_input,
                "parameters": {
                    "candidate_labels": candidate_labels,
                    "multi_class": False
                }
            }
            
            response = self.hf_client.request(
                self.INTENT_MODEL,
                payload,
                task="zero-shot-classification"
            )
            
            # Extract top classification result
            if isinstance(response, dict):
                labels = response.get("labels", [])
                scores = response.get("scores", [])
                
                if labels and scores:
                    top_label = labels[0]
                    top_score = scores[0]
                    
                    self.logger.info(
                        "LLM Intent Classification: %s (confidence: %.2f)",
                        top_label,
                        top_score
                    )
                    
                    # Map label back to TaskType
                    for task_type, label in self.TASK_LABELS.items():
                        if label == top_label:
                            # Apply secondary routing rule for images
                            if image and top_score > 0.5:  # Confidence threshold
                                if task_type != TaskType.IMAGE_ANALYSIS:
                                    self.logger.debug(
                                        "Image provided but LLM classified as %s, "
                                        "routing to IMAGE_ANALYSIS",
                                        task_type
                                    )
                                    return TaskType.IMAGE_ANALYSIS
                            
                            return task_type
            
            self.logger.warning("Unexpected response format from intent classification")
            return None
            
        except Exception as e:
            self.logger.error("LLM intent classification error: %s", e)
            raise
    
    def _route_by_rules(
        self,
        user_input: str,
        image: Optional[bytes] = None
    ) -> TaskType:
        """Route using rule-based matching (fallback).
        
        Args:
            user_input: User's text input
            image: Optional image bytes
            
        Returns:
            Determined TaskType
        """
        # Image present: prefer IMAGE_ANALYSIS unless explicit task requested
        if image is not None:
            self.logger.debug("Image detected, checking for explicit text task...")
            explicit_task = self._check_explicit_task(user_input)
            if explicit_task and explicit_task != TaskType.IMAGE_ANALYSIS:
                self.logger.info(
                    "Image present but text explicitly requests %s",
                    explicit_task
                )
                return explicit_task
            
            self.logger.info("Routing to IMAGE_ANALYSIS (image provided)")
            return TaskType.IMAGE_ANALYSIS
        
        # No image: route based on text content
        return self._check_explicit_task(user_input) or self.default_task
    
    def _check_explicit_task(self, text: str) -> Optional[TaskType]:
        """Check text for explicit task indicators.
        
        Args:
            text: Text to analyze
            
        Returns:
            TaskType if match found, None otherwise
        """
        if not text or not text.strip():
            return None
        
        text_lower = text.lower()
        matches = []
        
        # Check each task type's rules
        for task_type, rule_set in self.rules.items():
            match_score = self._calculate_match_score(text_lower, rule_set)
            
            if match_score > 0:
                matches.append((task_type, match_score, rule_set.get("priority", 99)))
        
        if not matches:
            self.logger.debug("No matching rules found for text: %s", text[:50])
            return None
        
        # Sort by match score (desc) then priority (asc)
        matches.sort(key=lambda x: (-x[1], x[2]))
        top_match, score, priority = matches[0]
        
        self.logger.info(
            "Matched %s with score %.1f: %s",
            top_match,
            score,
            text[:50]
        )
        
        return top_match
    
    def _calculate_match_score(self, text_lower: str, rule_set: dict) -> float:
        """Calculate match score for a rule set.
        
        Args:
            text_lower: Lowercase text to check
            rule_set: Rule set with keywords and patterns
            
        Returns:
            Match score (0 = no match, higher = better match)
        """
        score = 0.0
        
        # Check keywords (each keyword match = 1 point)
        keywords = rule_set.get("keywords", [])
        for keyword in keywords:
            if keyword in text_lower:
                score += 1.0
                self.logger.debug("Keyword match: '%s'", keyword)
        
        # Check patterns (each pattern match = 2 points, more specific)
        patterns = rule_set.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, text_lower):
                score += 2.0
                self.logger.debug("Pattern match: %s", pattern)
        
        return score
    
    def add_rule(
        self,
        task_type: TaskType,
        keywords: Optional[list] = None,
        patterns: Optional[list] = None,
        priority: int = 99
    ):
        """Add or update routing rules for a task type.
        
        Args:
            task_type: Task type to add rule for
            keywords: List of keyword strings
            patterns: List of regex patterns
            priority: Priority level (lower = higher priority)
        """
        if task_type not in self.rules:
            self.rules[task_type] = {}
        
        if keywords:
            self.rules[task_type]["keywords"] = keywords
        if patterns:
            self.rules[task_type]["patterns"] = patterns
        
        self.rules[task_type]["priority"] = priority
        
        self.logger.info(
            "Updated rules for %s: %d keywords, %d patterns, priority=%d",
            task_type,
            len(keywords or []),
            len(patterns or []),
            priority
        )
    
    def analyze(self, user_input: str, image: Optional[bytes] = None) -> dict:
        """Analyze user input and return detailed routing information.
        
        Useful for debugging and understanding routing decisions.
        Shows both LLM classification results and rule-based matches.
        
        Args:
            user_input: User's input text
            image: Optional image bytes
            
        Returns:
            Dictionary with routing analysis details
        """
        has_image = image is not None
        task_type = self.route(user_input, image)
        
        text_lower = user_input.lower() if user_input else ""
        matching_rules = {}
        llm_classification = None
        
        # Get LLM classification results (for analysis)
        if self.use_llm and self.hf_client:
            try:
                llm_classification = self._get_llm_classification_details(user_input)
            except Exception as e:
                self.logger.debug("Could not get LLM details for analysis: %s", e)
        
        # Find all matching rules
        for tt, rule_set in self.rules.items():
            matches = self._calculate_match_score(text_lower, rule_set)
            if matches > 0:
                keywords = rule_set.get("keywords", [])
                patterns = rule_set.get("patterns", [])
                matching_rules[tt.value] = {
                    "score": matches,
                    "priority": rule_set.get("priority", 99),
                    "matched_keywords": [k for k in keywords if k in text_lower],
                    "matched_patterns": [p for p in patterns if re.search(p, text_lower)]
                }
        
        return {
            "task_type": task_type.value,
            "classification_method": "llm" if llm_classification else "rules",
            "llm_results": llm_classification,
            "has_image": has_image,
            "text_length": len(user_input) if user_input else 0,
            "text_preview": user_input[:50] if user_input else "",
            "matching_rules": matching_rules,
            "default_fallback": task_type == self.default_task
        }
    
    def _get_llm_classification_details(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Get detailed LLM classification results for analysis.
        
        Args:
            user_input: User's text input
            
        Returns:
            Dictionary with all classification scores or None
        """
        if not user_input or not user_input.strip():
            return None
        
        candidate_labels = [self.TASK_LABELS[task] for task in TaskType]
        
        payload = {
            "inputs": user_input,
            "parameters": {
                "candidate_labels": candidate_labels,
                "multi_class": False
            }
        }
        
        response = self.hf_client.request(
            self.INTENT_MODEL,
            payload,
            task="zero-shot-classification"
        )
        
        if isinstance(response, dict):
            labels = response.get("labels", [])
            scores = response.get("scores", [])
            
            if labels and scores:
                return {
                    "model": self.INTENT_MODEL,
                    "scores": {label: float(score) for label, score in zip(labels, scores)}
                }
        
        return None


# ============================================================================
# Workflow Functions
# ============================================================================

def create_workflow(config):
    """Create and configure the workflow graph.
    
    Args:
        config: Application configuration object
        
    Returns:
        Dictionary with agents and workflow components
    """
    # Initialize task router
    router = TaskRouter()
    
    # Initialize all agents with error handling
    agents = {}
    
    try:
        summarizer = SummarizerAgent(config)
        agents["summarizer"] = summarizer
        logger.info("SummarizerAgent initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize SummarizerAgent: %s", e)
        raise  # Summarizer is critical, fail if it can't initialize
    
    try:
        stance = StanceAgent(config)
        agents["stance"] = stance
        logger.info("StanceAgent initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize StanceAgent: %s", e)
        raise  # Stance is critical, fail if it can't initialize
    
    try:
        text2image = Text2ImageV2Agent()
        agents["text2image"] = text2image
        logger.info("Text2ImageV2Agent initialized (Pollinations.AI â€” free, always enabled)")
    except Exception as e:
        logger.error("Failed to initialize Text2ImageV2Agent: %s", e)
        raise  # v2 has no external dependencies â€” failure is unexpected
    
    try:
        image_analysis = ImageAnalysisAgent(config)
        agents["image_analysis"] = image_analysis
        logger.info("ImageAnalysisAgent initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize ImageAnalysisAgent: %s", e)
        raise  # Image analysis is critical, fail if it can't initialize
    
    logger.info("Created all agents and task router")
    
    return {
        "router": router,
        "agents": agents
    }


def route_task(
    state: AgentStatePydantic,
    router: TaskRouter
) -> AgentStatePydantic:
    """Router node: Determine task type based on input.
    
    Args:
        state: Current agent state
        router: TaskRouter instance
        
    Returns:
        Updated state with task_type
    """
    try:
        task_type = router.route(state.user_input, state.image)
        state.task_type = task_type
        
        state.add_message(f"Router: Routed to {task_type.value}")
        logger.info("Routed to task: %s", task_type)
        
    except Exception as e:
        state.set_error(f"Routing failed: {str(e)}")
        logger.error("Routing error: %s", e)
    
    return state


def execute_task(
    state: AgentStatePydantic,
    agents: dict
) -> AgentStatePydantic:
    """Executor node: Execute the appropriate agent for the task.
    
    Args:
        state: Current agent state
        agents: Dictionary of agents (summarizer, stance, text2image, image_analysis)
        
    Returns:
        Updated state with result
    """
    try:
        task_type = state.task_type
        state.add_message(f"Agent: Executing {task_type.value}...")
        
        # Route to appropriate agent
        if task_type == TaskType.SUMMARIZATION:
            result = agents["summarizer"].summarize(state.user_input)
            state.set_result({"summary": result})
            
        elif task_type == TaskType.STANCE_DETECTION:
            result = agents["stance"].detect_stance(state.user_input)
            state.set_result(result)
            
        elif task_type == TaskType.IMAGE_GENERATION:
            result = agents["text2image"].generate_image(state.user_input)
            if isinstance(result, dict) and "error" in result:
                # Agent returned an error (e.g., disabled due to missing API key)
                state.set_error(result["error"])
            else:
                # Agent returned a URL
                state.set_result({"image_url": result})
            
        elif task_type == TaskType.IMAGE_ANALYSIS:
            if not state.image:
                raise ValueError("Image analysis requested but no image provided")
            result = agents["image_analysis"].analyze_image(state.image)
            state.set_result({"predictions": result})
            
        else:
            raise ValueError(f"Unknown task type: {task_type}")
        
        state.add_message(f"Agent: {task_type.value} completed successfully")
        logger.info("Task executed: %s", task_type)
        
    except Exception as e:
        state.set_error(f"Task execution failed: {str(e)}")
        logger.error("Execution error for %s: %s", state.task_type, e)
    
    return state


# ============================================================================
# LangGraph Nodes
# ============================================================================

def node_router(state: AgentStatePydantic, router: TaskRouter) -> dict:
    """Router node: Determine task type using LLM-based intent classification.
    
    Uses zero-shot classification with HuggingFace models (facebook/bart-large-mnli)
    to intelligently classify user intent into one of:
    - summary: text summarization
    - stance: sentiment/stance detection
    - image_gen: text-to-image generation
    - image_analysis: image classification/analysis
    
    Falls back to rule-based routing if LLM classification fails.
    
    Args:
        state: Current agent state
        router: Task router instance with LLM classification enabled
        
    Returns:
        Updated state dictionary with determined task_type
    """
    logger.debug("Entering router node with LLM-based intent classification")
    
    try:
        # Route the task using LLM-based classification
        task_type = router.route(state.user_input, state.image)
        state.task_type = task_type
        state.add_message(f"Ã°Å¸â€œÂ Router: LLM-classified as {task_type.value}")
        
        logger.info("LLM Router decision: %s for input: %s", task_type, state.user_input[:50])
        
    except Exception as e:
        state.set_error(f"Router failed: {str(e)}")
        logger.error("Router error: %s", e)
    
    return state.to_dict()


def node_summarizer(state: AgentStatePydantic, agent: SummarizerAgent) -> dict:
    """Summarizer node: Summarize text using BART.
    
    Args:
        state: Current agent state
        agent: SummarizerAgent instance
        
    Returns:
        Updated state dictionary
    """
    logger.debug("Entering summarizer node")
    
    if state.is_error():
        logger.warning("State already in error, skipping summarizer")
        return state.to_dict()
    
    try:
        state.add_message("Ã°Å¸â€œÂ Summarizer: Starting summarization...")
        
        summary = agent.summarize(state.user_input)
        
        state.set_result({
            "type": "summary",
            "content": summary,
            "status": "success"
        })
        
        state.add_message(f"Ã¢Å“â€œ Summarizer: Completed ({len(summary)} characters)")
        logger.info("Summarization completed: %d chars", len(summary))
        
    except Exception as e:
        state.set_error(f"Summarization failed: {str(e)}")
        logger.error("Summarizer error: %s", e)
    
    return state.to_dict()


def node_stance(state: AgentStatePydantic, agent: StanceAgent) -> dict:
    """Stance detection node: Detect stance/sentiment using zero-shot classification.
    
    Args:
        state: Current agent state
        agent: StanceAgent instance
        
    Returns:
        Updated state dictionary
    """
    logger.debug("Entering stance node")
    
    if state.is_error():
        logger.warning("State already in error, skipping stance detection")
        return state.to_dict()
    
    try:
        state.add_message("Ã°Å¸â€™Â­ Stance Detector: Analyzing sentiment...")
        
        result = agent.detect_stance(state.user_input)
        
        state.set_result({
            "type": "stance",
            "content": result,
            "status": "success"
        })
        
        state.add_message(
            f"Ã¢Å“â€œ Stance Detector: {result['label']} (confidence: {result['confidence']:.2%})"
        )
        logger.info("Stance detected: %s (%.2f)", result['label'], result['confidence'])
        
    except Exception as e:
        state.set_error(f"Stance detection failed: {str(e)}")
        logger.error("Stance detector error: %s", e)
    
    return state.to_dict()


def node_text_to_image(state: AgentStatePydantic, agent: Text2ImageV2Agent) -> dict:
    """Text-to-image generation node: Generate image using Pollinations.AI.

    The v2 agent returns a dict with status, image_path, image_url, and message.
    We map these into the standard workflow result format.

    Args:
        state: Current agent state
        agent: Text2ImageV2Agent instance

    Returns:
        Updated state dictionary
    """
    logger.debug("Entering text-to-image node (v2 Ã¢â‚¬â€ Pollinations.AI)")

    if state.is_error():
        logger.warning("State already in error, skipping image generation")
        return state.to_dict()

    try:
        state.add_message("Ã°Å¸Å½Â¨ Image Generator: Creating image (Pollinations.AI)...")

        result = agent.generate_image(state.user_input)

        if result.get("status") != "success":
            state.set_error(result.get("message", "Image generation failed"))
            return state.to_dict()

        # Build workflow-compatible result
        image_url = result.get("image_url", "")
        image_path = result.get("image_path", "")

        state.set_result({
            "type": "image_gen",
            "content": image_url,
            "image_url": image_url,
            "image_path": image_path,
            "source": "url",
            "status": "success",
        })

        state.add_message(f"Ã¢Å“â€œ Image Generator: {result.get('message', 'Done')}")
        logger.info("Image generated: path=%s", image_path)

    except Exception as e:
        state.set_error(f"Image generation failed: {str(e)}")
        logger.error("Image generator error: %s", e)

    return state.to_dict()

def node_image_analysis(state: AgentStatePydantic, agent: ImageAnalysisAgent) -> dict:
    """Image analysis node: Analyze image using Vision Transformer.
    
    Args:
        state: Current agent state
        agent: ImageAnalysisAgent instance
        
    Returns:
        Updated state dictionary
    """
    logger.debug("Entering image analysis node")
    
    if state.is_error():
        logger.warning("State already in error, skipping image analysis")
        return state.to_dict()
    
    try:
        state.add_message("Ã°Å¸â€Â Image Analyzer: Analyzing image...")
        
        if not state.image:
            raise ValueError("No image data provided for analysis")
        
        predictions = agent.analyze_image(state.image)
        
        state.set_result({
            "type": "analysis",
            "content": predictions,
            "status": "success"
        })
        
        top_label = predictions[0]['label'] if predictions else "unknown"
        state.add_message(f"Ã¢Å“â€œ Image Analyzer: Top label: {top_label}")
        logger.info("Image analysis completed: top label %s", top_label)
        
    except Exception as e:
        state.set_error(f"Image analysis failed: {str(e)}")
        logger.error("Image analyzer error: %s", e)
    
    return state.to_dict()


# ============================================================================
# Conditional Edge Router
# ============================================================================

def select_task_node(state: Union[dict, AgentStatePydantic]) -> str:
    """Conditional edge router: Select next node based on task type.
    
    Args:
        state: Current state dictionary or AgentStatePydantic instance
        
    Returns:
        Name of the next node to execute
    """
    if isinstance(state, AgentStatePydantic):
        raw_type = state.task_type
    else:
        raw_type = state.get("task_type")

    task_type = raw_type
    if isinstance(raw_type, str):
        try:
            task_type = TaskType(raw_type)
        except ValueError:
            task_type = None

    task_node_map = {
        TaskType.SUMMARIZATION: "summarizer",
        TaskType.STANCE_DETECTION: "stance",
        TaskType.IMAGE_GENERATION: "text_to_image",
        TaskType.IMAGE_ANALYSIS: "image_analysis",
    }

    node = task_node_map.get(task_type, "summarizer")
    logger.debug("Routing to node: %s for task: %s", node, raw_type)

    return node


# ============================================================================
# LangGraph Workflow Builder
# ============================================================================

def build_workflow(config):
    """Build the complete LangGraph workflow with LLM-based intent classification.
    
    Creates a graph with:
    - LLM-based intent classification router node (entry point)
    - 4 task-specific nodes (summarizer, stance, text2image, image_analysis)
    - Conditional edges for routing
    - Error handling and fallback strategies
    
    The router uses facebook/bart-large-mnli zero-shot classification to intelligently
    route requests to the most appropriate task handler. Falls back to rule-based
    routing if the LLM classification fails.
    
    Args:
        config: Application configuration with HF API key
        
    Returns:
        Compiled LangGraph workflow (StateGraph)
        
    Raises:
        ImportError: If LangGraph not installed
        ValueError: If configuration invalid
    """
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        logger.error("LangGraph not installed. Install with: pip install langgraph")
        raise ImportError("LangGraph required for workflow. Install with: pip install langgraph")
    
    # Initialize agents and HF client
    logger.info("Initializing agents and HF client...")
    from utils.hf_client import HFClientConfig, HFClient
    
    hf_config = HFClientConfig(
        api_key=getattr(config, "hf_api_key", None) if not isinstance(config, dict) else config.get("hf_api_key", None),
        timeout=getattr(config, "timeout", 30) if not isinstance(config, dict) else config.get("timeout", 30),
        max_retries=getattr(config, "max_retries", 3) if not isinstance(config, dict) else config.get("max_retries", 3),
        model_loading_timeout=getattr(config, "model_loading_timeout", 120) if not isinstance(config, dict) else config.get("model_loading_timeout", 120)
    )
    
    # Initialize HF client for intent classification
    hf_client = HFClient(hf_config)
    
    # Initialize task router with LLM-based classification enabled
    router = TaskRouter(use_llm=True, hf_client=hf_client)
    logger.info("TaskRouter initialized with LLM-based intent classification")
    
    # Initialize agents with error handling
    summarizer = SummarizerAgent(config=hf_config)
    stance = StanceAgent(config=hf_config)
    
    text2image = Text2ImageV2Agent()
    logger.info("Text2ImageV2Agent initialized (Pollinations.AI â€” free, always enabled)")
    
    image_analysis = ImageAnalysisAgent(config=hf_config)
    
    logger.info("All agents initialized successfully")
    
    # Create state graph
    workflow = StateGraph(AgentStatePydantic)
    
    # Add nodes
    logger.info("Adding workflow nodes...")
    workflow.add_node(
        "router",
        lambda state: node_router(normalize_state(state), router)
    )
    workflow.add_node(
        "summarizer",
        lambda state: node_summarizer(normalize_state(state), summarizer)
    )
    workflow.add_node(
        "stance",
        lambda state: node_stance(normalize_state(state), stance)
    )
    workflow.add_node(
        "text_to_image",
        lambda state: node_text_to_image(normalize_state(state), text2image)
    )
    workflow.add_node(
        "image_analysis",
        lambda state: node_image_analysis(normalize_state(state), image_analysis)
    )
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges
    logger.info("Setting up conditional routing...")
    workflow.add_conditional_edges(
        "router",
        select_task_node,
        {
            "summarizer": "summarizer",
            "stance": "stance",
            "text_to_image": "text_to_image",
            "image_analysis": "image_analysis"
        }
    )
    
    # Connect all task nodes to END
    workflow.add_edge("summarizer", END)
    workflow.add_edge("stance", END)
    workflow.add_edge("text_to_image", END)
    workflow.add_edge("image_analysis", END)
    
    # Compile the graph
    logger.info("Compiling LangGraph workflow...")
    compiled_graph = workflow.compile()
    
    logger.info("LangGraph workflow built successfully with LLM-based intent classification")
    
    return compiled_graph


# ============================================================================
# Workflow Execution
# ============================================================================

def run_workflow(
    compiled_graph,
    user_input: str,
    image: Optional[bytes] = None,
    verbose: bool = False
) -> AgentStatePydantic:
    """Execute the compiled LangGraph workflow.
    
    Args:
        compiled_graph: Compiled StateGraph from build_workflow()
        user_input: User's text input
        image: Optional image bytes
        verbose: Whether to print node execution details
        
    Returns:
        Final state after workflow execution
    """
    logger.info("Starting workflow execution")
    
    try:
        # Create initial state
        initial_state = AgentStatePydantic(
            user_input=user_input,
            image=image
        )
        
        initial_state.add_message("Ã°Å¸Å¡â‚¬ Workflow: Starting execution")
        
        # Execute workflow
        logger.info("Invoking compiled graph...")
        result = compiled_graph.invoke(
            initial_state.to_dict(),
            {"recursion_limit": 25}
        )
        
        # Convert result back to state object
        if isinstance(result, AgentStatePydantic):
            final_state = result
        else:
            final_state = AgentStatePydantic(**result)
        
        logger.info(
            "Workflow completed: task=%s, error=%s",
            final_state.task_type,
            final_state.is_error()
        )
        
        if verbose:
            logger.info("Final state messages: %d", len(final_state.messages))
            for msg in final_state.messages:
                print(f"  {msg}")
        
        return final_state
        
    except Exception as e:
        logger.error("Workflow execution failed: %s", e)
        raise

