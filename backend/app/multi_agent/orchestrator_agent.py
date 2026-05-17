import asyncio
from agents import Agent, ModelSettings,Runner 
from infrastructure.ai.openai_client import sub_model
from infrastructure.ai.prompt_loader import load_prompt
from multi_agent.agent_factory import AGENT_TOOLS
from infrastructure.tools.mcp.mcp_servers import baidu_map_mcp,search_mac_client
from contextlib import AsyncExitStack

# 创建主调度智能体
orchestrator_agent = Agent(
    name="主调度智能体",
    instructions=load_prompt("orchestrator"),
    model=sub_model,
    model_settings=ModelSettings(
        temperature=0,
    ),
    # 直接使用Agent Tools
    tools=AGENT_TOOLS,
)


# 测试代码
async def run_single_test(case_name: str, input_text: str): 
    print(f"\n{'='*80}")
    print(f"测试: {case_name}")
    print(f"输入: {input_text}")
    print("-"*80)

    # 使用 AsyncExitStack 同时管理多个连接
    async with AsyncExitStack() as stack:
        try: 
            print("连接MCP服务...")
            # 1. 进入上下文
            await stack.enter_async_context(search_mac_client)
            await stack.enter_async_context(baidu_map_mcp)
            print("思考中...")

            # 2. 使用流式处理运行 Orchestrator Agent
            result = Runner.run_streamed(
                starting_agent=orchestrator_agent,
                input=input_text,
            )

            # 3. 遍历流式事件
            async for event in result.stream_events():
                # 3.1 run_item_stream_event级别的事件（Agent运行时产生的事件）
                if event.type == "run_item_stream_event":
                    # 3.1.1 Agent运行时的工具调用事件
                    if hasattr(event, "name") and event.name == "tool_called":
                        from agents import ToolCallItem
                        if isinstance(event.item, ToolCallItem):
                            raw_item = event.item.raw_item
                            print(f"\n调用工具名: {raw_item.name}--->>工具参数:{raw_item.arguments}")
                        # 3.1.2 Agent运行时的工具调用结果事件
                        elif hasattr(event, "name") and event.name == "tool_output":
                            from agents import ToolCallOutputItem
                            if isinstance(event.item, ToolCallOutputItem):
                                print(f"调用工具结果 {event.item.output}")

            # 4. 打印最终输出（最后协调Agent的输出）
            print(f"最终输出:（来自{result.final_output}）：")
            print(result.final_output)
        except Exception as e:
            print(f"\n 异常原因: {str(e)}\n")
        
async def main():
    print("\n"+"="*80)
    print("测试协调Agent (Orchestrator)")
    print("=" *80)

    #定义测试案例
    test_cases = [
        #咨询技术智能体
        # ("单个任务(实时问题)","今天小米股价多少")
        #("单个任务(实时问题)","今天AI圈发生了些什么事儿”)，
        #("单个任务(技术问题)","我的电脑黑屏了怎么办”)
        #(单个务(技术问题)","为什么Windows7中删除文件之后，在回收站找不到呢?")，

        #服务站与导航智能体
        # ("单个任务(服务站查询)","我想去联想thinkpad电脑售后维修服务中心")
        #(”单个任务(服务站查询)","帮我找个最近的维修站”)，
        #("单个任务(POI导航)","导航去颐和园”)
        #(”单个任务(0I导航)","天安门广场都有哪些商场”)，

        # ("多跳任务(先实时问题在服务站)","查一下今天北京的天气预报，如果下雨的话，就帮我找一家最近的服务站，我去躲躲雨顺便维修电脑。")
        ("多跳任务(先技术问题在服务站)","我的联想笔记本开机蓝屏代码怎么解决?如果太复杂处理不了，就直接帮我导航去最近的联想官方服务站。")
        #("混合需求(先实时问题在POI导航)","帮我查一下今天故宫的门票售蕃了吗?如果没有，请给导航去故宫博物院。”)，
        #("多跳任务(先技术问题在POI导航)","电脑无法开机怎么办?问完这个，请帮我导航去清华大学，我想去拍夜景。”)，
        #("多跳任务(先服务站在实时问题)","帮我找一家最近的小米之家。另外，顺便查一下小米汽车现在的交付周期是多久?")，
        #("多跳任务(先服务站在技术问题)","请给我导航去附近的苹果官方维修点。在路上我想了解一下，iPhone 电池健康度掉到 80%以下必须更换吗?”)，
        #("多跳任务(先POI在实时问题)","我想去欢乐谷玩，请生成导航链接。顺便查一下今天欢乐谷闭园时间是几点?")，
        #("多跳任务(先POI在技术问题)","导航去中关村电子城。另外我想问问，组装一台4090显卡的电脑大概需要多大功率的电源?”)，
    ]

    # 循环执行测试
    for case_name, input_text in test_cases:
        await run_single_test(case_name, input_text)

if __name__ == '__main__':
    asyncio.run(main())
