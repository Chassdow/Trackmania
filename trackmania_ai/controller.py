from pynput.keyboard import Key, Controller
import time

class TrackmaniaController:
    def __init__(self):
        self.keyboard = Controller()
        self.last_movement_time = time.time()
        self.last_position = None
        self.stagnation_threshold = 3.0  # Temps en secondes avant de considérer que la voiture est bloquée

    def press_key(self, key):
        """Appuie sur une touche"""
        self.keyboard.press(key)

    def release_key(self, key):
        """Relâche une touche"""
        self.keyboard.release(key)

    def release_all_keys(self):
        """Relâche toutes les touches de contrôle"""
        self.keyboard.release('z')
        self.keyboard.release('s')
        self.keyboard.release('q')
        self.keyboard.release('d')

    def restart_race(self):
        """Redémarre la course en appuyant sur N"""
        print("🔄 La voiture est bloquée ! Redémarrage...")
        self.release_all_keys()
        time.sleep(0.5)  # Petit délai avant le restart
        self.keyboard.press('n')
        time.sleep(0.1)
        self.keyboard.release('n')
        time.sleep(2)  # Attendre que la course redémarre
        self.last_movement_time = time.time()

    def check_stagnation(self, current_position):
        """Vérifie si la voiture est bloquée"""
        if self.last_position is None:
            self.last_position = current_position
            return False

        # Calculer la distance parcourue
        distance = ((current_position[0] - self.last_position[0]) ** 2 +
                   (current_position[1] - self.last_position[1]) ** 2 +
                   (current_position[2] - self.last_position[2]) ** 2) ** 0.5

        current_time = time.time()
        
        # Si la voiture a bougé significativement
        if distance > 0.5:  # Seuil de mouvement en unités du jeu
            self.last_movement_time = current_time
            self.last_position = current_position
            return False

        # Si la voiture est immobile depuis trop longtemps
        if current_time - self.last_movement_time > self.stagnation_threshold:
            return True

        return False

    def apply_action(self, action):
        """Applique une action (accélérer, freiner, tourner)"""
        self.release_all_keys()
        
        if action == 'accelerate':
            self.press_key('z')
        elif action == 'brake':
            self.press_key('s')
        elif action == 'left':
            self.press_key('q')
        elif action == 'right':
            self.press_key('d')
        elif action == 'accelerate_left':
            self.press_key('z')
            self.press_key('q')
        elif action == 'accelerate_right':
            self.press_key('z')
            self.press_key('d')
        # On peut ajouter d'autres combinaisons si nécessaire 