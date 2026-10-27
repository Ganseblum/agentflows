# 证据工具用法

入口为插件根下的 `skills/agentflow/scripts/workflow.py`，需要 Python 3.10 或更高版本及 Git；工具本身只用标准库。它不提供模型运行时、沙箱、批准或任务状态系统。执行原则以[执行与验证](execution.md)为准。

## 命令与结果

| 命令 | 必需参数 | 含义 |
| --- | --- | --- |
| seal | `--root --input --output` | 绑定既有计划、请求与授权基线 |
| verify | `--root --sealed --fingerprint` | 检查原请求、计划、HEAD及写范围 |
| run | 同verify及`--output`，可选`--phase green/red` | 固定最终快照并执行精确命令 |
| inventory | `--root --input` | 核对补测文件、功能、用例和批次声明 |
| managed-preview | `--target --content --output`，可选成对标记和新begin标记 | 生成单文件内容预览 |
| managed-apply | `--preview --fingerprint` | 预览仍匹配时应用并读回 |

`--root` 必须是真实Git工作树根。项目内部字段使用正斜线相对路径，拒绝绝对路径、逃逸及用户控制的符号链接。输入/输出参数按当前进程目录解释，示例可使用绝对路径。工作树的 `.git` 可能是文件，临时状态目录应通过 `git rev-parse --git-path agentflow` 确定，而不是假定 `.git/` 永远为目录。

所有业务命令输出 JSON：`operation`、`status`、`error_kind`、`evidence`、`next_action`、`exit_code`。封存指纹位于输出的 `evidence.fingerprint`，也保存在封存文件顶层 `fingerprint`。

| 退出码 | 本次结果 |
| --- | --- |
| 0 | 当前操作满足约定，不等于整个需求完成 |
| 1 | 命令、报告或断言失败 |
| 2 | 参数或输入结构非法 |
| 3 | 拒绝执行：漂移、越界、冲突或已有证据 |
| 4 | 部分任务阻塞或未运行 |

## 执行说明

复制[执行请求模板](../templates/testing/execution-request.json)，替换计划、精确文件和原生命令。示例路径只示意目标项目，不是本插件已有文件。

| 字段 | 规则 |
| --- | --- |
| `plan` | 已有Markdown计划的项目相对路径；不能放进允许写范围 |
| `allowed_writes` | 精确文件数组，不是glob；实现可改变这些文件，但不能改计划或Git元数据 |
| `tasks[].id` | 唯一安全标识，用于日志文件名及依赖 |
| `tasks[].depends_on` | 已存在任务ID，无重复、无环；失败只阻止实际依赖 |
| `tasks[].argv` | 非空参数数组，直接运行且不经shell；工具不保存环境变量值 |
| `tasks[].cwd` | 项目内工作目录，根目录写`.` |
| `tasks[].timeout_seconds` | 正数且不超过3600；输出总量上限为8 MiB |
| `tasks[].kind` | `test`或`preflight`；预检不能冒充行为验证 |
| `tasks[].reporter` | `tap/junit/go/jest`；`exit`只用于无行为用例的预检 |
| `tasks[].cases` | 测试任务非空；每项包含唯一`id`和精确`report_name` |
| `tasks[].report_path` | 可选本次报告文件；执行前不得存在，不得是已跟踪、允许写或其他任务的报告路径 |

测试说明中的计划、请求原文件、HEAD或允许范围以外的输入变化会拒绝旧指纹。实现允许改变 `allowed_writes`；开始验证时重新绑定最终输入，验证过程中的输入改变使证据失效。Git可见的未跟踪和忽略输入也纳入检查，不因忽略规则静默漏掉数据文件。

```sh
python3 <工具路径> seal --root <项目根> --input <请求文件> --output <新封存文件>
python3 <工具路径> verify --root <项目根> --sealed <封存文件> --fingerprint <本次指纹>
python3 <工具路径> run --root <项目根> --sealed <封存文件> --fingerprint <本次指纹> --output <Git行政目录或项目外的新暂存目录>/red --phase red
# 在允许范围内实现；仍使用同一份已确认请求及计划
python3 <工具路径> run --root <项目根> --sealed <封存文件> --fingerprint <本次指纹> --output <Git行政目录或项目外的新暂存目录>/green --phase green
```

每次运行使用新的证据目录。目录不能隐藏计划、源码、允许写文件或已有输入；结果为 `result.json`，每个实际运行任务保留 `<任务ID>.stdout` 与 `.stderr`，文件仅所有者可读。持久化前核实日志已脱敏，权限模式不等于秘密已清除。

多轮验证期间，将请求、封存和运行输出暂存在项目外，或用 `git -C <项目根> rev-parse --git-path agentflow` 找到的Git行政目录内；相对返回值按项目根解析。不要假定工作树的 `.git` 是目录。最后一轮验证结束后，再把脱敏证据归档到项目已有的测试证据目录。项目内上一轮证据也属于可见输入，提前归档会使下一轮旧指纹拒绝执行；工具不会自动忽略整个 `evidence/` 来隐藏这些变化。

使用 `report_path` 的原生runner在下一轮生产报告前，该路径必须重新不存在。先核对上一轮报告归属并移到上述暂存目录保存，再运行；不得复用旧报告或删除不明用户文件。归档后的持久证据仍供人工复核，暂存目录本身不算交付完成证据。

`--phase red` 要求所选目标用例均实际失败且命令非零；未发现用例、runner报错或仅退出非零不能证明有效失败。工具只观察报告，失败原因仍需对照需求和原始输出复核。green要求命令及报告均通过。通过后 `coverage_status` 仍为 `needs_review`，由既有独立评审复核需求、入口和断言。

## 原生报告名称

| 格式 | `report_name` | 完整性约束 |
| --- | --- | --- |
| TAP | 顶层用例的准确名称 | 单一非空计划、顺序完整、无重名或skip/todo；嵌套跳过同样拒绝 |
| JUnit XML | 有classname时为`classname::name`，否则`name` | 本次stdout或新文件，套件计数一致，无跳过；拒绝外部实体声明 |
| Go JSON | `Package/Test` | run及终态事件完整，包与测试结果一致 |
| Jest JSON | `fullName` | 完整JSON、精确计数、套件及总结果一致，无pending/todo |

不支持的输出格式保持失败，不用 `echo`、旧文件或改写测试结果凑格式。报告解析不能防止同权限进程伪造生成器，也不能证明测试断言充分。

## 补测映射

复制[补测映射模板](../templates/testing/backfill-map.json)，逐个核对文件和真实用户行为。

- `files` 必须完整分类当前Git可见文件：`production/test/infrastructure/excluded`，排除项有理由。
- `features` 包含唯一id、真实入口、验收来源、生产文件和具名测试；每个生产文件有归属。
- 每项测试包含id、name、path、layer和布尔`planned`。已有测试写`false`且必须存在并分类为测试；计划新增写`true`，不得替换生产文件。
- 每个功能有单元测试；集成或E2E不适用时分别说明结构性理由。缺少runner或环境不能写成不适用。
- `batches` 将每个功能恰好分到一个批次，依赖必须存在且无环。

映射检查通过只代表声明的结构一致，覆盖状态仍待复核。工具不自动生成测试、不修改生产实现、不把一个文件等同于全部行为。

## 托管单文件

无标记时表示整文件内容管理；有其他用户指令的全局文件必须使用成对标记。`--content` 是块内正文，不包含标记。

```sh
python3 <工具路径> managed-preview --target <目标> --content <正文文件> --output <新预览文件> --begin-marker '<文件中的起始标记>' --end-marker '<结束标记>'
python3 <工具路径> managed-apply --preview <预览文件> --fingerprint <本次预览指纹>
```

起始标记含版本号且需升级时，预览增加 `--new-begin-marker '<新版本起始标记>'`。旧标记用于定位，新标记与正文一并绑定到预览摘要，结束标记保持不变。

预览绑定目标路径、存在性、原字节/模式、正文来源和拟写内容；任何变化拒绝旧预览。替换前保留备份，新建禁止覆盖其他文件，写后读回。只承诺单文件乐观检查，不承诺对不合作写入者的原子锁或跨文件事务。全局写入仍须已有授权，写入成功也不证明宿主已经加载。
