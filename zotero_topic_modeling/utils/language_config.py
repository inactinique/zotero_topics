from dataclasses import dataclass
from typing import List, Dict
from nltk.corpus import stopwords
import nltk

@dataclass
class LanguageConfig:
    code: str
    name: str
    nltk_resources: List[str]
    stopwords_available: bool = True

    def ensure_resources(self):
        """Ensure all required NLTK resources are available"""
        for resource in self.nltk_resources:
            try:
                nltk.data.find(resource)
            except LookupError:
                nltk.download(resource)

class LanguageManager:
    def __init__(self):
        self.languages: Dict[str, LanguageConfig] = {
            'en': LanguageConfig(
                code='en',
                name='English',
                nltk_resources=['punkt', 'stopwords', 'averaged_perceptron_tagger'],
            ),
            'fr': LanguageConfig(
                code='fr',
                name='French',
                nltk_resources=['punkt', 'stopwords', 'averaged_perceptron_tagger_fr'],
            ),
            'de': LanguageConfig(
                code='de',
                name='German',
                nltk_resources=['punkt', 'stopwords', 'averaged_perceptron_tagger_de'],
            ),
        }

    def get_language_names(self) -> List[str]:
        """Get list of available language names"""
        return [lang.name for lang in self.languages.values()]

    def get_language_by_name(self, name: str) -> LanguageConfig:
        """Get language config by its name"""
        for lang in self.languages.values():
            if lang.name == name:
                return lang
        raise ValueError(f"Language {name} not found")

    def get_stopwords(self, language_code: str) -> set:
        """Get stopwords for a specific language"""
        try:
            return set(stopwords.words(language_code))
        except OSError:
            return set()

    def add_language(self, code: str, name: str, nltk_resources: List[str]) -> None:
        """Add a new language configuration"""
        self.languages[code] = LanguageConfig(
            code=code,
            name=name,
            nltk_resources=nltk_resources
        )
