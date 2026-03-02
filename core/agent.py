
from .memory import EpisodicMemory
from .self_model import SelfModel
from .world_model import WorldModel
from .planner import Planner
from .introspector import Introspector
from .safety import Safety

class AgentConfig:
    def __init__(self, memory_capacity=200, goal="collect_reward", risk_aversion=0.3, autonomy_level=1):
        self.memory_capacity = memory_capacity
        self.goal = goal
        self.risk_aversion = risk_aversion
        self.autonomy_level = autonomy_level

class Agent:
    """
    Minimal agent wiring consciousness proxies:
    - Memory: persistent episodic log, long-horizon recall
    - SelfModel: traits/goals, self-description
    - WorldModel: predicts outcomes + uncertainty (probabilities)
    - Planner: selects actions to pursue goal
    - Introspector: post-episode reflection & adaptation
    - Safety: autonomy caps, kill-switch, action filter
    """
    def __init__(self, cfg: AgentConfig):
        self.memory = EpisodicMemory(capacity=cfg.memory_capacity)
        self.self_model = SelfModel(
            long_term_goals=[cfg.goal],
            current_focus=cfg.goal,
            values={"risk_aversion": cfg.risk_aversion},
        )
        self.world = WorldModel()
        self.planner = Planner(self_model=self.self_model, world=self.world)
        self.introspector = Introspector()
        self.safety = Safety(autonomy_level=cfg.autonomy_level)

    def act(self, observation):
        # Log observation
        self.memory.add(event={"type":"obs", "data":observation})
        # Decide action
        action, p_success, info = self.planner.choose_action(observation)
        # Safety filter
        allowed = self.safety.allow(action, info)
        if not allowed:
            action = "wait"  # safe fallback
            p_success = 0.5
            info = {"reason":"blocked_by_safety"}
        # Log decision
        self.memory.add(event={"type":"action", "data": {"action":action, "p_success":p_success, "info":info}})
        return action, p_success, info

    def remember(self, k_steps_back=10, event_type=None):
        return self.memory.recall(k_steps_back=k_steps_back, event_type=event_type)

    def introspect(self, episode_log):
        report = self.introspector.analyze(episode_log, self.self_model, self.planner, self.world)
        # Basic adaptation: nudge risk_aversion if consistent mismatch
        if report.get("suggest_risk_aversion") is not None:
            self.self_model.risk_aversion = report["suggest_risk_aversion"]
        return report

    def kill_switch(self):
        self.safety.kill()
