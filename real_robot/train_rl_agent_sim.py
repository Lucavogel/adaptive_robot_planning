import gymnasium as gym
from stable_baselines3 import SAC
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor

# Import the custom environment (ensure this path is correct)
from rl_robot_env_sim import RLRobotEnv

# --- Configuration for Training ---
LOG_DIR = "./rl_logs_sac_sim/" # Separate logs for simulation
MODEL_SAVE_FREQ = 5000 # Save model checkpoint every X timesteps
TOTAL_TIMESTEPS = 500000 # Increase for meaningful training in sim (e.g., 500k-1M)
LEARNING_RATE = 0.0003
BATCH_SIZE = 256
GAMMA = 0.99
TAU = 0.005
TRAIN_FREQ = (1, "step")
GRADIENT_STEPS = 1

def main():
    # Create environment for training. Use p.DIRECT for headless (faster).
    # Set render_mode="human" for visualization during training or testing.
    env = make_vec_env(RLRobotEnv, n_envs=1, seed=0, wrapper_class=Monitor,
                       env_kwargs={"render_mode": "human"}) # or "human" for GUI

    checkpoint_callback = CheckpointCallback(
        save_freq=MODEL_SAVE_FREQ,
        save_path=LOG_DIR,
        name_prefix="robot_sac_sim_model",
        save_replay_buffer=True,
        save_vecnormalize=False,
    )

    model = SAC(
        "MlpPolicy",
        env,
        learning_rate=LEARNING_RATE,
        batch_size=BATCH_SIZE,
        gamma=GAMMA,
        tau=TAU,
        train_freq=TRAIN_FREQ,
        gradient_steps=GRADIENT_STEPS,
        verbose=1,
        tensorboard_log=LOG_DIR,
        device="cuda" # Use "cuda" if you have an NVIDIA GPU
    )

    print(f"Training SAC model for {TOTAL_TIMESTEPS} timesteps. Logs at: {LOG_DIR}")
    try:
        model.learn(
            total_timesteps=TOTAL_TIMESTEPS,
            callback=checkpoint_callback,
            log_interval=10 # Log every 10 episodes
        )
    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving current model...")
    finally:
        model_path = f"{LOG_DIR}/final_sac_robot_sim_model"
        model.save(model_path)
        print(f"Final model saved to {model_path}")
        env.close()

    # --- Testing the Trained Model (Optional) ---
    print("\n--- Starting Testing Phase ---")
    del model

    env_test = make_vec_env(RLRobotEnv, n_envs=1, seed=1, wrapper_class=Monitor,
                            env_kwargs={"render_mode": "human"}) # Always use "human" for test visualization

    loaded_model = SAC.load(model_path, env=env_test)
    print(f"Loaded model from {model_path}")

    num_test_episodes = 5
    for i in range(num_test_episodes):
        # When using make_vec_env, reset returns batched observations and info lists
        obs_batch = env_test.reset()
        # print(env_test.reset())
        # Extract the single observation and info dict since n_envs=1
        obs = obs_batch[0]
        # info = info_list[0]

        done = False
        episode_reward = 0
        step_count = 0
        print(f"\n--- Test Episode {i+1} ---")
        while not done:
            action, _states = loaded_model.predict(obs, deterministic=True)
            # step also returns batched results
            obs_batch, reward_batch, done_batch, truncated_batch = env_test.step(action)
            # Extract the single observation, reward, done, truncated, and info dict
            obs = obs_batch[0]
            reward = reward_batch[0]
            done = done_batch[0]
            truncated = truncated_batch[0]
            # info = info_list[0]

            episode_reward += reward
            step_count += 1
            if done:
                print(f"Test Episode {i+1} finished after {step_count} steps. Total Reward: {episode_reward:.2f}")

    env_test.close()
    print("Testing complete.")

if __name__ == "__main__":
    main()
