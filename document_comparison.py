"""
Document Comparison Module

This module provides functionality for comparing legal documents,
identifying similarities, differences, and generating visual comparisons.
"""

import logging
import difflib
import re
from typing import Dict, List, Tuple, Any
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compare_documents(doc_texts: Dict[str, str], doc_names: Dict[str, str], 
                      comparison_type: str = "General Comparison") -> Dict[str, Any]:
    """
    Compare two or more legal documents and provide structured comparison results.
    
    Args:
        doc_texts: Dictionary of document texts with document IDs as keys
        doc_names: Dictionary of document names with document IDs as keys
        comparison_type: Type of comparison to perform (General, Legal Clauses, etc.)
        
    Returns:
        Dictionary containing structured comparison results
    """
    if not doc_texts or len(doc_texts) < 2:
        return {"error": "At least two documents are required for comparison"}
    
    try:
        # Initialize results structure
        results = {
            "analysis": f"Comparing documents: {', '.join(doc_names.values())}",
            "similarity": 0,
            "key_differences": {},
            "common_elements": {},
            "diff": []
        }
        
        # For direct comparison between two documents
        if len(doc_texts) == 2:
            doc_ids = list(doc_texts.keys())
            doc1_text = doc_texts[doc_ids[0]]
            doc2_text = doc_texts[doc_ids[1]]
            doc1_name = doc_names[doc_ids[0]]
            doc2_name = doc_names[doc_ids[1]]
            
            # Calculate text similarity
            matcher = difflib.SequenceMatcher(None, doc1_text, doc2_text)
            similarity = round(matcher.ratio() * 100, 1)
            results["similarity"] = similarity
            
            # Generate textual diff
            doc1_lines = doc1_text.splitlines()
            doc2_lines = doc2_text.splitlines()
            
            diff = list(difflib.unified_diff(
                doc1_lines, 
                doc2_lines, 
                fromfile=doc1_name, 
                tofile=doc2_name,
                lineterm=''
            ))
            results["diff"] = diff
            
            # Get AI-powered analysis based on comparison type
            ai_analysis = _get_ai_analysis(doc_texts, doc_names, comparison_type)
            
            # If AI analysis succeeded, incorporate it
            if "error" not in ai_analysis:
                results["analysis"] = ai_analysis.get("analysis", results["analysis"])
                results["key_differences"] = ai_analysis.get("key_differences", {})
                results["common_elements"] = ai_analysis.get("common_elements", {})
            else:
                # Fall back to rule-based analysis if AI fails
                results.update(_get_rule_based_analysis(doc_texts, doc_names, comparison_type))
        
        # For comparing more than two documents
        else:
            # Use rule-based comparison for multi-document comparison
            results.update(_get_rule_based_analysis(doc_texts, doc_names, comparison_type))
        
        return results
        
    except Exception as e:
        logger.error(f"Error in document comparison: {str(e)}")
        return {
            "error": f"Error during comparison: {str(e)}",
            "analysis": "An error occurred during the comparison process. Please try again with shorter documents."
        }

def _get_ai_analysis(doc_texts: Dict[str, str], doc_names: Dict[str, str], 
                    comparison_type: str) -> Dict[str, Any]:
    """
    Get AI-powered analysis of document differences using Gemini API.
    
    Args:
        doc_texts: Dictionary of document texts
        doc_names: Dictionary of document names
        comparison_type: Type of comparison to perform
        
    Returns:
        Dictionary containing AI analysis results
    """
    try:
        # Only handle direct 2-document comparison for AI analysis
        if len(doc_texts) != 2:
            return {"error": "AI analysis only supports two-document comparison"}
        
        # Get document IDs and texts
        doc_ids = list(doc_texts.keys())
        doc1_name = doc_names[doc_ids[0]]
        doc2_name = doc_names[doc_ids[1]]
        
        # Limit text length to avoid token limits
        max_chars = 2500  # Conservative limit
        doc1_text = doc_texts[doc_ids[0]][:max_chars] + ("..." if len(doc_texts[doc_ids[0]]) > max_chars else "")
        doc2_text = doc_texts[doc_ids[1]][:max_chars] + ("..." if len(doc_texts[doc_ids[1]]) > max_chars else "")
        
        # Custom prompt based on comparison type
        focus_instructions = {
            "General Comparison": "Compare these documents generally, highlighting similarities and differences.",
            "Legal Clauses": "Focus on legal clauses, terms, and conditions. Compare how they differ between documents.",
            "Compliance Elements": "Focus on compliance aspects like regulatory requirements and governance provisions.",
            "Risk Factors": "Focus on risk elements, liabilities, and how risks are addressed in each document."
        }
        
        # Build the complete prompt
        prompt = (
            f"Compare these two legal documents:\n\n"
            f"Document 1 ({doc1_name}):\n{doc1_text}\n\n"
            f"Document 2 ({doc2_name}):\n{doc2_text}\n\n"
            f"{focus_instructions.get(comparison_type, focus_instructions['General Comparison'])}\n\n"
            f"Provide your analysis in this format:\n"
            f"1. A paragraph explaining the main comparison findings\n"
            f"2. Key differences organized by category\n"
            f"3. Common elements shared between documents\n"
        )
        
        # Call Gemini API
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(prompt)
        
        if not response or not hasattr(response, "text"):
            return {"error": "No valid response from AI"}
        
        # Parse the response into structured format
        analysis_text = response.text.strip()
        
        # Extract the main analysis paragraph
        analysis_match = re.search(r"^(.*?)(?=Key Differences:|Common Elements:|\n\n)", 
                                 analysis_text, re.DOTALL | re.IGNORECASE)
        analysis = analysis_match.group(1).strip() if analysis_match else "Analysis not available."
        
        # Extract key differences
        key_diff_match = re.search(r"Key Differences:(.*?)(?=Common Elements:|\Z)", 
                                  analysis_text, re.DOTALL | re.IGNORECASE)
        key_diff_text = key_diff_match.group(1).strip() if key_diff_match else ""
        
        # Extract common elements
        common_match = re.search(r"Common Elements:(.*?)(?=\Z)", 
                                analysis_text, re.DOTALL | re.IGNORECASE)
        common_text = common_match.group(1).strip() if common_match else ""
        
        # Convert the extracted sections to structured format
        key_differences = _parse_section_to_dict(key_diff_text, doc1_name, doc2_name)
        common_elements = _parse_common_elements(common_text)
        
        return {
            "analysis": analysis,
            "key_differences": key_differences,
            "common_elements": common_elements
        }
        
    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        return {"error": f"AI analysis failed: {str(e)}"}

def _get_rule_based_analysis(doc_texts: Dict[str, str], doc_names: Dict[str, str], 
                            comparison_type: str) -> Dict[str, Any]:
    """
    Get rule-based analysis when AI is not available or for multiple documents.
    
    Args:
        doc_texts: Dictionary of document texts
        doc_names: Dictionary of document names
        comparison_type: Type of comparison to perform
        
    Returns:
        Dictionary containing rule-based analysis results
    """
    # Initialize analysis structures
    key_differences = {}
    common_elements = {}
    
    # General description based on document count
    if len(doc_texts) == 2:
        doc_ids = list(doc_texts.keys())
        doc1_text = doc_texts[doc_ids[0]].lower()
        doc2_text = doc_texts[doc_ids[1]].lower()
        doc1_name = doc_names[doc_ids[0]]
        doc2_name = doc_names[doc_ids[1]]
        
        # Calculate similarity
        matcher = difflib.SequenceMatcher(None, doc1_text, doc2_text)
        similarity = round(matcher.ratio() * 100, 1)
        
        # Generate basic analysis based on similarity
        if similarity >= 80:
            analysis = f"The documents are very similar ({similarity}% match). There are only minor differences between them."
        elif similarity >= 50:
            analysis = f"The documents have moderate similarity ({similarity}% match). There are several significant differences to review."
        else:
            analysis = f"The documents are substantially different ({similarity}% match). Major differences exist between these documents."
        
        # Different keyword sets based on comparison type
        if comparison_type == "Legal Clauses":
            keywords = ["agreement", "clause", "provision", "term", "condition", "covenant", 
                       "warranty", "liability", "termination"]
            key_differences["Legal Terms"] = []
            common_elements["Legal Terms"] = []
            
        elif comparison_type == "Compliance Elements":
            keywords = ["compliance", "regulation", "regulatory", "law", "standard", "requirement", 
                       "policy", "procedure", "governance", "audit"]
            key_differences["Compliance"] = []
            common_elements["Compliance"] = []
            
        elif comparison_type == "Risk Factors":
            keywords = ["risk", "liability", "penalty", "damage", "breach", "violation", 
                       "failure", "claim", "dispute", "litigation"]
            key_differences["Risk Elements"] = []
            common_elements["Risk Elements"] = []
            
        else:  # General Comparison
            keywords = ["introduction", "conclusion", "summary", "background", "scope", 
                       "purpose", "objective", "definition", "term", "condition"]
            key_differences["General Elements"] = []
            common_elements["General Elements"] = []
        
        # Find differences and similarities based on keywords
        category = list(key_differences.keys())[0]  # The main category based on comparison type
        
        for keyword in keywords:
            # Check for presence in each document
            in_doc1 = keyword in doc1_text
            in_doc2 = keyword in doc2_text
            
            if in_doc1 != in_doc2:
                # This is a difference
                key_differences[category].append({
                    "title": f"'{keyword.title()}' Reference",
                    "doc1": f"Present in document" if in_doc1 else "Not found in document",
                    "doc2": f"Present in document" if in_doc2 else "Not found in document"
                })
            elif in_doc1 and in_doc2:
                # This is a similarity
                common_elements[category].append({
                    "title": f"'{keyword.title()}' Element",
                    "content": f"Both documents contain references to '{keyword}'"
                })
                
    else:
        # Multi-document comparison (simpler)
        doc_count = len(doc_texts)
        analysis = f"Comparing {doc_count} documents: {', '.join(doc_names.values())}. Multi-document comparison provides limited detailed analysis."
        
        # Basic multi-document keyword analysis
        key_differences["Multi-Document Analysis"] = []
        common_elements["Shared Elements"] = []
        
        # Find keywords present in all documents
        keywords = ["agreement", "contract", "term", "condition", "clause", "provision", 
                  "party", "date", "signature", "termination", "payment", "obligation"]
                  
        for keyword in keywords:
            # Count documents containing this keyword
            docs_with_keyword = sum(1 for doc_text in doc_texts.values() 
                                   if keyword in doc_text.lower())
            
            if 0 < docs_with_keyword < len(doc_texts):
                # Term exists in some but not all documents
                key_differences["Multi-Document Analysis"].append({
                    "title": f"'{keyword.title()}' Term Variance",
                    "content": f"This term appears in {docs_with_keyword} out of {len(doc_texts)} documents"
                })
            elif docs_with_keyword == len(doc_texts):
                # Term exists in all documents
                common_elements["Shared Elements"].append({
                    "title": f"'{keyword.title()}' Term",
                    "content": f"All documents contain references to '{keyword}'"
                })
    
    return {
        "analysis": analysis,
        "key_differences": key_differences,
        "common_elements": common_elements
    }

def _parse_section_to_dict(section_text: str, doc1_name: str, doc2_name: str) -> Dict[str, List[Dict]]:
    """
    Parse a text section into a structured dictionary format.
    
    Args:
        section_text: Text to parse
        doc1_name: Name of first document
        doc2_name: Name of second document
        
    Returns:
        Dictionary of parsed elements
    """
    if not section_text:
        return {}
    
    result = {}
    current_category = "Uncategorized"
    
    # Split the text into lines for processing
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a category heading
        if line.endswith(':') or (len(line) < 50 and not line.startswith('-') and not line.startswith('*')):
            current_category = line.rstrip(':').strip()
            if current_category not in result:
                result[current_category] = []
        elif line.startswith('-') or line.startswith('*'):
            # This is a bullet point
            content = line[1:].strip()
            
            # Try to split into document-specific differences
            doc_split = content.split('vs.') if 'vs.' in content else content.split('while')
            
            if len(doc_split) == 2:
                # We have a comparison between two documents
                result[current_category].append({
                    "title": current_category,
                    "doc1": doc_split[0].strip(),
                    "doc2": doc_split[1].strip()
                })
            else:
                # General difference
                result[current_category].append({
                    "title": current_category,
                    "doc1": content,
                    "doc2": "Differs"
                })
    
    return result

def _parse_common_elements(section_text: str) -> Dict[str, List[Dict]]:
    """
    Parse common elements section into a structured dictionary format.
    
    Args:
        section_text: Text to parse
        
    Returns:
        Dictionary of parsed common elements
    """
    if not section_text:
        return {}
    
    result = {}
    current_category = "Shared Elements"
    
    # Split the text into lines for processing
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a category heading
        if line.endswith(':') or (len(line) < 50 and not line.startswith('-') and not line.startswith('*')):
            current_category = line.rstrip(':').strip()
            if current_category not in result:
                result[current_category] = []
        elif line.startswith('-') or line.startswith('*'):
            # This is a bullet point
            content = line[1:].strip()
            
            result[current_category].append({
                "title": content.split(':')[0].strip() if ':' in content else current_category,
                "content": content.split(':', 1)[1].strip() if ':' in content else content
            })
    
    return result
