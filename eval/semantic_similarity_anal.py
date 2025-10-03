import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util

class Semantic_Similarity_Anal:
    def __init__(self, query, nl_rag, nl_deepseek, dict_rag, dict_deepseek, openai=None):
        """
        tdif_score: Measures lexical similarity (based on word overlap)
        bert_score: Measures semantic similarity (based on meaning)
        """
        # Load a BERT model for embedding similarity (optional but improves accuracy)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.nl_rag = nl_rag
        self.nl_deepseek = nl_deepseek
        self.dict_rag = dict_rag
        self.dict_deepseek = dict_deepseek
        self.openai = openai
        self.query = query
        self.metrics = {}
        self.metrics["rag_vs_deepseek_similarity"] = self.compute_text_similarity(self.nl_rag, self.nl_deepseek)


    ### 1. RELEVANCE SCORING (TF-IDF + BERT) ###
    def compute_text_similarity(self, response1, response2):
        # TF-IDF Similarity
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([response1, response2])
        tfidf_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

        # BERT Embedding Similarity
        emb_rag = self.model.encode(response1, convert_to_tensor=True)
        emb_deepseek = self.model.encode(response2, convert_to_tensor=True)
        bert_score = np.dot(emb_rag, emb_deepseek) / (np.linalg.norm(emb_rag) * np.linalg.norm(emb_deepseek))

        return {"tfidf_score": tfidf_score, "bert_score": float(bert_score)}

    def calculate_thematic_relevancy(self):
        rag_score = self._thematic_relevancy(self.dict_rag)
        deepseek_score = self._thematic_relevancy(self.dict_deepseek)
        return {"rag" : rag_score, "deepseek" : deepseek_score}

    def _thematic_relevancy(self, dict):
        total = 0
        for day in dict.values():
            retrieved_pois = day

            # Compute embeddings
            query_embedding = self.model.encode(self.query, convert_to_tensor=True)
            poi_embeddings = self.model.encode(retrieved_pois, convert_to_tensor=True)

            # Compute similarity scores
            similarities = [util.pytorch_cos_sim(query_embedding, poi_emb).item() for poi_emb in poi_embeddings]

            # Average similarity score
            total += sum(similarities) / len(similarities)