"""
Researcher Agent - responsible for finding and evaluating information from the internet
and providing it to other agents in the system.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup
import time
import prometheus_client as prom

from .common.utils import get_logger, format_message

logger = get_logger("researcher_agent")

# Prometheus metrics
REQUESTS_TOTAL = prom.Counter(
    'researcher_requests_total', 
    'Total number of requests received by the researcher agent',
    ['type']
)
REQUESTS_SUCCESS = prom.Counter(
    'researcher_requests_success_total', 
    'Total number of successful requests processed by the researcher agent',
    ['type']
)
LATENCY = prom.Histogram(
    'researcher_latency_seconds', 
    'Time taken to process a research request',
    ['type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0)
)
EMBEDDING_MODEL_MEMORY = prom.Gauge(
    'researcher_embedding_model_memory_usage', 
    'Memory usage of the embedding model in percentage'
)
KNOWLEDGE_STORE_SIZE = prom.Gauge(
    'researcher_knowledge_store_size', 
    'Number of entries in the knowledge store'
)
SOURCES_BY_RELIABILITY = prom.Gauge(
    'researcher_sources_by_reliability_bucket', 
    'Number of sources by reliability score bucket',
    ['bucket']
)

class ResearcherAgent:
    """
    Agent responsible for researching information, evaluating its reliability,
    and sharing it with other agents.
    """
    
    def __init__(self, 
                 config: Dict[str, Any] = None, 
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the researcher agent
        
        Args:
            config: Configuration for the agent
            embedding_model: The sentence transformer model to use for embeddings
        """
        self.config = config or {}
        self.logger = logging.getLogger("researcher_agent")
        
        # Initialize embedding model for semantic search
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            # Mock memory usage for the model (in a real system, this would be actual memory tracking)
            EMBEDDING_MODEL_MEMORY.set(35.0)  # Using 35% of allocated memory
        except Exception as e:
            self.logger.error(f"Error loading embedding model: {e}")
            self.embedding_model = None
            EMBEDDING_MODEL_MEMORY.set(0)
            
        # Storage for embedded search results
        self.knowledge_store = {
            "embeddings": [],
            "texts": [],
            "sources": [],
            "reliability_scores": [],
            "timestamps": []
        }
        
        # Initialize reliability buckets
        self._update_reliability_metrics()
        KNOWLEDGE_STORE_SIZE.set(0)
    
    def _update_reliability_metrics(self):
        """Update Prometheus metrics for reliability buckets"""
        if not self.knowledge_store["reliability_scores"]:
            # Initialize with zeros
            SOURCES_BY_RELIABILITY.labels(bucket="high (0.8-1.0)").set(0)
            SOURCES_BY_RELIABILITY.labels(bucket="medium (0.6-0.8)").set(0)
            SOURCES_BY_RELIABILITY.labels(bucket="low (0.0-0.6)").set(0)
            return
            
        # Count sources by reliability score range
        high = sum(1 for score in self.knowledge_store["reliability_scores"] if score >= 0.8)
        medium = sum(1 for score in self.knowledge_store["reliability_scores"] if 0.6 <= score < 0.8)
        low = sum(1 for score in self.knowledge_store["reliability_scores"] if score < 0.6)
        
        SOURCES_BY_RELIABILITY.labels(bucket="high (0.8-1.0)").set(high)
        SOURCES_BY_RELIABILITY.labels(bucket="medium (0.6-0.8)").set(medium)
        SOURCES_BY_RELIABILITY.labels(bucket="low (0.0-0.6)").set(low)
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web for information on a given query
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of search results with content and metadata
        """
        self.logger.info(f"Searching web for: {query}")
        
        # Implementation would use an actual search API
        # For now using a placeholder/mock implementation
        try:
            # Could integrate with various search APIs like Bing, Google, or DuckDuckGo
            # This is a placeholder for actual implementation
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            search_url = f"https://api.search.example.com?q={query}"
            
            # Placeholder for actual search results
            mock_results = [
                {
                    "title": f"Result for {query} - {i}",
                    "url": f"https://example.com/result-{i}",
                    "snippet": f"This is a snippet of information about {query}.",
                    "source": "example.com",
                    "published_date": datetime.datetime.now().isoformat()
                }
                for i in range(num_results)
            ]
            
            return mock_results
            
        except Exception as e:
            self.logger.error(f"Error searching web: {e}")
            return []
    
    def evaluate_source_reliability(self, source_info: Dict[str, Any]) -> float:
        """
        Evaluate the reliability of a source based on various factors
        
        Args:
            source_info: Information about the source
            
        Returns:
            Reliability score from 0.0 to 1.0
        """
        # This would implement actual source evaluation logic based on:
        # - Domain reputation
        # - Publication date
        # - Author credentials
        # - Cross-referencing with known reliable sources
        # - Checking for citations
        
        # Placeholder implementation
        reliability_factors = {
            "domain_score": 0.8,  # Would be based on domain reputation database
            "recency_score": 0.9,  # Based on how recent the publication is
            "citation_score": 0.7,  # Based on presence of citations
            "author_score": 0.75   # Based on author reputation
        }
        
        # Weighted average of factors
        reliability_score = sum(reliability_factors.values()) / len(reliability_factors)
        return min(max(reliability_score, 0.0), 1.0)  # Ensure between 0 and 1
    
    def fetch_and_parse_content(self, url: str) -> Optional[str]:
        """
        Fetch and parse content from a URL
        
        Args:
            url: The URL to fetch content from
            
        Returns:
            Parsed text content or None if failed
        """
        try:
            # Placeholder for actual implementation
            # Would use requests to get the content and BeautifulSoup to parse it
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # Mock content for demonstration
            content = f"This is the parsed content from {url}. It contains information that would be relevant to the search query."
            
            return content
        except Exception as e:
            self.logger.error(f"Error fetching content from {url}: {e}")
            return None
    
    def embed_and_store(self, text: str, source: str, reliability_score: float) -> None:
        """
        Create embeddings for text and store in the knowledge base
        
        Args:
            text: The text to embed
            source: Source information
            reliability_score: Reliability score of the source
        """
        if not self.embedding_model:
            self.logger.warning("Embedding model not available, skipping embedding")
            return
            
        try:
            # Create embedding
            embedding = self.embedding_model.encode(text)
            
            # Store in knowledge base
            self.knowledge_store["embeddings"].append(embedding)
            self.knowledge_store["texts"].append(text)
            self.knowledge_store["sources"].append(source)
            self.knowledge_store["reliability_scores"].append(reliability_score)
            self.knowledge_store["timestamps"].append(datetime.datetime.now().isoformat())
            
            # Update metrics
            KNOWLEDGE_STORE_SIZE.set(len(self.knowledge_store["texts"]))
            self._update_reliability_metrics()
            
            self.logger.info(f"Stored new knowledge from {source}")
        except Exception as e:
            self.logger.error(f"Error embedding and storing text: {e}")
    
    def semantic_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search the knowledge store for semantically similar content
        
        Args:
            query: The search query
            top_k: Number of top results to return
            
        Returns:
            List of search results with content and metadata
        """
        if not self.embedding_model or not self.knowledge_store["embeddings"]:
            self.logger.warning("No embeddings available for search")
            return []
            
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Calculate cosine similarities
            embeddings = np.array(self.knowledge_store["embeddings"])
            similarities = np.dot(embeddings, query_embedding) / (
                np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # Get top k results
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                results.append({
                    "text": self.knowledge_store["texts"][idx],
                    "source": self.knowledge_store["sources"][idx],
                    "reliability": self.knowledge_store["reliability_scores"][idx],
                    "timestamp": self.knowledge_store["timestamps"][idx],
                    "similarity": similarities[idx]
                })
                
            return results
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []
    
    def research(self, query: str, use_existing: bool = True, 
                min_reliability: float = 0.6) -> Dict[str, Any]:
        """
        Research a topic and return the results
        
        Args:
            query: The research query
            use_existing: Whether to use existing knowledge before searching
            min_reliability: Minimum reliability score for sources
            
        Returns:
            Research results with sources and reliability information
        """
        self.logger.info(f"Researching: {query}")
        start_time = time.time()
        
        REQUESTS_TOTAL.labels(type="research").inc()
        
        results = {
            "query": query,
            "timestamp": datetime.datetime.now().isoformat(),
            "sources": [],
            "content": [],
            "reliability_scores": [],
            "summary": ""
        }
        
        success = False
        try:
            # First check existing knowledge if requested
            if use_existing and self.knowledge_store["embeddings"]:
                existing_results = self.semantic_search(query)
                if existing_results:
                    self.logger.info(f"Found {len(existing_results)} existing results")
                    for result in existing_results:
                        if result["reliability"] >= min_reliability:
                            results["sources"].append(result["source"])
                            results["content"].append(result["text"])
                            results["reliability_scores"].append(result["reliability"])
            
            # If we don't have enough results, search the web
            if len(results["content"]) < 3:
                search_results = self.search_web(query)
                
                for search_result in search_results:
                    content = self.fetch_and_parse_content(search_result["url"])
                    if not content:
                        continue
                        
                    reliability = self.evaluate_source_reliability(search_result)
                    
                    if reliability >= min_reliability:
                        results["sources"].append(search_result["url"])
                        results["content"].append(content)
                        results["reliability_scores"].append(reliability)
                        
                        # Store this for future use
                        self.embed_and_store(content, search_result["url"], reliability)
            
            # Create a summary of the findings
            if results["content"]:
                # Would use an LLM to create a summary in real implementation
                results["summary"] = f"Found {len(results['content'])} relevant results for '{query}'"
                success = True
            
            return results
        finally:
            # Record metrics
            if success:
                REQUESTS_SUCCESS.labels(type="research").inc()
            
            # Record latency
            elapsed_time = time.time() - start_time
            LATENCY.labels(type="research").observe(elapsed_time)
    
    def process_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request from another agent
        
        Args:
            message: The request message
            
        Returns:
            Response message
        """
        request_type = message.get("request_type", "")
        query = message.get("query", "")
        
        REQUESTS_TOTAL.labels(type=request_type or "unknown").inc()
        start_time = time.time()
        
        try:
            if not query:
                return format_message("researcher", "No query provided in request")
            
            if request_type == "research":
                # Perform research on the query
                research_results = self.research(
                    query=query,
                    use_existing=message.get("use_existing", True),
                    min_reliability=message.get("min_reliability", 0.6)
                )
                
                REQUESTS_SUCCESS.labels(type=request_type).inc()
                return format_message("researcher", json.dumps(research_results))
            else:
                return format_message("researcher", f"Unknown request type: {request_type}")
        finally:
            elapsed_time = time.time() - start_time
            LATENCY.labels(type=request_type or "unknown").observe(elapsed_time) 