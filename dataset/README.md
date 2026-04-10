# 数据集 (Dataset)

任务定义在 **`tasks/`** 下（按分组：foundation、secretary 等），本目录存放各任务对应的 **mock / 注入数据**。

## 目录对应关系

- 从 `tasks/{category}/task_*.md` 读任务说明与评分逻辑。
- 从 `dataset/{category}/{task_id}/` 取该任务所需的数据文件（如图片、视频、模拟 API 返回等），由 benchmark 运行时注入到工作区。

路径对应示例：

| 任务定义 | 数据目录 |
|----------|----------|
| tasks/foundation/task_f_01_web_search.md | dataset/foundation/task_f_01_web_search/（可选，f_01 无输入文件） |
| tasks/foundation/task_f_02_image_understand.md | dataset/foundation/task_f_02_image_understand/ |
| tasks/secretary/task_sec_01_info_extract.md | dataset/secretary/task_sec_01_info_extract/ |

## 当前分组

- **foundation/** — 基础能力层（f_05、f_06、f_12、f_13、f_15 等有数据；f_01～f_04 等部分任务需自备或 mock）
- **secretary/** — 秘书场景（sec_01、sec_02、sec_06 等）
- **programmer/** — 程序员场景（prog_01～prog_12，与 `tasks/programmer/README.md` 一致）
- **digital_twin/**、**finance/**、**operator/** — 部分任务有数据

每个 task 文件夹内仅放该任务需要的 mock 文件（如 test_image.jpg、demo.mp4、audio.wav、summary_source.txt 等），无单独 README。
