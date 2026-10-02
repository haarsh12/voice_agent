"""Query expansion for better scheme matching and recall."""

from __future__ import annotations

import logging
import re
from typing import Set

logger = logging.getLogger("sahayak.knowledge.query_expansion")

# Comprehensive scheme synonyms and variations across languages
SCHEME_SYNONYMS = {
    # Crop Insurance
    "fasal bima": ["crop insurance", "pmfby", "प्रधानमंत्री फसल बीमा", "फसल बीमा योजना", "पीएमएफबीवाई"],
    "crop insurance": ["pmfby", "fasal bima", "pradhan mantri fasal bima yojana"],
    "pmfby": ["crop insurance", "fasal bima", "फसल बीमा"],
    
    # PM-KISAN
    "kisan samman": ["pm kisan", "किसान सम्मान", "pm-kisan", "income support", "किसान सम्मान निधि"],
    "pm kisan": ["kisan samman", "किसान सम्मान", "income support for farmers"],
    "किसान सम्मान": ["pm kisan", "kisan samman", "pm-kisan"],
    
    # MSP
    "msp": ["minimum support price", "न्यूनतम समर्थन मूल्य", "procurement price", "support price"],
    "minimum support price": ["msp", "न्यूनतम समर्थन मूल्य", "support price"],
    "न्यूनतम समर्थन मूल्य": ["msp", "minimum support price"],
    
    # PM Kisan Maandhan
    "kisan maandhan": ["pm kisan maandhan", "pension scheme", "किसान मानधन"],
    "किसान मानधन": ["kisan maandhan", "pm kisan maandhan", "pension"],
    
    # Soil Health Card
    "soil health": ["soil health card", "मृदा स्वास्थ्य कार्ड", "shc"],
    "soil health card": ["shc", "soil testing", "मृदा स्वास्थ्य"],
    
    # Kisan Credit Card
    "kcc": ["kisan credit card", "किसान क्रेडिट कार्ड", "crop loan"],
    "kisan credit card": ["kcc", "किसान क्रेडिट", "farm loan"],
    "किसान क्रेडिट": ["kcc", "kisan credit card"],
    
    # Agriculture Infrastructure Fund
    "aif": ["agriculture infrastructure fund", "कृषि अवसंरचना कोष"],
    "agriculture infrastructure": ["aif", "farm infrastructure", "कृषि अवसंरचना"],
    
    # PM Kusum
    "kusum": ["pm kusum", "solar pump", "सौर पंप योजना"],
    "solar pump": ["kusum", "pm kusum", "solar energy"],
    
    # e-NAM
    "enam": ["e-nam", "national agriculture market", "राष्ट्रीय कृषि बाजार"],
    "e-nam": ["enam", "national agriculture market", "online mandi"],
    
    # Paramparagat Krishi Vikas Yojana
    "pkvy": ["paramparagat krishi vikas yojana", "organic farming", "जैविक खेती"],
    "organic farming": ["pkvy", "paramparagat krishi", "जैविक खेती"],
    
    # General terms
    "loan": ["kisan credit", "कर्ज", "ऋण", "कर्जा"],
    "subsidy": ["सब्सिडी", "अनुदान", "grant"],
    "pension": ["मानधन", "पेंशन", "retirement"],
    "insurance": ["बीमा", "विमा", "coverage"],
}

# Common stopwords that don't help in scheme matching
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in",
    "is", "it", "its", "of", "on", "that", "the", "to", "was", "will", "with",
    "मैं", "है", "के", "में", "को", "का", "की", "से", "पर", "यह", "वह",
    "एक", "और", "या", "तथा", "कि", "जो", "हैं",
}


def expand_query(query: str, max_expansions: int = 5) -> list[str]:
    """Expand query with synonyms and variations for better recall.
    
    Args:
        query: Original user query
        max_expansions: Maximum number of expansion terms to add
        
    Returns:
        List of queries including original plus expanded versions
    """
    queries = [query]
    query_lower = query.lower().strip()
    
    added_count = 0
    
    # Find matching synonyms
    for key, synonyms in SCHEME_SYNONYMS.items():
        if added_count >= max_expansions:
            break
            
        if key in query_lower:
            for synonym in synonyms:
                if synonym.lower() not in query_lower and added_count < max_expansions:
                    # Create new query by appending synonym
                    expanded = f"{query} {synonym}"
                    queries.append(expanded)
                    added_count += 1
                    
                    if added_count >= max_expansions:
                        break
    
    if len(queries) > 1:
        logger.debug(
            "query_expanded original=%s expansions=%d",
            query[:50],
            len(queries) - 1,
        )
    
    return queries


def extract_scheme_keywords(query: str) -> Set[str]:
    """Extract meaningful keywords from query, excluding stopwords.
    
    Args:
        query: User query text
        
    Returns:
        Set of normalized keywords
    """
    # Normalize and tokenize
    words = re.findall(r"[\w\u0900-\u097F]+", query.lower(), flags=re.UNICODE)
    
    # Filter stopwords and short words
    keywords = {
        word
        for word in words
        if len(word) > 2 and word not in STOPWORDS
    }
    
    return keywords


def get_scheme_variations(scheme_name: str) -> list[str]:
    """Get all known variations of a scheme name.
    
    Args:
        scheme_name: Official or common scheme name
        
    Returns:
        List of name variations
    """
    variations = [scheme_name]
    scheme_lower = scheme_name.lower()
    
    for key, synonyms in SCHEME_SYNONYMS.items():
        if key in scheme_lower or scheme_lower in [s.lower() for s in synonyms]:
            variations.extend([key] + synonyms)
            break
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for var in variations:
        var_lower = var.lower()
        if var_lower not in seen:
            seen.add(var_lower)
            unique_variations.append(var)
    
    return unique_variations


def enhance_search_terms(terms: list[str]) -> list[str]:
    """Enhance search terms with common abbreviations and variations.
    
    Args:
        terms: Original search terms
        
    Returns:
        Enhanced list with variations
    """
    enhanced = list(terms)
    
    for term in terms:
        term_lower = term.lower()
        
        # Add acronyms
        if " " in term:
            # Generate acronym from multi-word term
            words = term_lower.split()
            acronym = "".join(w[0] for w in words if w and w[0].isalpha())
            if len(acronym) >= 2 and acronym not in enhanced:
                enhanced.append(acronym)
        
        # Add variations from synonym map
        for key, synonyms in SCHEME_SYNONYMS.items():
            if key == term_lower:
                for syn in synonyms[:2]:  # Limit to top 2 synonyms
                    if syn not in enhanced:
                        enhanced.append(syn)
                break
    
    return enhanced
