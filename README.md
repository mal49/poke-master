# ⚡ PokéAssistant

An intelligent Pokémon companion chatbot powered by **PokeAPI** and **Google Gemini AI**. Chat naturally with your AI assistant about Pokémon, get detailed stats, view beautiful sprites, and receive expert advice!

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Gradio](https://img.shields.io/badge/Gradio-4.0+-orange?logo=gradio)
![Gemini](https://img.shields.io/badge/Google-Gemini_AI-red?logo=google)

## 🎯 Overview

PokéAssistant is an intelligent chatbot that helps Pokémon trainers by providing:

- **💬 Natural Language Chat** - Ask questions in plain English and get intelligent responses
- **📊 Pokémon Stats** - View base stats (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed) with visual stat bars
- **🏷️ Type Information** - See Pokémon types with color-coded badges
- **💡 AI-Powered Responses** - Get expert advice and explanations powered by Google Gemini AI 2.0
- **🔊 Pokémon Cries** - Listen to authentic Pokémon sound effects
- **🌍 Multi-Language Support** - Available in English, Bahasa Melayu, and 中文 (Chinese)

## ✨ Features

### Core Features
- **Modern Chat Interface** - Clean, dark-themed UI built with Gradio
- **Real-time Pokémon Data** - Fetches live data from PokeAPI (898+ Pokémon)
- **Intelligent Conversation** - Maintains conversation context for natural interactions
- **Sentiment Analysis** - Detects user mood and adapts responses accordingly
- **Domain Guardrails** - Ensures conversations stay Pokémon-related
- **Shareable Public Link** - Instantly share your assistant with others

### Advanced Features
- **🌍 Multi-Language Support** - Switch between English 🇬🇧, Bahasa Melayu 🇲🇾, and 中文 🇨🇳
- **💬 Chat History** - View your conversation history with timestamps
- **🗑️ History Management** - Clear chat history when needed
- **✨ Shiny Sprites** - Toggle to view shiny Pokémon variants
- **🎲 Random Pokémon** - Discover new Pokémon with the random button
- **❤️ Favorites** - Save your favorite Pokémon for quick access
- **📜 Search History** - Quick access to recently searched Pokémon (up to 10)
- **🎨 Beautiful Visualizations** - Type badges with official colors and animated stat bars
- **🔊 Audio Support** - Listen to Pokémon cries from the official games
- **🤖 Context-Aware Responses** - AI remembers your conversation and favorite Pokémon

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

6. **Run the application**
   ```bash
   python main.py
   ```

7. **Access the chatbot**
   
   The application will launch with:
   - A local URL (usually `http://127.0.0.1:7860`)
   - A shareable public link for easy sharing
   
   Open either URL in your browser to start chatting!

## 🎮 Usage

### Getting Started
1. Enter your question or Pokémon name in the chat input box
2. Click **SEND** or press Enter to get a response
3. Use the **RANDOM** button to discover random Pokémon
4. Toggle **✨ Show Shiny** to view shiny sprite variants

### Language Selection
- Click **🇬🇧 English**, **🇲🇾 Bahasa Melayu**, or **🇨🇳 中文** to switch languages
- The entire interface and AI responses will adapt to your selected language

### Example Queries

| Query Type | Example |
|------------|---------|
| Basic Info | `Who is Garchomp?` or just `Pikachu` |
| Stats & Abilities | `What are Garchomp's stats?` or `What moves does it learn?` |
| Team Building | `Build a team` or `What's a good team?` |
| Comparisons | `Compare Charizard vs Blastoise` |
| Strategy | `How do I beat Garchomp?` |
| General Q&A | `What is the strongest dragon type?` or `Tell me about fire types` |

### Interactive Features
- **✨ Shiny Toggle** - Enable to see shiny sprite variants
- **❤️ Add to Favorites** - Click to save Pokémon to your favorites list
- **🎲 Random** - Click to discover a random Pokémon (1-898)
- **📜 Recent Searches** - Click on any Pokémon name in the history to view it again
- **💬 Chat History** - Scroll through your conversation history
- **🗑️ Clear History** - Remove all chat history to start fresh
- **🔊 Pokémon Cry** - Audio player appears automatically when viewing Pokémon

## 📁 Project Structure

```
poke-master/
├── main.py           # Main application file with all logic and UI
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (create this - not in repo)
├── .gitignore        # Git ignore file
├── README.md         # This file
└── venv/             # Virtual environment (optional, not in repo)
```

## 🔑 Environment Variables

Create a `.env` file in the project root with your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

**Getting a Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

## 🔧 Technologies Used

- **[Gradio](https://gradio.app/)** - Web UI framework (v4.0+)
- **[PokeAPI](https://pokeapi.co/)** - Comprehensive Pokémon data API
- **[Google Gemini AI](https://ai.google.dev/)** - AI-powered conversational responses (Gemini 2.5 Flash Lite)
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - Environment variable management
- **[Requests](https://requests.readthedocs.io/)** - HTTP library for API calls

## 🧠 How It Works

1. **Natural Language Processing** - The AI extracts Pokémon names from your natural language queries
2. **Real-time Data Fetching** - When a Pokémon is mentioned, data is fetched from PokeAPI
3. **Context Injection** - Pokémon stats, types, and abilities are injected into the AI prompt for accurate responses
4. **Conversation Memory** - The last 20 conversation turns are maintained for context-aware responses
5. **Sentiment Analysis** - User sentiment is detected (positive, neutral, frustrated, curious) to adapt responses
6. **Domain Guardrails** - Ensures all queries remain Pokémon-related

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
