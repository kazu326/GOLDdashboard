from __future__ import annotations

import json

from app import db
from app.services import refresh_dashboard


def main() -> None:
    with db.session() as conn:
        payload = refresh_dashboard(conn)
    print(json.dumps({"status": "ok", "snapshot_id": payload["snapshot_id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

