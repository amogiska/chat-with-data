from typing import List, Dict, Any
import time
from openai import OpenAI
from config import Config


class EmbeddingGenerator:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.model = model or Config.EMBEDDING_MODEL
        self.batch_size = Config.EMBEDDING_BATCH_SIZE
        self.client = OpenAI(api_key=self.api_key)
        
        self.total_tokens = 0
        self.total_requests = 0
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._generate_batch(batch)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def _generate_batch(self, texts: List[str], retry_count: int = 3) -> List[List[float]]:
        for attempt in range(retry_count):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                
                self.total_tokens += response.usage.total_tokens
                self.total_requests += 1
                
                embeddings = [item.embedding for item in response.data]
                return embeddings
                
            except Exception as e:
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    print(f"Error generating embeddings (attempt {attempt + 1}/{retry_count}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to generate embeddings after {retry_count} attempts: {e}")
    
    def generate_embeddings_with_metadata(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        texts = [item['text'] for item in items]
        embeddings = self.generate_embeddings(texts)
        
        for item, embedding in zip(items, embeddings):
            item['embedding'] = embedding
        
        return items
    
    def get_embedding_dimension(self) -> int:
        dimensions = {
            'text-embedding-3-small': 1536,
            'text-embedding-3-large': 3072,
            'text-embedding-ada-002': 1536,
        }
        return dimensions.get(self.model, 1536)
    
    def estimate_cost(self, num_texts: int, avg_tokens_per_text: int = 100) -> float:
        total_tokens = num_texts * avg_tokens_per_text
        cost_per_1k = Config.get_embedding_cost_per_1k()
        return (total_tokens / 1000) * cost_per_1k
    
    def get_stats(self) -> Dict[str, Any]:
        cost_per_1k = Config.get_embedding_cost_per_1k()
        total_cost = (self.total_tokens / 1000) * cost_per_1k
        
        return {
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'total_cost_usd': total_cost,
            'model': self.model,
            'embedding_dimension': self.get_embedding_dimension()
        }
