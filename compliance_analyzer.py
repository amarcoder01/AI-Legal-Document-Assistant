"""
Compliance Analyzer Module

Provides comprehensive document analysis for regulatory and policy adherence across
multiple frameworks including GDPR, HIPAA, ISO 27001, and custom standards.
"""

import re
import json
import os
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class ComplianceRule:
    id: str
    framework: str
    description: str
    required_clauses: List[str]
    keywords: List[str]
    risk_level: str
    validation_regex: Optional[str] = None
    
    def __post_init__(self):
        # Convert lists to sets for faster lookups
        if isinstance(self.required_clauses, list):
            self.required_clauses = set(self.required_clauses)
        if isinstance(self.keywords, list):
            self.keywords = set(self.keywords)

@dataclass
class ComplianceIssue:
    rule_id: str
    section: str
    description: str
    risk_level: str
    line_number: int
    suggested_fix: str

class ComplianceAnalyzer:
    def __init__(self, config_path: Optional[str] = None):
        self.rules: Dict[str, ComplianceRule] = {}
        self.logger = logging.getLogger(__name__)
        self._load_rules(config_path)

    def _load_rules(self, config_path: Optional[str] = None) -> None:
        """Load compliance rules from configuration file or use defaults."""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    rules_data = json.load(f)
                    for rule in rules_data.get("rules", []):
                        self.rules[rule['id']] = ComplianceRule(**rule)
            except Exception as e:
                self.logger.error(f"Error loading rules: {e}")
                self._load_default_rules()
        else:
            self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load built-in compliance rules for common frameworks."""
        default_rules = [
            ComplianceRule(
                id="GDPR-001",
                framework="GDPR",
                description="Data Processing Consent",
                required_clauses=["consent", "data processing", "personal data"],
                keywords=["explicit consent", "opt-in", "data collection"],
                risk_level="HIGH"
            ),
            ComplianceRule(
                id="HIPAA-001",
                framework="HIPAA",
                description="PHI Protection",
                required_clauses=["health information", "confidentiality", "security"],
                keywords=["PHI", "medical records", "health data"],
                risk_level="CRITICAL"
            ),
            ComplianceRule(
                id="ISO27001-001",
                framework="ISO 27001",
                description="Information Security Policy",
                required_clauses=["security policy", "risk assessment", "controls"],
                keywords=["security measures", "risk management", "controls"],
                risk_level="MEDIUM"
            )
        ]
        for rule in default_rules:
            self.rules[rule.id] = rule

    def analyze_document(self, document_text: str, frameworks: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze document for compliance issues across specified frameworks.
        
        Args:
            document_text: The text content to analyze
            frameworks: Optional list of framework names to check (e.g., ["GDPR", "HIPAA"])
        
        Returns:
            Dict containing analysis results, issues found, and risk assessment
        """
        # Simple validation to prevent app from freezing
        if not document_text or len(document_text) < 10:
            return {
                "timestamp": datetime.now().isoformat(),
                "analyzed_frameworks": frameworks or [],
                "total_issues": 0,
                "issues": [],
                "risk_assessment": {
                    "level": "LOW",
                    "breakdown": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
                    "explanation": "Document too short for meaningful analysis."
                },
                "summary": "Document is too short to perform compliance analysis."
            }
            
        # Maximum document size to analyze (100KB)
        if len(document_text) > 100000:
            document_text = document_text[:100000]
            
        issues = []
        
        # Filter rules by requested frameworks
        active_rules = list(self.rules.values())
        if frameworks:
            active_rules = [r for r in active_rules if r.framework in frameworks]
            
        # Instead of analyzing line by line, we'll analyze paragraph by paragraph
        # This is much more efficient and less likely to freeze
        paragraphs = document_text.split('\n\n')
        
        # Process at most 200 paragraphs to prevent freezing on very large documents
        for para_num, paragraph in enumerate(paragraphs[:200], 1):
            if not paragraph.strip():
                continue
                
            for rule in active_rules:
                if not self._check_paragraph_compliance(paragraph, rule):
                    # Found compliance issue
                    issue = ComplianceIssue(
                        rule_id=rule.id,
                        section=f"Paragraph {para_num}",
                        description=f"Missing compliance with {rule.framework}: {rule.description}",
                        risk_level=rule.risk_level,
                        line_number=para_num,
                        suggested_fix=self._generate_fix_suggestion(rule)
                    )
                    issues.append(issue)
                    
                    # Limit issues per paragraph to prevent overwhelming results
                    if len(issues) >= 50:
                        break
            
            # Early exit if we've found enough issues
            if len(issues) >= 50:
                break

        # Generate analysis report
        return {
            "timestamp": datetime.now().isoformat(),
            "analyzed_frameworks": [r.framework for r in active_rules],
            "total_issues": len(issues),
            "issues": [self._issue_to_dict(i) for i in issues],
            "risk_assessment": self._assess_overall_risk(issues),
            "summary": self._generate_summary(issues)
        }
        
    def _check_paragraph_compliance(self, paragraph: str, rule: ComplianceRule) -> bool:
        """Check if a paragraph complies with a specific rule. More efficient than line-by-line."""
        paragraph_lower = paragraph.lower()
        
        # Check for required clauses - needs at least one required clause
        has_required = any(clause in paragraph_lower for clause in rule.required_clauses)
        
        # Check for keywords - needs at least one keyword
        has_keywords = any(keyword in paragraph_lower for keyword in rule.keywords)
        
        # Check regex pattern if specified
        regex_match = True
        if rule.validation_regex:
            regex_match = bool(re.search(rule.validation_regex, paragraph))
            
        return has_required and has_keywords and regex_match

    def _issue_to_dict(self, issue: ComplianceIssue) -> Dict[str, Any]:
        """Convert ComplianceIssue object to dictionary."""
        return {
            "rule_id": issue.rule_id,
            "section": issue.section,
            "description": issue.description,
            "risk_level": issue.risk_level,
            "line_number": issue.line_number,
            "suggested_fix": issue.suggested_fix
        }

    def _generate_fix_suggestion(self, rule: ComplianceRule) -> str:
        """Generate suggestion for fixing compliance issue."""
        return f"Add explicit clause addressing {rule.description} using keywords: {', '.join(rule.keywords)}"

    def _assess_overall_risk(self, issues: List[ComplianceIssue]) -> Dict[str, Any]:
        """Assess overall risk level based on found issues."""
        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in issues:
            risk_counts[issue.risk_level] = risk_counts.get(issue.risk_level, 0) + 1
            
        overall_risk = "LOW"
        if risk_counts["CRITICAL"] > 0:
            overall_risk = "CRITICAL"
        elif risk_counts["HIGH"] > 0:
            overall_risk = "HIGH"
        elif risk_counts["MEDIUM"] > 0:
            overall_risk = "MEDIUM"
            
        return {
            "level": overall_risk,
            "breakdown": risk_counts,
            "explanation": self._generate_risk_explanation(risk_counts)
        }

    def _generate_risk_explanation(self, risk_counts: Dict[str, int]) -> str:
        """Generate human-readable explanation of risk assessment."""
        total_issues = sum(risk_counts.values())
        if total_issues == 0:
            return "No compliance issues found. Document appears to be compliant."
            
        explanations = []
        for level, count in risk_counts.items():
            if count > 0:
                explanations.append(f"{count} {level.lower()} risk issue{'s' if count > 1 else ''}")
                
        return f"Found {', '.join(explanations)}. Immediate attention recommended for higher risk issues."

    def _generate_summary(self, issues: List[ComplianceIssue]) -> str:
        """Generate executive summary of compliance analysis."""
        if not issues:
            return "Document appears to be compliant with all analyzed frameworks."
            
        framework_issues = {}
        for issue in issues:
            framework = self.rules[issue.rule_id].framework
            framework_issues[framework] = framework_issues.get(framework, 0) + 1
            
        summary_parts = [
            f"Found compliance issues in {len(framework_issues)} framework(s):"
        ]
        
        for framework, count in framework_issues.items():
            summary_parts.append(f"- {framework}: {count} issue(s)")
            
        return "\n".join(summary_parts)
