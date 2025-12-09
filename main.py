# app.py
import os
import requests
import google.generativeai as genai
import gradio as gr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY in your .env file!")

genai.configure(api_key=GEMINI_API_KEY)

# Type effectiveness (simplified)
type_chart = {
    'fire': {'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5},
    'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2},
    'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'flying': 0.5, 'bug': 0.5, 'dragon': 0.5, 'steel': 0.5},
    'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2},
    'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
    'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'rock': 2, 'steel': 2, 'fairy': 0.5},
    'poison': {'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'steel': 0},
    'ground': {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2},
    'flying': {'electric': 0.5, 'ice': 0.5, 'rock': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2},
    'psychic': {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'steel': 0.5},
    'bug': {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5, 'steel': 0.5, 'fairy': 0.5},
    'rock': {'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2, 'steel': 0.5},
    'ghost': {'psychic': 2, 'ghost': 2, 'dark': 0.5},
    'dragon': {'dragon': 2, 'steel': 0.5, 'fairy': 0},
    'dark': {'psychic': 2, 'ghost': 2, 'dark': 0.5, 'fairy': 0.5},
    'steel': {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2, 'rock': 2, 'steel': 0.5, 'fairy': 2},
    'fairy': {'fighting': 2, 'dragon': 2, 'dark': 2, 'poison': 0.5, 'steel': 0.5},
    'normal': {'rock': 0.5, 'ghost': 0, 'steel': 0.5}
}

# Helper: Get Pokémon data
def get_pokemon_data(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}", timeout=5)
        res.raise_for_status()
        return res.json()
    except:
        return None

# Helper: Get Pokémon description
def get_pokemon_description(name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{name.lower()}", timeout=5)
        res.raise_for_status()
        data = res.json()
        for entry in data['flavor_text_entries']:
            if entry['language']['name'] == 'en':
                return entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')
        return "No description available."
    except:
        return "No description available."

# Helper: Find strong counter types
def find_counter_types(target_types):
    effective_types = set()
    for t in target_types:
        for attacker_type, matchups in type_chart.items():
            if matchups.get(t, 1) > 1:
                effective_types.add(attacker_type)
    return list(effective_types)[:3]

# Helper: Suggest example Pokémon
def suggest_counter_pokemon(counter_types):
    examples = {
        'water': 'Blastoise',
        'electric': 'Raichu',
        'grass': 'Venusaur',
        'ice': 'Articuno',
        'fighting': 'Lucario',
        'ground': 'Garchomp',
        'flying': 'Dragonite',
        'rock': 'Tyranitar',
        'steel': 'Metagross',
        'fairy': 'Togekiss',
        'psychic': 'Alakazam',
        'bug': 'Scizor'
    }
    suggestions = []
    for t in counter_types:
        if t in examples:
            suggestions.append(examples[t])
    return suggestions[:3]

# Helper: Ask Gemini for explanation
def get_gemini_explanation(attacker, defender):
    prompt = (
        f"You are a Pokémon battle expert. Explain in one short sentence "
        f"why {attacker} is a good counter to {defender}. "
        f"Focus on type matchups and common moves. Be concise and factual."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt, safety_settings={
            "HARM_CATEGORY_HARASSMENT": "block_none",
            "HARM_CATEGORY_HATE_SPEECH": "block_none",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "block_none",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "block_none"
        })
        return response.text.strip()
    except Exception as e:
        return f"💡 {attacker} counters {defender} through type advantage."

# Type colors for badges
TYPE_COLORS = {
    'normal': '#A8A878', 'fire': '#F08030', 'water': '#6890F0', 'electric': '#F8D030',
    'grass': '#78C850', 'ice': '#98D8D8', 'fighting': '#C03028', 'poison': '#A040A0',
    'ground': '#E0C068', 'flying': '#A890F0', 'psychic': '#F85888', 'bug': '#A8B820',
    'rock': '#B8A038', 'ghost': '#705898', 'dragon': '#7038F8', 'dark': '#705848',
    'steel': '#B8B8D0', 'fairy': '#EE99AC'
}

# Main chat function - returns structured data
def chat_response(user_input):
    if not user_input.strip():
        return None, "Please enter a Pokémon name!", "", "", "", ""

    # Extract Pokémon name
    words = user_input.lower().split()
    known = ['pikachu', 'charizard', 'blastoise', 'venusaur', 'dragonite', 'gengar', 
             'tyranitar', 'metagross', 'lucario', 'garchomp', 'mewtwo', 'mew', 'eevee',
             'snorlax', 'gyarados', 'lapras', 'articuno', 'zapdos', 'moltres']
    pokemon_name = None
    for word in words:
        if word in known:
            pokemon_name = word
            break
    if not pokemon_name:
        pokemon_name = words[0]

    # Get data
    data = get_pokemon_data(pokemon_name)
    if not data:
        return None, f"❌ Pokémon '{pokemon_name}' not found!", "", "", "", ""

    name = data['name'].capitalize()
    types = [t['type']['name'] for t in data['types']]
    
    # Create type badges HTML
    type_badges = " ".join([
        f'<span style="background: {TYPE_COLORS.get(t, "#888")}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85em; text-transform: uppercase; margin-right: 5px;">{t}</span>'
        for t in types
    ])
    
    stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
    hp, atk, defense = stats['hp'], stats['attack'], stats['defense']
    sp_atk, sp_def, speed = stats['special-attack'], stats['special-defense'], stats['speed']
    
    sprite = data['sprites']['other']['official-artwork']['front_default'] or data['sprites']['front_default']
    desc = get_pokemon_description(name)

    # Find counters
    counter_types = find_counter_types(types)
    counter_names = suggest_counter_pokemon(counter_types)
    
    # Counter badges
    counter_html = ""
    if counter_names:
        counter_html = " ".join([
            f'<span style="background: linear-gradient(135deg, #ee1515, #cc0000); color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; margin: 3px;">{c}</span>'
            for c in counter_names
        ])
    else:
        counter_html = '<span style="color: #888;">No specific counters found</span>'

    # Get Gemini explanation
    battle_tip = ""
    if counter_names:
        battle_tip = get_gemini_explanation(counter_names[0], name)

    # Stats bars HTML - Clean aligned design
    max_stat = 255
    stats_html = f"""
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

    return sprite, f"# {name}", type_badges, stats_html, desc, counter_html, battle_tip

# Build the Gradio UI
with gr.Blocks() as demo:
    
    # Inject CSS via HTML style tag - Clean dark theme with subtle texture
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
            
            /* Card styling */
            .card-section {
                background: rgba(22, 27, 34, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 16px;
            }
            
            /* Section headers */
            .section-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
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
                placeholder="Enter Pokémon name...",
                label="",
                show_label=False,
                container=False
            )
            search_btn = gr.Button("⚔️ ANALYZE", variant="primary", size="lg")
            
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
        
        # Right side - Results Panel
        with gr.Column(scale=2, min_width=500):
            # Pokemon Info Card
            gr.HTML('''
                <div class="card-section" style="margin-bottom: 0;">
                    <div class="section-header">
                        <span style="font-size: 1.2rem;">📊</span>
                        <span style="color: #ffffff; font-weight: 600; font-size: 1.1rem;">Pokémon Data</span>
                    </div>
                </div>
            ''')
            
            with gr.Row(equal_height=True):
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
            
            # Description Card
            gr.HTML('''
                <div style="margin-top: 20px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <span style="font-size: 1.1rem;">📖</span>
                        <span style="color: #58a6ff; font-weight: 600;">Description</span>
                    </div>
                </div>
            ''')
            desc_output = gr.Markdown("")
            
            # Counters Card  
            gr.HTML('''
                <div style="margin-top: 20px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <span style="font-size: 1.1rem;">⚔️</span>
                        <span style="color: #f85149; font-weight: 600;">Suggested Counters</span>
                    </div>
                </div>
            ''')
            counter_output = gr.HTML("")
            
            # AI Tip Card
            gr.HTML('''
                <div style="margin-top: 20px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <span style="font-size: 1.1rem;">💡</span>
                        <span style="color: #ffcb05; font-weight: 600;">AI Battle Tip</span>
                    </div>
                </div>
            ''')
            tip_output = gr.Markdown("")
    
    # Event handlers
    outputs = [sprite_output, name_output, type_output, stats_output, desc_output, counter_output, tip_output]
    
    search_btn.click(fn=chat_response, inputs=user_input, outputs=outputs)
    user_input.submit(fn=chat_response, inputs=user_input, outputs=outputs)
    
    # Quick pick buttons
    btn1.click(fn=lambda: "Charizard", outputs=user_input).then(fn=chat_response, inputs=user_input, outputs=outputs)
    btn2.click(fn=lambda: "Pikachu", outputs=user_input).then(fn=chat_response, inputs=user_input, outputs=outputs)
    btn3.click(fn=lambda: "Gengar", outputs=user_input).then(fn=chat_response, inputs=user_input, outputs=outputs)
    btn4.click(fn=lambda: "Dragonite", outputs=user_input).then(fn=chat_response, inputs=user_input, outputs=outputs)
    btn5.click(fn=lambda: "Blastoise", outputs=user_input).then(fn=chat_response, inputs=user_input, outputs=outputs)
    btn6.click(fn=lambda: "Venusaur", outputs=user_input).then(fn=chat_response, inputs=user_input, outputs=outputs)

# Launch
if __name__ == "__main__":
    demo.launch(share=True)