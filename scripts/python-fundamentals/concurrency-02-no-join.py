"""不 join，也能看到 worker 的结果吗？——能，只要读的时候它已经跑完了。

这说明：worker 线程是【独立运行(independent)】的，结果由它自己写入；
join() 不负责"交付结果"，它只负责"保证你读之前 worker 已经结束"。
不 join 就只能自己【赌时间(race)】——赌对了看到结果，赌错了照样读到 None。

    python3 concurrency-02-no-join.py
"""

import threading
import time

START = time.perf_counter()
box = {}                       # worker 把结果(result)写进这里


def worker():
    time.sleep(2)              # 干活 2 秒（模拟 I/O 或计算）
    box["result"] = 42         # 算完才写入结果


def show(msg):
    elapsed = time.perf_counter() - START
    print(f"[{elapsed:4.1f}s] {msg} box.get('result') = {box.get('result')}")


t = threading.Thread(target=worker)
t.start()                      # 启动 worker —— 但全程【绝不调用 t.join()】

show("刚 start，立刻读 ->")     # worker 还在睡，结果还没写 → None

time.sleep(3)                  # main 自己等 3 秒（> worker 的 2 秒）
                               # ⚠️ 注意：这是在"赌" worker 3 秒内一定跑完
show("等 3 秒后再读 ->")        # worker 早写完了，没 join 也能看到 → 42

print("\n结论：")
print("  · 不 join 也能拿到结果 —— 前提是【读的时候 worker 恰好已结束】；")
print("  · 但 time.sleep(3) 是在赌时间，万一 worker 要跑 5 秒，就又读到 None；")
print("  · join() 就是'不靠赌'的正解：它精确地等到 worker 真正结束，一秒都不多等。")
