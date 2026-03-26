"""
Tests for OllamaRama failover proxy
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import OllamaInstanceManager


class TestPortParsing:
    """Test port configuration parsing"""
    
    def test_parse_single_ports(self):
        """Test parsing individual ports"""
        manager = OllamaInstanceManager("11434,11435,11436")
        instances = manager.get_all_instances()
        assert len(instances) == 3
        assert "http://localhost:11434" in instances
        assert "http://localhost:11435" in instances
        assert "http://localhost:11436" in instances
    
    def test_parse_port_range(self):
        """Test parsing port ranges"""
        manager = OllamaInstanceManager("11434-11436")
        instances = manager.get_all_instances()
        assert len(instances) == 3
        assert "http://localhost:11434" in instances
        assert "http://localhost:11435" in instances
        assert "http://localhost:11436" in instances
    
    def test_parse_mixed_format(self):
        """Test parsing mixed single ports and ranges"""
        manager = OllamaInstanceManager("11434-11436,11440,11442-11443")
        instances = manager.get_all_instances()
        assert len(instances) == 6
        assert "http://localhost:11434" in instances
        assert "http://localhost:11440" in instances
        assert "http://localhost:11443" in instances
    
    def test_parse_with_spaces(self):
        """Test parsing with extra spaces"""
        manager = OllamaInstanceManager("11434 - 11436 , 11440")
        instances = manager.get_all_instances()
        assert len(instances) == 4
    
    def test_invalid_config_empty(self):
        """Test that empty config raises error"""
        with pytest.raises(ValueError):
            OllamaInstanceManager("")
    
    def test_invalid_config_none(self):
        """Test that None config raises error"""
        with pytest.raises(ValueError):
            OllamaInstanceManager("")


class TestInstanceFailover:
    """Test failover logic"""
    
    def test_get_next_instance_rotation(self):
        """Test that instances rotate correctly"""
        manager = OllamaInstanceManager("11434,11435,11436")
        
        # Should rotate through instances
        first = manager.get_next_instance()
        second = manager.get_next_instance()
        third = manager.get_next_instance()
        fourth = manager.get_next_instance()  # Should wrap around
        
        assert first == "http://localhost:11434"
        assert second == "http://localhost:11435"
        assert third == "http://localhost:11436"
        assert fourth == "http://localhost:11434"
    
    def test_reset_to_start(self):
        """Test reset to first instance"""
        manager = OllamaInstanceManager("11434,11435,11436")
        
        # Advance through instances
        manager.get_next_instance()
        manager.get_next_instance()
        
        # Reset
        manager.reset_to_start()
        
        # Should start from beginning
        assert manager.get_next_instance() == "http://localhost:11434"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
