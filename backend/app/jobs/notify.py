from __future__ import annotations

import json

from app import db
from app.discord import send_discord_summary
from app.services import current_dashboard


def main() -> None:
    with db.session() as conn:
        snapshot = current_dashboard(conn)
        result = send_discord_summary(conn, snapshot)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

