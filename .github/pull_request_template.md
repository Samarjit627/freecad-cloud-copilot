# PR Title

## Summary
- What changed and why?
- Risk level: Low / Medium / High (explain)

## Checklist (must pass before merge)
- [ ] I did NOT modify `StandaloneCoPilot.FCMacro` without explicit approval from the owner
- [ ] I did NOT modify `text_to_cad_integration.py` without explicit approval
- [ ] I did NOT modify `utils/llm_client.py` without explicit approval
- [ ] I did NOT modify `cloud_config.json` without explicit approval
- [ ] All new functionality is behind feature flags in `cloud_config.json`
- [ ] New functionality starts in shadow mode (no UI/CAD mutations) unless explicitly approved
- [ ] Smoke expectations:
  - [ ] Chat greeting works (Axis 5 responds to "hi")
  - [ ] DFM on sample does NOT surface the generic message "Unable to perform detailed analysis" as an issue
  - [ ] Basic CAD ops (cube or gear) succeed without errors

## Screenshots / Logs (optional)
- Paste relevant console logs or screenshots.

## Notes
- Anything reviewers should pay special attention to.
