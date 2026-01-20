from typing import Optional

class ProviderDetector:
    """
    Detects the lab provider based on page text content.
    """
    
    PROVIDERS = {
        "synevo": ["synevo", "laborator synevo", "medicover", "synevo romania"],
        "regina_maria": ["regina maria", "reteaua de sanatate", "reginamaria.ro", "centrul medical unirea"],
        "bioclinic": ["bioclinic", "bioclinica"]
    }

    @staticmethod
    def detect(text: str) -> str:
        """
        Returns 'synevo', 'regina_maria', or 'generic'.
        """
        if not text:
            return "generic"
            
        lower_text = text.lower()
        
        # Check specific signatures
        for provider, keywords in ProviderDetector.PROVIDERS.items():
            for k in keywords:
                if k in lower_text:
                    return provider
                    
        return "generic"
