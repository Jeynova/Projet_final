"""
Memory Agent with RAG capabilities for learning from successful patterns
"""

import hashlib
import sqlite3
from datetime import datetime
import numpy as np
from typing import Optional, Dict, Any, List
import requests
import time
import json
import pickle


class MemoryAgent:
    """
    Memory Agent with Simple Vector RAG - Stores successful project patterns using embeddings
    Uses Ollama embeddings with optimized SQLite vector storage
    """
    
    def __init__(self, db_path: str = "memory_rag.db", min_score: float = 7.0):
        self.db_path = db_path
        self.min_score = min_score
        self.embedding_model = "nomic-embed-text"
        self.ollama_base = "http://localhost:11434"
        self.vector_cache = {}  # In-memory cache for faster similarity search
        self.init_database()
        self._load_vector_cache()
        print(f"🧠 MemoryAgent: Optimized SQLite RAG with vector cache")
        print(f"🎯 Learning from projects with score >= {min_score}")

    def init_database(self):
        """Initialize SQLite database with tables for RAG storage"""
        with sqlite3.connect(self.db_path) as conn:
            # Main project memory table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_hash TEXT UNIQUE,
                    prompt_text TEXT,
                    tech_stack TEXT,
                    file_patterns TEXT,
                    score FLOAT,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Vector embeddings table for semantic similarity
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_hash TEXT,
                    embedding BLOB,
                    created_at TEXT,
                    FOREIGN KEY (prompt_hash) REFERENCES project_memory (prompt_hash)
                )
            """)
            
            conn.commit()

    def _load_vector_cache(self):
        """Load embeddings into memory cache for faster similarity search"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT pm.prompt_hash, pm.prompt_text, e.embedding
                    FROM project_memory pm
                    JOIN embeddings e ON pm.prompt_hash = e.prompt_hash
                    WHERE pm.score >= ?
                """, (self.min_score,))
                
                for prompt_hash, prompt_text, embedding_blob in cursor.fetchall():
                    try:
                        embedding = pickle.loads(embedding_blob)
                        self.vector_cache[prompt_hash] = {
                            'prompt': prompt_text,
                            'embedding': np.array(embedding)
                        }
                    except Exception as e:
                        print(f"⚠️ Failed to load embedding for {prompt_hash}: {e}")
                        
            print(f"🧠 Loaded {len(self.vector_cache)} embeddings into cache")
            
        except Exception as e:
            print(f"⚠️ Failed to load vector cache: {e}")

    def get_embedding(self, text: str, max_retries: int = 3) -> Optional[np.ndarray]:
        """Get embedding for text using Ollama"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.ollama_base}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return np.array(data.get("embedding", []))
                else:
                    print(f"⚠️ Embedding API error {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"⚠️ Embedding attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
        print(f"❌ Failed to get embedding after {max_retries} attempts")
        return None

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            if len(a) == 0 or len(b) == 0:
                return 0.0
            
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
                
            return dot_product / (norm_a * norm_b)
            
        except Exception as e:
            print(f"⚠️ Cosine similarity calculation failed: {e}")
            return 0.0

    def find_similar_projects(self, prompt: str, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """Find similar projects using vector similarity search"""
        
        if not self.vector_cache:
            print("🧠 MemoryAgent: No cached embeddings available")
            return self._fallback_exact_match(prompt)
        
        # Get embedding for current prompt
        prompt_embedding = self.get_embedding(prompt)
        if prompt_embedding is None:
            print("🧠 MemoryAgent: Failed to get prompt embedding, using fallback")
            return self._fallback_exact_match(prompt)
        
        # Calculate similarities with cached embeddings
        best_similarity = 0.0
        best_match = None
        best_hash = None
        
        for prompt_hash, cached_data in self.vector_cache.items():
            cached_embedding = cached_data['embedding']
            
            similarity = self.cosine_similarity(prompt_embedding, cached_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cached_data
                best_hash = prompt_hash
        
        if best_match and best_similarity >= similarity_threshold:
            # Get full project data from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT prompt_text, tech_stack, file_patterns, score
                    FROM project_memory 
                    WHERE prompt_hash = ?
                """, (best_hash,))
                
                result = cursor.fetchone()
                if result:
                    prompt_text, tech_stack, file_patterns, score = result
                    
                    # Update usage count
                    conn.execute("""
                        UPDATE project_memory 
                        SET usage_count = usage_count + 1 
                        WHERE prompt_hash = ?
                    """, (best_hash,))
                    
                    print(f"🧠 MemoryAgent: Found similar! Similarity: {best_similarity:.3f}")
                    print(f"   📝 Original: {prompt_text[:50]}...")
                    
                    return {
                        'found': True,
                        'tech_stack': json.loads(tech_stack),
                        'file_patterns': json.loads(file_patterns),
                        'confidence': best_similarity,
                        'source': 'vector_similarity',
                        'original_score': score
                    }
        
        print(f"🧠 MemoryAgent: No similar projects found (threshold: {similarity_threshold})")
        return {'found': False}
    
    def _fallback_exact_match(self, prompt: str) -> Dict[str, Any]:
        """Fallback to exact text matching"""
        prompt_hash = hashlib.md5(prompt.lower().strip().encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT tech_stack, file_patterns, score
                FROM project_memory 
                WHERE prompt_hash = ?
            """, (prompt_hash,))
            
            result = cursor.fetchone()
            if result:
                tech_stack, file_patterns, score = result
                print(f"🧠 MemoryAgent: Found exact match (score: {score})")
                return {
                    'found': True,
                    'tech_stack': json.loads(tech_stack),
                    'file_patterns': json.loads(file_patterns),
                    'confidence': 0.95,  # High confidence for exact match
                    'source': 'exact_match',
                    'original_score': score
                }
        
        return {'found': False}

    def store_project_pattern(self, prompt: str, tech_stack: Dict[str, Any], 
                             file_patterns: List[str], score: float) -> bool:
        """Store successful project pattern with embedding"""
        
        if score < self.min_score:
            print(f"🧠 MemoryAgent: Score {score} below threshold {self.min_score}, not storing")
            return False
        
        try:
            prompt_hash = hashlib.md5(prompt.lower().strip().encode()).hexdigest()
            timestamp = datetime.now().isoformat()
            
            # Get embedding for the prompt
            embedding = self.get_embedding(prompt)
            if embedding is None:
                print("🧠 MemoryAgent: Failed to get embedding, storing without vector search capability")
            
            with sqlite3.connect(self.db_path) as conn:
                # Store main pattern
                conn.execute("""
                    INSERT OR REPLACE INTO project_memory 
                    (prompt_hash, prompt_text, tech_stack, file_patterns, score, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (prompt_hash, prompt, json.dumps(tech_stack), 
                     json.dumps(file_patterns), score, timestamp, timestamp))
                
                # Store embedding if available
                if embedding is not None:
                    embedding_blob = pickle.dumps(embedding.tolist())
                    conn.execute("""
                        INSERT OR REPLACE INTO embeddings 
                        (prompt_hash, embedding, created_at)
                        VALUES (?, ?, ?)
                    """, (prompt_hash, embedding_blob, timestamp))
                    
                    # Update cache
                    self.vector_cache[prompt_hash] = {
                        'prompt': prompt,
                        'embedding': embedding
                    }
                
                conn.commit()
                
            print(f"🧠 MemoryAgent: Stored with embedding (score: {score})")
            return True
            
        except Exception as e:
            print(f"❌ MemoryAgent: Failed to store pattern: {e}")
            return False

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memory"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*), AVG(score), SUM(usage_count) FROM project_memory")
            count, avg_score, total_usage = cursor.fetchone()
            
            cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
            embeddings_count = cursor.fetchone()[0]
            
            return {
                'total_patterns': count or 0,
                'with_embeddings': embeddings_count or 0,
                'cached_vectors': len(self.vector_cache),
                'avg_score': round(avg_score or 0, 2),
                'total_reuses': total_usage or 0
            }
