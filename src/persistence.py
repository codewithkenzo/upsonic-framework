"""
Module for persisting agents between sessions.
"""

import os
import json
import pickle
from typing import Dict, Any, Optional

class AgentStore:
    """Store for persisting agents between sessions."""
    
    def __init__(self, storage_dir="storage"):
        """Initialize a new agent store.
        
        Args:
            storage_dir (str, optional): Directory to store agent data. Defaults to "storage".
        """
        self.storage_dir = storage_dir
        
        # Create the storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Dictionary of loaded agents (agent_id -> agent)
        self.loaded_agents = {}
        
    def save_agent(self, agent_id: str, agent: Any) -> None:
        """Save an agent to the store.
        
        Args:
            agent_id (str): ID of the agent.
            agent (Any): Agent to save.
        """
        # Store the agent in memory
        self.loaded_agents[agent_id] = agent
        
        # Create the agent file path
        file_path = os.path.join(self.storage_dir, f"{agent_id}.json")
        
        # Extract basic agent info for JSON serialization
        agent_info = {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "description": agent.description,
            "model": agent.model,
            "memory": agent.agent.memory,
        }
        
        # Save agent info to JSON file
        with open(file_path, "w") as f:
            json.dump(agent_info, f, indent=2)
            
        # Save full agent object to pickle file
        pickle_path = os.path.join(self.storage_dir, f"{agent_id}.pickle")
        with open(pickle_path, "wb") as f:
            pickle.dump(agent, f)
        
    def load_agent(self, agent_id: str) -> Optional[Any]:
        """Load an agent from the store.
        
        Args:
            agent_id (str): ID of the agent to load.
            
        Returns:
            Optional[Any]: The loaded agent, or None if not found.
        """
        # Check if the agent is already loaded
        if agent_id in self.loaded_agents:
            return self.loaded_agents[agent_id]
            
        # Check if the agent file exists
        pickle_path = os.path.join(self.storage_dir, f"{agent_id}.pickle")
        if not os.path.exists(pickle_path):
            return None
            
        # Load the agent from pickle file
        try:
            with open(pickle_path, "rb") as f:
                agent = pickle.load(f)
                
            # Store the agent in memory
            self.loaded_agents[agent_id] = agent
            
            return agent
        except Exception as e:
            print(f"Error loading agent {agent_id}: {e}")
            return None
            
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent from the store.
        
        Args:
            agent_id (str): ID of the agent to delete.
            
        Returns:
            bool: True if the agent was deleted, False otherwise.
        """
        # Remove the agent from memory
        if agent_id in self.loaded_agents:
            del self.loaded_agents[agent_id]
            
        # Check if the agent files exist
        json_path = os.path.join(self.storage_dir, f"{agent_id}.json")
        pickle_path = os.path.join(self.storage_dir, f"{agent_id}.pickle")
        
        json_exists = os.path.exists(json_path)
        pickle_exists = os.path.exists(pickle_path)
        
        # Delete the files if they exist
        if json_exists:
            os.remove(json_path)
            
        if pickle_exists:
            os.remove(pickle_path)
            
        return json_exists or pickle_exists
        
    def list_agents(self) -> Dict[str, Dict]:
        """List all agents in the store.
        
        Returns:
            Dict[str, Dict]: Dictionary of agent IDs to agent info.
        """
        agents = {}
        
        # Get all JSON files in the storage directory
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                # Get the agent ID from the filename
                agent_id = filename[:-5]  # Remove the ".json" extension
                
                # Load the agent info from the JSON file
                file_path = os.path.join(self.storage_dir, filename)
                try:
                    with open(file_path, "r") as f:
                        agent_info = json.load(f)
                        
                    agents[agent_id] = agent_info
                except Exception as e:
                    print(f"Error loading agent info for {agent_id}: {e}")
                    
        return agents 