"""Base interfaces for database lookups"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.models import DatabaseResult, Verdict


class BaseDatabase(ABC):
    """Base class for threat database lookups"""
    
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.cache = {}
    
    @abstractmethod
    async def lookup(self, input_str: str) -> Dict[str, Any]:
        """
        Look up input in database
        
        Returns:
            Dictionary with lookup results
        """
        pass
    
    async def analyze(self, input_str: str) -> DatabaseResult:
        """
        Analyze input using database lookup
        
        Args:
            input_str: Input to analyze
            
        Returns:
            DatabaseResult object
        """
        try:
            result = await self.lookup(input_str)
            
            if result.get('found'):
                verdict_map = {
                    'malicious': Verdict.MALICIOUS,
                    'phishing': Verdict.MALICIOUS,
                    'suspicious': Verdict.SUSPICIOUS
                }
                verdict = verdict_map.get(result.get('threat_type', 'malicious'), Verdict.MALICIOUS)
                confidence = result.get('confidence', 0.9)
                
                return DatabaseResult(
                    db_name=self.db_name,
                    found=True,
                    verdict=verdict,
                    confidence=confidence,
                    details=result.get('details', 'Found in database')
                )
            else:
                return DatabaseResult(
                    db_name=self.db_name,
                    found=False,
                    verdict=Verdict.SAFE,
                    confidence=0.1,
                    details="Not found in database"
                )
                
        except Exception as e:
            return DatabaseResult(
                db_name=self.db_name,
                found=False,
                verdict=Verdict.ERROR,
                confidence=0.0,
                details=f"Database error: {str(e)}"
            )