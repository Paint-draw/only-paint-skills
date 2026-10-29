"""端到端脚本骨架：按「业务闭环」记录结果，失败也落盘。

报告里的「端到端 N 条」只认这里写出的结果文件，所以每一步都要么 PASS、要么 FAIL，
不要用 try/except 把失败吞掉——吞掉的那条在报告里就是一句假话。

用法：

    from harness import Harness

    h = Harness("e2e_full")
    with h.flow("01 认证：管理员登录") as step:
        token = login("admin")
        step["detail"] = "1 个身份"
    h.save()

产物：test/results/e2e_full.json
[{"flow": "...", "status": "PASS", "detail": "...", "seconds": 0.4}, ...]

路径与目标服务都可用环境变量覆盖：
    TEST_BASE_URL   默认 http://localhost:8080
    TEST_RESULTS_DIR 默认为 test/results
"""
from __future__ import annotations

import json
import os
import time
import traceback
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8080").rstrip("/")
RESULTS_DIR = Path(os.environ.get("TEST_RESULTS_DIR", "test/results"))


class Harness:
    def __init__(self, name: str, results_dir: Path | str | None = None):
        self.name = name
        self.dir = Path(results_dir) if results_dir else RESULTS_DIR
        self.items: list[dict] = []

    # ---- 记录 ---------------------------------------------------------
    @contextmanager
    def flow(self, title: str):
        """一个业务闭环。块内抛异常即记为 FAIL，不会中断后续步骤。"""
        started = time.time()
        step: dict = {"detail": ""}
        try:
            yield step
            status = "PASS"
        except Exception as exc:  # noqa: BLE001 - 失败要落盘，不能吞掉
            status = "FAIL"
            step["detail"] = (step.get("detail") or "") + f" | {type(exc).__name__}: {exc}"
            traceback.print_exc()
        finally:
            self.items.append({
                "flow": title,
                "status": status,
                "detail": step.get("detail", ""),
                "seconds": round(time.time() - started, 2),
            })
            mark = "PASS" if status == "PASS" else "FAIL"
            print(f"[{mark}] {title}  {self.items[-1]['detail']}")

    def expect(self, condition, message: str):
        """断言失败要带人话，报告里的 detail 直接读它。"""
        if not condition:
            raise AssertionError(message)

    def save(self) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        out = self.dir / f"{self.name}.json"
        out.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
        ok = sum(1 for i in self.items if i["status"] == "PASS")
        print(f"\n共 {len(self.items)} 条，PASS {ok}，FAIL {len(self.items) - ok} → {out}")
        return out


# ---- 最小 HTTP 客户端 ---------------------------------------------------
def call(method: str, path: str, body=None, token: str | None = None, timeout: int = 30):
    """返回 (HTTP 状态码, 解析后的 body)。body 不是 JSON 时退回原文。"""
    url = path if path.startswith("http") else BASE_URL + path
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    try:
        return status, json.loads(raw or b"{}")
    except json.JSONDecodeError:
        return status, raw.decode("utf-8", "replace")
