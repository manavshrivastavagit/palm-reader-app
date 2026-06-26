"""
🔮 Hasthrekha — AI-Powered Multilingual Palm Reading
Streamlit app that uses Gemini's multimodal vision to analyze palm images.
"""

import streamlit as st
from typing import Optional
from google import genai
from PIL import Image, ImageDraw, ImageFilter
import io
import os
import json
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import plotly.graph_objects as go

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("hasthrekha")

load_dotenv()

# ─────────────────────────────────────────────
# Structured API Response Schemas
# ─────────────────────────────────────────────

class PalmMetrics(BaseModel):
    rationality: int = Field(description="Rating from 1 to 100 for logic, intellect, and analytical thinking style based on the Head Line")
    emotionality: int = Field(description="Rating from 1 to 100 for emotional sensitivity, relationships, and depth of feelings based on the Heart Line")
    vitality: int = Field(description="Rating from 1 to 100 for physical vitality, energy, and life drive based on the Life Line")
    ambition: int = Field(description="Rating from 1 to 100 for ambition, focus, leadership, and career drive based on the Jupiter mount and Fate Line")
    intuition: int = Field(description="Rating from 1 to 100 for intuition, creativity, and subconscious insights based on the Moon mount and markings")

class PalmReadingResponse(BaseModel):
    is_valid_hand: bool = Field(description="True if the uploaded image contains a visible human hand or open palm, False otherwise")
    refusal_reason: str = Field(default="", description="If is_valid_hand is False, explain politely why the image is invalid and request a clear palm photo. Otherwise, leave empty.")
    metrics: Optional[PalmMetrics] = Field(None, description="The palmistry metrics. Required if is_valid_hand is True.")
    reading: str = Field("", description="The detailed markdown reading content. Required if is_valid_hand is True.")

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

READING_CATEGORIES_HI = {
    "✨ संपूर्ण विश्लेषण": "complete",
    "❤️ प्रेम और संबंध": "love",
    "💼 करियर और उद्देश्य": "career",
    "💪 स्वास्थ्य और ऊर्जा": "health",
    "💰 धन और भाग्य": "wealth",
    "🧠 व्यक्तित्व और स्वभाव": "personality",
}

READING_CATEGORIES_EN = {
    "✨ Complete Reading": "complete",
    "❤️ Love & Relationships": "love",
    "💼 Career & Purpose": "career",
    "💪 Health & Vitality": "health",
    "💰 Wealth & Fortune": "wealth",
    "🧠 Personality & Temperament": "personality",
}

TRADITIONS_HI = {
    "🕉️ वैदिक (भारतीय)": "Vedic/Indian",
    "🌍 पश्चिमी": "Western",
    "🏮 चीनी (手相)": "Chinese",
    "🌐 सभी परंपराएं": "all three traditions (Vedic, Western, and Chinese)",
}

TRADITIONS_EN = {
    "🕉️ Vedic (Indian)": "Vedic/Indian",
    "🌍 Western": "Western",
    "🏮 Chinese (手相)": "Chinese",
    "🌐 All Traditions": "all three traditions (Vedic, Western, and Chinese)",
}

# ─────────────────────────────────────────────
# Translations
# ─────────────────────────────────────────────

TRANSLATIONS = {
    "hi": {
        "app_title": "🔮🖐️ हस्तरेखा (Hasthrekha)",
        "app_subtitle": "एआई-संचालित हस्तरेखा शास्त्र — प्राचीन ज्ञान और आधुनिक तकनीक का मिलन",
        "settings": "⚙️ सेटिंग्स",
        "lang_label": "🌐 ऐप की भाषा (App Language)",
        "api_key_label": "🔑 जेमिनी एपीआई कुंजी (Gemini API Key)",
        "api_key_help": "https://aistudio.google.com/apikey पर अपनी एपीआई कुंजी प्राप्त करें",
        "category_label": "📖 विश्लेषण का प्रकार",
        "category_help": "हस्तरेखा के किस पहलू पर ध्यान केंद्रित करना है, चुनें",
        "tradition_label": "🌏 हस्तरेखा परंपरा",
        "tradition_help": "अपने हाथ की व्याख्या करने के लिए परंपरा चुनें",
        "how_it_works": "📋 यह कैसे काम करता है",
        "how_it_works_steps": """
1. 📸 **अपलोड करें**: अपने हाथ की एक साफ फोटो अपलोड करें
2. 🔮 **चुनें**: विश्लेषण का प्रकार और परंपरा चुनें
3. ✨ **प्राप्त करें**: अपना एआई-संचालित हस्तरेखा विश्लेषण देखें
4. 💬 **पूछें**: यदि कोई प्रश्न हो तो आगे चैट करें
""",
        "tips_title": "📷 सर्वोत्तम परिणामों के लिए टिप्स",
        "tips_content": """
- **अच्छी और समान रोशनी** का उपयोग करें (प्राकृतिक रोशनी सबसे अच्छी है)
- **अपनी हथेली पूरी तरह से खोलें** — उंगलियों को थोड़ा फैलाएं
- अपने **मुख्य हाथ** की फोटो लें (दाएं हाथ से काम करते हैं तो दायां)
- हथेली पर **परछाई न आने दें**
- **इतना करीब लाएं** कि रेखाएं स्पष्ट रूप से दिखाई दें
- कैमरे को हथेली के **ठीक ऊपर** सीधा रखें
""",
        "disclaimer_poc": "🔮 हस्तरेखा POC v1.0\n\nजेमिनी 2.5 फ्लैश द्वारा संचालित\n\nकेवल मनोरंजन और आत्म-चिंतन के लिए",
        "upload_label": "अपने हाथ की फोटो अपलोड करें",
        "upload_help": "अपनी खुली हथेली की एक साफ, अच्छी रोशनी वाली फोटो अपलोड करें",
        "upload_instruction": "📸 **हथेली की फोटो अपलोड करें** या यहां ड्रैग एंड ड्रॉप करें",
        "camera_instruction": "या अपने कैमरे से फोटो लें",
        "camera_help": "अपनी हथेली को फ्रेम में स्पष्ट रूप से रखें",
        "your_palm": "आपकी हथेली",
        "read_button": "🔮 हस्तरेखा विश्लेषण करें — {category}",
        "spinner_reading": "✨ हस्तरेखा शास्त्री आपके हाथ का अध्ययन कर रहे हैं...",
        "detecting_lines": "🔍 पाम रेखाओं का पता लगाया जा रहा है...",
        "error_reading": "❌ विश्लेषण के दौरान त्रुटि: {error}",
        "new_reading": "🔄 नया विश्लेषण",
        "download_reading": "📥 विश्लेषण डाउनलोड करें",
        "copy_reading": "📋 क्लिपबोर्ड पर कॉपी करें",
        "copy_toast": "📋 विश्लेषण कॉपी हो गया!",
        "chat_title": "💬 हस्तरेखा शास्त्री से प्रश्न पूछें",
        "chat_caption": "अपने विश्लेषण के बारे में कुछ भी पूछें — प्रेम, करियर, विशिष्ट रेखाएं या जीवन मार्गदर्शन।",
        "chat_input_placeholder": "अपने हस्तरेखा विश्लेषण के बारे में पूछें...",
        "chat_spinner": "विचार किया जा रहा है...",
        "ai_vision_title": "🔬 एआई विज़न विश्लेषण",
        "ai_vision_desc": "जेमिनी का मल्टीमॉडल एआई आपकी हथेली की रेखाओं, पर्वतों, हाथ के आकार और विशेष निशानों का सटीकता से विश्लेषण करता है।",
        "traditions_title": "📜 तीन परंपराएं",
        "traditions_desc": "वैदिक, पश्चिमी और चीनी हस्तरेखा शास्त्र पर आधारित विश्लेषण प्राप्त करें — या तीनों को मिलाकर देखें।",
        "chat_feature_title": "💬 प्रश्न पूछें",
        "chat_feature_desc": "अपने विश्लेषण के बारे में हस्तरेखा शास्त्री से चैट करें। प्यार, करियर, स्वास्थ्य या किसी भी रेखा के बारे में पूछें।",
        "portfolio_title": "👤 मानव श्रीवास्तव — एआई सॉल्यूशन आर्किटेक्ट",
        "github_label": "💻 गिटहब रिपोजिटरी",
        "linkedin_label": "🔗 लिंक्डइन प्रोफाइल",
        "app_intro": "हस्तरेखा शास्त्र (हस्तरेखा) हथेली के आकार, रेखाओं, पर्वतों और निशानों के अध्ययन के माध्यम से किसी व्यक्ति के चरित्र, ऊर्जा, क्षमता और जीवन पथ को समझने की एक प्राचीन कला और विज्ञान है। सदियों से विविध संस्कृतियों में उपयोग की जाने वाली यह पद्धति आत्म-चिंतन, अपनी क्षमता को समझने और जीवन मार्गदर्शन प्राप्त करने के लिए एक दर्पण का कार्य करती है।",
        "footer_disclaimer": "⚠️ हस्तरेखा केवल मनोरंजन और आत्म-चिंतन के उद्देश्य से है। यह चिकित्सा, वित्तीय या व्यावसायिक सलाह प्रदान नहीं करती है।\n\nआपकी हथेली की तस्वीरें एआई द्वारा प्रोसेस की जाती हैं और इन्हें कहीं भी स्टोर नहीं किया जाता है।",
        "tab_reading": "🔮 हस्तरेखा विश्लेषण",
        "tab_live": "📷 लाइव स्कैनर",
        "live_title": "🖐️ लाइव हस्त पहचान",
        "live_caption": "अपनी हथेली कैमरे के सामने रखें। मीडियापाइप एआई तुरंत आपकी हस्त रेखाओं की पहचान करेगा।",
        "live_tip": "💡 टिप: सर्वोत्तम पहचान के लिए अपना हाथ खुला रखें और अच्छी रोशनी सुनिश्चित करें।",
        "live_snapshot_hint": "📸 पूर्ण एआई विश्लेषण के लिए **हस्तरेखा विश्लेषण** टैब का उपयोग करें।",
        "scan_heading": "🔬 एआई दृष्टि विश्लेषण — हथेली स्कैन हो रही है...",
        "scan_complete": "✅ हस्तेली स्कैन पूर्ण — विश्लेषण के लिए तैयार",
    },
    "en": {
        "app_title": "🔮🖐️ Hasthrekha",
        "app_subtitle": "AI-Powered Palm Reading — Ancient Wisdom Meets Modern Intelligence",
        "settings": "⚙️ Settings",
        "lang_label": "🌐 App Language",
        "api_key_label": "🔑 Gemini API Key",
        "api_key_help": "Get your key at https://aistudio.google.com/apikey",
        "category_label": "📖 Reading Category",
        "category_help": "Choose what aspect of your palm to focus on",
        "tradition_label": "🌏 Palmistry Tradition",
        "tradition_help": "Choose which tradition to interpret your palm",
        "how_it_works": "📋 How It Works",
        "how_it_works_steps": """
1. 📸 **Upload** a clear photo of your palm
2. 🔮 **Choose** reading category & tradition
3. ✨ **Get** your AI-powered reading
4. 💬 **Ask** follow-up questions
""",
        "tips_title": "📷 Tips for Best Results",
        "tips_content": """
- Use **good, even lighting** (natural light is best)
- **Open your palm fully** — spread fingers slightly
- Capture your **dominant hand** (right if right-handed)
- **Avoid shadows** across the palm
- Get **close enough** to see the lines clearly
- Hold the camera **directly above** the palm
""",
        "disclaimer_poc": "🔮 Hasthrekha POC v1.0\n\nPowered by Gemini 2.5 Flash\n\nFor entertainment & self-reflection only",
        "upload_label": "Upload your palm image",
        "upload_help": "Upload a clear, well-lit photo of your open palm",
        "upload_instruction": "📸 **Upload a photo of your palm** or drag and drop here",
        "camera_instruction": "Or take a photo with your camera",
        "camera_help": "Position your palm clearly in frame",
        "your_palm": "Your Palm",
        "read_button": "🔮 Read My Palm — {category}",
        "spinner_reading": "✨ Hasthrekha is studying your palm...",
        "detecting_lines": "🔍 Detecting palm lines...",
        "error_reading": "❌ Error during reading: {error}",
        "new_reading": "🔄 New Reading",
        "download_reading": "📥 Download Reading",
        "copy_reading": "📋 Copy to Clipboard",
        "copy_toast": "📋 Reading copied!",
        "chat_title": "💬 Ask Hasthrekha a Follow-up Question",
        "chat_caption": "Ask anything about your reading — love, career, specific lines, or life guidance.",
        "chat_input_placeholder": "Ask about your palm reading...",
        "chat_spinner": "Hasthrekha is reflecting...",
        "ai_vision_title": "🔬 AI Vision Analysis",
        "ai_vision_desc": "Gemini's multimodal AI examines your palm lines, mounts, hand shape, and special markings with precision.",
        "traditions_title": "📜 Three Traditions",
        "traditions_desc": "Get readings grounded in Vedic, Western, and Chinese palmistry — or all three combined.",
        "chat_feature_title": "💬 Ask Follow-ups",
        "chat_feature_desc": "Chat with Hasthrekha about your reading. Ask about love, career, health, or any specific line.",
        "portfolio_title": "👤 Manav Shrivastava — AI Solution Architect",
        "github_label": "💻 GitHub Repository",
        "linkedin_label": "🔗 LinkedIn Profile",
        "app_intro": "Palmistry (Hasthrekha) is the ancient art and science of reading the character, vitality, traits, and life path of an individual through the study of the shape, lines, mounts, and markings of the palm. Used across diverse cultures for centuries, it serves as a powerful mirror for self-reflection, understanding potential, and seeking guidance.",
        "footer_disclaimer": "⚠️ Hasthrekha is for entertainment and self-reflection purposes only. It does not provide medical, financial, or professional advice.\n\nYour palm images are processed by AI and are not permanently stored.",
        "tab_reading": "🔮 Palm Reading",
        "tab_live": "📷 Live Scanner",
        "live_title": "🖐️ Live Hand Detection",
        "live_caption": "Hold your palm up to the camera. MediaPipe AI will detect and highlight your hand landmarks in real time.",
        "live_tip": "💡 Tip: Open your hand flat towards the camera with good lighting for best detection results.",
        "live_snapshot_hint": "📸 Use the **Palm Reading** tab to upload a snapshot for a full AI reading.",
        "scan_heading": "🔬 AI Vision Analysis — Scanning Palm...",
        "scan_complete": "✅ Palm Scan Complete — Ready for Reading",
    }
}

# ─────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────

def get_system_prompt(lang: str) -> str:
    if lang == "hi":
        lang_instruction = """- ALWAYS respond in Hindi (Devanagari script). Use Hindi for all explanations and insights.
  Keep palmistry technical terms in English where needed (e.g., Heart Line, Head Line, Jupiter Mount) 
  but explain everything else in Hindi. The tone should be polite, respectful, and wise."""
    else:
        lang_instruction = """- ALWAYS respond in English. Use English for all explanations and insights.
  Use clear, readable, warm English."""

    return f"""You are Hasthrekha, the world's foremost AI palm reader trained across 
Vedic, Western, and Chinese palmistry traditions. You are warm, insightful, and speak with 
gentle confidence — like a wise mentor who has studied thousands of palms.

CRITICAL RULES:
- IMAGE VALIDATION GUARDRAIL: Before providing any reading, verify if the uploaded image contains a human hand or open palm. If the image is NOT a human hand or palm (e.g., it is a random object, animal, document, landscape, or extremely blurry/unclear image), you MUST refuse to perform the analysis. State politely, in the requested language, that the image does not appear to show a clear human palm, and request the user to upload a well-lit photo of their open palm. Do NOT provide any reading in this case.
- You MUST analyze the actual image provided. Identify specific features visible in THIS palm.
- Never give generic readings. Reference specific lines, curves, depths, and markings you observe.
- Use language like "I can see that your [line] is [description]..." to show you're reading THEIR palm.
- Be specific about positions: "near the Jupiter mount," "ending under the Saturn finger," etc.
- Include both strengths and growth areas — never be entirely positive or negative.
- End sections with an empowering, forward-looking insight.
- Include a disclaimer that this is for entertainment and self-reflection purposes.
- Never make medical diagnoses or specific financial predictions.
- Format your response in rich markdown with clear sections and emoji headers.
{lang_instruction}"""


def get_followup_system_prompt(lang: str) -> str:
    if lang == "hi":
        lang_instruction = "ALWAYS respond in Hindi (Devanagari script). Keep palmistry terms in English but explain in Hindi."
    else:
        lang_instruction = "ALWAYS respond in English."

    return f"""You are Hasthrekha, continuing a palm reading conversation. 
The user has already received their initial reading and is now asking follow-up questions.

You have the context of their palm reading. Answer their questions with the same depth 
and specificity as the initial reading. Reference specific features from their palm.

If they ask about something not visible in the palm image, honestly say you cannot determine 
that from what's visible, and explain why.

DOMAIN LOCK & CONVERSATIONAL GUARDRAIL:
- You are strictly a palmistry and life guidance advisor.
- You MUST refuse to answer questions that are completely unrelated to palmistry, the user's uploaded hand image, or self-reflection based on their palm reading (e.g., asking for programming code, general knowledge questions, math problems, translations of unrelated text, or general chat).
- If the user asks an unrelated question, politely refuse to answer in the requested language and redirect them to ask questions related to their palmistry reading or hand guidance.

Stay in character — warm, insightful, and grounded in palmistry traditions.
Always format responses in clean markdown.
{lang_instruction}"""


def build_reading_prompt(category: str, tradition: str, lang: str) -> str:
    """Build the reading prompt based on user selections and language."""
    if lang == "hi":
        tradition_instruction = f"यह हस्तरेखा विश्लेषण {tradition} हस्तरेखा परंपरा(ओं) के दृष्टिकोण से प्रदान करें।"
        
        if category == "complete":
            return f"""इस हथेली की छवि का विश्लेषण करें और एक संपूर्ण विस्तृत हस्तरेखा विश्लेषण प्रदान करें।

{tradition_instruction}

अपनी प्रतिक्रिया को ठीक उसी प्रकार व्यवस्थित करें जैसा नीचे दिया गया है:

## 🖐️ हथेली का अवलोकन (Palm Overview)
छवि में दिखाई देने वाले हाथ के सामान्य आकार (पृथ्वी/वायु/अग्नि/जल), त्वचा की बनावट और उंगलियों के अनुपात का वर्णन करें।

## ❤️ हृदय रेखा विश्लेषण (Heart Line Analysis)
हृदय रेखा का विश्लेषण करें — इसका शुरुआती बिंदु, वक्र, गहराई, लंबाई, कोई भी टूटन या कांटे (forks), और वे भावनात्मक स्वभाव और संबंधों के बारे में क्या प्रकट करते हैं।

## 🧠 मस्तिष्क रेखा विश्लेषण (Head Line Analysis)
मस्तिष्क रेखा का विश्लेषण करें — इसका मार्ग, जीवन रेखा से जुड़ाव या अलगाव, कोई भी शाखाएं, और वे विचार शैली और बुद्धि के बारे में क्या संकेत देती हैं।

## 🌿 जीवन रेखा विश्लेषण (Life Line Analysis)
जीवन रेखा का विश्लेषण करें — इसका चाप (arc), गहराई, कोई भी टूटन या शाखाएं, और वे जीवन शक्ति, ऊर्जा और प्रमुख जीवन परिवर्तनों के बारे में क्या संकेत देती हैं। स्पष्ट करें कि यह जीवनकाल (lifespan) की अवधि के बारे में नहीं है।

## ⚡ भाग्य रेखा विश्लेषण (Fate Line Analysis)
यदि भाग्य रेखा दिखाई दे रही है, तो इसका विश्लेषण करें — इसका शुरुआती बिंदु, मजबूती, और यह करियर की दिशा और जीवन के उद्देश्य के बारे में क्या प्रकट करती है।

## ☀️ अन्य महत्वपूर्ण रेखाएं और निशान (Other Notable Lines & Markings)
दिखाई देने वाली किसी भी अतिरिक्त रेखा की पहचान करें (सूर्य रेखा, बुध रेखा, संबंध रेखाएं, मणिबंध (bracelets), तारे, क्रॉस, द्वीप, या अन्य विशेष निशान)।

## 🏔️ पर्वतों का विश्लेषण (Mount Analysis)
दिखाई देने वाले किसी भी पर्वत (गुरु, शनि, सूर्य/अपोलो, बुध, शुक्र, चंद्र, मंगल) के उभार और उनके महत्व का वर्णन करें।

## 🌟 समन्वय और जीवन मार्गदर्शन (Synthesis & Life Guidance)
व्यक्ति के चरित्र, ताकत, जीवन पथ और विकास के क्षेत्रों के बारे में एक सुसंगत विश्लेषण के साथ सभी अवलोकनों को एक साथ जोड़ें।

## 🔮 मुख्य निष्कर्ष (Key Takeaways)
5 बिंदुवार निष्कर्ष प्रदान करें — सबसे महत्वपूर्ण बातें जो यह हथेली प्रकट करती है।

इस छवि में आप जो देख रहे हैं, केवल उसी का संदर्भ लें। वास्तविक दृश्य विशेषताओं का उल्लेख करें।"""

        elif category == "love":
            return f"""इस हथेली की छवि का विश्लेषण विशेष रूप से प्रेम, संबंधों और भावनात्मक जीवन पर केंद्रित करते हुए करें।

{tradition_instruction}

इनका परीक्षण करें:
- हृदय रेखा (Heart Line): गहराई, वक्र, शुरुआती/समाप्ति बिंदु, कांटे, शाखाएं, द्वीप
- शुक्र पर्वत (Venus Mount): उभार और यह जुनून और कामुकता के बारे में क्या दर्शाता है
- संबंध/विवाह रेखाएं (Relationship/Marriage Lines): कनिष्ठिका उंगली (little finger) के नीचे किनारे पर कोई भी छोटी क्षैतिज रेखाएं
- शुक्र वलय (Girdle of Venus): यदि उपस्थित हो, तो इसका महत्व
- प्रभाव रेखाएं (Influence Lines): चंद्र पर्वत से भाग्य रेखा में शामिल होने वाली कोई भी रेखाएं

उनके भावनात्मक स्वभाव, संबंध पैटर्न, रोमांटिक प्रवृत्तियों और प्रेम जीवन के लिए मार्गदर्शन पर अंतर्दृष्टि प्रदान करें। इस हथेली में आप जो देख रहे हैं, केवल उसी का उल्लेख करें।"""

        elif category == "career":
            return f"""इस हथेली की छवि का विश्लेषण विशेष रूप से करियर, उद्देश्य और व्यावसायिक जीवन पर केंद्रित करते हुए करें।

{tradition_instruction}

इनका परीक्षण करें:
- भाग्य रेखा (Fate Line): मजबूती, शुरुआती बिंदु, टूटन, शाखाएं — करियर की दिशा के संकेतक
- सूर्य रेखा (Sun Line): उपस्थिति और स्पष्टता — प्रसिद्धि, सफलता और रचनात्मक उपलब्धि
- मस्तिष्क रेखा (Head Line): विचार शैली — व्यावहारिक बनाम रचनात्मक करियर संरेखण
- गुरु पर्वत और उंगली (Jupiter Mount & Finger): नेतृत्व क्षमता, महत्वाकांक्षा
- बुध उंगली और पर्वत (Mercury Finger & Mount): संचार और व्यावसायिक कौशल
- करियर की सफलता से संबंधित कोई भी विशेष निशान (पर्वतों पर तारे, वर्ग, त्रिकोण)

करियर की ताकत, आदर्श कार्य वातावरण, नेतृत्व शैली और व्यावसायिक मार्गदर्शन पर अंतर्दृष्टि प्रदान करें। इस हथेली में जो दिख रहा है, उसी का उल्लेख करें।"""

        elif category == "health":
            return f"""इस हथेली की छवि का विश्लेषण विशेष रूप से स्वास्थ्य संकेतकों और जीवन शक्ति पर केंद्रित करते हुए करें।

{tradition_instruction}

इनका परीक्षण करें:
- जीवन रेखा (Life Line): चाप, गहराई, जीवन शक्ति के संकेतक (जीवनकाल की भविष्यवाणी नहीं)
- स्वास्थ्य/बुध रेखा (Health/Mercury Line): यदि उपस्थित हो, तो उसकी स्थिति
- छवि में दिखाई देने वाले सामान्य रंग और बनावट का अवलोकन
- नाखून (यदि दिखाई दे रहे हों): पारंपरिक स्वास्थ्य संकेतकों के रूप में आकार और स्थिति
- तनाव के संकेतक: मुख्य रेखाओं पर द्वीप, जंजीरें, या गड़बड़ी
- शुक्र पर्वत (Venus Mount): जीवन शक्ति और शारीरिक ऊर्जा

महत्वपूर्ण: स्पष्ट रूप से बताएं कि ये आत्म-चिंतन के लिए पारंपरिक हस्तरेखा शास्त्र के अवलोकन हैं, चिकित्सा सलाह नहीं। स्वास्थ्य संबंधी चिंताओं के लिए हमेशा स्वास्थ्य पेशेवरों से परामर्श करने की सिफारिश करें। इस हथेली में जो दिख रहा है, उसी का उल्लेख करें।"""

        elif category == "wealth":
            return f"""इस हथेली की छवि का विश्लेषण विशेष रूप से धन, भाग्य और वित्तीय प्रवृत्तियों पर केंद्रित करते हुए करें।

{tradition_instruction}

इनका परीक्षण करें:
- भाग्य रेखा (Fate Line): स्थिरता और करियर-संचालित आय संकेतक
- सूर्य रेखा (Sun Line): सफलता, पहचान और समृद्धि के संकेतक
- बुध रेखा (Mercury Line): व्यावसायिक समझ और वित्तीय बुद्धिमत्ता
- धन त्रिकोण (Money Triangle): यदि मस्तिष्क, भाग्य और बुध रेखाओं द्वारा बनता है — उसकी पूर्णता
- गुरु पर्वत (Jupiter Mount): महत्वाकांक्षा और विकास की क्षमता
- कोई भी विशेष धन निशान (प्रासंगिक पर्वतों पर त्रिकोण, त्रिशूल, तारे)

वित्तीय प्रवृत्तियों, धन-निर्माण की ताकत और व्यावहारिक मार्गदर्शन पर अंतर्दृष्टि प्रदान करें। इस हथेली में जो दिख रहा है, उसी का उल्लेख करें।"""

        elif category == "personality":
            return f"""इस हथेली की छवि का विश्लेषण विशेष रूप से व्यक्तित्व और स्वभाव पर केंद्रित करते हुए करें।

{tradition_instruction}

इनका परीक्षण करें:
- हाथ का आकार: पृथ्वी/वायु/अग्नि/जल प्रकार का वर्गीकरण और यह क्या प्रकट करता है
- उंगलियों के अनुपात और वे व्यक्तित्व लक्षणों के बारे में क्या संकेत देते हैं
- मस्तिष्क रेखा (Head Line): विचार शैली, रचनात्मक बनाम विश्लेषणात्मक स्वभाव
- हृदय रेखा (Heart Line): भावनात्मक अभिव्यक्ति की शैली
- अंगूठा: इच्छाशक्ति (पहला पोर) और तर्क (दूसरा पोर) यदि दिखाई दे रहा हो
- मुख्य पर्वत: कौन सा पर्वत सबसे प्रमुख है और इसके व्यक्तित्व प्रभाव

एक समृद्ध व्यक्तित्व प्रोफ़ाइल प्रदान करें — ताकत, चुनौतियाँ, संचार शैली और आंतरिक स्वभाव। इस हथेली में जो दिख रहा है, उसी का उल्लेख करें।"""
    else:
        tradition_instruction = f"Provide the reading from the perspective of {tradition} palmistry tradition(s)."
        
        if category == "complete":
            return f"""Analyze this palm image and provide a COMPLETE detailed palm reading.

{tradition_instruction}

Structure your response EXACTLY as follows:

## 🖐️ Palm Overview
Describe the overall hand shape (Earth/Air/Fire/Water), skin texture observations, and finger proportions visible in the image.

## ❤️ Heart Line Analysis
Analyze the heart line — its starting point, curve, depth, length, any breaks or forks, and what they reveal about emotional nature and relationships.

## 🧠 Head Line Analysis
Analyze the head line — its path, connection or separation from the life line, any branches, and what they indicate about thinking style and intellect.

## 🌿 Life Line Analysis
Analyze the life line — its arc, depth, any breaks or branches, and what they suggest about vitality, life energy, and major life transitions. Clarify that this is NOT about lifespan.

## ⚡ Fate Line Analysis
If visible, analyze the fate line — its starting point, strength, and what it reveals about career direction and sense of purpose.

## ☀️ Other Notable Lines & Markings
Identify any additional lines visible (Sun line, Mercury line, relationship lines, bracelets, stars, crosses, islands, or other special markings).

## 🏔️ Mount Analysis
Describe the prominence of any visible mounts (Jupiter, Saturn, Apollo, Mercury, Venus, Moon, Mars) and their significance.

## 🌟 Synthesis & Life Guidance
Tie all the observations together into a cohesive narrative about the person's character, strengths, life path, and areas for growth.

## 🔮 Key Takeaways
Provide 5 bullet-point insights — the most important things this palm reveals.

Be specific to what you see in THIS image. Reference actual visual features."""

        elif category == "love":
            return f"""Analyze this palm image focusing SPECIFICALLY on love, relationships, and emotional life.

{tradition_instruction}

Examine:
- Heart Line: depth, curve, starting/ending points, forks, branches, islands
- Venus Mount: prominence and what it reveals about passion and sensuality
- Relationship/Marriage Lines: any small horizontal lines on the edge below the little finger
- Girdle of Venus: if present, its significance
- Influence Lines: any lines joining the fate line from the Moon mount

Provide insights on their emotional nature, relationship patterns, romantic tendencies, and guidance for love life. Be specific to what you see in THIS palm."""

        elif category == "career":
            return f"""Analyze this palm image focusing SPECIFICALLY on career, purpose, and professional life.

{tradition_instruction}

Examine:
- Fate Line: strength, starting point, breaks, branches — career direction indicators
- Sun Line: presence and clarity — fame, success, and creative achievement
- Head Line: thinking style — practical vs creative career alignment
- Jupiter Mount & Finger: leadership ability, ambition
- Mercury Finger & Mount: communication and business acumen
- Any special markings related to career success (stars, squares, triangles on mounts)

Provide insights on career strengths, ideal work environments, leadership style, and professional guidance. Be specific to THIS palm."""

        elif category == "health":
            return f"""Analyze this palm image focusing SPECIFICALLY on health indicators and vitality.

{tradition_instruction}

Examine:
- Life Line: arc, depth, vitality indicators (NOT lifespan prediction)
- Health/Mercury Line: if present, its condition
- Overall color and texture observations visible in the image
- Nails (if visible): shape and condition as traditional health indicators
- Stress indicators: islands, chains, or disturbances on major lines
- Venus Mount: vitality and physical energy

IMPORTANT: Clearly state these are traditional palmistry observations for self-reflection, NOT medical advice. Always recommend consulting healthcare professionals for health concerns. Be specific to THIS palm."""

        elif category == "wealth":
            return f"""Analyze this palm image focusing SPECIFICALLY on wealth, fortune, and financial tendencies.

{tradition_instruction}

Examine:
- Fate Line: stability and career-driven income indicators
- Sun Line: success, recognition, and prosperity markers
- Mercury Line: business acumen and financial intelligence
- Money Triangle: if formed by Head, Fate, and Mercury lines — its completeness
- Jupiter Mount: ambition and growth potential
- Any special wealth markings (triangles, tridents, stars on relevant mounts)

Provide insights on financial tendencies, wealth-building strengths, and practical guidance. Be specific to THIS palm."""

        elif category == "personality":
            return f"""Analyze this palm image focusing SPECIFICALLY on personality and temperament.

{tradition_instruction}

Examine:
- Hand Shape: Earth/Air/Fire/Water type classification and what it reveals
- Finger proportions and what they indicate about personality traits
- Head Line: thinking style, creativity vs analytical nature
- Heart Line: emotional expression style
- Thumb: willpower (first phalanx) and logic (second phalanx) if visible
- Dominant Mount: which mount is most prominent and its personality implications

Provide a rich personality profile — strengths, challenges, communication style, and inner nature. Be specific to THIS palm."""
    return ""

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────

def get_custom_css() -> str:
    """Load background image, base64 encode it, and return custom CSS."""
    bg_image_path = "docs/cosmic_palm_bg.png"
    if os.path.exists(bg_image_path):
        import base64
        try:
            with open(bg_image_path, "rb") as f:
                bg_base64 = base64.b64encode(f.read()).decode("utf-8")
            bg_rule = f"background: radial-gradient(circle at 50% 10%, rgba(28, 10, 53, 0.7) 0%, rgba(10, 10, 26, 0.95) 80%), url('data:image/png;base64,{bg_base64}'); background-size: cover; background-position: center; background-attachment: fixed; background-blend-mode: multiply;"
        except Exception as e:
            logger.error(f"Error loading background image base64: {str(e)}")
            bg_rule = "background: radial-gradient(circle at 50% 10%, #1c0a35 0%, #0a0a1a 70%); background-attachment: fixed;"
    else:
        bg_rule = "background: radial-gradient(circle at 50% 10%, #1c0a35 0%, #0a0a1a 70%); background-attachment: fixed;"

    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght=300;400;500;600;700;800&family=Playfair+Display:ital,wght=0,400..900;1,400..900&display=swap');

    /* Global typography */
    html, body, [class*="css"], .stApp {{
        font-family: 'Outfit', -apple-system, sans-serif !important;
    }}

    /* Ensure clear text readability on dark background */
    .stApp p, .stApp span, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3 {{
        color: #f0f0f5;
    }}

    /* Force black text for the browse files upload button and download reading button */
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploader"] button *,
    [data-testid="stDownloadButton"] button,
    [data-testid="stDownloadButton"] button * {{
        color: #121214 !important;
    }}

    /* Main background with cosmic nebula effect */
    .stApp {{
        {bg_rule}
    }}

    /* Custom Scrollbar for a premium feel */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: #0a0a1a;
    }}
    ::-webkit-scrollbar-thumb {{
        background: #4c1d95;
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #6d28d9;
    }}

    /* Header styling with pulsing glowing text */
    .main-header {{
        text-align: center;
        padding: 2.5rem 0 1.5rem;
    }}
    .main-header h1 {{
        font-family: 'Playfair Display', Georgia, serif !important;
        background: linear-gradient(135deg, #ffe082 0%, #ffb300 40%, #e040fb 70%, #00e5ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.8rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0.4rem;
        filter: drop-shadow(0 2px 8px rgba(255, 224, 130, 0.15));
        animation: titleGlow 4s ease-in-out infinite alternate;
    }}
    @keyframes titleGlow {{
        from {{
            filter: drop-shadow(0 2px 8px rgba(255, 224, 130, 0.15));
        }}
        to {{
            filter: drop-shadow(0 4px 20px rgba(224, 64, 251, 0.35));
        }}
    }}
    .main-header p {{
        color: #a78bfa;
        font-size: 1.15rem;
        font-style: italic;
        font-weight: 300;
        letter-spacing: 0.5px;
    }}

    /* Premium Glassmorphism Cards */
    .glass-card {{
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.8rem;
        margin: 1rem 0;
        backdrop-filter: blur(16px) saturate(180%);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .glass-card:hover {{
        transform: translateY(-4px);
        background: rgba(255, 255, 255, 0.04);
        border-color: rgba(167, 139, 250, 0.25);
        box-shadow: 0 12px 40px 0 rgba(124, 58, 237, 0.18);
    }}
    .glass-card h3 {{
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 1.4rem;
        color: #ffb300;
        margin-bottom: 0.6rem;
    }}

    /* File upload design */
    .upload-section {{
        background: rgba(124, 58, 237, 0.03);
        border: 2px dashed rgba(167, 139, 250, 0.2);
        border-radius: 20px;
        padding: 2.5rem 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: inset 0 0 20px rgba(124, 58, 237, 0.05);
    }}
    .upload-section:hover {{
        border-color: rgba(167, 139, 250, 0.5);
        background: rgba(124, 58, 237, 0.06);
        box-shadow: inset 0 0 25px rgba(124, 58, 237, 0.08);
    }}

    /* Reading result container */
    .reading-container {{
        background: rgba(10, 10, 26, 0.5);
        border: 1px solid rgba(167, 139, 250, 0.2);
        border-radius: 24px;
        padding: 2.5rem;
        margin-top: 2rem;
        line-height: 1.85;
        backdrop-filter: blur(20px);
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.5), inset 0 0 15px rgba(167, 139, 250, 0.05);
    }}
    .reading-container h2 {{
        font-family: 'Playfair Display', Georgia, serif !important;
        color: #c4b5fd;
        font-size: 2rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(167, 139, 250, 0.15);
    }}
    .reading-container h3 {{
        font-family: 'Playfair Display', Georgia, serif !important;
        color: #ffb300;
        font-size: 1.45rem;
        margin-top: 1.5rem;
    }}

    /* Sidebar customize */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #090915 0%, #150926 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.04);
    }}
    section[data-testid="stSidebar"] h2 {{
        font-family: 'Playfair Display', Georgia, serif !important;
        color: #ffd54f !important;
        font-size: 1.5rem;
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {{
        color: #c4b5fd !important;
        font-weight: 500;
    }}

    /* Interactive Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, #6d28d9 0%, #a855f7 50%, #4c1d95 100%);
        background-size: 200% auto;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        width: 100%;
        box-shadow: 0 4px 15px rgba(109, 40, 217, 0.2);
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        background-position: right center;
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.4);
    }}

    /* Modern Chat Bubble styling with hover effects */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(167, 139, 250, 0.1) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        margin-bottom: 1rem !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
    }}
    .stChatMessage:hover {{
        border-color: rgba(167, 139, 250, 0.3) !important;
        box-shadow: 0 8px 32px 0 rgba(167, 139, 250, 0.1) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }}
    
    /* Modern Chat Input box styling */
    .stChatInput {{
        padding-bottom: 1.5rem !important;
    }}
    .stChatInput textarea {{
        color: #f0f0f5 !important;
        font-family: 'Outfit', sans-serif !important;
    }}
    .stChatInput > div {{
        border: 1px solid rgba(167, 139, 250, 0.2) !important;
        border-radius: 20px !important;
        background: rgba(21, 9, 38, 0.6) !important;
        backdrop-filter: blur(16px) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s ease !important;
    }}
    .stChatInput > div:focus-within {{
        border-color: rgba(255, 179, 0, 0.6) !important;
        box-shadow: 0 0 15px rgba(255, 179, 0, 0.25) !important;
    }}

    /* Spinner color */
    .stSpinner > div {{
        border-color: #a855f7 !important;
    }}

    /* Celestial Divider */
    .mystic-divider {{
        text-align: center;
        margin: 2rem 0;
        color: #ffb300;
        font-size: 1.3rem;
        letter-spacing: 12px;
        opacity: 0.85;
    }}

    /* Image display styling */
    .palm-image-container {{
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid rgba(167, 139, 250, 0.15);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }}

    /* Hide default elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Expander styling */
    .streamlit-expanderHeader {{
        color: #c4b5fd !important;
        font-weight: 600;
        background: transparent !important;
    }}
    .streamlit-expanderContent {{
        background: rgba(255, 255, 255, 0.01) !important;
        border-radius: 0 0 12px 12px;
    }}
</style>
"""

# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────


@st.cache_resource
def _create_cached_client(api_key: str) -> genai.Client:
    """Create a cached GenAI client instance."""
    logger.info("Initializing a new cached GenAI client instance.")
    return genai.Client(api_key=api_key)


def get_gemini_client() -> Optional[genai.Client]:
    """Initialize and return the Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY", "") or st.session_state.get("api_key", "")
    if not api_key:
        return None
    return _create_cached_client(api_key.strip())


def analyze_palm_stream(client: genai.Client, image: Image.Image, category: str, tradition: str, lang: str):
    """Send palm image to Gemini for streaming analysis."""
    logger.info(f"Starting palm analysis (category={category}, tradition={tradition}, lang={lang})")
    prompt = build_reading_prompt(category, tradition, lang)

    # Upload image to GenAI File API for reliable model access
    _buf = io.BytesIO()
    image.save(_buf, format="PNG")
    _buf.seek(0)
    uploaded_file = client.files.upload(file=_buf)

    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=[prompt, uploaded_file],
            config=genai.types.GenerateContentConfig(
                system_instruction=get_system_prompt(lang),
                temperature=0.8,
                max_output_tokens=4096,
            ),
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
        # Clean up uploaded file after streaming completes
        client.files.delete(name=uploaded_file.name)
    except Exception as e:
        logger.error(f"Error during palm analysis: {str(e)}", exc_info=True)
        if lang == "hi":
            yield f"\n\n❌ **त्रुटि**: विश्लेषण करने में विफल। ({str(e)})"
        else:
            yield f"\n\n❌ **Error**: Failed to analyze palm. ({str(e)})"


def chat_followup_stream(client: genai.Client, image: Image.Image, reading: str, history: list, question: str, lang: str):
    """Handle follow-up questions about the reading using streaming and native chat history format."""
    logger.info(f"Starting chat follow-up (history_len={len(history)}, lang={lang})")

    # Upload image to GenAI File API for reliable model access
    _buf = io.BytesIO()
    image.save(_buf, format="PNG")
    _buf.seek(0)
    _uploaded = client.files.upload(file=_buf)

    # 1. Initial reading context: flat list — SDK auto-wraps text+image in Content(role="user")
    contents = [f"Initial Palm Reading Context:\n\n{reading}", _uploaded]

    # 2. Add validation acknowledgement by the model to lock the turn
    contents.append(genai.types.Content(
        role="model",
        parts=[
            genai.types.Part.from_text(text="Understood. I have analyzed the palm image and will reference the reading context for your follow-up questions.")
        ]
    ))

    # 3. Add the rest of the chat history turns, filtering out empty contents
    for msg in history[:-1]:
        if msg.get("content") and msg["content"].strip():
            role = "user" if msg["role"] == "user" else "model"
            contents.append(genai.types.Content(
                role=role,
                parts=[genai.types.Part.from_text(text=msg["content"].strip())]
            ))

    # 4. Add the current user question
    if question and question.strip():
        contents.append(genai.types.Content(
            role="user",
            parts=[genai.types.Part.from_text(text=question.strip())]
        ))

    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=get_followup_system_prompt(lang),
                temperature=0.8,
                max_output_tokens=2048,
            ),
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
        # Clean up after streaming completes
        client.files.delete(name=_uploaded.name)
    except Exception as e:
        logger.error(f"Error during chat follow-up: {str(e)}", exc_info=True)
        if lang == "hi":
            yield f"\n\n❌ **त्रुटि**: प्रतिक्रिया उत्पन्न करने में विफल। ({str(e)})"
        else:
            yield f"\n\n❌ **Error**: Failed to generate response. ({str(e)})"
        try:
            client.files.delete(name=_uploaded.name)
        except Exception:
            pass


# ─────────────────────────────────────────────
# Hand Crop — MediaPipe + OpenCV
# ─────────────────────────────────────────────

def _center_crop_fallback(image: Image.Image) -> Image.Image:
    """Pure-PIL center crop onto dark background.  No OpenCV required."""
    w, h = image.size
    if w < 64 or h < 64:
        return image
    side = min(w, h)
    crop_size = int(side * 0.72)
    x1 = (w - crop_size) // 2
    y1 = (h - crop_size) // 2
    x2 = x1 + crop_size
    y2 = y1 + crop_size
    fallback = image.crop((x1, y1, x2, y2))
    # Composite onto dark background for consistent theme blending
    bg = Image.new("RGB", fallback.size, (10, 10, 26))
    return Image.blend(fallback, bg, 0.15)


def _detect_hand_bbox(img_array):
    """Detect hand bounding box — tries YCrCb skin detection first
    (zero native deps), then MediaPipe if available.
    Returns (x1,y1,x2,y2) pixel coords or None."""
    h, w = img_array.shape[:2]

    # ── Approach 1: YCrCb skin colour segmentation ──────────────────
    # Works on every platform, no native libraries, no model downloads.
    try:
        import numpy as np
        R = img_array[:, :, 0].astype(np.float32)
        G = img_array[:, :, 1].astype(np.float32)
        B = img_array[:, :, 2].astype(np.float32)

        # RGB → YCrCb  (ITU-R BT.601, the standard for skin detection)
        Y  = 0.299 * R + 0.587 * G + 0.114 * B
        Cr = (R - Y) * 0.713 + 128
        Cb = (B - Y) * 0.564 + 128

        # Classic skin range in YCrCb
        skin = (Cr >= 133) & (Cr <= 173) & (Cb >= 77) & (Cb <= 127)

        ys, xs = np.where(skin)
        if len(ys) >= 200:  # enough skin pixels → hand found
            pad = int(min(w, h) * 0.06)
            x1 = max(0, int(xs.min()) - pad)
            y1 = max(0, int(ys.min()) - pad)
            x2 = min(w, int(xs.max()) + pad)
            y2 = min(h, int(ys.max()) + pad)
            # If box is very tall (arm included), take the top palm portion
            box_h, box_w = y2 - y1, x2 - x1
            if box_h > box_w * 1.6:
                y2 = y1 + int(box_w * 1.4)
            logger.info("Hand detected via YCrCb skin (%d×%d)", x2 - x1, y2 - y1)
            return (x1, y1, x2, y2)
    except Exception as e:
        logger.debug("YCrCb skin detection failed: %s", e)

    # ── Approach 2: MediaPipe landmark detection ─────────────────────
    try:
        import mediapipe as mp
        if hasattr(mp, "solutions"):
            _hands = mp.solutions.hands.Hands(
                static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5,
            )
            _res = _hands.process(img_array[:, :, ::-1].copy())
            _hands.close()
            if _res.multi_hand_landmarks:
                _pts = [(int(lm.x * w), int(lm.y * h)) for lm in _res.multi_hand_landmarks[0].landmark]
                _pad = int(min(w, h) * 0.08)
                _xs = [p[0] for p in _pts]
                _ys = [p[1] for p in _pts]
                logger.info("Hand detected via mp.solutions")
                return (
                    max(0, min(_xs) - _pad),
                    max(0, min(_ys) - _pad),
                    min(w, max(_xs) + _pad),
                    min(h, max(_ys) + _pad),
                )
    except Exception as e:
        logger.debug("MediaPipe approach failed: %s", e)

    # ── Approach 3: mp.tasks.vision (0.10.21+) ───────────────────────
    try:
        from mediapipe.tasks import python as _mp_t
        from mediapipe.tasks.python import vision as _mp_v
        import mediapipe as _mp2
        import os as _os, urllib.request as _ul

        _mpath = "/tmp/hand_landmarker.task"
        if not _os.path.exists(_mpath):
            _ul.urlretrieve(
                "https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/"
                "hand_landmarker.task",
                _mpath,
            )
        _det = _mp_v.HandLandmarker.create_from_options(
            _mp_v.HandLandmarkerOptions(
                base_options=_mp_t.BaseOptions(model_asset_path=_mpath),
                running_mode=_mp_v.RunningMode.IMAGE,
                num_hands=1,
                min_hand_detection_confidence=0.5,
            )
        )
        _r = _det.detect(_mp2.Image(image_format=_mp2.ImageFormat.SRGB, data=img_array))
        _det.close()
        if _r.hand_landmarks:
            _pts2 = [(int(lm.x * w), int(lm.y * h)) for lm in _r.hand_landmarks[0]]
            _pad2 = int(min(w, h) * 0.08)
            _xs2 = [p[0] for p in _pts2]
            _ys2 = [p[1] for p in _pts2]
            logger.info("Hand detected via mp.tasks")
            return (
                max(0, min(_xs2) - _pad2),
                max(0, min(_ys2) - _pad2),
                min(w, max(_xs2) + _pad2),
                min(h, max(_ys2) + _pad2),
            )
    except Exception as e:
        logger.debug("mp.tasks approach failed: %s", e)

    return None


def crop_hand_image(image: Image.Image) -> Image.Image:
    """Detect hand using CV preprocessing, crop tightly, and composite
    onto dark background.  Falls back to center-crop."""
    import numpy as np

    if image.mode != "RGB":
        img = image.convert("RGB")
    else:
        img = image.copy()
    img_array = np.array(img)
    h, w = img_array.shape[:2]
    if w < 64 or h < 64:
        return image

    bbox = _detect_hand_bbox(img_array)
    if bbox is None:
        return _center_crop_fallback(image)

    x1, y1, x2, y2 = bbox

    # ── Create rough mask for background removal ─────────────────────
    # Use skin-colour mask within the bounding box
    R = img_array[:, :, 0].astype(np.float32)
    G = img_array[:, :, 1].astype(np.float32)
    B = img_array[:, :, 2].astype(np.float32)
    Y  = 0.299 * R + 0.587 * G + 0.114 * B
    Cr = (R - Y) * 0.713 + 128
    Cb = (B - Y) * 0.564 + 128
    skin = (Cr >= 133) & (Cr <= 173) & (Cb >= 77) & (Cb <= 127)

    mask = Image.new("L", (w, h), 0)
    mask_np = np.array(mask, dtype=np.uint8)
    mask_np[skin] = 255
    # Fill holes and smooth
    mask = Image.fromarray(mask_np).filter(ImageFilter.GaussianBlur(radius=9))

    # ── Composite onto dark background ───────────────────────────────
    mask_f = np.array(mask, dtype=np.float32) / 255.0
    mask_3ch = np.stack([mask_f, mask_f, mask_f], axis=-1)
    dark_bg = np.full_like(img_array, (10, 10, 26), dtype=np.uint8)
    blended = (img_array * mask_3ch + dark_bg * (1 - mask_3ch)).astype(np.uint8)
    cropped = blended[y1:y2, x1:x2]

    logger.info("Hand crop (%d×%d → %d×%d)", w, h, x2 - x1, y2 - y1)
    return Image.fromarray(cropped)


# ─────────────────────────────────────────────
# Palm Line Detection — Gemini
# ─────────────────────────────────────────────

def detect_palm_lines(client: genai.Client, image: Image.Image, t: dict) -> dict:
    """Ask Gemini to detect heart, head, and life lines and return coordinates.

    Returns a dict keyed by line id with arrays of [x,y] normalized control
    points (0-1).  Also estimates fate/sun/mercury from the detected lines.
    Returns empty dict on failure (caller falls back to defaults).
    """
    import numpy as np

    prompt = (
        "You are a palmistry expert. Analyze this palm image and detect "
        "the three major palm lines — Heart Line, Head Line, Life Line.\n\n"
        "For each line, return 4 to 5 control points as [x, y] coordinates "
        "normalized to 0–1 range (top-left = [0,0], bottom-right = [1,1]).\n"
        "Trace the actual visible curve of each line on THIS specific hand.\n\n"
        "Line descriptions:\n"
        "- Heart Line: starts below the index finger, arcs across the upper palm\n"
        "- Head Line: starts near the thumb base, runs across the mid-palm\n"
        "- Life Line: curves around the thumb mound, runs toward the wrist\n\n"
        "Return ONLY valid JSON with no markdown fences or extra text:\n"
        '{"heart":[[x1,y1],[x2,y2],[x3,y3],[x4,y4],[x5,y5]],'
        '"head":[[x1,y1],[x2,y2],[x3,y3],[x4,y4],[x5,y5]],'
        '"life":[[x1,y1],[x2,y2],[x3,y3],[x4,y4],[x5,y5]]}'
    )

    try:
        _buf = io.BytesIO()
        image.save(_buf, format="PNG")
        _buf.seek(0)
        uploaded_file = client.files.upload(file=_buf)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, uploaded_file],
            config=genai.types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
        client.files.delete(name=uploaded_file.name)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        lines = json.loads(text)
    except Exception as e:
        logger.warning("Gemini line detection failed: %s", e)
        return {}

    # Validate — each must have 4+ points
    for key in ("heart", "head", "life"):
        pts = lines.get(key)
        if not isinstance(pts, list) or len(pts) < 4:
            logger.warning("Gemini returned invalid %s line", key)
            return {}
        lines[key] = [[float(x), float(y)] for x, y in pts]

    # ── Estimate fate, sun, mercury from detected heart/head/life ──
    heart = np.array(lines["heart"])
    head = np.array(lines["head"])
    life = np.array(lines["life"])

    # Fate: vertical through palm center, from wrist (life bottom) to middle-finger base (heart top-center)
    life_bottom_y = float(np.max(life[:, 1]))
    heart_center_x = float(np.mean(heart[:, 0]))
    heart_top_y = float(np.min(heart[:, 1]))
    lines["fate"] = [
        [heart_center_x, life_bottom_y],
        [heart_center_x, life_bottom_y - 0.14],
        [heart_center_x, life_bottom_y - 0.28],
        [heart_center_x, heart_top_y + 0.06],
        [heart_center_x, heart_top_y],
    ]

    # Sun: parallel to fate, shifted toward ring finger
    sun_x = min(1.0, heart_center_x + 0.16)
    lines["sun"] = [
        [sun_x, life_bottom_y],
        [sun_x, life_bottom_y - 0.14],
        [sun_x, life_bottom_y - 0.28],
        [sun_x, heart_top_y + 0.06],
        [sun_x, heart_top_y],
    ]

    # Mercury: further right toward pinky
    merc_x = min(1.0, heart_center_x + 0.30)
    lines["mercury"] = [
        [merc_x, life_bottom_y],
        [merc_x, life_bottom_y - 0.14],
        [merc_x, life_bottom_y - 0.28],
        [merc_x, heart_top_y + 0.06],
        [merc_x, heart_top_y],
    ]

    logger.info("Palm lines detected: heart=%d, head=%d, life=%d",
                len(lines["heart"]), len(lines["head"]), len(lines["life"]))
    return lines


# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "reading_result": None,
        "palm_image": None,
        "chat_history": [],
        "reading_done": False,
        "app_lang": "en",  # English by default
        "selected_category": None,
        "selected_tradition": None,
        "last_uploaded_file_id": None,
        "loading": False,
        "scan_done": False,  # tracks if scanning animation already ran
        "_clean_img_bytes": None,  # cached clean PNG bytes (no EXIF/metadata)
        "palm_lines": None,  # Gemini-detected palm line coordinates
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ─────────────────────────────────────────────
# UI Components
# ─────────────────────────────────────────────

def render_header(t):
    """Render the main app header."""
    st.markdown(
        f"""
        <div class="main-header">
            <h1>{t["app_title"]}</h1>
            <p>{t["app_subtitle"]}</p>
        </div>
        <div class="mystic-divider">✦ ✦ ✦</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(t):
    """Render the sidebar with settings and info."""
    with st.sidebar:
        st.markdown(f"## {t['settings']}")

        # Language Selector (English default)
        lang_options = {"English (English)": "en", "Hindi (हिन्दी)": "hi"}
        current_lang_idx = 0 if st.session_state.app_lang == "en" else 1
        selected_lang_name = st.selectbox(
            t["lang_label"],
            options=list(lang_options.keys()),
            index=current_lang_idx,
            key="lang_selector"
        )
        
        new_lang = lang_options[selected_lang_name]
        if new_lang != st.session_state.app_lang:
            st.session_state.app_lang = new_lang
            st.session_state.selected_category = None
            st.session_state.selected_tradition = None
            st.session_state.reading_result = None
            st.session_state.reading_done = False
            st.session_state.chat_history = []
            st.rerun()

        # API Key input (if not in env)
        if not os.getenv("GEMINI_API_KEY"):
            st.text_input(
                t["api_key_label"],
                type="password",
                key="api_key",
                help=t["api_key_help"],
            )
            st.markdown("---")

        category_map = READING_CATEGORIES_HI if st.session_state.app_lang == "hi" else READING_CATEGORIES_EN
        tradition_map = TRADITIONS_HI if st.session_state.app_lang == "hi" else TRADITIONS_EN

        # Reading category
        category_options = list(category_map.keys())
        cat_idx = 0
        if st.session_state.selected_category in category_options:
            cat_idx = category_options.index(st.session_state.selected_category)
            
        st.session_state.selected_category = st.selectbox(
            t["category_label"],
            options=category_options,
            index=cat_idx,
            help=t["category_help"],
        )

        # Tradition
        tradition_options = list(tradition_map.keys())
        trad_idx = 3  # All Traditions default
        if st.session_state.selected_tradition in tradition_options:
            trad_idx = tradition_options.index(st.session_state.selected_tradition)
            
        st.session_state.selected_tradition = st.radio(
            t["tradition_label"],
            options=tradition_options,
            index=trad_idx,
            help=t["tradition_help"],
        )

        st.markdown("---")

        # Info section
        st.markdown(f"## {t['how_it_works']}")
        st.markdown(t["how_it_works_steps"])

        st.markdown("---")

        # Tips
        with st.expander(t["tips_title"]):
            st.markdown(t["tips_content"])

        st.markdown("---")

        # Portfolio links
        st.markdown(f"## {t['portfolio_title']}")
        st.markdown(
            f"""
            <a href="https://github.com/manavshrivastavagit/palm-reader-app" target="_blank" style="text-decoration:none;">
                <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); border-radius:8px; padding:0.6rem; margin-bottom:0.5rem; text-align:center; transition: all 0.3s ease;">
                    <span style="color:#ffb300 !important; font-weight:600; font-size:0.9rem;">{t['github_label']}</span>
                </div>
            </a>
            <a href="https://www.linkedin.com/in/manav-shrivastava" target="_blank" style="text-decoration:none;">
                <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); border-radius:8px; padding:0.6rem; text-align:center; transition: all 0.3s ease;">
                    <span style="color:#a78bfa !important; font-weight:600; font-size:0.9rem;">{t['linkedin_label']}</span>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            f"""
            <div style="text-align:center; color:#6c6c8a; font-size:0.8rem;">
                <p>{t["disclaimer_poc"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_upload_section(t):
    """Render the image upload area."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            t["upload_label"],
            type=["jpg", "jpeg", "png", "webp"],
            help=t["upload_help"],
            label_visibility="collapsed",
        )
        st.markdown(t["upload_instruction"])
        st.markdown("</div>", unsafe_allow_html=True)

        camera_file = st.camera_input(
            t["camera_instruction"],
            help=t["camera_help"],
        )

    return uploaded_file or camera_file


def render_palm_display(image: Image.Image, t):
    """Display the uploaded palm image."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="palm-image-container">', unsafe_allow_html=True)
        # Convert to bytes before passing to st.image() to avoid
        # Streamlit PIL serialization issues with dirty metadata
        _buf = io.BytesIO()
        image.save(_buf, format="PNG")
        st.image(_buf.getvalue(), caption=t["your_palm"], width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)


def render_palm_scanning_animation(image: Image.Image, t, palm_lines=None):
    """Display a cinematic AI palm scanning animation over the uploaded palm image."""
    import base64
    buf = io.BytesIO()
    # Resize to a sensible canvas size before base64 encoding
    display_img = image.copy()
    display_img.thumbnail((640, 640))
    display_img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # Serialise Gemini-detected palm lines for the JS
    palm_lines_json = json.dumps(palm_lines or {})

    scan_heading  = t.get("scan_heading", "🔬 AI Vision Analysis — Scanning Palm...")
    scan_complete = t.get("scan_complete", "✅ Palm Scan Complete — Ready for Reading")

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui; display: flex; flex-direction: column;
      align-items: center; justify-content: start; min-height: 100vh; padding: 12px 0;
      background: #0a0a1a; }}
    #wrapper {{
      position: relative; width: 100%; max-width: 520px;
      border-radius: 18px; overflow: hidden;
      border: 2px solid rgba(167,139,250,0.4);
      box-shadow: 0 0 40px rgba(124,58,237,0.3), 0 0 80px rgba(124,58,237,0.1);
    }}
    #palmImg {{
      display: block; width: 100%; border-radius: 18px;
    }}
    #overlay {{
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      pointer-events: none; border-radius: 18px;
    }}
    #statusBar {{
      width: 100%; max-width: 520px; margin-top: 12px;
      display: flex; flex-direction: column; align-items: center; gap: 8px;
    }}
    #statusText {{
      color: #a78bfa; font-size: 0.82rem; letter-spacing: 1.2px;
      text-transform: uppercase; font-weight: 600;
      transition: color 0.6s;
    }}
    #progressTrack {{
      width: 100%; height: 4px;
      background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;
    }}
    #progressBar {{
      height: 100%; width: 0%;
      background: linear-gradient(90deg, #7c3aed, #a855f7, #fbbf24);
      border-radius: 4px;
      transition: width 0.12s ease-out;
      box-shadow: 0 0 12px rgba(168,85,247,0.6);
    }}
    #featureTags {{
      display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin-top: 4px;
    }}
    .ftag {{
      padding: 3px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700;
      letter-spacing: 0.5px; opacity: 0;
      transition: opacity 0.5s, transform 0.5s;
      transform: translateY(6px);
    }}
    .ftag.show {{ opacity: 1; transform: translateY(0); }}
  </style>
</head>
<body>
  <div id="wrapper">
    <img id="palmImg" src="data:image/png;base64,{img_b64}">
    <canvas id="overlay"></canvas>
  </div>
  <div id="statusBar">
    <span id="statusText">⏳ Initialising AI scanner...</span>
    <div id="progressTrack"><div id="progressBar"></div></div>
    <div id="featureTags"></div>
  </div>

  <script>
  (function() {{
    const canvas  = document.getElementById('overlay');
    const ctx     = canvas.getContext('2d');
    const img     = document.getElementById('palmImg');
    const status  = document.getElementById('statusText');
    const pBar    = document.getElementById('progressBar');
    const tagsDiv = document.getElementById('featureTags');

    // ── Default bezier control points (approximate palm proportions)
    const DEFAULT_PTS = {{
      heart: [[0.12,0.38],[0.26,0.28],[0.48,0.25],[0.70,0.29],[0.86,0.37]],
      head:  [[0.10,0.52],[0.28,0.50],[0.50,0.52],[0.70,0.56],[0.84,0.63]],
      life:  [[0.34,0.28],[0.26,0.44],[0.22,0.60],[0.24,0.76],[0.34,0.86]],
      fate:  [[0.50,0.88],[0.50,0.72],[0.50,0.56],[0.50,0.40],[0.50,0.28]],
      sun:   [[0.67,0.82],[0.66,0.68],[0.65,0.56],[0.65,0.44]],
      mercury: [[0.80,0.76],[0.78,0.64],[0.77,0.54],[0.77,0.44]],
    }};

    // ── Gemini-detected palm lines (empty object = use defaults)
    const USER_PTS = {palm_lines_json};

    const FEATURES = [
      {{
        id: 'heart', label: '\u2764\ufe0f Heart Line', color: '#f43f5e', glow: 'rgba(244,63,94,0.55)',
        pts: USER_PTS.heart || DEFAULT_PTS.heart,
      }},
      {{
        id: 'head', label: '\ud83e\udde0 Head Line', color: '#38bdf8', glow: 'rgba(56,189,248,0.55)',
        pts: USER_PTS.head || DEFAULT_PTS.head,
      }},
      {{
        id: 'life', label: '\ud83c\udf3f Life Line', color: '#4ade80', glow: 'rgba(74,222,128,0.55)',
        pts: USER_PTS.life || DEFAULT_PTS.life,
      }},
      {{
        id: 'fate', label: '\u26a1 Fate Line', color: '#fbbf24', glow: 'rgba(251,191,36,0.55)',
        pts: USER_PTS.fate || DEFAULT_PTS.fate,
      }},
      {{
        id: 'sun', label: '\u2600\ufe0f Sun Line', color: '#fb923c', glow: 'rgba(251,146,60,0.55)',
        pts: USER_PTS.sun || DEFAULT_PTS.sun,
      }},
      {{
        id: 'mercury', label: '\u2606 Mercury Line', color: '#e879f9', glow: 'rgba(232,121,249,0.55)',
        pts: USER_PTS.mercury || DEFAULT_PTS.mercury,
      }},
    ];

    const MOUNTS = [
      {{ label: '\u2648 Jupiter', x: 0.23, y: 0.24, color: '#a78bfa' }},
      {{ label: '\u2649 Saturn',  x: 0.38, y: 0.20, color: '#fbbf24' }},
      {{ label: '\u2650 Apollo',  x: 0.56, y: 0.21, color: '#f97316' }},
      {{ label: '\u2643 Mercury', x: 0.72, y: 0.24, color: '#e879f9' }},
      {{ label: '\u2640 Venus',   x: 0.25, y: 0.72, color: '#f43f5e' }},
      {{ label: '\u263d Moon',    x: 0.78, y: 0.72, color: '#38bdf8' }},
    ];

    // ── State
    let W, H;
    let scanY    = 0;
    let phase    = 0;   // 0=boot, 1=scan, 2=lines, 3=mounts, 4=done
    let lineProgress = [];
    let mountProgress = [];
    let particles = [];
    let startTime = 0;
    let progress  = 0;  // 0-100
    let pulseDone = false;
    let pulseAlpha = 0;
    // Continuous looping xerox-style scanner line
    let loopScanY = 0;
    const LOOP_SCAN_SPEED = 0.00015; // fraction of H per ms

    FEATURES.forEach(() => lineProgress.push(0));
    MOUNTS.forEach(() => mountProgress.push(0));

    // ── Helpers
    function lerp(a,b,t) {{ return a + (b-a)*t; }}
    function clamp(v,lo,hi) {{ return Math.max(lo,Math.min(hi,v)); }}
    function ease(t) {{ return t<0.5 ? 2*t*t : -1+(4-2*t)*t; }}

    function resize() {{
      W = canvas.width  = img.offsetWidth;
      H = canvas.height = img.offsetHeight;
    }}

    // ── Particles for boot phase
    function spawnParticles() {{
      particles = [];
      for (let i=0; i<38; i++) {{
        particles.push({{
          x: Math.random(), y: Math.random(),
          vx: (Math.random()-0.5)*0.0007,
          vy: (Math.random()-0.5)*0.0007,
          r: Math.random()*1.5+0.5,
          a: Math.random()*0.5+0.2,
          color: ['#a78bfa','#fbbf24','#38bdf8','#4ade80'][Math.floor(Math.random()*4)]
        }});
      }}
    }}

    function drawParticles(alpha) {{
      ctx.save();
      ctx.globalAlpha = alpha;
      particles.forEach(p => {{
        p.x += p.vx; p.y += p.vy;
        if (p.x<0) p.x=1; if (p.x>1) p.x=0;
        if (p.y<0) p.y=1; if (p.y>1) p.y=0;
        ctx.beginPath();
        ctx.arc(p.x*W, p.y*H, p.r, 0, Math.PI*2);
        ctx.fillStyle = p.color;
        ctx.fill();
      }});
      ctx.restore();
    }}

    // ── Draw scanning beam
    function drawScanBeam(y) {{
      const grad = ctx.createLinearGradient(0, y-40, 0, y+40);
      grad.addColorStop(0, 'rgba(124,58,237,0)');
      grad.addColorStop(0.5, 'rgba(167,139,250,0.55)');
      grad.addColorStop(1, 'rgba(124,58,237,0)');
      ctx.save();
      ctx.fillStyle = grad;
      ctx.fillRect(0, y-40, W, 80);

      // bright centre line
      ctx.beginPath();
      ctx.moveTo(0, y); ctx.lineTo(W, y);
      ctx.strokeStyle = 'rgba(200,180,255,0.95)';
      ctx.lineWidth = 1.5;
      ctx.shadowColor = '#a78bfa';
      ctx.shadowBlur = 18;
      ctx.stroke();
      ctx.restore();
    }}

    // ── Draw scan grid overlay
    function drawGrid(alpha) {{
      ctx.save();
      ctx.globalAlpha = alpha * 0.12;
      ctx.strokeStyle = '#a78bfa';
      ctx.lineWidth = 0.5;
      const step = 24;
      for (let x=0; x<W; x+=step) {{ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }}
      for (let y=0; y<H; y+=step) {{ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }}
      ctx.restore();
    }}

    // ── Draw a bezier chain with animated progress
    function drawLine(feature, prog) {{
      const pts = feature.pts;
      if (prog <= 0 || pts.length < 2) return;
      const totalSegs = pts.length - 1;
      const drawn = prog * totalSegs;

      ctx.save();
      ctx.strokeStyle = feature.color;
      ctx.lineWidth = 3;
      ctx.shadowColor = feature.glow;
      ctx.shadowBlur = 16;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();
      ctx.moveTo(pts[0][0]*W, pts[0][1]*H);

      for (let i=0; i<totalSegs; i++) {{
        const frac = clamp(drawn - i, 0, 1);
        if (frac <= 0) break;
        const ax = pts[i][0]*W,   ay = pts[i][1]*H;
        const bx = pts[i+1][0]*W, by = pts[i+1][1]*H;
        const cpx = lerp(ax,bx,0.5), cpy = lerp(ay,by,0.5);
        ctx.bezierCurveTo(cpx, ay, cpx, by, lerp(ax,bx,frac), lerp(ay,by,frac));
      }}
      ctx.stroke();

      // Leading dot glow
      const segIdx = Math.min(Math.floor(drawn), totalSegs-1);
      const segFrac = drawn - Math.floor(drawn);
      const lx = lerp(pts[segIdx][0], pts[segIdx+1]?pts[segIdx+1][0]:pts[segIdx][0], segFrac) * W;
      const ly = lerp(pts[segIdx][1], pts[segIdx+1]?pts[segIdx+1][1]:pts[segIdx][1], segFrac) * H;
      ctx.beginPath();
      ctx.arc(lx, ly, 6, 0, Math.PI*2);
      ctx.fillStyle = feature.color;
      ctx.shadowBlur = 28;
      ctx.fill();
      ctx.restore();
    }}

    // ── Draw mount label pip
    function drawMount(mount, alpha) {{
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(mount.x*W, mount.y*H, 6, 0, Math.PI*2);
      ctx.fillStyle = mount.color;
      ctx.shadowColor = mount.color;
      ctx.shadowBlur = 18;
      ctx.fill();

      ctx.font = '9px Segoe UI';
      ctx.fillStyle = '#ffffff';
      ctx.shadowBlur = 0;
      ctx.fillText(mount.label, mount.x*W + 8, mount.y*H + 3);
      ctx.restore();
    }}

    // ── Draw final done pulse
    function drawDonePulse(alpha) {{
      const cx = W/2, cy = H/2;
      [80, 130, 180].forEach((r,i) => {{
        const a = Math.max(0, alpha - i*0.15);
        ctx.save();
        ctx.globalAlpha = a;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI*2);
        ctx.strokeStyle = '#a78bfa';
        ctx.lineWidth = 1.2;
        ctx.shadowColor = '#7c3aed';
        ctx.shadowBlur = 20;
        ctx.stroke();
        ctx.restore();
      }});
    }}

    // ── Add feature tag to bar
    const tagMap = {{}};
    function showTag(id, label, color) {{
      if (tagMap[id]) return;
      const el = document.createElement('span');
      el.className = 'ftag';
      el.textContent = label;
      el.style.background = color + '22';
      el.style.border = '1px solid ' + color + '66';
      el.style.color = color;
      tagsDiv.appendChild(el);
      tagMap[id] = el;
      requestAnimationFrame(() => el.classList.add('show'));
    }}

    // ── Main animation loop
    let lastTs = 0;
    const SCAN_DURATION   = 2200;  // ms full sweep
    const LINE_DURATION   = 280;   // ms per line
    const MOUNT_DURATION  = 120;   // ms per mount
    const PULSE_DURATION  = 1000;  // ms done pulse

    let lineStartTimes = [];
    let mountStartTimes = [];
    let linePhaseStart = 0;
    let mountPhaseStart = 0;
    let doneStart = 0;

    // ── Continuous xerox scanner line (drawn each frame regardless of phase)
    function drawLoopScanLine(y) {{
      const grad = ctx.createLinearGradient(0, y-20, 0, y+20);
      grad.addColorStop(0, 'rgba(124,58,237,0)');
      grad.addColorStop(0.5, 'rgba(200,180,255,0.18)');
      grad.addColorStop(1, 'rgba(124,58,237,0)');
      ctx.save();
      ctx.fillStyle = grad;
      ctx.fillRect(0, y-20, W, 40);
      ctx.beginPath();
      ctx.moveTo(0, y); ctx.lineTo(W, y);
      ctx.strokeStyle = 'rgba(200,180,255,0.30)';
      ctx.lineWidth = 1;
      ctx.shadowColor = '#a78bfa';
      ctx.shadowBlur = 6;
      ctx.stroke();
      ctx.restore();
    }}

    function tick(ts) {{
      if (!startTime) {{ startTime = ts; spawnParticles(); }}
      const elapsed = ts - startTime;

      // Update continuous looping scanner line (top→bottom loop)
      loopScanY += LOOP_SCAN_SPEED * (ts - (lastTs||ts));
      if (loopScanY > 1) loopScanY -= 1;
      lastTs = ts;

      resize();
      ctx.clearRect(0, 0, W, H);

      // ── Phase 0: SCAN SWEEP
      if (phase === 0) {{
        status.textContent = '🔍 Scanning biometric palm data...';
        const t = clamp(elapsed / SCAN_DURATION, 0, 1);
        scanY = ease(t) * H;
        progress = Math.round(t * 35);
        pBar.style.width = progress + '%';
        drawGrid(t);
        drawParticles(0.6);
        // draw faint hex corners
        ctx.save();
        ctx.strokeStyle = 'rgba(167,139,250,0.25)';
        ctx.lineWidth = 1;
        [[0.05,0.05],[0.95,0.05],[0.05,0.95],[0.95,0.95]].forEach(([rx,ry]) => {{
          const cx=rx*W, cy=ry*H, s=18;
          ctx.beginPath(); ctx.moveTo(cx,cy+s); ctx.lineTo(cx,cy);
          ctx.lineTo(cx+s*(rx>0.5?-1:1), cy); ctx.stroke();
        }});
        ctx.restore();
        drawScanBeam(scanY);
        if (t >= 1) {{
          phase = 1;
          linePhaseStart = ts;
          FEATURES.forEach((_,i) => lineStartTimes[i] = ts + i * (LINE_DURATION * 1.1));
        }}
      }}

      // ── Phase 1: LINE DETECTION
      if (phase === 1) {{
        status.textContent = '🧬 Detecting palm lines...';
        let allDone = true;
        FEATURES.forEach((f, i) => {{
          const lt = lineStartTimes[i];
          if (!lt) return;
          const lp = clamp((ts - lt) / LINE_DURATION, 0, 1);
          lineProgress[i] = ease(lp);
          drawLine(f, lineProgress[i]);
          if (lp >= 0.5) showTag(f.id, f.label, f.color);
          if (lp < 1) allDone = false;
        }});
        progress = 35 + Math.round((ts - linePhaseStart) / (LINE_DURATION * FEATURES.length * 1.1) * 35);
        pBar.style.width = Math.min(progress, 70) + '%';
        drawGrid(0.5);
        if (allDone) {{
          phase = 2;
          mountPhaseStart = ts;
          MOUNTS.forEach((_,i) => mountStartTimes[i] = ts + i * MOUNT_DURATION);
        }}
      }}

      // ── Phase 2: MOUNT LABELS
      if (phase === 2) {{
        status.textContent = '🏛️ Identifying palm mounts...';
        let allDone = true;
        FEATURES.forEach((f,i) => drawLine(f, lineProgress[i]));
        MOUNTS.forEach((m,i) => {{
          const mt = mountStartTimes[i];
          const mp = clamp((ts - mt) / MOUNT_DURATION, 0, 1);
          mountProgress[i] = ease(mp);
          drawMount(m, mountProgress[i]);
          if (mp < 1) allDone = false;
        }});
        progress = 70 + Math.round((ts - mountPhaseStart) / (MOUNT_DURATION * MOUNTS.length) * 22);
        pBar.style.width = Math.min(progress, 92) + '%';
        if (allDone) {{ phase = 3; doneStart = ts; }}
      }}

      // ── Phase 3: DONE PULSE
      if (phase === 3) {{
        FEATURES.forEach((f,i) => drawLine(f, lineProgress[i]));
        MOUNTS.forEach((m,i) => drawMount(m, mountProgress[i]));
        const tp = clamp((ts - doneStart) / PULSE_DURATION, 0, 1);
        pulseAlpha = Math.sin(tp * Math.PI);
        drawDonePulse(pulseAlpha);
        progress = 92 + Math.round(tp * 8);
        pBar.style.width = Math.min(progress, 100) + '%';
        status.textContent = '\u2728 Composing reading...';
        if (tp >= 1) {{
          phase = 4;
          pBar.style.width = '100%';
          pBar.style.background = 'linear-gradient(90deg,#4ade80,#22d3ee,#a855f7)';
          status.textContent = '{scan_complete}';
          status.style.color = '#4ade80';
        }}
      }}

      if (phase === 4) {{
        // Static final state — all lines + mounts
        FEATURES.forEach((f,i) => drawLine(f, lineProgress[i]));
        MOUNTS.forEach((m,i) => drawMount(m, 0.85));
        // subtle outer glow border pulse
        const pulse = 0.5 + 0.5*Math.sin(ts/600);
        ctx.save();
        ctx.strokeStyle = `rgba(74,222,128,${{pulse*0.6}})`;
        ctx.lineWidth = 3;
        ctx.strokeRect(1.5,1.5,W-3,H-3);
        ctx.restore();
      }}

      // Continuous xerox scanner line overlay (always visible, all phases)
      drawLoopScanLine(loopScanY * H);

      if (phase < 4) requestAnimationFrame(tick);
      else requestAnimationFrame(tick); // keep alive for border pulse
    }}

    img.onload = () => requestAnimationFrame(tick);
    if (img.complete) requestAnimationFrame(tick);
  }})();
  </script>
</body>
</html>
"""
    st.markdown(
        f'<p style="text-align:center;color:#a78bfa;font-weight:600;font-size:0.88rem;'
        f'letter-spacing:1px;text-transform:uppercase;margin:8px 0 2px;">{scan_heading}</p>',
        unsafe_allow_html=True
    )
    import base64 as _b64
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Sanitise against surrogates that crash protobuf serialization
        safe = html.encode("utf-8", errors="replace").decode("utf-8")
        _encoded = _b64.b64encode(safe.encode("utf-8")).decode("utf-8")
        st.iframe(f"data:text/html;base64,{_encoded}", height=500)


def render_reading_result(reading: str):
    """Display the palm reading result."""
    st.markdown('<div class="reading-container">', unsafe_allow_html=True)
    st.markdown(reading)
    st.markdown("</div>", unsafe_allow_html=True)


def render_chat_section(client: genai.Client, image: Image.Image, reading: str, t):
    """Render the follow-up chat section."""
    st.markdown('<div class="mystic-divider">✦ ✦ ✦</div>', unsafe_allow_html=True)
    st.markdown(f"### {t['chat_title']}")
    st.caption(t["chat_caption"])

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🔮"):
            st.markdown(msg["content"])

    # Chat input
    if question := st.chat_input(t["chat_input_placeholder"]):
        # Show user message
        with st.chat_message("user", avatar="🧑"):
            st.markdown(question)
        st.session_state.chat_history.append({"role": "user", "content": question})

        # Get AI response with loader
        with st.chat_message("assistant", avatar="🔮"):
            with st.spinner(t["chat_spinner"]):
                stream = chat_followup_stream(client, image, reading, st.session_state.chat_history, question, st.session_state.app_lang)
                response = st.write_stream(stream)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()


def render_live_scanner(t):
    """Render the live webcam palm/hand scanner using MediaPipe JS running in-browser."""
    st.markdown(f"### {t['live_title']}")
    st.caption(t["live_caption"])
    st.info(t["live_tip"])
    st.markdown(t["live_snapshot_hint"])

    # Self-contained MediaPipe Hand Landmarker component running entirely client-side.
    # Uses MediaPipe JS v0.10 tasks-vision for zero-latency, GPU-accelerated inference.
    html_code = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: transparent;
      display: flex;
      flex-direction: column;
      align-items: center;
      font-family: 'Segoe UI', sans-serif;
      padding: 8px;
    }
    #container {
      position: relative;
      width: 100%;
      max-width: 680px;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 0 30px rgba(167,139,250,0.25);
      border: 2px solid rgba(167,139,250,0.35);
    }
    #webcam, #canvas {
      width: 100%;
      display: block;
      border-radius: 16px;
    }
    #canvas {
      position: absolute;
      top: 0;
      left: 0;
      pointer-events: none;
    }
    #status {
      margin-top: 10px;
      color: #a78bfa;
      font-size: 0.85rem;
      letter-spacing: 0.5px;
      text-align: center;
    }
    #badge {
      display: none;
      margin-top: 8px;
      padding: 6px 18px;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-align: center;
    }
    .badge-detected {
      background: rgba(74,222,128,0.15);
      border: 1px solid rgba(74,222,128,0.45);
      color: #4ade80;
    }
    .badge-none {
      background: rgba(248,113,113,0.12);
      border: 1px solid rgba(248,113,113,0.35);
      color: #f87171;
    }
  </style>
</head>
<body>
  <div id="container">
    <video id="webcam" autoplay playsinline muted></video>
    <canvas id="canvas"></canvas>
  </div>
  <p id="status">⏳ Loading MediaPipe Hand Landmarker...</p>
  <div id="badge"></div>

  <!-- MediaPipe JS CDN -->
  <script type="module">
    import { HandLandmarker, FilesetResolver } from
      'https://unpkg.com/@mediapipe/tasks-vision@0.10.3/vision_bundle.mjs';

    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const status = document.getElementById('status');
    const badge = document.getElementById('badge');

    // ── MediaPipe hand connections ──────────────────────────────────────
    const CONNECTIONS = [
      [0,1],[1,2],[2,3],[3,4],         // thumb
      [0,5],[5,6],[6,7],[7,8],         // index
      [0,9],[9,10],[10,11],[11,12],    // middle
      [0,13],[13,14],[14,15],[15,16],  // ring
      [0,17],[17,18],[18,19],[19,20],  // pinky
      [5,9],[9,13],[13,17]             // palm arch
    ];

    // ── Cosmic color palette ────────────────────────────────────────────
    const JOINT_COLORS = [
      '#ffd54f', // wrist
      '#e040fb','#ce93d8','#ba68c8','#9c27b0',  // thumb
      '#64b5f6','#42a5f5','#2196f3','#1565c0',  // index
      '#81c784','#66bb6a','#4caf50','#2e7d32',  // middle
      '#ffb74d','#ffa726','#ff9800','#e65100',  // ring
      '#ef9a9a','#ef5350','#e53935','#b71c1c',  // pinky
    ];
    const CONN_COLOR_PALM  = 'rgba(167,139,250,0.9)';
    const CONN_COLOR_FINGER= 'rgba(255,213,79,0.85)';
    const GLOW_COLOR       = 'rgba(167,139,250,0.18)';

    // ── Draw overlay ────────────────────────────────────────────────────
    function drawHand(landmarks) {
      const W = canvas.width, H = canvas.height;

      // Glow pass (fat semi-transparent lines behind)
      ctx.save();
      ctx.lineWidth = 14;
      ctx.strokeStyle = GLOW_COLOR;
      CONNECTIONS.forEach(([a, b]) => {
        ctx.beginPath();
        ctx.moveTo(landmarks[a].x * W, landmarks[a].y * H);
        ctx.lineTo(landmarks[b].x * W, landmarks[b].y * H);
        ctx.stroke();
      });
      ctx.restore();

      // Main connection lines
      CONNECTIONS.forEach(([a, b]) => {
        const isPalmConn = [5,9,13,17].includes(a) && [9,13,17].includes(b)
          || (a===0 && [5,9,13,17].includes(b));
        ctx.save();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = isPalmConn ? CONN_COLOR_PALM : CONN_COLOR_FINGER;
        ctx.shadowColor = isPalmConn ? 'rgba(167,139,250,0.8)' : 'rgba(255,213,79,0.7)';
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.moveTo(landmarks[a].x * W, landmarks[a].y * H);
        ctx.lineTo(landmarks[b].x * W, landmarks[b].y * H);
        ctx.stroke();
        ctx.restore();
      });

      // Landmark dots
      landmarks.forEach((lm, i) => {
        const x = lm.x * W, y = lm.y * H;
        // Outer glow ring
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255,255,255,0.06)';
        ctx.fill();
        ctx.restore();
        // Dot
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, 4.5, 0, Math.PI * 2);
        ctx.fillStyle = JOINT_COLORS[i] || '#ffffff';
        ctx.shadowColor = JOINT_COLORS[i] || '#ffffff';
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.restore();
      });
    }

    // ── Initialise MediaPipe ─────────────────────────────────────────────
    const vision = await FilesetResolver.forVisionTasks(
      'https://unpkg.com/@mediapipe/tasks-vision@0.10.3/wasm'
    );
    const handLandmarker = await HandLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
        delegate: 'GPU'
      },
      runningMode: 'VIDEO',
      numHands: 2
    });

    // ── Start camera ─────────────────────────────────────────────────────
    status.textContent = '📷 Starting camera...';
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 1280, height: 720 } });
    video.srcObject = stream;
    await new Promise(res => video.onloadeddata = res);
    status.textContent = '✅ Camera ready — raise your palm!';
    badge.style.display = 'block';

    // ── Detection loop ───────────────────────────────────────────────────
    let lastTs = -1;
    let noHandFrames = 0;
    const NO_HAND_THRESHOLD = 8;

    function detect() {
      if (video.readyState < 2) { requestAnimationFrame(detect); return; }

      const now = performance.now();
      if (now === lastTs) { requestAnimationFrame(detect); return; }
      lastTs = now;

      canvas.width  = video.videoWidth  || 640;
      canvas.height = video.videoHeight || 480;

      const result = handLandmarker.detectForVideo(video, now);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (result.landmarks && result.landmarks.length > 0) {
        noHandFrames = 0;
        result.landmarks.forEach(lms => drawHand(lms));
        badge.textContent = result.landmarks.length === 2
          ? '✋ 2 Hands Detected'
          : '✋ Hand Detected';
        badge.className = 'badge-detected';
      } else {
        noHandFrames++;
        if (noHandFrames > NO_HAND_THRESHOLD) {
          badge.textContent = '🤚 No Hand Detected';
          badge.className = 'badge-none';
        }
      }
      requestAnimationFrame(detect);
    }
    requestAnimationFrame(detect);
  </script>
</body>
</html>
"""

    import html as _html
    _escaped = _html.escape(html_code)
    st.markdown(
        f'<iframe srcdoc="{_escaped}" width="100%" height="580" '
        f'allow="camera *; microphone *" '
        f'sandbox="allow-scripts allow-same-origin allow-user-media">'
        f'</iframe>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────

def main():
    # Initialize state first
    init_session_state()

    t = TRANSLATIONS[st.session_state.app_lang]

    st.set_page_config(
        page_title=f"{t['app_title']} — AI Palm Reading",
        page_icon="🔮",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # Render UI
    render_header(t)
    render_sidebar(t)

    # Check for API key
    client = get_gemini_client()
    if client is None:
        if st.session_state.app_lang == "hi":
            st.warning("🔑 शुरू करने के लिए कृपया साइडबार में अपनी जेमिनी एपीआई कुंजी दर्ज करें।")
            st.info("अपनी मुफ्त एपीआई कुंजी प्राप्त करें [गूगल एआई स्टूडियो (Google AI Studio)](https://aistudio.google.com/apikey)")
        else:
            st.warning("🔑 Please enter your Gemini API key in the sidebar to get started.")
            st.info("Get your free API key at [Google AI Studio](https://aistudio.google.com/apikey)")
        return

    # Render introduction paragraph
    st.markdown(
        f"""
        <div style="text-align:center; max-width:850px; margin:0 auto 2.2rem; color:#b0a8d6; font-size:1.1rem; line-height:1.75; font-style:italic;">
            {t["app_intro"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tabs: Palm Reading | Live Scanner ──────────────────────────────
    tab_reading, tab_live = st.tabs([t["tab_reading"], t["tab_live"]])

    # ── Live scanner tab ─────────────────────────────────────────────────
    with tab_live:
        render_live_scanner(t)

    # ── Main palm reading tab ─────────────────────────────────────────────
    with tab_reading:

        # Upload section
        image_file = render_upload_section(t)

        if image_file is not None:
            # Detect if a different file is uploaded and reset the reading state
            file_identifier = getattr(image_file, "name", "camera") + f"_{getattr(image_file, 'size', 0)}"
            if st.session_state.get("last_uploaded_file_id") != file_identifier:
                st.session_state.last_uploaded_file_id = file_identifier
                st.session_state.reading_result = None
                st.session_state.reading_done = False
                st.session_state.chat_history = []
                st.session_state.palm_lines = None  # new image needs fresh line detection
                # Force reprocess on new file
                st.session_state.pop("_clean_img_bytes", None)

            # Retrieve or compute a clean image (bytes + PIL object)
            clean_bytes = st.session_state.get("_clean_img_bytes")
            if clean_bytes is not None:
                # Reuse the already-processed image from a prior run
                image = Image.open(io.BytesIO(clean_bytes))
            else:
                with st.spinner(""):
                    try:
                        raw_bytes = image_file.getvalue()
                        pil_img = Image.open(io.BytesIO(raw_bytes))
                        pil_img = pil_img.copy()
                        pil_img.load()
                        if pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")
                        pil_img.info.clear()

                        # Crop to hand region and remove background
                        pil_img = crop_hand_image(pil_img)

                        clean_buf = io.BytesIO()
                        pil_img.save(clean_buf, format="PNG")
                        png_bytes = clean_buf.getvalue()

                        # Cache for subsequent reruns — avoids re-processing
                        # the same upload on every interaction
                        st.session_state["_clean_img_bytes"] = png_bytes
                        image = Image.open(io.BytesIO(png_bytes))
                    except UnicodeError as e:
                        import traceback
                        logger.error("UnicodeError during image decode/save:\n%s", traceback.format_exc())
                        if st.session_state.app_lang == "hi":
                            st.error("❌ छवि लोड करने में त्रुटि: तस्वीर के मेटाडेटा में असमर्थित वर्ण हैं। कृपया सुनिश्चित करें कि यह एक मान्य छवि फ़ाइल (PNG, JPG, WEBP) है।")
                        else:
                            st.error("❌ Error loading image: the image metadata contains unsupported characters. Please make sure it is a valid image file (PNG, JPG, WEBP).")
                        return
                    except Exception as e:
                        import traceback
                        logger.error("Image load failed:\n%s", traceback.format_exc())
                        if st.session_state.app_lang == "hi":
                            st.error(f"❌ छवि लोड करने में त्रुटि: {e}। कृपया सुनिश्चित करें कि यह एक मान्य छवि फ़ाइल (PNG, JPG, WEBP) है।")
                        else:
                            st.error(f"❌ Error loading image: {e}. Please make sure it is a valid image file (PNG, JPG, WEBP).")
                        return

            # Display palm + scanning animation
            try:
                render_palm_display(image, t)
                if not st.session_state.reading_done and st.session_state.palm_lines is not None:
                    render_palm_scanning_animation(image, t, palm_lines=st.session_state.palm_lines)
            except UnicodeError as e:
                import traceback
                logger.error("UnicodeError during display/scan render:\n%s", traceback.format_exc())
                if st.session_state.app_lang == "hi":
                    st.error("❌ छवि प्रदर्शित करने में त्रुटि: तस्वीर के मेटाडेटा में असमर्थित वर्ण हैं।")
                else:
                    st.error("❌ Error displaying image: the image metadata contains unsupported characters.")
                return

            # Read Palm button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                category_key = st.session_state.selected_category
                tradition_key = st.session_state.selected_tradition

                category_map = READING_CATEGORIES_HI if st.session_state.app_lang == "hi" else READING_CATEGORIES_EN
                tradition_map = TRADITIONS_HI if st.session_state.app_lang == "hi" else TRADITIONS_EN

                # Handle edge case where keys are missing when language switched
                if category_key not in category_map:
                    category_key = list(category_map.keys())[0]
                if tradition_key not in tradition_map:
                    tradition_key = list(tradition_map.keys())[3] # default to "all traditions"

                category = category_map[category_key]
                tradition = tradition_map[tradition_key]

                # If currently loading, display the spinner and call LLM stream
                if st.session_state.loading:
                    # Phase 1: detect palm lines (runs once per reading)
                    if st.session_state.palm_lines is None:
                        with st.spinner(t.get("detecting_lines", "🔍 Detecting palm lines...")):
                            st.session_state.palm_lines = detect_palm_lines(client, image, t)
                        st.rerun()

                    # Phase 2: stream the full reading
                    try:
                        # Clear previous state
                        st.session_state.reading_result = None
                        st.session_state.reading_done = False

                        # Show a modern loading spinner and stream the analysis
                        with st.spinner(t["spinner_reading"]):
                            stream = analyze_palm_stream(client, image, category, tradition, st.session_state.app_lang)
                            reading = st.write_stream(stream)

                        st.session_state.reading_result = reading
                        st.session_state.reading_done = True
                        st.session_state.chat_history = []  # Reset chat for new reading
                    except Exception as e:
                        st.error(t["error_reading"].format(error=str(e)))
                    finally:
                        st.session_state.loading = False
                        st.rerun()

                button_label = t["read_button"].format(category=category_key)
                if st.button(button_label, width="stretch", disabled=st.session_state.loading):
                    st.session_state.loading = True
                    st.rerun()

            # Display reading if available
            if st.session_state.reading_done and st.session_state.reading_result:
                render_reading_result(st.session_state.reading_result)

                # Action buttons row
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button(t["new_reading"], width="stretch"):
                        st.session_state.reading_result = None
                        st.session_state.reading_done = False
                        st.session_state.chat_history = []
                        st.rerun()
                with col_b:
                    st.download_button(
                        t["download_reading"],
                        data=st.session_state.reading_result,
                        file_name="hasthrekha_reading.md",
                        mime="text/markdown",
                        width="stretch",
                    )
                with col_c:
                    if st.button(t["copy_reading"], width="stretch"):
                        st.toast(t["copy_toast"], icon="✅")

                # Follow-up chat
                render_chat_section(client, image, st.session_state.reading_result, t)

        else:
            # No image — show features and reset reading state
            st.session_state.last_uploaded_file_id = None
            st.session_state.reading_result = None
            st.session_state.reading_done = False
            st.session_state.chat_history = []

            st.markdown('<div class="mystic-divider">✦ ✦ ✦</div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                    f"""
                    <div class="glass-card">
                        <h3>{t["ai_vision_title"]}</h3>
                        <p style="color:#8b8ba3;">{t["ai_vision_desc"]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f"""
                    <div class="glass-card">
                        <h3>{t["traditions_title"]}</h3>
                        <p style="color:#8b8ba3;">{t["traditions_desc"]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    f"""
                    <div class="glass-card">
                        <h3>{t["chat_feature_title"]}</h3>
                        <p style="color:#8b8ba3;">{t["chat_feature_desc"]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


    # Footer disclaimer
    st.markdown(
        f"""
        <div style="text-align:center; padding:2rem 0 1rem; color:#4a4a6a; font-size:0.75rem;">
            {t["footer_disclaimer"]}
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
