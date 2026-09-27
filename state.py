# state.py

class AgentState:
    """Maintain state across agent loop"""
    
    def __init__(self):
        self.attempts = 0
        self.max_attempts = 10
        self.tool_calls = []  # Log of all tool calls
        self.errors = []      # Failed attempts
        self.successful_tools = set()
        self.conversation_history = []
    
    def log_attempt(self, tool_name, success=True, error_msg=None):
        """Log a tool attempt"""
        self.attempts += 1
        
        self.tool_calls.append({
            "attempt": self.attempts,
            "tool": tool_name,
            "success": success,
            "error": error_msg
        })
        
        if success:
            self.successful_tools.add(tool_name)
        else:
            self.errors.append(error_msg)
    
    def should_continue(self):
        """Check if agent should continue"""
        return self.attempts < self.max_attempts
    
    def add_message(self, role, content):
        """Track conversation"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_context_summary(self):
        """Summarize state for LLM to avoid loops"""
        return f"""
Current attempt: {self.attempts}/{self.max_attempts}
Tools used successfully: {', '.join(self.successful_tools) or 'None yet'}
Previous errors: {self.errors[-2:] if self.errors else 'None'}
"""
    
    def print_log(self):
        """For debugging"""
        print("\n=== AGENT STATE ===")
        print(f"Attempts: {self.attempts}")
        print(f"Successful tools: {self.successful_tools}")
        print(f"Errors: {self.errors}")
