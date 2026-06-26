"""
🔮 PalmVerse — AI-Powered Palm Reading POC
Streamlit app that uses Gemini's multimodal vision to analyze palm images.
"""

import streamlit as st
from typing import Optional
from google import genai
from PIL import Image
import io
import os
import json
from dotenv import load_dotenv

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
    /* Global text color */
    .stApp, .stApp p, .stApp span, .stApp li, .stApp label, .stApp div {
        color: #f0f0f5 !important;
    }

    /* Override for input boxes, selectboxes, dropdown options, and browse file buttons to be dark */
    div[data-baseweb="select"] *, 
    div[data-baseweb="popover"] *,
    div[role="listbox"] *,
    [data-testid="stFileUploader"] button,
    [data-testid="stFileUploader"] button * {
        color: #121214 !important;
    }

    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 30%, #0d1b2a 70%, #0a0a1a 100%);
    }

    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 1rem;
    }
    .main-header h1 {
        background: linear-gradient(135deg, #f7d794 0%, #e8a87c 30%, #d4a5ff 60%, #a29bfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0.2rem;
    }
    .main-header p {
        color: #8b8ba3;
        font-size: 1.1rem;
        font-style: italic;
    }

    /* Card containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }

    /* Upload area */
    .upload-section {
        background: rgba(167, 139, 250, 0.05);
        border: 2px dashed rgba(167, 139, 250, 0.25);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .upload-section:hover {
        border-color: rgba(167, 139, 250, 0.5);
        background: rgba(167, 139, 250, 0.08);
    }

    /* Reading result container */
    .reading-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(212, 165, 255, 0.15);
        border-radius: 20px;
        padding: 2rem;
        margin-top: 1.5rem;
        line-height: 1.8;
    }
    .reading-container h2 {
        color: #d4a5ff;
        margin-top: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(212, 165, 255, 0.15);
    }
    .reading-container h3 {
        color: #f7d794;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d2b 0%, #1a0a2e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #c4b5fd !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
    }

    /* Chat input */
    .stChatInput > div {
        border-color: rgba(167, 139, 250, 0.3) !important;
        border-radius: 12px !important;
    }

    /* Spinner */
    .stSpinner > div {
        border-color: #a855f7 !important;
    }

    /* Divider */
    .mystic-divider {
        text-align: center;
        margin: 1.5rem 0;
        color: #6c6c8a;
        font-size: 1.2rem;
        letter-spacing: 8px;
    }

    /* Feature pills in sidebar */
    .feature-pill {
        display: inline-block;
        background: rgba(167, 139, 250, 0.1);
        border: 1px solid rgba(167, 139, 250, 0.2);
        border-radius: 20px;
        padding: 4px 12px;
        margin: 3px;
        font-size: 0.75rem;
        color: #c4b5fd;
    }

    /* Image display */
    .palm-image-container {
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid rgba(212, 165, 255, 0.2);
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Expander styling */
    .streamlit-expanderHeader {
        color: #d4a5ff !important;
        font-weight: 600;
    }
</style>
"""

# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────


def get_gemini_client() -> Optional[genai.Client]:
    """Initialize and return the Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY", "") or st.session_state.get("api_key", "")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def analyze_palm(client: genai.Client, image: Image.Image, category: str, tradition: str, lang: str) -> str:
    """Send palm image to Gemini for analysis."""
    prompt = build_reading_prompt(category, tradition, lang)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image],
        config=genai.types.GenerateContentConfig(
            system_instruction=get_system_prompt(lang),
            temperature=0.8,
            max_output_tokens=4096,
        ),
    )
    return response.text


def chat_followup(client: genai.Client, image: Image.Image, reading: str, history: list, question: str, lang: str) -> str:
    """Handle follow-up questions about the reading."""
    context = f"""Here is the initial palm reading that was provided:

---
{reading}
---

The user is now asking a follow-up question. Answer based on the palm image 
and the reading context above."""

    messages = [context, image]
    for msg in history:
        messages.append(f"{msg['role'].upper()}: {msg['content']}")
    messages.append(f"USER: {question}")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=messages,
        config=genai.types.GenerateContentConfig(
            system_instruction=get_followup_system_prompt(lang),
            temperature=0.8,
            max_output_tokens=2048,
        ),
    )
    return response.text


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
        "app_lang": "hi",  # Hindi by default
        "selected_category": None,
        "selected_tradition": None,
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

        # Language Selector (Hindi default)
        lang_options = {"Hindi (हिन्दी)": "hi", "English (English)": "en"}
        current_lang_idx = 0 if st.session_state.app_lang == "hi" else 1
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
        st.image(image, caption=t["your_palm"], use_container_width=True)
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
            with st.spinner(t["chat_spinner"]):
                response = chat_followup(client, image, reading, st.session_state.chat_history, question, st.session_state.app_lang)
                st.markdown(response)
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
        # Load image
        image = Image.open(image_file)
        st.session_state.palm_image = image

        # Display palm
        render_palm_display(image, t)

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
            if st.button(button_label, use_container_width=True):
                with st.spinner(t["spinner_reading"]):
                    try:
                        reading = analyze_palm(client, image, category, tradition, st.session_state.app_lang)
                        st.session_state.reading_result = reading
                        st.session_state.reading_done = True
                        st.session_state.chat_history = []  # Reset chat for new reading
                    except Exception as e:
                        st.error(t["error_reading"].format(error=str(e)))
                        return

        # Display reading if available
        if st.session_state.reading_done and st.session_state.reading_result:
            render_reading_result(st.session_state.reading_result)

            # Action buttons row
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button(t["new_reading"], use_container_width=True):
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
                    use_container_width=True,
                )
            with col_c:
                if st.button(t["copy_reading"], use_container_width=True):
                    st.toast(t["copy_toast"], icon="✅")

            # Follow-up chat
            render_chat_section(client, image, st.session_state.reading_result, t)

    else:
        # No image — show features
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
