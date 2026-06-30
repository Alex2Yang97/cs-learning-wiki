# Deployment & Ops

把服务从「能在本地跑」做到「在生产环境（production）里稳定、可重复、可观测地
运行」，需要一整套知识：打包、CI/CD、基础设施即代码（Infrastructure as Code,
IaC）、云上运行形态、发布策略和可观测性（observability）。

这一节是一张学习路线图（roadmap），按「从代码到生产，再到长期运行」的顺序组织。
每个子主题先讲**是什么 / 为什么**，再列**关键词**和**该学什么**。

## 路线图 / Roadmap

### 1. From code to production / 从代码到生产

- **是什么**：理解一次「部署」到底发生了什么 —— 构建（build）→ 测试（test）→
  发布（release）→ 运行（run）；以及多环境（multi-environment）：开发 dev /
  预发 staging / 生产 production。
- **关键词**：环境一致性（environment parity）、配置与代码分离、十二要素应用
  （Twelve-Factor App）、不可变部署（immutable deployment）、构建产物（artifact）。
- **该学什么**：为什么「在我机器上能跑」不够；rollback（回滚）为何必须简单。

### 2. Containers / 容器（Docker）

- **是什么**：把「应用 + 依赖 + 运行环境」打包成一个可移植的镜像（image），
  到哪儿都能一致地跑起来。
- **关键词**：镜像（image）/ 容器（container）/ 镜像仓库（registry）、Dockerfile、
  层（layer）、多阶段构建（multi-stage build）。
- **该学什么**：写一个 Dockerfile；镜像与容器的区别；容器如何让「环境一致」成立。

### 3. CI/CD / 持续集成与持续交付

- **是什么**：把构建、测试、部署自动化。CI（Continuous Integration，持续集成）=
  每次提交自动构建 + 测试；CD（Continuous Delivery / Deployment，持续交付 / 部署）=
  自动发布到（准）生产。
- **关键词**：流水线（pipeline）、阶段 / 任务 / 执行器（stage / job / runner）、
  触发器（trigger）、门禁（gate）、GitHub Actions。
- **该学什么**：一个最小的 GitHub Actions 工作流（这个 wiki 自己就用它部署）；
  自动化为什么能降低发布风险。

### 4. Infrastructure as Code (IaC) / 基础设施即代码

- **是什么**：用代码（而不是点控制台）来声明和管理服务器、网络、数据库等基础设施
  —— 可版本化、可重复、可审计。
- **关键词**：声明式 vs 命令式（declarative vs imperative）、Terraform、
  状态（state）、plan / apply、幂等（idempotent）、漂移（drift）。
- **该学什么**：declarative 为什么优于手点；state 文件是干什么的；plan 与 apply 的区别。

### 5. Cloud infrastructure & compute / 云基础设施与计算形态

- **是什么**：服务最终要跑在某种计算资源上 —— 理解不同「运行形态」及其取舍。
- **关键词**：虚拟机（VM）/ 容器服务（如 ECS）/ 无服务器（serverless，如 Lambda）/
  托管平台（PaaS）、负载均衡（load balancer）、DNS、虚拟网络（VPC / networking）。
- **该学什么**：VM vs 容器 vs serverless 的取舍（成本、运维、冷启动）；流量怎么进到你的服务。

### 6. Orchestration / 容器编排（Kubernetes）

- **是什么**：当实例多到单机管不过来时，用编排系统统一调度、扩缩容、自愈。
- **关键词**：Kubernetes (K8s)、Pod / Deployment / Service、调度（scheduling）、
  自动扩缩容（autoscaling）、自愈（self-healing）。
- **该学什么**：什么时候才真的需要 K8s（不要过早上）；最小的 Deployment + Service 长什么样。

### 7. Configuration & secrets / 配置与密钥管理

- **是什么**：把配置和敏感信息（密钥、密码、证书）安全地注入运行环境，而不是写死在代码里。
- **关键词**：环境变量（env var）、ConfigMap / Secret、密钥管理服务（secret manager，
  如 AWS Secrets Manager / Vault）、最小权限（least privilege）。
- **该学什么**：为什么 secret 不能进 git；配置怎么按环境切换。

### 8. Release strategies / 发布策略

- **是什么**：怎么把新版本安全地推给用户，出问题能快速止血。
- **关键词**：滚动发布（rolling）、蓝绿（blue-green）、金丝雀（canary）、
  健康检查（health check）、回滚（rollback）、特性开关（feature flag）。
- **该学什么**：每种策略的取舍；health check 怎么决定一个实例是否就绪 / 健康。

### 9. Observability & reliability / 可观测性与可靠性

- **是什么**：服务上线后怎么知道它「健康」，出事怎么发现、定位、复盘。
- **关键词**：三大支柱 —— 日志（logs）/ 指标（metrics）/ 链路追踪（traces）、
  告警（alerting）、SLI / SLO / 错误预算（error budget）、值班与事故复盘
  （on-call / postmortem）。
- **该学什么**：logs / metrics / traces 各解决什么问题；SLO 怎么定；好的告警长什么样。

## Articles

*No articles yet.* 想深入某个子主题时，在本文件夹新建一个 `.md`，把它列到上面，
并在 `mkdocs.yml` 的 **Deployment & Ops** 下注册即可。
