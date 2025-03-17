import numpy as np
import pandas as pd
from trackmania_ai.controller import TrackmaniaController
import time

class TrackmaniaAI:
    def __init__(self):
        self.controller = TrackmaniaController()
        self.actions = [
            'accelerate',
            'brake',
            'left',
            'right',
            'accelerate_left',
            'accelerate_right',
            'nothing'
        ]
        
        # Paramètres d'apprentissage
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.3  # Taux d'exploration
        self.q_table = {}  # Table Q-learning
        
        # État précédent pour l'apprentissage
        self.previous_state = None
        self.previous_action = None
        self.previous_checkpoint = None
        
    def get_state(self, data):
        """Convertit les données brutes en un état discret"""
        pos_x = round(data['PosX'] / 10) * 10
        pos_y = round(data['PosY'] / 10) * 10
        pos_z = round(data['PosZ'] / 10) * 10
        speed = round(data['Speed'] / 5) * 5
        checkpoint = data['CurrentCP']
        
        return (pos_x, pos_y, pos_z, speed, checkpoint)
        
    def get_reward(self, current_state, previous_state, checkpoint_passed):
        """Calcule la récompense basée sur la progression"""
        if previous_state is None:
            return 0
            
        # Récompense de base pour le mouvement
        distance = np.sqrt(
            (current_state[0] - previous_state[0])**2 +
            (current_state[1] - previous_state[1])**2 +
            (current_state[2] - previous_state[2])**2
        )
        
        reward = distance * (current_state[3] / 100)  # Distance × Vitesse normalisée
        
        # Bonus pour passage de checkpoint
        if checkpoint_passed:
            reward += 1000
            
        # Pénalité si la voiture recule ou ne bouge pas
        if distance < 0.1:
            reward -= 50
            
        return reward
        
    def choose_action(self, state):
        """Choisit une action selon la politique epsilon-greedy"""
        if np.random.random() < self.epsilon:
            return np.random.choice(self.actions)
            
        if state not in self.q_table:
            self.q_table[state] = {action: 0 for action in self.actions}
            
        return max(self.q_table[state].items(), key=lambda x: x[1])[0]
        
    def update_q_table(self, state, action, reward, next_state):
        """Met à jour la table Q avec la nouvelle expérience"""
        if state not in self.q_table:
            self.q_table[state] = {action: 0 for action in self.actions}
            
        if next_state not in self.q_table:
            self.q_table[next_state] = {action: 0 for action in self.actions}
            
        # Formule Q-learning
        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state].values())
        new_value = (1 - self.learning_rate) * old_value + \
                   self.learning_rate * (reward + self.discount_factor * next_max)
        self.q_table[state][action] = new_value
        
    def train_on_data(self, csv_file):
        """Entraîne l'IA sur un fichier CSV de données"""
        print("🎮 Démarrage de l'entraînement...")
        df = pd.read_csv(csv_file)
        
        for index, row in df.iterrows():
            current_state = self.get_state(row)
            checkpoint_passed = (self.previous_checkpoint is not None and 
                               row['CurrentCP'] > self.previous_checkpoint)
            
            if self.previous_state is not None:
                reward = self.get_reward(current_state, self.previous_state, checkpoint_passed)
                action = self.choose_action(self.previous_state)
                self.update_q_table(self.previous_state, action, reward, current_state)
            
            self.previous_state = current_state
            self.previous_checkpoint = row['CurrentCP']
            
            if index % 100 == 0:
                print(f"⚡ Progression : {index}/{len(df)} frames traitées")
                
        print("✅ Entraînement terminé !")
        
    def run(self, csv_file):
        """Fait rouler l'IA sur la piste"""
        print("🏁 Démarrage de la course...")
        df = pd.read_csv(csv_file)
        
        # Attendre que le joueur soit prêt
        print("⚠️ Placez la voiture sur la ligne de départ")
        print("⚡ Démarrage dans 3 secondes...")
        time.sleep(3)
        
        start_time = time.time()
        self.controller.release_all_keys()
        
        for index, row in df.iterrows():
            current_state = self.get_state(row)
            action = self.choose_action(current_state)
            self.controller.apply_action(action)
            
            # Vérifier si la voiture est bloquée
            if self.controller.check_stagnation((row['PosX'], row['PosY'], row['PosZ'])):
                self.controller.restart_race()
                break
                
            # Attendre le bon timing
            target_time = start_time + (row['RaceTime'] / 1000.0)
            while time.time() < target_time:
                pass
                
            if index % 60 == 0:
                print(f"⚡ Frame {index} | Temps: {(time.time() - start_time)*1000:.0f}ms") 