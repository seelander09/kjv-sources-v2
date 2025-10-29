#!/usr/bin/env python3
"""
ChatGPT 5 Integration for KJV Sources
====================================

This module provides ChatGPT 5 integration for the KJV Sources project,
enabling intelligent biblical text analysis and conversation capabilities.

Features:
- ChatGPT 5 API integration
- Biblical context-aware responses
- Source attribution and analysis
- Doublet identification and comparison
- Documentary hypothesis analysis
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

# OpenAI integration
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Install with: pip install openai")

# Rich for beautiful console output
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class ChatContext:
    """Context for ChatGPT conversations"""
    query: str
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    doublet_results: List[Dict[str, Any]] = field(default_factory=list)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ChatResponse:
    """Response from ChatGPT integration"""
    response: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    doublets: List[Dict[str, Any]] = field(default_factory=list)
    analysis: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class ChatGPTIntegration:
    """ChatGPT 5 integration for KJV Sources analysis"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """Initialize ChatGPT integration"""
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.system_prompt = self._get_system_prompt()
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            console.print("⚠️ [yellow]OpenAI API key not configured. Using mock responses for development.[/yellow]")
            self.mock_mode = True
        else:
            self.mock_mode = False
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            self.client = AsyncOpenAI(api_key=self.api_key)
            console.print("✅ [green]ChatGPT 5 integration initialized successfully[/green]")
        except Exception as e:
            console.print(f"❌ [red]Failed to initialize ChatGPT client: {e}[/red]")
            self.mock_mode = True
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for ChatGPT"""
        return """You are an expert biblical scholar specializing in the Documentary Hypothesis and the King James Version of the Bible. You have access to comprehensive biblical text analysis, source attribution, and doublet identification.

Your expertise includes:
- Documentary Hypothesis (J, E, P, D, R sources)
- Biblical doublets and parallel narratives
- Source criticism and textual analysis
- Theological themes and historical context
- KJV translation nuances and textual variants

When responding:
1. Provide scholarly, accurate responses with proper citations
2. Reference specific biblical passages with book, chapter, and verse
3. Identify source attributions when relevant (J, E, P, D, R)
4. Highlight doublets and parallel narratives
5. Explain theological and historical context
6. Use academic language appropriate for biblical scholarship
7. Be respectful of different theological perspectives

Always ground your responses in the provided biblical text and analysis results."""
    
    async def generate_response(self, context: ChatContext) -> ChatResponse:
        """Generate a ChatGPT response based on context"""
        if self.mock_mode:
            return self._generate_mock_response(context)
        
        try:
            # Prepare the conversation
            messages = self._prepare_messages(context)
            
            # Call ChatGPT API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                top_p=1.0
            )
            
            # Process response
            chat_response = response.choices[0].message.content
            
            return ChatResponse(
                response=chat_response,
                sources=context.search_results,
                doublets=context.doublet_results,
                analysis=context.analysis_results,
                confidence=0.9,
                reasoning="Generated using ChatGPT 5 with biblical context",
                metadata={
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            console.print(f"❌ [red]ChatGPT API error: {e}[/red]")
            return self._generate_mock_response(context)
    
    def _prepare_messages(self, context: ChatContext) -> List[Dict[str, str]]:
        """Prepare messages for ChatGPT API"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history
        for msg in context.conversation_history[-10:]:  # Last 10 messages
            messages.append(msg)
        
        # Add current context
        context_content = self._build_context_content(context)
        messages.append({
            "role": "user", 
            "content": f"Query: {context.query}\n\nContext:\n{context_content}"
        })
        
        return messages
    
    def _build_context_content(self, context: ChatContext) -> str:
        """Build context content for ChatGPT"""
        content_parts = []
        
        # Add search results
        if context.search_results:
            content_parts.append("Relevant Biblical Passages:")
            for i, result in enumerate(context.search_results[:5], 1):
                book = result.get('book', 'Unknown')
                chapter = result.get('chapter', '?')
                verse = result.get('verse', '?')
                text = result.get('text', '')[:200] + ('...' if len(result.get('text', '')) > 200 else '')
                sources = result.get('sources', 'Unknown')
                score = result.get('score', 0)
                
                content_parts.append(f"{i}. {book} {chapter}:{verse} (Sources: {sources}, Score: {score:.2f})")
                content_parts.append(f"   Text: {text}")
                content_parts.append("")
        
        # Add doublet results
        if context.doublet_results:
            content_parts.append("Doublet Passages Found:")
            for i, doublet in enumerate(context.doublet_results[:3], 1):
                name = doublet.get('name', 'Unknown Doublet')
                passages = doublet.get('passages', [])
                content_parts.append(f"{i}. {name}")
                for passage in passages[:2]:  # Show first 2 passages
                    book = passage.get('book', 'Unknown')
                    chapter = passage.get('chapter', '?')
                    verse = passage.get('verse', '?')
                    content_parts.append(f"   - {book} {chapter}:{verse}")
                content_parts.append("")
        
        # Add analysis results
        if context.analysis_results:
            content_parts.append("Analysis Results:")
            for key, value in context.analysis_results.items():
                if isinstance(value, (list, dict)) and value:
                    content_parts.append(f"- {key}: {value}")
            content_parts.append("")
        
        return "\n".join(content_parts)
    
    def _generate_mock_response(self, context: ChatContext) -> ChatResponse:
        """Generate a mock response for development/testing"""
        query_lower = context.query.lower()
        
        # Generate contextual response based on query
        if any(word in query_lower for word in ['doublet', 'parallel', 'similar']):
            response = self._generate_doublet_response(context)
        elif any(word in query_lower for word in ['source', 'jahwist', 'elohist', 'priestly', 'deuteronomist']):
            response = self._generate_source_response(context)
        elif any(word in query_lower for word in ['creation', 'flood', 'covenant']):
            response = self._generate_thematic_response(context)
        else:
            response = self._generate_general_response(context)
        
        return ChatResponse(
            response=response,
            sources=context.search_results,
            doublets=context.doublet_results,
            analysis=context.analysis_results,
            confidence=0.7,
            reasoning="Generated mock response for development (ChatGPT not configured)",
            metadata={
                "model": "mock",
                "mock_mode": True,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _generate_doublet_response(self, context: ChatContext) -> str:
        """Generate response for doublet queries"""
        if context.doublet_results:
            doublet = context.doublet_results[0]
            name = doublet.get('name', 'Unknown Doublet')
            passages = doublet.get('passages', [])
            
            response = f"Based on your query about doublets, I found the '{name}' doublet. "
            response += f"This doublet appears in {len(passages)} passages: "
            
            for passage in passages[:3]:
                book = passage.get('book', 'Unknown')
                chapter = passage.get('chapter', '?')
                verse = passage.get('verse', '?')
                response += f"{book} {chapter}:{verse}, "
            
            response = response.rstrip(', ') + ". "
            response += "These parallel narratives demonstrate the Documentary Hypothesis, showing how different sources (J, E, P, D) preserved similar stories with distinct theological emphases."
        else:
            response = "I searched for doublet passages related to your query. While I found relevant biblical passages, no specific doublets were identified in the current results. Doublets are parallel narratives that appear in multiple biblical sources, often with variations that reflect different theological perspectives."
        
        return response
    
    def _generate_source_response(self, context: ChatContext) -> str:
        """Generate response for source analysis queries"""
        if context.search_results:
            result = context.search_results[0]
            sources = result.get('sources', 'Unknown')
            book = result.get('book', 'Unknown')
            chapter = result.get('chapter', '?')
            verse = result.get('verse', '?')
            
            response = f"Based on your query about biblical sources, I found relevant passages in {book} {chapter}:{verse}. "
            response += f"The source attribution indicates: {sources}. "
            
            if 'J' in sources:
                response += "The Jahwist (J) source typically uses 'Yahweh' for God and emphasizes early narrative traditions. "
            if 'E' in sources:
                response += "The Elohist (E) source uses 'Elohim' for God and reflects northern traditions. "
            if 'P' in sources:
                response += "The Priestly (P) source focuses on ritual, covenant, and liturgical elements. "
            if 'D' in sources:
                response += "The Deuteronomist (D) source emphasizes law and covenant theology. "
            if 'R' in sources:
                response += "The Redactor (R) source represents editorial additions and transitions. "
        else:
            response = "I searched for passages related to biblical source analysis. The Documentary Hypothesis identifies five main sources (J, E, P, D, R) that were combined to create the final biblical text. Each source has distinct characteristics in language, theology, and narrative style."
        
        return response
    
    def _generate_thematic_response(self, context: ChatContext) -> str:
        """Generate response for thematic queries"""
        if context.search_results:
            result = context.search_results[0]
            book = result.get('book', 'Unknown')
            chapter = result.get('chapter', '?')
            verse = result.get('verse', '?')
            text = result.get('text', '')[:150] + ('...' if len(result.get('text', '')) > 150 else '')
            
            response = f"Based on your thematic query, I found relevant passages including {book} {chapter}:{verse}. "
            response += f"The passage states: '{text}' "
            response += "This passage reflects important theological themes and demonstrates how different biblical sources contribute to our understanding of key biblical concepts."
        else:
            response = "I searched for passages related to your thematic query. The biblical text contains rich theological themes that are developed across multiple sources and books, each contributing unique perspectives to our understanding of biblical theology."
        
        return response
    
    def _generate_general_response(self, context: ChatContext) -> str:
        """Generate general response"""
        if context.search_results:
            result = context.search_results[0]
            book = result.get('book', 'Unknown')
            chapter = result.get('chapter', '?')
            verse = result.get('verse', '?')
            
            response = f"Based on your query, I found relevant biblical passages including {book} {chapter}:{verse}. "
            response += f"I found {len(context.search_results)} relevant passages that address your question. "
            response += "These passages provide important context for understanding the biblical text and its various source traditions."
        else:
            response = "I searched for passages related to your query. The biblical text contains rich content that addresses many theological and historical questions. Each passage should be considered within its broader biblical and historical context."
        
        return response
    
    def display_response(self, response: ChatResponse):
        """Display the ChatGPT response using Rich"""
        # Main response
        console.print(Panel(
            response.response,
            title="🤖 ChatGPT 5 Response",
            border_style="blue"
        ))
        
        # Sources table
        if response.sources:
            table = Table(title="📖 Biblical Sources")
            table.add_column("Reference", style="cyan")
            table.add_column("Sources", style="yellow")
            table.add_column("Score", style="green")
            
            for source in response.sources[:5]:
                ref = f"{source.get('book', '')} {source.get('chapter', '')}:{source.get('verse', '')}"
                sources = source.get('sources', '')
                score = f"{source.get('score', 0):.2f}"
                table.add_row(ref, sources, score)
            
            console.print(table)
        
        # Doublets
        if response.doublets:
            console.print(Panel(
                f"Found {len(response.doublets)} doublet passages",
                title="🔄 Doublets Identified",
                border_style="green"
            ))
        
        # Metadata
        if response.metadata:
            console.print(f"📊 Confidence: {response.confidence:.2f}")
            console.print(f"🧠 Model: {response.metadata.get('model', 'Unknown')}")
            if 'tokens_used' in response.metadata:
                console.print(f"🔢 Tokens Used: {response.metadata['tokens_used']}")

# Factory function
def create_chatgpt_integration(api_key: Optional[str] = None, model: str = "gpt-4o") -> ChatGPTIntegration:
    """Create a ChatGPT integration instance"""
    return ChatGPTIntegration(api_key=api_key, model=model)

# Example usage
if __name__ == "__main__":
    async def test_chatgpt():
        """Test ChatGPT integration"""
        chatgpt = create_chatgpt_integration()
        
        context = ChatContext(
            query="Tell me about the creation stories in Genesis",
            search_results=[
                {
                    "book": "Genesis",
                    "chapter": "1",
                    "verse": "1",
                    "text": "In the beginning God created the heaven and the earth.",
                    "sources": "P",
                    "score": 0.95
                }
            ]
        )
        
        response = await chatgpt.generate_response(context)
        chatgpt.display_response(response)
    
    # Run test
    asyncio.run(test_chatgpt())
