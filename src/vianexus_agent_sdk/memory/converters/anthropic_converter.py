"""
Message converter for Anthropic Claude API format.
"""

from typing import List, Any, Dict
from ..base_memory import UniversalMessage, MessageRole, MessageType


class AnthropicMessageConverter:
    """Converts between Anthropic messages and UniversalMessage format."""
    
    def to_universal(self, anthropic_message: Dict[str, Any]) -> UniversalMessage:
        """Convert Anthropic message format to UniversalMessage."""
        role = MessageRole(anthropic_message["role"])
        content = anthropic_message["content"]
        
        # Determine message type based on content structure
        message_type = MessageType.TEXT
        tool_calls = None
        tool_results = None
        
        if isinstance(content, list):
            # Check for tool usage in content blocks
            has_tool_use = any(
                isinstance(block, dict) and block.get("type") == "tool_use" 
                for block in content
            )
            has_tool_result = any(
                isinstance(block, dict) and block.get("type") == "tool_result" 
                for block in content
            )
            
            if has_tool_use:
                message_type = MessageType.TOOL_CALL
                tool_calls = [
                    block for block in content 
                    if isinstance(block, dict) and block.get("type") == "tool_use"
                ]
            elif has_tool_result:
                message_type = MessageType.TOOL_RESULT
                tool_results = [
                    block for block in content 
                    if isinstance(block, dict) and block.get("type") == "tool_result"
                ]
        
        return UniversalMessage(
            role=role,
            content=content,
            message_type=message_type,
            provider="anthropic",
            raw_content=anthropic_message,
            tool_calls=tool_calls,
            tool_results=tool_results
        )
    
    def from_universal(self, universal_message: UniversalMessage) -> Dict[str, Any]:
        """Convert UniversalMessage back to Anthropic format."""
        # If we have the raw content and it's from Anthropic, use it
        if (universal_message.raw_content and 
            universal_message.provider == "anthropic" and
            isinstance(universal_message.raw_content, dict)):
            return universal_message.raw_content
        
        # Otherwise construct from universal format
        return {
            "role": universal_message.role.value,
            "content": universal_message.content
        }
    
    def to_universal_batch(self, anthropic_messages: List[Dict]) -> List[UniversalMessage]:
        """Convert batch of Anthropic messages."""
        return [self.to_universal(msg) for msg in anthropic_messages]
    
    def from_universal_batch(self, universal_messages: List[UniversalMessage]) -> List[Dict]:
        """Convert batch back to Anthropic format."""
        return [self.from_universal(msg) for msg in universal_messages]
    
    def extract_text_content(self, anthropic_message: Dict[str, Any]) -> str:
        """Extract text content from Anthropic message for search/display."""
        content = anthropic_message.get("content", "")
        
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        # Include tool name for searchability
                        tool_name = block.get("name", "unknown_tool")
                        text_parts.append(f"[Tool: {tool_name}]")
                    elif block.get("type") == "tool_result":
                        # Include tool result summary
                        text_parts.append("[Tool Result]")
                elif isinstance(block, str):
                    text_parts.append(block)
            
            return " ".join(text_parts)
        
        return str(content)
