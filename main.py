# app.py
import os
import requests
import google.generativeai as genai
import gradio as gr
from dotenv import load_dotenv
import random
import json

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

# System prompt for the intelligent Pokémon assistant
POKEMON_ASSISTANT_SYSTEM_PROMPT = """You are PokéAssistant, an enthusiastic and knowledgeable Pokémon expert AI assistant. You combine the conversational intelligence of a modern AI chatbot with deep expertise in all things Pokémon.

## Your Personality:
- Friendly, enthusiastic, and passionate about Pokémon
- Use occasional Pokémon-themed expressions naturally (but don't overdo it)
- Be helpful and encouraging, especially to newer trainers
- Show genuine excitement when discussing rare or powerful Pokémon
- Have opinions and preferences (you can have favorite Pokémon!)

## Your Knowledge Covers:
- All Pokémon from Generation 1-9 (stats, types, abilities, moves, evolutions)
- Competitive battling strategies and team building
- Game mechanics (type matchups, breeding, EVs/IVs, natures)
- Pokémon games, anime, movies, and lore
- Where to find/catch Pokémon in various games
- Pokémon trivia and fun facts

## How to Respond:
1. Be conversational and natural - not robotic or overly formal
2. If the user asks something vague, ask clarifying questions
3. Provide helpful context even if not explicitly asked
4. Use formatting (bold, lists) for clarity when giving detailed info
5. If you notice the user is building a team, offer synergy suggestions
6. Remember context from the conversation
7. If asked about non-Pokémon topics, briefly acknowledge but gently steer back to Pokémon
8. Be honest if you're uncertain about something

## Response Style:
- Keep responses concise but informative (2-4 paragraphs for most questions)
- Use emojis sparingly and naturally (⚡🔥💧 for types, 🎮 for games, etc.)
- Format lists and stats clearly
- End with a follow-up question or suggestion when appropriate

## Important Rules:
- Always provide accurate Pokémon information
- When discussing competitive viability, mention the context (casual, VGC, Smogon tiers)
- If someone asks about a specific game, tailor advice to that game's mechanics
- Be inclusive - all playstyles are valid (competitive, casual, shiny hunting, etc.)
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
                  'where', 'catch', 'found', 'habitat'}
    
    potential_names = [word.strip('?!.,') for word in words if word.strip('?!.,') not in stop_words]
    
    for word in potential_names:
        if word and is_valid_pokemon(word):
            return word
    
    for word in words:
        clean_word = word.strip('?!.,')
        if clean_word and is_valid_pokemon(clean_word):
            return clean_word
    
    return None

def extract_two_pokemon(user_input):
    """Extract two Pokémon names from comparison queries"""
    words = user_input.lower().replace(',', ' ').replace(' vs ', ' ').replace(' versus ', ' ').replace(' and ', ' ').split()
    pokemon_found = []
    
    for word in words:
        clean_word = word.strip('?!.,')
        if clean_word and is_valid_pokemon(clean_word) and clean_word not in pokemon_found:
            pokemon_found.append(clean_word)
            if len(pokemon_found) == 2:
                break
    
    return pokemon_found if len(pokemon_found) == 2 else None

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

def get_pokemon_description(name):
    try:
        data = get_pokemon_species_data(name)
        if data:
            for entry in data['flavor_text_entries']:
                if entry['language']['name'] == 'en':
                    return entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')
        return "No description available."
    except:
        return "No description available."

def get_evolution_chain(species_data):
    """Get evolution chain for a Pokémon"""
    try:
        if not species_data or 'evolution_chain' not in species_data:
            return None
        
        evo_url = species_data['evolution_chain']['url']
        res = requests.get(evo_url, timeout=5)
        res.raise_for_status()
        return res.json()
    except:
        return None

def parse_evolution_chain(chain_data):
    """Parse evolution chain into a list of stages"""
    if not chain_data:
        return []
    
    evolutions = []
    
    def traverse_chain(chain, stage=1):
        species_name = chain['species']['name']
        evolutions.append({'name': species_name, 'stage': stage})
        
        for evo in chain.get('evolves_to', []):
            traverse_chain(evo, stage + 1)
    
    traverse_chain(chain_data['chain'])
    return evolutions

def get_location_encounters(pokemon_name):
    """Get location data for where a Pokémon can be found"""
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/encounters", timeout=5)
        res.raise_for_status()
        return res.json()
    except:
        return []

def get_ability_details(ability_name):
    """Get detailed information about an ability"""
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/ability/{ability_name.lower()}", timeout=5)
        res.raise_for_status()
        data = res.json()
        
        effect = "No description available."
        for entry in data.get('effect_entries', []):
            if entry['language']['name'] == 'en':
                effect = entry['short_effect']
                break
        
        return {'name': ability_name, 'effect': effect}
    except:
        return {'name': ability_name, 'effect': 'Unable to fetch ability details.'}

def get_move_details(move_name):
    """Get detailed information about a move"""
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/move/{move_name.lower()}", timeout=5)
        res.raise_for_status()
        data = res.json()
        
        return {
            'name': move_name.replace('-', ' ').title(),
            'type': data.get('type', {}).get('name', 'unknown'),
            'power': data.get('power', 'N/A'),
            'accuracy': data.get('accuracy', 'N/A'),
            'pp': data.get('pp', 'N/A'),
            'damage_class': data.get('damage_class', {}).get('name', 'unknown')
        }
    except:
        return None

def detect_query_types(user_input):
    """Detect what types of information the user is asking about"""
    input_lower = user_input.lower()
    query_types = []
    
    # Recommendation query - asking for Pokemon suggestions
    if any(kw in input_lower for kw in ['recommend', 'suggest', 'give me a', 'good pokemon', 'best pokemon', 'which pokemon should']):
        query_types.append('recommendation')
    
    # Team building query
    if any(kw in input_lower for kw in ['team', 'build a team', 'create a team', 'team of', 'pokemon team']):
        query_types.append('team_building')
    
    # Add to favorites query
    if any(kw in input_lower for kw in ['add', 'favourite', 'favorite']) and any(kw in input_lower for kw in ['favourite', 'favorite', 'fav']):
        query_types.append('add_favorite')
    
    # Type advantage query with generation filter
    if any(kw in input_lower for kw in ['type advantage', 'super effective', 'effective against', 'advantage against']):
        query_types.append('type_advantage')
    
    # Comparison query
    if any(kw in input_lower for kw in ['compare', 'vs', 'versus', 'between', '1v1', 'matchup', 'who would win']):
        query_types.append('comparison')
    
    # Move recommendations
    if any(kw in input_lower for kw in ['move', 'moves', 'moveset', 'best moves', 'recommended moves', 'learn']):
        query_types.append('moves')
    
    # Ability info
    if any(kw in input_lower for kw in ['ability', 'abilities', 'hidden ability']):
        query_types.append('abilities')
    
    # Evolution
    if any(kw in input_lower for kw in ['evolution', 'evolve', 'evolves', 'evolution chain', 'evolve into']):
        query_types.append('evolution')
    
    # Location with game context
    if any(kw in input_lower for kw in ['location', 'where', 'catch', 'find', 'found', 'habitat', 'encounter']):
        query_types.append('location')
    
    # Trivia/Fun facts
    if any(kw in input_lower for kw in ['trivia', 'fun fact', 'interesting', 'did you know', 'tell me about']):
        query_types.append('trivia')
    
    # Battle scenario
    if any(kw in input_lower for kw in ['scenario', 'if my', 'facing', 'what should', 'battle strategy', 'how to beat']):
        query_types.append('scenario')
    
    # Color-related
    if any(kw in input_lower for kw in ['color', 'colour']):
        query_types.append('color')
    
    # Height-related
    if any(kw in input_lower for kw in ['tall', 'height', 'how tall']):
        query_types.append('height')
    
    # Weight-related
    if any(kw in input_lower for kw in ['heavy', 'weight', 'weigh']):
        query_types.append('weight')
    
    # Battle/counter
    if any(kw in input_lower for kw in ['counter', 'beat', 'defeat', 'weak', 'weakness', 'strong', 'effective']):
        query_types.append('battle')
    
    if not query_types:
        query_types.append('general')
    
    return query_types

def detect_game_context(user_input):
    """Detect if user mentions a specific Pokemon game"""
    input_lower = user_input.lower()
    games = {
        'sword': 'Pokemon Sword',
        'shield': 'Pokemon Shield',
        'scarlet': 'Pokemon Scarlet',
        'violet': 'Pokemon Violet',
        'brilliant diamond': 'Pokemon Brilliant Diamond',
        'shining pearl': 'Pokemon Shining Pearl',
        'legends arceus': 'Pokemon Legends: Arceus',
        'sun': 'Pokemon Sun',
        'moon': 'Pokemon Moon',
        'ultra sun': 'Pokemon Ultra Sun',
        'ultra moon': 'Pokemon Ultra Moon',
        'x': 'Pokemon X',
        'y': 'Pokemon Y',
        'omega ruby': 'Pokemon Omega Ruby',
        'alpha sapphire': 'Pokemon Alpha Sapphire',
        'black': 'Pokemon Black',
        'white': 'Pokemon White',
        'black 2': 'Pokemon Black 2',
        'white 2': 'Pokemon White 2',
        'heartgold': 'Pokemon HeartGold',
        'soulsilver': 'Pokemon SoulSilver',
        'diamond': 'Pokemon Diamond',
        'pearl': 'Pokemon Pearl',
        'platinum': 'Pokemon Platinum',
        'firered': 'Pokemon FireRed',
        'leafgreen': 'Pokemon LeafGreen',
        'ruby': 'Pokemon Ruby',
        'sapphire': 'Pokemon Sapphire',
        'emerald': 'Pokemon Emerald',
        'gold': 'Pokemon Gold',
        'silver': 'Pokemon Silver',
        'crystal': 'Pokemon Crystal',
        'red': 'Pokemon Red',
        'blue': 'Pokemon Blue',
        'yellow': 'Pokemon Yellow',
        'lets go pikachu': "Pokemon Let's Go Pikachu",
        'lets go eevee': "Pokemon Let's Go Eevee",
    }
    
    for game_key, game_name in games.items():
        if game_key in input_lower:
            return game_name
    return None

def detect_generation(user_input):
    """Detect if user mentions a specific generation"""
    input_lower = user_input.lower()
    
    # Check for generation mentions
    gen_patterns = {
        'generation 1': 1, 'gen 1': 1, 'gen1': 1, 'generation i': 1, 'kanto': 1,
        'generation 2': 2, 'gen 2': 2, 'gen2': 2, 'generation ii': 2, 'johto': 2,
        'generation 3': 3, 'gen 3': 3, 'gen3': 3, 'generation iii': 3, 'hoenn': 3,
        'generation 4': 4, 'gen 4': 4, 'gen4': 4, 'generation iv': 4, 'sinnoh': 4,
        'generation 5': 5, 'gen 5': 5, 'gen5': 5, 'generation v': 5, 'unova': 5,
        'generation 6': 6, 'gen 6': 6, 'gen6': 6, 'generation vi': 6, 'kalos': 6,
        'generation 7': 7, 'gen 7': 7, 'gen7': 7, 'generation vii': 7, 'alola': 7,
        'generation 8': 8, 'gen 8': 8, 'gen8': 8, 'generation viii': 8, 'galar': 8,
        'generation 9': 9, 'gen 9': 9, 'gen9': 9, 'generation ix': 9, 'paldea': 9,
    }
    
    for pattern, gen_num in gen_patterns.items():
        if pattern in input_lower:
            return gen_num
    return None

def get_pokemon_by_generation(generation):
    """Get Pokemon ID ranges by generation"""
    gen_ranges = {
        1: (1, 151),
        2: (152, 251),
        3: (252, 386),
        4: (387, 493),
        5: (494, 649),
        6: (650, 721),
        7: (722, 809),
        8: (810, 905),
        9: (906, 1025),
    }
    return gen_ranges.get(generation, (1, 1025))

def get_pokemon_with_type_advantage(target_pokemon_name, generation=None):
    """Get Pokemon that have type advantage against a target Pokemon"""
    target_data = get_pokemon_data(target_pokemon_name)
    if not target_data:
        return []
    
    target_types = [t['type']['name'] for t in target_data['types']]
    
    # Find types that are super effective against target
    effective_types = set()
    for target_type in target_types:
        for attacker_type, matchups in type_chart.items():
            if matchups.get(target_type, 1) > 1:
                effective_types.add(attacker_type)
    
    # Get Pokemon of those types from the specified generation
    result_pokemon = []
    
    if generation:
        start_id, end_id = get_pokemon_by_generation(generation)
    else:
        start_id, end_id = 1, 898
    
    # Sample some Pokemon from the effective types
    type_pokemon_map = {
        'fire': ['charizard', 'arcanine', 'typhlosion', 'infernape', 'blaziken', 'cinderace'],
        'water': ['blastoise', 'gyarados', 'feraligatr', 'empoleon', 'greninja', 'inteleon'],
        'grass': ['venusaur', 'sceptile', 'torterra', 'serperior', 'rillaboom', 'decidueye'],
        'electric': ['pikachu', 'raichu', 'jolteon', 'ampharos', 'luxray', 'zeraora'],
        'ice': ['articuno', 'lapras', 'glaceon', 'weavile', 'mamoswine', 'frosmoth'],
        'fighting': ['machamp', 'lucario', 'conkeldurr', 'blaziken', 'infernape', 'urshifu'],
        'poison': ['nidoking', 'gengar', 'crobat', 'toxicroak', 'dragalge', 'toxtricity'],
        'ground': ['garchomp', 'hippowdon', 'excadrill', 'landorus', 'sandaconda', 'mudsdale'],
        'flying': ['dragonite', 'togekiss', 'staraptor', 'braviary', 'corviknight', 'talonflame'],
        'psychic': ['alakazam', 'espeon', 'gardevoir', 'metagross', 'reuniclus', 'hatterene'],
        'bug': ['scizor', 'heracross', 'volcarona', 'golisopod', 'orbeetle', 'frosmoth'],
        'rock': ['tyranitar', 'aerodactyl', 'rhyperior', 'gigalith', 'coalossal', 'lycanroc'],
        'ghost': ['gengar', 'mismagius', 'chandelure', 'aegislash', 'dragapult', 'spectrier'],
        'dragon': ['dragonite', 'salamence', 'garchomp', 'hydreigon', 'dragapult', 'kommo-o'],
        'dark': ['umbreon', 'tyranitar', 'absol', 'hydreigon', 'grimmsnarl', 'zarude'],
        'steel': ['metagross', 'scizor', 'lucario', 'ferrothorn', 'corviknight', 'duraludon'],
        'fairy': ['togekiss', 'gardevoir', 'sylveon', 'mimikyu', 'hatterene', 'grimmsnarl'],
        'normal': ['snorlax', 'blissey', 'staraptor', 'cinccino', 'diggersby', 'obstagoon']
    }
    
    # Gen 4 specific Pokemon for each type
    gen4_pokemon = {
        'fire': ['infernape', 'magmortar', 'heatran'],
        'water': ['empoleon', 'floatzel', 'gastrodon'],
        'grass': ['torterra', 'roserade', 'leafeon'],
        'electric': ['luxray', 'electivire', 'magnezone'],
        'ice': ['weavile', 'mamoswine', 'glaceon', 'froslass'],
        'fighting': ['lucario', 'infernape', 'gallade', 'toxicroak'],
        'poison': ['toxicroak', 'drapion', 'roserade'],
        'ground': ['garchomp', 'hippowdon', 'rhyperior', 'mamoswine', 'gliscor'],
        'flying': ['staraptor', 'honchkrow', 'togekiss', 'gliscor'],
        'psychic': ['gallade', 'bronzong', 'uxie', 'mesprit', 'azelf'],
        'bug': ['yanmega', 'vespiquen'],
        'rock': ['rhyperior', 'rampardos', 'probopass'],
        'ghost': ['dusknoir', 'mismagius', 'spiritomb', 'rotom', 'froslass', 'giratina'],
        'dragon': ['garchomp', 'dialga', 'palkia', 'giratina'],
        'dark': ['weavile', 'honchkrow', 'drapion', 'spiritomb', 'darkrai'],
        'steel': ['lucario', 'magnezone', 'bronzong', 'empoleon', 'dialga', 'heatran'],
        'fairy': ['togekiss'],  # Fairy type didn't exist in Gen 4, but Togekiss was retconned
    }
    
    for eff_type in effective_types:
        if generation == 4:
            pokemon_list = gen4_pokemon.get(eff_type, [])
        else:
            pokemon_list = type_pokemon_map.get(eff_type, [])
        
        for poke in pokemon_list:
            if poke not in result_pokemon:
                # Verify the Pokemon exists and has the right type
                poke_data = get_pokemon_data(poke)
                if poke_data:
                    poke_types = [t['type']['name'] for t in poke_data['types']]
                    if eff_type in poke_types:
                        result_pokemon.append({
                            'name': poke,
                            'types': poke_types,
                            'advantage_type': eff_type
                        })
    
    return result_pokemon[:10]  # Return up to 10 Pokemon

def get_gemini_recommendation(user_input):
    """Get AI recommendation for a good Pokemon based on user's request"""
    prompt = (
        f"You are a Pokémon expert. The user asked: '{user_input}'\n"
        f"Recommend 3-5 good Pokémon based on their request. For each Pokémon, explain briefly why it's a good choice.\n"
        f"Consider factors like: versatility, strength, typing, availability, and popularity.\n"
        f"Format your response with the Pokémon names in bold (**name**) and keep explanations concise (1-2 sentences each).\n"
        f"Start by naming your top recommendation clearly."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        # Fallback recommendations
        recommendations = [
            ("**Garchomp**", "A powerful Dragon/Ground type with excellent stats and movepool. Great for both casual and competitive play."),
            ("**Tyranitar**", "A versatile Rock/Dark pseudo-legendary that can fill many roles on a team."),
            ("**Lucario**", "A popular Fighting/Steel type with good offensive stats and a cool design."),
            ("**Gengar**", "A fast Ghost/Poison type special attacker that's been a fan favorite since Gen 1."),
            ("**Dragonite**", "The original pseudo-legendary with great bulk, power, and the Multiscale ability."),
        ]
        result = "🌟 **Here are some great Pokémon recommendations:**\n\n"
        for name, reason in recommendations:
            result += f"• {name}: {reason}\n\n"
        return result

def get_gemini_location_with_game(pokemon_name, game_name):
    """Get location info for a Pokemon in a specific game"""
    prompt = (
        f"Where can I catch {pokemon_name.capitalize()} in {game_name}?\n"
        f"Provide specific location(s), method of encounter (grass, fishing, trade, etc.), "
        f"and any special conditions (time of day, weather, etc.).\n"
        f"If {pokemon_name.capitalize()} is not available in {game_name}, clearly state that and suggest alternatives.\n"
        f"Keep the response concise but informative (3-5 sentences)."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        return f"📍 I couldn't fetch specific location data for {pokemon_name.capitalize()} in {game_name}. Try checking a dedicated Pokémon database like Serebii or Bulbapedia for detailed location information."

def analyze_user_input_with_ai(user_input):
    """
    Use Gemini AI to intelligently analyze user input for intent, parameters,
    inconsistencies, and potential issues. Returns structured analysis.
    """
    import json
    
    prompt = f"""You are an intelligent input analyzer for a Pokémon chatbot. Analyze the following user input and return a JSON response.

USER INPUT: "{user_input}"

Analyze the input and return ONLY a valid JSON object (no markdown, no explanation) with these fields:

{{
    "is_valid": true/false,
    "intent": "team_building" | "recommendation" | "pokemon_info" | "comparison" | "type_advantage" | "location" | "moves" | "abilities" | "evolution" | "trivia" | "battle_scenario" | "add_favorite" | "general_question" | "unclear",
    "errors": ["list of critical errors that prevent processing, empty if none"],
    "warnings": ["list of warnings or clarifications needed, empty if none"],
    "parameters": {{
        "team_size": number or null (if team building, what size? standard is 6, max is 6),
        "pokemon_mentioned": ["list of pokemon names mentioned"],
        "types_mentioned": ["list of pokemon types mentioned"],
        "generation": number or null (1-9 if mentioned),
        "game_mentioned": "game name or null",
        "count_requested": number or null (how many pokemon they want),
        "exclusions": ["things to exclude like 'no legendaries'"],
        "constraints": ["special constraints like 'only fire type', 'from gen 4'"]
    }},
    "clarification_needed": "question to ask user if intent is unclear, or null",
    "adjusted_request": "what the system should actually do based on analysis, or null"
}}

IMPORTANT RULES:
1. If user asks for a team of more than 6, set team_size to 6 and add a warning
2. If user asks for a team of 0 or negative, set is_valid to false with an error
3. If user asks for generation outside 1-9, set is_valid to false with an error
4. If the request has contradictions (e.g., "fire type water pokemon"), add a warning
5. If the request is ambiguous, set clarification_needed
6. Detect if user is asking multiple unrelated questions and warn them
7. If input seems like gibberish or spam, set is_valid to false
8. Be smart about understanding natural language variations

Return ONLY the JSON object, nothing else."""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        if response and response.text:
            # Clean up the response - remove markdown code blocks if present
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            analysis = json.loads(text)
            
            # Ensure required fields exist
            analysis.setdefault('is_valid', True)
            analysis.setdefault('intent', 'general_question')
            analysis.setdefault('errors', [])
            analysis.setdefault('warnings', [])
            analysis.setdefault('parameters', {})
            analysis.setdefault('clarification_needed', None)
            analysis.setdefault('adjusted_request', None)
            
            # Add original input
            analysis['original_input'] = user_input
            
            return analysis
    except json.JSONDecodeError as e:
        # Fallback if JSON parsing fails
        pass
    except Exception as e:
        # Fallback for any other error
        pass
    
    # Fallback to basic analysis if AI fails
    return analyze_user_input_fallback(user_input)

def analyze_user_input_fallback(user_input):
    """
    Fallback analysis using regex patterns if AI analysis fails.
    """
    import re
    
    input_lower = user_input.lower().strip()
    analysis = {
        'original_input': user_input,
        'is_valid': True,
        'intent': 'general_question',
        'warnings': [],
        'errors': [],
        'parameters': {},
        'clarification_needed': None,
        'adjusted_request': None
    }
    
    # Empty or too short input
    if len(input_lower) < 2:
        analysis['errors'].append("❌ Input too short. Please provide more details.")
        analysis['is_valid'] = False
        return analysis
    
    # Team size detection
    team_patterns = [
        r'team\s+of\s+(\d+)',
        r'(\d+)\s+pokemon\s+team',
        r'(\d+)\s+member\s+team',
    ]
    
    is_team_request = any(kw in input_lower for kw in ['team', 'build a team', 'create a team', 'party'])
    
    for pattern in team_patterns:
        match = re.search(pattern, input_lower)
        if match:
            team_size = int(match.group(1))
            if team_size < 1:
                analysis['errors'].append(f"❌ Invalid team size: {team_size}. A team must have at least 1 Pokémon.")
                analysis['is_valid'] = False
            elif team_size > 6:
                analysis['warnings'].append(f"⚠️ You requested {team_size} Pokémon, but max team size is 6. I'll create a team of 6.")
                analysis['parameters']['team_size'] = 6
            else:
                analysis['parameters']['team_size'] = team_size
                if team_size != 6 and is_team_request:
                    analysis['warnings'].append(f"📝 Creating a team of {team_size} Pokémon (not the standard 6).")
            break
    
    # Generation validation
    gen_match = re.search(r'gen(?:eration)?\s*(\d+)', input_lower)
    if gen_match:
        gen_num = int(gen_match.group(1))
        if gen_num < 1 or gen_num > 9:
            analysis['errors'].append(f"❌ Invalid generation: {gen_num}. Pokémon generations range from 1 to 9.")
            analysis['is_valid'] = False
        else:
            analysis['parameters']['generation'] = gen_num
    
    # Multiple questions detection
    if input_lower.count('?') > 1:
        analysis['warnings'].append(f"📝 You asked multiple questions. For best results, ask one at a time.")
    
    return analysis

def analyze_user_input(user_input):
    """
    Main entry point for input analysis. Uses AI for smart analysis.
    """
    return analyze_user_input_with_ai(user_input)

def format_analysis_warnings(analysis):
    """Format analysis warnings and errors into HTML"""
    html = ""
    
    if analysis.get('errors'):
        html += '<div style="padding: 15px; background: rgba(248, 81, 73, 0.15); border-radius: 12px; border: 2px solid #f85149; margin-bottom: 15px;">'
        for error in analysis['errors']:
            # Add emoji if not present
            if not any(error.startswith(e) for e in ['❌', '⚠️', '📝', '💡']):
                error = f"❌ {error}"
            html += f'<p style="color: #f85149; margin: 5px 0;">{error}</p>'
        html += '</div>'
    
    if analysis.get('warnings'):
        html += '<div style="padding: 15px; background: rgba(255, 203, 5, 0.15); border-radius: 12px; border: 2px solid #ffcb05; margin-bottom: 15px;">'
        for warning in analysis['warnings']:
            # Add emoji if not present
            if not any(warning.startswith(e) for e in ['❌', '⚠️', '📝', '💡']):
                warning = f"⚠️ {warning}"
            html += f'<p style="color: #ffcb05; margin: 5px 0;">{warning}</p>'
        html += '</div>'
    
    # Show clarification needed if present
    if analysis.get('clarification_needed'):
        html += '<div style="padding: 15px; background: rgba(88, 166, 255, 0.15); border-radius: 12px; border: 2px solid #58a6ff; margin-bottom: 15px;">'
        html += f'<p style="color: #58a6ff; margin: 5px 0;">💬 {analysis["clarification_needed"]}</p>'
        html += '</div>'
    
    # Show adjusted request if present
    if analysis.get('adjusted_request'):
        html += '<div style="padding: 15px; background: rgba(59, 185, 80, 0.15); border-radius: 12px; border: 2px solid #3fb950; margin-bottom: 15px;">'
        html += f'<p style="color: #3fb950; margin: 5px 0;">💡 {analysis["adjusted_request"]}</p>'
        html += '</div>'
    
    return html

def get_gemini_team_builder(user_input, required_pokemon=None, team_size=6):
    """Build a team of Pokemon based on user's request with validated team size"""
    
    # Ensure team size is valid
    team_size = max(1, min(team_size, 6))
    
    prompt = (
        f"You are a Pokémon team building expert. The user requested: '{user_input}'\n"
    )
    if required_pokemon:
        prompt += f"The team MUST include: {required_pokemon.capitalize()}\n"
    
    prompt += (
        f"Create a balanced team of exactly {team_size} Pokémon. Consider:\n"
        f"1. Type coverage (minimize shared weaknesses)\n"
        f"2. Role diversity (attacker, tank, support, etc.)\n"
        f"3. Synergy between team members\n\n"
        f"For each Pokémon, provide:\n"
        f"- Name (in bold)\n"
        f"- Type(s)\n"
        f"- Role on the team (1 sentence)\n\n"
        f"Format the response clearly with all {team_size} Pokémon numbered from 1 to {team_size}.\n"
        f"IMPORTANT: Output EXACTLY {team_size} Pokémon, no more, no less."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        # Fallback team - adjusted for team size
        base_team = [
            ("Garchomp", "Dragon/Ground - Physical sweeper with great coverage"),
            ("Togekiss", "Fairy/Flying - Special attacker and support"),
            ("Tyranitar", "Rock/Dark - Bulky attacker with Sand Stream"),
            ("Ferrothorn", "Grass/Steel - Defensive wall with hazards"),
            ("Rotom-Wash", "Electric/Water - Defensive pivot with only one weakness"),
            ("Cinderace", "Fire - Fast physical attacker with Libero"),
        ]
        
        if required_pokemon:
            team = [(required_pokemon.capitalize(), "Your requested Pokémon")]
            team.extend(base_team[:team_size - 1])
        else:
            team = base_team[:team_size]
        
        result = f"🎮 **Here's your balanced team of {team_size} Pokémon:**\n\n"
        for i, (name, role) in enumerate(team, 1):
            result += f"{i}. **{name}** - {role}\n\n"
        result += f"\n💡 This team of {team_size} has good type coverage and role diversity!"
        return result

def find_counter_types(target_types):
    effective_types = set()
    for t in target_types:
        for attacker_type, matchups in type_chart.items():
            if matchups.get(t, 1) > 1:
                effective_types.add(attacker_type)
    return list(effective_types)[:3]

def suggest_counter_pokemon(counter_types):
    examples = {
        'water': 'Blastoise', 'electric': 'Raichu', 'grass': 'Venusaur',
        'ice': 'Articuno', 'fighting': 'Lucario', 'ground': 'Garchomp',
        'flying': 'Dragonite', 'rock': 'Tyranitar', 'steel': 'Metagross',
        'fairy': 'Togekiss', 'psychic': 'Alakazam', 'bug': 'Scizor',
        'fire': 'Charizard', 'ghost': 'Gengar', 'dark': 'Umbreon',
        'dragon': 'Salamence', 'poison': 'Nidoking', 'normal': 'Snorlax'
    }
    suggestions = []
    for t in counter_types:
        if t in examples:
            suggestions.append(examples[t])
    return suggestions[:3]

def calculate_type_effectiveness(attacker_types, defender_types):
    """Calculate overall type effectiveness multiplier"""
    multiplier = 1.0
    for atk_type in attacker_types:
        for def_type in defender_types:
            multiplier *= type_chart.get(atk_type, {}).get(def_type, 1.0)
    return multiplier

def get_random_pokemon():
    """Get a random Pokémon (from Gen 1-8, IDs 1-898)"""
    random_id = random.randint(1, 898)
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{random_id}", timeout=5)
        res.raise_for_status()
        return res.json()['name']
    except:
        return "pikachu"  # Fallback

# ============== GEMINI AI FUNCTIONS ==============

def get_gemini_explanation(attacker, defender, all_counters):
    """Get battle tips using Gemini AI with fallback"""
    counters_list = ", ".join(all_counters) if all_counters else attacker
    prompt = (
        f"You are a Pokémon battle expert providing strategic advice. "
        f"Give detailed battle tips for defeating {defender} using counters like {counters_list}. "
        f"Include the following in your response (use 3-4 sentences total):\n"
        f"1. Explain the type advantage and why these counters are effective\n"
        f"2. Suggest 1-2 specific powerful moves these counters can use against {defender}\n"
        f"3. Mention any important battle strategy tips\n"
        f"Keep it informative but easy to read."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        # Fallback: Generate basic tips using type data
        return f"💡 **Battle Strategy for {defender}:**\n\n• Use {counters_list} as they have type advantages against {defender}.\n• Focus on super-effective moves to deal maximum damage.\n• Watch out for {defender}'s potential coverage moves!"

def get_gemini_comparison(pokemon1, pokemon2, data1, data2):
    """Get AI analysis of a Pokémon matchup with fallback"""
    types1 = [t['type']['name'] for t in data1['types']]
    types2 = [t['type']['name'] for t in data2['types']]
    stats1 = {s['stat']['name']: s['base_stat'] for s in data1['stats']}
    stats2 = {s['stat']['name']: s['base_stat'] for s in data2['stats']}
    
    prompt = (
        f"Compare {pokemon1.capitalize()} ({'/'.join(types1)} type, HP:{stats1['hp']}, ATK:{stats1['attack']}, DEF:{stats1['defense']}, SPD:{stats1['speed']}) "
        f"vs {pokemon2.capitalize()} ({'/'.join(types2)} type, HP:{stats2['hp']}, ATK:{stats2['attack']}, DEF:{stats2['defense']}, SPD:{stats2['speed']}). "
        f"In 3-4 sentences, analyze: 1) Type matchup advantages, 2) Which has better stats for battle, 3) Who would likely win in a 1v1 and why. "
        f"Be specific about type effectiveness multipliers."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        # Fallback: Generate basic comparison using stats
        total1 = sum(stats1.values())
        total2 = sum(stats2.values())
        eff_1_on_2 = calculate_type_effectiveness(types1, types2)
        eff_2_on_1 = calculate_type_effectiveness(types2, types1)
        
        analysis = f"**{pokemon1.capitalize()}** is a {'/'.join(types1)} type with {total1} total base stats. "
        analysis += f"**{pokemon2.capitalize()}** is a {'/'.join(types2)} type with {total2} total base stats.\n\n"
        
        if eff_1_on_2 > 1:
            analysis += f"• {pokemon1.capitalize()} deals {eff_1_on_2}x damage to {pokemon2.capitalize()}!\n"
        if eff_2_on_1 > 1:
            analysis += f"• {pokemon2.capitalize()} deals {eff_2_on_1}x damage to {pokemon1.capitalize()}!\n"
        
        if stats1['speed'] > stats2['speed']:
            analysis += f"• {pokemon1.capitalize()} is faster and will move first."
        else:
            analysis += f"• {pokemon2.capitalize()} is faster and will move first."
        
        return analysis

def get_gemini_move_recommendations(pokemon_name, pokemon_data):
    """Get AI-recommended moveset with fallback using PokeAPI data"""
    types = [t['type']['name'] for t in pokemon_data['types']]
    moves = [m['move']['name'].replace('-', ' ').title() for m in pokemon_data['moves'][:50]]
    
    prompt = (
        f"You are a competitive Pokémon expert. Recommend the best 4-move set for {pokemon_name.capitalize()} "
        f"(Type: {'/'.join(types)}). Available moves include: {', '.join(moves[:20])}... "
        f"For each move, briefly explain why it's good (1 sentence each). Consider STAB, coverage, and utility. "
        f"Format: Move Name - Reason"
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        # Fallback: Show available moves from PokeAPI
        stab_moves = []
        other_moves = []
        
        for move in pokemon_data['moves'][:30]:
            move_name = move['move']['name']
            move_details = get_move_details(move_name)
            if move_details:
                if move_details['type'] in types:
                    stab_moves.append(f"**{move_details['name']}** ({move_details['type'].capitalize()}) - STAB move, Power: {move_details['power'] or 'Status'}")
                elif move_details['power'] and move_details['power'] != 'N/A':
                    other_moves.append(f"**{move_details['name']}** ({move_details['type'].capitalize()}) - Coverage, Power: {move_details['power']}")
        
        result = f"📋 **Available Moves for {pokemon_name.capitalize()}:**\n\n"
        if stab_moves:
            result += "**STAB Moves (Same Type Attack Bonus):**\n" + "\n".join(stab_moves[:4]) + "\n\n"
        if other_moves:
            result += "**Coverage Moves:**\n" + "\n".join(other_moves[:4])
        
        return result if (stab_moves or other_moves) else f"This Pokémon can learn moves like: {', '.join(moves[:10])}"

def get_gemini_trivia(pokemon_name, pokemon_data=None, species_data=None):
    """Get fun trivia about a Pokémon with PokeAPI fallback"""
    prompt = (
        f"Share 3 interesting and fun trivia facts about the Pokémon {pokemon_name.capitalize()}. "
        f"Include facts about its design inspiration, anime appearances, game history, or unique characteristics. "
        f"Make it engaging and fun! Format each fact with an emoji."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        # Fallback: Generate trivia from PokeAPI data
        trivia_facts = []
        name = pokemon_name.capitalize()
        
        # Get data if not provided
        if not pokemon_data:
            pokemon_data = get_pokemon_data(pokemon_name)
        if not species_data:
            species_data = get_pokemon_species_data(pokemon_name)
        
        if pokemon_data:
            # Fact 1: Physical stats
            height_m = pokemon_data['height'] / 10
            weight_kg = pokemon_data['weight'] / 10
            trivia_facts.append(f"📏 **{name}** stands at {height_m}m tall and weighs {weight_kg}kg!")
            
            # Fact 2: Types
            types = [t['type']['name'].capitalize() for t in pokemon_data['types']]
            trivia_facts.append(f"⚡ {name} is a **{'/'.join(types)}** type Pokémon!")
            
            # Fact 3: Base stats highlight
            stats = {s['stat']['name']: s['base_stat'] for s in pokemon_data['stats']}
            best_stat = max(stats, key=stats.get)
            trivia_facts.append(f"💪 {name}'s best stat is **{best_stat.replace('-', ' ').title()}** with a base value of **{stats[best_stat]}**!")
            
            # Fact 4: Abilities
            abilities = [a['ability']['name'].replace('-', ' ').title() for a in pokemon_data['abilities']]
            trivia_facts.append(f"🎯 {name} can have these abilities: **{', '.join(abilities)}**")
        
        if species_data:
            # Fact 5: Generation
            gen_url = species_data.get('generation', {}).get('name', '')
            if gen_url:
                gen_num = gen_url.replace('generation-', '').upper()
                trivia_facts.append(f"🎮 {name} was introduced in **Generation {gen_num}**!")
            
            # Fact 6: Color
            color = species_data.get('color', {}).get('name', '')
            if color:
                trivia_facts.append(f"🎨 {name} is classified as a **{color.capitalize()}** colored Pokémon!")
            
            # Fact 7: Habitat
            habitat = species_data.get('habitat')
            if habitat:
                trivia_facts.append(f"🏠 {name} is typically found in **{habitat['name'].replace('-', ' ').title()}** habitats!")
            
            # Fact 8: Legendary/Mythical status
            if species_data.get('is_legendary'):
                trivia_facts.append(f"⭐ {name} is a **Legendary Pokémon**!")
            elif species_data.get('is_mythical'):
                trivia_facts.append(f"✨ {name} is a **Mythical Pokémon**!")
            
            # Fact 9: Capture rate
            capture_rate = species_data.get('capture_rate', 0)
            if capture_rate:
                difficulty = "very easy" if capture_rate > 200 else "easy" if capture_rate > 100 else "moderate" if capture_rate > 45 else "hard" if capture_rate > 3 else "extremely rare"
                trivia_facts.append(f"🎯 {name} has a capture rate of **{capture_rate}** ({difficulty} to catch)!")
        
        # Return 3-5 random facts
        import random
        selected_facts = random.sample(trivia_facts, min(5, len(trivia_facts))) if len(trivia_facts) > 3 else trivia_facts
        return "\n\n".join(selected_facts) if selected_facts else f"🔍 {name} is a fascinating Pokémon! Search for more details about its stats and abilities."

def get_gemini_battle_scenario(user_pokemon, opponent_pokemon, user_data, opponent_data):
    """Get AI advice for a specific battle scenario with fallback"""
    user_types = [t['type']['name'] for t in user_data['types']]
    opp_types = [t['type']['name'] for t in opponent_data['types']]
    user_stats = {s['stat']['name']: s['base_stat'] for s in user_data['stats']}
    opp_stats = {s['stat']['name']: s['base_stat'] for s in opponent_data['stats']}
    
    prompt = (
        f"Battle Scenario: My {user_pokemon.capitalize()} ({'/'.join(user_types)}, Speed:{user_stats['speed']}) "
        f"is facing an opponent's {opponent_pokemon.capitalize()} ({'/'.join(opp_types)}, Speed:{opp_stats['speed']}). "
        f"Give me specific battle advice in 4-5 sentences: "
        f"1) Who moves first? 2) Type effectiveness analysis 3) Best strategy (attack, switch, or status moves?) "
        f"4) Specific move recommendations 5) What to watch out for from the opponent."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        # Fallback: Generate battle analysis using type chart
        user_name = user_pokemon.capitalize()
        opp_name = opponent_pokemon.capitalize()
        
        # Speed check
        speed_analysis = f"⚡ **Speed:** "
        if user_stats['speed'] > opp_stats['speed']:
            speed_analysis += f"Your {user_name} (Speed: {user_stats['speed']}) is faster than {opp_name} (Speed: {opp_stats['speed']}) and will move first!"
        elif user_stats['speed'] < opp_stats['speed']:
            speed_analysis += f"{opp_name} (Speed: {opp_stats['speed']}) is faster than your {user_name} (Speed: {user_stats['speed']}) and will move first!"
        else:
            speed_analysis += f"Both Pokémon have equal speed ({user_stats['speed']})! It's a speed tie - random who moves first."
        
        # Type effectiveness
        user_eff = calculate_type_effectiveness(user_types, opp_types)
        opp_eff = calculate_type_effectiveness(opp_types, user_types)
        
        type_analysis = f"\n\n🎯 **Type Matchup:**\n"
        type_analysis += f"• Your {user_name}'s {'/'.join(user_types)} attacks deal **{user_eff}x** damage to {opp_name}\n"
        type_analysis += f"• {opp_name}'s {'/'.join(opp_types)} attacks deal **{opp_eff}x** damage to your {user_name}"
        
        # Strategy recommendation
        strategy = f"\n\n💡 **Strategy:**\n"
        if user_eff > 1 and opp_eff <= 1:
            strategy += f"✅ You have the advantage! Attack with {'/'.join(user_types)}-type moves for super effective damage!"
        elif user_eff <= 1 and opp_eff > 1:
            strategy += f"⚠️ You're at a disadvantage! Consider switching to a better counter or using status moves to stall."
        elif user_eff > 1 and opp_eff > 1:
            strategy += f"⚔️ Both sides can deal super effective damage! Speed and prediction are key - try to outspeed or predict switches."
        else:
            strategy += f"📊 Neutral matchup. Focus on your Pokémon's strongest stats and coverage moves."
        
        return speed_analysis + type_analysis + strategy

def get_intelligent_response(user_message, pokemon_context=None):
    """
    Generate an intelligent, conversational response using Gemini with full context.
    This is the main AI brain of the chatbot - handles all types of queries naturally.
    """
    global conversation_history
    
    # Build context from recent conversation (last 10 exchanges)
    conversation_context = ""
    if conversation_history:
        recent_history = conversation_history[-10:]
        conversation_context = "\n## Recent Conversation:\n"
        for entry in recent_history:
            conversation_context += f"User: {entry['user']}\nAssistant: {entry['assistant'][:500]}...\n\n"
    
    # Build Pokemon data context if available
    pokemon_data_context = ""
    if pokemon_context:
        pokemon_data_context = f"\n## Relevant Pokémon Data (from PokéAPI):\n{pokemon_context}\n"
    
    # Build user preferences context
    preferences_context = ""
    if favorites:
        preferences_context += f"\n## User's Favorite Pokémon: {', '.join([p.capitalize() for p in favorites])}\n"
    if search_history:
        preferences_context += f"## Recently Searched: {', '.join([p.capitalize() for p in search_history[:5]])}\n"
    
    # Create the full prompt
    full_prompt = f"""{POKEMON_ASSISTANT_SYSTEM_PROMPT}

{conversation_context}
{pokemon_data_context}
{preferences_context}

## Current User Message:
{user_message}

## Instructions for this response:
- Respond naturally and conversationally
- If the user's message relates to their favorites or recent searches, acknowledge that connection
- If you need more information to give a good answer, ask follow-up questions
- If the user seems to be building towards something (like team building), proactively help
- Keep the response focused but don't be too brief - be helpful and thorough
- If the question is completely unrelated to Pokémon, briefly acknowledge it but gently redirect to Pokémon topics
- Use markdown formatting for clarity (bold, lists, etc.)

Respond now:"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            assistant_response = response.text.strip()
            
            # Store in conversation history
            conversation_history.append({
                'user': user_message,
                'assistant': assistant_response
            })
            
            # Keep history manageable (last 20 exchanges)
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            return assistant_response
        raise Exception("Empty response")
    except Exception as e:
        # Fallback response
        return f"🤔 I'm having a moment here! Let me try to help anyway.\n\n**You asked:** {user_message}\n\n💡 **Tip:** Try asking about a specific Pokémon, or I can help you build a team, find counters, or discuss battle strategies!"

def get_gemini_qa(question):
    """Legacy function - now routes to intelligent response"""
    return get_intelligent_response(question)

def clear_conversation_history():
    """Clear the conversation history for a fresh start"""
    global conversation_history
    conversation_history = []
    return "🔄 Conversation cleared! Let's start fresh. What would you like to know about Pokémon?"

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
    """Add a Pokémon to search history"""
    global search_history
    if pokemon_name not in search_history:
        search_history.insert(0, pokemon_name)
        if len(search_history) > 10:
            search_history = search_history[:10]

def toggle_favorite(pokemon_name):
    """Add or remove a Pokémon from favorites"""
    global favorites
    if pokemon_name in favorites:
        favorites.remove(pokemon_name)
        return f"💔 Removed {pokemon_name.capitalize()} from favorites"
    else:
        favorites.append(pokemon_name)
        return f"❤️ Added {pokemon_name.capitalize()} to favorites!"

def get_history_html():
    """Generate HTML for search history"""
    if not search_history:
        return '<span style="color: #8b949e;">No recent searches</span>'
    return " ".join([
        f'<span style="background: #21262d; color: #8b949e; padding: 4px 10px; border-radius: 8px; margin: 2px; font-size: 0.8em; cursor: pointer;">{p.capitalize()}</span>'
        for p in search_history[:5]
    ])

def get_favorites_html():
    """Generate HTML for favorites"""
    if not favorites:
        return '<span style="color: #8b949e;">No favorites yet</span>'
    return " ".join([
        f'<span style="background: linear-gradient(135deg, #f85149, #da3633); color: white; padding: 4px 10px; border-radius: 8px; margin: 2px; font-size: 0.8em;">❤️ {p.capitalize()}</span>'
        for p in favorites[:5]
    ])

# ============== MAIN RESPONSE FUNCTIONS ==============

def chat_response(user_input, show_shiny=False):
    """Main chat response function"""
    global search_history, favorites
    
    # Cry section HTML (visible for normal queries)
    cry_section_html = '<p style="color: #8b949e; margin: 10px 0 5px; font-size: 0.85rem;">🔊 Pokémon Cry</p>'
    
    if not user_input.strip():
        return None, "Please enter a Pokémon name or question!", "", "", "<p style='color: #8b949e;'>Enter a Pokémon name to see its description.</p>", "", "", "", "", get_history_html(), get_favorites_html(), cry_section_html, gr.update(visible=True)

    # ============== INPUT ANALYSIS ==============
    # Analyze user input for validation and parameter extraction
    input_analysis = analyze_user_input(user_input)
    
    # If there are critical errors, return early with error message
    if not input_analysis['is_valid'] and input_analysis['errors']:
        error_html = format_analysis_warnings(input_analysis)
        error_html += '<p style="color: #8b949e; margin-top: 15px;">Please try again with a valid request.</p>'
        return None, "# ❌ Input Error", "", "", error_html, "", "", "", "", get_history_html(), get_favorites_html(), "", gr.update(visible=False)

    query_types = detect_query_types(user_input)
    game_context = detect_game_context(user_input)
    generation = detect_generation(user_input)
    
    # Handle "add to favorites" command directly
    if 'add_favorite' in query_types:
        pokemon_name = extract_pokemon_name(user_input)
        if pokemon_name:
            # Add to favorites and show the Pokemon info
            if pokemon_name not in favorites:
                favorites.append(pokemon_name)
            
            # Get Pokemon data to show
            data = get_pokemon_data(pokemon_name)
            if data:
                add_to_history(pokemon_name)
                name = data['name'].capitalize()
                types = [t['type']['name'] for t in data['types']]
                stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                
                if show_shiny:
                    sprite = data['sprites']['other']['official-artwork'].get('front_shiny') or data['sprites'].get('front_shiny') or data['sprites']['front_default']
                else:
                    sprite = data['sprites']['other']['official-artwork']['front_default'] or data['sprites']['front_default']
                
                species_data = get_pokemon_species_data(pokemon_name)
                desc = "No description available."
                if species_data:
                    for entry in species_data.get('flavor_text_entries', []):
                        if entry['language']['name'] == 'en':
                            desc = entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')
                            break
                
                type_badges = create_type_badges(types)
                stats_html = create_stats_html(stats)
                counter_types = find_counter_types(types)
                counter_names = suggest_counter_pokemon(counter_types)
                
                counter_html = ""
                if counter_names:
                    counter_html = " ".join([
                        f'<span style="background: linear-gradient(135deg, #ee1515, #cc0000); color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; margin: 3px;">{c}</span>'
                        for c in counter_names
                    ])
                
                cry_url = data.get('cries', {}).get('latest', '') or data.get('cries', {}).get('legacy', '')
                
                desc_html = f'''
                <div style="margin-top: 20px;">
                    <div style="padding: 15px; background: linear-gradient(135deg, rgba(59, 185, 80, 0.2), rgba(22, 27, 34, 0.9)); border-radius: 12px; border: 2px solid #3fb950; margin-bottom: 15px;">
                        <p style="color: #3fb950; font-weight: 600; margin: 0;">❤️ Added {name} to your favorites!</p>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <span style="font-size: 1.1rem;">📖</span>
                        <span style="color: #58a6ff; font-weight: 600;">Description</span>
                    </div>
                    <p style="color: #c9d1d9; line-height: 1.6; margin: 0;">{desc}</p>
                </div>
                '''
                
                return gr.update(value=sprite, visible=True), f"# {name}", type_badges, stats_html, desc_html, counter_html, "", cry_url, pokemon_name, get_history_html(), get_favorites_html(), cry_section_html, gr.update(visible=True)
    
    # Handle team building queries
    if 'team_building' in query_types or input_analysis.get('intent') == 'team_building':
        # Extract any required Pokemon from the query
        required_pokemon = extract_pokemon_name(user_input)
        
        # Also check AI-detected pokemon
        ai_pokemon = input_analysis.get('parameters', {}).get('pokemon_mentioned', [])
        if ai_pokemon and not required_pokemon:
            # Use first AI-detected pokemon
            for poke in ai_pokemon:
                if is_valid_pokemon(poke):
                    required_pokemon = poke
                    break
        
        # Get team size from AI analysis (default to 6)
        team_size = 6
        warnings_html = ""
        
        # Check for team_size from AI analysis
        ai_team_size = input_analysis.get('parameters', {}).get('team_size')
        if ai_team_size is not None:
            team_size = max(1, min(int(ai_team_size), 6))
        
        # Format any warnings/errors from AI analysis
        if input_analysis.get('warnings') or input_analysis.get('errors') or input_analysis.get('clarification_needed') or input_analysis.get('adjusted_request'):
            warnings_html = format_analysis_warnings(input_analysis)
        
        team_response = get_gemini_team_builder(user_input, required_pokemon, team_size)
        
        answer_html = f'''
        <div style="padding: 25px; background: rgba(22, 27, 34, 0.9); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
            {warnings_html}
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                <span style="font-size: 1.5rem;">🎮</span>
                <h2 style="color: #ffcb05; margin: 0;">Team Builder ({team_size} Pokémon)</h2>
            </div>
            <div style="color: #c9d1d9; line-height: 1.8; white-space: pre-wrap;">{team_response}</div>
        </div>
        '''
        return None, f"# 🎮 Pokémon Team Builder ({team_size} Pokémon)", "", "", answer_html, "", "", "", "", get_history_html(), get_favorites_html(), "", gr.update(visible=False)
    
    # Handle recommendation queries
    if 'recommendation' in query_types or input_analysis.get('intent') == 'recommendation':
        # Format any warnings from analysis
        warnings_html = ""
        if input_analysis.get('warnings') or input_analysis.get('clarification_needed') or input_analysis.get('adjusted_request'):
            warnings_html = format_analysis_warnings(input_analysis)
        
        recommendation = get_gemini_recommendation(user_input)
        answer_html = f'''
        <div style="padding: 25px; background: rgba(22, 27, 34, 0.9); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
            {warnings_html}
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                <span style="font-size: 1.5rem;">🌟</span>
                <h2 style="color: #ffcb05; margin: 0;">Pokémon Recommendations</h2>
            </div>
            <div style="color: #c9d1d9; line-height: 1.8; white-space: pre-wrap;">{recommendation}</div>
        </div>
        '''
        return None, "# 🌟 Pokémon Recommendations", "", "", answer_html, "", "", "", "", get_history_html(), get_favorites_html(), "", gr.update(visible=False)
    
    # Handle type advantage queries with generation filter
    if 'type_advantage' in query_types or input_analysis.get('intent') == 'type_advantage':
        pokemon_name = extract_pokemon_name(user_input)
        
        # Also check AI-detected pokemon
        if not pokemon_name:
            ai_pokemon = input_analysis.get('parameters', {}).get('pokemon_mentioned', [])
            for poke in ai_pokemon:
                if is_valid_pokemon(poke):
                    pokemon_name = poke
                    break
        
        # Check AI-detected generation
        if not generation:
            generation = input_analysis.get('parameters', {}).get('generation')
        
        if pokemon_name:
            # Format any warnings from analysis
            warnings_html = ""
            if input_analysis.get('warnings') or input_analysis.get('clarification_needed') or input_analysis.get('adjusted_request'):
                warnings_html = format_analysis_warnings(input_analysis)
            
            advantage_pokemon = get_pokemon_with_type_advantage(pokemon_name, generation)
            if advantage_pokemon:
                gen_text = f" from Generation {generation}" if generation else ""
                
                pokemon_cards = ""
                for poke in advantage_pokemon:
                    poke_data = get_pokemon_data(poke['name'])
                    if poke_data:
                        sprite = poke_data['sprites']['front_default']
                        type_badges = create_type_badges(poke['types'])
                        pokemon_cards += f'''
                        <div style="display: inline-block; background: rgba(0,0,0,0.3); border-radius: 12px; padding: 15px; margin: 8px; text-align: center; min-width: 140px;">
                            <img src="{sprite}" style="width: 80px; height: 80px;" />
                            <p style="color: #fff; font-weight: 600; margin: 8px 0 5px;">{poke['name'].capitalize()}</p>
                            <div style="margin-bottom: 8px;">{type_badges}</div>
                            <p style="color: #3fb950; font-size: 0.8rem; margin: 0;">Super effective with {poke['advantage_type']}</p>
                        </div>
                        '''
                
                answer_html = f'''
                <div style="padding: 25px; background: rgba(22, 27, 34, 0.9); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
                    {warnings_html}
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                        <span style="font-size: 1.5rem;">⚔️</span>
                        <h2 style="color: #f85149; margin: 0;">Pokémon with Type Advantage vs {pokemon_name.capitalize()}{gen_text}</h2>
                    </div>
                    <p style="color: #8b949e; margin-bottom: 20px;">These Pokémon can deal super effective damage:</p>
                    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
                        {pokemon_cards}
                    </div>
                </div>
                '''
                return None, f"# ⚔️ Type Advantage vs {pokemon_name.capitalize()}", "", "", answer_html, "", "", "", "", get_history_html(), get_favorites_html(), "", gr.update(visible=False)
    
    # Handle comparison queries
    if 'comparison' in query_types or input_analysis.get('intent') == 'comparison':
        pokemon_pair = extract_two_pokemon(user_input)
        if pokemon_pair:
            return handle_comparison(pokemon_pair[0], pokemon_pair[1], show_shiny)
    
    # Handle general Q&A (no specific Pokémon mentioned)
    pokemon_name = extract_pokemon_name(user_input)
    
    if not pokemon_name:
        # Use intelligent response for ANY query - the AI will handle it naturally
        # Format any warnings from analysis
        warnings_html = ""
        if input_analysis.get('warnings') or input_analysis.get('clarification_needed'):
            warnings_html = format_analysis_warnings(input_analysis)
        
        # Get intelligent conversational response
        answer = get_intelligent_response(user_input)
        
        # Format the response nicely
        answer_html = f'''
        <div style="padding: 25px; background: rgba(22, 27, 34, 0.9); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
            {warnings_html}
            <div style="color: #c9d1d9; line-height: 1.8; white-space: pre-wrap;">{answer}</div>
        </div>
        '''
        return None, "# 🤖 PokéAssistant", "", "", answer_html, "", "", "", "", get_history_html(), get_favorites_html(), "", gr.update(visible=False)

    # Get Pokémon data
    data = get_pokemon_data(pokemon_name)
    if not data:
        return None, f"❌ Pokémon '{pokemon_name}' not found!", "", "", "<p style='color: #f85149;'>Could not find this Pokémon in the database.</p>", "", "", "", "", get_history_html(), get_favorites_html(), cry_section_html, gr.update(visible=True)

    # Add to history
    add_to_history(pokemon_name)

    name = data['name'].capitalize()
    types = [t['type']['name'] for t in data['types']]
    stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
    
    # Get sprite (shiny or regular)
    if show_shiny:
        sprite = data['sprites']['other']['official-artwork'].get('front_shiny') or data['sprites'].get('front_shiny') or data['sprites']['front_default']
    else:
        sprite = data['sprites']['other']['official-artwork']['front_default'] or data['sprites']['front_default']
    
    # Get species data
    species_data = get_pokemon_species_data(pokemon_name)
    
    # Get description
    desc = "No description available."
    if species_data:
        for entry in species_data.get('flavor_text_entries', []):
            if entry['language']['name'] == 'en':
                desc = entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')
                break

    type_badges = create_type_badges(types)
    stats_html = create_stats_html(stats)
    
    # Find counters
    counter_types = find_counter_types(types)
    counter_names = suggest_counter_pokemon(counter_types)
    
    counter_html = ""
    if counter_names:
        counter_html = " ".join([
            f'<span style="background: linear-gradient(135deg, #ee1515, #cc0000); color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; margin: 3px;">{c}</span>'
            for c in counter_names
        ])
    else:
        counter_html = '<span style="color: #888;">No specific counters found</span>'

    # Build response based on query types
    extra_info = []
    
    # Handle different query types
    if 'moves' in query_types:
        move_recs = get_gemini_move_recommendations(pokemon_name, data)
        extra_info.append(f"## 🎯 Recommended Moveset\n{move_recs}")
    
    if 'abilities' in query_types:
        abilities = data.get('abilities', [])
        ability_info = []
        for ab in abilities:
            ab_details = get_ability_details(ab['ability']['name'])
            hidden = " (Hidden)" if ab.get('is_hidden') else ""
            ability_info.append(f"**{ab_details['name'].replace('-', ' ').title()}{hidden}**: {ab_details['effect']}")
        extra_info.append(f"## ⚡ Abilities\n" + "\n".join(ability_info))
    
    if 'evolution' in query_types:
        evo_chain = get_evolution_chain(species_data)
        evolutions = parse_evolution_chain(evo_chain)
        if evolutions:
            evo_text = " → ".join([f"**{e['name'].capitalize()}**" for e in evolutions])
            extra_info.append(f"## 🔄 Evolution Chain\n{evo_text}")
    
    if 'location' in query_types:
        # Check if user specified a game
        if game_context:
            location_info = get_gemini_location_with_game(pokemon_name, game_context)
            extra_info.append(f"## 📍 Location in {game_context}\n{location_info}")
        else:
            locations = get_location_encounters(pokemon_name)
            if locations:
                loc_names = list(set([loc['location_area']['name'].replace('-', ' ').title() for loc in locations[:5]]))
                extra_info.append(f"## 📍 Locations\n" + ", ".join(loc_names[:5]))
            else:
                extra_info.append("## 📍 Locations\nNo wild encounter data available (may be starter, legendary, or event Pokémon)")
    
    if 'trivia' in query_types:
        trivia = get_gemini_trivia(pokemon_name, data, species_data)
        extra_info.append(f"## 🎲 Fun Trivia\n{trivia}")
    
    if 'scenario' in query_types:
        # Try to find opponent Pokémon
        words = user_input.lower().split()
        opponent = None
        for word in words:
            clean = word.strip('?!.,')
            if clean != pokemon_name and is_valid_pokemon(clean):
                opponent = clean
                break
        
        if opponent:
            opp_data = get_pokemon_data(opponent)
            if opp_data:
                scenario = get_gemini_battle_scenario(pokemon_name, opponent, data, opp_data)
                extra_info.append(f"## ⚔️ Battle Scenario vs {opponent.capitalize()}\n{scenario}")
    
    # Default battle tips if no specific query or battle query
    if 'battle' in query_types or 'general' in query_types:
        if counter_names:
            battle_tip = get_gemini_explanation(counter_names[0], name, counter_names)
            extra_info.append(f"## 💡 Battle Tips\n{battle_tip}")
    
    # Physical attributes
    if 'color' in query_types and species_data:
        color = species_data.get('color', {}).get('name', 'Unknown')
        extra_info.append(f"🎨 **Color**: {color.capitalize()}")
    
    if 'height' in query_types:
        height_m = data['height'] / 10
        extra_info.append(f"📏 **Height**: {height_m:.1f}m")
    
    if 'weight' in query_types:
        weight_kg = data['weight'] / 10
        extra_info.append(f"⚖️ **Weight**: {weight_kg:.1f}kg")

    # Combine extra info
    combined_extra = "\n\n---\n\n".join(extra_info) if extra_info else ""
    
    # Get cry URL
    cry_url = data.get('cries', {}).get('latest', '') or data.get('cries', {}).get('legacy', '')

    # Wrap description in HTML with header
    desc_html = f'''
    <div style="margin-top: 20px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
            <span style="font-size: 1.1rem;">📖</span>
            <span style="color: #58a6ff; font-weight: 600;">Description</span>
        </div>
        <p style="color: #c9d1d9; line-height: 1.6; margin: 0;">{desc}</p>
    </div>
    '''
    
    # Cry section HTML
    cry_section_html = '<p style="color: #8b949e; margin: 10px 0 5px; font-size: 0.85rem;">🔊 Pokémon Cry</p>'

    # Return with sprite visible (for normal Pokemon lookup)
    return gr.update(value=sprite, visible=True), f"# {name}", type_badges, stats_html, desc_html, counter_html, combined_extra, cry_url, pokemon_name, get_history_html(), get_favorites_html(), cry_section_html, gr.update(visible=True)

def handle_comparison(pokemon1, pokemon2, show_shiny=False):
    """Handle Pokémon comparison queries with beautiful side-by-side UI"""
    data1 = get_pokemon_data(pokemon1)
    data2 = get_pokemon_data(pokemon2)
    
    cry_section_html = '<p style="color: #8b949e; margin: 10px 0 5px; font-size: 0.85rem;">🔊 Pokémon Cry</p>'
    
    if not data1 or not data2:
        return gr.update(value=None, visible=True), "❌ Could not find one or both Pokémon!", "", "", "<p style='color: #f85149;'>Could not find one or both Pokémon for comparison.</p>", "", "", "", "", get_history_html(), get_favorites_html(), cry_section_html, gr.update(visible=True)
    
    add_to_history(pokemon1)
    add_to_history(pokemon2)
    
    name1, name2 = data1['name'].capitalize(), data2['name'].capitalize()
    types1 = [t['type']['name'] for t in data1['types']]
    types2 = [t['type']['name'] for t in data2['types']]
    stats1 = {s['stat']['name']: s['base_stat'] for s in data1['stats']}
    stats2 = {s['stat']['name']: s['base_stat'] for s in data2['stats']}
    
    # Get sprites for both Pokémon
    if show_shiny:
        sprite1 = data1['sprites']['other']['official-artwork'].get('front_shiny') or data1['sprites']['front_default']
        sprite2 = data2['sprites']['other']['official-artwork'].get('front_shiny') or data2['sprites']['front_default']
    else:
        sprite1 = data1['sprites']['other']['official-artwork']['front_default'] or data1['sprites']['front_default']
        sprite2 = data2['sprites']['other']['official-artwork']['front_default'] or data2['sprites']['front_default']
    
    # Type effectiveness
    eff_1_on_2 = calculate_type_effectiveness(types1, types2)
    eff_2_on_1 = calculate_type_effectiveness(types2, types1)
    
    # Stats comparison
    total1 = sum(stats1.values())
    total2 = sum(stats2.values())
    
    # Determine winner for visual styling
    winner_is_1 = (eff_1_on_2 > eff_2_on_1) or (eff_1_on_2 == eff_2_on_1 and total1 > total2)
    winner_is_2 = (eff_2_on_1 > eff_1_on_2) or (eff_1_on_2 == eff_2_on_1 and total2 > total1)
    
    # AI Analysis
    ai_analysis = get_gemini_comparison(pokemon1, pokemon2, data1, data2)
    
    # Determine winner prediction
    if eff_1_on_2 > eff_2_on_1:
        verdict = f"🏆 **{name1}** has the type advantage and is predicted to win!"
    elif eff_2_on_1 > eff_1_on_2:
        verdict = f"🏆 **{name2}** has the type advantage and is predicted to win!"
    elif total1 > total2:
        verdict = f"📊 **{name1}** has better stats ({total1} vs {total2})!"
    elif total2 > total1:
        verdict = f"📊 **{name2}** has better stats ({total2} vs {total1})!"
    else:
        verdict = "⚖️ It's an even match!"
    
    # Create beautiful centered comparison HTML
    comparison_html = f"""
<div style="max-width: 900px; margin: 0 auto; padding: 20px;">
    <!-- Title -->
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="
            background: linear-gradient(135deg, #ffcb05, #ff6b35);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2rem;
            font-weight: 800;
            margin: 0;
        ">⚔️ BATTLE COMPARISON ⚔️</h1>
    </div>
    
    <!-- Pokemon Cards Side by Side -->
    <div style="display: flex; justify-content: center; align-items: stretch; gap: 20px; flex-wrap: wrap;">
        
        <!-- Pokemon 1 Card -->
        <div style="
            flex: 1;
            min-width: 280px;
            max-width: 350px;
            background: linear-gradient(180deg, {'rgba(59, 185, 80, 0.2)' if winner_is_1 else 'rgba(88, 166, 255, 0.15)'} 0%, rgba(22, 27, 34, 0.95) 100%);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            border: 3px solid {'#3fb950' if winner_is_1 else 'rgba(88, 166, 255, 0.4)'};
            position: relative;
            box-shadow: 0 10px 40px {'rgba(59, 185, 80, 0.3)' if winner_is_1 else 'rgba(88, 166, 255, 0.2)'};
        ">
            {'<div style="position: absolute; top: -15px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #3fb950, #2ea043); color: white; padding: 6px 20px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; box-shadow: 0 4px 15px rgba(59, 185, 80, 0.4);">👑 ADVANTAGE</div>' if winner_is_1 else ''}
            
            <!-- Sprite -->
            <div style="
                background: radial-gradient(circle, {'rgba(59, 185, 80, 0.3)' if winner_is_1 else 'rgba(88, 166, 255, 0.2)'} 0%, transparent 70%);
                padding: 15px;
                margin: 10px auto 20px;
                display: inline-block;
            ">
                <img src="{sprite1}" alt="{name1}" style="
                    width: 150px;
                    height: 150px;
                    object-fit: contain;
                    filter: drop-shadow(0 8px 25px {'rgba(59, 185, 80, 0.5)' if winner_is_1 else 'rgba(88, 166, 255, 0.4)'});
                "/>
            </div>
            
            <!-- Name -->
            <h2 style="
                color: {'#3fb950' if winner_is_1 else '#58a6ff'};
                margin: 0 0 15px 0;
                font-size: 1.6rem;
                font-weight: 700;
            ">{name1}</h2>
            
            <!-- Types -->
            <div style="margin-bottom: 20px;">
                {create_type_badges(types1)}
            </div>
            
            <!-- Stats Grid -->
            <div style="
                background: rgba(0, 0, 0, 0.4);
                border-radius: 15px;
                padding: 18px;
            ">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div style="text-align: center; padding: 8px; background: rgba(248, 81, 73, 0.15); border-radius: 10px;">
                        <div style="color: #f85149; font-size: 0.75rem; margin-bottom: 4px;">❤️ HP</div>
                        <div style="color: #fff; font-size: 1.2rem; font-weight: 700;">{stats1['hp']}</div>
                    </div>
                    <div style="text-align: center; padding: 8px; background: rgba(240, 136, 62, 0.15); border-radius: 10px;">
                        <div style="color: #f0883e; font-size: 0.75rem; margin-bottom: 4px;">⚔️ ATK</div>
                        <div style="color: #fff; font-size: 1.2rem; font-weight: 700;">{stats1['attack']}</div>
                    </div>
                    <div style="text-align: center; padding: 8px; background: rgba(88, 166, 255, 0.15); border-radius: 10px;">
                        <div style="color: #58a6ff; font-size: 0.75rem; margin-bottom: 4px;">🛡️ DEF</div>
                        <div style="color: #fff; font-size: 1.2rem; font-weight: 700;">{stats1['defense']}</div>
                    </div>
                    <div style="text-align: center; padding: 8px; background: rgba(219, 97, 162, 0.15); border-radius: 10px;">
                        <div style="color: #db61a2; font-size: 0.75rem; margin-bottom: 4px;">💨 SPD</div>
                        <div style="color: #fff; font-size: 1.2rem; font-weight: 700;">{stats1['speed']}</div>
                    </div>
                </div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); text-align: center;">
                    <span style="color: #8b949e; font-size: 0.85rem;">Total Stats: </span>
                    <span style="color: #fff; font-size: 1.3rem; font-weight: 700;">{total1}</span>
                </div>
            </div>
            
            <!-- Damage Output -->
            <div style="
                margin-top: 20px;
                padding: 15px;
                background: {'rgba(59, 185, 80, 0.2)' if eff_1_on_2 > 1 else 'rgba(248, 81, 73, 0.2)' if eff_1_on_2 < 1 else 'rgba(139, 148, 158, 0.15)'};
                border-radius: 12px;
                border: 2px solid {'#3fb950' if eff_1_on_2 > 1 else '#f85149' if eff_1_on_2 < 1 else '#8b949e'};
            ">
                <div style="color: #8b949e; font-size: 0.8rem; margin-bottom: 5px;">Damage to {name2}</div>
                <div style="color: {'#3fb950' if eff_1_on_2 > 1 else '#f85149' if eff_1_on_2 < 1 else '#fff'}; font-size: 1.8rem; font-weight: 800;">
                    {eff_1_on_2}x {'🔥' if eff_1_on_2 > 1 else '❄️' if eff_1_on_2 < 1 else ''}
                </div>
            </div>
        </div>
        
        <!-- VS Badge (Center) -->
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 10px;
        ">
            <div style="
                background: linear-gradient(135deg, #f85149, #da3633);
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.8rem;
                font-weight: 900;
                color: white;
                box-shadow: 0 0 40px rgba(248, 81, 73, 0.6);
                border: 4px solid rgba(255, 255, 255, 0.3);
            ">VS</div>
        </div>
        
        <!-- Pokemon 2 Card -->
        <div style="
            flex: 1;
            min-width: 280px;
            max-width: 350px;
            background: linear-gradient(180deg, {'rgba(59, 185, 80, 0.2)' if winner_is_2 else 'rgba(248, 81, 73, 0.15)'} 0%, rgba(22, 27, 34, 0.95) 100%);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            border: 3px solid {'#3fb950' if winner_is_2 else 'rgba(248, 81, 73, 0.4)'};
            position: relative;
            box-shadow: 0 10px 40px {'rgba(59, 185, 80, 0.3)' if winner_is_2 else 'rgba(248, 81, 73, 0.2)'};
        ">
            {'<div style="position: absolute; top: -15px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #3fb950, #2ea043); color: white; padding: 6px 20px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; box-shadow: 0 4px 15px rgba(59, 185, 80, 0.4);">👑 ADVANTAGE</div>' if winner_is_2 else ''}
            
            <!-- Sprite -->
            <div style="
                background: radial-gradient(circle, {'rgba(59, 185, 80, 0.3)' if winner_is_2 else 'rgba(248, 81, 73, 0.2)'} 0%, transparent 70%);
                padding: 15px;
                margin: 10px auto 20px;
                display: inline-block;
            ">
                <img src="{sprite2}" alt="{name2}" style="
                    width: 150px;
                    height: 150px;
                    object-fit: contain;
                    filter: drop-shadow(0 8px 25px {'rgba(59, 185, 80, 0.5)' if winner_is_2 else 'rgba(248, 81, 73, 0.4)'});
                "/>
            </div>
            
            <!-- Name -->
            <h2 style="
                color: {'#3fb950' if winner_is_2 else '#f85149'};
                margin: 0 0 15px 0;
                font-size: 1.6rem;
                font-weight: 700;
            ">{name2}</h2>
            
            <!-- Types -->
            <div style="margin-bottom: 20px;">
                {create_type_badges(types2)}
            </div>
            
            <!-- Stats Grid -->
            <div style="
                background: rgba(0, 0, 0, 0.4);
                border-radius: 15px;
                padding: 18px;
            ">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div style="text-align: center; padding: 8px; background: rgba(248, 81, 73, 0.15); border-radius: 10px;">
                        <div style="color: #f85149; font-size: 0.75rem; margin-bottom: 4px;">❤️ HP</div>
                        <div style="color: #fff; font-size: 1.2rem; font-weight: 700;">{stats2['hp']}</div>
                    </div>
                    <div style="text-align: center; padding: 8px; background: rgba(240, 136, 62, 0.15); border-radius: 10px;">
                        <div style="color: #f0883e; font-size: 0.75rem; margin-bottom: 4px;">⚔️ ATK</div>
                        <div style="color: #fff; font-size: 1.2rem; font-weight: 700;">{stats2['attack']}</div>
                    </div>
                    <div style="text-align: center; padding: 8px; background: rgba(88, 166, 255, 0.15); border-radius: 10px;">
                        <div style="color: #58a6ff; font-size: 0.75rem; margin-bottom: 4px;">🛡️ DEF</div>
                        <div style="color: #fff; font-size: 1.2rem; font-weight: 700;">{stats2['defense']}</div>
                    </div>
                    <div style="text-align: center; padding: 8px; background: rgba(219, 97, 162, 0.15); border-radius: 10px;">
                        <div style="color: #db61a2; font-size: 0.75rem; margin-bottom: 4px;">💨 SPD</div>
                        <div style="color: #fff; font-size: 1.2rem; font-weight: 700;">{stats2['speed']}</div>
                    </div>
                </div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); text-align: center;">
                    <span style="color: #8b949e; font-size: 0.85rem;">Total Stats: </span>
                    <span style="color: #fff; font-size: 1.3rem; font-weight: 700;">{total2}</span>
                </div>
            </div>
            
            <!-- Damage Output -->
            <div style="
                margin-top: 20px;
                padding: 15px;
                background: {'rgba(59, 185, 80, 0.2)' if eff_2_on_1 > 1 else 'rgba(248, 81, 73, 0.2)' if eff_2_on_1 < 1 else 'rgba(139, 148, 158, 0.15)'};
                border-radius: 12px;
                border: 2px solid {'#3fb950' if eff_2_on_1 > 1 else '#f85149' if eff_2_on_1 < 1 else '#8b949e'};
            ">
                <div style="color: #8b949e; font-size: 0.8rem; margin-bottom: 5px;">Damage to {name1}</div>
                <div style="color: {'#3fb950' if eff_2_on_1 > 1 else '#f85149' if eff_2_on_1 < 1 else '#fff'}; font-size: 1.8rem; font-weight: 800;">
                    {eff_2_on_1}x {'🔥' if eff_2_on_1 > 1 else '❄️' if eff_2_on_1 < 1 else ''}
                </div>
            </div>
        </div>
    </div>
    
    <!-- Stat Comparison Bars -->
    <div style="
        margin-top: 30px;
        background: rgba(22, 27, 34, 0.9);
        border-radius: 16px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <h3 style="color: #fff; margin: 0 0 20px 0; text-align: center; font-size: 1.1rem;">📊 HEAD-TO-HEAD STATS</h3>
        
        <!-- HP -->
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: {'#3fb950' if stats1['hp'] >= stats2['hp'] else '#8b949e'}; font-size: 0.9rem; font-weight: 600; min-width: 40px;">{stats1['hp']}</span>
                <span style="color: #f85149; font-size: 0.85rem; font-weight: 600;">HP</span>
                <span style="color: {'#3fb950' if stats2['hp'] >= stats1['hp'] else '#8b949e'}; font-size: 0.9rem; font-weight: 600; min-width: 40px; text-align: right;">{stats2['hp']}</span>
            </div>
            <div style="display: flex; height: 10px; border-radius: 5px; overflow: hidden; background: #21262d;">
                <div style="width: 50%; display: flex; justify-content: flex-end;">
                    <div style="width: {min(stats1['hp']/180*100, 100)}%; background: linear-gradient(90deg, rgba(88, 166, 255, 0.3), #58a6ff); border-radius: 5px 0 0 5px;"></div>
                </div>
                <div style="width: 2px; background: #fff;"></div>
                <div style="width: 50%; display: flex;">
                    <div style="width: {min(stats2['hp']/180*100, 100)}%; background: linear-gradient(90deg, #f85149, rgba(248, 81, 73, 0.3)); border-radius: 0 5px 5px 0;"></div>
                </div>
            </div>
        </div>
        
        <!-- Attack -->
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: {'#3fb950' if stats1['attack'] >= stats2['attack'] else '#8b949e'}; font-size: 0.9rem; font-weight: 600; min-width: 40px;">{stats1['attack']}</span>
                <span style="color: #f0883e; font-size: 0.85rem; font-weight: 600;">ATTACK</span>
                <span style="color: {'#3fb950' if stats2['attack'] >= stats1['attack'] else '#8b949e'}; font-size: 0.9rem; font-weight: 600; min-width: 40px; text-align: right;">{stats2['attack']}</span>
            </div>
            <div style="display: flex; height: 10px; border-radius: 5px; overflow: hidden; background: #21262d;">
                <div style="width: 50%; display: flex; justify-content: flex-end;">
                    <div style="width: {min(stats1['attack']/180*100, 100)}%; background: linear-gradient(90deg, rgba(88, 166, 255, 0.3), #58a6ff); border-radius: 5px 0 0 5px;"></div>
                </div>
                <div style="width: 2px; background: #fff;"></div>
                <div style="width: 50%; display: flex;">
                    <div style="width: {min(stats2['attack']/180*100, 100)}%; background: linear-gradient(90deg, #f85149, rgba(248, 81, 73, 0.3)); border-radius: 0 5px 5px 0;"></div>
                </div>
            </div>
        </div>
        
        <!-- Defense -->
        <div style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: {'#3fb950' if stats1['defense'] >= stats2['defense'] else '#8b949e'}; font-size: 0.9rem; font-weight: 600; min-width: 40px;">{stats1['defense']}</span>
                <span style="color: #58a6ff; font-size: 0.85rem; font-weight: 600;">DEFENSE</span>
                <span style="color: {'#3fb950' if stats2['defense'] >= stats1['defense'] else '#8b949e'}; font-size: 0.9rem; font-weight: 600; min-width: 40px; text-align: right;">{stats2['defense']}</span>
            </div>
            <div style="display: flex; height: 10px; border-radius: 5px; overflow: hidden; background: #21262d;">
                <div style="width: 50%; display: flex; justify-content: flex-end;">
                    <div style="width: {min(stats1['defense']/180*100, 100)}%; background: linear-gradient(90deg, rgba(88, 166, 255, 0.3), #58a6ff); border-radius: 5px 0 0 5px;"></div>
                </div>
                <div style="width: 2px; background: #fff;"></div>
                <div style="width: 50%; display: flex;">
                    <div style="width: {min(stats2['defense']/180*100, 100)}%; background: linear-gradient(90deg, #f85149, rgba(248, 81, 73, 0.3)); border-radius: 0 5px 5px 0;"></div>
                </div>
            </div>
        </div>
        
        <!-- Speed -->
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: {'#3fb950' if stats1['speed'] >= stats2['speed'] else '#8b949e'}; font-size: 0.9rem; font-weight: 600; min-width: 40px;">{stats1['speed']}</span>
                <span style="color: #db61a2; font-size: 0.85rem; font-weight: 600;">SPEED</span>
                <span style="color: {'#3fb950' if stats2['speed'] >= stats1['speed'] else '#8b949e'}; font-size: 0.9rem; font-weight: 600; min-width: 40px; text-align: right;">{stats2['speed']}</span>
            </div>
            <div style="display: flex; height: 10px; border-radius: 5px; overflow: hidden; background: #21262d;">
                <div style="width: 50%; display: flex; justify-content: flex-end;">
                    <div style="width: {min(stats1['speed']/180*100, 100)}%; background: linear-gradient(90deg, rgba(88, 166, 255, 0.3), #58a6ff); border-radius: 5px 0 0 5px;"></div>
                </div>
                <div style="width: 2px; background: #fff;"></div>
                <div style="width: 50%; display: flex;">
                    <div style="width: {min(stats2['speed']/180*100, 100)}%; background: linear-gradient(90deg, #f85149, rgba(248, 81, 73, 0.3)); border-radius: 0 5px 5px 0;"></div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- AI Analysis Section -->
    <div style="
        margin-top: 25px;
        background: rgba(22, 27, 34, 0.9);
        border-radius: 16px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <h3 style="color: #58a6ff; margin: 0 0 15px 0; font-size: 1.1rem;">🤖 AI Analysis</h3>
        <p style="color: #c9d1d9; line-height: 1.6; margin: 0;">{ai_analysis}</p>
    </div>
    
    <!-- Verdict Section -->
    <div style="
        margin-top: 25px;
        background: linear-gradient(135deg, rgba(255, 203, 5, 0.15), rgba(255, 107, 53, 0.15));
        border-radius: 16px;
        padding: 25px;
        border: 2px solid rgba(255, 203, 5, 0.3);
        text-align: center;
    ">
        <h3 style="color: #ffcb05; margin: 0 0 10px 0; font-size: 1.2rem;">🎯 VERDICT</h3>
        <p style="color: #fff; font-size: 1.1rem; font-weight: 600; margin: 0;">{verdict}</p>
    </div>
</div>
    """
    
    # Return with the comparison in the description slot, hide sprite and cry sections
    # Returns: sprite, name, type, stats, desc, counter, extra, cry_url, current_pokemon, history, favorites, cry_section, cry_audio
    return gr.update(value=None, visible=False), "", "", "", comparison_html, "", "", "", pokemon1, get_history_html(), get_favorites_html(), "", gr.update(visible=False)

def random_pokemon_handler(show_shiny):
    """Handle random Pokémon button"""
    random_name = get_random_pokemon()
    return chat_response(random_name, show_shiny)

def handle_favorite_toggle(pokemon_name):
    """Handle adding/removing favorites"""
    if pokemon_name:
        msg = toggle_favorite(pokemon_name)
        return msg, get_favorites_html()
    return "No Pokémon selected!", get_favorites_html()

def history_click(pokemon_name, show_shiny):
    """Handle clicking on history item"""
    return chat_response(pokemon_name, show_shiny)

# ============== BUILD GRADIO UI ==============

with gr.Blocks(title="Pokémon Battle Assistant") as demo:
    
    # State for current Pokémon
    current_pokemon = gr.State("")
    
    # CSS Styling
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
            <p style="color: #58a6ff; font-size: 0.9rem; margin-top: 8px;">
                Chat naturally about anything Pokémon! I remember our conversation 🧠
            </p>
        </div>
    """)
    
    with gr.Row(equal_height=False):
        # Left side - Search Panel
        with gr.Column(scale=1, min_width=300):
            gr.HTML('''
                <div class="card-section">
                    <div class="section-header">
                        <span style="font-size: 1.2rem;">💬</span>
                        <span style="color: #ffffff; font-weight: 600; font-size: 1.1rem;">Chat with PokéAssistant</span>
                    </div>
                </div>
            ''')
            user_input = gr.Textbox(
                placeholder="Ask me anything about Pokémon! e.g., 'Who's your favorite starter?' or 'Help me build a team'",
                label="",
                show_label=False,
                container=False,
                lines=2
            )
            
            with gr.Row():
                search_btn = gr.Button("💬 SEND", variant="primary", size="lg")
                random_btn = gr.Button("🎲", variant="secondary", size="lg")
                new_chat_btn = gr.Button("🔄", variant="secondary", size="lg")
            
            # Shiny toggle
            shiny_toggle = gr.Checkbox(label="✨ Show Shiny", value=False)
            
            # Favorite button
            favorite_btn = gr.Button("❤️ Add to Favorites", variant="secondary", size="sm")
            favorite_status = gr.Markdown("")
            
            gr.HTML('<p style="color: #8b949e; margin: 24px 0 12px; font-size: 0.85rem; font-weight: 500;">QUICK PICKS</p>')
            with gr.Row():
                btn1 = gr.Button("🔥 Charizard", size="sm", variant="secondary")
                btn2 = gr.Button("⚡ Pikachu", size="sm", variant="secondary")
            with gr.Row():
                btn3 = gr.Button("👻 Gengar", size="sm", variant="secondary")
                btn4 = gr.Button("🐉 Dragonite", size="sm", variant="secondary")
            with gr.Row():
                btn5 = gr.Button("🌊 Blastoise", size="sm", variant="secondary")
                btn6 = gr.Button("🍃 Venusaur", size="sm", variant="secondary")
            
            # Search History
            gr.HTML('<p style="color: #8b949e; margin: 24px 0 12px; font-size: 0.85rem; font-weight: 500;">📜 RECENT SEARCHES</p>')
            history_output = gr.HTML(get_history_html())
            
            # Favorites
            gr.HTML('<p style="color: #8b949e; margin: 24px 0 12px; font-size: 0.85rem; font-weight: 500;">❤️ FAVORITES</p>')
            favorites_output = gr.HTML(get_favorites_html())
            
            # Example queries - more conversational
            gr.HTML('''
                <div style="margin-top: 20px; padding: 15px; background: rgba(22, 27, 34, 0.9); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                    <p style="color: #58a6ff; font-weight: 600; margin-bottom: 10px;">💬 Chat naturally:</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"Hey! What's a good starter for beginners?"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"I love Eevee! What should I evolve it into?"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"Help me build a competitive team"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"Who would win: Mewtwo or Arceus?"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"What's your favorite Pokémon?"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"I'm stuck on the Elite Four, any tips?"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"Tell me something cool about Gengar"</p>
                </div>
            ''')
        
        # Right side - Results Panel
        with gr.Column(scale=2, min_width=500):
            gr.HTML('''
                <div class="card-section" style="margin-bottom: 0;">
                    <div class="section-header">
                        <span style="font-size: 1.2rem;">📊</span>
                        <span style="color: #ffffff; font-weight: 600; font-size: 1.1rem;">Pokémon Data</span>
                    </div>
                </div>
            ''')
            
            # Pokemon info row (hidden during comparison)
            with gr.Row(equal_height=True) as pokemon_info_row:
                sprite_output = gr.Image(
                    label="",
                    show_label=False,
                    height=220,
                    width=220,
                    container=False
                )
                with gr.Column():
                    name_output = gr.Markdown("", elem_id="pokemon-name")
                    type_output = gr.HTML("")
                    stats_output = gr.HTML("")
            
            # Cry audio player section
            cry_section = gr.HTML('<p style="color: #8b949e; margin: 10px 0 5px; font-size: 0.85rem;">🔊 Pokémon Cry</p>')
            cry_audio = gr.Audio(label="", show_label=False, type="filepath", visible=True)
            cry_url_hidden = gr.Textbox(visible=False)
            
            # Description / Comparison output (HTML for comparison, Markdown for description)
            desc_output = gr.HTML("")
            
            # Counters
            gr.HTML('''
                <div style="margin-top: 20px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <span style="font-size: 1.1rem;">⚔️</span>
                        <span style="color: #f85149; font-weight: 600;">Suggested Counters</span>
                    </div>
                </div>
            ''')
            counter_output = gr.HTML("")
            
            # Extra info (moves, abilities, evolution, etc.)
            gr.HTML('''
                <div style="margin-top: 20px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <span style="font-size: 1.1rem;">💡</span>
                        <span style="color: #ffcb05; font-weight: 600;">AI Insights</span>
                    </div>
                </div>
            ''')
            extra_output = gr.Markdown("")
    
    # Outputs list - includes visibility controls for sprite, cry section
    outputs = [sprite_output, name_output, type_output, stats_output, desc_output, counter_output, extra_output, cry_url_hidden, current_pokemon, history_output, favorites_output, cry_section, cry_audio]
    
    # Event handlers
    search_btn.click(fn=chat_response, inputs=[user_input, shiny_toggle], outputs=outputs)
    user_input.submit(fn=chat_response, inputs=[user_input, shiny_toggle], outputs=outputs)
    
    # Random Pokémon button
    random_btn.click(fn=random_pokemon_handler, inputs=[shiny_toggle], outputs=outputs)
    
    # New Chat button - clears conversation history
    def handle_new_chat():
        message = clear_conversation_history()
        welcome_html = f'''
        <div style="padding: 25px; background: rgba(22, 27, 34, 0.9); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <span style="font-size: 3rem;">👋</span>
            </div>
            <h2 style="color: #ffcb05; text-align: center; margin-bottom: 15px;">Welcome to PokéAssistant!</h2>
            <p style="color: #c9d1d9; text-align: center; line-height: 1.8;">
                {message}<br><br>
                I'm your intelligent Pokémon companion! I can help you with:
            </p>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 20px;">
                <div style="background: rgba(255,203,5,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                    <span style="font-size: 1.5rem;">🎮</span>
                    <p style="color: #ffcb05; margin: 5px 0 0; font-size: 0.9rem;">Team Building</p>
                </div>
                <div style="background: rgba(248,81,73,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                    <span style="font-size: 1.5rem;">⚔️</span>
                    <p style="color: #f85149; margin: 5px 0 0; font-size: 0.9rem;">Battle Strategy</p>
                </div>
                <div style="background: rgba(88,166,255,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                    <span style="font-size: 1.5rem;">📚</span>
                    <p style="color: #58a6ff; margin: 5px 0 0; font-size: 0.9rem;">Pokémon Info</p>
                </div>
                <div style="background: rgba(59,185,80,0.1); padding: 12px; border-radius: 10px; text-align: center;">
                    <span style="font-size: 1.5rem;">💬</span>
                    <p style="color: #3fb950; margin: 5px 0 0; font-size: 0.9rem;">Casual Chat</p>
                </div>
            </div>
            <p style="color: #8b949e; text-align: center; margin-top: 20px; font-size: 0.9rem;">
                Just type naturally - I understand context and remember our conversation!
            </p>
        </div>
        '''
        return None, "# 🤖 PokéAssistant", "", "", welcome_html, "", "", "", "", get_history_html(), get_favorites_html(), "", gr.update(visible=False)
    
    new_chat_btn.click(fn=handle_new_chat, inputs=[], outputs=outputs)
    
    # Favorite button
    favorite_btn.click(fn=handle_favorite_toggle, inputs=[current_pokemon], outputs=[favorite_status, favorites_output])
    
    # Quick pick buttons
    btn1.click(fn=lambda s: chat_response("Charizard", s), inputs=[shiny_toggle], outputs=outputs)
    btn2.click(fn=lambda s: chat_response("Pikachu", s), inputs=[shiny_toggle], outputs=outputs)
    btn3.click(fn=lambda s: chat_response("Gengar", s), inputs=[shiny_toggle], outputs=outputs)
    btn4.click(fn=lambda s: chat_response("Dragonite", s), inputs=[shiny_toggle], outputs=outputs)
    btn5.click(fn=lambda s: chat_response("Blastoise", s), inputs=[shiny_toggle], outputs=outputs)
    btn6.click(fn=lambda s: chat_response("Venusaur", s), inputs=[shiny_toggle], outputs=outputs)
    
    # Update cry audio when URL changes
    def update_cry(url):
        if url and url.startswith('http'):
            return url
        return None
    
    cry_url_hidden.change(fn=update_cry, inputs=[cry_url_hidden], outputs=[cry_audio])

# Launch
if __name__ == "__main__":
    demo.launch(share=True)
