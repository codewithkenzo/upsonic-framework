"""
Module for managing knowledge bases for agents.
"""

import os
from typing import List, Optional, Union, Dict

from src.agent_base import KnowledgeBase

class KnowledgeManager:
    """Manager for agent knowledge bases."""
    
    def __init__(self, knowledge_dir="knowledge"):
        """Initialize a new knowledge manager.
        
        Args:
            knowledge_dir (str, optional): Directory to store knowledge files. Defaults to "knowledge".
        """
        self.knowledge_dir = knowledge_dir
        
        # Create the knowledge directory if it doesn't exist
        os.makedirs(knowledge_dir, exist_ok=True)
        
    def create_knowledge_base(
        self,
        name: str,
        sources: List[Union[str, Dict[str, str]]],
        rag_enabled: bool = False,
        rag_model: Optional[str] = None
    ) -> KnowledgeBase:
        """Create a new knowledge base.
        
        Args:
            name (str): Name of the knowledge base.
            sources (List[Union[str, Dict[str, str]]]): List of source files or content dictionaries.
            rag_enabled (bool, optional): Whether to enable RAG. Defaults to False.
            rag_model (Optional[str], optional): RAG model to use. Defaults to None.
                Required if rag_enabled is True.
                
        Returns:
            KnowledgeBase: The created knowledge base.
        """
        if rag_enabled and rag_model is None:
            raise ValueError("rag_model must be provided when rag_enabled is True")
            
        # Create the knowledge base
        # Note: In our simplified implementation, we ignore rag_enabled and rag_model
        kb = KnowledgeBase(
            sources=sources
        )
            
        return kb
        
    def create_from_text(
        self,
        name: str,
        texts: Dict[str, str],
        rag_enabled: bool = False,
        rag_model: Optional[str] = None
    ) -> KnowledgeBase:
        """Create a knowledge base from text content.
        
        Args:
            name (str): Name of the knowledge base.
            texts (Dict[str, str]): Dictionary of text sources (name -> content).
            rag_enabled (bool, optional): Whether to enable RAG. Defaults to False.
            rag_model (Optional[str], optional): RAG model to use. Defaults to None.
                Required if rag_enabled is True.
                
        Returns:
            KnowledgeBase: The created knowledge base.
        """
        # Create file sources from texts
        sources = []
        
        for text_name, text_content in texts.items():
            # Create a file for the text
            file_path = os.path.join(self.knowledge_dir, f"{name}_{text_name}.txt")
            
            with open(file_path, "w") as f:
                f.write(text_content)
                
            sources.append(file_path)
            
        # Create the knowledge base
        return self.create_knowledge_base(
            name=name,
            sources=sources,
            rag_enabled=rag_enabled,
            rag_model=rag_model
        )
        
    def create_from_urls(
        self,
        name: str,
        urls: List[str],
        rag_enabled: bool = False,
        rag_model: Optional[str] = None
    ) -> KnowledgeBase:
        """Create a knowledge base from URLs.
        
        Args:
            name (str): Name of the knowledge base.
            urls (List[str]): List of URLs to get content from.
            rag_enabled (bool, optional): Whether to enable RAG. Defaults to False.
            rag_model (Optional[str], optional): RAG model to use. Defaults to None.
                Required if rag_enabled is True.
                
        Returns:
            KnowledgeBase: The created knowledge base.
        """
        # In a real implementation, this would fetch the content from the URLs
        # For now, we'll just use the URLs as sources
        
        # Create the knowledge base
        return self.create_knowledge_base(
            name=name,
            sources=urls,
            rag_enabled=rag_enabled,
            rag_model=rag_model
        ) 