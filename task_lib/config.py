import json
from pathlib import Path
from typing import Optional, Dict

class Config:
    def __init__(self, config_path: Optional[Path] = None):
        self.base_dir: Path = Path('.')
        self.openai_api_key: Optional[str] = None
        self.openai_model: str = "gpt-3.5-turbo"
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: Path) -> None:
        """Load configuration from a JSON file."""
        if not config_path.exists():
            logging.error(f"Config file {config_path} does not exist")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path) as f:
            config_data = json.load(f)
            
        # Set base directory
        if 'base_dir' in config_data:
            self.base_dir = Path(config_data['base_dir']).expanduser().resolve()
            logging.debug(f"Base directory set to: {self.base_dir}")

        # Set OpenAI configuration
        if 'openai' in config_data:
            openai_config = config_data['openai']
            self.openai_api_key = openai_config.get('api_key')
            self.openai_model = openai_config.get('model', self.openai_model)
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        result = {
            'base_dir': str(self.base_dir),
            'openai': {
                'api_key': self.openai_api_key,
                'model': self.openai_model
            }
        }
        logging.debug(f"Configuration converted to dict: {result}")
        return result
    
    def save_config(self, config_path: Path) -> None:
        """Save configuration to a JSON file."""
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logging.debug(f"Configuration saved to: {config_path}")
