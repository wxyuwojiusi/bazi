# manual_runner.py
"""
八字推理手动测试工具 (Human-in-the-loop)
用于手动执行推理链条，生成 Prompt 并允许用户输入 LLM 结果。
"""

import json
import os
from reasoning_orchestrator import ReasoningOrchestrator

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    orchestrator = ReasoningOrchestrator()
    data_path = "output_full.json"
    
    if not os.path.exists(data_path):
        print(f"错误: 找不到 {data_path}。请先运行 test_complete.py 生成数据。")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        bazi_data = json.load(f)

    # 初始上下文
    context = {
        "user_name": input("请输入缘主姓名 (默认: 张三): ") or "张三"
    }

    # 定义推理步骤
    steps = [
        ("pattern", "第一步：格局定性"),
        ("strength", "第二步：旺衰分析"),
        ("yongshen", "第三步：用神选取"),
        ("dayun", "第四步：大运评估"),
        ("liunian", "第五步：流年预测"),
        ("report", "第六步：最终报告")
    ]

    print("\n" + "="*40)
    print("  八字推理手动运行工具 (V2.0)")
    print("="*40)
    print("说明：本工具将按步骤为您生成渲染后的 Prompt。")
    print("您可以将其复制到 Claude/ChatGPT 中运行，然后将返回的 JSON 结果粘贴回来。")
    input("\n按回车键开始...")

    for step_id, step_name in steps:
        clear_screen()
        print(f"当前阶段：{step_name}")
        print("-" * 20)
        
        try:
            # 1. 生成 Prompt
            prompt = orchestrator.get_prompt_for_step(step_id, bazi_data, context)
            
            # 2. 将 Prompt 保存到临时文件，方便用户复制
            filename = f"manual_prompt_{step_id}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(prompt)
            
            print(f"✓ Prompt 已生成并更新至文件: {filename}")
            print("请在该文件中复制内容，并发送给 LLM。")
            
            # 如果是报告环节，仅展示 Prompt，不需要输入
            if step_id == "report":
                print("\n所有推理已完成！最终报告 Prompt 已准备好。")
                print("程序结束。")
                break

            # 3. 询问用户 LLM 的输出
            print("\n" + "!" * 40)
            print("请在下方粘贴 LLM 返回的 JSON 结果 (输入 END 后回车结束输入):")
            print("!" * 40)
            
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            
            json_str = "".join(lines)
            if not json_str.strip():
                print("未检测到输入，将使用默认/空值继续（仅推荐用于快速测试）。")
                input("按回车继续...")
                continue
                
            # 4. 解析并更新 Context
            try:
                # 尝试提取 JSON 内容（处理 LLM 可能带有的 ```json 代码块）
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                result_data = json.loads(json_str)
                context.update(result_data)
                
                # 统一协议映射：确保每一个环节的输出都能被下一步的看板识别
                if step_id == "pattern":
                    context["pattern_type"] = result_data.get("pattern_type") or result_data.get("pattern_conclusion")[:20] or "未知格局"
                    context["pattern_conclusion"] = result_data.get("pattern_conclusion") or result_data.get("reasoning") or "格局分析通过"
                elif step_id == "strength":
                    context["strength_level"] = result_data.get("strength_level") or "状态未知"
                    context["strength_conclusion"] = result_data.get("strength_conclusion") or result_data.get("reasoning") or result_data.get("overall_strength") or "旺衰分析通过"
                elif step_id == "special_flow":
                    context["special_flow_conclusion"] = result_data.get("special_flow_conclusion") or result_data.get("reasoning") or "自化格局分析通过"
                elif step_id == "yongshen":
                    context["yongshen_conclusion"] = result_data.get("yongshen_conclusion") or result_data.get("yongshen_advice") or "用神分析通过"
                    # 辅助：更新用神概览用于报告
                    pg = result_data.get("primary_god", {})
                    if pg:
                        elem = pg.get("element") if isinstance(pg, dict) else str(pg)
                        context["primary_god_summary"] = f"用神：{elem}"
                elif step_id == "dayun":
                    context["dayun_conclusion"] = result_data.get("dayun_conclusion") or result_data.get("dayun_summary") or "大运评估通过"
                    context["dayun_report"] = result_data.get("dayun_summary") or context["dayun_conclusion"][:50]
                elif step_id == "liunian":
                    context["liunian_conclusion"] = result_data.get("liunian_conclusion") or result_data.get("liunian_theme") or "流年预测通过"
                    context["liunian_report"] = result_data.get("liunian_theme") or context["liunian_conclusion"][:50]
                
                print("\n✓ JSON 解析成功，Context 已更新。")
                input("按回车进行下一步...")
                
            except Exception as e:
                print(f"\n❌ JSON 解析失败: {e}")
                print("输入内容无效。请确保粘贴的是合法的 JSON 格式。")
                input("按回车重新开始本步骤...")
                # 这里可以考虑让循环重试本步，简化直接跳过
                continue

        except Exception as e:
            print(f"运行出错: {e}")
            break

if __name__ == "__main__":
    main()
