import numpy as np
from matplotlib.figure import Figure

class TopicVisualizer:
    @staticmethod
    def create_topic_visualization(figure, lda_model, num_words=10):
        figure.clear()
        
        num_topics = lda_model.num_topics
        
        # Get top words for each topic
        topics_words = []
        for topic_id in range(num_topics):
            top_words = lda_model.show_topic(topic_id, num_words)
            topics_words.append([word for word, _ in top_words])
        
        # Create heatmap
        word_scores = np.zeros((num_topics, num_words))
        for topic_id in range(num_topics):
            top_words = lda_model.show_topic(topic_id, num_words)
            for word_id, (word, score) in enumerate(top_words):
                word_scores[topic_id, word_id] = score
        
        # Plot heatmap
        ax = figure.add_subplot(111)
        im = ax.imshow(word_scores, cmap='YlOrRd')
        
        # Add labels
        ax.set_xticks(np.arange(num_words))
        ax.set_yticks(np.arange(num_topics))
        ax.set_xticklabels([topics_words[0][i] for i in range(num_words)], rotation=45, ha='right')
        ax.set_yticklabels([f'Topic {i+1}' for i in range(num_topics)])
        
        # Add colorbar
        figure.colorbar(im)
        
        # Add title
        ax.set_title("Topic-Word Distributions")
        
        # Adjust layout
        figure.tight_layout()
        
        return topics_words
