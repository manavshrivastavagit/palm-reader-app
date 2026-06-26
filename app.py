"""
🔮 Hasthrekha — AI-Powered Multilingual Palm Reading
Streamlit app that uses Gemini's multimodal vision to analyze palm images.
"""

import streamlit as st
from typing import Optional
from google import genai
from PIL import Image
import io
import os
import json
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("hasthrekha")

load_dotenv()

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
        "app_title": "🔮 हस्तरेखा (Hasthrekha)",
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
        "portfolio_title": "👤 आर्किटेक्ट पोर्टफोलियो",
        "github_label": "💻 गिटहब रिपोजिटरी",
        "linkedin_label": "🔗 लिंक्डइन प्रोफाइल",
        "footer_disclaimer": "⚠️ हस्तरेखा केवल मनोरंजन और आत्म-चिंतन के उद्देश्य से है। यह चिकित्सा, वित्तीय या व्यावसायिक सलाह प्रदान नहीं करती है।\n\nआपकी हथेली की तस्वीरें एआई द्वारा प्रोसेस की जाती हैं और इन्हें कहीं भी स्टोर नहीं किया जाता है।"
    },
    "en": {
        "app_title": "🔮 Hasthrekha",
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
        "spinner_reading": "✨ PalmGuide is studying your palm...",
        "error_reading": "❌ Error during reading: {error}",
        "new_reading": "🔄 New Reading",
        "download_reading": "📥 Download Reading",
        "copy_reading": "📋 Copy to Clipboard",
        "copy_toast": "📋 Reading copied!",
        "chat_title": "💬 Ask PalmGuide a Follow-up Question",
        "chat_caption": "Ask anything about your reading — love, career, specific lines, or life guidance.",
        "chat_input_placeholder": "Ask about your palm reading...",
        "chat_spinner": "PalmGuide is reflecting...",
        "ai_vision_title": "🔬 AI Vision Analysis",
        "ai_vision_desc": "Gemini's multimodal AI examines your palm lines, mounts, hand shape, and special markings with precision.",
        "traditions_title": "📜 Three Traditions",
        "traditions_desc": "Get readings grounded in Vedic, Western, and Chinese palmistry — or all three combined.",
        "chat_feature_title": "💬 Ask Follow-ups",
        "chat_feature_desc": "Chat with PalmGuide about your reading. Ask about love, career, health, or any specific line.",
        "portfolio_title": "👤 Architect Portfolio",
        "github_label": "💻 GitHub Repository",
        "linkedin_label": "🔗 LinkedIn Profile",
        "footer_disclaimer": "⚠️ Hasthrekha is for entertainment and self-reflection purposes only. It does not provide medical, financial, or professional advice.\n\nYour palm images are processed by AI and are not permanently stored."
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

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght=300;400;500;600;700;800&family=Playfair+Display:ital,wght=0,400..900;1,400..900&display=swap');

    /* Global typography */
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', -apple-system, sans-serif !important;
    }

    /* Ensure clear text readability on dark background */
    .stApp p, .stApp span, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3 {
        color: #f0f0f5;
    }

    /* Main background with cosmic nebula effect */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #1c0a35 0%, #0a0a1a 70%);
        background-attachment: fixed;
    }

    /* Custom Scrollbar for a premium feel */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0a1a;
    }
    ::-webkit-scrollbar-thumb {
        background: #4c1d95;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #6d28d9;
    }

    /* Header styling with pulsing glowing text */
    .main-header {
        text-align: center;
        padding: 2.5rem 0 1.5rem;
    }
    .main-header h1 {
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
    }
    @keyframes titleGlow {
        from {
            filter: drop-shadow(0 2px 8px rgba(255, 224, 130, 0.15));
        }
        to {
            filter: drop-shadow(0 4px 20px rgba(224, 64, 251, 0.35));
        }
    }
    .main-header p {
        color: #a78bfa;
        font-size: 1.15rem;
        font-style: italic;
        font-weight: 300;
        letter-spacing: 0.5px;
    }

    /* Premium Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.8rem;
        margin: 1rem 0;
        backdrop-filter: blur(16px) saturate(180%);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .glass-card:hover {
        transform: translateY(-4px);
        background: rgba(255, 255, 255, 0.04);
        border-color: rgba(167, 139, 250, 0.25);
        box-shadow: 0 12px 40px 0 rgba(124, 58, 237, 0.18);
    }
    .glass-card h3 {
        font-family: 'Playfair Display', Georgia, serif !important;
        font-size: 1.4rem;
        color: #ffb300;
        margin-bottom: 0.6rem;
    }

    /* File upload design */
    .upload-section {
        background: rgba(124, 58, 237, 0.03);
        border: 2px dashed rgba(167, 139, 250, 0.2);
        border-radius: 20px;
        padding: 2.5rem 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: inset 0 0 20px rgba(124, 58, 237, 0.05);
    }
    .upload-section:hover {
        border-color: rgba(167, 139, 250, 0.5);
        background: rgba(124, 58, 237, 0.06);
        box-shadow: inset 0 0 25px rgba(124, 58, 237, 0.08);
    }

    /* Reading result container */
    .reading-container {
        background: rgba(10, 10, 26, 0.4);
        border: 1px solid rgba(167, 139, 250, 0.15);
        border-radius: 24px;
        padding: 2.5rem;
        margin-top: 2rem;
        line-height: 1.85;
        backdrop-filter: blur(16px);
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.4), inset 0 0 15px rgba(167, 139, 250, 0.05);
    }
    .reading-container h2 {
        font-family: 'Playfair Display', Georgia, serif !important;
        color: #c4b5fd;
        font-size: 2rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(167, 139, 250, 0.15);
    }
    .reading-container h3 {
        font-family: 'Playfair Display', Georgia, serif !important;
        color: #ffb300;
        font-size: 1.45rem;
        margin-top: 1.5rem;
    }

    /* Sidebar customize */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090915 0%, #150926 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.04);
    }
    section[data-testid="stSidebar"] h2 {
        font-family: 'Playfair Display', Georgia, serif !important;
        color: #ffd54f !important;
        font-size: 1.5rem;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #c4b5fd !important;
        font-weight: 500;
    }

    /* Interactive Buttons */
    .stButton > button {
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
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        background-position: right center;
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.4);
    }

    /* Modern Chat Bubble styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        margin-bottom: 0.8rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    /* Chat input focus */
    .stChatInput > div {
        border-color: rgba(167, 139, 250, 0.2) !important;
        border-radius: 14px !important;
        background-color: rgba(15, 10, 25, 0.6) !important;
    }

    /* Spinner color */
    .stSpinner > div {
        border-color: #a855f7 !important;
    }

    /* Celestial Divider */
    .mystic-divider {
        text-align: center;
        margin: 2rem 0;
        color: #ffb300;
        font-size: 1.3rem;
        letter-spacing: 12px;
        opacity: 0.85;
    }

    /* Image display styling */
    .palm-image-container {
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid rgba(167, 139, 250, 0.15);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Expander styling */
    .streamlit-expanderHeader {
        color: #c4b5fd !important;
        font-weight: 600;
        background: transparent !important;
    }
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.01) !important;
        border-radius: 0 0 12px 12px;
    }
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

    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=[prompt, image],
            config=genai.types.GenerateContentConfig(
                system_instruction=get_system_prompt(lang),
                temperature=0.8,
                max_output_tokens=4096,
            ),
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        logger.error(f"Error during palm analysis: {str(e)}", exc_info=True)
        if lang == "hi":
            yield f"\n\n❌ **त्रुटि**: विश्लेषण करने में विफल। ({str(e)})"
        else:
            yield f"\n\n❌ **Error**: Failed to analyze palm. ({str(e)})"


def chat_followup_stream(client: genai.Client, image: Image.Image, reading: str, history: list, question: str, lang: str):
    """Handle follow-up questions about the reading using streaming and native chat history format."""
    logger.info(f"Starting chat follow-up (history_len={len(history)}, lang={lang})")
    contents = []
    
    # 1. Add initial reading context as the first user turn
    contents.append(genai.types.Content(
        role="user",
        parts=[
            genai.types.Part.from_text(text=f"Initial Palm Reading Context:\n\n{reading}"),
            image
        ]
    ))
    
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
    except Exception as e:
        logger.error(f"Error during chat follow-up: {str(e)}", exc_info=True)
        if lang == "hi":
            yield f"\n\n❌ **त्रुटि**: प्रतिक्रिया उत्पन्न करने में विफल। ({str(e)})"
        else:
            yield f"\n\n❌ **Error**: Failed to generate response. ({str(e)})"


# ─────────────────────────────────────────────
# Session State Init
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
        st.image(image, caption=t["your_palm"], width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)


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

        # Get AI response
        with st.chat_message("assistant", avatar="🔮"):
            stream = chat_followup_stream(client, image, reading, st.session_state.chat_history, question, st.session_state.app_lang)
            response = st.write_stream(stream)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()


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
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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

        try:
            # Load image
            image = Image.open(image_file)
            
            # Apply EXIF transpose to ensure correct orientation (prevent sideways images)
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
            
            st.session_state.palm_image = image

            # Display palm
            render_palm_display(image, t)
        except Exception as e:
            if st.session_state.app_lang == "hi":
                st.error(f"❌ छवि लोड करने में त्रुटि: {str(e)}। कृपया सुनिश्चित करें कि यह एक मान्य छवि फ़ाइल (PNG, JPG, WEBP) है।")
            else:
                st.error(f"❌ Error loading image: {str(e)}. Please make sure it is a valid image file (PNG, JPG, WEBP).")
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

            button_label = t["read_button"].format(category=category_key)
            if st.button(button_label, width="stretch"):
                try:
                    # Clear previous state
                    st.session_state.reading_result = None
                    st.session_state.reading_done = False
                    
                    # Show a subtle notice while streaming starts
                    status_placeholder = st.empty()
                    status_placeholder.markdown(f"*{t['spinner_reading']}*")
                    
                    # Call streaming function
                    stream = analyze_palm_stream(client, image, category, tradition, st.session_state.app_lang)
                    
                    # Clear spinner notice and stream the text
                    status_placeholder.empty()
                    reading = st.write_stream(stream)
                    
                    st.session_state.reading_result = reading
                    st.session_state.reading_done = True
                    st.session_state.chat_history = []  # Reset chat for new reading
                    st.rerun()
                except Exception as e:
                    st.error(t["error_reading"].format(error=str(e)))
                    return

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
