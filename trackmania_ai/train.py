import argparse
from trackmania_ai.model import TrackmaniaAI
from utils import prepare_training_data, plot_training_progress, save_model, analyze_performance
import os
import time

def main():
    parser = argparse.ArgumentParser(description="Entraînement de l'IA Trackmania")
    parser.add_argument('--csv', type=str, required=True,
                       help='Chemin vers le fichier CSV des données d\'entraînement')
    parser.add_argument('--episodes', type=int, default=100,
                       help='Nombre d\'épisodes d\'entraînement')
    parser.add_argument('--test', action='store_true',
                       help='Mode test : exécute l\'IA sur la piste après l\'entraînement')
    parser.add_argument('--load', type=str,
                       help='Charger un modèle existant (chemin vers le fichier .npy)')
    args = parser.parse_args()

    # Vérifier que le fichier CSV existe
    if not os.path.exists(args.csv):
        print(f"❌ Erreur : Le fichier {args.csv} n'existe pas")
        return

    print("🎮 Initialisation de l'IA Trackmania...")
    ai = TrackmaniaAI()

    # Charger un modèle existant si spécifié
    if args.load and os.path.exists(args.load):
        print(f"📥 Chargement du modèle {args.load}")
        ai.q_table = load_model(args.load)

    # Préparer les données
    print("📊 Préparation des données d'entraînement...")
    try:
        data = prepare_training_data(args.csv)
    except ValueError as e:
        print(f"❌ Erreur : {e}")
        return

    # Entraînement
    print(f"\n🚀 Démarrage de l'entraînement sur {args.episodes} épisodes")
    rewards_history = []
    
    for episode in range(args.episodes):
        print(f"\n📝 Épisode {episode + 1}/{args.episodes}")
        
        episode_rewards = []
        ai.previous_state = None
        ai.previous_checkpoint = None
        
        for _, row in data.iterrows():
            current_state = ai.get_state(row)
            checkpoint_passed = (ai.previous_checkpoint is not None and 
                               row['CurrentCP'] > ai.previous_checkpoint)
            
            if ai.previous_state is not None:
                reward = ai.get_reward(current_state, ai.previous_state, checkpoint_passed)
                action = ai.choose_action(ai.previous_state)
                ai.update_q_table(ai.previous_state, action, reward, current_state)
                episode_rewards.append(reward)
            
            ai.previous_state = current_state
            ai.previous_checkpoint = row['CurrentCP']
        
        # Calculer la récompense totale de l'épisode
        total_reward = sum(episode_rewards)
        rewards_history.append(total_reward)
        
        print(f"💫 Récompense totale : {total_reward:.2f}")
        
        # Réduire epsilon progressivement
        ai.epsilon = max(0.01, ai.epsilon * 0.995)

    # Sauvegarder le modèle et tracer la progression
    print("\n💾 Sauvegarde du modèle...")
    save_model(ai.q_table)
    
    print("📈 Génération du graphique de progression...")
    plot_training_progress(rewards_history)

    # Mode test si demandé
    if args.test:
        print("\n🏁 Démarrage du mode test...")
        print("⚠️ Assurez-vous que Trackmania est en premier plan")
        time.sleep(3)
        ai.run(args.csv)
        analyze_performance(args.csv)

if __name__ == "__main__":
    main() 