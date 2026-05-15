import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

from rl.environment import BackgammonEnv
from game.board import Player

class SelfPlayCallback(BaseCallback):
    """
    """
    def __init__(self, update_interval: int = 10000, verbose: int = 0):
        super().__init__(verbose)
        self.update_interval = update_interval
        self.last_update = 0

    def _on_step(self) -> bool:
        if self.n_calls - self.last_update >= self.update_interval:
            if self.verbose > 0:
                print(f"Updating opponent policy at step {self.n_calls}")
            self.last_update = self.n_calls
        
        return True
    
def mask_fn(env):
    return env.action_masks()

def train_self_play(
        total_timesteps: int = 500000,
        update_opponent_interval: int = 10000,
        save_freq: int = 10000,
        log_dir: str = "./logs/",
        model_dir: str = "./models/",
        scoring_function: str = "winloss"
        ):
    """
    """
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    print("Creating environments")
    env_white = BackgammonEnv(player=Player.WHITE, scoring_function=scoring_function)
    env_white = ActionMasker(env_white, mask_fn)
    env_white = Monitor(env_white, log_dir + f"{scoring_function}_white/")
    
    env_black = BackgammonEnv(player=Player.BLACK, scoring_function=scoring_function)
    env_black = ActionMasker(env_black, mask_fn)
    env_black = Monitor(env_black, log_dir + f"{scoring_function}_black/")

    print("Initializing models")

    model_white = MaskablePPO(
        MaskableActorCriticPolicy,
        env_white,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        verbose=1,
        tensorboard_log=log_dir + f"{scoring_function}_white_tb/",
    )
    
    model_black = MaskablePPO(
        MaskableActorCriticPolicy,
        env_black,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        verbose=1,
        tensorboard_log=log_dir + f"{scoring_function}_black_tb/",
    )

    print("Starting self-play training")
    
    steps_per_iteration = update_opponent_interval
    num_iterations = total_timesteps // steps_per_iteration
    
    for iteration in range(num_iterations):
        print(f"\n{'='*60}")
        print(f"Iteration {iteration + 1}/{num_iterations}")
        print(f"{'='*60}")
        
        # Train white player
        env_white.env.opponent_policy = model_black
        model_white.learn(
            total_timesteps=steps_per_iteration // 2,
            reset_num_timesteps=False,
            tb_log_name="white",
            progress_bar=True
        )
        
        # Train black player
        env_black.env.opponent_policy = model_white
        model_black.learn(
            total_timesteps=steps_per_iteration // 2,
            reset_num_timesteps=False,
            tb_log_name="black",
            progress_bar=True
        )
        
        # Save checkpoints
        if (iteration + 1) % (save_freq // steps_per_iteration) == 0:
            print(f"\nSaving models at iteration {iteration + 1}")
            model_white.save(f"{model_dir}/white_{scoring_function}_{iteration + 1}")
            model_black.save(f"{model_dir}/black_{scoring_function}_{iteration + 1}")

    # Final save
    print("\nSaving final models")
    model_white.save(f"{model_dir}/white_{scoring_function}_final")
    model_black.save(f"{model_dir}/black_{scoring_function}_final")
    
    print("\nTraining complete")
    
    return model_white, model_black

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train backgammon agents")
    parser.add_argument("--scoring", type=str, default="winloss",
                       choices=["winloss", "pipcount", "bearingoff", "blotpenalty", "combined", "advanced"],
                       help="Scoring function to use")
    parser.add_argument("--timesteps", type=int, default=200000,
                       help="Total training timesteps")
    parser.add_argument("--update-interval", type=int, default=10000,
                       help="Opponent update interval")
    parser.add_argument("--save-freq", type=int, default=50000,
                       help="Save frequency")
    
    args = parser.parse_args()
    
    train_self_play(
        total_timesteps=args.timesteps,
        update_opponent_interval=args.update_interval,
        save_freq=args.save_freq,
        scoring_function=args.scoring
    )