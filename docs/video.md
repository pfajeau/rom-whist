Video conferencing
===================

Each game can optionally have an associated video conference room. The
application supports several video backends behind one interface: game code
never mentions a specific service, and the implementation used is chosen by
configuration and loaded at run time.

Galene is one such backend. Its setup guide is in [galene.md](galene.md).


Architecture
------------

```
romwhist/video/              provider-neutral API
  base.py                    VideoService, VideoRoom, VideoToken
  errors.py                  VideoError, VideoUnavailable, VideoConflict
  config.py                  VideoConfig, read from the VIDEO_* settings
  managed.py                 ManagedVideoService: registry, cooldown, sweeper
  factory.py                 provider registry, loaded lazily by name
  null.py                    NullVideoService, an inert implementation
  galene/                    one provider
    config.py                GALENE_* settings
    client.py                Galene administrative HTTP API
    service.py               GaleneService(ManagedVideoService)
```

Layering rules, enforced by `tests/test_video.py`:

* Nothing outside `romwhist/video/galene/` mentions Galene, except the provider
  table in `video/factory.py`.
* No module imports a concrete provider. The factory resolves the configured
  name with `importlib` when the service is created, so selecting `none` never
  imports any backend.
* Provider settings are read by the provider. `VideoConfig` only carries what
  every video service needs, so adding a provider requires no change to the
  core.

`ManagedVideoService` owns everything that is not specific to a backend: the
in-memory room registry, per-player token caching and refresh, the
unavailability cooldown, and the sweeper thread. A provider implements only
these primitives:

| Method | Responsibility |
|---|---|
| `room_name(game_type, game_id)` | Provider identifier for a game's room |
| `_remote_create(room)` | Create the remote room; raise `VideoConflict` if it exists |
| `_remote_destroy(room)` | Delete the room and any credential attached to it |
| `_remote_mint_token(room, alias)` | Create a credential for one player |
| `_remote_join_url(room, alias, token)` | Build that player's join URL |
| `_remote_list_rooms()` | List every room the provider knows about |
| `_parse_names(names, live)` | Map remote room names back to game types |

`VideoService.page_context()` always returns the same four keys, which the game
templates pass to `add_video_button()` in `game_common.js`:

```python
{
    "video_enabled": bool,      # a room exists for this game
    "video_available": bool,    # a provider is configured and usable
    "video_owner": bool,        # may enable or disable video
    "video_join_url": str|None, # this player's personal join link
}
```


Configuration
-------------

Add the settings below to `instance/config.py` (it is not version controlled):

```python
VIDEO_PROVIDER = "galene"     # "none" | "galene" | another registered provider
VIDEO_ENABLED = True          # master switch
VIDEO_SWEEP_ENABLED = True
VIDEO_SWEEP_INTERVAL_SECONDS = 900
```

| Setting | Default | Meaning |
|---|---|---|
| `VIDEO_PROVIDER` | `none` | Which provider to use |
| `VIDEO_ENABLED` | provider != `none` | Master switch |
| `VIDEO_SWEEP_ENABLED` | `True` | Purge rooms whose game no longer exists |
| `VIDEO_SWEEP_INTERVAL_SECONDS` | `900` | Sweeper period |

An unknown provider, or a provider that cannot be imported, is reported once at
startup and video stays off; gameplay is never affected. Settings without a
`VIDEO_PROVIDER` but with `GALENE_ENABLED = True` are treated as Galene, with a
deprecation warning, so existing installations keep working.

Provider-specific settings stay provider-scoped. For Galene, see
[galene.md](galene.md).


Runtime wiring
--------------

`create_app()` calls `romwhist.video.configure(app, live_games_provider=...)`
once, which builds the process-wide service and starts the sweeper when the
provider is enabled. Application code then only calls `romwhist.video.get_service()`:

```python
from romwhist import video

service = video.get_service()
```

The game route modules never do this themselves: they call the helpers in
`common_routes`, which are already provider neutral:

| Helper | Purpose |
|---|---|
| `create_video_room` | Create the room of a new game when the creator asked for it |
| `video_context` | Template context for the video button |
| `toggle_video` | Owner-only websocket action to enable or disable video |
| `join_video_chat` | Hand a player its own join URL |
| `clean_game_data`, `clean_old_games` | Tear rooms down with their game |
| `live_video_games` | Game ids per type, supplied to the sweeper |


Adding a provider
-----------------

1. Create `romwhist/video/<name>/` with a `create_service(app_config,
   video_config, expiration_hours)` factory returning a `VideoService`.
2. For room bookkeeping and cleanup, subclass
   `romwhist.video.managed.ManagedVideoService` and implement the primitives
   listed above; read that provider's own settings in its `config.py`.
3. Add the name to the `_PROVIDERS` table in `romwhist/video/factory.py`, or call
   `romwhist.video.register_provider()` before `configure()`.
4. Select it with `VIDEO_PROVIDER = "<name>"`. No other file changes.
5. Add a test module next to `tests/test_video_galene.py`. The generic checks in
   `tests/test_video.py` (no provider leakage, inert default, factory
   behaviour) apply automatically.


Tests
-----

```sh
venv/bin/python -m pytest tests/test_video.py tests/test_video_galene.py -q
```
