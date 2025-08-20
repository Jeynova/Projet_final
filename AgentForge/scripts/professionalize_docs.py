#!/usr/bin/env python3
"""
Script de professionnalisation de la documentation AgentForge
Supprime tous les emojis et réécrit dans un style technique professionnel
"""

import os
import re
from pathlib import Path

def clean_emojis_and_style(text):
    """Supprime emojis et transforme en style professionnel"""
    
    # Mapping des expressions informelles vers style professionnel
    replacements = {
        # Emojis et symboles
        r'[🎯🚀✨🖥️🤖💾🔄📊🎮🖥️🎨🔧🏗️📋📡🧪🔍⚡📈🛡️🔄💡🎯🏆📝📚🚨❌🔧💻⚙️📄🤝🎉⭐💎🌟🎊🔥💥⚡🌈🎪🎭🎸🎵🎶🎤🎮🎲🎯🎪🎨🎬🎥📹📷📸🔍🔎📊📈📉📋📌📍📎📝✏️✒️🖊️🖋️🖌️🖍️📐📏📖📗📘📙📔📒📚🗂️🗄️🗃️📂📁💼👔💻🖥️🖨️⌨️🖱️💾💿📀💽💻📱☎️📞📟📠📺📻🎙️🎚️🎛️⏰⏱️⏲️🕰️⌛⏳📡🔋🔌💡🔦🕯️🪔🧯🛢️💸💰💴💵💶💷🪙💳💎⚖️🧰🔧🔨⚒️🛠️⛏️🔩⚙️🧱⛓️🧲🔫💣🧨🪓🔪🗡️⚔️🛡️🚬⚰️🪦⚱️🏺🔮📿🧿📡🔭🔬🕳️🩹🩺💊💉🩸🧬🦠🧫🧪🌡️🧹🧺🧻🚽🚰🚿🛁🛀🧴🧷🧸🧵🪡🧶🪢👗👔👕👖🧣🧤🧥🧦👠👡🩰👢👞👟🥾🥿👒🎩🎓⛑️📿👑💍👝👛👜💼🎒👓🕶️🥽⚗️🔬🔭📏📐⚖️🧮🩺🔧🔨🪛🔩⚙️🧰⚒️🛠️⚱️💣🪓🔪🗡️⚔️🛡️🔫🏹🪃🪚🔗⛓️🧲⚖️⚗️⚰️⚱️]': '',
        
        # Expressions informelles
        r'\*\*([^*]+)\*\*': r'\1',  # Supprime markdown bold
        r'✅\s*': '',
        r'❌\s*': '',
        r'⚠️\s*': '',
        r'ℹ️\s*': '',
        
        # Titre avec emojis
        r'^#+ [🎯🚀✨🖥️🤖💾🔄📊🎮🖥️🎨🔧🏗️📋📡🧪🔍⚡📈🛡️🔄💡🎯🏆📝📚🚨❌🔧💻⚙️📄🤝🎉]+\s*(.+)': r'# \1',
        
        # Expressions enthousiastes
        r'PARFAIT\s*!': 'Validé',
        r'EXCELLENT\s*!': 'Validé',
        r'FANTASTIQUE\s*!': 'Réussi',
        r'SUCCÈS TOTAL\s*!': 'Succès complet',
        r'BINGO\s*!': 'Confirmation',
        r'VICTOIRE TOTALE\s*!': 'Résultat positif',
        
        # Style chatty
        r'Allez-y[,.]?\s*testez\s*!': 'Procédez aux tests.',
        r'Voulez-vous.+\?': '',
        r'C\'est\s+(génial|super|parfait|excellent)': 'Ceci est satisfaisant',
        r'Vous devriez voir': 'Le résultat attendu est',
        r'Maintenant\s*[,.]?\s*': '',
        r'Cette fois[,.]?\s*': '',
        r'Allez[,.]?\s*': '',
        
        # Bullet points avec emojis
        r'- ✅': '-',
        r'- ❌': '-',
        r'- ⚠️': '-',
        r'- 🔧': '-',
        r'- 📊': '-',
        
        # Expressions de debug
        r'DEBUG\s*(Flask|Ollama|LLM):': r'LOG \1:',
        
        # Multiple espaces et ligne vides
        r'\n\s*\n\s*\n+': r'\n\n',
        r'  +': ' ',
    }
    
    # Appliquer toutes les transformations
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.IGNORECASE)
    
    return text

def process_documentation_files():
    """Traite tous les fichiers de documentation"""
    
    files_to_process = [
        "README.md",
        "DOCUMENTATION_ORAL.md", 
        "NOTES_VALIDATION.md",
        "RAPPORT_FINAL_ORAL.md",
        "METRIQUES_ORAL.md",
        "ARCHITECTURE.md"
    ]
    
    base_dir = Path(__file__).parent.parent
    
    processed_files = []
    
    for file_name in files_to_process:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"Traitement de {file_name}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Nettoyer le contenu
            cleaned_content = clean_emojis_and_style(original_content)
            
            # Sauvegarder si modifié
            if cleaned_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                processed_files.append(file_name)
                print(f"  → {file_name} professionalisé")
            else:
                print(f"  → {file_name} déjà propre")
    
    return processed_files

def create_professional_summary():
    """Crée un résumé professionnel du projet"""
    
    summary = """# AgentForge v2.0 - Résumé Technique

## Description
AgentForge v2.0 est un système multi-agent de génération automatique de projets développé en Python. Le système combine l'intelligence artificielle (LLM) avec des algorithmes déterministes pour assurer une génération fiable de projets d'applications web.

## Architecture Technique
- **Orchestration**: LangGraph pour coordination multi-agent  
- **Interface**: Flask avec sélection LLM en temps réel
- **Base de données**: SQLite pour persistance des projets
- **Templates**: Jinja2 pour génération de code structuré
- **LLM Support**: Ollama local et OpenAI API

## Agents Spécialisés
1. **Spec Extractor**: Analyse du langage naturel vers structures de données
2. **Tech Selector**: Recommandations technologiques automatisées
3. **Planner**: Sélection de templates projet appropriés
4. **Scaffolder**: Génération de structure de fichiers
5. **Codegen**: Production de code métier et tests
6. **Eval Agent**: Validation et scoring qualité

## Résultats
- Taux de succès: 100% (fallbacks garantis)
- Templates supportés: FastAPI + PostgreSQL/SQLite
- Code généré: Modèles ORM, routes CRUD, tests unitaires
- Containerisation: Docker et Docker Compose automatiques
- CI/CD: GitHub Actions configuré automatiquement

## Technologies
- Python 3.10+, Flask 3.0, LangGraph 0.2, SQLAlchemy 2.0
- Pydantic 2.8, Ollama, OpenAI API, Jinja2 Templates
- Docker, PostgreSQL, SQLite, Pytest, GitHub Actions

---
Documentation technique professionnelle - AgentForge v2.0
"""
    
    with open("RESUME_TECHNIQUE.md", "w", encoding='utf-8') as f:
        f.write(summary)
    
    print("Résumé technique créé: RESUME_TECHNIQUE.md")

if __name__ == "__main__":
    print("Professionnalisation de la documentation AgentForge v2.0...")
    print("=" * 60)
    
    processed = process_documentation_files()
    create_professional_summary()
    
    print(f"\nTerminé. {len(processed)} fichiers traités:")
    for file_name in processed:
        print(f"  - {file_name}")
    
    print("\nDocumentation maintenant dans un style technique professionnel.")
