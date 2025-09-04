from typing import List, Dict, Any
import logging

class EntitySimilarityService:
    """Service for calculating similarity between play entities and news entities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def weighted_containment_similarity(self, play_entities: List[Dict], news_entities: List[Dict], min_score: float = 0.7) -> Dict[str, Any]:
        """
        Calculate weighted containment similarity between play entities and news entities
        
        Args:
            play_entities: List of entities from play text, each containing 'text' and 'confidence'
            news_entities: List of entities from news text, each containing 'text' and 'confidence'
            min_score: Minimum confidence threshold, only consider entities with confidence >= min_score
            
        Returns:
            Dictionary containing:
                - score: Weighted similarity score (0.0 to 1.0)
                - play_entity_count: Number of filtered play entities
                - news_entity_count: Number of filtered news entities
                - matched_count: Number of matched entities
                - matched_entities: List of matched entity texts
                - play_entities: List of filtered play entities
                - news_entities: List of filtered news entities
        """
        try:
            # Filter entities by minimum confidence score
            filtered_play_entities = [entity for entity in play_entities if entity['confidence'] >= min_score]
            filtered_news_entities = [entity for entity in news_entities if entity['confidence'] >= min_score]
            
            # Handle edge cases
            if not filtered_play_entities:
                self.logger.warning(f"Play entities is empty after filtering (min_score={min_score})")
                return {
                    'score': 0.0,
                    'play_entity_count': 0,
                    'news_entity_count': len(filtered_news_entities),
                    'matched_count': 0,
                    'matched_entities': [],
                    'play_entities': filtered_play_entities,
                    'news_entities': filtered_news_entities
                }
            
            if not filtered_news_entities:
                self.logger.warning(f"News entities is empty after filtering (min_score={min_score})")
                return {
                    'score': 0.0,
                    'play_entity_count': len(filtered_play_entities),
                    'news_entity_count': 0,
                    'matched_count': 0,
                    'matched_entities': [],
                    'play_entities': filtered_play_entities,
                    'news_entities': filtered_news_entities
                }
            
            # Create entity text to confidence mappings
            news_entity_conf = {entity['text']: entity['confidence'] for entity in filtered_news_entities}
            
            total_weight = 0
            matched_weight = 0
            matched_count = 0
            matched_entities = []  # Track matched entity texts
            
            for play_entity in filtered_play_entities:
                text = play_entity['text']
                play_conf = play_entity['confidence']
                news_conf = news_entity_conf.get(text, 0)  # Default to 0 if not found
                
                total_weight += play_conf
                matched_weight += min(play_conf, news_conf)

                if text in news_entity_conf:
                    matched_count += 1
                    matched_entities.append(text)  # Add matched entity text
            
            score = round(matched_weight / total_weight, 3) if total_weight > 0 else 0.0
            
            return {
                'score': score,
                'play_entity_count': len(filtered_play_entities),
                'news_entity_count': len(filtered_news_entities),
                'matched_count': matched_count,
                'matched_entities': matched_entities,  # Add matched entity texts
                'play_entities': filtered_play_entities,
                'news_entities': filtered_news_entities
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating weighted containment similarity: {e}")
            return {
                'score': 0.0,
                'play_entity_count': 0,
                'news_entity_count': 0,
                'matched_count': 0,
                'matched_entities': [],
                'play_entities': [],
                'news_entities': []
            }
    

