# Voice Outreach (ElevenLabs ConvAI)

This folder is the ElevenLabs ConvAI project for the optional voice-outreach
path. The ElevenLabs CLI discovers agents from `agents.json` in the directory it
runs from, so run it from here, not the repo root:

```powershell
cd voice
elevenlabs auth login
elevenlabs agents pull --agent "<agent_id>" --update
elevenlabs agents push
```

Files:

- `agents.json`: project manifest mapping the agent id to its config
- `agent_configs/Candidate-Outreach.json`: the recruiter outreach agent
  (turn-taking, TTS, dynamic variables, workflow graph, guardrails)
- `tools.json`, `tests.json`: ConvAI tool and test registries, empty for now

Full setup, dynamic variables, and the manual acceptance test are in
[../docs/elevenlabs-voice-agent-setup.md](../docs/elevenlabs-voice-agent-setup.md).

All demo content is synthetic. Live calls are active by default and run only behind backend credentials; see the repo README for the voice safety controls.
