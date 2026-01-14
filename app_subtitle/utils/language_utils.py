# app_subtitle/utils/language_utils.py
"""Utility functions for language code normalization."""

# Mapping from French language names to ISO codes accepted by Whisper
LANGUAGE_NAME_TO_CODE = {
    # French names (lowercase) -> ISO code
    "français": "fr",
    "francais": "fr",
    "anglais": "en",
    "espagnol": "es",
    "allemand": "de",
    "italien": "it",
    "portugais": "pt",
    "néerlandais": "nl",
    "neerlandais": "nl",
    "russe": "ru",
    "chinois": "zh",
    "japonais": "ja",
    "coréen": "ko",
    "arabe": "ar",
    "hindi": "hi",
    "turc": "tr",
    "polonais": "pl",
    "suédois": "sv",
    "danois": "da",
    "norvégien": "no",
    "norvegien": "no",
    "finnois": "fi",
    "grec": "el",
    "hébreu": "he",
    "hebreu": "he",
    "thaï": "th",
    "thai": "th",
    "vietnamien": "vi",
    "indonésien": "id",
    "indonesien": "id",
    "malais": "ms",
    "catalan": "ca",
    "ukrainien": "uk",
    "roumain": "ro",
    "tchèque": "cs",
    "tcheque": "cs",
    "hongrois": "hu",
    
    # English names (lowercase) -> keep as is
    "french": "fr",
    "english": "en",
    "spanish": "es",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "dutch": "nl",
    "russian": "ru",
    "chinese": "zh",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
    "hindi": "hi",
    "turkish": "tr",
    "polish": "pl",
    "swedish": "sv",
    "danish": "da",
    "norwegian": "no",
    "finnish": "fi",
    "greek": "el",
    "hebrew": "he",
    "thai": "th",
    "vietnamese": "vi",
    "indonesian": "id",
    "malay": "ms",
    "catalan": "ca",
    "ukrainian": "uk",
    "romanian": "ro",
    "czech": "cs",
    "hungarian": "hu",
}

# Valid ISO codes accepted by Whisper
WHISPER_SUPPORTED_CODES = {
    "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs",
    "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi",
    "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy",
    "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb",
    "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt",
    "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru",
    "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw",
    "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi",
    "yi", "yo", "zh", "yue"
}


def normalize_language_code(language: str) -> str:
    """
    Normalize language input to a valid Whisper language code.
    
    Handles:
    - None, "auto", "" -> None (auto-detection)
    - French names (e.g., "Espagnol") -> ISO code (e.g., "es")
    - English names (e.g., "Spanish") -> ISO code (e.g., "es")
    - ISO codes (e.g., "es") -> validated and returned as is
    
    Args:
        language: Language name or code (can be None)
        
    Returns:
        Valid ISO language code or None for auto-detection
        
    Raises:
        ValueError: If language is not recognized or supported
    """
    # Handle None, empty string, or "auto"
    if not language or language.lower() in ["auto", "none"]:
        return None
    
    # Normalize to lowercase and strip whitespace
    normalized = language.lower().strip()
    
    # Check if already a valid ISO code
    if normalized in WHISPER_SUPPORTED_CODES:
        return normalized
    
    # Try to find in mapping (French/English names)
    if normalized in LANGUAGE_NAME_TO_CODE:
        return LANGUAGE_NAME_TO_CODE[normalized]
    
    # If not found, raise a helpful error
    raise ValueError(
        f"Unsupported language: '{language}'. "
        f"Please use an ISO code (e.g., 'es', 'fr', 'en') "
        f"or a recognized language name (e.g., 'Spanish', 'Espagnol')."
    )


def get_language_display_name(code: str) -> str:
    """
    Get a user-friendly display name for a language code.
    
    Args:
        code: ISO language code
        
    Returns:
        Display name in French (or code if not found)
    """
    code_to_name = {
        "fr": "Français",
        "en": "Anglais",
        "es": "Espagnol",
        "de": "Allemand",
        "it": "Italien",
        "pt": "Portugais",
        "nl": "Néerlandais",
        "ru": "Russe",
        "zh": "Chinois",
        "ja": "Japonais",
        "ko": "Coréen",
        "ar": "Arabe",
        "hi": "Hindi",
        "tr": "Turc",
        "pl": "Polonais",
        "sv": "Suédois",
        "da": "Danois",
        "no": "Norvégien",
        "fi": "Finnois",
        "el": "Grec",
        "he": "Hébreu",
        "th": "Thaï",
        "vi": "Vietnamien",
        "id": "Indonésien",
        "ms": "Malais",
        "ca": "Catalan",
        "uk": "Ukrainien",
        "ro": "Roumain",
        "cs": "Tchèque",
        "hu": "Hongrois",
    }
    return code_to_name.get(code, code.upper())
