# Hypotheses — cs-skill-lab-001（自指：cs-skill-lab 评自己）

实验对象：`cs-skill-lab`（author/review 能力）对「带缺陷的 skill 草稿」的识别。
oracle：`planted_defect` 召回，[measured]。收敛用 **meta-focused**（方法本身是目标：V_meta≥0.80 且 V_instance≥0.55）。

- **H-selfreview-recall**: cs-skill-lab 对已知 skill-authoring/代码缺陷的 recall ≥ 0.80。threshold: 0.80。

自指说明：本实验用与其它实验**同一** runner/scorer 指向 `cs-skill-lab/SKILL.md` 自身；
不调用 cs-skill-lab 的工具（无递归），只把其 SKILL.md 作为被测文本注入。
统计功效：3 fixtures（n<8）→ [underpowered]，作自指可行性证明。
