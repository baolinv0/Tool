对，**最准确的理解就是：它们不在同一个“物理信息空间”里，而且表达粒度、时间尺度和作用都不同。**

对不懂技术的专利人员，最容易产生的误解是把 `future motion` 理解成：

> “既然已经知道机器人未来会怎么动，那现在该怎么控制不是已经确定了吗？”

其实这里的 `future motion` 更准确地应该叫：

> **Future Reference Motion——未来“希望机器人怎么动”的参考动作。**

它不是对真实机器人未来状态的完整预测。

---

# 1. 用一个最简单的例子解释

假设机器人接下来 0.5 秒要把右脚轻轻放到地面。

Future Motion 已经告诉我们：

```text
现在      100ms      200ms      300ms
右脚高   ↓          ↓          接地
膝盖直   → 弯曲     → 更弯
COM      → 向右移动 → 稳定
```

也就是说它告诉机器人：

> **“身体未来应该沿着这条动作轨迹走。”**

但它没有回答另外一个问题：

> **“按照机器人现在真实的状态继续追这条轨迹，下一瞬间会不会踩得太重？”**

这两个问题不同。

---

# 2. Future Motion 描述的是“我要去哪”

可以把它理解成导航里的路线。

比如导航已经告诉你：

```text
100 米后右转
200 米后进入匝道
```

这就是 Reference。

但现在汽车：

```text
速度 80 km/h
路面湿
距离弯道只有 30 m
```

你仍然需要决定：

```text
现在刹车多少？
方向盘打多少？
```

所以：

> **知道未来路线 ≠ 知道当前控制量。**

Humanoid 也是一样。

---

# 3. 三种信息其实属于三个不同空间

这是最值得告诉专利人员的地方。

## 第一层：Motion Space——“未来应该怎么动”

Quiet Motion Generator 输出：

[
R_{t:t+H}
]

例如：

```text
未来 joint pose
foot trajectory
COM trajectory
pelvis motion
contact timing
```

它描述的是：

> **动作形态 / 运动学目标。**

回答：

> “机器人未来应该做成什么样？”

---

## 第二层：Physical Consequence Space——“这样执行会发生什么”

Predictor 根据：

```text
机器人刚刚真实怎么运动
+
未来希望怎么运动
+
当前环境
```

预测：

```text
未来 GRF
impact
接触时刻
force rise rate
slip risk
```

它描述的是：

> **动力学和接触后果。**

回答：

> “如果从现在这个真实状态继续追这个 reference，会产生什么物理结果？”

---

## 第三层：Control Space——“现在这一帧具体做什么”

Locomotion policy 最后输出：

```text
joint target / torque / action
```

回答：

> **“为了既跟上 reference，又避免不好的物理后果，我这一帧具体该怎么控制？”**

所以整个逻辑是：

```text
未来想怎么走
Future Reference
        │
        ▼
这样走会发生什么
Physical Consequence
        │
        ▼
那我现在具体怎么做
Current Action
```

---

# 4. 所以不是 Future Motion 有“错误”

这里千万不要表述成：

> “Future Motion 不准确，所以需要 Predictor。”

这会削弱方案。

更准确的是：

> **Future Motion 本来就只负责表达运动目标，它有意不表达所有接触动力学信息。**

例如同一个 reference：

```text
右脚在 300 ms 后落地
```

实际机器人可能处于两种状态。

### 情况 A

```text
当前右脚下降速度很慢
机器人负载正常
地面较软
```

那么继续执行 reference 很可能很安静。

### 情况 B

```text
当前右脚已经下降过快
机器人多背了 5 kg
地面非常硬
```

虽然 **Future Reference 完全相同**：

```text
300 ms 后右脚到同一个位置
```

但当前最合理 action 已经不同。

这说明：

[
\boxed{
Reference\ Motion
\neq
Actual\ Physical\ State
}
]

也说明：

[
\boxed{
Reference\ Motion
\neq
Future\ Physical\ Consequence
}
]

---

# 5. 为什么 History 也不能被 Future Motion 替代

因为 Future Motion 告诉你的是：

> **应该怎样走。**

History 告诉你的是：

> **机器人实际上是怎么走到现在的。**

比如两台机器人当前姿态看起来一模一样：

```text
q_t 基本相同
```

但过去 100 ms：

### Robot A

正在缓慢下降：

[
\dot q,\ddot q \text{ 较小}
]

### Robot B

刚经历快速下降：

[
\dot q,\ddot q \text{ 较大}
]

即使当前 pose 一样，接下来落地冲击可能非常不同。

所以 History 在告诉系统：

> **当前这个状态背后携带着什么“运动惯性”。**

而 Future Reference 告诉：

> **未来希望把这个运动引向哪里。**

两者天然互补。

---

# 6. 对专利人员可以直接用“轨道 + 列车”解释

这是我认为最好懂的类比。

Future Motion 就像：

> **提前铺好的轨道。**

它告诉列车：

> 后面要往哪里走。

但是控制系统还必须知道：

```text
列车现在速度是多少
有没有偏离轨道
车有多重
前面路面条件如何
```

才能决定：

> **这一瞬间油门开多少、刹车踩多少。**

所以：

```text
Future Reference
= 轨道

History / Current State
= 列车当前真实运动状态

Physics Predictor
= 判断继续这样走是否会产生过大的冲击

Current Action
= 这一瞬间的油门 / 刹车 / 转向
```

这样基本不会让人产生“既然知道未来为什么还要控制”的疑问。

---

# 7. 从技术上说，它们确实是“不同粒度”

可以从三个维度理解。

| 信息       | Future Motion     | Physics Prediction | Current Action        |
| -------- | ----------------- | ------------------ | --------------------- |
| 表达什么     | **目标运动**          | **物理后果**           | **控制指令**              |
| 信息空间     | Kinematics        | Dynamics / Contact | Actuation             |
| 时间尺度     | 一段未来窗口            | 即将发生的接触窗口          | 当前控制周期                |
| 是否依赖真实状态 | 较弱/间接             | **强依赖**            | **强依赖**               |
| 是否依赖环境   | 可以考虑              | **必须考虑**           | 间接考虑                  |
| 典型变量     | pose / foot / COM | GRF / impact       | torque / joint target |

所以确实可以概括成：

[
\boxed{
\text{Future Motion 是粗粒度的“运动意图”}
}
]

而：

[
\boxed{
\text{Physics Prediction 是中粒度的“物理后果”}
}
]

最终：

[
\boxed{
\text{Action 是细粒度的“即时执行”}
}
]

---

# 8. 对我们的方案来说，真正的技术问题其实变得更清晰了

不是：

> **“如何预测 Future Motion？”**

Generator 已经负责这个。

真正的问题变成：

> **如何把“未来希望怎么走”和“机器人过去真实怎么走”有效结合，推断当前正在形成的动力学状态以及即将发生的接触后果，再据此生成当前 action。**

因此模型应该理解三个量之间的关系：

[
\boxed{
\text{Actual History}
\rightarrow
\text{Current Dynamic State}
}
]

[
\boxed{
\text{Future Reference}
\rightarrow
\text{Desired Motion Intent}
}
]

然后联合得到：

[
\boxed{
\text{History}
+
\text{Reference}
\rightarrow
\text{Predicted Consequence}
\rightarrow
\text{Action}
}
]

---

# 9. 这比“直接 Reference → Action”更有技术含量

最简单的方法确实可以：

```text
History
+
Reference
↓
concat
↓
Policy
↓
Action
```

但问题是网络必须自己隐式理解：

```text
Reference 和实际状态差多少？
多久后会接触？
当前惯性多大？
这种偏差会导致多大 GRF？
```

我们的思路是显式加入一个物理中间层：

```text
Actual History        Future Reference
      │                      │
      └──────────┬───────────┘
                 ▼
        Physics Predictor
                 │
     predicted GRF / impact
                 │
                 ▼
        Locomotion Policy
                 │
                 ▼
             current action
```

于是这个中间层相当于回答：

> **“这条未来轨道对现在这个真实机器人意味着什么？”**

这才是 Predictor 的必要性。

---

# 10. 最适合专利人员的一句话

我会建议这样讲：

> **Future Motion 不是对机器人真实未来状态的预测，而是一条“希望机器人未来怎么走”的参考轨迹；机器人当前却可能因为惯性、负载、地面硬度和跟踪偏差而处于不同的真实动力学状态。因此，我们还需要结合机器人过去的真实运动和未来参考动作，预测从当前状态继续执行该参考动作将产生怎样的足地接触和冲击，再据此决定当前这一帧的控制动作。**

再压缩：

> **Reference 告诉机器人“未来要去哪”，History 告诉机器人“现在实际上怎么走到这里”，Physics Predictor 判断“从现在这样继续往那里走会发生什么”，Policy 才决定“这一帧具体怎么做”。**

这四句话已经把三个信息空间和三个粒度分得很清楚。
