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
        Tries multiple patterns to find JSON in the response.

        Args:
            response_text: Agent response containing possible Plotly JSON

        Returns:
            Tuple of (remaining_text_without_json, plotly_dict or None)
        """
        try:
            remaining_text = response_text
            json_str = None
            
            # Pattern 1: ```json\n...\n```
            match = re.search(r'```json\s*\n(.*?)\n\s*```', response_text, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                remaining_text = re.sub(r'```json\s*\n(.*?)\n\s*```', '', response_text, count=1, flags=re.DOTALL)
                logger.debug("Found JSON in pattern 1: ```json...```")
            
            # Pattern 2: ```json...\n``` (no newline after json keyword)
            if not json_str:
                match = re.search(r'```json(.*?)\n```', response_text, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                    remaining_text = re.sub(r'```json(.*?)\n```', '', response_text, count=1, flags=re.DOTALL)
                    logger.debug("Found JSON in pattern 2: ```json...```")
            
            # Pattern 3: Plain ``` with JSON inside
            if not json_str:
                match = re.search(r'```\s*\n\s*(\{[\s\S]*?\})\s*\n```', response_text, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                    remaining_text = re.sub(r'```\s*\n\s*(\{[\s\S]*?\})\s*\n```', '', response_text, count=1, flags=re.DOTALL)
                    logger.debug("Found JSON in pattern 3: ```...```")
            
            # Pattern 4: Raw JSON without code fences (starts with {)
            if not json_str:
                # Look for {"data" or {"marker"
                for json_start_pattern in ['{"data"', '{"marker"', '{', '{"layout"']:
                    json_start = response_text.find(json_start_pattern)
                    if json_start >= 0:
                        # Use brace matching to find end
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
                            logger.debug(f"Found raw JSON in pattern 4 starting with: {json_start_pattern}")
                            break
            
            # Try to parse JSON
            if json_str:
                try:
                    plotly_dict = json.loads(json_str)
                    
                    # Verify it's a Plotly figure (has 'data' and 'layout')
                    if 'data' in plotly_dict and 'layout' in plotly_dict:
                        logger.debug("Successfully extracted and validated Plotly chart")
                        return remaining_text.strip(), plotly_dict
                    else:
                        logger.debug(f"JSON found but not a valid Plotly figure. Keys: {list(plotly_dict.keys())}")
                        return response_text, None
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON parsing failed: {e}")
                    return response_text, None
            
            logger.debug("No JSON found in any pattern")
            return response_text, None
            
        except Exception as e:
            logger.error(f"Error extracting Plotly chart: {e}", exc_info=True)
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
