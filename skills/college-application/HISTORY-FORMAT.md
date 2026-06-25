# history/events.jsonl 格式

每行一个 JSON 对象：

```json
{"id":"evt_...","timestamp":"2026-06-24T10:00:00+08:00","stage":"self-discovery","type":"answer-updated","summary":"用户将偏好从稳定环境改为项目变化较多","version":3,"related_ids":["answer_work_style"]}
```

允许的 `stage`：

- `self-discovery`
- `guidance`
- `major-research`
- `industry-research`
- `admission-analysis`
- `simulation`
- `audit`

历史只追加不覆盖。修正错误时追加新事件并通过 `related_ids` 指向旧记录。

