# ⚡ Pokémon Battle Assistant

A smart Pokémon battle assistant chatbot powered by **PokeAPI** and **Google Gemini AI**. Get detailed Pokémon stats, type matchups, counter suggestions, and AI-generated battle tips!

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Gradio](https://img.shields.io/badge/Gradio-UI-orange?logo=gradio)
![Gemini](https://img.shields.io/badge/Google-Gemini_AI-red?logo=google)

## 🎯 Overview

This chatbot helps Pokémon trainers by providing:

- **📊 Pokémon Stats** - View base stats (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed) with visual stat bars
- **🏷️ Type Information** - See Pokémon types with color-coded badges
- **📖 Pokédex Descriptions** - Read official Pokémon descriptions from the games
- **⚔️ Counter Suggestions** - Get recommended Pokémon that are effective against your target
- **💡 AI Battle Tips** - Receive intelligent battle advice powered by Google Gemini AI

## ✨ Features

- Clean, modern dark-themed UI built with Gradio
- Real-time Pokémon data from PokeAPI
- Type effectiveness calculations for counter suggestions
- Quick pick buttons for popular Pokémon
- AI-powered battle strategy explanations
- Shareable public link option

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

## 🎮 Usage

1. **Search for a Pokémon** - Type any Pokémon name in the search box and click "ANALYZE" or press Enter
2. **Use Quick Picks** - Click on any of the preset Pokémon buttons for instant analysis
3. **View Results** - See the Pokémon's image, stats, description, counters, and AI battle tips

## 📁 Project Structure

```
poke-master/
├── main.py           # Main application file
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (create this)
├── .gitignore        # Git ignore file
├── README.md         # This file
└── venv/             # Virtual environment (optional)
```

## 🔧 Technologies Used

- **[Gradio](https://gradio.app/)** - Web UI framework
- **[PokeAPI](https://pokeapi.co/)** - Pokémon data API
- **[Google Gemini AI](https://ai.google.dev/)** - AI-powered battle tips
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - Environment variable management

## 📝 License

This project is for educational purposes. Pokémon and all related names are trademarks of Nintendo/Game Freak.

---

Made with ❤️ for Pokémon trainers everywhere!

