import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

def prepare_training_data(csv_file):
    """Prépare et nettoie les données d'entraînement"""
    df = pd.read_csv(csv_file)
    
    # Vérifier les colonnes requises
    required_columns = ['RaceTime', 'PosX', 'PosY', 'PosZ', 'Speed', 'CurrentCP']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colonnes manquantes dans le CSV : {missing_columns}")
    
    # Supprimer les lignes avec des valeurs manquantes
    df = df.dropna(subset=required_columns)
    
    # Trier par temps de course
    df = df.sort_values('RaceTime')
    
    return df

def plot_training_progress(rewards, window_size=100):
    """Affiche un graphique de la progression de l'entraînement"""
    plt.figure(figsize=(12, 6))
    
    # Moyenne mobile des récompenses
    rolling_mean = pd.Series(rewards).rolling(window=window_size).mean()
    
    plt.plot(rewards, alpha=0.3, color='blue', label='Récompenses')
    plt.plot(rolling_mean, color='red', label=f'Moyenne mobile ({window_size} épisodes)')
    
    plt.title('Progression de l\'apprentissage')
    plt.xlabel('Épisode')
    plt.ylabel('Récompense totale')
    plt.legend()
    plt.grid(True)
    
    # Sauvegarder le graphique
    os.makedirs('training_plots', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    plt.savefig(f'training_plots/training_progress_{timestamp}.png')
    plt.close()

def save_model(q_table, filename='q_table.npy'):
    """Sauvegarde la table Q dans un fichier"""
    os.makedirs('models', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'models/q_table_{timestamp}.npy'
    
    # Convertir la table Q en format numpy
    states = list(q_table.keys())
    actions = list(q_table[states[0]].keys())
    
    # Créer une matrice numpy
    q_matrix = np.zeros((len(states), len(actions)))
    state_mapping = {state: i for i, state in enumerate(states)}
    action_mapping = {action: i for i, action in enumerate(actions)}
    
    for state, actions_dict in q_table.items():
        for action, value in actions_dict.items():
            q_matrix[state_mapping[state], action_mapping[action]] = value
    
    # Sauvegarder la matrice et les mappings
    np.savez(filename, 
             q_matrix=q_matrix,
             states=states,
             actions=actions,
             state_mapping=state_mapping,
             action_mapping=action_mapping)
    
    print(f"✅ Modèle sauvegardé dans {filename}")

def load_model(filename):
    """Charge une table Q depuis un fichier"""
    data = np.load(filename, allow_pickle=True)
    
    # Reconstruire la table Q
    q_table = {}
    q_matrix = data['q_matrix']
    states = data['states']
    actions = data['actions']
    
    for i, state in enumerate(states):
        q_table[state] = {}
        for j, action in enumerate(actions):
            q_table[state][action] = q_matrix[i, j]
    
    return q_table

def analyze_performance(csv_file):
    """Analyse les performances d'une course"""
    df = pd.read_csv(csv_file)
    
    # Statistiques de base
    total_time = df['RaceTime'].max() / 1000  # Convertir en secondes
    avg_speed = df['Speed'].mean()
    max_speed = df['Speed'].max()
    checkpoints = df['CurrentCP'].max() + 1
    
    print("\n📊 Analyse de la performance :")
    print(f"⏱️  Temps total : {total_time:.2f} secondes")
    print(f"🚀 Vitesse moyenne : {avg_speed:.2f} km/h")
    print(f"💨 Vitesse maximale : {max_speed:.2f} km/h")
    print(f"🏁 Checkpoints franchis : {checkpoints}")
    
    # Calculer le temps par checkpoint
    checkpoint_times = []
    for cp in range(checkpoints):
        cp_data = df[df['CurrentCP'] == cp]
        if not cp_data.empty:
            checkpoint_times.append(cp_data['RaceTime'].min() / 1000)
    
    if len(checkpoint_times) > 1:
        print("\n⏱️  Temps par checkpoint :")
        for i in range(1, len(checkpoint_times)):
            time_diff = checkpoint_times[i] - checkpoint_times[i-1]
            print(f"   CP {i}: {time_diff:.2f} secondes") 