"""Helper to extract structured data from agent responses for Cloud compatibility."""

import json
import logging
import re
from typing import Tuple, Optional, Dict, Any

import plotly.graph_objects as go

logger = logging.getLogger(__name__)


class AgentResponseParser:
    """Parse agent responses and extract structured data for Streamlit rendering."""

    @staticmethod
    def extract_plotly_chart(response_text: str) -> Tuple[str, Optional[Dict]]:
        """
        Extract Plotly JSON from agent response.

        Args:
            response_text: Agent response containing possible Plotly JSON

        Returns:
            Tuple of (remaining_text, plotly_dict or None)
        """
        try:
            remaining_text = response_text
            
            # Try to find JSON in code fence first
            code_fence_pattern = r'```json\n(.*?)\n```'
            match = re.search(code_fence_pattern, response_text, re.DOTALL)
            
            if match:
                json_str = match.group(1)
                remaining_text = re.sub(code_fence_pattern, '', response_text, count=1, flags=re.DOTALL)
            else:
                # Find raw JSON with brace matching
                json_start = response_text.find('{"data"')
                if json_start < 0:
                    json_start = response_text.find('{"marker"')
                
                if json_start >= 0:
                    brace_count = 0
                    json_end = json_start
                    in_string = False
                    escape_next = False
                    
                    for i in range(json_start, len(response_text)):
                        char = response_text[i]
                        
                        if escape_next:
                            escape_next = False
                            continue
                        
                        if char == '\\':
                            escape_next = True
                            continue
                        
                        if char == '"':
                            in_string = not in_string
                            continue
                        
                        if not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                    
                    if brace_count == 0 and json_end > json_start:
                        json_str = response_text[json_start:json_end]
                        remaining_text = response_text[:json_start] + response_text[json_end:]
                    else:
                        return response_text, None
                else:
                    return response_text, None
            
            # Parse and validate as Plotly
            plotly_dict = json.loads(json_str)
            
            if 'data' in plotly_dict and 'layout' in plotly_dict:
                return remaining_text.strip(), plotly_dict
            
        except (json.JSONDecodeError, AttributeError, KeyError, Exception) as e:
            logger.debug(f"Could not extract Plotly: {e}")
        
        return response_text, None

    @staticmethod
    def extract_file_reference(response_text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Extract file reference from agent response.

        Looks for patterns like:
        - "file_20251030_101329.xlsx"
        - "documents_with_issues_20251030_101329.csv"

        Args:
            response_text: Agent response

        Returns:
            Tuple of (remaining_text, file_info_dict or None)
        """
        try:
            # Pattern: {name}_{YYYYMMDD}_{HHMMSS}.{ext}
            file_pattern = r'([a-zA-Z0-9_]+_\d{8}_\d{6}\.(xlsx|csv|png|parquet))'
            match = re.search(file_pattern, response_text)
            
            if match:
                filename = match.group(1)
                ext = match.group(2)
                
                # Remove filename from text
                remaining_text = response_text[:match.start()] + response_text[match.end():]
                
                return remaining_text.strip(), {
                    "filename": filename,
                    "ext": ext
                }
        except Exception as e:
            logger.debug(f"Could not extract file reference: {e}")
        
        return response_text, None

    @staticmethod
    def parse_response(response_text: str) -> Dict[str, Any]:
        """
        Parse full agent response into structured components.

        Args:
            response_text: Full agent response

        Returns:
            Dict with keys:
            - text: Remaining markdown text
            - chart: Plotly dict if present
            - file: File reference dict if present
        """
        result = {
            "text": response_text,
            "chart": None,
            "file": None
        }
        
        # Extract chart first
        text, chart = AgentResponseParser.extract_plotly_chart(response_text)
        if chart:
            result["chart"] = chart
            result["text"] = text
        
        # Extract file reference from remaining text
        text, file_ref = AgentResponseParser.extract_file_reference(result["text"])
        if file_ref:
            result["file"] = file_ref
            result["text"] = text
        
        return result
