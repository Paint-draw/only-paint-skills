"""只读接口 × 角色 冒烟矩阵：定位「菜单看得见、接口调不通」。

只打 GET，不改任何数据。跑完把矩阵写进 test/results/smoke_matrix.json，
报告里「接口矩阵 N 次调用」就从这份结果读。

改这三处就能用到别的项目：
    ROLES   角色与登录账号
    PATHS   只读接口清单
    login() 登录方式（默认账号密码 → /api/auth/login）
口令从环境变量读，不要写死。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from harness import call

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8080").rstrip("/")
PASSWORD = os.environ.get("TEST_PASSWORD", "")
RESULT = Path(os.environ.get("TEST_RESULTS_DIR", "test/results")) / "smoke_matrix.json"

ROLES = [
    ("admin", "管理员"),
    ("operator", "运营"),
    ("viewer", "只读"),
]
PATHS = [
    "/api/me",
    "/api/users",
]


def login(account: str) -> str | None:
    _, d = call("POST", "/api/auth/login", {"account": account, "password": PASSWORD})
    if isinstance(d, dict) and d.get("code") == 0:
        return (d.get("data") or {}).get("accessToken")
    print(f"登录失败 {account}: {d}")
    return None


def cell(status: int, body) -> str:
    if status == 403:
        return "403"
    code = body.get("code") if isinstance(body, dict) else None
    if code == 0:
        return "ok"
    if code == 403:
        return "403"
    return f"ERR:{code} {body.get('message', '') if isinstance(body, dict) else status}"


def main() -> int:
    tokens = {account: login(account) for account, _ in ROLES}

    header = f"{'端点':40s}" + "".join(f"{label:<12s}" for _, label in ROLES)
    print(header)
    matrix: dict[str, dict[str, str]] = {}
    problems: list[dict] = []

    for path in PATHS:
        row = {}
        for account, _ in ROLES:
            token = tokens[account]
            if not token:
                row[account] = "NO-LOGIN"
                continue
            status, body = call("GET", path, None, token)
            row[account] = cell(status, body)
        matrix[path] = row
        print(f"{path:40s}" + "".join(f"{row[a]:<12s}" for a, _ in ROLES))
        for account, value in row.items():
            if value.startswith("ERR") or value in ("NO-LOGIN",):
                problems.append({"path": path, "account": account, "result": value})

    print("\n非权限类异常（可能是真故障）:")
    for p in problems:
        print(f"  {p['path']} [{p['account']}] → {p['result']}")
    if not problems:
        print("  无")

    # 每个格子一条：403 是权限边界内的预期结果，记 SKIP，不算失败
    items = []
    for path, row in matrix.items():
        for account, value in row.items():
            status = "PASS" if value == "ok" else ("SKIP" if value == "403" else "FAIL")
            items.append({"flow": f"{account} {path}", "status": status, "detail": value})

    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps({
        "name": "smoke_matrix",
        "kind": "matrix",
        "base_url": BASE_URL,
        "roles": [label for _, label in ROLES],
        "paths": PATHS,
        "matrix": matrix,
        "problems": problems,
        "count": len(items),
        "items": items,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写 {RESULT}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
