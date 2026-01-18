"""Custom financial-specific metrics."""
import re
from typing import List, Dict, Tuple, Optional


class FinancialMetrics:
    """
    Custom evaluation metrics for financial document Q&A.
    """
    
    def __init__(self):
        # Load spaCy for NER (optional)
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            print("Warning: spaCy model not found. Entity accuracy will be disabled.")
            print("Install with: python -m spacy download en_core_web_sm")
    
    def numerical_accuracy(
        self,
        generated_answer: str,
        ground_truth: str,
        tolerance: float = 0.01
    ) -> Dict:
        """
        Check if numbers in generated answer match ground truth.
        
        Args:
            generated_answer: Generated answer text
            ground_truth: Ground truth answer text
            tolerance: Tolerance for numerical comparison (default 1%)
        
        Returns:
            {
                'score': 0.0-1.0,
                'total_numbers': int,
                'correct_numbers': int,
                'incorrect_numbers': List[Tuple[str, str]]  # (generated, expected)
            }
        """
        # Extract numbers from both texts
        gen_numbers = self._extract_numbers(generated_answer)
        truth_numbers = self._extract_numbers(ground_truth)
        
        if not truth_numbers:
            return {'score': 1.0, 'total_numbers': 0, 'correct_numbers': 0, 'incorrect_numbers': []}
        
        # Match numbers (order-based for now)
        correct = 0
        incorrect = []
        
        for i, truth_num in enumerate(truth_numbers):
            if i < len(gen_numbers):
                gen_num = gen_numbers[i]
                
                # Check if within tolerance
                if abs(gen_num - truth_num) / max(abs(truth_num), 1) <= tolerance:
                    correct += 1
                else:
                    incorrect.append((str(gen_num), str(truth_num)))
            else:
                incorrect.append(("missing", str(truth_num)))
        
        score = correct / len(truth_numbers) if truth_numbers else 0.0
        
        return {
            'score': score,
            'total_numbers': len(truth_numbers),
            'correct_numbers': correct,
            'incorrect_numbers': incorrect
        }
    
    def citation_quality(self, generated_answer: str) -> Dict:
        """
        Evaluate citation quality in answer.
        
        Returns:
            {
                'has_citations': bool,
                'citation_count': int,
                'citation_rate': float,  # citations per sentence
                'score': 0.0-1.0
            }
        """
        # Count citations (format: [doc_X], [doc_X:chunk_Y], etc.)
        citation_pattern = r'\[(?:doc_\d+|source_\d+)[:\w-]*\]'
        citations = re.findall(citation_pattern, generated_answer)
        
        # Count sentences
        sentences = re.split(r'[.!?]+', generated_answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        has_citations = len(citations) > 0
        citation_count = len(citations)
        citation_rate = citation_count / len(sentences) if sentences else 0
        
        # Score based on citation rate
        # Ideal: 0.5-1 citations per sentence for factual content
        if citation_rate >= 0.5:
            score = 1.0
        elif citation_rate >= 0.3:
            score = 0.8
        elif citation_rate >= 0.1:
            score = 0.6
        elif has_citations:
            score = 0.4
        else:
            score = 0.0
        
        return {
            'has_citations': has_citations,
            'citation_count': citation_count,
            'citation_rate': citation_rate,
            'score': score
        }
    
    def temporal_accuracy(
        self,
        generated_answer: str,
        ground_truth: str
    ) -> Dict:
        """
        Check if dates and time periods are correct.
        
        Returns:
            {
                'score': 0.0-1.0,
                'dates_matched': int,
                'dates_total': int,
                'mismatches': List[str]
            }
        """
        # Extract dates from both
        gen_dates = self._extract_dates(generated_answer)
        truth_dates = self._extract_dates(ground_truth)
        
        if not truth_dates:
            return {'score': 1.0, 'dates_matched': 0, 'dates_total': 0, 'mismatches': []}
        
        # Check if all truth dates appear in generated answer
        matched = 0
        mismatches = []
        
        for truth_date in truth_dates:
            if truth_date in gen_dates:
                matched += 1
            else:
                mismatches.append(truth_date)
        
        score = matched / len(truth_dates) if truth_dates else 1.0
        
        return {
            'score': score,
            'dates_matched': matched,
            'dates_total': len(truth_dates),
            'mismatches': mismatches
        }
    
    def entity_accuracy(
        self,
        generated_answer: str,
        ground_truth: str
    ) -> Dict:
        """
        Check if entities (companies, people, locations) are correct.
        
        Uses spaCy NER to extract entities.
        
        Returns:
            {
                'score': 0.0-1.0,
                'entities_matched': int,
                'entities_total': int,
                'missing_entities': List[str],
                'incorrect_entities': List[str]
            }
        """
        if not self.nlp:
            return {
                'score': 1.0, 
                'entities_matched': 0, 
                'entities_total': 0,
                'missing_entities': [],
                'incorrect_entities': [],
                'error': 'spaCy not available'
            }
        
        # Extract entities
        gen_entities = self._extract_entities(generated_answer)
        truth_entities = self._extract_entities(ground_truth)
        
        if not truth_entities:
            return {
                'score': 1.0,
                'entities_matched': 0,
                'entities_total': 0,
                'missing_entities': [],
                'incorrect_entities': []
            }
        
        # Check matches
        matched = 0
        missing = []
        incorrect = []
        
        for truth_entity in truth_entities:
            if truth_entity in gen_entities:
                matched += 1
            else:
                missing.append(truth_entity)
        
        # Check for hallucinated entities
        for gen_entity in gen_entities:
            if gen_entity not in truth_entities:
                incorrect.append(gen_entity)
        
        score = matched / len(truth_entities) if truth_entities else 1.0
        
        return {
            'score': score,
            'entities_matched': matched,
            'entities_total': len(truth_entities),
            'missing_entities': missing,
            'incorrect_entities': incorrect
        }
    
    def comprehensive_score(
        self,
        generated_answer: str,
        ground_truth: str
    ) -> Dict:
        """
        Calculate comprehensive custom metrics score.
        
        Combines all custom metrics with weights.
        """
        numerical = self.numerical_accuracy(generated_answer, ground_truth)
        citation = self.citation_quality(generated_answer)
        temporal = self.temporal_accuracy(generated_answer, ground_truth)
        entity = self.entity_accuracy(generated_answer, ground_truth)
        
        # Weighted average
        weights = {
            'numerical': 0.35,
            'citation': 0.25,
            'temporal': 0.20,
            'entity': 0.20
        }
        
        overall_score = (
            weights['numerical'] * numerical['score'] +
            weights['citation'] * citation['score'] +
            weights['temporal'] * temporal['score'] +
            weights['entity'] * entity['score']
        )
        
        return {
            'overall_score': overall_score,
            'numerical_accuracy': numerical,
            'citation_quality': citation,
            'temporal_accuracy': temporal,
            'entity_accuracy': entity
        }
    
    # Helper methods
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract all numbers from text."""
        # Pattern for numbers with commas, decimals, percentages
        pattern = r'-?\d+(?:,\d{3})*(?:\.\d+)?%?'
        matches = re.findall(pattern, text)
        
        numbers = []
        for match in matches:
            # Clean and convert
            clean = match.replace(',', '').replace('%', '')
            try:
                numbers.append(float(clean))
            except Exception:
                pass
        
        return numbers
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        # Common date patterns
        patterns = [
            r'\b\d{4}\b',  # Year (2023)
            r'\b(?:Q[1-4])\s+\d{4}\b',  # Quarter (Q3 2023)
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month Day, Year
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
        ]
        
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(dates))  # Remove duplicates
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities using spaCy."""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PERSON', 'GPE', 'MONEY', 'PERCENT']:
                entities.append(ent.text)
        
        return list(set(entities))


# Backward compatibility alias
CustomMetrics = FinancialMetrics
