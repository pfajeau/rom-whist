Video conferencing (Galene)
===========================

Each game can optionally have an associated [Galene](https://galene.org) video
room. The room is created by the game creator when the game is created (there
is also an *Enable video chat* button on the game page for the owner). Players
then get a **Join video** button which opens the room in its own browser window,
so the game page is left untouched.

The room is named after the game: `<GALENE_GROUP_PREFIX>-<game type>-<game id>`,
e.g. `cards-whist-42`. The game type is part of the name because game ids are
allocated independently per game type.

All of the integration lives in `romwhist/galene/`:

| Module | Responsibility |
|---|---|
| `config.py` | Reads the `GALENE_*` settings and derives group/URL names |
| `client.py` | Thin wrapper over Galene's administrative HTTP API |
| `service.py` | Room lifecycle, per-player join tokens, cleanup |

Game modules only call the helpers in `common_routes`: `create_video_room`,
`video_context`, and the owner action handled by `redirect_game_start`.
Consequently `clean_game_data` and `clean_old_games` take a game type so that
rooms are removed alongside their game.


Galene server setup
-------------------

Galene must run with group definitions writable, and needs an administrator
account for the game server:

```json
{
  "canonicalHost": "meet.example.org",
  "writableGroups": true,
  "users": {
    "romwhist": {
      "password": {"type": "bcrypt", "key": "$2a$12$..."},
      "permissions": "admin"
    }
  },
  "allowOrigin": ["https://cards.fajor.ca"]
}
```

`writableGroups` is disabled by default; without it every group creation fails
with `403`. The `allowOrigin` entry is only needed if the game page embeds
Galene; the default setup opens Galene in its own window and does not.

The hash is produced with `galenectl hash-password`.

Behind a reverse proxy also set `proxyURL` in the same file, and remember that
browsers require HTTPS for camera and microphone access.


Application configuration
-------------------------

Add the setting below to `instance/config.py` (it is not version controlled):

```python
GALENE_ENABLED = True
GALENE_API_URL = "https://meet.example.org"
# Only needed when Flask reaches Galene on a different address than browsers do
GALENE_PUBLIC_URL = "https://meet.example.org"
GALENE_ADMIN_USER = "romwhist"
GALENE_ADMIN_PASSWORD = "..."
```

| Setting | Default | Meaning |
|---|---|---|
| `GALENE_ENABLED` | `False` | Master switch. While off, no Galene call is ever made |
| `GALENE_API_URL` | | Base URL used by the server side API calls |
| `GALENE_PUBLIC_URL` | `GALENE_API_URL` | Base URL used in links for browsers |
| `GALENE_ADMIN_USER` / `GALENE_ADMIN_PASSWORD` | | Galene administrator credentials |
| `GALENE_GROUP_PREFIX` | `cards` | Prefix of generated group names |
| `GALENE_PERMISSIONS` | `["present", "message"]` | Permissions granted to each join token |
| `GALENE_MAX_EXTRA_CLIENTS` | `1` | Seats on top of the number of players |
| `GALENE_TOKEN_TTL_HOURS` | `0` | Room and token lifetime; `0` uses `GAME_EXPIRATION_HOURS` |
| `GALENE_VERIFY_TLS` | `True` | TLS verification for API calls |
| `GALENE_TIMEOUT_SECONDS` | `3` | API call timeout |

If `GALENE_ENABLED` is on but a required value is missing, an error is logged at
startup and the feature stays disabled. Video problems never prevent a game from
being created or played.


How a player joins
------------------

When a player enters a game, the server creates (once) a Galene *stateful token*
bound to that player's alias and returns a link of the form:

```
https://meet.example.org/group/cards-whist-42/?token=<token>
```

Galene's own frontend reads the `token` query parameter, authenticates with it
and then removes it from the address bar. The username and permissions therefore
come from the token and cannot be spoofed by the client.

The button opens the room in its own **popup window** (via `window.open` with
window features) rather than a tab. Browsers only allow that from a user
gesture, so the window is opened from the click handler, never on page load.
The element is still an `<a>` with `target` and a valid `href`, so when a popup
is blocked the room simply opens in a tab instead. While the window stays open,
further clicks focus it rather than opening another one.

Tokens are cached per alias, so refreshing the game page does not create new
ones. They expire with the room.

Permissions are the internal Galene permission names: `present` implies the
right to send audio and video, `message` the right to chat. Do not use the
friendly names such as `presenter`; the token API expects the internal values.


Enabling and disabling from the game page
------------------------------------------

The owner sees a button that toggles video chat at any time. It is handled over
the game's websocket (`video state changed`), never by submitting the page form,
so the game page is neither reloaded nor navigated away from. Every client in
the room gets the event and updates its buttons in place; players other than the
owner see only the *Join video* link appear or disappear.

The server refuses a toggle from anyone but the owner (`not_owner`), and the
room is only created when the feature is enabled and Galene answers.

Lifecycle and cleanup
---------------------

Rooms are removed when:

* the owner stops the game or presses *Disable video chat*;
* a game is discarded by `clean_game_data`;
* `clean_old_games` expires a game older than `GAME_EXPIRATION_HOURS`;
* the periodic sweeper detects a group whose game no longer exists.

The sweeper runs in a daemon thread started by `create_app`, with an immediate
first pass so groups left behind by a previous process are removed at startup.
Its interval is `GALENE_SWEEP_INTERVAL_SECONDS` (default 900) and it can be
turned off with `GALENE_SWEEP_ENABLED`. Live games are supplied by
`common_routes.live_video_games()`; the sweeper only touches groups belonging to
the game types it is given, so one game type's sweep never removes another's
rooms.

Token deletion is always attempted before the group is deleted, because Galene
leaves a group's tokens behind when the group is deleted.

If a game id is reused, the leftover group from the previous game is purged and
recreated, so old invitation links cannot reach the new room.

The room registry is held in memory, like the games themselves. This matches the
current deployment, which runs a single `gunicorn` worker. Group names are
derived from the game type and id, so a restarted process can still recognise
and delete rooms it did not create.

When Galene is unreachable, the failure is logged and further calls are skipped
for 30 seconds so an outage does not add a timeout to every page render.


Galene API notes
----------------

Verified against Galene 1.2.1:

* `PUT /galene-api/v0/.groups/<group>/` with `If-None-Match: *` creates a group
  (`201`), and returns `412` when it already exists.
* `HEAD /galene-api/v0/.groups/<group>/` returns the entity tag needed by
  `DELETE`, which returns `204`.
* `POST /galene-api/v0/.groups/<group>/.tokens/` creates a stateful token and
  returns its name in the `Location` header (`201`). A `GET` on the same path
  returns the entity tag needed for updates and deletion.
* An empty group or token list is serialised as `null`, not `[]`.
* Naming a token explicitly with `PUT .../.tokens/<name>` crashes the 1.2.x
  server with a nil dereference when the token does not exist yet, so tokens are
  always created with `POST` and the generated name is reused.
* Deleting a group does not delete its tokens.

The API path is versioned (`/v0/`); `GaleneConfig.api_base` is the single place
that would need updating for a future version.


Tests
-----

```sh
venv/bin/python -m pytest tests/test_galene.py -q
```

The tests cover configuration handling, the exact HTTP requests sent, token
caching and refresh, room teardown, sweeping, and the route level behaviour that
a Galene outage must not prevent a game from being created.
