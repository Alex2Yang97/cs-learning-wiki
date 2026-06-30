---
tags:
  - python
  - basics
---

# Concurrency

## Fundamentals

- A process is an isolated container with its own address space and resources. Inside that process, the OS or language runtime can create one or more threads.
- A thread is an independent execution path. It has its own program counter, registers, and stack, but it shares the heap, globals, and open resources with other threads in the same process.

On multi-core machines, threads may run in parallel.
On a single core, the OS rapidly switches between threads and interleaves their instructions.

From the program's point of view, both cases are the same: operations from different threads can interleave in unpredictable ways. That unpredictability is the root of concurrency bugs. Code that looks atomic at the source level is often multiple machine instructions.

## Toolbox

### 1. Atomics 原子操作

Python 是一个特殊情况，它缺乏原生的原子操作，所以你需要用锁来安全地跨线程递增计数器。也就是说，Java 有 AtomicInteger，Go 有 sync/atomic，但 Python 没有原生 atomics，只能退化成用 Lock 模拟：

> Atomics（原子操作） 是 CPU 硬件层面直接支持的指令，比如 CAS（compare-and-swap）。这是一条机器指令，执行过程不可能被打断

```python
import threading

lock = threading.Lock()
counter = 0

def increment():
    global counter
    with lock:
        counter += 1  # 用 Lock 模拟原子递增（Python 没有原生 atomics）
```

> **注意：不加锁的 `counter += 1` 在 CPython 上常常「碰巧」也对**
>
> 如果把上面的 `with lock:` 去掉，用 10 个线程各自 `+= 1` 十万次，在 CPython 上很可能**仍然**得到 1,000,000。这不代表不需要锁，而是 GIL 的实现细节：
>
> - `counter += 1` 编译成大致 `LOAD → 加 → STORE` 三步，原理上可被打断；
> - 但 **CPython 只在「安全点」切换线程**（函数入口、循环回跳、函数调用等），而这段「读-改-写」中间没有这样的切换点，所以它在 CPython 上**事实上是原子的** —— 因此不加锁也常常正确。
>
> ⚠️ 这是**实现细节，不是语言保证**，不能依赖：一旦读和写之间出现**函数调用**（多了一个切换点）race 立刻重现；free-threaded（无 GIL）的 Python 3.13+ 上这种简单 `+=` 也会丢更新；不同 CPython 版本切换点位置可能变。
>
> 可运行的对比实验见 [`scripts/python-fundamentals/concurrency-01.py`](https://github.com/Alex2Yang97/my-wiki/blob/main/scripts/python-fundamentals/concurrency-01.py)：①加锁、②不加锁的简单 `+=`、③读写之间插入函数调用。在 CPython 3.11 上 ① ② 都得到 1,000,000，而 ③ 会稳定丢失约 ⅔ 的更新：
>
> ```
> 1. LockedCounter       ->   1000000  OK (== 1,000,000)
> 2. UnlockedCounter +=  ->   1000000  OK (== 1,000,000)
> 3. RacyCounter         ->    337346  LOST 662654 updates
> ```
>
> **结论**：简单 `+=` 在 CPython 上「碰巧」原子，是脆弱且不可移植的；要正确，仍然必须加锁。

### 2. Locks / Mutexes 锁（互斥锁）

核心思想：互斥（mutual exclusion）——一个线程持锁时，其他线程想拿同一把锁就会阻塞（block），直到锁被释放。被锁保护的代码段叫 critical section（临界区）。

**真实例子：售票系统超卖（check-then-act 竞争）。** 典型 bug 模式是「先检查、再修改」：先确认还有票，再扣减库存。两步之间只要有任何工作（这里是 `charge_card` 调用支付网关，有网络延迟），别的线程就会趁这个空档也通过检查，于是卖出的票超过库存。把整个「检查 + 扣减」放进同一个临界区，才能保证它不可分割。

```python
def attempt(buyer):
    if store["remaining"] > 0:     # 检查：还有票吗？
        charge_card(buyer)          # 扣款（有网络延迟）—— 空档里别人也通过了检查
        store["remaining"] -= 1     # 扣减库存
        store["sold"] += 1

def buy(buyer):
    barrier.wait()                  # 让 200 个买家同时冲向临界区，放大竞争
    with lock:                      # ← 去掉这把锁就会超卖
        attempt(buyer)
```

200 个买家抢 10 张票：

```text
加锁    -> 卖出  10 张  OK
不加锁  -> 卖出  61 张  OVERSOLD（超卖！）
```

### 3. Semaphores 信号量

核心思想：信号量是"计数版的锁"。不是简单的锁/不锁二态，而是持有 N 个许可证（permits）。线程先 acquire（获取）一个许可证才能继续，用完 release（释放）。许可证用完时，新来的线程就阻塞等待。

**真实例子：下载限流。** 第三方 API 限制并发数，或连接池只有 N 个连接 —— 不能让所有线程一拥而上。用 `Semaphore(N)` 保证同一时刻最多 N 个线程进入。下面记录「峰值并发数」来验证。

```python
sem = threading.Semaphore(3)        # 最多 3 个并发下载

def download(i):
    with sem:                       # 没有可用许可证时阻塞
        enter()                     # 记录当前并发数 / 峰值
        time.sleep(0.01)            # 模拟下载耗时
        leave()
```

20 个下载任务：

```text
有信号量 -> 峰值并发 3   OK
无信号量 -> 峰值并发 20  (全部一拥而上)
```

### 4. Condition Variables 条件变量

核心思想：让线程能够"高效地等待某个条件成立"，而不是用 while 循环空转浪费 CPU（这叫 busy waiting / 忙等待）。

线程先获取锁，检查某个条件，如果不满足就 wait()。wait() 这个动作会原子地释放锁并让线程休眠；当另一个线程发出信号（signal）时，等待者会被唤醒并重新检查条件

**真实例子：手写有界缓冲区（bounded buffer）。** 生产者/消费者共享一个固定容量的缓冲区：满了生产者要等，空了消费者要等。关键细节：`wait()` 必须放在 `while` 里而不是 `if` —— 被唤醒后必须**重新检查**条件（防止虚假唤醒，以及被唤醒后名额又被别人抢走）。

```python
class BoundedBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []
        self.cond = threading.Condition()

    def put(self, x):
        with self.cond:
            while len(self.items) >= self.capacity:
                self.cond.wait()        # 满了：原子地释放锁 + 休眠
            self.items.append(x)
            self.cond.notify_all()      # 唤醒可能在等「非空」的消费者

    def get(self):
        with self.cond:
            while not self.items:
                self.cond.wait()        # 空了：原子地释放锁 + 休眠
            x = self.items.pop(0)
            self.cond.notify_all()      # 唤醒可能在等「非满」的生产者
            return x
```

### 5. Blocking Queues 阻塞队列

核心思想：把 Queue（队列）和 Condition Variable 的能力打包好，提供线程安全的"生产者-消费者"交接（producer-consumer handoff）。put() 满了就阻塞，get() 空了就阻塞，所有同步细节都封装在内部。

**真实例子：工作队列。** 和上面的有界缓冲区是同一个问题，但 `queue.Queue` 内部已经封装好锁和条件变量，多生产者多消费者也开箱即用。收工时用「毒丸 sentinel」通知每个消费者退出。

```python
q = queue.Queue(maxsize=10)
SENTINEL = object()                  # 毒丸：消费者收到它就退出

def producer(pid):
    for i in range(50):
        q.put((pid, i))              # 队列满时自动阻塞

def consumer():
    while True:
        item = q.get()               # 队列空时自动阻塞
        try:
            if item is SENTINEL:
                return
            process(item)
        finally:
            q.task_done()

# ... 生产者全部 join 后，给每个消费者投一个毒丸 ...
for _ in consumers:
    q.put(SENTINEL)
```

3 生产者 / 4 消费者，每个任务恰好被处理一次：

```text
处理 150/150 个任务，恰好各一次: True
```

> 以上 5 个例子都是可运行的，完整代码（含「加锁 vs 不加锁」对照）见
> [`scripts/python-fundamentals/concurrency-01.py`](https://github.com/Alex2Yang97/my-wiki/blob/main/scripts/python-fundamentals/concurrency-01.py)，
> 直接 `python3 concurrency-01.py` 即可看到每个原语解决的具体问题。

## Three Problem Types

- **Correctness** — when shared state gets corrupted
- **Coordination** — when threads need to hand off work or wait for each other
- **Scarcity** — when resources are limited
