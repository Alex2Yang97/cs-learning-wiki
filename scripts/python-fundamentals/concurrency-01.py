"""并发的 5 个原语，每个配一个可运行的「真实」例子。

直接运行即可看到每个原语解决的具体问题：

    python3 concurrency-01.py

  1. Atomics    计数器：为什么 += 需要保护，以及 GIL 带来的「假象」
  2. Lock       售票系统：check-then-act 竞争导致超卖
  3. Semaphore  下载限流：最多 N 个任务并发
  4. Condition  有界缓冲区：手写生产者/消费者，满了等、空了等
  5. Queue      工作队列：用 queue.Queue 把上面的同步细节打包好

贯穿全篇的结论：简单操作在 CPython 上常常「碰巧」正确，是 GIL 的实现细节，
不是语言保证；要正确，仍然必须显式同步。
"""

import queue
import sys
import threading
import time


# ===========================================================================
# 1. Atomics 原子操作 —— 计数器
# ===========================================================================
N_THREADS = 10
N_ITER = 100_000
EXPECTED = N_THREADS * N_ITER  # 1,000,000


def run_counter(counter):
    """用 N_THREADS 个线程，每个线程调用 counter.increment() N_ITER 次。"""
    def worker():
        for _ in range(N_ITER):
            counter.increment()

    threads = [threading.Thread(target=worker) for _ in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return counter.value


class LockedCounter:
    """加锁：永远正确。"""
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()  # Python 没有 AtomicInteger，用 Lock 保护

    def increment(self):
        with self.lock:
            self.value += 1


class UnlockedCounter:
    """不加锁的简单 +=：在 CPython 上「碰巧」也对。

    self.value += 1 编译成大致 LOAD_ATTR -> BINARY_OP -> STORE_ATTR 三步，
    原理上可被打断。但 CPython 只在「安全点」（函数入口 RESUME、循环回跳
    JUMP_BACKWARD、函数调用 CALL……）才切换线程，这段「读-改-写」中间没有
    切换点，所以它在 CPython 上事实上是原子的 —— 因此不加锁也常常正确。

    ⚠️ 这是实现细节不是保证：free-threaded（无 GIL）的 3.13+ 会丢更新；
    不同 CPython 版本切换点位置可能变；见下面的 RacyCounter。
    """
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1


def _identity(x):
    return x  # 一个真实的函数调用 —— CPython 会在 CALL 处检查是否切换线程


class RacyCounter:
    """读和写之间插入函数调用（切换点），真的会 race。"""
    def __init__(self):
        self.value = 0

    def increment(self):
        v = self.value          # 读
        v = _identity(v) + 1    # 调用处可能被切走，此刻 self.value 还是旧值
        self.value = v          # 写回，可能覆盖掉别的线程的更新


# RacyCounter 的 bug 在任何切换间隔下都存在，但默认间隔（0.005s）下是否丢更新
# 看运气，短程序常「碰巧」全对。把间隔调小让 race 稳定复现 —— 只是让既有的 bug
# 显形，并没有制造它。
RACY_SWITCH_INTERVAL = 1e-5


def demo_atomics():
    print("1. Atomics —— 10 线程各 +=10 万次，期望 1,000,000")

    def report(name, value):
        status = "OK" if value == EXPECTED else f"LOST {EXPECTED - value} updates"
        print(f"     {name:<22} -> {value:>9}  {status}")

    report("LockedCounter", run_counter(LockedCounter()))
    report("UnlockedCounter +=", run_counter(UnlockedCounter()))

    default_interval = sys.getswitchinterval()
    sys.setswitchinterval(RACY_SWITCH_INTERVAL)
    try:
        report("RacyCounter", run_counter(RacyCounter()))
    finally:
        sys.setswitchinterval(default_interval)


# ===========================================================================
# 2. Locks / Mutexes 锁 —— 售票系统（check-then-act 超卖）
#
#    真实 bug 模式：先「检查还有票」，再「扣减库存」。两步之间如果有别的工作
#    （这里是 _charge_card 模拟支付网关的网络往返），别的线程会趁这个空档也
#    通过检查，于是卖出的票超过库存（超卖 / oversell）。
#    把整个 check-then-act 放进锁的临界区，就保证「检查 + 扣减」不可分割。
# ===========================================================================
TICKETS = 10
BUYERS = 200


def _charge_card(buyer):
    time.sleep(0.0002)  # 模拟支付网关的网络往返延迟（同时让出 GIL）


def run_ticket_sale(use_lock):
    lock = threading.Lock()
    barrier = threading.Barrier(BUYERS)  # 让所有买家同时冲向临界区，放大竞争
    store = {"remaining": TICKETS, "sold": 0}

    def attempt(buyer):
        if store["remaining"] > 0:    # 检查：还有票吗？
            _charge_card(buyer)        # 扣款（有延迟）—— 空档里别人也通过了检查
            store["remaining"] -= 1    # 扣减库存
            store["sold"] += 1

    def buy(buyer):
        barrier.wait()
        if use_lock:
            with lock:
                attempt(buyer)
        else:
            attempt(buyer)

    threads = [threading.Thread(target=buy, args=(f"u{i}",)) for i in range(BUYERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return store["sold"]


def demo_lock():
    print(f"2. Lock —— {BUYERS} 个买家抢 {TICKETS} 张票，卖出数不应超过库存")
    sold = run_ticket_sale(use_lock=True)
    print(f"     加锁    -> 卖出 {sold:>3} 张  {'OK' if sold == TICKETS else 'BUG'}")
    sold = run_ticket_sale(use_lock=False)
    flag = "OVERSOLD（超卖！）" if sold > TICKETS else "OK"
    print(f"     不加锁  -> 卖出 {sold:>3} 张  {flag}")


# ===========================================================================
# 3. Semaphores 信号量 —— 下载限流（最多 N 个并发）
#
#    真实场景：第三方 API 限制并发数，或连接池只有 N 个连接。信号量保证同一
#    时刻最多 N 个线程进入临界区。我们记录「峰值并发数」来验证。
# ===========================================================================
DL_LIMIT = 3
DL_WORKERS = 20


def run_downloads(use_semaphore):
    sem = threading.Semaphore(DL_LIMIT)
    meter_lock = threading.Lock()
    state = {"active": 0, "peak": 0}

    def enter():
        with meter_lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])

    def leave():
        with meter_lock:
            state["active"] -= 1

    def download(i):
        if use_semaphore:
            sem.acquire()  # 没有可用许可证时阻塞
        try:
            enter()
            time.sleep(0.01)  # 模拟下载耗时
            leave()
        finally:
            if use_semaphore:
                sem.release()  # 务必释放，即使发生异常

    threads = [threading.Thread(target=download, args=(i,)) for i in range(DL_WORKERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return state["peak"]


def demo_semaphore():
    print(f"3. Semaphore —— {DL_WORKERS} 个下载任务，限流到最多 {DL_LIMIT} 并发")
    peak = run_downloads(use_semaphore=True)
    print(f"     有信号量 -> 峰值并发 {peak}  {'OK' if peak <= DL_LIMIT else 'BUG'}")
    peak = run_downloads(use_semaphore=False)
    print(f"     无信号量 -> 峰值并发 {peak}  (全部一拥而上)")


# ===========================================================================
# 4. Condition Variables 条件变量 —— 手写有界缓冲区
#
#    生产者/消费者：缓冲区满了生产者要等，空了消费者要等。Condition 让线程
#    高效地「等某个条件成立」而不是 while 空转。注意 wait() 必须放在 while
#    里（而不是 if）—— 被唤醒后必须重新检查条件（防止虚假唤醒和竞争唤醒）。
# ===========================================================================
class BoundedBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []
        self.cond = threading.Condition()

    def put(self, x):
        with self.cond:
            while len(self.items) >= self.capacity:
                self.cond.wait()        # 满了：释放锁 + 休眠，被唤醒后重新检查
            self.items.append(x)
            self.cond.notify_all()      # 唤醒可能在等「非空」的消费者

    def get(self):
        with self.cond:
            while not self.items:
                self.cond.wait()        # 空了：释放锁 + 休眠
            x = self.items.pop(0)
            self.cond.notify_all()      # 唤醒可能在等「非满」的生产者
            return x


def demo_condition():
    n_items = 30
    buf = BoundedBuffer(capacity=5)
    produced = list(range(n_items))
    consumed = []

    def producer():
        for x in produced:
            buf.put(x)

    def consumer():
        for _ in range(n_items):
            consumed.append(buf.get())

    p = threading.Thread(target=producer)
    c = threading.Thread(target=consumer)
    p.start()
    c.start()
    p.join()
    c.join()

    ok = consumed == produced  # 单消费者：顺序也应完全一致
    print(f"4. Condition —— 容量 5 的有界缓冲区，生产/消费 {n_items} 个")
    print(f"     消费 {len(consumed)} 个，顺序与内容正确: {ok}")


# ===========================================================================
# 5. Blocking Queues 阻塞队列 —— 工作队列（queue.Queue 把同步打包好）
#
#    和上面的有界缓冲区是同一个问题，但 queue.Queue 内部已经封装好锁和条件
#    变量：put() 满了阻塞、get() 空了阻塞。多生产者多消费者也开箱即用。
#    用「毒丸 sentinel」通知消费者收工。
# ===========================================================================
N_PRODUCERS = 3
N_CONSUMERS = 4
PER_PRODUCER = 50
_SENTINEL = object()  # 毒丸：消费者收到它就退出


def demo_queue():
    q = queue.Queue(maxsize=10)
    processed = []
    plock = threading.Lock()

    def producer(pid):
        for i in range(PER_PRODUCER):
            q.put((pid, i))  # 队列满时自动阻塞

    def consumer():
        while True:
            item = q.get()   # 队列空时自动阻塞
            try:
                if item is _SENTINEL:
                    return
                with plock:
                    processed.append(item)
            finally:
                q.task_done()

    consumers = [threading.Thread(target=consumer) for _ in range(N_CONSUMERS)]
    producers = [threading.Thread(target=producer, args=(p,)) for p in range(N_PRODUCERS)]
    for t in consumers:
        t.start()
    for t in producers:
        t.start()
    for t in producers:
        t.join()
    for _ in consumers:
        q.put(_SENTINEL)  # 每个消费者发一个毒丸
    for t in consumers:
        t.join()

    expected = N_PRODUCERS * PER_PRODUCER
    got = len(processed)
    once = len(set(processed)) == got  # 每个任务恰好被处理一次
    print(f"5. Queue —— {N_PRODUCERS} 生产者 / {N_CONSUMERS} 消费者")
    print(f"     处理 {got}/{expected} 个任务，恰好各一次: {got == expected and once}")


if __name__ == "__main__":
    for demo in (demo_atomics, demo_lock, demo_semaphore, demo_condition, demo_queue):
        demo()
        print()
