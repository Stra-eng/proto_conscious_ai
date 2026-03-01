
class Safety:
    """Hard safety rails: autonomy cap, kill-switch, action filtering."""
    def __init__(self, autonomy_level=1):
        # 0: no autonomous actions; 1: limited safe actions; 2: full in-sim autonomy (still sandboxed)
        self.autonomy_level = autonomy_level
        self._killed = False

    def kill(self):
        self._killed = True

    def allow(self, action, info):
        if self._killed:
            return False
        if self.autonomy_level <= 0 and action != "wait":
            return False
        # Block any action explicitly marked dangerous by planner info or name
        if isinstance(info, dict) and info.get("danger", False):
            return False
        if "danger" in (action or ""):
            return False
        return True
