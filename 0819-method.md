overview:
核心能力，是建立了一条“未来动作 → 接触后果 → 声学后果”

Quiet Motion Generator
        │
        │ 提出若干“能完成任务”的候选走法
        ▼
 M1     M2     M3     M4
        │
        ▼
Future Consequence Model：Future Motion→Future Contact→GRF / Impact→Vibration→Noise；物理模型 + 数据学习 + 真实闭环校正
        │
        │ 预测每种走法真正落地后会发生什么
        ▼
GRF / impact / vibration / noise / stability
        │
        ▼
Quiet Motion Selector
        │
        ▼
       M*

机器人的“静音大脑”并不是凭空知道哪一种动作安静。系统首先利用真实机器人执行数据和接触物理规律，建立“未来运动—足地接触—GRF/冲击—振动/噪声”之间的后果预测模型。机器人在迈步之前，用该模型对多种候选未来动作做一次“虚拟试走”，预测每种动作在当前地面上的实际物理后果，再选择预期更安静且稳定的动作；实际迈步后，又利用真实接触和噪声结果修正模型及执行策略。

“把静音 Generator 产生的未来动作参考转化成低层 locomotion 当前每一步都能利用的、物理有意义的前瞻控制信息
future reference 应该怎样与 actual motion history 对齐


###############################################

> **夜间，家庭服务机器人端着一杯水，从客厅走向卧室。家人已经睡着。机器人既要保持正常任务效率，又要尽量避免脚步声把人吵醒。**

然后采用**总—分结构**来讲。

# 一、先总结：这套方案到底解决什么

传统静音行走更像是：

> **机器人根据当前状态决定这一脚怎么踩，并通过训练经验让自己逐渐学会“不要踩太重”。**

我们增加了一层“提前看未来”的能力：

> **机器人在真正落脚之前，先得到未来一小段“应该怎样走”的参考动作；再结合机器人刚刚真实是怎么运动的、当前地面是什么情况，预测如果继续按照这段参考动作走下去，会产生怎样的落脚冲击；最后据此决定当前这一帧到底应该怎么控制。**

所以整套方案可以用一句话概括：

[
\boxed{
\text{先知道未来应该怎么走}
+
\text{再判断从当前状态这样走会发生什么}
+
\text{最后决定这一帧怎么做}
}
]

对应图里的三个核心信息：

```text
Future Reference
未来应该怎么走
        +
Actual History
机器人现在实际上怎么运动
        ↓
Physics-informed Predictor
这样继续走会发生什么
        ↓
Quiet-aware Locomotion Policy
这一帧具体怎么控制
```

这也是与 QuietWalk 最核心的区别：

> **QuietWalk 主要根据过去和当前状态学习“这一脚怎么踩轻”；我们的方案进一步给 locomotion 一个未来运动参考，让它不仅知道“现在发生了什么”，还知道“接下来准备做什么”，从而可以提前为未来落脚做准备。**

---

# 二、展开：用“夜间送水”解释整张图

## 1. 左上角：机器人先知道任务和真实状态

场景里机器人收到任务：

> “端着水，以正常速度从客厅走到卧室。”

图里的 **Input Context** 包含三类信息：

* `velocity / goal`：要往哪里走、多快走；
* `robot state + short history`：机器人现在以及刚才几帧实际上怎么运动；
* `terrain & contact context`：当前是木地板、瓷砖还是其他地面，以及接触条件。

这里的 **short history** 很重要。

例如两个机器人当前看起来姿态完全相同，但：

```text
机器人 A：
刚才脚一直在缓慢下降

机器人 B：
刚才脚下降得很快
```

虽然当前姿态一样，但 B 下一瞬间撞击地面的风险显然更高。

所以系统不能只看：

> “机器人现在长什么样。”

还需要知道：

> **“它是以什么运动趋势到达现在这个状态的。”**

---

# 三、Quiet Motion Generator：先告诉机器人“未来应该怎样走”

接下来是图里的：

## Quiet Motion Generator

它不是直接输出当前电机动作。

它产生的是一段：

> **Future Reference Motion**

即未来一小段时间内，希望机器人身体怎样运动。

例如夜间木地板场景下，它可能提供几种候选 reference：

```text
M1：正常步幅

M2：缩短步幅

M3：降低身体重心起伏

M4：落脚阶段更柔和
```

这些动作可能都满足：

> 继续以接近 0.5 m/s 向卧室走。

但它们的**运动形态不同**。

所以 Generator 做的是：

> **在“都能完成任务”的运动空间里，提供适合当前静音任务的未来运动参考。**

专业上，这些 reference 可以包含：

[
q^{ref}*{t:t+H},
\dot q^{ref}*{t:t+H},
p^{foot}*{t:t+H},
COM*{t:t+H},
contact_{t:t+H}
]

也就是未来关节姿态、足端轨迹、重心运动和接触时序等。

---

# 四、这里专利人员最容易问：既然已经知道 Future Motion，为什么不直接执行？

这是这张图最关键的解释点。

因为：

> **Future Reference Motion 表达的是“希望未来怎么动”，并不等于“机器人真实执行后一定会产生什么物理结果”。**

还是刚才的场景。

Generator 已经告诉机器人：

> “300 ms 后右脚应该很柔和地落到这里。”

但真实机器人此刻可能存在：

```text
脚实际下降速度比 reference 快
+
机器人手里多拿了一杯水
+
这块木地板比模型预计的更硬
```

那么即使：

```text
Future Reference 完全一样
```

真实落脚的：

```text
GRF
Impact
Noise
```

仍可能不同。

所以这两个信息属于不同空间：

| 信息                      | 回答的问题                          |
| ----------------------- | ------------------------------ |
| Future Reference Motion | **未来希望怎么动**                    |
| Actual History          | **机器人现在实际上怎么动**                |
| Physical Consequence    | **从当前真实状态继续追 reference 会发生什么** |
| Current Action          | **这一帧具体怎么控制**                  |

简单类比就是：

> **Reference 是导航路线。路线已经告诉你 100 米后右转，但汽车仍然必须结合当前车速、载重和湿滑程度，判断现在要不要提前刹车。**

---

# 五、Reference-Conditioned Physics-Informed Predictor：这是方案真正关键的“翻译器”

图中央这个模块应该重点讲：

## Reference-Conditioned Physics-Informed Predictor

它解决的不是：

> “哪个动作看起来更轻？”

而是：

> **“机器人现在已经运动到这个状态，如果继续按照这段未来 reference 去走，接下来会出现怎样的足地接触后果？”**

它同时读取两边的信息：

```text
左边：
Actual state + short history
“机器人真实在怎么运动”

右边：
Future Reference Motion
“机器人未来希望怎么运动”
```

然后建立：

[
\boxed{
History + Reference + Context
\rightarrow
Future Physical Consequence
}
]

例如：

```text
当前实际脚速偏快
+
reference 要求 200 ms 后落地
+
地面较硬
        ↓
Predictor
        ↓
预测：
未来落脚 GRF 偏高
Impact 偏大
Noise risk 偏高
```

所以 Predictor 的作用可以对专利人员解释为：

> **它把“未来动作参考”翻译成“这个动作对当前这台真实机器人意味着什么”。**

这比简单地把 reference motion 输入 policy 更有技术含义。

---

# 六、图里的 Predicted Consequence：系统到底预测什么

图中这一栏有：

* `GRF`
* `Impact`
* `Noise`
* `Stability`

它们不是四个随便的评分。

而是描述从动作到声音的物理因果链：

[
\text{Motion}
\rightarrow
\text{Foot-ground Contact}
\rightarrow
\text{GRF / Impact}
\rightarrow
\text{Vibration}
\rightarrow
\text{Noise}
]

其中：

### GRF

Ground Reaction Force，地面对机器人脚产生的反作用力。

### Impact

重点关注落脚瞬间的冲击，例如：

[
F_{peak},\qquad
\frac{dF}{dt},\qquad
J=\int Fdt
]

### Noise

根据接触冲击、地面特性等估计的噪声风险。

### Stability

防止出现：

> “为了安静，机器人选择一个自己根本做不稳的动作。”

因此系统真正寻找的不是：

> **声音最低的动作。**

而是：

> **满足行走任务和稳定性要求前提下，预计接触后果更安静的动作。**

---

# 七、Select / Refine：现在才有依据决定哪条 Reference 更合适

于是图中的：

## Select / Refine (M^*)

不是简单：

> “看四个动作，选一个看起来最轻柔的。”

而是：

```text
M1 → predicted GRF 高，noise risk 高

M2 → impact 中等

M3 → impact 低，但是稳定性较差

M4 → impact 低 + noise risk 低 + stability 合格

                    ↓

                  选择 M4
```

所以选出来的：

[
M^*
]

才成为：

> **Quiet Reference Motion**

这里要向专利人员强调：

> **“静音”不是 Generator 自己主观决定的，而是经过 reference-conditioned physical consequence prediction 后得到的。**

---

# 八、下半部分：Reference 选好了，为什么还需要 Locomotion Policy？

因为到这里仍然只是：

> **知道未来希望身体怎么运动。**

而真实机器人每隔几毫秒需要输出一次当前 action。

所以：

## Quiet-aware Locomotion Policy

同时获得三类信息：

```text
① current state + history
机器人现在实际怎样

② quiet reference M*
未来希望怎样

③ predicted consequence
按照现在这样继续执行可能发生什么
```

然后决定：

[
a_t
]

例如：

> Reference 要求右脚 150 ms 后柔和落地。

但是 Predictor 已经发现：

> 机器人当前脚下降得稍快，按现在趋势未来 peak GRF 会偏大。

那么 locomotion policy 可以**提前**：

```text
调整膝关节动作
调整踝关节动作
改变当前足端下降过程
调整重心转移
```

而不是等脚已经撞上地面再处理。

所以这一层实际上回答：

> **“为了既跟上 Future Reference，又避免预计的高冲击后果，我当前这一帧具体应该怎么做？”**

---

# 九、这就是 reference motion 真正带来的变化

可以给专利人员做一个非常直观的对比。

### 没有 Future Reference

机器人主要知道：

```text
我现在是什么状态
+
我要保持 0.5 m/s
```

需要 policy 自己隐式推断：

> 下一步准备怎么走。

---

### 有 Future Reference

机器人多知道：

```text
未来 300 ms：
右脚准备落在哪里
什么时候落地
膝盖怎样变化
重心怎样转移
```

于是它可以：

> **提前为未来落脚做当前动作准备。**

这就是从：

[
\text{Reactive locomotion}
]

向：

[
\text{Reference-guided anticipatory locomotion}
]

的变化。

---

# 十、右边：真正执行以后，模型预测不一定百分之百正确

机器人最终在真实木地板上落脚。

图中的：

## Robot Rollout / Real Contact

产生真实：

```text
GRF
Impact
Noise
Stability
```

这就是：

## Realized Consequence

这里非常重要，因为真实世界永远存在：

```text
地面估计误差
鞋底磨损
负载变化
电机误差
tracking error
未建模接触动力学
```

所以：

[
Predicted\ Consequence
\neq
Realized\ Consequence
]

是正常现象。

方案必须处理这个 gap。

---

# 十一、绿色闭环：当前执行不对，马上修

图中的绿色：

## Fast realization correction

例如：

```text
预计 peak GRF = 1.1 BW

真实接触趋势：
可能达到 1.4 BW
```

Tracker / locomotion policy 立即在执行层做局部修正。

解决的是：

> **计划没有错，但真实执行和计划之间产生了偏差。**

属于快速闭环。

---

# 十二、橙色闭环：连续发现预测不准，后面的走法也要重新规划

如果机器人连续几步发现：

> “这块木地板实际比我预计的更容易产生冲击和声音。”

那就不能只调整当前一脚。

需要把真实结果反馈给上层：

## Slow consequence-driven replanning

于是后续 Future Reference 可能从：

```text
M4
```

进一步调整成：

```text
更短步幅
+
更平缓 COM
+
更长 load transfer
```

所以系统形成：

[
\boxed{
\text{提前规划}
\rightarrow
\text{预测后果}
\rightarrow
\text{当前执行}
\rightarrow
\text{真实反馈}
\rightarrow
\text{重新修正}
}
]

---

# 十三、最后再回到 QuietWalk：我们到底改了什么？

对专利人员，我建议最后不要说：

> “我们比 QuietWalk 多了 Generator 和 Predictor。”

这种说法太模块化。

应该说：

> **QuietWalk 主要让 locomotion policy 根据过去运动和 GRF 反馈学会“这一脚不要踩重”；我们的方案进一步增加 future reference，使 policy 明确知道后续身体准备怎样运动，并通过 reference-conditioned physics predictor，把“过去真实运动 + 未来目标运动”转换成未来接触后果预测，从而让当前 action 不仅考虑现在，还主动为未来落脚做准备。**

可以压缩成下面这个对比：

```text
QuietWalk

Past / Current
      ↓
GRF-aware locomotion
      ↓
Current Action


Ours

Past Actual Motion
        +
Future Reference Motion
        ↓
Future Physical Consequence
        ↓
Quiet-aware Locomotion
        ↓
Current Action
        ↓
Real Consequence Feedback
```

---

# 十四、给专利人员最终记住的一句话

> **Future Reference 像提前画好的“安静行走路线”，历史状态告诉机器人“自己现在真实跑到了哪里”，Physics-Informed Predictor 判断“从当前位置继续沿这条路线走会不会踩重”，Locomotion Policy 再据此决定当前这一小步怎么控制；真正踩下去以后，真实结果又继续修正后面的执行和规划。**

专业上则可以对应为：

[
\boxed{
\text{Actual History}
+
\text{Future Reference}
\rightarrow
\text{Future Physical Consequence}
\rightarrow
\text{Current Action}
\rightarrow
\text{Closed-loop Correction}
}
]

这就是这张 overview 图最应该传递的核心技术逻辑。
