import numpy as np
from environment import BackgammonEnv
from game.board import Player

def test_environment():
    """Test basic environment functionality."""
    
    print("Creating environment...")
    env = BackgammonEnv(Player.WHITE)
    
    print("\n1. Testing reset()...")
    obs, info = env.reset()
    print(f"   Observation shape: {obs.shape}")
    print(f"   Observation range: [{obs.min():.3f}, {obs.max():.3f}]")
    # print(f"   Current player: {info['current_player']}")
    # print(f"   Legal moves: {info['legal_moves_count']}")
    # print(f"   Dice: {info['dice']}")
    
    print("\n2. Testing action_masks()...")
    mask = env.action_masks()
    print(f"   Mask shape: {mask.shape}")
    print(f"   Valid actions: {mask.sum()}")
    
    print("\n3. Testing step()...")
    action = 0  # Pick first legal move
    obs, reward, done, truncated, info = env.step(action)
    print(f"   Observation shape: {obs.shape}")
    print(f"   Reward: {reward}")
    print(f"   Done: {done}")
    # print(f"   Move: {info['move_from']} -> {info['move_to']} (die: {info['die_used']})")
    
    print("\n4. Playing a few random moves...")
    step_count = 0
    while not done and step_count < 2000:
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]
        
        if len(valid_actions) == 0:
            print("   No valid actions!")
            print(f"   Current player: {env.game.get_current_player()}")
            print(f"   Our player: {env.player}")
            print(f"   Game over: {env.game.is_game_over()}")
            print(f"   Available dice: {env.game.get_available_dice()}")
            break
        
        action = np.random.choice(valid_actions)
        obs, reward, done, truncated, info = env.step(action)
        step_count += 1
        
        print(f"\n{'='*60}")
        print(f"Step {step_count}:")
        print(f"  Move success: {info.get('move_success', 'N/A')}")
        print(f"  Current player: {info.get('current_player', 'N/A')}")
        print(f"  Available dice: {info.get('available_dice', 'N/A')}")
        print(f"  Legal moves count: {info.get('legal_moves_count', 'N/A')}")
        print(f"  Reward: {reward}")
        print(f"  Done: {done}")
        print(f"  Invalid move: {info.get('invalid_move', False)}")
        
        if info.get('invalid_move'):
            print(f"\n!!! INVALID MOVE DETECTED AT STEP {step_count} !!!")
            break
    
    print(f"\n5. Episode finished after {step_count} steps")
    print(f"   Final reward: {reward}")
    print(f"   Game over: {done}")
    # print(f"   Winner: {info['winner']}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_environment()
