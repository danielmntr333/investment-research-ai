"""Golden dataset management."""
from typing import List, Dict
import json
from pathlib import Path


class GoldenDataset:
    """
    Manage the golden evaluation dataset.
    """
    
    def __init__(self, dataset_path: str = "data/golden_dataset/questions.json"):
        """
        Initialize golden dataset manager.
        
        Args:
            dataset_path: Path to the JSON file containing test cases
        """
        self.dataset_path = Path(dataset_path)
        self.test_cases = self._load_dataset()
    
    def _load_dataset(self) -> List[Dict]:
        """Load golden dataset from JSON."""
        if not self.dataset_path.exists():
            print(f"Warning: Golden dataset not found at {self.dataset_path}")
            return []
        
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {self.dataset_path}")
            return []
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return []
    
    def load_dataset(self) -> List[Dict]:
        """Public method to load dataset (for backward compatibility)."""
        return self.test_cases
    
    def get_all_cases(self) -> List[Dict]:
        """Get all test cases."""
        return self.test_cases
    
    def get_by_difficulty(self, difficulty: str) -> List[Dict]:
        """
        Get test cases by difficulty level.
        
        Args:
            difficulty: 'easy', 'medium', or 'hard'
        """
        return [
            case for case in self.test_cases
            if case.get('difficulty') == difficulty
        ]
    
    def get_by_capability(self, capability: str) -> List[Dict]:
        """
        Get test cases requiring specific capability.
        
        Args:
            capability: e.g., 'multi_doc', 'calculation', 'comparison'
        """
        return [
            case for case in self.test_cases
            if capability in case.get('required_capabilities', [])
        ]
    
    def add_test_case(self, test_case: Dict):
        """
        Add a new test case to the dataset.
        
        Args:
            test_case: Dict containing test case fields
        """
        self.test_cases.append(test_case)
        self._save_dataset()
    
    def _save_dataset(self):
        """Save dataset to JSON."""
        # Ensure directory exists
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.dataset_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_cases, f, indent=2, ensure_ascii=False)
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics."""
        difficulties = {}
        capabilities = {}
        
        for case in self.test_cases:
            # Count by difficulty
            diff = case.get('difficulty', 'unknown')
            difficulties[diff] = difficulties.get(diff, 0) + 1
            
            # Count by capability
            for cap in case.get('required_capabilities', []):
                capabilities[cap] = capabilities.get(cap, 0) + 1
        
        return {
            'total_cases': len(self.test_cases),
            'by_difficulty': difficulties,
            'by_capability': capabilities
        }
    
    def validate_test_case(self, test_case: Dict) -> bool:
        """
        Validate that a test case has required fields.
        
        Args:
            test_case: Test case dict to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['id', 'question', 'expected_answer']
        return all(field in test_case for field in required_fields)
