"""Threads vs asyncio：同样的 I/O-bound 工作，几种跑法的耗时对比。

跑这个文件你会看到（N=10，每个任务等待约 0.5s，理想并发耗时 ≈ 0.5s）：
  1. sequential (blocking)         -> 约 5.0s  完全串行，一个接一个
  2. threads (ThreadPoolExecutor)  -> 约 0.5s  I/O 等待时释放 GIL，等待相互重叠
  3. asyncio (await asyncio.sleep) -> 约 0.5s  单线程，await 时让出事件循环
  4. asyncio + time.sleep (BUG)    -> 约 5.0s  在协程里用阻塞调用 → 卡死事件循环

结论：
  - threads 和 asyncio 都能把 I/O 等待重叠起来，对 I/O-bound 任务都有效；
  - 但 asyncio 是「协作式」的，一旦在协程里调用阻塞函数（time.sleep / requests 等），
    整个事件循环停摆，并发优势立刻消失 —— 见第 4 个例子。

    python3 concurrency-02.py
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

N_TASKS = 10
IO_SECONDS = 0.5  # 模拟一次网络/磁盘 I/O 的耗时


# --- 被调用的「工作」：一次 I/O-bound 操作（用 sleep 模拟等待） ---
def blocking_io(i):
    time.sleep(IO_SECONDS)            # 阻塞当前线程；真实场景是 requests.get / 读文件
    return i


async def async_io(i):
    await asyncio.sleep(IO_SECONDS)   # 协程版等待：让出事件循环，不阻塞线程
    return i


# 1. 顺序执行：一个接一个，总耗时 ≈ N * IO_SECONDS
def run_sequential():
    return [blocking_io(i) for i in range(N_TASKS)]


# 2. 线程池：每任务一个线程，I/O 等待期间 GIL 被释放，等待相互重叠
def run_threads():
    with ThreadPoolExecutor(max_workers=N_TASKS) as pool:
        return list(pool.map(blocking_io, range(N_TASKS)))


# 3. asyncio：单线程事件循环，gather 并发调度所有协程
def run_asyncio():
    async def main():
        return await asyncio.gather(*(async_io(i) for i in range(N_TASKS)))
    return asyncio.run(main())


# 4. 坑：在协程里用阻塞的 time.sleep，事件循环被卡住 → 退化成串行
def run_asyncio_blocking():
    async def bad(i):
        time.sleep(IO_SECONDS)        # ❌ 阻塞！其它协程根本拿不到执行机会
        return i

    async def main():
        return await asyncio.gather(*(bad(i) for i in range(N_TASKS)))
    return asyncio.run(main())


def timed(label, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"{label:<34} -> {elapsed:5.2f}s  (完成 {len(result)} 个)")
    return elapsed


if __name__ == "__main__":
    print(f"N_TASKS={N_TASKS}，每个任务 I/O 约 {IO_SECONDS}s，理想并发耗时 ≈ {IO_SECONDS}s\n")
    timed("1. sequential (blocking)", run_sequential)
    timed("2. threads (ThreadPoolExecutor)", run_threads)
    timed("3. asyncio (await asyncio.sleep)", run_asyncio)
    print()
    timed("4. asyncio + time.sleep (BUG)", run_asyncio_blocking)
    print("\n注意 4 ≈ 1：在 async 函数里用阻塞调用会卡死事件循环，并发优势消失。")
