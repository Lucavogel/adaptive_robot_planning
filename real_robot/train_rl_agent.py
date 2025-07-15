import gymnasium as gym
from stable_baselines3 import SAC # Soft Actor-Critic is a good choice for continuous control
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback # To save models during training
from stable_baselines3.common.monitor import Monitor # To log training metrics properly

# Import the custom environment and configuration
from rl_robot_env import RLRobotEnv
import rl_config

def main():
    # Create the environment. make_vec_env is recommended by Stable-Baselines3 even for a single env.
    # It adds a VecMonitor wrapper by default which helps in logging.
    env = make_vec_env(RLRobotEnv, n_envs=1, seed=0, wrapper_class=Monitor) # wrapper_class=Monitor is important for logging

    # Setup Checkpoint Callback to save the model periodically
    checkpoint_callback = CheckpointCallback(
        save_freq=rl_config.MODEL_SAVE_FREQ,
        save_path=rl_config.LOG_DIR,
        name_prefix="robot_sac_model",
        save_replay_buffer=True, # Recommended to save replay buffer for continued training
        save_vecnormalize=False, # Only needed if using VecNormalize wrapper, which we currently are not.
    )

    # Initialize the SAC model (Soft Actor-Critic)
    # MlpPolicy creates a Multilayer Perceptron (feedforward neural network) policy
    model = SAC(
        "MlpPolicy", # Policy type
        env,
        learning_rate=rl_config.LEARNING_RATE,
        batch_size=rl_config.BATCH_SIZE,
        gamma=rl_config.GAMMA,
        tau=rl_config.TAU,
        train_freq=rl_config.TRAIN_FREQ,
        gradient_steps=rl_config.GRADIENT_STEPS,
        verbose=1, # 1 for training progress output, 0 for silent
        tensorboard_log=rl_config.LOG_DIR, # Enable TensorBoard logging
        device="cpu" # Use 'auto' to let SB3 detect, 'cuda' for GPU, 'cpu' for CPU
                      # Ensure you have a compatible GPU and PyTorch installed with CUDA if using 'cuda'
    )

    print(f"Training SAC model for {rl_config.TOTAL_TIMESTEPS} timesteps. Logs will be at: {rl_config.LOG_DIR}")
    try:
        model.learn(
            total_timesteps=rl_config.TOTAL_TIMESTEPS,
            callback=checkpoint_callback,
            log_interval=10 # Log every 10 episodes in the terminal
        )
    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving current model...")
    finally:
        # Save the final trained model
        model_path = f"{rl_config.LOG_DIR}/final_sac_robot_model"
        model.save(model_path)
        print(f"Final model saved to {model_path}")
        env.close() # Close the environment properly

    # --- Testing the Trained Model (Optional) ---
    print("\n--- Starting Testing Phase ---")
    del model # Delete model object to free memory before loading fresh

    # Re-create the environment for evaluation with render_mode="human" if desired
    # Use a different seed for testing.
    env_test = make_vec_env(RLRobotEnv, n_envs=1, seed=1, wrapper_class=Monitor, env_kwargs={"render_mode": "human"})

    # Load the trained model
    loaded_model = SAC.load(model_path, env=env_test)
    print(f"Loaded model from {model_path}")

    num_test_episodes = rl_config.NUM_TEST_EPISODES # Number of episodes to test the agent
    for i in range(num_test_episodes):
        # obs, info = env_test.reset()
        obs = env_test.reset()
        done = False
        episode_reward = 0
        step_count = 0
        print(f"\n--- Test Episode {i+1} ---")
        while not done:
            # Predict action from the loaded model. deterministic=True for evaluation.
            action, _states = loaded_model.predict(obs, deterministic=True)
            # obs, reward, done, truncated, info = env_test.step(action)
            obs, reward, done, truncated = env_test.step(action)
            episode_reward += reward[0] # Reward is an array from make_vec_env
            step_count += 1
            if done:
                print(f"Test Episode {i+1} finished after {step_count} steps. Total Reward: {episode_reward:.2f}")

    env_test.close()
    print("Testing complete.")

if __name__ == "__main__":
    main()
