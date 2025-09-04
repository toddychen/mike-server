import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

try:
    from flair.data import Sentence
    from flair.models import SequenceTagger
    from flair.nn import Classifier
    FLAIR_AVAILABLE = True
except ImportError:
    FLAIR_AVAILABLE = False
    logging.warning("Flair not available. Please install with: pip install flair")

@dataclass
class ExtractedEntity:
    """Extracted entity information"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    description: str

@dataclass
class ExtractionResult:
    """Result of information extraction"""
    entities: Dict[str, List[ExtractedEntity]]
    summary: Dict[str, int]
    raw_text: str
    confidence_scores: Dict[str, float]

class InformationExtractor:
    """Extract named entities using Flair NER models"""
    
    def __init__(self, model_name: str = "flair/ner-english"):
        """
        Initialize the information extractor
        
        Args:
            model_name: Flair model name. Options:
                - "flair/ner-english": English NER (fast, accurate)
                - "flair/ner-english-fast": English NER (very fast, slightly less accurate)
                - "flair/ner-english-large": English NER (slow, most accurate)
                - "flair/ner-multi": Multi-language NER
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        
        if not FLAIR_AVAILABLE:
            raise ImportError("Flair is not installed. Please install with: pip install flair")
        
        try:
            # Load Flair NER model
            self.tagger = SequenceTagger.load(model_name)
            self.logger.info(f"Successfully loaded Flair model: {model_name}")
            
            # Define entity categories mapping
            self.entity_categories = {
                'PERSON': 'Person',
                'ORG': 'Organization', 
                'LOC': 'Location',
                'MISC': 'Miscellaneous',
                'PER': 'Person',
                'LOC': 'Location',
                'ORG': 'Organization',
                'GPE': 'Geopolitical Entity',
                'FAC': 'Facility',
                'PRODUCT': 'Product',
                'EVENT': 'Event',
                'WORK_OF_ART': 'Work of Art',
                'LAW': 'Law',
                'LANGUAGE': 'Language',
                'DATE': 'Date',
                'TIME': 'Time',
                'MONEY': 'Money',
                'QUANTITY': 'Quantity',
                'ORDINAL': 'Ordinal',
                'CARDINAL': 'Cardinal Number',
                'NORP': 'Nationality, Religious or Political Group',
                'PERCENT': 'Percentage'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load Flair model {model_name}: {e}")
            raise
    
    def extract_entities(self, text: str) -> ExtractionResult:
        """
        Extract named entities from text using Flair
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            ExtractionResult containing extracted entities and summary
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided for entity extraction")
            return ExtractionResult(
                entities={},
                summary={},
                raw_text=text,
                confidence_scores={}
            )
        
        try:
            self.logger.info(f"Starting entity extraction for text of length: {len(text)}")
            
            # Create Flair Sentence object
            sentence = Sentence(text)
            
            # Run NER tagging
            self.tagger.predict(sentence)
            
            # Extract entities
            entities = defaultdict(list)
            confidence_scores = {}
            
            for entity in sentence.get_spans('ner'):
                # Map Flair labels to our categories
                label = self._map_flair_label(entity.tag)
                
                if label:
                    entity_obj = ExtractedEntity(
                        text=entity.text,
                        label=label,
                        start=entity.start_position,
                        end=entity.end_position,
                        confidence=entity.score,
                        description=self.entity_categories.get(label, label)
                    )
                    entities[label].append(entity_obj)
                    
                    # Track confidence scores
                    if label not in confidence_scores:
                        confidence_scores[label] = []
                    confidence_scores[label].append(entity.score)
            
            # Create summary
            summary = {label: len(entities[label]) for label in entities}
            
            # Calculate average confidence per category
            avg_confidence = {}
            for label, scores in confidence_scores.items():
                avg_confidence[label] = sum(scores) / len(scores)
            
            result = ExtractionResult(
                entities=dict(entities),
                summary=summary,
                raw_text=text,
                confidence_scores=avg_confidence
            )
            
            self.logger.info(f"Entity extraction completed. Found {sum(summary.values())} entities across {len(summary)} categories")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during entity extraction: {e}")
            raise
    
    def _map_flair_label(self, flair_label: str) -> str:
        """Map Flair NER labels to our standard categories"""
        # Flair uses different label conventions
        label_mapping = {
            'PER': 'PERSON',
            'LOC': 'LOC',
            'ORG': 'ORG',
            'MISC': 'MISC',
            'PERSON': 'PERSON',
            'GPE': 'GPE',
            'FAC': 'FAC',
            'PRODUCT': 'PRODUCT',
            'EVENT': 'EVENT',
            'WORK_OF_ART': 'WORK_OF_ART',
            'LAW': 'LAW',
            'LANGUAGE': 'LANGUAGE',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'MONEY': 'MONEY',
            'QUANTITY': 'QUANTITY',
            'ORDINAL': 'ORDINAL',
            'CARDINAL': 'CARDINAL',
            'NORP': 'NORP',
            'PERCENT': 'PERCENT'
        }
        
        return label_mapping.get(flair_label, flair_label)
    
    def extract_people(self, text: str) -> List[ExtractedEntity]:
        """Extract only person names from text"""
        result = self.extract_entities(text)
        return result.entities.get('PERSON', [])
    
    def extract_places(self, text: str) -> List[ExtractedEntity]:
        """Extract only place names from text"""
        result = self.extract_entities(text)
        places = []
        for category in ['LOC', 'GPE', 'FAC']:
            places.extend(result.entities.get(category, []))
        return places
    
    def extract_organizations(self, text: str) -> List[ExtractedEntity]:
        """Extract only organization names from text"""
        result = self.extract_entities(text)
        return result.entities.get('ORG', [])
    
    def extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extract only date entities from text"""
        result = self.extract_entities(text)
        return result.entities.get('DATE', [])
    
    def extract_numbers(self, text: str) -> List[ExtractedEntity]:
        """Extract only number entities from text"""
        result = self.extract_entities(text)
        numbers = []
        for category in ['CARDINAL', 'ORDINAL', 'QUANTITY', 'MONEY', 'PERCENT']:
            numbers.extend(result.entities.get(category, []))
        return numbers
    
    def get_entity_statistics(self, text: str) -> Dict[str, any]:
        """Get detailed statistics about entities in text"""
        result = self.extract_entities(text)
        
        stats = {
            'total_entities': sum(result.summary.values()),
            'categories_found': len(result.summary),
            'category_breakdown': result.summary,
            'text_length': len(text),
            'entity_density': sum(result.summary.values()) / len(text) if text else 0,
            'average_confidence': sum(result.confidence_scores.values()) / len(result.confidence_scores) if result.confidence_scores else 0,
            'confidence_by_category': result.confidence_scores
        }
        
        return stats
    
    def change_model(self, new_model_name: str) -> bool:
        """Change the Flair model"""
        try:
            self.tagger = SequenceTagger.load(new_model_name)
            self.model_name = new_model_name
            self.logger.info(f"Successfully changed Flair model to: {new_model_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to change model to {new_model_name}: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Flair NER models"""
        return [
            "ner-english",
            "ner-english-fast", 
            "ner-english-large",
            "ner-multi",
            "ner-ontonotes",
            "ner-ontonotes-fast"
        ]
    
    def get_model_info(self) -> Dict[str, any]:
        """Get information about current model"""
        try:
            return {
                'model_name': self.model_name,
                'model_type': 'Flair SequenceTagger',
                'entity_categories': self.entity_categories,
                'available_models': self.get_available_models()
            }
        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return {'error': str(e)}
    
    def batch_extract(self, texts: List[str]) -> List[ExtractionResult]:
        """Extract entities from multiple texts efficiently"""
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.extract_entities(text)
                results.append(result)
                self.logger.info(f"Processed text {i+1}/{len(texts)}")
            except Exception as e:
                self.logger.error(f"Failed to process text {i+1}: {e}")
                # Return empty result for failed texts
                results.append(ExtractionResult(
                    entities={},
                    summary={},
                    raw_text=text,
                    confidence_scores={}
                ))
        
        return results
    
    def convert_entities_to_list(self, entities_dict: Dict[str, List[ExtractedEntity]]) -> List[Dict]:
        """
        Convert entities from dict format to list format for similarity calculation
        
        Args:
            entities_dict: Dictionary with entity types as keys and lists of ExtractedEntity objects as values
            
        Returns:
            List of entity dictionaries with 'text' and 'confidence' fields (deduplicated by text)
        """
        entities_list = []
        seen_texts = set()  # Track seen entity texts for deduplication
        
        for entities in entities_dict.values():
            for entity in entities:
                # Only add entity if we haven't seen this text before
                if entity.text not in seen_texts:
                    entities_list.append({
                        'text': entity.text,
                        'confidence': round(entity.confidence, 3)
                    })
                    seen_texts.add(entity.text)
        
        return entities_list
    
    def convert_db_entities_to_list(self, entities_dict: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Convert database entities from dict format to list format for similarity calculation
        
        Args:
            entities_dict: Dictionary with entity types as keys and lists of dict entities as values
                          Each dict entity has 'text' and 'confidence' fields
            
        Returns:
            List of entity dictionaries with 'text' and 'confidence' fields (deduplicated by text)
        """
        entities_list = []
        seen_texts = set()  # Track seen entity texts for deduplication
        
        for entities in entities_dict.values():
            for entity in entities:
                # Only add entity if we haven't seen this text before
                if entity['text'] not in seen_texts:
                    entities_list.append(entity)
                    seen_texts.add(entity['text'])
        
        return entities_list