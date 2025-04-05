"""
Simple example of using the Upsonic agent framework.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import framework
from src.agent_base import KnowledgeBase

def main():
    # Create a simple knowledge base
    kb = KnowledgeBase(
        sources=[
            {
                "content": """
                Upsonic is a task-oriented AI agent framework for digital workers and vertical AI agents.
                It offers a cutting-edge enterprise-ready framework where you can orchestrate LLM calls, 
                agents, and computer use to complete tasks cost-effectively.
                
                Key features:
                - Tasks: Jobs with clear objectives that use specific tools.
                - Agents: LLMs that use tools to complete tasks.
                - Secure Runtime: Isolated environment to run agents.
                - Model Context Protocol: A tool standard for LLMs.
                """
            }
        ]
    )
    
    # Create a regular agent
    agent = framework.create_agent(
        name="Upsonic Expert",
        description="An expert on the Upsonic framework",
        model_name="llama3-70b",  # Using the model name from our config
        enable_memory=True,
        knowledge_base=kb
    )
    
    # Create an MCP agent
    mcp_agent = framework.create_mcp_agent(
        name="Desktop Commander",
        description="An agent that can control the desktop",
        model_name="llama3-70b",
        mcp_server_name="desktop_commander"
    )
    
    # Execute a simple task with the regular agent
    print("Executing task with regular agent...")
    result = agent.execute_task(
        "What is Upsonic and what are its key features?"
    )
    print(f"\nResult: {result}\n")
    
    # Execute a direct LLM call with the regular agent
    print("Executing direct LLM call...")
    result = agent.direct_llm_call(
        "What is the difference between an agent and a direct LLM call in Upsonic?"
    )
    print(f"\nResult: {result}\n")
    
    # Execute parallel tasks
    print("Executing parallel tasks...")
    results = framework.run_parallel_tasks([
        {
            "agent": agent,
            "task": "What are the advantages of using Upsonic for enterprise applications?"
        },
        {
            "agent": agent,
            "task": "How does the Model Context Protocol work in Upsonic?"
        }
    ])
    
    print("\nParallel task results:")
    for i, result in enumerate(results):
        print(f"\nTask {i+1} result: {result}")
    
if __name__ == "__main__":
    main() 