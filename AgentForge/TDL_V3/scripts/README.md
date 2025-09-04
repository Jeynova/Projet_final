# Tests AgentForge

Suite complète de tests pour valider le système AgentForge.

## 🎯 Vue d'Ensemble

Ce dossier contient 5 types de tests pour garantir la qualité et robustesse d'AgentForge :

1. **Tests Complets** - Scénarios réels de génération
2. **Benchmarks** - Performance et métriques
3. **Tests de Stress** - Robustesse et edge cases
4. **Tests UI** - Interface Flask
5. **Suite Maître** - Orchestration de tous les tests

## 🚀 Exécution Rapide

### Windows (PowerShell)
```powershell
.\scripts\run_tests.ps1
```

### Linux/Mac
```bash
python scripts/run_all_tests.py
```

## 📋 Scripts Disponibles

### 1. `test_comprehensive.py`
- **But**: Tests de scénarios réels complets
- **Scénarios**: 6 cas d'usage (simple, e-commerce, blog, etc.)
- **Validation**: Pipeline complet avec évaluation
- **Durée**: ~2-3 minutes

```python
python scripts/test_comprehensive.py
```

### 2. `benchmark.py`
- **But**: Mesure de performances
- **Métriques**: Temps, mémoire, génération de fichiers
- **Comparaison**: Manual vs LangGraph
- **Durée**: ~5-10 minutes

```python
python scripts/benchmark.py
```

### 3. `stress_test.py`
- **But**: Tests de robustesse
- **Edge Cases**: Prompts vides, syntaxe cassée, entités multiples
- **Validation**: Gestion gracieuse des erreurs
- **Durée**: ~3-5 minutes

```python
python scripts/stress_test.py
```

### 4. `ui_integration_test.py`
- **But**: Tests de l'interface Flask
- **Tests**: Endpoints, génération via UI, API
- **Validation**: Interface utilisateur complète
- **Durée**: ~2-4 minutes
- **Note**: Démarre automatiquement le serveur Flask

```python
python scripts/ui_integration_test.py
```

### 5. `run_all_tests.py`
- **But**: Suite complète orchestrée
- **Exécution**: Tous les tests séquentiellement
- **Rapport**: Consolidé avec métriques globales
- **Durée**: ~10-20 minutes

```python
python scripts/run_all_tests.py
```

## 📊 Fichiers de Résultats

Après exécution, les résultats sont sauvegardés en JSON :

- `test_comprehensive_results.json` - Résultats tests complets
- `benchmark_results.json` - Métriques de performance
- `stress_test_results.json` - Résultats robustesse
- `ui_integration_test_results.json` - Résultats interface
- `master_test_report.json` - Rapport consolidé global

## 🎯 Critères de Réussite

### Tests Complets
- ✅ Score ≥ 0.7 pour chaque scénario
- ✅ 100% des fichiers générés
- ✅ Pipeline complet sans erreur

### Benchmarks
- ✅ Génération < 30s par projet
- ✅ Mémoire < 500MB
- ✅ Consistance entre modes

### Tests de Stress
- ✅ 0 crash (gestion gracieuse)
- ✅ Taux de robustesse ≥ 90%
- ✅ Edge cases gérés

### Tests UI
- ✅ Tous endpoints fonctionnels
- ✅ Génération via interface
- ✅ Temps de réponse < 5s

### Suite Globale
- ✅ Toutes suites réussies
- ✅ Taux global ≥ 85%
- ✅ Rapport consolidé généré

## 🔧 Configuration

### Prérequis
```bash
pip install -r requirements.txt
```

### Variables d'Environnement (optionnel)
```bash
export AGENTFORGE_TEST_TIMEOUT=300  # Timeout par défaut
export AGENTFORGE_UI_PORT=5000      # Port Flask pour tests UI
```

### Configuration LLM
Les tests utilisent la configuration LLM du projet :
- OpenAI API (si configurée)
- Fallback vers génération déterministe

## 📈 Interprétation des Résultats

### Scores d'Évaluation
- **1.0** : Parfait (tous fichiers + structure correcte)
- **0.8-0.9** : Excellent (quelques détails mineurs)
- **0.6-0.7** : Bon (fonctionnel avec améliorations)
- **0.4-0.5** : Acceptable (basique mais utilisable)
- **< 0.4** : Insuffisant (corrections nécessaires)

### Temps de Performance
- **< 10s** : Excellent
- **10-20s** : Bon
- **20-30s** : Acceptable
- **> 30s** : À optimiser

### Robustesse
- **0 crash** : Excellent
- **1-2 crashes** : Acceptable
- **> 3 crashes** : À corriger

## 🐛 Dépannage

### Problèmes Courants

1. **TimeoutError**
   - Augmenter le timeout
   - Vérifier la configuration LLM

2. **ModuleNotFoundError**
   ```bash
   pip install -r requirements.txt
   ```

3. **Port 5000 occupé (tests UI)**
   - Changer le port ou arrêter le service existant
   - Le script détecte automatiquement les conflits

4. **Permissions d'écriture**
   - Vérifier les droits sur le dossier
   - Les tests créent des fichiers temporaires

### Logs de Debug
Activer les logs détaillés :
```bash
export AGENTFORGE_DEBUG=1
python scripts/run_all_tests.py
```

## 🎓 Usage pour Présentation

### Pour l'Oral
1. Exécuter la suite complète une fois : `run_all_tests.py`
2. Montrer le rapport consolidé : `master_test_report.json`
3. Détailler les métriques clés :
   - Taux de réussite global
   - Temps de génération moyens
   - Robustesse (0 crash)
   - Couverture fonctionnelle

### Démonstration Live
1. Test rapide : `test_comprehensive.py`
2. Montrer un scénario spécifique
3. Expliquer les scores d'évaluation
4. Présenter la génération de fichiers

## 📚 Architecture des Tests

```
scripts/
├── test_comprehensive.py    # Tests scénarios complets
├── benchmark.py            # Métriques performance  
├── stress_test.py          # Robustesse et edge cases
├── ui_integration_test.py  # Interface Flask
├── run_all_tests.py        # Orchestrateur principal
└── run_tests.ps1          # Script PowerShell Windows
```

Chaque script est autonome mais s'intègre dans la suite globale pour une validation complète du système AgentForge.
