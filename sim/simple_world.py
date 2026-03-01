# sim/simple_world.py
import random
from core.agent import Agent, AgentConfig
from core.world_model import WorldModel

class SimpleWorld:
    """A tiny offline simulation: each step offers safe/risky/wait with base chances, then resolves outcome."""
    def __init__(self, seed=42):
        random.seed(seed)

    def observation(self, goal="collect_reward"):
        # Randomize base success a little each step
        base_safe = random.uniform(0.55, 0.75)
        base_risky = random.uniform(0.65, 0.90)
        base_wait = 0.5
        return {
            "goal": goal,
            "actions": {
                "safe": base_safe,
                "risky": base_risky,
                "wait": base_wait
            }
        }

def run_episode(steps=50, risk_aversion=0.3, autonomy_level=1, seed=42, goal="collect_reward"):
    world = SimpleWorld(seed=seed)
    agent = Agent(AgentConfig(goal=goal, risk_aversion=risk_aversion, autonomy_level=autonomy_level))
    log = []
    probs, outcomes = [], []

    for t in range(steps):
        obs = world.observation(goal=goal)
        action, p_success, info = agent.act(obs)

        wm = WorldModel()
        y = wm.outcome(p_success)

        probs.append(p_success)
        outcomes.append(y)
        log.append({
            "type": "decision",
            "t": t,
            "action": action,
            "p_success": p_success,
            "outcome": "success" if y == 1 else "fail"
        })

        # Store outcome (obs is already stored by agent.act internally)
        agent.memory.add(event={"type": "outcome", "data": {"t": t, "y": y}})

        # Periodically test recall
        if t % 10 == 9:
            recalled = agent.remember(k_steps_back=9, event_type="obs")
            log.append({"type": "recall_check", "t": t, "ok": recalled is not None})

    report = agent.introspect(log)

    return {
        "log": log,
        "probs": probs,
        "outcomes": outcomes,
        "report": report,
        "agent": agent
    }