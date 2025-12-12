# ⚡ Pokémon Battle Assistant

A smart Pokémon battle assistant chatbot powered by **PokeAPI** and **Google Gemini AI**. Get detailed Pokémon stats, type matchups, counter suggestions, AI-generated battle tips, and much more!

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange?logo=gradio)
![Gemini](https://img.shields.io/badge/Google-Gemini_AI-red?logo=google)

## 🎯 Overview

This chatbot helps Pokémon trainers by providing:

- **📊 Pokémon Stats** - View base stats (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed) with visual stat bars
- **🏷️ Type Information** - See Pokémon types with color-coded badges
- **📖 Pokédex Descriptions** - Read official Pokémon descriptions from the games
- **⚔️ Counter Suggestions** - Get recommended Pokémon that are effective against your target
- **💡 AI Battle Tips** - Receive intelligent battle advice powered by Google Gemini AI
- **🔊 Pokémon Cries** - Listen to authentic Pokémon sound effects

## ✨ Features

### Core Features
- Clean, modern dark-themed UI built with Gradio
- Real-time Pokémon data from PokeAPI (Gen 1-8, 898+ Pokémon)
- Type effectiveness calculations for counter suggestions
- Quick pick buttons for popular Pokémon
- AI-powered battle strategy explanations
- Shareable public link option

### Advanced Features
- **⚔️ Pokémon Comparison** - Compare two Pokémon side-by-side with detailed stat breakdowns, type matchups, and AI analysis (e.g., "Compare Charizard vs Blastoise")
- **🎯 Move Recommendations** - Get AI-suggested optimal movesets (e.g., "What moves should Pikachu learn?")
- **⚡ Ability Information** - View detailed ability descriptions including hidden abilities (e.g., "What are Gengar's abilities?")
- **🔄 Evolution Chains** - See complete evolution paths (e.g., "How does Eevee evolve?")
- **📍 Location Data** - Find where to catch Pokémon in the games (e.g., "Where can I catch Eevee?")
- **🎲 Fun Trivia** - Discover interesting facts about any Pokémon (e.g., "Tell me trivia about Mewtwo")
- **🎮 Battle Scenarios** - Get strategic advice for specific matchups (e.g., "My Pikachu is facing Onix")
- **✨ Shiny Sprites** - Toggle to view shiny Pokémon variants
- **🎲 Random Pokémon** - Discover new Pokémon with the random button
- **❤️ Favorites** - Save your favorite Pokémon for quick access
- **📜 Search History** - Quick access to recently searched Pokémon
- **🤖 Natural Language Q&A** - Ask general Pokémon questions

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/poke-master.git
   cd poke-master
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the chatbot**
   
   Open your browser and go to the local URL shown in the terminal (usually `http://127.0.0.1:7860`)
   
   A shareable public link will also be generated automatically.

## 🎮 Usage

### Basic Search
- Type any Pokémon name in the search box and click "ANALYZE" or press Enter
- Use Quick Pick buttons for instant analysis of popular Pokémon
- Click the 🎲 button for a random Pokémon

### Example Queries

| Query Type | Example |
|------------|---------|
| Basic Info | `Pikachu` |
| Comparison | `Compare Charizard vs Blastoise` |
| Movesets | `What moves should Pikachu learn?` |
| Abilities | `What are Gengar's abilities?` |
| Evolution | `How does Eevee evolve?` |
| Location | `Where can I catch Eevee?` |
| Trivia | `Tell me trivia about Mewtwo` |
| Battle Scenario | `My Pikachu is facing Onix` |
| Height/Weight | `How tall is Charizard?` |
| General Q&A | `What is the strongest dragon type?` |

### Features
- **✨ Shiny Toggle** - Enable to see shiny sprite variants
- **❤️ Favorites** - Click to save Pokémon to your favorites list
- **🔊 Pokémon Cry** - Listen to the Pokémon's authentic cry sound

## 📁 Project Structure

```
poke-master/
├── main.py           # Main application file with all logic and UI
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (create this)
├── .gitignore        # Git ignore file
├── README.md         # This file
└── venv/             # Virtual environment (optional)
```

## 🔧 Technologies Used

- **[Gradio](https://gradio.app/)** - Web UI framework (v4.0+)
- **[PokeAPI](https://pokeapi.co/)** - Comprehensive Pokémon data API
- **[Google Gemini AI](https://ai.google.dev/)** - AI-powered battle tips and analysis (gemini-1.5-flash)
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - Environment variable management
- **[Requests](https://requests.readthedocs.io/)** - HTTP library for API calls

## 🎨 Type Color Reference

The app uses official Pokémon type colors for badges:

| Type | Color |
|------|-------|
| Normal | #A8A878 |
| Fire | #F08030 |
| Water | #6890F0 |
| Electric | #F8D030 |
| Grass | #78C850 |
| Ice | #98D8D8 |
| Fighting | #C03028 |
| Poison | #A040A0 |
| Ground | #E0C068 |
| Flying | #A890F0 |
| Psychic | #F85888 |
| Bug | #A8B820 |
| Rock | #B8A038 |
| Ghost | #705898 |
| Dragon | #7038F8 |
| Dark | #705848 |
| Steel | #B8B8D0 |
| Fairy | #EE99AC |

## 📝 License

This project is for educational purposes. Pokémon and all related names are trademarks of Nintendo/Game Freak.

---

Made with ❤️ for Pokémon trainers everywhere!
