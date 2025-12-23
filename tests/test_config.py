import unittest
import json
import tempfile
import shutil
from pathlib import Path
from task_lib.config import Config


class TestConfig(unittest.TestCase):
    """Test suite for the Config class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_file = self.test_dir / "test_config.json"

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_config_default_initialization(self):
        """Test Config initialization with defaults."""
        config = Config()
        self.assertEqual(config.base_dir, Path('.'))
        self.assertIsNone(config.openai_api_key)
        self.assertEqual(config.openai_model, "gpt-3.5-turbo")

    def test_config_initialization_with_file(self):
        """Test Config initialization with config file."""
        config_data = {
            'base_dir': str(self.test_dir),
            'openai': {
                'api_key': 'test-key-123',
                'model': 'gpt-4'
            }
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config(self.config_file)
        self.assertEqual(config.base_dir, self.test_dir)
        self.assertEqual(config.openai_api_key, 'test-key-123')
        self.assertEqual(config.openai_model, 'gpt-4')

    def test_load_config_basic(self):
        """Test loading basic configuration."""
        config_data = {
            'base_dir': str(self.test_dir)
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config()
        config.load_config(self.config_file)
        self.assertEqual(config.base_dir, self.test_dir)

    def test_load_config_with_openai(self):
        """Test loading configuration with OpenAI settings."""
        config_data = {
            'base_dir': str(self.test_dir),
            'openai': {
                'api_key': 'sk-test123',
                'model': 'gpt-4-turbo'
            }
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config()
        config.load_config(self.config_file)
        self.assertEqual(config.openai_api_key, 'sk-test123')
        self.assertEqual(config.openai_model, 'gpt-4-turbo')

    def test_load_config_openai_partial(self):
        """Test loading config with only OpenAI API key."""
        config_data = {
            'base_dir': str(self.test_dir),
            'openai': {
                'api_key': 'sk-test123'
            }
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config()
        config.load_config(self.config_file)
        self.assertEqual(config.openai_api_key, 'sk-test123')
        self.assertEqual(config.openai_model, 'gpt-3.5-turbo')  # Default

    def test_load_config_file_not_found(self):
        """Test loading non-existent config file raises error."""
        config = Config()
        non_existent_file = self.test_dir / "non_existent.json"

        with self.assertRaises(FileNotFoundError):
            config.load_config(non_existent_file)

    def test_load_config_expands_user_path(self):
        """Test that config expands ~ in paths."""
        config_data = {
            'base_dir': '~/test_tasks'
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config()
        config.load_config(self.config_file)

        # Should be expanded and resolved
        self.assertNotIn('~', str(config.base_dir))
        self.assertTrue(config.base_dir.is_absolute())

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
        config.base_dir = self.test_dir
        config.openai_api_key = 'test-key'
        config.openai_model = 'gpt-4'

        config_dict = config.to_dict()

        self.assertEqual(config_dict['base_dir'], str(self.test_dir))
        self.assertEqual(config_dict['openai']['api_key'], 'test-key')
        self.assertEqual(config_dict['openai']['model'], 'gpt-4')

    def test_to_dict_with_none_api_key(self):
        """Test converting config to dict with None API key."""
        config = Config()
        config.base_dir = self.test_dir

        config_dict = config.to_dict()

        self.assertEqual(config_dict['base_dir'], str(self.test_dir))
        self.assertIsNone(config_dict['openai']['api_key'])
        self.assertEqual(config_dict['openai']['model'], 'gpt-3.5-turbo')

    def test_save_config(self):
        """Test saving configuration to file."""
        config = Config()
        config.base_dir = self.test_dir
        config.openai_api_key = 'test-key-save'
        config.openai_model = 'gpt-4'

        config.save_config(self.config_file)

        # Verify file was created
        self.assertTrue(self.config_file.exists())

        # Verify content
        with open(self.config_file, 'r') as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data['base_dir'], str(self.test_dir))
        self.assertEqual(saved_data['openai']['api_key'], 'test-key-save')
        self.assertEqual(saved_data['openai']['model'], 'gpt-4')

    def test_save_and_load_roundtrip(self):
        """Test that saving and loading preserves config."""
        original_config = Config()
        original_config.base_dir = self.test_dir
        original_config.openai_api_key = 'roundtrip-key'
        original_config.openai_model = 'gpt-4-turbo'

        original_config.save_config(self.config_file)

        loaded_config = Config(self.config_file)

        self.assertEqual(loaded_config.base_dir, original_config.base_dir)
        self.assertEqual(loaded_config.openai_api_key, original_config.openai_api_key)
        self.assertEqual(loaded_config.openai_model, original_config.openai_model)

    def test_load_config_with_empty_openai(self):
        """Test loading config with empty openai section."""
        config_data = {
            'base_dir': str(self.test_dir),
            'openai': {}
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config()
        config.load_config(self.config_file)

        self.assertIsNone(config.openai_api_key)
        self.assertEqual(config.openai_model, 'gpt-3.5-turbo')

    def test_load_config_minimal(self):
        """Test loading minimal config with only base_dir."""
        config_data = {
            'base_dir': str(self.test_dir)
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)

        config = Config()
        config.load_config(self.config_file)

        self.assertEqual(config.base_dir, self.test_dir)
        self.assertIsNone(config.openai_api_key)
        self.assertEqual(config.openai_model, 'gpt-3.5-turbo')


if __name__ == '__main__':
    unittest.main()
