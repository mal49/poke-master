# app.py
import os
import requests
import google.generativeai as genai
import gradio as gr
from dotenv import load_dotenv
import random
import json
import re
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY in your .env file!")

genai.configure(api_key=GEMINI_API_KEY)

# Global state for search history and favorites
search_history = []
favorites = []
conversation_history = []  # Store conversation context for intelligent responses
chat_display_history = []  # NEW: Store formatted chat messages for display

# Language translations
TRANSLATIONS = {
    'en': {
        'title': 'PokéAssistant',
        'subtitle': 'Your intelligent Pokémon companion',
        'placeholder': "Ask me anything! 'Who is Garchomp?', 'What are its moves?', 'Build a team'",
        'send': 'SEND',
        'random': 'RANDOM',
        'shiny': '✨ Show Shiny',
        'favorite': '❤️ Add to Favorites',
        'recent': '📜 RECENT SEARCHES',
        'favorites': '❤️ FAVORITES',
        'response': '📊 Assistant Response',
        'chat_history': '💬 CHAT HISTORY',
        'clear_history': '🗑️ Clear History',
        'no_searches': 'No recent searches',
        'no_favorites': 'No favorites yet',
        'no_history': 'No conversation history yet',
        'added_fav': '❤️ Added {name} to favorites!',
        'removed_fav': '💔 Removed {name} from favorites',
        'history_cleared': '✅ Chat history cleared!'
    },
    'ms': {
        'title': 'PokéAssistant',
        'subtitle': 'Pembantu Pokémon pintar anda',
        'placeholder': "Tanya apa sahaja! 'Siapa Garchomp?', 'Apa gerakannya?', 'Bina pasukan'",
        'send': 'HANTAR',
        'random': 'RAWAK',
        'shiny': '✨ Tunjuk Shiny',
        'favorite': '❤️ Tambah ke Kegemaran',
        'recent': '📜 CARIAN TERKINI',
        'favorites': '❤️ KEGEMARAN',
        'response': '📊 Respons Pembantu',
        'chat_history': '💬 SEJARAH SEMBANG',
        'clear_history': '🗑️ Padam Sejarah',
        'no_searches': 'Tiada carian terkini',
        'no_favorites': 'Tiada kegemaran lagi',
        'no_history': 'Tiada sejarah perbualan lagi',
        'added_fav': '❤️ Menambah {name} ke kegemaran!',
        'removed_fav': '💔 Membuang {name} daripada kegemaran',
        'history_cleared': '✅ Sejarah sembang dipadam!'
    },
    'zh': {
        'title': 'PokéAssistant',
        'subtitle': '您的智能宝可梦助手',
        'placeholder': "问我任何问题！'谁是烈咬陆鲨？'，'它的技能是什么？'，'组建队伍'",
        'send': '发送',
        'random': '随机',
        'shiny': '✨ 显示闪光',
        'favorite': '❤️ 添加到收藏',
        'recent': '📜 最近搜索',
        'favorites': '❤️ 收藏夹',
        'response': '📊 助手回复',
        'chat_history': '💬 聊天记录',
        'clear_history': '🗑️ 清除记录',
        'no_searches': '没有最近的搜索',
        'no_favorites': '还没有收藏',
        'no_history': '还没有对话记录',
        'added_fav': '❤️ 已将{name}添加到收藏！',
        'removed_fav': '💔 已从收藏中移除{name}',
        'history_cleared': '✅ 聊天记录已清除！'
    }
}

# Refined System Prompt with Formatting Rules (with language support)
def get_system_prompt(language='en'):
    lang_instruction = ""
    if language == 'ms':
        lang_instruction = "\n\n**IMPORTANT: Respond in Bahasa Melayu (Malay language).**"
    elif language == 'zh':
        lang_instruction = "\n\n**IMPORTANT: Respond in Simplified Chinese (简体中文).**"
    
    return f"""You are PokéAssistant, an intelligent and enthusiastic Pokémon expert.{lang_instruction}

## Your Goal:
Provide accurate, strategic, and engaging Pokémon advice. You have access to real-time data about Pokémon stats, types, and abilities—use it to give specific answers.

## Personality & Tone:
- **Enthusiastic & Helpful:** Use emojis naturally (✨, 🔥, 🛡️). Be encouraging to beginners.
- **Expert but Accessible:** Explain competitive terms (like STAB, IVs, Natures) simply unless asked for deep analysis.
- **Adaptive:** Match the user's energy. If they are frustrated, be empathetic. If excited, celebrate with them.

## Formatting Rules (CRITICAL):
1. **Structure:** Use bullet points and bold text for readability. Avoid walls of text.
2. **Analysis:** When recommending Pokémon, explain *why* (e.g., "Garchomp is great because of its high Speed and Attack...").
3. **Accuracy:** If you don't know something, admit it. Do not invent Pokémon or stats.

## Domain Constraint:
You strictly discuss Pokémon, Nintendo, and related gaming culture. If a user asks about non-Pokémon topics (like math, cooking, politics), politely steer the conversation back to Pokémon (e.g., "I'm better at baking Poffins than cakes! Let's talk about your team.").
"""

# Type effectiveness (simplified)
type_chart = {
    'fire': {'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5, 'fire': 0.5, 'steel': 2},
    'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2},
    'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'flying': 0.5, 'bug': 0.5, 'dragon': 0.5, 'steel': 0.5, 'ground': 2, 'rock': 2},
    'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2},
    'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
    'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'rock': 2, 'steel': 2, 'fairy': 0.5, 'ghost': 0, 'dark': 2},
    'poison': {'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'steel': 0, 'fairy': 2},
    'ground': {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2},
    'flying': {'electric': 0.5, 'ice': 0.5, 'rock': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2},
    'psychic': {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'steel': 0.5, 'dark': 0},
    'bug': {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5, 'steel': 0.5, 'fairy': 0.5, 'dark': 2},
    'rock': {'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2, 'steel': 0.5},
    'ghost': {'psychic': 2, 'ghost': 2, 'dark': 0.5, 'normal': 0},
    'dragon': {'dragon': 2, 'steel': 0.5, 'fairy': 0},
    'dark': {'psychic': 2, 'ghost': 2, 'dark': 0.5, 'fairy': 0.5, 'fighting': 0.5},
    'steel': {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2, 'rock': 2, 'steel': 0.5, 'fairy': 2},
    'fairy': {'fighting': 2, 'dragon': 2, 'dark': 2, 'poison': 0.5, 'steel': 0.5, 'fire': 0.5},
    'normal': {'rock': 0.5, 'ghost': 0, 'steel': 0.5}
}

# Type colors for badges
TYPE_COLORS = {
    'normal': '#A8A878', 'fire': '#F08030', 'water': '#6890F0', 'electric': '#F8D030',
    'grass': '#78C850', 'ice': '#98D8D8', 'fighting': '#C03028', 'poison': '#A040A0',
    'ground': '#E0C068', 'flying': '#A890F0', 'psychic': '#F85888', 'bug': '#A8B820',
    'rock': '#B8A038', 'ghost': '#705898', 'dragon': '#7038F8', 'dark': '#705848',
    'steel': '#B8B8D0', 'fairy': '#EE99AC'
}

# ============== HELPER FUNCTIONS ==============

def is_valid_pokemon(name):
    """Check if a name is a valid Pokémon by querying the API"""
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}", timeout=3)
        return res.status_code == 200
    except:
        return False

def extract_pokemon_name(user_input):
    """Extract Pokémon name from natural language input using PokeAPI validation"""
    words = user_input.lower().split()
    
    stop_words = {'what', 'is', 'the', 'best', 'counter', 'for', 'against', 'how', 'to', 
                  'beat', 'defeat', 'a', 'an', 'can', 'i', 'find', 'me', 'about', 'tell',
                  'show', 'give', 'info', 'information', 'on', 'of', 'with', 'good', 'are',
                  'which', 'pokemon', 'pokémon', 'type', 'types', 'weak', 'weakness', 
                  'strong', 'strength', 'stats', 'moves', 'move', 'and', 'or', 'vs', 'versus',
                  'color', 'colour', 'colored', 'coloured', 'tall', 'height', 'high', 'size',
                  'heavy', 'weight', 'weigh', 'much', 'does', 'mass', 'physical', 'body',
                  'appearance', 'look', 'looks', 'like', 'describe', 'description', 'compare',
                  'comparison', 'between', 'battle', 'fight', 'would', 'win', 'trivia', 'fact',
                  'facts', 'fun', 'interesting', 'scenario', 'if', 'my', 'facing', 'should',
                  'do', 'abilities', 'ability', 'evolution', 'evolve', 'evolves', 'location',
                  'where', 'catch', 'found', 'habitat', 'team', 'build'}
    
    potential_names = [word.strip('?!.,') for word in words if word.strip('?!.,') not in stop_words]
    
    for word in potential_names:
        if word and is_valid_pokemon(word):
            return word
    
    for word in words:
        clean_word = word.strip('?!.,')
        if clean_word and len(clean_word) > 2 and is_valid_pokemon(clean_word):
            return clean_word
    
    return None

def get_pokemon_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}", timeout=5)
        res.raise_for_status()
        return res.json()
    except:
        return None

def get_pokemon_species_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{name.lower()}", timeout=5)
        res.raise_for_status()
        return res.json()
    except:
        return None

# ============== NEW INTELLIGENCE FUNCTIONS ==============

def check_domain_compliance(user_input):
    """Guardrail: Uses Gemini to ensure the query is related to Pokemon."""
    pokemon_keywords = ['pokemon', 'poke', 'pikachu', 'charizard', 'nintendo', 'game', 'anime', 'type', 'move', 'gym', 'trainer', 'battle']
    if any(kw in user_input.lower() for kw in pokemon_keywords):
        return True

    prompt = f"""
    Analyze if the following user input is related to Pokémon, Nintendo, video games, anime culture, or casual chit-chat (greetings).
    Input: "{user_input}"
    
    Reply with only one word: "ALLOWED" or "BLOCKED".
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(prompt)
        return "ALLOWED" in response.text.strip().upper()
    except:
        return True

def get_intelligent_response(user_message, pokemon_context_data=None, sentiment="neutral", language='en'):
    """Generate an intelligent response with language support."""
    global conversation_history
    
    conversation_context = ""
    if conversation_history:
        recent_history = conversation_history[-10:]
        conversation_context = "\n## Recent Conversation:\n"
        for entry in recent_history:
            conversation_context += f"User: {entry['user']}\nAssistant: {entry['assistant'][:500]}...\n\n"
            
    data_context = ""
    if pokemon_context_data:
        p_name = pokemon_context_data.get('name', 'Unknown').capitalize()
        types = [t['type']['name'] for t in pokemon_context_data.get('types', [])]
        stats = {s['stat']['name']: s['base_stat'] for s in pokemon_context_data.get('stats', [])}
        abilities = [a['ability']['name'] for a in pokemon_context_data.get('abilities', [])]
        
        data_context = f"""
        [SYSTEM: REAL-TIME DATA INJECTION]
        Use this verified data to answer the user:
        - Pokémon: {p_name}
        - Types: {', '.join(types)}
        - Stats: {json.dumps(stats)}
        - Abilities: {', '.join(abilities)}
        """
        
    preferences_context = ""
    if favorites:
        preferences_context += f"\n## Favorites: {', '.join([p.capitalize() for p in favorites])}\n"

    full_prompt = f"""{get_system_prompt(language)}

{conversation_context}
{data_context}
{preferences_context}

## Current Interaction:
User Sentiment: {sentiment.upper()}
User Message: {user_message}

## Instructions:
- Respond naturally and conversationally.
- If verified data is provided above in [SYSTEM], use it.
- If the input is general (like "I love pokemon"), engage them enthusiastically.

Respond now:"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            assistant_response = response.text.strip()
            
            conversation_history.append({'user': user_message, 'assistant': assistant_response})
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
                
            return assistant_response
            
        raise Exception("Empty response from AI")

    except Exception as e:
        print(f"❌ GEMINI API ERROR: {str(e)}")
        fallback_messages = {
            'en': "I'm having trouble connecting to the network, but I'm still here! Try asking about a specific Pokémon like 'Pikachu' or 'Charizard' so I can look up their stats directly.",
            'ms': "Saya menghadapi masalah sambungan rangkaian, tetapi saya masih di sini! Cuba tanya tentang Pokémon tertentu seperti 'Pikachu' atau 'Charizard' supaya saya boleh cari statistik mereka terus.",
            'zh': "我在连接网络时遇到了问题，但我还在这里！试着询问特定的宝可梦，比如'皮卡丘'或'喷火龙'，这样我可以直接查找它们的数据。"
        }
        return fallback_messages.get(language, fallback_messages['en'])

def analyze_user_input(user_input):
    """Simple local analysis to detect sentiment and intent."""
    input_lower = user_input.lower()
    
    sentiment = "neutral"
    if any(w in input_lower for w in ["love", "awesome", "cool", "great", "thanks", "wow"]):
        sentiment = "positive"
    elif any(w in input_lower for w in ["hate", "bad", "sucks", "annoying", "hard", "stuck"]):
        sentiment = "frustrated"
    elif "?" in user_input:
        sentiment = "curious"
        
    intent = "general_question"
    if "team" in input_lower: intent = "team_building"
    elif "vs" in input_lower or "compare" in input_lower: intent = "comparison"
    elif "recommend" in input_lower: intent = "recommendation"
    
    return {
        "is_valid": True,
        "intent": intent,
        "sentiment": sentiment,
        "errors": [],
        "warnings": [],
        "clarification_needed": None
    }

# ============== UI HELPER FUNCTIONS ==============

def create_type_badges(types):
    return " ".join([
        f'<span style="background: {TYPE_COLORS.get(t, "#888")}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85em; text-transform: uppercase; margin-right: 5px;">{t}</span>'
        for t in types
    ])

def create_stats_html(stats, max_stat=255):
    hp, atk, defense = stats['hp'], stats['attack'], stats['defense']
    sp_atk, sp_def, speed = stats['special-attack'], stats['special-defense'], stats['speed']
    
    return f"""
    <div style="margin-top: 16px; display: grid; gap: 10px;">
        <div style="display: grid; grid-template-columns: 70px 1fr 40px; align-items: center; gap: 12px;">
            <span style="font-weight: 500; color: #f85149; font-size: 0.85rem;">HP</span>
            <div style="background: #21262d; border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="background: #f85149; width: {hp/max_stat*100}%; height: 100%; border-radius: 6px;"></div>
            </div>
            <span style="color: #8b949e; font-size: 0.85rem; text-align: right;">{hp}</span>
        </div>
        <div style="display: grid; grid-template-columns: 70px 1fr 40px; align-items: center; gap: 12px;">
            <span style="font-weight: 500; color: #f0883e; font-size: 0.85rem;">Attack</span>
            <div style="background: #21262d; border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="background: #f0883e; width: {atk/max_stat*100}%; height: 100%; border-radius: 6px;"></div>
            </div>
            <span style="color: #8b949e; font-size: 0.85rem; text-align: right;">{atk}</span>
        </div>
        <div style="display: grid; grid-template-columns: 70px 1fr 40px; align-items: center; gap: 12px;">
            <span style="font-weight: 500; color: #58a6ff; font-size: 0.85rem;">Defense</span>
            <div style="background: #21262d; border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="background: #58a6ff; width: {defense/max_stat*100}%; height: 100%; border-radius: 6px;"></div>
            </div>
            <span style="color: #8b949e; font-size: 0.85rem; text-align: right;">{defense}</span>
        </div>
        <div style="display: grid; grid-template-columns: 70px 1fr 40px; align-items: center; gap: 12px;">
            <span style="font-weight: 500; color: #3fb950; font-size: 0.85rem;">Sp. Atk</span>
            <div style="background: #21262d; border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="background: #3fb950; width: {sp_atk/max_stat*100}%; height: 100%; border-radius: 6px;"></div>
            </div>
            <span style="color: #8b949e; font-size: 0.85rem; text-align: right;">{sp_atk}</span>
        </div>
        <div style="display: grid; grid-template-columns: 70px 1fr 40px; align-items: center; gap: 12px;">
            <span style="font-weight: 500; color: #a371f7; font-size: 0.85rem;">Sp. Def</span>
            <div style="background: #21262d; border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="background: #a371f7; width: {sp_def/max_stat*100}%; height: 100%; border-radius: 6px;"></div>
            </div>
            <span style="color: #8b949e; font-size: 0.85rem; text-align: right;">{sp_def}</span>
        </div>
        <div style="display: grid; grid-template-columns: 70px 1fr 40px; align-items: center; gap: 12px;">
            <span style="font-weight: 500; color: #db61a2; font-size: 0.85rem;">Speed</span>
            <div style="background: #21262d; border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="background: #db61a2; width: {speed/max_stat*100}%; height: 100%; border-radius: 6px;"></div>
            </div>
            <span style="color: #8b949e; font-size: 0.85rem; text-align: right;">{speed}</span>
        </div>
    </div>
    """

def add_to_history(pokemon_name):
    global search_history
    if pokemon_name not in search_history:
        search_history.insert(0, pokemon_name)
        if len(search_history) > 10:
            search_history = search_history[:10]

def toggle_favorite(pokemon_name, language='en'):
    global favorites
    if pokemon_name in favorites:
        favorites.remove(pokemon_name)
        return TRANSLATIONS[language]['removed_fav'].format(name=pokemon_name.capitalize())
    else:
        favorites.append(pokemon_name)
        return TRANSLATIONS[language]['added_fav'].format(name=pokemon_name.capitalize())

def get_history_html(language='en'):
    if not search_history:
        return f'<span style="color: #8b949e;">{TRANSLATIONS[language]["no_searches"]}</span>'
    return " ".join([
        f'<span style="background: #21262d; color: #8b949e; padding: 4px 10px; border-radius: 8px; margin: 2px; font-size: 0.8em; cursor: pointer;">{p.capitalize()}</span>'
        for p in search_history[:5]
    ])

def get_favorites_html(language='en'):
    if not favorites:
        return f'<span style="color: #8b949e;">{TRANSLATIONS[language]["no_favorites"]}</span>'
    return " ".join([
        f'<span style="background: linear-gradient(135deg, #f85149, #da3633); color: white; padding: 4px 10px; border-radius: 8px; margin: 2px; font-size: 0.8em;">❤️ {p.capitalize()}</span>'
        for p in favorites[:5]
    ])

def get_chat_history_html(language='en'):
    """NEW: Generate HTML for chat history display"""
    global chat_display_history
    if not chat_display_history:
        return f'<div style="color: #8b949e; text-align: center; padding: 20px;">{TRANSLATIONS[language]["no_history"]}</div>'
    
    html = '<div style="display: flex; flex-direction: column; gap: 12px; max-height: 400px; overflow-y: auto; padding: 10px;">'
    for entry in reversed(chat_display_history[-10:]):  # Show last 10 messages
        timestamp = entry.get('timestamp', '')
        user_msg = entry.get('user', '')
        ai_msg = entry.get('assistant', '')[:200] + '...' if len(entry.get('assistant', '')) > 200 else entry.get('assistant', '')
        
        html += f'''
        <div style="background: rgba(88, 166, 255, 0.1); border-left: 3px solid #58a6ff; padding: 10px; border-radius: 8px;">
            <div style="color: #58a6ff; font-size: 0.75rem; margin-bottom: 4px;">{timestamp}</div>
            <div style="color: #c9d1d9; font-size: 0.85rem;"><strong>You:</strong> {user_msg}</div>
        </div>
        <div style="background: rgba(163, 113, 247, 0.1); border-left: 3px solid #a371f7; padding: 10px; border-radius: 8px;">
            <div style="color: #c9d1d9; font-size: 0.85rem;"><strong>Assistant:</strong> {ai_msg}</div>
        </div>
        '''
    html += '</div>'
    return html

def clear_chat_history(language='en'):
    """NEW: Clear chat history"""
    global chat_display_history, conversation_history
    chat_display_history = []
    conversation_history = []
    return get_chat_history_html(language), TRANSLATIONS[language]['history_cleared']

# ============== MAIN RESPONSE FUNCTIONS ==============

def chat_response(user_input, show_shiny=False, current_pokemon_state=None, language='en'):
    """Main chat response function with memory and language support."""
    global search_history, favorites, chat_display_history
    
    if not check_domain_compliance(user_input):
        domain_messages = {
            'en': "🚫 I can only talk about Pokémon and related gaming topics! Let's get back to training! 🧢",
            'ms': "🚫 Saya hanya boleh bercakap tentang Pokémon dan topik permainan berkaitan! Mari kembali berlatih! 🧢",
            'zh': "🚫 我只能谈论宝可梦和相关的游戏话题！让我们回到训练吧！🧢"
        }
        return (
            gr.update(visible=False),
            "🚫 Domain Restriction", 
            "", "", 
            f"<div style='padding: 20px; color: #f85149;'>{domain_messages[language]}</div>", 
            "", "", "", 
            current_pokemon_state,
            get_history_html(language), get_favorites_html(language), get_chat_history_html(language), "", gr.update(visible=False)
        )

    if not user_input.strip():
        return (
            gr.update(visible=False), 
            "Please enter a Pokémon name or question!", 
            "", "", "", "", "", "", 
            current_pokemon_state, 
            get_history_html(language), get_favorites_html(language), get_chat_history_html(language), "", gr.update(visible=False)
        )

    pokemon_name = extract_pokemon_name(user_input)
    
    if not pokemon_name and current_pokemon_state:
        pronouns = ['it', 'its', 'he', 'she', 'they', 'this pokemon', 'him', 'her']
        if any(p in user_input.lower().split() for p in pronouns):
            pokemon_name = current_pokemon_state

    input_analysis = analyze_user_input(user_input)
    user_sentiment = input_analysis.get('sentiment', 'neutral')
    sentiment_color = '#ffcb05'
    if user_sentiment == 'positive': sentiment_color = '#3fb950'
    if user_sentiment == 'frustrated': sentiment_color = '#f85149'

    pokemon_data = None
    if pokemon_name:
        pokemon_data = get_pokemon_data(pokemon_name)
        if pokemon_data:
            current_pokemon_state = pokemon_name
            add_to_history(pokemon_name)

    ai_response = get_intelligent_response(user_input, pokemon_data, user_sentiment, language)
    
    # NEW: Add to chat display history
    timestamp = datetime.now().strftime("%H:%M")
    chat_display_history.append({
        'timestamp': timestamp,
        'user': user_input,
        'assistant': ai_response
    })
    if len(chat_display_history) > 50:
        chat_display_history = chat_display_history[-50:]

    answer_html = f'''
    <div style="padding: 25px; background: rgba(22, 27, 34, 0.9); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
        <div style="margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: flex-end; align-items: center; gap: 8px;">
            <span style="color: #8b949e; font-size: 0.8rem;">Mood detected:</span>
            <span style="background: {sentiment_color}20; color: {sentiment_color}; border: 1px solid {sentiment_color}40; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">
                {user_sentiment}
            </span>
        </div>
        <div style="color: #c9d1d9; line-height: 1.8; white-space: pre-wrap;">{ai_response}</div>
    </div>
    '''

    if pokemon_data:
        name = pokemon_data['name'].capitalize()
        types = [t['type']['name'] for t in pokemon_data['types']]
        stats = {s['stat']['name']: s['base_stat'] for s in pokemon_data['stats']}
        
        if show_shiny:
            sprite = pokemon_data['sprites']['other']['official-artwork'].get('front_shiny') or pokemon_data['sprites']['front_default']
        else:
            sprite = pokemon_data['sprites']['other']['official-artwork']['front_default'] or pokemon_data['sprites']['front_default']
            
        type_badges = create_type_badges(types)
        stats_html = create_stats_html(stats)
        cry_url = pokemon_data.get('cries', {}).get('latest', '')
        
        return (
            gr.update(value=sprite, visible=True),
            f"# {name}", 
            type_badges, 
            stats_html, 
            answer_html,
            "", "", 
            cry_url, 
            current_pokemon_state,
            get_history_html(language), 
            get_favorites_html(language), 
            get_chat_history_html(language),
            '<p style="color: #8b949e;">🔊 Pokémon Cry</p>', 
            gr.update(visible=True)
        )
    else:
        return (
            gr.update(visible=False), 
            f"# 💬 {TRANSLATIONS[language]['title']}", 
            "", "", 
            answer_html, 
            "", "", "", 
            current_pokemon_state, 
            get_history_html(language), 
            get_favorites_html(language), 
            get_chat_history_html(language),
            "", 
            gr.update(visible=False)
        )

def random_pokemon_handler(show_shiny, current_state, language='en'):
    """Handle random Pokémon button"""
    random_id = random.randint(1, 898)
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{random_id}")
        if res.status_code == 200:
            name = res.json()['name']
            return chat_response(name, show_shiny, current_state, language)
    except:
        pass
    return chat_response("pikachu", show_shiny, current_state, language)

def handle_favorite_toggle(pokemon_name, language='en'):
    if pokemon_name:
        msg = toggle_favorite(pokemon_name, language)
        return msg, get_favorites_html(language)
    no_selection = {
        'en': "No Pokémon selected!",
        'ms': "Tiada Pokémon dipilih!",
        'zh': "未选择宝可梦！"
    }
    return no_selection[language], get_favorites_html(language)

def change_language(lang, current_state):
    """Handle language change"""
    return (
        get_history_html(lang),
        get_favorites_html(lang),
        get_chat_history_html(lang),
        TRANSLATIONS[lang]['placeholder'],
        TRANSLATIONS[lang]['send'],
        TRANSLATIONS[lang]['random'],
        TRANSLATIONS[lang]['shiny'],
        TRANSLATIONS[lang]['favorite'],
        current_state
    )

# ============== BUILD GRADIO UI ==============

with gr.Blocks(title="Pokémon Battle Assistant") as demo:
    
    current_pokemon_state = gr.State(None)
    language_state = gr.State('en')
    
    gr.HTML("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            .gradio-container { 
                background: #0d1117 !important;
                background-image: 
                    radial-gradient(circle at 20% 80%, rgba(238, 21, 21, 0.08) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(59, 76, 202, 0.08) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(255, 203, 5, 0.05) 0%, transparent 60%) !important;
                font-family: 'Inter', sans-serif !important;
                min-height: 100vh;
            }
            
            footer { display: none !important; }
            
            .card-section {
                background: rgba(22, 27, 34, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 16px;
            }
            
            .section-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            audio { width: 100%; margin-top: 10px; }
        </style>
        
        <div style="text-align: center; padding: 40px 20px 30px;">
            <h1 style="font-size: 2.5rem; font-weight: 700; color: #ffffff; margin-bottom: 8px; letter-spacing: -0.5px;">
                <span style="color: #ffcb05;">⚡</span> PokéAssistant <span style="color: #ffcb05;">⚡</span>
            </h1>
            <p style="color: #8b949e; font-size: 1.05rem;">
                Your intelligent Pokémon companion • Powered by <span style="color: #f85149;">Gemini AI</span>
            </p>
        </div>
    """)
    
    # Language selector at top
    with gr.Row():
        with gr.Column(scale=1):
            pass
        with gr.Column(scale=2):
            with gr.Row():
                lang_en = gr.Button("🇬🇧 English", size="sm", variant="secondary")
                lang_ms = gr.Button("🇲🇾 Bahasa Melayu", size="sm", variant="secondary")
                lang_zh = gr.Button("🇨🇳 中文", size="sm", variant="secondary")
    
    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=300):
            gr.HTML('''
                <div class="card-section">
                    <div class="section-header">
                        <span style="color: #ffffff; font-weight: 600; font-size: 1.1rem;">Chat with PokéAssistant</span>
                    </div>
                </div>
            ''')
            user_input = gr.Textbox(
                placeholder="Ask me anything! 'Who is Garchomp?', 'What are its moves?', 'Build a team'",
                label="",
                show_label=False,
                container=False,
                lines=2
            )
            
            with gr.Row():
                search_btn = gr.Button("SEND", variant="primary", size="lg")
                random_btn = gr.Button("RANDOM", variant="secondary", size="lg")
                
            shiny_toggle = gr.Checkbox(label="✨ Show Shiny", value=False)
            
            favorite_btn = gr.Button("❤️ Add to Favorites", variant="secondary", size="sm")
            favorite_status = gr.Markdown("")
            
            gr.HTML('<p style="color: #8b949e; margin: 24px 0 12px; font-size: 0.85rem; font-weight: 500;">📜 RECENT SEARCHES</p>')
            history_output = gr.HTML(get_history_html('en'))
            
            gr.HTML('<p style="color: #8b949e; margin: 24px 0 12px; font-size: 0.85rem; font-weight: 500;">❤️ FAVORITES</p>')
            favorites_output = gr.HTML(get_favorites_html('en'))
            
            # NEW: Chat History Section
            chat_history_header = gr.HTML('<p style="color: #8b949e; margin: 24px 0 12px; font-size: 0.85rem; font-weight: 500;">💬 CHAT HISTORY</p>')
            clear_history_btn = gr.Button("🗑️ Clear History", variant="secondary", size="sm")
            chat_history_output = gr.HTML(get_chat_history_html('en'))
        
        with gr.Column(scale=2, min_width=500):
            gr.HTML('''
                <div class="card-section" style="margin-bottom: 0;">
                    <div class="section-header">
                        <span style="font-size: 1.2rem;">📊</span>
                        <span style="color: #ffffff; font-weight: 600; font-size: 1.1rem;">Assistant Response</span>
                    </div>
                </div>
            ''')
            
            with gr.Row(equal_height=True) as pokemon_info_row:
                sprite_output = gr.Image(label="", show_label=False, height=220, width=220, container=False, visible=False)
                with gr.Column():
                    name_output = gr.Markdown("", elem_id="pokemon-name")
                    type_output = gr.HTML("")
                    stats_output = gr.HTML("")
            
            cry_section = gr.HTML('', visible=False)
            cry_audio = gr.Audio(label="", show_label=False, type="filepath", visible=False)
            cry_url_hidden = gr.Textbox(visible=False)
            
            desc_output = gr.HTML("")
            
            counter_output = gr.HTML(visible=False)
            extra_output = gr.Markdown(visible=False)
    
    outputs = [
        sprite_output, name_output, type_output, stats_output, 
        desc_output, counter_output, extra_output, 
        cry_url_hidden, current_pokemon_state, 
        history_output, favorites_output, chat_history_output,
        cry_section, cry_audio
    ]
    
    # Event handlers
    def chat_with_lang(user_input, show_shiny, current_state, lang):
        return chat_response(user_input, show_shiny, current_state, lang)
    
    search_btn.click(fn=chat_with_lang, inputs=[user_input, shiny_toggle, current_pokemon_state, language_state], outputs=outputs)
    user_input.submit(fn=chat_with_lang, inputs=[user_input, shiny_toggle, current_pokemon_state, language_state], outputs=outputs)
    
    random_btn.click(fn=random_pokemon_handler, inputs=[shiny_toggle, current_pokemon_state, language_state], outputs=outputs)
    
    favorite_btn.click(fn=handle_favorite_toggle, inputs=[current_pokemon_state, language_state], outputs=[favorite_status, favorites_output])
    
    # NEW: Clear history button
    clear_history_btn.click(fn=clear_chat_history, inputs=[language_state], outputs=[chat_history_output, favorite_status])
    
    # Language switching
    def set_language(lang, current_state):
        result = change_language(lang, current_state)
        return result + (lang,)
    
    lang_outputs = [history_output, favorites_output, chat_history_output, user_input, search_btn, random_btn, shiny_toggle, favorite_btn, current_pokemon_state, language_state]
    
    lang_en.click(fn=lambda cs: set_language('en', cs), inputs=[current_pokemon_state], outputs=lang_outputs)
    lang_ms.click(fn=lambda cs: set_language('ms', cs), inputs=[current_pokemon_state], outputs=lang_outputs)
    lang_zh.click(fn=lambda cs: set_language('zh', cs), inputs=[current_pokemon_state], outputs=lang_outputs)
    
    def update_cry(url):
        if url and url.startswith('http'):
            return url
        return None
    
    cry_url_hidden.change(fn=update_cry, inputs=[cry_url_hidden], outputs=[cry_audio])

if __name__ == "__main__":
    demo.launch(share=True)