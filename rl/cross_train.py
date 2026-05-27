import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import torch
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from stable_baselines3.common.monitor import Monitor

from rl.environment import BackgammonEnv
from game.board import Player


# Ordered from weakest to strongest based on tournament results
CURRICULUM = [
    "advanced",
    "winloss",
    "blotpenalty",
    "pipcount",
]

OPPONENT_PATHS = {
    "advanced":     {"white": "./models/white_advanced_final",     "black": "./models/black_advanced_final"},
    "winloss":      {"white": "./models/white_winloss_final",      "black": "./models/black_winloss_final"},
    "blotpenalty":  {"white": "./models/white_blotpenalty_final",  "black": "./models/black_blotpenalty_final"},
    "pipcount":     {"white": "./models/white_pipcount_final",     "black": "./models/black_pipcount_final"},
}


def mask_fn(env):
    return env.action_masks()


def load_opponents() -> dict:
    """Load all opponent models."""
    opponents = {}
    for name, paths in OPPONENT_PATHS.items():
        try:
            opponents[name] = {
                "white": MaskablePPO.load(paths["white"]),
                "black": MaskablePPO.load(paths["black"]),
            }
            print(f"  Loaded opponent: {name}")
        except Exception as e:
            print(f"  Skipping opponent {name}: {e}")
    return opponents


def make_env(player: Player, log_dir: str, scoring_function: str = "combined"):
    env = BackgammonEnv(player=player, scoring_function=scoring_function)
    env = ActionMasker(env, mask_fn)
    env = Monitor(env, log_dir)
    return env


def cross_train(
        base_model_path: str = None,
        total_timesteps_per_opponent: int = 100000,
        save_freq: int = 50000,
        log_dir: str = "./logs/cross_train/",
        model_dir: str = "./models/",
        scoring_function: str = "combined",
        mode: str = "curriculum",
):
    """
    Cross-train the combined model against other pre-trained models.
    
    Args:
        base_model_path: Path to starting model (None = train from scratch)
        total_timesteps_per_opponent: Timesteps to train against each opponent
        save_freq: How often to save checkpoints (in timesteps per opponent stage)
        log_dir: Directory for logs
        model_dir: Directory for saving models
        scoring_function: Scoring function for the training environment
        mode: "curriculum" (ordered weakest to strongest) or "league" (random sampling)
    """
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    print("\nLoading opponent models...")
    opponents = load_opponents()

    if len(opponents) == 0:
        print("No opponents loaded, exiting.")
        return

    print("\nCreating environments...")
    env_white = make_env(Player.WHITE, log_dir + "white/", scoring_function)
    env_black = make_env(Player.BLACK, log_dir + "black/", scoring_function)

    print("Initializing combined models...")
    if base_model_path:
        print(f"  Loading base model from {base_model_path}")
        model_white = MaskablePPO.load(f"./models/white_{scoring_function}_cross_final", env=env_white, device=device)
        model_black = MaskablePPO.load(f"./models/black_{scoring_function}_cross_final", env=env_black, device=device)
    else:
        print("  Starting from scratch")
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
            tensorboard_log=log_dir + "white_tb/",
            device=device,
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
            tensorboard_log=log_dir + "black_tb/",
            device=device,
        )

    if mode == "curriculum":
        _train_curriculum(
            model_white, model_black,
            env_white, env_black,
            opponents,
            total_timesteps_per_opponent,
            save_freq,
            model_dir,
            scoring_function,
        )
    elif mode == "league":
        _train_league(
            model_white, model_black,
            env_white, env_black,
            opponents,
            total_timesteps_per_opponent,
            save_freq,
            model_dir,
            scoring_function,
        )
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'curriculum' or 'league'.")

    print("\nSaving final models...")
    model_white.save(f"{model_dir}/white_{scoring_function}_league_final")
    model_black.save(f"{model_dir}/black_{scoring_function}_league_final")
    print("Cross-training complete.")

    return model_white, model_black


def _train_curriculum(
        model_white, model_black,
        env_white, env_black,
        opponents: dict,
        total_timesteps_per_opponent: int,
        save_freq: int,
        model_dir: str,
        scoring_function: str,
):
    """
    Train against opponents in order from weakest to strongest.
    """
    stages = [name for name in CURRICULUM if name in opponents]
    # Final stage: self-play
    stages.append("self")

    print(f"\nCurriculum stages: {stages}")

    for stage_idx, opponent_name in enumerate(stages):
        print(f"\n{'='*60}")
        print(f"Stage {stage_idx + 1}/{len(stages)}: Training against {opponent_name}")
        print(f"{'='*60}")

        steps_per_half = total_timesteps_per_opponent // 2
        update_interval = save_freq // 2
        num_iterations = steps_per_half // update_interval

        for iteration in range(num_iterations):
            print(f"\nIteration {iteration + 1}/{num_iterations}")

            # Set opponents
            if opponent_name == "self":
                env_white.env.opponent_policy = model_black
                env_black.env.opponent_policy = model_white
            else:
                env_white.env.opponent_policy = opponents[opponent_name]["black"]
                env_black.env.opponent_policy = opponents[opponent_name]["white"]

            # Train white
            model_white.learn(
                total_timesteps=update_interval,
                reset_num_timesteps=False,
                tb_log_name=f"white_vs_{opponent_name}",
                progress_bar=True,
            )

            # Train black
            model_black.learn(
                total_timesteps=update_interval,
                reset_num_timesteps=False,
                tb_log_name=f"black_vs_{opponent_name}",
                progress_bar=True,
            )

        print(f"\nSaving checkpoint after stage {opponent_name}...")
        model_white.save(f"{model_dir}/white_{scoring_function}_cross_{opponent_name}")
        model_black.save(f"{model_dir}/black_{scoring_function}_cross_{opponent_name}")


def _train_league(
        model_white, model_black,
        env_white, env_black,
        opponents: dict,
        total_timesteps: int,
        save_freq: int,
        model_dir: str,
        scoring_function: str,
):
    """
    Train against randomly sampled opponents from the pool, including self-play.
    """
    import random

    opponent_names = list(opponents.keys()) + ["self"]
    steps_per_iteration = save_freq // 2
    num_iterations = total_timesteps // save_freq

    print(f"\nLeague pool: {opponent_names}")
    print(f"Total iterations: {num_iterations}")

    for iteration in range(num_iterations):
        opponent_name = random.choice(opponent_names)

        print(f"\n{'='*60}")
        print(f"Iteration {iteration + 1}/{num_iterations}: Training against {opponent_name}")
        print(f"{'='*60}")

        if opponent_name == "self":
            env_white.env.opponent_policy = model_black
            env_black.env.opponent_policy = model_white
        else:
            env_white.env.opponent_policy = opponents[opponent_name]["black"]
            env_black.env.opponent_policy = opponents[opponent_name]["white"]

        model_white.learn(
            total_timesteps=steps_per_iteration,
            reset_num_timesteps=False,
            tb_log_name=f"white_league",
            progress_bar=True,
        )

        model_black.learn(
            total_timesteps=steps_per_iteration,
            reset_num_timesteps=False,
            tb_log_name=f"black_league",
            progress_bar=True,
        )

        if (iteration + 1) % 5 == 0:
            print(f"\nSaving checkpoint at iteration {iteration + 1}...")
            model_white.save(f"{model_dir}/white_{scoring_function}_league_{iteration + 1}")
            model_black.save(f"{model_dir}/black_{scoring_function}_league_{iteration + 1}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-train backgammon agents")
    parser.add_argument("--mode", type=str, default="curriculum",
                        choices=["curriculum", "league"],
                        help="Training mode")
    parser.add_argument("--base-model", type=str, default=None,
                        help="Base model path prefix (without _white/_black suffix). Defaults to training from scratch")
    parser.add_argument("--timesteps-per-opponent", type=int, default=100000,
                        help="Timesteps to train against each opponent (curriculum) or total timesteps (league)")
    parser.add_argument("--save-freq", type=int, default=50000,
                        help="Save frequency in timesteps")
    parser.add_argument("--scoring", type=str, default="combined",
                        choices=["winloss", "pipcount", "blotpenalty", "combined", "advanced"],
                        help="Scoring function to use")

    args = parser.parse_args()

    cross_train(
        base_model_path=args.base_model,
        total_timesteps_per_opponent=args.timesteps_per_opponent,
        save_freq=args.save_freq,
        scoring_function=args.scoring,
        mode=args.mode,
    )
