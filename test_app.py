import unittest
import os
import streamlit as st
from app import (
    build_reading_prompt, 
    get_system_prompt, 
    get_followup_system_prompt, 
    get_gemini_client,
    get_custom_css,
    init_session_state
)

class TestHasthrekhaApp(unittest.TestCase):
    
    def test_build_reading_prompt_english(self):
        """Test build_reading_prompt returns the correct English prompt structure."""
        prompt = build_reading_prompt("complete", "Western", "en")
        self.assertIn("complete", prompt.lower())
        self.assertIn("western", prompt.lower())
        self.assertIn("heart line", prompt.lower())

    def test_build_reading_prompt_hindi(self):
        """Test build_reading_prompt returns the correct Hindi prompt structure."""
        prompt = build_reading_prompt("complete", "🕉️ वैदिक (भारतीय)", "hi")
        self.assertIn("वैदिक", prompt)
        self.assertIn("हृदय रेखा", prompt)

    def test_build_reading_prompt_categories(self):
        """Test different reading categories are routed properly."""
        love_prompt_en = build_reading_prompt("love", "Vedic", "en")
        self.assertIn("venus", love_prompt_en.lower())
        self.assertIn("relationship", love_prompt_en.lower())

        career_prompt_en = build_reading_prompt("career", "Vedic", "en")
        self.assertIn("fate", career_prompt_en.lower())
        self.assertIn("sun", career_prompt_en.lower())
        self.assertIn("jupiter", career_prompt_en.lower())

    def test_system_prompt_languages(self):
        """Test get_system_prompt injects appropriate language instructions."""
        prompt_hi = get_system_prompt("hi")
        self.assertIn("devanagari", prompt_hi.lower())
        self.assertIn("hindi", prompt_hi.lower())

        prompt_en = get_system_prompt("en")
        self.assertIn("english", prompt_en.lower())

    def test_followup_system_prompt_languages(self):
        """Test get_followup_system_prompt injects appropriate language instructions."""
        prompt_hi = get_followup_system_prompt("hi")
        self.assertIn("devanagari", prompt_hi.lower())
        
        prompt_en = get_followup_system_prompt("en")
        self.assertIn("english", prompt_en.lower())

    def test_client_init_without_key(self):
        """Test client initialization returns None when no key is configured."""
        # Backup environment key
        old_env_key = os.environ.get("GEMINI_API_KEY")
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
            
        old_session_key = st.session_state.get("api_key")
        st.session_state["api_key"] = ""
        
        try:
            client = get_gemini_client()
            self.assertIsNone(client)
        finally:
            # Restore backup
            if old_env_key is not None:
                os.environ["GEMINI_API_KEY"] = old_env_key
            if old_session_key is not None:
                st.session_state["api_key"] = old_session_key

    def test_get_custom_css(self):
        """Test get_custom_css returns valid CSS configurations and styling tags."""
        css = get_custom_css()
        self.assertTrue(css.strip().startswith("<style>"))
        self.assertTrue(css.strip().endswith("</style>"))
        self.assertIn("stApp", css)
        self.assertIn("stChatMessage", css)
        self.assertIn("stChatInput", css)

    def test_init_session_state(self):
        """Test that init_session_state sets default variables correctly."""
        # Ensure clean state for variables we test
        test_keys = ["loading", "last_uploaded_file_id", "reading_done", "chat_history"]
        for key in test_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        init_session_state()
        self.assertFalse(st.session_state.loading)
        self.assertIsNone(st.session_state.last_uploaded_file_id)
        self.assertFalse(st.session_state.reading_done)
        self.assertEqual(st.session_state.chat_history, [])

if __name__ == "__main__":
    unittest.main()
