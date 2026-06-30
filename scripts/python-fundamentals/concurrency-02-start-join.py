"""看懂 thread 的 start() 和 join()，尤其是 join()。

核心问题：join() 到底解决什么？答案——它保证「worker 已经跑完，结果(result)就绪」。

下面用一个「共享结果(shared result)」演示：worker 算完才把 42 写进 box。
  - 场景 A：在 join 之前就读 → 读到 None（worker 还没算完）——这就是 bug。
  - 场景 B：先 join 再读 → 读到 42（join 保证 worker 已结束）。
  - 场景 C：多线程时，start/join 的循环顺序决定 并发(concurrent) 还是 串行(serial)。

注意 A 和 B 的差别不是「有没有 join」，而是「在 join 的哪一边用结果」。

    python3 concurrency-02-start-join.py
"""

import threading
import time

START = time.perf_counter()


def log(who, msg):
    """打印一行带「从程序启动到现在过了多少秒」的时间戳(timestamp)。"""
    elapsed = time.perf_counter() - START
    print(f"[{elapsed:5.2f}s] {who:<7}| {msg}")


def make_worker(box, secs):
    """返回一个 worker：睡 secs 秒（模拟干活），算完才把结果写进 box。"""
    def worker():
        log("worker", f"开始计算，需要 {secs}s")
        time.sleep(secs)
        box["result"] = 42                 # 干完活才写入结果
        log("worker", "结果写好了：box['result'] = 42")
    return worker


# ---------------------------------------------------------------------------
# 场景 A：在 join 之前就读结果 —— 主线程没等，读到 None（bug）
# ---------------------------------------------------------------------------
def scene_a():
    print("\n=== A. 不等就读：start() 之后【立刻】读结果 ===")
    box = {}
    t = threading.Thread(target=make_worker(box, 2))
    t.start()                              # 点火：worker 开始在后台跑
    # ↓↓↓ 关键：这里【还没 join】，主线程直接往下读
    log("main", f"start() 后马上读 → box.get('result') = {box.get('result')}   ← None！worker 还没算完")
    log("main", "主线程没等 worker 就用结果了 → 拿到空的（这就是缺 join 的 bug）")
    t.join()                               # 仅为收尾：别让线程泄漏，和上面的演示无关
    log("main", f"（收尾 join 之后再看 → box['result'] = {box.get('result')}）")


# ---------------------------------------------------------------------------
# 场景 B：join 之后再读结果 —— 主线程等 worker 算完，读到 42
# ---------------------------------------------------------------------------
def scene_b():
    print("\n=== B. 等了再读：start() 之后【先 join()】再读结果 ===")
    box = {}
    t = threading.Thread(target=make_worker(box, 2))
    t.start()
    log("main", "调用 t.join()，在读结果之前先把 worker 等完……（被阻塞 blocking）")
    t.join()                               # 关键：读之前就 join，确保 worker 一定算完
    log("main", f"join() 之后再读 → box.get('result') = {box.get('result')}   ← 42，保证就绪")


# ---------------------------------------------------------------------------
# 场景 C：多线程时，start/join 的循环顺序决定 并发 vs 串行
# ---------------------------------------------------------------------------
def run_two_loops():
    """✅ 先全部 start（一起开跑），再全部 join（一起等）→ 并发。"""
    ts = [threading.Thread(target=time.sleep, args=(1,)) for _ in range(3)]
    s = time.perf_counter()
    for t in ts:
        t.start()                          # 3 个线程几乎同时开跑
    for t in ts:
        t.join()                           # 等它们各自结束（它们正在并发地睡）
    return time.perf_counter() - s


def run_start_join_together():
    """❌ start 完立刻 join → 等这个跑完才启动下一个 → 串行。"""
    s = time.perf_counter()
    for _ in range(3):
        t = threading.Thread(target=time.sleep, args=(1,))
        t.start()
        t.join()                           # 在这里就等死了，下一个线程还没生出来
    return time.perf_counter() - s


def scene_c():
    print("\n=== C. start/join 的循环顺序：并发还是串行？===")
    print(f"先全 start 再全 join（并发）-> {run_two_loops():.2f}s   理论 ≈ 1s")
    print(f"start 完马上 join（串行）   -> {run_start_join_together():.2f}s   理论 ≈ 3s")


if __name__ == "__main__":
    scene_a()
    scene_b()
    scene_c()
    print("\n要点：join() 让【调用者】等到该线程结束、结果就绪；区别在你于 join 的哪一边用结果。")
