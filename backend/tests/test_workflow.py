from backend.state import WorkflowState, set_state


def test_workflow_state_roundtrip():
    set_state(WorkflowState.idle)
    assert set_state(WorkflowState.seeded) == WorkflowState.seeded
    assert (
        set_state(WorkflowState.paused_for_recruiter_approval)
        == WorkflowState.paused_for_recruiter_approval
    )
