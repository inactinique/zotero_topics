from gensim import corpora, models
import logging
from typing import Tuple, List, Any

class TopicModel:
    def __init__(self, num_topics: int = 5, language: str = 'en', passes: int = 15):
        """
        Initialize the topic model

        Args:
            num_topics (int): Number of topics to generate
            language (str): Language code for the model (affects logging only)
            passes (int): Number of passes through the corpus during training
        """
        self.num_topics = num_topics
        self.language = language
        self.passes = passes
        logging.info(f"Initializing topic model with {num_topics} topics for language '{language}'")

    def create_model(self, processed_texts: List[List[str]]) -> Tuple[Any, Any, Any]:
        """
        Create and train the topic model

        Args:
            processed_texts: List of preprocessed documents (each document is a list of tokens)

        Returns:
            Tuple containing (lda_model, dictionary, corpus)
        """
        try:
            # Create dictionary
            dictionary = corpora.Dictionary(processed_texts)
            
            # Filter out extreme frequencies
            dictionary.filter_extremes(no_below=2, no_above=0.8)
            logging.info(f"Created dictionary with {len(dictionary)} terms")
            
            # Create corpus
            corpus = [dictionary.doc2bow(text) for text in processed_texts]
            logging.info(f"Created corpus with {len(corpus)} documents")
            
            # Train LDA model
            lda_model = models.LdaModel(
                corpus,
                num_topics=self.num_topics,
                id2word=dictionary,
                passes=self.passes,
                random_state=42
            )
            
            logging.info(f"Successfully trained LDA model with {self.num_topics} topics")
            
            # Log top words for each topic
            for idx, topic in lda_model.print_topics(-1):
                logging.debug(f"Topic {idx}: {topic}")
            
            return lda_model, dictionary, corpus
            
        except Exception as e:
            logging.error(f"Error creating topic model: {str(e)}")
            raise

    def get_document_topics(self, lda_model, corpus):
        """
        Get topic distribution for each document

        Args:
            lda_model: Trained LDA model
            corpus: Document corpus

        Returns:
            List of topic distributions for each document
        """
        try:
            return [lda_model.get_document_topics(doc) for doc in corpus]
        except Exception as e:
            logging.error(f"Error getting document topics: {str(e)}")
            raise

    def get_topic_terms(self, lda_model, num_words: int = 10):
        """
        Get top terms for each topic

        Args:
            lda_model: Trained LDA model
            num_words: Number of top words to return per topic

        Returns:
            List of top terms for each topic
        """
        try:
            return [lda_model.show_topic(topicid, num_words) 
                   for topicid in range(self.num_topics)]
        except Exception as e:
            logging.error(f"Error getting topic terms: {str(e)}")
            raise

    def get_model_info(self) -> dict:
        """
        Get information about the model configuration

        Returns:
            Dictionary containing model information
        """
        return {
            'num_topics': self.num_topics,
            'language': self.language,
            'passes': self.passes
        }