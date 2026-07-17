from transformers import pipeline

class FinBertAnalyzer:
    def __init__(self):
        # Loads the model into memory. 
        self.analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")

    def calculate_sentiment(self, text_list):
        """
        Takes a list of strings and returns a composite sentiment score between -1.0 and 1.0.
        """
        if not text_list or not text_list[0]:
            return 0.0

        results = self.analyzer(text_list)
        cumulative_score = 0.0
        
        for result in results:
            label = result['label']
            confidence = result['score'] 
            
            if label == 'positive':
                cumulative_score += confidence
            elif label == 'negative':
                cumulative_score -= confidence
            # Neutral labels contribute 0.0

        return cumulative_score / len(text_list)