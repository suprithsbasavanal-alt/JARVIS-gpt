"""
brain.py
This file connects to the Ollama AI model to generate intelligent responses.
"""
import ollama
import logging

logging.basicConfig(filename='jarvis_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# This list keeps track of the conversation history so Jarvis remembers the context
conversation_history = []

def ask_ollama(prompt, memory_context="", model="llama3"):
    """
    Sends the user's prompt to the local Ollama model and gets a reply.
    
    Args:
        prompt (str): What the user said.
        memory_context (str): Relevant information retrieved from the memory database.
        model (str): The AI model to use (default is llama3).
        
    Returns:
        str: The AI's response.
    """
    try:
        # Create a system prompt that tells the AI how to behave
        system_message = {
            'role': 'system',
            'content': f"You are JARVIS, a highly intelligent and helpful personal AI assistant for a Mac user. Keep your answers concise, helpful, and natural. Here is what you know about the user from your permanent memory: {memory_context}"
        }
        
        # Add the user's message to the conversation history
        conversation_history.append({'role': 'user', 'content': prompt})
        
        # Combine system message and history for the AI
        messages = [system_message] + conversation_history
        
        # Call the Ollama API
        response = ollama.chat(model=model, messages=messages)
        
        # Get the text reply
        reply = response['message']['content']
        
        # Add the AI's reply to the history so it remembers what it said
        conversation_history.append({'role': 'assistant', 'content': reply})
        
        # Keep history from getting too long (keep last 10 messages)
        if len(conversation_history) > 10:
            # Remove oldest user/assistant pair
            conversation_history.pop(0)
            conversation_history.pop(0)
            
        return reply
        
    except Exception as e:
        error_msg = f"Error connecting to Ollama: {e}. Make sure Ollama app is running and the model '{model}' is installed."
        print(error_msg)
        logging.error(error_msg)
        return "I am sorry, but my AI brain is not responding. Please check if Ollama is running."
