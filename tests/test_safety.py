from orion.safety.layer import SafetyLayer


def test_blacklisted_command_blocked():
    decision = SafetyLayer().evaluate("rm -rf /")
    assert not decision.allowed


def test_non_whitelisted_requires_confirmation():
    decision = SafetyLayer().evaluate("python script.py")
    assert decision.allowed
    assert decision.requires_confirmation
