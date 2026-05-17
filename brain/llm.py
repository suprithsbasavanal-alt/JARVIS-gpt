"""
brain/llm.py
Handles the integration with Ollama for offline AI capabilities.
Also manages the AI's persona as JARVIS.
"""
import ollama
import memory.database as db
import memory.rag as rag

# Keep a short history in memory to maintain context during a session
session_history = []

def generate_response(user_input, custom_system_prompt=None):
    """
    Sends the user's input to the local Llama3 model via Ollama.
    It injects persistent memory into the system prompt, or uses a custom one for agents.
    """
    # 1. Gather context from persistent memory & RAG
    facts = db.get_all_facts()
    tasks = db.get_tasks()
    user_name = db.get_fact("name") or "Sir"
    
    # Search RAG memory for semantic matches to the user_input
    rag_results = rag.search_memory(user_input, top_k=2)
    rag_context = ""
    if rag_results:
        rag_context = "Relevant long-term memories: " + " | ".join(rag_results) + ". "
    
    if custom_system_prompt:
        context = custom_system_prompt + "\n" + rag_context
    else:
        context = f"You are JARVIS, a highly advanced, futuristic AI assistant running on macOS. Your user is {user_name}. "
        context += f"You have the following facts in your memory: {facts}. "
        if tasks:
            context += f"The user has these pending tasks: {', '.join(tasks)}. "
        context += rag_context
        context += "Be concise, professional, and highly intelligent, like Tony Stark's JARVIS. If asked to write code, provide it clearly."

    system_message = {"role": "system", "content": context}
    
    # 2. Append user input to session history
    session_history.append({"role": "user", "content": user_input})
    
    # Keep history manageable (last 10 interactions)
    if len(session_history) > 20:
        session_history.pop(0)
        
    messages = [system_message] + session_history
    
    try:
        print("JARVIS is thinking...")
        # 3. Call Ollama
        response = ollama.chat(model='llama3', messages=messages)
        ai_reply = response['message']['content']
        
        # 4. Save AI reply to history
        session_history.append({"role": "assistant", "content": ai_reply})
        return ai_reply
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "I am currently unable to connect to my neural network. Please ensure Ollama is running and the llama3 model is installed."
