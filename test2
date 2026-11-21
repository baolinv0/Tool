**根因判断：8004 服务没有完整落实输出合约，同时 Rewriter 接口让模型重新生成了本应由代码保管的锚句和权限。优先修这两处。**

## 1. 格式失败：JSON 约束没有在实际输出链路中生效

**证据：**请求了 `json_object`，仍返回 Markdown 围栏。

**最可能的原因：**wrapper 接受了 `response_format`，但没有把它正确传入后端约束解码；也可能是具体版本中 reasoning 与约束解码的衔接失效。标准 vLLM 的 `json_object` 本来就会映射到结构化解码，不需要额外加 `guided_json` 才生效。[docs.vllm.ai](https://docs.vllm.ai/en/v0.11.1/api/vllm/entrypoints/openai/protocol/?utm_source=chatgpt.com)

**解决方案：**

- 检查 wrapper 调用后端时，是否真正传入结构化输出参数。
- 使用完整的 **`json_schema`**，约束 CF/CT/CFT、字段类型和额外字段。
- 用一个极小 Schema 对比“原生后端”和“8004 wrapper”；原生通过、wrapper 失败，就能直接定位到 wrapper。

## 2. thinking 泄漏：生成模式与响应解析没有正确配合

**证据：**E 开启 thinking，推理正文进入了 `content`，没有被正确分离。

**最可能的原因：**未启用匹配的 reasoning parser，或者模板、parser、wrapper 响应拼装不一致。

**解决方案：**

- Rewriter 先使用 **`enable_thinking=False`**，确认它实际传到 tokenizer 的模板渲染。
- 如果保留 thinking，使用匹配模型和版本的 parser，把 reasoning 与 `content` 分开。
- 暂停用 `low/xhigh` 调参：**原版 Qwen3-8B 模板并不读取这些 effort 参数**，除非 wrapper 另外实现了映射。[huggingface.co](https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json?utm_source=chatgpt.com)

你们的 B/D 没有证明“关 thinking 失败”；它们证明的是关闭后仍有格式和业务错误。

## 3. 语义失败：接口给了模型过多不必要的写权限

**核心问题：**只需要模型提出恢复策略，却要求它重新输出整个 IR、锚句、`scope`、`mutable_by` 和完整 `new_text`。因此复制错误与权限漂移都可能触发 `protected_requirement_modified`。

**最有效的解决方案：模型只输出 ID 和追加文本。**

```json
{
  "requirement_id": "req_face_strategy",
  "append_text": "仅恢复输入可支持的面部纹理，保持五官轮廓与表情。"
}
```

代码负责：

```python
new_text = frozen_ir[requirement_id].source_span + separator + append_text
```

同时：

- 原始 IR、锚句、`mutable_by` 全部冻结，由代码读取；
- 每个 slot 只能选择允许的 requirement ID；
- 保留原编译器检查；
- J1 检查追加内容是否与保护要求冲突。

**这项修改能从构造方式上保证原文保留，比让模型逐字复述更可靠。**

## 建议执行顺序

1. **先修 8004：**确认 non-thinking 和 JSON Schema 约束真实生效。
2. **再改 Rewriter：**只生成 `requirement_id + append_text`，代码拼接并检查权限。
3. **最后评估更大模型：**用于改善策略质量和冲突判断。

**r3 的 JSON 提取可以用于诊断，但不能算原始 JSON 合格；`mutable_by` 也不应通过推断来“修正”。当前优先级最高的是服务接线和接口收缩，继续增加 token 或强化 prompt 的收益较低。**
