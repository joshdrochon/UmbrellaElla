# Audio spend counter and cap. Branch area/audiocap. Read docs/build/worker-rules.md first.
Like the image path (IMAGE_SPEND_FILE / IMAGE_SPEND_CAP_USD in tools/assetgen.py): every ElevenLabs / Stable Audio call in
tools/assetgen.py sfx|music (and pipeline/audio/build helpers that call the API) adds its cost (credits from the response
when the API returns them, else the provider's published price per second, recorded in asset-tools.json) to ONE counter
shared by all workers (env AUDIO_SPEND_FILE, written with a lock; tools/build/start_area.sh sets it). At the cap (env
AUDIO_SPEND_CAP, no default: no cap means no paid call) every further call stops with a clear message; a provider
quota_exceeded also stops further calls for the run instead of retrying. Never print or log a key.
Tests with a fake client (no network): counter shared and locked, cap stops calls, quota_exceeded stops the run.
Lane: tools/assetgen.py (audio paths only), asset-tools.json (audio entries), tests/test_assetgen*.py,
pipeline/audio/build/*.py (only the API-call wrapper lines). Done: tests OK; commit, stop.
