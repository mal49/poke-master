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
    
    # Location
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

def get_gemini_qa(question):
    """Handle natural language Q&A about Pokémon with fallback"""
    prompt = (
        f"You are a Pokémon expert assistant. Answer this question about Pokémon: {question}\n"
        f"Be informative, accurate, and engaging. If the question is about game mechanics, lore, or strategy, "
        f"provide detailed but concise answers (3-5 sentences). Use emojis to make it fun!"
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        raise Exception("Empty response")
    except Exception as e:
        # Fallback response
        return f"🤔 I'm having trouble connecting to my knowledge base right now.\n\n**Your question:** {question}\n\n💡 **Tip:** Try searching for a specific Pokémon name to get detailed information from the PokéAPI database!"

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
    global search_history
    
    # Cry section HTML (visible for normal queries)
    cry_section_html = '<p style="color: #8b949e; margin: 10px 0 5px; font-size: 0.85rem;">🔊 Pokémon Cry</p>'
    
    if not user_input.strip():
        return None, "Please enter a Pokémon name or question!", "", "", "<p style='color: #8b949e;'>Enter a Pokémon name to see its description.</p>", "", "", "", "", get_history_html(), get_favorites_html(), cry_section_html, gr.update(visible=True)

    query_types = detect_query_types(user_input)
    
    # Handle comparison queries
    if 'comparison' in query_types:
        pokemon_pair = extract_two_pokemon(user_input)
        if pokemon_pair:
            return handle_comparison(pokemon_pair[0], pokemon_pair[1], show_shiny)
    
    # Handle general Q&A (no specific Pokémon mentioned)
    pokemon_name = extract_pokemon_name(user_input)
    
    if not pokemon_name:
        # Try to answer as a general Pokémon question
        if any(kw in user_input.lower() for kw in ['pokemon', 'pokémon', 'type', 'game', 'battle', 'how', 'what', 'why', 'who']):
            answer = get_gemini_qa(user_input)
            answer_html = f'<div style="padding: 20px; background: rgba(22, 27, 34, 0.9); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"><p style="color: #c9d1d9; line-height: 1.6; margin: 0;">{answer}</p></div>'
            return None, "# 🤖 Pokémon Assistant", "", "", answer_html, "", "", "", "", get_history_html(), get_favorites_html(), "", gr.update(visible=False)
        return None, "❌ No valid Pokémon name found!", "", "", "<p style='color: #f85149;'>Try entering a Pokémon name like 'Pikachu' or ask a Pokémon question.</p>", "", "", "", "", get_history_html(), get_favorites_html(), cry_section_html, gr.update(visible=True)

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
                <span style="color: #ffcb05;">⚡</span> Pokémon Battle Assistant <span style="color: #ffcb05;">⚡</span>
            </h1>
            <p style="color: #8b949e; font-size: 1.05rem;">
                Powered by <span style="color: #58a6ff;">PokeAPI</span> + <span style="color: #f85149;">Google Gemini AI</span>
            </p>
        </div>
    """)
    
    with gr.Row(equal_height=False):
        # Left side - Search Panel
        with gr.Column(scale=1, min_width=300):
            gr.HTML('''
                <div class="card-section">
                    <div class="section-header">
                        <span style="font-size: 1.2rem;">🔍</span>
                        <span style="color: #ffffff; font-weight: 600; font-size: 1.1rem;">Search Pokémon</span>
                    </div>
                </div>
            ''')
            user_input = gr.Textbox(
                placeholder="Enter Pokémon name, compare two, or ask a question...",
                label="",
                show_label=False,
                container=False
            )
            
            with gr.Row():
                search_btn = gr.Button("⚔️ ANALYZE", variant="primary", size="lg")
                random_btn = gr.Button("🎲", variant="secondary", size="lg")
            
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
            
            # Example queries
            gr.HTML('''
                <div style="margin-top: 20px; padding: 15px; background: rgba(22, 27, 34, 0.9); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                    <p style="color: #58a6ff; font-weight: 600; margin-bottom: 10px;">💡 Try asking:</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"Compare Charizard vs Blastoise"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"What moves should Pikachu learn?"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"Tell me trivia about Mewtwo"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"Where can I catch Eevee?"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"What are Gengar's abilities?"</p>
                    <p style="color: #8b949e; font-size: 0.85rem; margin: 5px 0;">"My Pikachu is facing Onix"</p>
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
