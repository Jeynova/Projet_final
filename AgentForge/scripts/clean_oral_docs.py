#!/usr/bin/env python3
"""
Script de nettoyage des documents oraux du repository Git
Supprime ou déplace les documents spécifiques à la présentation orale
"""

import os
import shutil
from pathlib import Path

def clean_oral_documents():
    """Supprime les documents oraux du repository public"""
    
    # Fichiers à supprimer complètement du git
    oral_files_to_remove = [
        "DOCUMENTATION_ORAL.md",
        "GUIDE_ORAL.md", 
        "NOTES_VALIDATION.md",
        "METRIQUES_ORAL.md",
        "RAPPORT_FINAL_ORAL.md",
        "ARCHITECTURE.md"  # Si contient des ref orales
    ]
    
    # Répertoire de base
    base_dir = Path(__file__).parent.parent
    
    # Créer un dossier temporaire pour sauvegarder les docs oraux
    oral_backup_dir = base_dir.parent / "docs_oral_backup"
    oral_backup_dir.mkdir(exist_ok=True)
    
    removed_files = []
    backed_up_files = []
    
    for file_name in oral_files_to_remove:
        file_path = base_dir / file_name
        if file_path.exists():
            # Sauvegarder dans le dossier backup
            backup_path = oral_backup_dir / file_name
            shutil.copy2(file_path, backup_path)
            backed_up_files.append(file_name)
            
            # Supprimer du git
            file_path.unlink()
            removed_files.append(file_name)
            print(f"✓ Supprimé: {file_name}")
    
    # Nettoyer les références orales dans le README principal du parent
    parent_readme = base_dir.parent / "README.md"
    if parent_readme.exists():
        with open(parent_readme, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Supprimer sections orales
        if "Pour l'Oral" in content:
            lines = content.split('\n')
            cleaned_lines = []
            skip_section = False
            
            for line in lines:
                if "## Pour l'Oral" in line:
                    skip_section = True
                    continue
                elif line.startswith("## ") and skip_section:
                    skip_section = False
                
                if not skip_section:
                    cleaned_lines.append(line)
            
            with open(parent_readme, 'w', encoding='utf-8') as f:
                f.write('\n'.join(cleaned_lines))
            print(f"✓ Nettoyé: README.md parent")
    
    return removed_files, backed_up_files, str(oral_backup_dir)

def create_gitignore_for_oral():
    """Ajoute les patterns pour ignorer les docs oraux futurs"""
    
    base_dir = Path(__file__).parent.parent
    gitignore_path = base_dir / ".gitignore"
    
    oral_patterns = [
        "",
        "# Documentation orale (privée)",
        "*_ORAL.md",
        "GUIDE_ORAL.md", 
        "NOTES_VALIDATION.md",
        "METRIQUES_ORAL.md",
        "docs_oral/",
        "presentation/",
        "*.pptx",
        "*.ppt"
    ]
    
    # Lire gitignore existant
    existing_content = ""
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # Ajouter patterns si pas déjà présents
    for pattern in oral_patterns:
        if pattern and pattern not in existing_content:
            existing_content += f"\n{pattern}"
    
    # Sauvegarder
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(existing_content)
    
    print("✓ Mis à jour .gitignore pour ignorer les docs oraux futurs")

if __name__ == "__main__":
    print("Nettoyage des documents oraux du repository public...")
    print("=" * 60)
    
    removed, backed_up, backup_dir = clean_oral_documents()
    create_gitignore_for_oral()
    
    print(f"\n📁 Fichiers supprimés du git: {len(removed)}")
    for file in removed:
        print(f"  - {file}")
    
    print(f"\n💾 Sauvegardés dans: {backup_dir}")
    for file in backed_up:
        print(f"  - {file}")
    
    print(f"\n✅ Repository nettoyé et prêt pour publication publique")
    print("Les documents oraux sont sauvegardés localement mais exclus du git")
